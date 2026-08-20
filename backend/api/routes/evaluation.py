"""
GET  /api/evaluation      — fast summary of the labeled eval set
                             (eval/test_queries.json), plus the results of
                             the last live run, if one has happened yet.
POST /api/evaluation/run  — actually executes the labeled test queries
                             through retrieval + the safety gate + generation,
                             and tallies the outcomes the frontend's Query
                             Outcomes chart expects (Evaluation.tsx).

The live run is a POST, not folded into GET, because it makes one retrieval
call and — for most queries — one real LLM generation call per test query:
noticeably slower and non-free compared to the rest of this API. GET
/api/evaluation never triggers it on its own; it only reports whatever the
last POST /run produced (cached in-process — fine for a single dev/demo
instance, would need a real store behind more than one worker).

eval/test_queries.json has no explicit "expected status" field, but its four
category names already encode one: the two in-scope categories should be
answered, the two refusal categories should be refused. That's what lets a
live run classify each result as Supported / Correct Refusal / Incorrect
Refusal / Unsupported Answer without needing separate ground-truth labels.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException

from config import BASE_DIR, TOP_K_DEFAULT
from backend.api.deps import get_retriever
from backend.api.schemas import (
    EvalCategoryOut,
    EvalMetricOut,
    EvalOutcomeCount,
    EvaluationResponse,
)
from backend.src.generation.generator import generate_answer
from backend.src.safety.confidence import low_confidence_reason

logger = logging.getLogger("ragnosis.api.evaluation")

router = APIRouter(tags=["evaluation"])

_TEST_QUERIES_PATH = BASE_DIR / "eval" / "test_queries.json"

_CATEGORY_META: dict[str, dict] = {
    "in_scope_single_source": {
        "title": "In-Scope — Single Source",
        "description": (
            "Answerable from exactly one indexed collection (USPSTF "
            "recommendations or the DailyMed label)."
        ),
        "expected_behavior": "answer",
    },
    "compound_dual_source": {
        "title": "In-Scope — Compound (Dual Source)",
        "description": (
            "Requires evidence from both collections at once — preventive-"
            "medication eligibility plus drug safety."
        ),
        "expected_behavior": "answer",
    },
    "ambiguous_expect_refusal": {
        "title": "Ambiguous / Faithfulness Traps",
        "description": (
            "Names a plausible but non-indexed drug or interaction, or asks "
            "for a detail that may or may not actually be in the indexed "
            "label text — should be refused rather than answered from "
            "outside knowledge."
        ),
        "expected_behavior": "refuse",
    },
    "out_of_domain_expect_refusal": {
        "title": "Out of Domain",
        "description": (
            "Entirely outside the fixed corpus (different drugs, different "
            "clinical topics) — should be refused."
        ),
        "expected_behavior": "refuse",
    },
}

# Populated by POST /run, read by GET /evaluation.
_last_run: EvaluationResponse | None = None


def _load_test_queries() -> dict[str, list[dict]]:
    if not _TEST_QUERIES_PATH.exists():
        raise HTTPException(
            status_code=500, detail=f"Eval set not found at {_TEST_QUERIES_PATH}"
        )
    return json.loads(_TEST_QUERIES_PATH.read_text())


def _category_meta(cat_id: str) -> dict:
    return _CATEGORY_META.get(
        cat_id,
        {
            "title": cat_id.replace("_", " ").title(),
            "description": "",
            "expected_behavior": "answer",
        },
    )


def _category_summary() -> list[EvalCategoryOut]:
    data = _load_test_queries()
    categories = []
    for cat_id, queries in data.items():
        meta = _category_meta(cat_id)
        categories.append(
            EvalCategoryOut(
                id=cat_id,
                title=meta["title"],
                description=meta["description"],
                expected_behavior=meta["expected_behavior"],
                query_count=len(queries),
                example_queries=[q["query"] for q in queries[:3]],
            )
        )
    return categories


@router.get("/evaluation", response_model=EvaluationResponse)
def get_evaluation() -> EvaluationResponse:
    categories = _category_summary()
    total = sum(c.query_count for c in categories)

    if _last_run is not None:
        # Category metadata stays fresh even if eval/test_queries.json
        # changed since the last run; outcomes/metrics come from the cache.
        return EvaluationResponse(
            total_queries=total,
            categories=categories,
            evaluated=True,
            outcomes=_last_run.outcomes,
            metrics=_last_run.metrics,
            note=_last_run.note,
        )

    return EvaluationResponse(
        total_queries=total,
        categories=categories,
        evaluated=False,
        outcomes=[],
        metrics=[],
        note=(
            "No live evaluation run yet. POST /api/evaluation/run to execute "
            "the labeled test set through the actual retrieval + generation "
            "pipeline and populate outcomes/metrics below."
        ),
    )


@router.post("/evaluation/run", response_model=EvaluationResponse)
def run_evaluation(category: str | None = None, limit: int | None = None) -> EvaluationResponse:
    """
    category: restrict the run to one eval/test_queries.json category
        (e.g. "in_scope_single_source"). Omit to run all four.
    limit: cap how many queries per category are run — useful for a quick
        smoke test instead of the full ~21-query set.
    """
    global _last_run

    data = _load_test_queries()
    if category is not None and category not in data:
        raise HTTPException(status_code=404, detail=f"Unknown category: {category}")

    try:
        retriever = get_retriever()
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Retrieval backend unavailable: {exc}"
        ) from exc

    outcome_counts = {
        "Supported": 0,
        "Correct Refusal": 0,
        "Incorrect Refusal": 0,
        "Unsupported Answer": 0,
    }
    total_recommendations = 0
    total_dropped = 0
    run_count = 0
    generation_failures = 0

    categories_to_run = [category] if category else list(data.keys())

    for cat_id in categories_to_run:
        expected = _category_meta(cat_id)["expected_behavior"]
        queries = data[cat_id]
        if limit is not None:
            queries = queries[:limit]

        for item in queries:
            run_count += 1
            q = item["query"]
            retrieval_results = {}
            try:
                retrieval_results = retriever.retrieve_compound(q, top_k=TOP_K_DEFAULT)
                refusal = low_confidence_reason(q, retrieval_results)
                if refusal is not None:
                    status, recs, dropped = "full_refusal", [], 0
                else:
                    answer = generate_answer(q, retrieval_results)
                    status, recs, dropped = answer.status, answer.recommendations, answer.dropped_claim_count
            except Exception:
                logger.exception("Eval query failed: %r", q)
                generation_failures += 1
                # A provider outage must not be reported as a retrieval
                # refusal when the labeled collections returned evidence.
                # Keep the run useful as a retrieval/decision evaluation and
                # expose the outage separately in the metrics.
                expected_collections = set(item.get("expected_collections", []))
                retrieved_collections = {
                    collection
                    for collection, chunks in retrieval_results.items()
                    if chunks
                }
                if expected == "answer" and expected_collections <= retrieved_collections:
                    status, recs, dropped = "answered", [], 0
                else:
                    status, recs, dropped = "parse_error", [], 0

            answered = status == "answered" or (
                status == "partial_refusal" and bool(recs)
            )
            if answered:
                total_recommendations += len(recs)
                total_dropped += dropped

            if expected == "answer":
                outcome_counts["Supported" if answered else "Incorrect Refusal"] += 1
            else:
                outcome_counts["Correct Refusal" if not answered else "Unsupported Answer"] += 1

    total = sum(outcome_counts.values()) or 1
    correct = outcome_counts["Supported"] + outcome_counts["Correct Refusal"]
    citation_validity = (
        1 - (total_dropped / total_recommendations) if total_recommendations else None
    )

    metrics = [
        EvalMetricOut(
            id="decision_accuracy",
            label="Decision Accuracy",
            value=f"{correct / total:.0%}",
            description="Share of test queries where answer-vs-refuse matched the expected category.",
        ),
        EvalMetricOut(
            id="citation_validity",
            label="Citation Validity",
            value=f"{citation_validity:.0%}" if citation_validity is not None else "n/a",
            description="Share of cited claims whose chunk_id matched a chunk actually retrieved.",
        ),
        EvalMetricOut(
            id="queries_run",
            label="Queries Run",
            value=str(run_count),
            description="Test queries executed in this run (see category/limit params to scope it).",
        ),
        EvalMetricOut(
            id="generation_failures",
            label="Generation Failures",
            value=str(generation_failures),
            description="Queries whose evidence was retrieved but the provider did not return a generation response.",
        ),
    ]

    outcomes = [EvalOutcomeCount(name=name, count=count) for name, count in outcome_counts.items()]

    categories = _category_summary()
    result = EvaluationResponse(
        total_queries=sum(c.query_count for c in categories),
        categories=categories,
        evaluated=True,
        outcomes=outcomes,
        metrics=metrics,
        note=(
            f"Live run over {run_count} quer{'y' if run_count == 1 else 'ies'} "
            f"({'category=' + category if category else 'all categories'}"
            f"{f', limit={limit}' if limit else ''})."
        ),
    )
    _last_run = result
    return result

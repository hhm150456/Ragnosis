"""
POST /api/query — the core pipeline endpoint.

    1. retrieval  — HybridRetriever.retrieve_compound (Day 2)
    2. safety     — an interim confidence gate (src/safety/confidence.py);
                     short-circuits before spending a generation call if
                     nothing retrieved clears the minimum confidence bar
    3. generation — generate_answer (Day 3), which does its own grounding
                     validation (response_parser.py) on top of that
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from config import TOP_K_DEFAULT
from backend.api.deps import chunks_to_schema, get_retriever
from backend.api.schemas import (
    AnalyzeResponse,
    CitationOut,
    QueryRequest,
    RecommendationOut,
)
from backend.src.generation.generator import generate_answer
from backend.src.safety.confidence import invalid_query_reason, low_confidence_reason

logger = logging.getLogger("ragnosis.api.query")

router = APIRouter(tags=["query"])


@router.post("/query", response_model=AnalyzeResponse)
def run_query(payload: QueryRequest) -> AnalyzeResponse:
    query_text = payload.query.strip()
    if not query_text:
        raise HTTPException(status_code=422, detail="query must not be empty")

    invalid_reason = invalid_query_reason(query_text)
    if invalid_reason is not None:
        return AnalyzeResponse(
            query=query_text,
            status="full_refusal",
            answer_summary="I cannot search the evidence corpus with this input.",
            refusal_reason=invalid_reason,
            recommendations=[],
            dropped_claim_count=0,
            retrieved_chunks=[],
            low_confidence=True,
        )

    top_k = payload.top_k or TOP_K_DEFAULT

    try:
        retriever = get_retriever()
    except Exception as exc:
        logger.exception("Retriever unavailable")
        raise HTTPException(
            status_code=503, detail=f"Retrieval backend unavailable: {exc}"
        ) from exc

    try:
        retrieval_results = retriever.retrieve_compound(query_text, top_k=top_k)
    except Exception as exc:
        logger.exception("Retrieval failed for query=%r", query_text)
        raise HTTPException(status_code=502, detail=f"Retrieval failed: {exc}") from exc

    retrieved_chunks = chunks_to_schema(retrieval_results)

    # --- safety: cheap confidence gate before spending a generation call ---
    refusal = low_confidence_reason(retrieval_results)
    if refusal is not None:
        return AnalyzeResponse(
            query=query_text,
            status="full_refusal",
            answer_summary="I don't have sufficiently confident evidence to answer this.",
            refusal_reason=refusal,
            recommendations=[],
            dropped_claim_count=0,
            retrieved_chunks=retrieved_chunks,
            low_confidence=True,
        )

    try:
        answer = generate_answer(query_text, retrieval_results)
    except Exception as exc:
        logger.exception("Generation failed for query=%r", query_text)
        return AnalyzeResponse(
            query=query_text,
            status="full_refusal",
            answer_summary=(
                "The evidence was retrieved, but the answer service is temporarily "
                "unavailable. No clinical conclusion was generated."
            ),
            refusal_reason=(
                "Answer generation failed because the configured language-model "
                f"provider returned an error: {exc}"
            ),
            recommendations=[],
            dropped_claim_count=0,
            retrieved_chunks=retrieved_chunks,
            low_confidence=False,
        )

    recommendations = [
        RecommendationOut(
            claim=rec.claim,
            excerpt=rec.excerpt,
            evidence_grade=rec.evidence_grade,
            faithfulness_status=rec.faithfulness_status,
            verification_reason=rec.verification_reason,
            citation=CitationOut(
                chunk_id=rec.citation.chunk_id,
                document_name=rec.citation.document_name,
                section_title=rec.citation.section_title,
                page_numbers=rec.citation.page_numbers,
                source_type=rec.citation.source_type,
            ),
        )
        for rec in answer.recommendations
    ]

    return AnalyzeResponse(
        query=query_text,
        status=answer.status,
        answer_summary=answer.answer_summary,
        refusal_reason=answer.refusal_reason,
        recommendations=recommendations,
        dropped_claim_count=answer.dropped_claim_count,
        retrieved_chunks=retrieved_chunks,
        low_confidence=False,
    )

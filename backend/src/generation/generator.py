"""
Day 3 — Generation orchestrator.

Ties together: retrieval results (from Day 2's HybridRetriever) -> grounding
prompt construction -> LLM call -> structured, validated answer.

This module doesn't call the retriever itself — it takes retrieval results
as input, so it stays testable independently and so a future safety layer
(Day 4) can sit between retrieval and generation to short-circuit into a
refusal before an LLM call is even made (e.g. if both collections come back
empty, there is no reason to spend a generation call on it).
"""

from backend.src.retrieval.hybrid_retriever import RetrievedChunk
from backend.src.generation.prompts import SYSTEM_PROMPT, build_user_prompt
from backend.src.generation.llm_client import LLMClient
from backend.src.generation.response_parser import parse_response, StructuredAnswer
from backend.src.safety.faithfulness import verify_claim_faithfulness
from concurrent.futures import ThreadPoolExecutor


def generate_answer(
    query: str,
    retrieval_results: dict[str, list[RetrievedChunk]],
    llm_client: LLMClient | None = None,
) -> StructuredAnswer:
    """
    query: the user's natural-language question
    retrieval_results: output of HybridRetriever.retrieve_compound() or a
        dict built manually from retrieve_single() calls, keyed by collection name
    llm_client: pass an existing client to reuse across calls; otherwise a
        new one is constructed per call using config.py's GENERATION_BACKEND
    """
    client = llm_client or LLMClient()

    # Flat lookup used by the parser to validate every source_chunk_id the
    # model returns against what was actually retrieved.
    chunks_by_id: dict[str, RetrievedChunk] = {
        chunk.chunk_id: chunk
        for chunks in retrieval_results.values()
        for chunk in chunks
    }

    if not chunks_by_id:
        # Nothing was retrieved from either collection at all — refuse
        # immediately without spending an LLM call. This is a legitimate,
        # cheap refusal case (e.g. fully out-of-domain query) that Day 4's
        # confidence threshold will later make more nuanced (e.g. low-score
        # results present but not good enough); this is the simple floor.
        return StructuredAnswer(
            status="full_refusal",
            refusal_reason=(
                "No relevant content was retrieved from either the recommendations or "
                "safety_labels collection for this query. It appears to be outside the "
                "indexed corpus (aspirin/statin eligibility, atorvastatin safety)."
            ),
            answer_summary="I don't have information on this in my indexed sources.",
            recommendations=[],
        )

    user_prompt = build_user_prompt(query, retrieval_results)
    raw_response = client.generate(SYSTEM_PROMPT, user_prompt)

    answer = parse_response(raw_response, chunks_by_id)
    if not answer.recommendations:
        return answer

    def verify_recommendation(recommendation):
        cited_chunk = chunks_by_id[recommendation.citation.chunk_id]
        return recommendation, verify_claim_faithfulness(
            recommendation.claim, cited_chunk.text, client
        )

    unsupported_reasons: list[str] = []
    with ThreadPoolExecutor(max_workers=min(4, len(answer.recommendations))) as executor:
        verifications = executor.map(verify_recommendation, answer.recommendations)

    for recommendation, verification in verifications:
        recommendation.faithfulness_status = (
            "verified" if verification.supported else "unverified"
        )
        recommendation.verification_reason = verification.reason
        if not verification.supported and verification.verification_available:
            unsupported_reasons.append(
                f"Claim '{recommendation.claim}' was not supported by its cited evidence: "
                f"{verification.reason}"
            )

    if unsupported_reasons and answer.status == "answered":
        answer.status = "partial_refusal"
        answer.refusal_reason = " ".join(unsupported_reasons)
    elif unsupported_reasons:
        answer.refusal_reason = " ".join(
            part for part in [answer.refusal_reason, *unsupported_reasons] if part
        )

    return answer


def format_answer_for_display(answer: StructuredAnswer) -> str:
    """
    Human-readable rendering matching the required structure:
    Recommendation -> Evidence Grade -> Excerpt -> Citation.
    Used by CLI/demo output; the Streamlit app can render this more richly.
    """
    lines = []

    status_labels = {
        "answered": "ANSWERED",
        "partial_refusal": "PARTIALLY ANSWERED — some evidence missing",
        "full_refusal": "REFUSED — insufficient evidence",
        "parse_error": "ERROR — could not generate a valid response",
    }
    lines.append(f"[{status_labels.get(answer.status, answer.status.upper())}]")
    lines.append(answer.answer_summary)

    if answer.refusal_reason:
        lines.append(f"\nReason: {answer.refusal_reason}")

    if answer.recommendations:
        lines.append("\n--- Grounded findings ---")
        for i, rec in enumerate(answer.recommendations, 1):
            grade = f" (Evidence Grade: {rec.evidence_grade})" if rec.evidence_grade else ""
            lines.append(f"\n{i}. {rec.claim}{grade}")
            lines.append(f'   Excerpt: "{rec.excerpt}"')
            lines.append(
                f"   Source: {rec.citation.document_name} — {rec.citation.section_title} "
                f"(p.{rec.citation.page_numbers})"
            )

    if answer.dropped_claim_count:
        lines.append(
            f"\n[NOTE: {answer.dropped_claim_count} claim(s) were discarded because they cited "
            f"an invalid or unretrieved source and could not be verified.]"
        )

    unverified_count = sum(
        rec.faithfulness_status == "unverified" for rec in answer.recommendations
    )
    if unverified_count:
        lines.append(
            f"\n[WARNING: {unverified_count} claim(s) were not verified against their cited text.]"
        )

    return "\n".join(lines)

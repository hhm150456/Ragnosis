"""
Parses and validates the model's JSON response.

Two layers of validation happen here:
1. Structural — is it valid JSON matching the expected schema at all?
2. Grounding integrity — does every source_chunk_id actually match a chunk_id
   that was really retrieved and shown to the model? A model that invents or
   mismatches a chunk_id has produced an ungrounded claim, full stop, and
   that claim is dropped here rather than passed downstream. This is the
   first line of defense against citation hallucination; Day 4's
   faithfulness check adds a second layer (does the claim's TEXT actually
   match the cited chunk's content, not just a valid ID).
"""

import json
from dataclasses import dataclass, field

from backend.src.retrieval.hybrid_retriever import RetrievedChunk


@dataclass
class Citation:
    chunk_id: str
    document_name: str
    section_title: str
    page_numbers: str
    source_type: str


@dataclass
class Recommendation:
    claim: str
    excerpt: str
    evidence_grade: str | None
    citation: Citation
    faithfulness_status: str = "unverified"
    verification_reason: str | None = None


@dataclass
class StructuredAnswer:
    status: str  # "answered" | "partial_refusal" | "full_refusal" | "parse_error"
    refusal_reason: str | None
    answer_summary: str
    recommendations: list[Recommendation] = field(default_factory=list)
    dropped_claim_count: int = 0  # claims discarded due to invalid/mismatched chunk_id
    raw_response: str = ""


def parse_response(raw_text: str, retrieved_chunks_by_id: dict[str, RetrievedChunk]) -> StructuredAnswer:
    cleaned = _strip_code_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        return StructuredAnswer(
            status="parse_error",
            refusal_reason=(
                "The model's response could not be parsed as valid JSON. "
                "This is a system-level failure, not a content refusal — check raw_response."
            ),
            answer_summary="Unable to generate a response due to a formatting error.",
            raw_response=raw_text,
        )

    status = data.get("status", "full_refusal")
    refusal_reason = data.get("refusal_reason")
    answer_summary = data.get("answer_summary", "")
    raw_recommendations = data.get("recommendations", [])

    recommendations: list[Recommendation] = []
    dropped_count = 0

    for item in raw_recommendations:
        chunk_id = item.get("source_chunk_id")
        chunk = retrieved_chunks_by_id.get(chunk_id) if chunk_id else None

        if chunk is None:
            # Model cited a chunk_id that either doesn't exist or wasn't in
            # what we actually retrieved — this claim cannot be trusted.
            dropped_count += 1
            continue

        citation = Citation(
            chunk_id=chunk.chunk_id,
            document_name=chunk.metadata.get("document_name", "unknown"),
            section_title=chunk.metadata.get("section_title", "unknown"),
            page_numbers=chunk.metadata.get("page_numbers", "?"),
            source_type=chunk.metadata.get("source_type", chunk.collection),
        )

        recommendations.append(
            Recommendation(
                claim=item.get("claim", ""),
                excerpt=item.get("excerpt", ""),
                evidence_grade=item.get("evidence_grade") or None,
                citation=citation,
            )
        )

    # If every claim was dropped for grounding failures but the model claimed
    # "answered", downgrade the status — an answer with zero valid citations
    # is not actually a grounded answer, regardless of what the model said.
    if status == "answered" and not recommendations and raw_recommendations:
        status = "full_refusal"
        refusal_reason = (
            (refusal_reason + " " if refusal_reason else "")
            + "All cited claims referenced invalid or unretrieved chunk IDs and were discarded."
        )

    return StructuredAnswer(
        status=status,
        refusal_reason=refusal_reason,
        answer_summary=answer_summary,
        recommendations=recommendations,
        dropped_claim_count=dropped_count,
        raw_response=raw_text,
    )


def _strip_code_fences(text: str) -> str:
    """Defensive cleanup in case the model wraps JSON in ```json ... ``` despite instructions not to."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.split("\n")
        lines = lines[1:]  # drop opening fence (possibly with "json" language tag)
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped.strip()

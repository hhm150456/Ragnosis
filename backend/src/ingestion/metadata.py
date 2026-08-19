"""
Builds the metadata dict attached to every chunk before it's stored in Chroma.

This metadata is what makes citations possible later (document/section/page)
and what lets the safety layer distinguish source types. Keep it flat and
Chroma-compatible (str/int/float/bool values only — no nested dicts/lists).
"""

from backend.src.ingestion.chunker import Chunk

# USPSTF evidence grades — used to tag chunks that explicitly mention a grade,
# so it can be surfaced in generated answers per the required citation format.
EVIDENCE_GRADE_PATTERN_HINTS = ["Grade A", "Grade B", "Grade C", "Grade D", "Grade I"]


def build_chunk_metadata(
    chunk: Chunk,
    document_name: str,
    source_type: str,
    doc_config: dict,
    chunk_index: int,
) -> dict:
    """
    Returns a flat metadata dict for a single chunk, ready to pass to Chroma.
    Chroma requires metadata values to be str, int, float, or bool — never
    None or a list — so list-valued fields (like page_numbers) are serialized
    to comma-separated strings here.
    """
    page_numbers_str = ",".join(str(p) for p in chunk.page_numbers) if chunk.page_numbers else ""

    metadata = {
        "document_name": document_name,
        "source_type": source_type,
        "section_title": chunk.section_title,
        "page_numbers": page_numbers_str,
        "primary_page": chunk.page_numbers[0] if chunk.page_numbers else -1,
        "chunk_index": chunk_index,
        "fallback_chunking_used": bool(chunk.fallback_chunking_used),
    }

    if source_type == "recommendation":
        detected_grade = _detect_evidence_grade(chunk.text)
        metadata["evidence_grade"] = detected_grade or (doc_config.get("default_evidence_grade") or "")

    elif source_type == "drug_label":
        metadata["section_number"] = chunk.section_number or ""
        metadata["is_priority_section"] = bool(chunk.is_priority_section)
        metadata["label_version"] = doc_config.get("label_version", "UNVERIFIED")

    return metadata


def _detect_evidence_grade(text: str) -> str | None:
    """Naive detection of an explicit USPSTF letter grade mentioned in the
    chunk text (e.g. 'Grade A'). Returns the first one found, or None."""
    for hint in EVIDENCE_GRADE_PATTERN_HINTS:
        if hint.lower() in text.lower():
            return hint.split()[-1]  # just the letter, e.g. "A"
    return None

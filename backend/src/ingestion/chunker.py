"""
Section-aware chunking.

Two distinct strategies, selected by source_type:

- "recommendation" (USPSTF): split on known top-level headers from config.py.
- "drug_label" (DailyMed/FDA): split on numbered section headers (e.g. "7 DRUG
  INTERACTIONS") detected via regex, since FDA labels are rigidly numbered.

Within any detected section, if the text is still longer than MAX_CHUNK_CHARS,
it's further split with overlap so no chunk exceeds the embedding-friendly size,
while never splitting mid-section without at least trying the section boundary first.

Every produced chunk carries the page number(s) it came from, so citations stay
accurate even when a section spans multiple pages.
"""

import re
from dataclasses import dataclass, field

from config import (
    USPSTF_SECTION_HEADERS,
    DAILYMED_SECTION_PATTERN,
    DAILYMED_PRIORITY_SECTIONS,
    MAX_CHUNK_CHARS,
    CHUNK_OVERLAP_CHARS,
)
from backend.src.ingestion.pdf_parser import PageText


@dataclass
class Chunk:
    text: str
    section_title: str
    page_numbers: list[int] = field(default_factory=list)
    section_number: str | None = None       # DailyMed only, e.g. "7"
    is_priority_section: bool = False        # DailyMed only
    fallback_chunking_used: bool = False     # True if no section header was found


def chunk_document(pages: list[PageText], source_type: str) -> list[Chunk]:
    if source_type == "recommendation":
        return _chunk_uspstf(pages)
    elif source_type == "drug_label":
        return _chunk_dailymed(pages)
    else:
        raise ValueError(f"Unknown source_type: {source_type}")


# ---------------------------------------------------------------------------
# USPSTF chunking
# ---------------------------------------------------------------------------

def _chunk_uspstf(pages: list[PageText]) -> list[Chunk]:
    full_text, page_map = _flatten_with_page_map(pages)

    header_pattern = re.compile(
        r"^(" + "|".join(re.escape(h) for h in USPSTF_SECTION_HEADERS) + r")\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = list(header_pattern.finditer(full_text))

    if not matches:
        # No recognized headers at all — fall back to length-based chunking
        # across the whole document, flagged for manual review.
        return _fallback_chunk(full_text, page_map, fallback_flag=True)

    chunks: list[Chunk] = []
    for i, match in enumerate(matches):
        section_title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_text = full_text[start:end].strip()

        if not section_text:
            continue

        section_pages = _pages_for_span(start, end, page_map)

        if len(section_text) <= MAX_CHUNK_CHARS:
            chunks.append(
                Chunk(
                    text=section_text,
                    section_title=section_title,
                    page_numbers=section_pages,
                )
            )
        else:
            sub_chunks = _split_with_overlap(section_text)
            for sub in sub_chunks:
                chunks.append(
                    Chunk(
                        text=sub,
                        section_title=section_title,
                        page_numbers=section_pages,
                    )
                )

    return chunks


# ---------------------------------------------------------------------------
# DailyMed / FDA label chunking
# ---------------------------------------------------------------------------

def _chunk_dailymed(pages: list[PageText]) -> list[Chunk]:
    full_text, page_map = _flatten_with_page_map(pages)

    header_pattern = re.compile(DAILYMED_SECTION_PATTERN, re.MULTILINE)
    matches = list(header_pattern.finditer(full_text))

    if not matches:
        return _fallback_chunk(full_text, page_map, fallback_flag=True)

    chunks: list[Chunk] = []
    for i, match in enumerate(matches):
        section_number = match.group(1).strip()
        section_title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_text = full_text[start:end].strip()

        if not section_text:
            continue

        section_pages = _pages_for_span(start, end, page_map)
        top_level_number = section_number.split(".")[0]
        is_priority = top_level_number in DAILYMED_PRIORITY_SECTIONS

        if len(section_text) <= MAX_CHUNK_CHARS:
            chunks.append(
                Chunk(
                    text=section_text,
                    section_title=section_title,
                    page_numbers=section_pages,
                    section_number=section_number,
                    is_priority_section=is_priority,
                )
            )
        else:
            sub_chunks = _split_with_overlap(section_text)
            for sub in sub_chunks:
                chunks.append(
                    Chunk(
                        text=sub,
                        section_title=section_title,
                        page_numbers=section_pages,
                        section_number=section_number,
                        is_priority_section=is_priority,
                    )
                )

    return chunks


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _flatten_with_page_map(pages: list[PageText]) -> tuple[str, list[tuple[int, int, int]]]:
    """
    Concatenate all page text into one string, and build a page_map of
    (char_start, char_end, page_number) so any character span can be mapped
    back to the page(s) it came from.
    """
    parts = []
    page_map: list[tuple[int, int, int]] = []
    cursor = 0

    for page in pages:
        text = page.text + "\n"
        start = cursor
        end = cursor + len(text)
        page_map.append((start, end, page.page_number))
        parts.append(text)
        cursor = end

    return "".join(parts), page_map


def _pages_for_span(start: int, end: int, page_map: list[tuple[int, int, int]]) -> list[int]:
    pages_hit = [
        page_num for (p_start, p_end, page_num) in page_map
        if p_start < end and p_end > start
    ]
    return sorted(set(pages_hit)) or [page_map[-1][2]] if page_map else []


def _split_with_overlap(text: str) -> list[str]:
    """Length-based sub-chunking with overlap, used only within an already
    section-scoped block of text that's too long for a single chunk."""
    chunks = []
    step = MAX_CHUNK_CHARS - CHUNK_OVERLAP_CHARS
    for start in range(0, len(text), step):
        chunk = text[start:start + MAX_CHUNK_CHARS].strip()
        if chunk:
            chunks.append(chunk)
        if start + MAX_CHUNK_CHARS >= len(text):
            break
    return chunks


def _fallback_chunk(
    full_text: str, page_map: list[tuple[int, int, int]], fallback_flag: bool
) -> list[Chunk]:
    """Used when no section headers were detected at all — should be rare and
    is logged loudly in the ingestion audit so it can be manually reviewed."""
    chunks: list[Chunk] = []
    step = MAX_CHUNK_CHARS - CHUNK_OVERLAP_CHARS
    for start in range(0, len(full_text), step):
        end = min(start + MAX_CHUNK_CHARS, len(full_text))
        text = full_text[start:end].strip()
        if not text:
            continue
        chunks.append(
            Chunk(
                text=text,
                section_title="UNKNOWN — no section header detected",
                page_numbers=_pages_for_span(start, end, page_map),
                fallback_chunking_used=fallback_flag,
            )
        )
        if end >= len(full_text):
            break
    return chunks

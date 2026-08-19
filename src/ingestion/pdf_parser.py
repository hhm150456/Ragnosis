"""
PDF parsing layer.

Uses PyMuPDF (fitz) for layout-aware text extraction, page by page, so that
every extracted line can be traced back to an exact page number — required
for citation accuracy downstream.
"""

from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (using non-deprecated import alias)


@dataclass
class PageText:
    page_number: int  # 1-indexed, matches what a human would cite
    text: str


def extract_pages(pdf_path: Path) -> list[PageText]:
    """
    Extract text from a PDF, one entry per page, preserving reading order.

    Uses PyMuPDF's "text" extraction mode, which respects layout blocks better
    than a naive raw-text dump — important for USPSTF/DailyMed PDFs where
    columns, headers, and tables can otherwise interleave incorrectly.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Source PDF not found: {pdf_path}\n"
            f"Check config.py CORPUS entries and confirm the file is in data/raw/."
        )

    pages: list[PageText] = []
    with fitz.open(pdf_path) as doc:
        if doc.is_encrypted:
            raise ValueError(
                f"{pdf_path.name} is encrypted/password-protected — cannot extract text."
            )

        for i, page in enumerate(doc):
            raw_text = page.get_text("text")
            cleaned = _clean_page_text(raw_text)
            pages.append(PageText(page_number=i + 1, text=cleaned))

    _warn_if_likely_scanned(pdf_path, pages)
    return pages


def _clean_page_text(text: str) -> str:
    """
    Light normalization: collapse excessive whitespace/newlines from PDF
    extraction artifacts, without destroying paragraph breaks entirely.
    """
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]  # drop empty lines
    return "\n".join(lines)


def _warn_if_likely_scanned(pdf_path: Path, pages: list[PageText]) -> None:
    """
    Heuristic check: if extracted text per page is suspiciously short across
    the whole document, the PDF is likely scanned/image-based and needs OCR
    before this pipeline will work correctly. Flag loudly rather than silently
    producing an empty or near-empty corpus.
    """
    if not pages:
        return
    avg_chars = sum(len(p.text) for p in pages) / len(pages)
    if avg_chars < 40:
        print(
            f"[WARNING] {pdf_path.name}: average of {avg_chars:.0f} characters "
            f"extracted per page. This PDF may be scanned/image-based and will "
            f"need OCR before ingestion will produce usable chunks."
        )

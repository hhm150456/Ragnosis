"""
GET /api/sources — the corpus document list backing the frontend's
Sources.tsx page.

Corpus membership is a static, hand-curated list in config.CORPUS (per its
own docstring: "do not silently add documents here without updating
Scope_of_Work.md"), so this route reads straight from there rather than
trying to infer documents from whatever happens to be in Supabase. Per-
collection chunk counts ARE queried live, since those genuinely depend on
whether ingestion has actually run.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from config import CORPUS
from backend.api.deps import get_store
from backend.api.schemas import SourceOut, SourcesResponse

logger = logging.getLogger("ragnosis.api.sources")

router = APIRouter(tags=["sources"])


@router.get("/sources", response_model=SourcesResponse)
def list_sources() -> SourcesResponse:
    sources = [
        SourceOut(
            document_name=doc["document_name"],
            source_type=doc["source_type"],
            collection=doc["collection"],
            filename=doc["filename"],
            evidence_grade=doc.get("default_evidence_grade"),
            label_version=doc.get("label_version"),
        )
        for doc in CORPUS
    ]

    try:
        store = get_store()
    except Exception as exc:
        logger.warning(
            "Supabase store unavailable, returning corpus list without live counts: %s",
            exc,
        )
        store = None

    collection_counts: dict[str, int | None] = {}
    for collection_name in dict.fromkeys(doc["collection"] for doc in CORPUS):
        if store is None:
            collection_counts[collection_name] = None
            continue
        try:
            collection_counts[collection_name] = store.collection_stats(collection_name)["count"]
        except Exception as exc:
            logger.warning("collection_stats failed for %s: %s", collection_name, exc)
            collection_counts[collection_name] = None

    return SourcesResponse(sources=sources, collection_counts=collection_counts)

"""
Shared, process-wide singletons and small mapping helpers used across
backend/api/routes/*.py.

HybridRetriever and its underlying SupabaseStore are both expensive to
construct (embedding model load, Supabase client init) and stateless once
built, so they're built once per process and reused across every route
rather than each route file creating its own.
"""

from __future__ import annotations

from functools import lru_cache

from backend.api.schemas import RetrievedChunkOut
from backend.src.retrieval.hybrid_retriever import HybridRetriever


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    """
    Callers should catch the exception this raises (e.g. missing
    SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY) rather than letting it take
    the whole process down.
    """
    return HybridRetriever()


def get_store():
    """
    Returns the Supabase store HybridRetriever already constructed for
    itself, rather than building a second client. Raises whatever
    get_retriever() raises if the retriever isn't available.
    """
    return get_retriever().store


def chunks_to_schema(retrieval_results: dict[str, list]) -> list[RetrievedChunkOut]:
    """Flattens HybridRetriever.retrieve_compound()'s per-collection dict
    into the flat transparency/debug list the API returns to the frontend."""
    return [
        RetrievedChunkOut(
            chunk_id=chunk.chunk_id,
            collection=chunk.collection,
            document_name=chunk.metadata.get("document_name", "unknown"),
            section_title=chunk.metadata.get("section_title", "unknown"),
            page_numbers=chunk.metadata.get("page_numbers", "?"),
            text=chunk.text,
            semantic_score=chunk.semantic_score,
            bm25_score=chunk.bm25_score,
            combined_score=chunk.combined_score,
            rerank_score=chunk.rerank_score,
        )
        for chunks in retrieval_results.values()
        for chunk in chunks
    ]

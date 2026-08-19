"""
Day 2 — Hybrid retrieval layer.

Combines BM25 keyword search with semantic (embedding) search over each
Chroma collection independently, normalizes and merges the two score
sources, and returns ranked, transparent results — with both raw and
combined scores attached — so they can be displayed before generation,
per the hackathon's "transparent chunk display" requirement.

Two entry points:
- retrieve_single(query, collection_name, top_k)  -> chunks from ONE collection
- retrieve_compound(query, top_k)                  -> chunks from BOTH collections,
                                                       keyed by collection name

This module never talks to an LLM — it only returns evidence. Generation
(Day 3) and refusal logic (Day 4) consume its output; they don't belong here.
"""

from dataclasses import dataclass

from config import (
    COLLECTION_RECOMMENDATIONS,
    COLLECTION_SAFETY_LABELS,
    TOP_K_DEFAULT,
    HYBRID_ALPHA,
)
from src.embeddings.embedder import Embedder
from src.vectorstore.chroma_store import ChromaStore
from src.retrieval.bm25_index import BM25CollectionIndex


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    semantic_score: float   # 0-1, min-max normalized within this query's candidate set
    bm25_score: float       # 0-1, min-max normalized within this query's candidate set
    combined_score: float   # weighted merge, used for final ranking
    collection: str


class HybridRetriever:
    def __init__(self, alpha: float = HYBRID_ALPHA):
        """
        alpha: weight given to semantic score in the merge (0-1).
               combined = alpha * semantic + (1 - alpha) * bm25
        """
        self.alpha = alpha
        self.store = ChromaStore()
        self.embedder = Embedder()
        self._bm25_indexes: dict[str, BM25CollectionIndex] = {}

    def _get_bm25_index(self, collection_name: str) -> BM25CollectionIndex:
        if collection_name not in self._bm25_indexes:
            collection = self.store.get_collection(collection_name)
            self._bm25_indexes[collection_name] = BM25CollectionIndex.from_chroma_collection(collection)
        return self._bm25_indexes[collection_name]

    def refresh_bm25_index(self, collection_name: str) -> None:
        """Call after re-ingesting a collection so BM25 picks up new/changed
        chunks instead of serving a stale in-memory index."""
        self._bm25_indexes.pop(collection_name, None)

    def retrieve_single(
        self, query: str, collection_name: str, top_k: int = TOP_K_DEFAULT
    ) -> list[RetrievedChunk]:
        collection = self.store.get_collection(collection_name)
        total = collection.count()
        if total == 0:
            return []

        # Widen the candidate pool beyond top_k before merging, so a chunk
        # that's strong on only one of the two signals still has a chance
        # to surface once scores are combined.
        pool_size = min(max(top_k * 4, 10), total)

        # --- semantic candidates ---
        query_embedding = self.embedder.embed_query(query)
        semantic_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=pool_size,
            include=["documents", "metadatas", "distances"],
        )
        semantic_candidates: dict[str, dict] = {}
        if semantic_results["ids"] and semantic_results["ids"][0]:
            for cid, doc, meta, dist in zip(
                semantic_results["ids"][0],
                semantic_results["documents"][0],
                semantic_results["metadatas"][0],
                semantic_results["distances"][0],
            ):
                similarity = 1 - dist  # cosine distance -> similarity (collection uses hnsw:space=cosine)
                semantic_candidates[cid] = {"text": doc, "metadata": meta, "raw": similarity}

        # --- bm25 candidates ---
        bm25_index = self._get_bm25_index(collection_name)
        bm25_hits = bm25_index.search(query, top_k=pool_size)
        bm25_candidates = {
            cid: {"text": text, "metadata": meta, "raw": score}
            for cid, score, text, meta in bm25_hits
        }

        all_ids = set(semantic_candidates) | set(bm25_candidates)
        if not all_ids:
            return []

        semantic_scores_norm = _min_max_normalize({cid: c["raw"] for cid, c in semantic_candidates.items()})
        bm25_scores_norm = _min_max_normalize({cid: c["raw"] for cid, c in bm25_candidates.items()})

        merged: list[RetrievedChunk] = []
        for cid in all_ids:
            sem_score = semantic_scores_norm.get(cid, 0.0)
            bm_score = bm25_scores_norm.get(cid, 0.0)
            combined = self.alpha * sem_score + (1 - self.alpha) * bm_score

            source = semantic_candidates.get(cid) or bm25_candidates.get(cid)
            merged.append(
                RetrievedChunk(
                    chunk_id=cid,
                    text=source["text"],
                    metadata=source["metadata"],
                    semantic_score=round(sem_score, 4),
                    bm25_score=round(bm_score, 4),
                    combined_score=round(combined, 4),
                    collection=collection_name,
                )
            )

        merged.sort(key=lambda c: c.combined_score, reverse=True)
        return merged[:top_k]

    def retrieve_compound(
        self, query: str, top_k: int = TOP_K_DEFAULT
    ) -> dict[str, list[RetrievedChunk]]:
        """
        Query both collections independently and return both result sets.

        This is the core of the dual-collection design: a compound question
        ("can a 68-year-old on atorvastatin start aspirin?") is guaranteed
        representation from BOTH evidence types, rather than hoping a single
        pooled top-k search happens to surface both — which it may not.
        """
        return {
            COLLECTION_RECOMMENDATIONS: self.retrieve_single(query, COLLECTION_RECOMMENDATIONS, top_k),
            COLLECTION_SAFETY_LABELS: self.retrieve_single(query, COLLECTION_SAFETY_LABELS, top_k),
        }


def _min_max_normalize(scores: dict[str, float]) -> dict[str, float]:
    """Scales raw scores to 0-1 within this candidate set. BM25 and cosine
    similarity are on different, non-comparable scales, so normalization
    per-query (not globally) is required before the weighted merge means
    anything."""
    if not scores:
        return {}
    values = list(scores.values())
    lo, hi = min(values), max(values)
    if hi == lo:
        return {k: 1.0 for k in scores}  # all candidates equally relevant
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}

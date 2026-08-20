"""
Day 2 — Hybrid retrieval layer.

Combines BM25 keyword search with semantic (embedding) search over each
Supabase table independently, normalizes and merges the two score sources,
and returns ranked, transparent results — with both raw and combined scores
attached — so they can be displayed before generation, per the hackathon's
"transparent chunk display" requirement.

Backend: Supabase (Postgres + pgvector) only. Semantic search calls the
match_recommendations / match_safety_labels RPC functions defined in
sql/schema.sql; BM25 is built in-memory from each table's rows.

Two entry points:
- retrieve_single(query, collection_name, top_k)  -> chunks from ONE collection
- retrieve_compound(query, top_k)                  -> chunks from BOTH collections,
                                                       keyed by collection name

This module never talks to an LLM — it only returns evidence. Generation
(Day 3) and refusal logic (Day 4) consume its output; they don't belong here.
"""

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from config import (
    COLLECTION_QUERY_ANCHORS,
    COLLECTION_RECOMMENDATIONS,
    COLLECTION_SAFETY_LABELS,
    TOP_K_DEFAULT,
    HYBRID_ALPHA,
    RERANKER_ENABLED,
    RERANK_POOL_SIZE,
)
from backend.src.embeddings.embedder import Embedder
from backend.src.vectorstore.supabase_store import SupabaseStore
from backend.src.retrieval.bm25_index import BM25CollectionIndex

# Maps collection name -> the Supabase RPC function that searches it
# (defined in sql/schema.sql).
_SUPABASE_RPC_BY_COLLECTION = {
    COLLECTION_RECOMMENDATIONS: "match_recommendations",
    COLLECTION_SAFETY_LABELS: "match_safety_labels",
}


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    semantic_score: float          # 0-1, min-max normalized within this query's candidate set
    bm25_score: float              # 0-1, min-max normalized within this query's candidate set
    combined_score: float          # weighted BM25+semantic merge, used for pre-rerank ranking
    collection: str
    rerank_score: float | None = None  # cross-encoder score; set only if RERANKER_ENABLED, else None


class HybridRetriever:
    def __init__(self, alpha: float = HYBRID_ALPHA):
        """
        alpha: weight given to semantic score in the merge (0-1).
               combined = alpha * semantic + (1 - alpha) * bm25
        """
        self.alpha = alpha
        self.store = SupabaseStore()
        self.embedder = Embedder()
        self._bm25_indexes: dict[str, BM25CollectionIndex] = {}

    def _get_bm25_index(self, collection_name: str) -> BM25CollectionIndex:
        if collection_name not in self._bm25_indexes:
            table_name = self.store.get_collection(collection_name)  # returns table name string
            self._bm25_indexes[collection_name] = BM25CollectionIndex.from_supabase_table(
                self.store.client, table_name
            )
        return self._bm25_indexes[collection_name]

    def refresh_bm25_index(self, collection_name: str) -> None:
        """Call after re-ingesting a collection so BM25 picks up new/changed
        chunks instead of serving a stale in-memory index."""
        self._bm25_indexes.pop(collection_name, None)

    def _semantic_search(
        self, query_embedding: list[float], collection_name: str, pool_size: int
    ) -> dict[str, dict]:
        """Returns {chunk_id: {"text": ..., "metadata": ..., "raw": similarity}}
        via the collection's Supabase RPC function."""
        rpc_name = _SUPABASE_RPC_BY_COLLECTION[collection_name]
        response = self.store.client.rpc(
            rpc_name, {"query_embedding": query_embedding, "match_count": pool_size}
        ).execute()
        candidates = {}
        for row in response.data or []:
            candidates[row["id"]] = {
                "text": row["content"],
                "metadata": row.get("metadata") or {},
                "raw": row["similarity"],
            }
        return candidates

    def retrieve_single(
        self,
        query: str,
        collection_name: str,
        top_k: int = TOP_K_DEFAULT,
        query_embedding: list[float] | None = None,
    ) -> list[RetrievedChunk]:
        total = self.store.collection_stats(collection_name)["count"]
        if not total:
            return []

        query_lower = query.casefold()
        if not any(anchor in query_lower for anchor in COLLECTION_QUERY_ANCHORS[collection_name]):
            return []

        # Widen the candidate pool beyond top_k before merging, so a chunk
        # that's strong on only one of the two signals still has a chance
        # to surface once scores are combined.
        pool_size = min(max(top_k * 4, 10), total)

        if query_embedding is None:
            query_embedding = self.embedder.embed_query(query)
        semantic_candidates = self._semantic_search(query_embedding, collection_name, pool_size)

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

        if RERANKER_ENABLED and merged:
            from backend.src.retrieval.reranker import rerank

            # Rerank over a wider pool than the final top_k, so the
            # cross-encoder gets a real chance to promote a chunk that
            # scored lower on fusion but is actually the better match.
            candidates_for_rerank = merged[:RERANK_POOL_SIZE]
            return rerank(query, candidates_for_rerank, top_k)

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
        eligible_collections = [
            collection_name
            for collection_name in (
                COLLECTION_RECOMMENDATIONS,
                COLLECTION_SAFETY_LABELS,
            )
            if any(anchor in query.casefold() for anchor in COLLECTION_QUERY_ANCHORS[collection_name])
        ]
        query_embedding = self.embedder.embed_query(query) if eligible_collections else None

        def retrieve(collection_name: str) -> tuple[str, list[RetrievedChunk]]:
            return collection_name, self.retrieve_single(
                query,
                collection_name,
                top_k,
                query_embedding=query_embedding,
            )

        with ThreadPoolExecutor(max_workers=len(eligible_collections) or 1) as executor:
            results = dict(executor.map(retrieve, eligible_collections))

        return {
            COLLECTION_RECOMMENDATIONS: results.get(COLLECTION_RECOMMENDATIONS, []),
            COLLECTION_SAFETY_LABELS: results.get(COLLECTION_SAFETY_LABELS, []),
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
"""
Cross-encoder reranking — an optional final pass applied after BM25 +
semantic score fusion in HybridRetriever.

Why this is a separate step from fusion: BM25 and bi-encoder embeddings both
score the query and each chunk INDEPENDENTLY, then compare the two scores
afterward. A cross-encoder instead feeds the (query, chunk) pair into a
single model together, which captures interactions between them that
independent scoring can't — this is particularly valuable for compound
clinical queries where relevance depends on a specific combination of
conditions (e.g. a chunk must relate to BOTH age and bleeding risk, not just
one of the two topically).

Trade-off: cross-encoders are slower per-item than the fusion step, so this
only runs over a bounded candidate pool (config.RERANK_POOL_SIZE), not the
full corpus.

Runs locally via sentence-transformers.CrossEncoder — no API dependency,
same reasoning as the local embedding model choice (demo reliability).
"""

from functools import lru_cache

from config import RERANKER_MODEL


@lru_cache(maxsize=1)
def _load_reranker():
    from sentence_transformers import CrossEncoder

    return CrossEncoder(RERANKER_MODEL)


def rerank(query: str, candidates: list, top_k: int) -> list:
    """
    candidates: list of RetrievedChunk objects (from hybrid_retriever),
        already fused and sorted by combined_score.
    Returns the same objects, re-ordered by rerank_score (mutated in place
        on each object) and truncated to top_k.

    If candidates is empty, returns an empty list without loading the model
    (avoids an unnecessary model load on a guaranteed-empty result set).
    """
    if not candidates:
        return []

    model = _load_reranker()
    pairs = [(query, c.text) for c in candidates]
    scores = model.predict(pairs)  # raw cross-encoder logits; higher = more relevant

    for chunk, score in zip(candidates, scores):
        chunk.rerank_score = float(score)

    reranked = sorted(candidates, key=lambda c: c.rerank_score, reverse=True)
    return reranked[:top_k]

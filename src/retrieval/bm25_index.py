"""
BM25 keyword index, built per Chroma collection.

Rebuilt in-memory from the collection's stored documents whenever a
HybridRetriever needs it — fine at this corpus size (a few hundred chunks
across 4 PDFs). If the corpus grows significantly, persist the tokenized
corpus to disk instead of rebuilding on every process start.

BM25 exists alongside semantic search specifically because drug names and
numeric thresholds ("70 years old", "12% risk") are exactly what pure
embedding similarity tends to under-match.
"""

import re
from dataclasses import dataclass

from rank_bm25 import BM25Okapi

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


@dataclass
class BM25CollectionIndex:
    chunk_ids: list[str]
    documents: list[str]
    metadatas: list[dict]
    bm25: BM25Okapi | None

    @classmethod
    def from_chroma_collection(cls, collection) -> "BM25CollectionIndex":
        data = collection.get(include=["documents", "metadatas"])
        chunk_ids = data["ids"]
        documents = data["documents"]
        metadatas = data["metadatas"]

        tokenized_corpus = [_tokenize(doc) for doc in documents]
        bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None

        return cls(chunk_ids=chunk_ids, documents=documents, metadatas=metadatas, bm25=bm25)

    def search(self, query: str, top_k: int) -> list[tuple[str, float, str, dict]]:
        """Returns (chunk_id, raw_bm25_score, text, metadata) tuples, ranked
        descending, excluding zero-score results (which are just noise in
        the candidate pool, not genuine matches)."""
        if not self.bm25 or not self.chunk_ids:
            return []

        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [
            (self.chunk_ids[i], float(scores[i]), self.documents[i], self.metadatas[i])
            for i in ranked_indices
            if scores[i] > 0
        ]

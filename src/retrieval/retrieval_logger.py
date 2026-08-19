"""
Logs every retrieval call to a JSONL file.

This satisfies two hackathon requirements at once:
- "Log retrieval scores" (Day 2 end-of-day outcome)
- Feeds the Day 4 evaluation (Retrieval Precision@k, manual review of
  ambiguous/refusal cases) without needing to re-run queries later.

Append-only by design — never overwritten, so you accumulate a real usage
log across all of Day 2-5 testing.
"""

import json
from datetime import datetime, timezone

from config import PROCESSED_DIR
from src.retrieval.hybrid_retriever import RetrievedChunk

LOG_PATH = PROCESSED_DIR / "retrieval_logs.jsonl"


def log_retrieval(query: str, results: dict[str, list[RetrievedChunk]]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "results": {
            collection_name: [
                {
                    "chunk_id": c.chunk_id,
                    "document_name": c.metadata.get("document_name"),
                    "section_title": c.metadata.get("section_title"),
                    "page_numbers": c.metadata.get("page_numbers"),
                    "semantic_score": c.semantic_score,
                    "bm25_score": c.bm25_score,
                    "combined_score": c.combined_score,
                }
                for c in chunks
            ]
            for collection_name, chunks in results.items()
        },
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

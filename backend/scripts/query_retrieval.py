#!/usr/bin/env python3
"""
Day 2 CLI: run a query against the hybrid retrieval layer and display
retrieved chunks with their scores — no LLM call, no generation. This is
for manually verifying retrieval quality (and tuning HYBRID_ALPHA / TOP_K_DEFAULT
in config.py) before wiring up Day 3 generation.

Usage:
    python scripts/query_retrieval.py "Can a 70-year-old on atorvastatin start aspirin?"
    python scripts/query_retrieval.py "What are the contraindications for atorvastatin?" --top_k 3
    python scripts/query_retrieval.py "What's the metformin dose for diabetes?"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import TOP_K_DEFAULT
from backend.src.retrieval.hybrid_retriever import HybridRetriever
from backend.src.retrieval.retrieval_logger import log_retrieval


def main():
    parser = argparse.ArgumentParser(description="Query the hybrid retrieval layer.")
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--top_k", type=int, default=TOP_K_DEFAULT)
    args = parser.parse_args()

    retriever = HybridRetriever()
    results = retriever.retrieve_compound(args.query, top_k=args.top_k)

    print(f"\nQuery: {args.query}\n")
    for collection_name, chunks in results.items():
        print(f"--- {collection_name} ({len(chunks)} results) ---")
        if not chunks:
            print("  (no results — collection may be empty, or nothing matched)")
        for c in chunks:
            doc = c.metadata.get("document_name", "?")
            section = c.metadata.get("section_title", "?")
            pages = c.metadata.get("page_numbers", "?")
            rerank_str = f"  rerank={c.rerank_score:.3f}" if c.rerank_score is not None else ""
            print(f"  [combined={c.combined_score:.3f}]  (semantic={c.semantic_score:.3f}  bm25={c.bm25_score:.3f}{rerank_str})")
            print(f"    {doc} — {section} (p.{pages})")
            preview = c.text[:160].replace("\n", " ")
            print(f"    \"{preview}...\"")
        print()

    log_retrieval(args.query, results)
    print("Logged to data/processed/retrieval_logs.jsonl")


if __name__ == "__main__":
    main()
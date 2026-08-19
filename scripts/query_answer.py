#!/usr/bin/env python3
"""
Day 3 CLI: run a query through the full pipeline — hybrid retrieval, then
grounded generation — and print the structured, cited answer (or refusal).

Requires ANTHROPIC_API_KEY or OPENAI_API_KEY set in .env, matching whichever
GENERATION_BACKEND is set in config.py, and requires the model name
placeholders in config.py to be filled in with a real model you have access to.

Usage:
    python scripts/query_answer.py "Can a 70-year-old on atorvastatin start aspirin?"
    python scripts/query_answer.py "What's the metformin dose for diabetes?"   # refusal case
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

from config import TOP_K_DEFAULT
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.retrieval_logger import log_retrieval
from src.generation.generator import generate_answer, format_answer_for_display


def main():
    parser = argparse.ArgumentParser(description="Run a query through retrieval + generation.")
    parser.add_argument("query", type=str, help="Natural language query")
    parser.add_argument("--top_k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument(
        "--show-chunks", action="store_true",
        help="Also print the raw retrieved chunks before the generated answer."
    )
    args = parser.parse_args()

    retriever = HybridRetriever()
    results = retriever.retrieve_compound(args.query, top_k=args.top_k)
    log_retrieval(args.query, results)

    if args.show_chunks:
        print("\n=== Retrieved chunks ===")
        for collection_name, chunks in results.items():
            print(f"\n-- {collection_name} --")
            for c in chunks:
                print(f"  [{c.chunk_id}] combined={c.combined_score:.3f} "
                      f"{c.metadata.get('section_title')} (p.{c.metadata.get('page_numbers')})")

    print(f"\n=== Query ===\n{args.query}")

    answer = generate_answer(args.query, results)

    print("\n=== Answer ===")
    print(format_answer_for_display(answer))


if __name__ == "__main__":
    main()

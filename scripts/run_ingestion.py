#!/usr/bin/env python3
"""
CLI entrypoint for Day 1 ingestion.

Usage:
    python scripts/run_ingestion.py
    python scripts/run_ingestion.py --report   # verbose per-document + collection report
"""

import argparse
import sys
from pathlib import Path

# Allow running as `python scripts/run_ingestion.py` from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.ingest import run_ingestion, print_report


def main():
    parser = argparse.ArgumentParser(description="Run the Day 1 ingestion pipeline.")
    parser.add_argument(
        "--report", action="store_true",
        help="Print a detailed per-document and per-collection report after ingestion."
    )
    args = parser.parse_args()

    summary = run_ingestion()

    if args.report:
        print_report(summary)
    else:
        total_chunks = sum(s["count"] for s in summary["collection_stats"])
        print(f"\nIngestion complete. {total_chunks} total chunks indexed across "
              f"{len(summary['collection_stats'])} collections.")
        if summary["warnings"]:
            print(f"{len(summary['warnings'])} warning(s) — rerun with --report for details.")


if __name__ == "__main__":
    main()

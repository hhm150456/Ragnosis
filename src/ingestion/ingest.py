"""
Day 1 ingestion orchestrator.

For each document in config.CORPUS:
  1. Parse PDF into per-page text (pdf_parser)
  2. Apply section-aware chunking based on source_type (chunker)
  3. Build metadata for every chunk (metadata)
  4. Embed all chunk texts (embeddings.Embedder)
  5. Store into the correct Chroma collection (vectorstore.ChromaStore)

Also writes a human-readable audit log to data/processed/chunks_audit.json
so chunk boundaries and metadata can be manually spot-checked before Day 2
retrieval tuning — this is the fastest way to catch a bad chunking rule
before it quietly hurts your Retrieval Precision score.
"""

import json
from pathlib import Path

from tqdm import tqdm

from config import CORPUS, RAW_DIR, PROCESSED_DIR
from src.ingestion.pdf_parser import extract_pages
from src.ingestion.chunker import chunk_document
from src.ingestion.metadata import build_chunk_metadata
from src.embeddings.embedder import Embedder
from src.vectorstore.chroma_store import ChromaStore


def run_ingestion() -> dict:
    """Runs the full ingestion pipeline. Returns a summary dict used by
    scripts/run_ingestion.py --report."""

    store = ChromaStore()
    embedder = Embedder()

    # Group corpus entries by target collection so each collection is rebuilt
    # exactly once, then populated by all documents assigned to it.
    collections_needed = {doc["collection"] for doc in CORPUS}
    chroma_collections = {name: store.rebuild_collection(name) for name in collections_needed}

    audit_log: list[dict] = []
    summary = {"documents": [], "warnings": []}

    for doc_config in CORPUS:
        pdf_path = RAW_DIR / doc_config["filename"]
        print(f"\n--- Ingesting {doc_config['document_name']} ({doc_config['filename']}) ---")

        try:
            pages = extract_pages(pdf_path)
        except FileNotFoundError as e:
            msg = str(e)
            print(f"[SKIPPED] {msg}")
            summary["warnings"].append(msg)
            continue

        chunks = chunk_document(pages, doc_config["source_type"])

        fallback_count = sum(1 for c in chunks if c.fallback_chunking_used)
        if fallback_count:
            warning = (
                f"{doc_config['filename']}: {fallback_count}/{len(chunks)} chunks used "
                f"fallback length-based chunking (no section header matched). "
                f"Review USPSTF_SECTION_HEADERS / DAILYMED_SECTION_PATTERN in config.py."
            )
            print(f"[WARNING] {warning}")
            summary["warnings"].append(warning)

        ids, embeddings_input, documents, metadatas = [], [], [], []

        for i, chunk in enumerate(chunks):
            meta = build_chunk_metadata(
                chunk=chunk,
                document_name=doc_config["document_name"],
                source_type=doc_config["source_type"],
                doc_config=doc_config,
                chunk_index=i,
            )
            chunk_id = f"{doc_config['filename']}::chunk_{i}"

            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append(meta)
            audit_log.append({"chunk_id": chunk_id, "metadata": meta, "text_preview": chunk.text[:300]})

        print(f"  {len(chunks)} chunks produced. Embedding...")
        embeddings_input = embedder.embed_texts(documents)

        target_collection = chroma_collections[doc_config["collection"]]
        store.add_chunks(
            collection=target_collection,
            ids=ids,
            embeddings=embeddings_input,
            documents=documents,
            metadatas=metadatas,
        )
        print(f"  Stored into collection '{doc_config['collection']}'.")

        summary["documents"].append(
            {
                "filename": doc_config["filename"],
                "document_name": doc_config["document_name"],
                "collection": doc_config["collection"],
                "chunk_count": len(chunks),
                "fallback_chunk_count": fallback_count,
            }
        )

    audit_path = PROCESSED_DIR / "chunks_audit.json"
    audit_path.write_text(json.dumps(audit_log, indent=2))
    print(f"\nAudit log written to {audit_path}")

    summary["collection_stats"] = [store.collection_stats(name) for name in collections_needed]
    return summary


def print_report(summary: dict) -> None:
    print("\n=== Ingestion Report ===")
    for doc in summary["documents"]:
        flag = f"  [!] {doc['fallback_chunk_count']} fallback chunks" if doc["fallback_chunk_count"] else ""
        print(f"- {doc['document_name']}: {doc['chunk_count']} chunks -> '{doc['collection']}'{flag}")

    print("\nCollection totals:")
    for stat in summary["collection_stats"]:
        print(f"- {stat['name']}: {stat['count']} chunks")

    if summary["warnings"]:
        print("\nWarnings:")
        for w in summary["warnings"]:
            print(f"- {w}")
    else:
        print("\nNo warnings.")

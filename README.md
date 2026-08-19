# Clinical RAG — Contraindication & Drug-Interaction Checker

A Retrieval-Augmented Generation system for aspirin/statin preventive-medication
eligibility (USPSTF) and atorvastatin drug safety (DailyMed), with strict grounding,
transparent citations, and refusal on out-of-scope queries.

## Repo Structure

```
clinical-rag/
├── README.md
├── requirements.txt
├── .env.example
├── config.py                     # corpus config: file paths, source_type mapping, chunking rules
│
├── data/
│   ├── raw/                      # put source PDFs here (see config.py for expected filenames)
│   └── processed/                # output of ingestion: chunked JSON + logs (gitignored)
│
├── src/
│   ├── ingestion/
│   │   ├── pdf_parser.py         # PyMuPDF text+layout extraction, per-page
│   │   ├── chunker.py            # section-aware chunking (USPSTF vs DailyMed rules)
│   │   ├── metadata.py           # builds per-chunk metadata dict
│   │   └── ingest.py             # orchestrates parse -> chunk -> embed -> store
│   │
│   ├── embeddings/
│   │   └── embedder.py           # local embedding model wrapper (bge-small-en-v1.5)
│   │
│   ├── vectorstore/
│   │   └── chroma_store.py       # two Chroma collections: recommendations / safety_labels
│   │
│   ├── retrieval/                # Day 2 — hybrid BM25 + semantic retrieval
│   ├── generation/                # Day 3 — grounded generation + citation formatting
│   └── safety/                    # Day 4 — confidence threshold + faithfulness check
│
├── eval/
│   └── test_queries.json         # labeled eval set (in-scope / ambiguous / out-of-domain)
│
├── app/
│   └── streamlit_app.py          # Day 5 demo UI (placeholder)
│
└── scripts/
    └── run_ingestion.py          # CLI entrypoint for Day 1
```

## Day 1 Quickstart

1. Place the three source PDFs into `data/raw/` using the filenames listed in `config.py`:
   - `uspstf_aspirin.pdf`
   - `uspstf_statin.pdf`
   - `dailymed_atorvastatin.pdf`

2. Install dependencies:
   ```bash
   pip install -r requirements.txt --break-system-packages
   ```

3. Run ingestion:
   ```bash
   python scripts/run_ingestion.py
   ```

   This will:
   - Parse each PDF page-by-page with PyMuPDF
   - Apply section-aware chunking rules based on `source_type` (recommendation vs drug_label)
   - Attach metadata (document_name, source_type, section_title, page_number, evidence_grade / label_version)
   - Embed each chunk locally with `bge-small-en-v1.5`
   - Store into two separate persistent Chroma collections: `recommendations` and `safety_labels`
   - Write a chunk audit log to `data/processed/chunks_audit.json` so you can manually verify
     chunk boundaries and metadata before Day 2 retrieval tuning

4. Sanity check the output:
   ```bash
   python scripts/run_ingestion.py --report
   ```
   Prints chunk counts per collection, per source document, and flags any chunk with
   missing page/section metadata (these should be fixed before Day 2).

## Design Notes

- **Two collections, not one.** USPSTF recommendation PDFs and DailyMed FDA labels have
  different internal structure, so they get different chunking rules and are queried/reasoned
  about separately by the generation layer later (see project problem statement).
- **Local embeddings by default.** `bge-small-en-v1.5` runs fully offline via
  `sentence-transformers` — no API dependency for retrieval, which matters for demo reliability
  on Day 5. Swap to OpenAI `text-embedding-3-small` in `config.py` if you want to compare quality.
- **Everything is re-runnable and idempotent.** Re-running ingestion clears and rebuilds the
  named collections rather than appending duplicates.

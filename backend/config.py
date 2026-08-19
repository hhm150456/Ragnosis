"""
Central configuration for the Clinical RAG ingestion pipeline.

This is the single source of truth for:
- the fixed document corpus (per the project's Scope of Work — do not silently
  add documents here without updating Scope_of_Work.md)
- which vector collection each document belongs to
- the section-header patterns used for section-aware chunking
- embedding backend selection
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CHROMA_PERSIST_DIR = BASE_DIR / "data" / "chroma_db"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Vector collections
# ---------------------------------------------------------------------------
COLLECTION_RECOMMENDATIONS = "recommendations"   # USPSTF-style guidance docs
COLLECTION_SAFETY_LABELS = "safety_labels"       # DailyMed / FDA label docs

# ---------------------------------------------------------------------------
# Fixed corpus definition
# ---------------------------------------------------------------------------
# source_type drives which chunker + which Chroma collection a document goes into.
# "recommendation" -> section headers like Recommendation Summary / Rationale / etc.
# "drug_label"      -> numbered FDA label sections (4, 5, 7, ...)
#
# evidence_grade is attached at the document level here as a default; if a single
# PDF contains multiple graded recommendations (e.g. separate grades per age band),
# refine per-chunk in chunker.py rather than relying solely on this default.

# NOTE: "filename" is a path RELATIVE TO data/raw/ — it may include subfolders,
# e.g. "Guidelines/aspirin-use-cvd-prevention-clinician-summary.pdf". Forward
# slashes work fine on Windows too since these are joined with pathlib.
CORPUS = [
    {
        "filename": "Guidelines/aspirin-use-cvd-prevention-clinician-summary.pdf",
        "document_name": "USPSTF Aspirin Use to Prevent Cardiovascular Disease (2022)",
        "source_type": "recommendation",
        "collection": COLLECTION_RECOMMENDATIONS,
        "default_evidence_grade": None,  # aspirin recommendation varies by age band; leave
                                          # None here and let chunker extract grade per section
    },
    {
        # TODO CONFIRM: filename/subfolder not yet verified against actual disk layout
        "filename": "Guidelines/statin-use-cvd-prevention-clinician-summary.pdf",
        "document_name": "USPSTF Statin Use for Primary Prevention of CVD (2022)",
        "source_type": "recommendation",
        "collection": COLLECTION_RECOMMENDATIONS,
        "default_evidence_grade": None,
    },
    {
        # TODO CONFIRM: filename/subfolder not yet verified against actual disk layout
        "filename": "MedicalLabels/atorvastatin-calcium-label.pdf",
        "document_name": "DailyMed Atorvastatin Calcium Label",
        "source_type": "drug_label",
        "collection": COLLECTION_SAFETY_LABELS,
        "label_version": "UNVERIFIED — set this explicitly once you confirm the label date",
    },
    {
        # TODO CONFIRM: filename/subfolder not yet verified against actual disk layout
        "filename": "MedicalLabels/atorvastatin-calcium-tablet-Nucare.pdf",
        "document_name": "NuCare Atorvastatin Calcium Label",
        "source_type": "drug_label",
        "collection": COLLECTION_SAFETY_LABELS,
        "label_version": "UNVERIFIED — set this explicitly once you confirm the label date",
    },
]

# ---------------------------------------------------------------------------
# Section-aware chunking rules
# ---------------------------------------------------------------------------
# USPSTF documents follow a fairly consistent set of top-level headers.
# These are matched case-insensitively, at the start of a line, to split text
# into sections before any further sub-chunking by length.
USPSTF_SECTION_HEADERS = [
    "Recommendation Summary",
    "Rationale",
    "Risk Assessment",
    "Screening Tests",
    "Screening or Treatment",
    "Preventive Medication",
    "Balance of Benefits and Harms",
    "Clinical Considerations",
    "Other Considerations",
    "Practice Considerations",
    "Response to Public Comment",
    "Update of Previous Recommendations",
    "Discussion",
]

# FDA drug labels use numbered top-level sections. Matched by regex on the
# leading number token (e.g. "4 CONTRAINDICATIONS", "5.1 ...", "7 DRUG INTERACTIONS").
DAILYMED_SECTION_PATTERN = r"^\s*(\d{1,2}(?:\.\d+)?)\s+([A-Z][A-Z \-/]{3,})\s*$"

# Sections we especially care about for the safety layer — used to flag chunks
# at ingestion time so retrieval/generation can prioritize them.
DAILYMED_PRIORITY_SECTIONS = {
    "4": "CONTRAINDICATIONS",
    "5": "WARNINGS AND PRECAUTIONS",
    "7": "DRUG INTERACTIONS",
    "8": "USE IN SPECIFIC POPULATIONS",
}

# Fallback chunking (used within a section if it's too long, or if no section
# headers are detected at all — flagged in the audit log when this triggers).
MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP_CHARS = 150

# ---------------------------------------------------------------------------
# Embedding backend
# ---------------------------------------------------------------------------
# "local"  -> sentence-transformers, fully offline, recommended for demo reliability
# "openai" -> text-embedding-3-small, requires OPENAI_API_KEY, hosted only
EMBEDDING_BACKEND = "local"
LOCAL_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"

TOP_K_DEFAULT = 4
HYBRID_ALPHA = 0.4
GENERATION_BACKEND = "gemini"
GENERATION_MODEL_ANTHROPIC = "REPLACE_WITH_YOUR_MODEL"   # e.g. check console.anthropic.com/docs
GENERATION_MODEL_OPENAI = "REPLACE_WITH_YOUR_MODEL"       # e.g. check platform.openai.com/docs
GENERATION_MODEL_GEMINI = "gemini-3.5-flash-lite"        # e.g. check ai.google.dev/gemini-api/docs/models

GENERATION_TEMPERATURE = 0.0   # deterministic, minimizes drift from grounded text
GENERATION_MAX_TOKENS = 1500
HF_TOKEN = ""
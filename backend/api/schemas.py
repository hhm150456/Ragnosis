"""
Pydantic request/response schemas for the Ragnosis API.

These sit on top of (and translate) the dataclasses already defined deeper in
the backend:
- backend.src.retrieval.hybrid_retriever.RetrievedChunk
- backend.src.generation.response_parser.{StructuredAnswer, Recommendation, Citation}

Keeping them as separate Pydantic models (rather than reusing the dataclasses
directly as FastAPI response models) means the HTTP contract can evolve
independently of the internal retrieval/generation data shapes, and gives us
automatic request validation + OpenAPI docs for free.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class QueryRequest(BaseModel):
    """Body for POST /analyze."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The clinician's natural-language question.",
        examples=["Can a 68-year-old on atorvastatin start daily aspirin?"],
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description=(
            "Chunks to retrieve per collection. Defaults to config.TOP_K_DEFAULT "
            "when omitted."
        ),
    )


# ---------------------------------------------------------------------------
# Shared / nested response pieces
# ---------------------------------------------------------------------------


class CitationOut(BaseModel):
    """Mirrors backend.src.generation.response_parser.Citation."""

    chunk_id: str
    document_name: str
    section_title: str
    page_numbers: str
    source_type: str


class RecommendationOut(BaseModel):
    """Mirrors backend.src.generation.response_parser.Recommendation."""

    claim: str
    excerpt: str
    evidence_grade: str | None = None
    faithfulness_status: Literal["verified", "unverified"] = "unverified"
    verification_reason: str | None = None
    citation: CitationOut


class RetrievedChunkOut(BaseModel):
    """
    Transparency/debug view of a single retrieved chunk, independent of
    whether the model ended up citing it in a recommendation. Lets the
    frontend show "what was retrieved" (RetrievalTrace / SourceCard) even
    for chunks that didn't make it into the final grounded answer.
    """

    chunk_id: str
    collection: str
    document_name: str
    section_title: str
    page_numbers: str
    text: str
    semantic_score: float
    bm25_score: float
    combined_score: float
    rerank_score: float | None = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

AnswerStatus = Literal["answered", "partial_refusal", "full_refusal", "parse_error"]


class AnalyzeResponse(BaseModel):
    """Body returned by POST /api/query."""

    query: str
    status: AnswerStatus
    answer_summary: str
    refusal_reason: str | None = None
    recommendations: list[RecommendationOut] = Field(default_factory=list)
    dropped_claim_count: int = 0
    retrieved_chunks: list[RetrievedChunkOut] = Field(default_factory=list)
    low_confidence: bool = Field(
        default=False,
        description=(
            "True if the safety confidence gate (src/safety/confidence.py) "
            "short-circuited before a generation call was made."
        ),
    )


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    detail: str | None = None


class ErrorResponse(BaseModel):
    """Standard error body. FastAPI's HTTPException already serializes to
    {"detail": ...}, this model just documents that shape in the OpenAPI schema."""

    detail: str


# ---------------------------------------------------------------------------
# GET /api/sources
# ---------------------------------------------------------------------------


class SourceOut(BaseModel):
    """One entry from config.CORPUS, the fixed document list."""

    document_name: str
    source_type: str  # "recommendation" | "drug_label", per config.CORPUS
    collection: str
    filename: str
    evidence_grade: str | None = None
    label_version: str | None = None


class SourcesResponse(BaseModel):
    sources: list[SourceOut]
    collection_counts: dict[str, int | None] = Field(
        default_factory=dict,
        description="Live chunk count per collection from Supabase. None if unavailable.",
    )


# ---------------------------------------------------------------------------
# GET /api/evaluation, POST /api/evaluation/run
# ---------------------------------------------------------------------------

ExpectedBehavior = Literal["answer", "refuse"]


class EvalCategoryOut(BaseModel):
    """One category from eval/test_queries.json."""

    id: str
    title: str
    description: str
    expected_behavior: ExpectedBehavior
    query_count: int
    example_queries: list[str]


class EvalOutcomeCount(BaseModel):
    """One bar in the frontend's Query Outcomes chart."""

    name: Literal["Supported", "Correct Refusal", "Incorrect Refusal", "Unsupported Answer"]
    count: int


class EvalMetricOut(BaseModel):
    id: str
    label: str
    value: str
    description: str


class EvaluationResponse(BaseModel):
    total_queries: int
    categories: list[EvalCategoryOut]
    evaluated: bool = Field(
        description="False until POST /api/evaluation/run has produced at least one result."
    )
    outcomes: list[EvalOutcomeCount] = Field(default_factory=list)
    metrics: list[EvalMetricOut] = Field(default_factory=list)
    note: str = ""

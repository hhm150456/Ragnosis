"""
FastAPI entrypoint for the Ragnosis Clinical RAG API.

Run from the repository root with:

    .venv/Scripts/python.exe -m uvicorn backend.api.main:app --reload --port 8000

Endpoints:

    GET  /health              readiness check (also verifies the retriever
                               can be constructed, i.e. Supabase env vars
                               are present)
    POST /api/query           retrieval + safety gate + generation
                               (backend/api/routes/query.py)
    GET  /api/sources         corpus document list, for Sources.tsx
                               (backend/api/routes/sources.py)
    GET  /api/evaluation      labeled eval set summary + last live-run
                               results, for Evaluation.tsx
    POST /api/evaluation/run  actually executes the eval set
                               (backend/api/routes/evaluation.py)

Note on imports: the rest of this codebase mixes two import styles —
`backend.src.foo` (assumes the *repository root* is on sys.path) and
`from config import ...` (assumes the *backend/* directory itself is on
sys.path). Rather than touching every existing module, we add both
directories to sys.path here, once, before importing anything that depends
on them, so this app runs correctly regardless of the working directory it's
launched from. This must run before any local imports below.
"""

from __future__ import annotations

import logging
import os
import re
import sys
from pathlib import Path

_API_DIR = Path(__file__).resolve().parent          # backend/api
_BACKEND_DIR = _API_DIR.parent                       # backend
_REPO_ROOT = _BACKEND_DIR.parent                     # repo root

for _path in (str(_REPO_ROOT), str(_BACKEND_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.deps import get_retriever  # noqa: E402 (path setup must run first)
from backend.api.routes import evaluation, query, sources  # noqa: E402
from backend.api.schemas import HealthResponse  # noqa: E402

logger = logging.getLogger("ragnosis.api")


def _cors_origins() -> list[str]:
    configured = os.getenv("FRONTEND_URLS", os.getenv("FRONTEND_URL", ""))
    origins = {
        origin.strip().rstrip("/")
        for origin in configured.split(",")
        if origin.strip()
    }
    origins.update({"http://localhost:5173", "http://127.0.0.1:5173"})
    return sorted(origins)

app = FastAPI(
    title="Ragnosis Clinical RAG API",
    description=(
        "Grounded aspirin/statin eligibility and atorvastatin safety Q&A, "
        "backed by USPSTF recommendations and DailyMed drug labels."
    ),
    version="0.2.0",
)

# FRONTEND_URLS accepts a comma-separated list so preview and production
# frontends can share one backend deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_origin_regex=r"https://[A-Za-z0-9-]+(?:\.up)?\.railway\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api")
app.include_router(sources.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Ragnosis Clinical RAG API",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        get_retriever()
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller, not swallowed
        logger.warning("Health check: retriever unavailable: %s", exc)
        return HealthResponse(status="degraded", detail=str(exc))
    return HealthResponse(status="ok")

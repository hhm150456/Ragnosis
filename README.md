# Ragnosis

Clinical evidence assistant for preventive-care eligibility and drug-safety questions.

This repository combines a Python FastAPI backend with a React + Vite frontend to provide grounded answers over a curated clinical corpus. The app is designed around evidence-backed responses for aspirin/statin preventive medication questions and atorvastatin safety queries, with retrieval transparency and refusals when confidence is too low.

## What this repo contains

- Backend API in `backend/`
- Clinical retrieval, generation, and safety logic in `backend/src/`
- Frontend dashboard and evidence UI in `frontend/src/`
- Ingestion and evaluation assets in `backend/data/` and `backend/eval/`
- Supabase schema in `backend/sql/schema.sql`

## High-level architecture

- `backend/api/main.py` exposes the FastAPI app and CORS setup
- `backend/api/routes/query.py` handles the main evidence query pipeline
- `backend/api/routes/sources.py` returns corpus metadata for the Sources page
- `backend/api/routes/evaluation.py` runs and returns evaluation summaries
- `backend/src/retrieval/` contains hybrid retrieval logic (BM25 + semantic)
- `backend/src/generation/` handles the LLM response and grounding validation
- `backend/src/safety/` filters low-confidence or invalid queries before generation
- `frontend/` is the React interface for dashboard, evidence review, sources, and evaluation

## Repository structure

```text
Ragnosis/
├── README.md
├── backend/
│   ├── api/
│   │   ├── deps.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── routes/
│   │       ├── evaluation.py
│   │       ├── query.py
│   │       └── sources.py
│   ├── config.py
│   ├── requirements.txt
│   ├── scripts/
│   │   ├── query_answer.py
│   │   ├── query_retrieval.py
│   │   └── run_ingestion.py
│   ├── sql/
│   │   └── schema.sql
│   └── src/
│       ├── embeddings/
│       ├── generation/
│       ├── ingestion/
│       ├── retrieval/
│       ├── safety/
│       └── vectorstore/
│   ├── data/
│   │   ├── chroma_db/
│   │   ├── processed/
│   │   └── raw/
│   └── eval/
│       └── test_queries.json
├── frontend/
│   ├── package.json
│   ├── src/
│   ├── vite.config.ts
│   └── ...
└── .gitignore
```

## Core capabilities

- Query a curated clinical corpus with hybrid retrieval
- Combine evidence from recommendation and safety-label sources
- Refuse unsupported or low-confidence queries
- Show retrieved chunks and source context to the user
- Display structured evaluation and evidence coverage in the UI

## Prerequisites

Before running the app locally, make sure you have:

- Python 3.11+
- Node.js 18+
- A Supabase project configured for vector storage
- A valid LLM provider API key (Gemini, OpenAI, or Anthropic), depending on your selected generation backend

## Environment setup

Create a `.env` file in the backend directory with the variables required by the project. The app reads configuration from `backend/config.py`, which loads environment variables via `python-dotenv`.

At minimum, expected values include:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# choose the generation backend you want to use
GENERATION_BACKEND=gemini
GEMINI_API_KEY=your_gemini_key

# optional if you are using OpenAI or Anthropic instead
# OPENAI_API_KEY=your_openai_key
# ANTHROPIC_API_KEY=your_anthropic_key
```

For the retrieval/vector pipeline, make sure the schema in `backend/sql/schema.sql` has already been run in your Supabase SQL editor and that the tables match the collection names configured in `backend/config.py`.

## Backend setup

From the repository root, create the virtual environment in `.venv`:

```bash
python -m venv .venv
source .venv/bin/activate       # macOS/Linux
\.\.venv\Scripts\Activate.ps1 # Windows PowerShell

pip install -r backend/requirements.txt
```

Start the API:

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

The app will be available at:

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Frontend setup

From the repo root:

```bash
cd frontend
npm install
npm run dev
```

The frontend typically runs at:

- http://localhost:5173

If the backend is not on the default host/port, create `frontend/.env.local` with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Railway deployment

Deploy the backend and frontend as two Railway services from this repository.
For the backend, set the service root directory to `backend/` and select
`Dockerfile` as the builder file. Alternatively, leave Railpack enabled and
use the root `Procfile` from a repository-root service.
The backend start command is:

```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

For the frontend, use the repository root as the service root directory and
set the Dockerfile path to `frontend/Dockerfile`:

- Frontend: `frontend/Dockerfile`

Set these backend variables in Railway:

```env
GENERATION_BACKEND=gemini
GEMINI_API_KEY=your_gemini_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FRONTEND_URL=https://your-frontend-service.up.railway.app
```

Set this frontend variable before deploying or redeploying the frontend:

```env
VITE_API_BASE_URL=https://your-backend-service.up.railway.app
```

Railway injects `PORT` automatically. The backend listens on it, and the
frontend container serves its production bundle through Nginx on port 80.

## Recommended workflow

1. Configure Supabase and `backend/.env` values
2. Run the SQL schema setup in `backend/sql/schema.sql`
3. Start the backend API
4. Start the frontend dev server
5. Test the query flow in the UI and inspect retrieval/transparency data

## Ingestion and evaluation

The backend includes scripts for ingestion and retrieval testing.

Run ingestion:

```bash
cd backend
python scripts/run_ingestion.py
```

Run a retrieval-only sanity check:

```bash
cd backend
python scripts/query_retrieval.py
```

Run an answer-generation check:

```bash
cd backend
python scripts/query_answer.py
```

The evaluation suite is located at `backend/eval/test_queries.json` and is used by the `/api/evaluation` endpoints.

## Frontend checks

Run these commands from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run build
```

## Notes on the current implementation

- The project uses a fixed clinical corpus defined in `backend/config.py`; source PDFs belong under `backend/data/raw/`
- Retrieval is split across recommendation and safety-label collections
- The backend intentionally blocks low-confidence or invalid inputs before generation
- The frontend is built to surface evidence, citations, and coverage for transparency

## Troubleshooting

If the app does not start correctly, check the following:

- `.env` values are present and loaded correctly
- Supabase variables match your project
- The SQL schema was applied to Supabase
- The selected LLM provider key is valid
- The frontend is pointing to the correct backend URL

## License

This project is intended for internal research and clinical evidence tooling. Use the code according to your project requirements and applicable licensing constraints.

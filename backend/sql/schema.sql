-- Clinical RAG — Supabase schema
-- Run this once in the Supabase SQL Editor (Project -> SQL Editor -> New query).
--
-- Mirrors the two-collection design from the Chroma version: two tables,
-- one per evidence type, rather than one table with a filter column. This
-- keeps the same architectural guarantee — a compound query always gets
-- results from BOTH tables independently, never a single pooled search
-- that might return only one evidence type.
--
-- IMPORTANT: vector(384) matches BAAI/bge-small-en-v1.5's output dimension
-- (the default local embedding model in config.py). If you switch
-- EMBEDDING_BACKEND to "openai" (text-embedding-3-small, 1536 dims), you
-- must change vector(384) to vector(1536) below BEFORE ingesting anything —
-- pgvector enforces a fixed dimension per column and mixed dimensions will
-- fail on insert.

create extension if not exists vector;

-- ---------------------------------------------------------------------
-- Table 1: recommendations (USPSTF aspirin + statin chunks)
-- ---------------------------------------------------------------------
create table if not exists recommendations_chunks (
    id             text primary key,       -- chunk_id, e.g. "uspstf_aspirin.pdf::chunk_3"
    document_name  text not null,
    section_title  text,
    page_numbers   text,
    content        text not null,
    metadata       jsonb,                   -- full metadata dict (evidence_grade, etc.)
    embedding      vector(384) not null,
    created_at     timestamptz default now()
);

create index if not exists recommendations_chunks_embedding_idx
    on recommendations_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ---------------------------------------------------------------------
-- Table 2: safety_labels (DailyMed atorvastatin label chunks)
-- ---------------------------------------------------------------------
create table if not exists safety_labels_chunks (
    id             text primary key,
    document_name  text not null,
    section_title  text,
    page_numbers   text,
    content        text not null,
    metadata       jsonb,                   -- full metadata dict (section_number, label_version, etc.)
    embedding      vector(384) not null,
    created_at     timestamptz default now()
);

create index if not exists safety_labels_chunks_embedding_idx
    on safety_labels_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- ---------------------------------------------------------------------
-- Similarity search functions (cosine distance via pgvector's <=> operator)
-- Called via supabase-py's .rpc(...) from the retrieval layer.
-- ---------------------------------------------------------------------
create or replace function match_recommendations(
    query_embedding vector(384),
    match_count int default 10
)
returns table (
    id text,
    document_name text,
    section_title text,
    page_numbers text,
    content text,
    metadata jsonb,
    similarity float
)
language sql stable
as $$
    select
        id,
        document_name,
        section_title,
        page_numbers,
        content,
        metadata,
        1 - (embedding <=> query_embedding) as similarity
    from recommendations_chunks
    order by embedding <=> query_embedding
    limit match_count;
$$;

create or replace function match_safety_labels(
    query_embedding vector(384),
    match_count int default 10
)
returns table (
    id text,
    document_name text,
    section_title text,
    page_numbers text,
    content text,
    metadata jsonb,
    similarity float
)
language sql stable
as $$
    select
        id,
        document_name,
        section_title,
        page_numbers,
        content,
        metadata,
        1 - (embedding <=> query_embedding) as similarity
    from safety_labels_chunks
    order by embedding <=> query_embedding
    limit match_count;
$$;

-- ---------------------------------------------------------------------
-- Row Level Security
-- ---------------------------------------------------------------------
-- Ingestion runs with the service_role key (bypasses RLS) from your local
-- machine / CI, never from a browser — so these tables stay locked down to
-- anon/authenticated clients by default. If your Day 5 demo app queries
-- Supabase directly from client-side code, add a read-only policy instead
-- of disabling RLS entirely.
alter table recommendations_chunks enable row level security;
alter table safety_labels_chunks enable row level security;

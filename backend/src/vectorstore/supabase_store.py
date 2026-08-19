"""
Supabase (Postgres + pgvector) vector store wrapper.

Exposes a small, consistent interface (rebuild_collection, add_chunks,
collection_stats) used by the ingestion pipeline and the retrieval layer.

Requires:
- sql/schema.sql already run once in the Supabase SQL Editor
- SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY set in .env

Uses the service_role key deliberately — this client is only ever run from
your local machine or CI for ingestion, never shipped to a browser. Never
put the service_role key in client-side/demo-app code; use the anon key
with a read-only RLS policy there instead.
"""

import os
from functools import lru_cache

from config import SUPABASE_TABLE_BY_COLLECTION


class SupabaseStore:
    def __init__(self):
        self.client = _load_supabase_client()

    def rebuild_collection(self, collection_name: str) -> str:
        """
        Deletes all rows from the table mapped to this collection, then
        returns the table name (used as the 'handle' passed to add_chunks).
        """
        table_name = self._table_name(collection_name)
        # Supabase requires a filter on delete; this matches all rows since
        # every id is a non-empty string chunk_id.
        self.client.table(table_name).delete().neq("id", "").execute()
        return table_name

    def get_collection(self, collection_name: str) -> str:
        """Returns the table name mapped to this collection."""
        return self._table_name(collection_name)

    def add_chunks(
        self,
        collection,  # table name string, as returned by rebuild_collection/get_collection
        ids: list[str],
        embeddings: list[list[float]],
        documents: list[str],
        metadatas: list[dict],
    ):
        table_name = collection
        rows = []
        for chunk_id, embedding, text, meta in zip(ids, embeddings, documents, metadatas):
            rows.append(
                {
                    "id": chunk_id,
                    "document_name": meta.get("document_name"),
                    "section_title": meta.get("section_title"),
                    "page_numbers": meta.get("page_numbers"),
                    "content": text,
                    "metadata": meta,   # full dict preserved as jsonb
                    "embedding": embedding,
                }
            )

        # Batch upserts to avoid oversized single requests on larger PDFs.
        batch_size = 100
        for i in range(0, len(rows), batch_size):
            batch = rows[i : i + batch_size]
            self.client.table(table_name).upsert(batch).execute()

    def collection_stats(self, collection_name: str) -> dict:
        table_name = self._table_name(collection_name)
        result = self.client.table(table_name).select("id", count="exact").execute()
        return {"name": collection_name, "count": result.count}

    @staticmethod
    def _table_name(collection_name: str) -> str:
        table_name = SUPABASE_TABLE_BY_COLLECTION.get(collection_name)
        if not table_name:
            raise ValueError(
                f"No Supabase table mapped for collection '{collection_name}'. "
                f"Check config.SUPABASE_TABLE_BY_COLLECTION."
            )
        return table_name


@lru_cache(maxsize=1)
def _load_supabase_client():
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise EnvironmentError(
            "VECTORSTORE_BACKEND is 'supabase' but SUPABASE_URL and/or "
            "SUPABASE_SERVICE_ROLE_KEY are not set. Set both in your .env file. "
            "Find them in Supabase dashboard -> Project Settings -> API."
        )
    return create_client(url, key)

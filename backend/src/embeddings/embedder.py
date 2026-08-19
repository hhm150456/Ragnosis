"""
Embedding backend wrapper.

Default is a local sentence-transformers model (bge-small-en-v1.5) — fully
offline, no API keys, chosen specifically for demo reliability on Day 5 so
retrieval never depends on external API uptime.

Set EMBEDDING_BACKEND = "openai" in config.py to switch to text-embedding-3-small
if you want to compare quality; that path requires OPENAI_API_KEY.
"""

from functools import lru_cache

from config import EMBEDDING_BACKEND, LOCAL_EMBEDDING_MODEL, OPENAI_EMBEDDING_MODEL


class Embedder:
    def __init__(self, backend: str = EMBEDDING_BACKEND):
        self.backend = backend
        if backend == "local":
            self._model = _load_local_model()
        elif backend == "openai":
            self._client = _load_openai_client()
        else:
            raise ValueError(f"Unknown EMBEDDING_BACKEND: {backend}")

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.backend == "local":
            # bge models recommend a retrieval-oriented prefix for passages
            # vs. queries; here we're embedding passages (chunks).
            embeddings = self._model.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            )
            return [e.tolist() for e in embeddings]
        else:
            response = self._client.embeddings.create(
                model=OPENAI_EMBEDDING_MODEL, input=texts
            )
            return [item.embedding for item in response.data]

    def embed_query(self, query: str) -> list[float]:
        if self.backend == "local":
            # bge models benefit from a query instruction prefix
            prefixed = f"Represent this sentence for searching relevant passages: {query}"
            embedding = self._model.encode(
                [prefixed], normalize_embeddings=True, show_progress_bar=False
            )[0]
            return embedding.tolist()
        else:
            return self.embed_texts([query])[0]


@lru_cache(maxsize=1)
def _load_local_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(LOCAL_EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def _load_openai_client():
    import os
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "EMBEDDING_BACKEND is 'openai' but OPENAI_API_KEY is not set. "
            "Set it in your .env, or switch config.EMBEDDING_BACKEND to 'local'."
        )
    return OpenAI(api_key=api_key)

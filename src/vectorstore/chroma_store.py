"""
Persistent Chroma vector store wrapper.

Manages exactly two collections per the project's dual-collection architecture:
- recommendations  (USPSTF)
- safety_labels    (DailyMed)

Ingestion is idempotent: rebuild_collection() clears an existing collection
before repopulating, so re-running ingestion never produces duplicate chunks.
"""

import chromadb

from config import CHROMA_PERSIST_DIR


class ChromaStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))

    def rebuild_collection(self, name: str):
        """Delete the collection if it exists, then recreate it empty."""
        try:
            self.client.delete_collection(name)
        except Exception:
            pass  # didn't exist yet — fine
        return self.client.create_collection(name=name, metadata={"hnsw:space": "cosine"})

    def get_collection(self, name: str):
        return self.client.get_collection(name)

    @staticmethod
    def add_chunks(collection, ids: list[str], embeddings: list[list[float]],
                    documents: list[str], metadatas: list[dict]):
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def collection_stats(self, name: str) -> dict:
        collection = self.get_collection(name)
        return {"name": name, "count": collection.count()}

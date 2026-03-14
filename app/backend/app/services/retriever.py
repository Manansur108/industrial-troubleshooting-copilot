from __future__ import annotations

from app.backend.app.services.vector_store import LocalVectorStore


def retrieve_relevant_chunks(question: str, top_k: int = 5) -> list[dict]:
    store = LocalVectorStore()
    return store.search(question, top_k=top_k)

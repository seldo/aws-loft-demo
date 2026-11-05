from __future__ import annotations

import os
from pathlib import Path

import chromadb

# The index is built into the container image at build time (see
# index_products.py and the Dockerfile), so there's no Chroma server to run.
CHROMA_PATH = os.environ.get(
    "CHROMA_PATH", str(Path(__file__).parent.parent / "chroma-index")
)
COLLECTION_NAME = "products"

_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def get_products_collection():
    try:
        return _get_client().get_collection(name=COLLECTION_NAME)
    except Exception as e:
        print(f"ChromaDB unavailable, falling back to keyword search: {e}")
        return None


def vector_search(
    query: str,
    n_results: int = 20,
    where: dict | None = None,
) -> list[str] | None:
    collection = get_products_collection()
    if collection is None:
        return None

    try:
        kwargs: dict = {"query_texts": [query], "n_results": n_results}
        if where:
            kwargs["where"] = where
        results = collection.query(**kwargs)
        return results["ids"][0] if results["ids"] else []
    except Exception as e:
        print(f"ChromaDB query failed, falling back to keyword search: {e}")
        return None

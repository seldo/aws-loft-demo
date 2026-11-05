"""
Index all products into an embedded ChromaDB for vector search.

Runs at image build time, so the index (and Chroma's embedding model) ship
inside the container.

Usage:
  python -m agent.index_products
"""

import json
from pathlib import Path

from agent.chroma_client import CHROMA_PATH, COLLECTION_NAME, _get_client

BATCH_SIZE = 50


def main():
    data_path = Path(__file__).parent / "products.json"
    products = json.loads(data_path.read_text())

    print(f"Building ChromaDB index at {CHROMA_PATH}...")
    client = _get_client()

    # Delete and recreate collection for a clean index
    try:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing '{COLLECTION_NAME}' collection")
    except Exception:
        pass  # Collection doesn't exist yet

    collection = client.create_collection(name=COLLECTION_NAME)

    ids = []
    documents = []
    metadatas = []

    for p in products:
        ids.append(p["id"])

        doc = "\n\n".join(
            [
                p["name"],
                p["description"],
                p["marketingCopy"],
                f"Category: {p['category']}",
                f"Keywords: {', '.join(p['keywords'])}",
                f"Manufacturer: {p['manufacturer']}",
                f"Ages {p['ageRange']['min']} to {p['ageRange']['max']}",
            ]
        )
        documents.append(doc)

        metadatas.append(
            {
                "category": p["category"],
                "ageMin": p["ageRange"]["min"],
                "ageMax": p["ageRange"]["max"],
                "price": p["price"],
                "inStock": p["inventory"] > 0,
                "manufacturer": p["manufacturer"],
            }
        )

    total = len(ids)
    for i in range(0, total, BATCH_SIZE):
        end = min(i + BATCH_SIZE, total)
        collection.add(
            ids=ids[i:end],
            documents=documents[i:end],
            metadatas=metadatas[i:end],
        )
        print(f"Indexed products {i + 1}–{end} of {total}")

    print(f"\nDone! {total} products indexed in ChromaDB.")


if __name__ == "__main__":
    main()

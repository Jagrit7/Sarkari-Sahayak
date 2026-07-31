"""
ingest.py — one-time (or whenever-the-dataset-changes) ingestion script.

Loads all schemes from schemes_rebuilt.jsonl and writes them into Qdrant
via QdrantVectorStore.from_documents(), which creates the collection AND
embeds/uploads the documents in one call. Also creates the payload indexes
that filters.py's Qdrant filters require — Qdrant doesn't auto-index
payload fields just because a filter references them. Not part of the
live pipeline — run this manually, not on every call.
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_qdrant import QdrantVectorStore, RetrievalMode

from voice.retrieval.embeddings import embeddings, sparse_embeddings
from voice.retrieval.loader import loader

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "sarkari-schemes-voice"


def main():
    print("Loading documents from schemes_rebuilt.jsonl...")
    docs = loader.load()
    print(f"Loaded {len(docs)} documents.")

    print("Embedding and uploading to Qdrant (this creates the collection if it doesn't exist)...")
    QdrantVectorStore.from_documents(
        docs,
        embedding=embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        collection_name=COLLECTION_NAME,
        vector_name="dense",
        sparse_vector_name="bm25",
    )
    print(f"Ingested {len(docs)} documents into '{COLLECTION_NAME}'.")

    print("Creating payload indexes for filterable fields...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.government_level",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="metadata.target_state",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    print("Indexes created.")

    print("Done.")


if __name__ == "__main__":
    main()




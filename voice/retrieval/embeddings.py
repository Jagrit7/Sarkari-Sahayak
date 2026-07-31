"""
embeddings.py — Cloudflare BGE-M3 dense embeddings + BM25 sparse embeddings
for the voice retriever. Both get passed to QdrantVectorStore.
"""

import os
from dotenv import load_dotenv
from langchain_cloudflare.embeddings import CloudflareWorkersAIEmbeddings
from langchain_qdrant import FastEmbedSparse

load_dotenv()

cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")

embeddings = CloudflareWorkersAIEmbeddings(
    account_id=cloudflare_account_id,
    api_token=cloudflare_api_token,
    model_name="@cf/baai/bge-large-en-v1.5",
)

sparse_embeddings = FastEmbedSparse(model_name="Qdrant/bm25")
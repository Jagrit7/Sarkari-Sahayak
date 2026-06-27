"""
common.py — shared config + embedding helpers for Sarkari Sahayak.

Secrets come from environment variables so nothing is hardcoded:
    export QDRANT_URL="https://xxxx.cloud.qdrant.io:6333"
    export QDRANT_API_KEY="..."
Optional overrides:
    export QDRANT_COLLECTION="sarkari_schemes"
    export OLLAMA_URL="http://localhost:11434"
    export DENSE_MODEL="bge-m3:567m-fp16"
    export SCHEMES_JSONL="schemes_rebuilt.jsonl"
"""

import os
import time
import uuid

import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

# Load a .env file (this directory or any parent) into the environment BEFORE the reads below.
# Every script imports `common`, so this one call makes all of them pick up your .env.
load_dotenv()

# ---- config ----
QDRANT_URL     = os.environ.get("QDRANT_URL", "")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
COLLECTION     = os.environ.get("QDRANT_COLLECTION", "sarkari_schemes")
OLLAMA_URL     = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
DENSE_MODEL    = os.environ.get("DENSE_MODEL", "bge-m3:567m-fp16")
SPARSE_MODEL   = "Qdrant/bm25"          # BM25 via FastEmbed; IDF applied server-side
DENSE_DIM      = 1024                   # BGE-M3 dense dimension
DENSE_VEC      = "dense"                # named-vector keys in the collection
SPARSE_VEC     = "bm25"
SCHEMES_JSONL  = os.environ.get("SCHEMES_JSONL", "schemes_rebuilt.jsonl")
PROGRESS_FILE  = os.environ.get("PROGRESS_FILE", "ingest_progress.txt")
NUM_CTX        = 8192                   # use BGE-M3's full context window

# stable namespace so scheme_id -> the same Qdrant point id every run (idempotent upserts)
_NS = uuid.UUID("a1b2c3d4-e5f6-4a5b-8c7d-000000000001")


def require_env():
    if not QDRANT_URL or not QDRANT_API_KEY:
        raise SystemExit(
            "Missing QDRANT_URL / QDRANT_API_KEY.\n"
            "  export QDRANT_URL='https://<your-cluster>.cloud.qdrant.io:6333'\n"
            "  export QDRANT_API_KEY='<your-api-key>'"
        )


def get_client() -> QdrantClient:
    require_env()
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120, cloud_inference=True)


def point_id(scheme_id: str) -> str:
    """Deterministic Qdrant point id from the (string) scheme_id."""
    return str(uuid.uuid5(_NS, scheme_id))


# ---- dense embeddings via local Ollama (bge-m3) ----
def ollama_embed(texts, retries: int = 3):
    """Embed a list of texts with the local Ollama BGE-M3 model. Returns list[list[float]]."""
    if isinstance(texts, str):
        texts = [texts]
    payload = {"model": DENSE_MODEL, "input": texts, "options": {"num_ctx": NUM_CTX}}
    last = None
    for attempt in range(retries):
        try:
            r = requests.post(f"{OLLAMA_URL}/api/embed", json=payload, timeout=600)
            r.raise_for_status()
            embs = r.json().get("embeddings")
            if not embs or len(embs) != len(texts):
                raise RuntimeError(f"Ollama returned {len(embs) if embs else 0} embeddings for {len(texts)} inputs")
            return embs
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Ollama embedding failed after {retries} tries: {last}")


# ---- sparse BM25 via FastEmbed (local, deterministic; same vectors Qdrant produces server-side) ----
_bm25 = None


def _get_bm25():
    global _bm25
    if _bm25 is None:
        from fastembed import SparseTextEmbedding
        _bm25 = SparseTextEmbedding(model_name=SPARSE_MODEL)
    return _bm25


def bm25_embed(texts):
    """Return list[models.SparseVector] for the given texts."""
    if isinstance(texts, str):
        texts = [texts]
    out = []
    for emb in _get_bm25().embed(list(texts)):
        out.append(models.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist()))
    return out

CF_ACCOUNT_ID = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
CF_API_TOKEN  = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CF_EMBED_MODEL = os.environ.get("CF_EMBED_MODEL", "@cf/baai/bge-m3")
CF_EMBED_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/v1/embeddings"

def cloudflare_embed(texts, retries: int = 3):
    if isinstance(texts, str):
        texts = [texts]
    if not CF_ACCOUNT_ID or not CF_API_TOKEN:
        raise SystemExit("Missing CLOUDFLARE_ACCOUNT_ID / CLOUDFLARE_API_TOKEN.")
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    out = []
    for text in texts:
        snippet = (text or " ")[:20000]      # one request per scheme; cap length to stay under CF's limit
        last = None
        for attempt in range(retries):
            try:
                r = requests.post(CF_EMBED_URL, headers=headers,
                                  json={"model": CF_EMBED_MODEL, "input": [snippet]}, timeout=30)
                r.raise_for_status()
                out.append(r.json()["data"][0]["embedding"])
                break
            except Exception as e:
                last = e
                time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"Cloudflare embedding failed after {retries} tries: {last}")
    return out

def embed_query(text):
    return cloudflare_embed(text)[0]

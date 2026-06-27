# Sarkari Sahayak — Qdrant ingestion (Step 1)

Loads the cleaned scheme dataset into a Qdrant Cloud collection set up for **hybrid retrieval**:
**BGE-M3 dense** (local, via Ollama) + **BM25 sparse** (IDF maintained server-side) + metadata payload, fused with RRF at query time.

## Prerequisites

1. **Qdrant Cloud free cluster** — create one, then grab its URL and API key.
2. **Ollama with BGE-M3** (full F16):
   ```bash
   ollama pull bge-m3:567m-fp16
   ```
3. **Your data file** — put `schemes_rebuilt.jsonl` in this folder (or point `SCHEMES_JSONL` at it).
4. **Python deps:**
   ```bash
   pip install -r requirements.txt
   ```

## Configure (.env file)

Create a `.env` file in this folder. The scripts load it automatically (via `python-dotenv`):

```dotenv
QDRANT_URL=https://<your-cluster>.cloud.qdrant.io:6333
QDRANT_API_KEY=<your-api-key>
# optional overrides (defaults shown):
# QDRANT_COLLECTION=sarkari_schemes
# OLLAMA_URL=http://localhost:11434
# DENSE_MODEL=bge-m3:567m-fp16
# SCHEMES_JSONL=schemes_rebuilt.jsonl
```

Only `QDRANT_URL` and `QDRANT_API_KEY` are required; the rest have working defaults.

## Run (in order)

```bash
python create_collection.py     # 1) create the hybrid collection + payload indexes
python ingest.py                # 2) embed + upsert all schemes (resumable)
python query.py                 # 3) smoke-test hybrid retrieval
```

Single query with a filter:
```bash
python query.py -q "housing scheme for rural families" --state "Bihar"
python query.py -q "startup loan" --level Central
```

## Resumability

`ingest.py` checkpoints to `ingest_progress.txt` after every successful batch.
If it's interrupted (network, laptop sleep, Ctrl-C), just run `python ingest.py` again —
it skips everything already done and never re-embeds it. To start over: `python ingest.py --reset-progress`.

## How the pieces fit

- **Dense** vectors are computed by you (Ollama BGE-M3) and sent to Qdrant. 1024-dim, cosine.
  Cosine distance absorbs any normalization difference between local Ollama and the incremental API later.
- **Sparse** vectors here are produced by FastEmbed BM25 locally (fine for the one-time bulk).
  The collection's **IDF modifier** means Qdrant maintains corpus statistics server-side, so when you
  add new schemes later via Qdrant's server-side BM25, they stay consistent with this bulk load.
- **Payload** holds every scheme field except `embedding_text` (which is just a concat of the others).
  Filters use only the trustworthy fields: `government_level`, `scheme_category_*`, `target_state`,
  `language`, `is_active`.

## Next steps (not in this folder yet)

- Incremental refresh job (new/changed schemes) using `content_hash` for change detection,
  with dense via the BGE-M3 **API** and sparse via Qdrant **server-side** BM25.
- Wire `hybrid_search()` into the pipecat voice agent as a retrieval tool.

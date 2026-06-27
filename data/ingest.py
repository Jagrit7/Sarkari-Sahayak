"""
ingest.py — bulk-load schemes_rebuilt.jsonl into Qdrant (RESUMABLE).

For each scheme:
  * dense  = Ollama BGE-M3 over `embedding_text`        (you compute it; sent as the vector)
  * sparse = FastEmbed BM25 over `embedding_text`        (local; IDF applied server-side)
  * payload = all scheme fields EXCEPT `embedding_text`  (it's just a concat of the others)

Resumability:
  After each chunk is upserted, the scheme_ids are appended to PROGRESS_FILE.
  Re-running skips anything already in that file — no re-embedding. Safe to Ctrl-C and rerun.
  Upserts are idempotent (deterministic point ids), so a partial chunk can't corrupt anything.

    python ingest.py                 # ingest everything not yet done
    python ingest.py --chunk 16      # tune batch size (default 16)
    python ingest.py --reset-progress # forget progress and re-ingest all
"""

import argparse
import json
import os

from qdrant_client import models

from common import (
    COLLECTION, DENSE_VEC, SPARSE_VEC, PROGRESS_FILE, SCHEMES_JSONL,
    cloudflare_embed, get_client, point_id,
)


def load_schemes(path):
    if not os.path.exists(path):
        raise SystemExit(f"Cannot find {path}. Set SCHEMES_JSONL or place the file next to this script.")
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_done(path):
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as f:
        return {ln.strip() for ln in f if ln.strip()}


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=16, help="schemes embedded+upserted per batch")
    ap.add_argument("--reset-progress", action="store_true", help="ignore + clear the progress file")
    args = ap.parse_args()

    if args.reset_progress and os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("Cleared progress file.")

    client = get_client()
    if not client.collection_exists(COLLECTION):
        raise SystemExit(f"Collection '{COLLECTION}' does not exist. Run create_collection.py first.")

    schemes = load_schemes(SCHEMES_JSONL)
    done = load_done(PROGRESS_FILE)
    todo = [s for s in schemes if s.get("scheme_id") not in done]

    print(f"Total schemes: {len(schemes)} | already done: {len(done)} | to ingest: {len(todo)}")
    if not todo:
        print("Nothing to do — ingestion already complete.")
        return

    ingested = len(done)
    total = len(schemes)
    with open(PROGRESS_FILE, "a", encoding="utf-8") as prog:
        for chunk in chunks(todo, args.chunk):
            texts = [s.get("embedding_text", "") for s in chunk]
            dense_vecs = cloudflare_embed(texts)

            points = []
            for scheme, dvec, txt in zip(chunk, dense_vecs, texts):
                payload = {k: v for k, v in scheme.items() if k != "embedding_text"}
                points.append(models.PointStruct(
                    id=point_id(scheme["scheme_id"]),
                    vector={DENSE_VEC: dvec,
                            SPARSE_VEC: models.Document(text=txt, model="qdrant/bm25")},
                    payload=payload,
                ))

            client.upsert(collection_name=COLLECTION, points=points, wait=True)

            for scheme in chunk:                       # checkpoint AFTER a successful upsert
                prog.write(scheme["scheme_id"] + "\n")
            prog.flush()

            ingested += len(chunk)
            print(f"  ingested {ingested}/{total}", flush=True)

    print("Bulk ingestion complete.")


if __name__ == "__main__":
    main()

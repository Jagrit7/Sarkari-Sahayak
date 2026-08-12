import sys
import time

import requests

from voice.retrieval.loader import load_files
from voice.retrieval.vectorstore import get_vectorstore

# add_documents() embeds THEN upserts — for the whole list at once, that means
# nothing lands in Weaviate until every embedding call succeeds. Chunking bounds
# a single 429 (or any failure) to CHUNK_SIZE docs instead of the entire dataset.
CHUNK_SIZE = 200
MAX_RETRIES = 5
INITIAL_BACKOFF_SECS = 30
PROGRESS_FILE = "/app/data/ingest_progress.txt"  # must be on a mounted volume to survive `--rm`


def _load_progress():
    try:
        return int(open(PROGRESS_FILE).read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _save_progress(n):
    with open(PROGRESS_FILE, "w") as f:
        f.write(str(n))


def _add_with_retry(vectorstore, batch):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            vectorstore.add_documents(batch)
            return
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 429 and attempt < MAX_RETRIES:
                wait = INITIAL_BACKOFF_SECS * attempt
                print(f"  Rate/quota limited (429). Retrying in {wait}s (attempt {attempt}/{MAX_RETRIES})...")
                time.sleep(wait)
                continue
            raise


def pipeline(reset_progress=False):
    if reset_progress:
        _save_progress(0)

    print("Loading documents from schemes_compact_cleaned_merged_chunked.csv...")
    docs = load_files()
    print(f"Loaded {len(docs)} documents.")

    vectorstore = get_vectorstore()  # creates the collection on first successful write

    start = _load_progress()
    if start:
        print(f"Resuming from checkpoint: {start}/{len(docs)} already ingested.")

    # Track distinct schemes seen so far so a 429 tells you exactly which scheme
    # it died on, not just a chunk count. Pre-seed with anything before the
    # resume point so a resumed run doesn't re-print/re-count old schemes.
    seen_schemes = {doc.metadata.get("scheme_name") for doc in docs[:start]}

    for i in range(start, len(docs), CHUNK_SIZE):
        batch = docs[i : i + CHUNK_SIZE]
        _add_with_retry(vectorstore, batch)
        _save_progress(i + len(batch))

        for doc in batch:
            name = doc.metadata.get("scheme_name")
            if name not in seen_schemes:
                seen_schemes.add(name)
                print(f"  [{len(seen_schemes)}] ingested: {name}")

    print(f"Done. {len(seen_schemes)} schemes, {len(docs)} chunks ingested.")


if __name__ == "__main__":
    pipeline(reset_progress="--reset-progress" in sys.argv)



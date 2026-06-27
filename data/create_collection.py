"""
create_collection.py — create the hybrid collection (run once).

Dense vector : 1024-dim, cosine  (BGE-M3, you provide the vectors)
Sparse vector: BM25 with IDF modifier (IDF maintained server-side as the corpus grows)
Payload indexes: only the fields that are clean/trustworthy to filter on.

    python create_collection.py            # create (errors if it already exists)
    python create_collection.py --recreate # drop and recreate (wipes data!)
"""

import argparse

from qdrant_client import models

from common import COLLECTION, DENSE_DIM, DENSE_VEC, SPARSE_VEC, get_client

# field_name -> payload schema. Keyword for exact/array match, bool for flags.
PAYLOAD_INDEXES = {
    "government_level":        models.PayloadSchemaType.KEYWORD,
    "scheme_category_primary": models.PayloadSchemaType.KEYWORD,
    "scheme_category_list":    models.PayloadSchemaType.KEYWORD,  # array of strings
    "target_state":            models.PayloadSchemaType.KEYWORD,
    "language":                models.PayloadSchemaType.KEYWORD,
    "is_active":               models.PayloadSchemaType.BOOL,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--recreate", action="store_true", help="drop and recreate (DELETES all data)")
    args = ap.parse_args()

    client = get_client()

    if args.recreate and client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
        print(f"Deleted existing collection '{COLLECTION}'.")

    if client.collection_exists(COLLECTION):
        raise SystemExit(f"Collection '{COLLECTION}' already exists. Use --recreate to replace it.")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config={
            DENSE_VEC: models.VectorParams(size=DENSE_DIM, distance=models.Distance.COSINE),
        },
        sparse_vectors_config={
            # IDF modifier => Qdrant computes/maintains inverse-document-frequency on its side,
            # so incremental adds stay correct as the corpus grows.
            SPARSE_VEC: models.SparseVectorParams(modifier=models.Modifier.IDF),
        },
    )
    print(f"Created collection '{COLLECTION}' (dense={DENSE_DIM}d cosine, sparse=BM25/IDF).")

    for field, schema in PAYLOAD_INDEXES.items():
        client.create_payload_index(COLLECTION, field_name=field, field_schema=schema)
        print(f"  indexed payload field: {field}")

    print("Collection ready.")


if __name__ == "__main__":
    main()

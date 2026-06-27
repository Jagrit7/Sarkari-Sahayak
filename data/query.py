"""
query.py — hybrid retrieval (dense + BM25 -> RRF) with optional metadata filters.

`hybrid_search(...)` is the function your pipecat agent calls as a tool.
Running this file directly executes a few smoke-test queries to verify the index.

    python query.py
"""

import argparse

from qdrant_client import models

from common import COLLECTION, DENSE_VEC, SPARSE_VEC, embed_query, get_client

_client = None


def client():
    global _client
    if _client is None:
        _client = get_client()
    return _client


def build_filter(government_level=None, state=None, category=None, active_only=True):
    """Compose a Qdrant payload filter from the trustworthy fields. Returns None if empty."""
    must = []
    if active_only:
        must.append(models.FieldCondition(key="is_active", match=models.MatchValue(value=True)))
    if government_level:
        must.append(models.FieldCondition(key="government_level", match=models.MatchValue(value=government_level)))
    if state:
        # match schemes scoped to this state OR nationwide
        must.append(models.FieldCondition(key="target_state", match=models.MatchAny(any=[state, "All India"])))
    if category:
        must.append(models.FieldCondition(key="scheme_category_list", match=models.MatchValue(value=category)))
    return models.Filter(must=must) if must else None


def hybrid_search(query_text, top_k=5, prefetch_k=40, query_filter=None):
    """
    Dense (BGE-M3) + sparse (BM25) retrieval fused with Reciprocal Rank Fusion,
    optionally narrowed by a metadata filter. Returns a list of ScoredPoint.
    """

    dense_q = embed_query(query_text)

    res = client().query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(query=dense_q, using=DENSE_VEC, limit=prefetch_k, filter=query_filter),
            models.Prefetch(query=models.Document(text=query_text, model="qdrant/bm25"),
                            using=SPARSE_VEC, limit=prefetch_k, filter=query_filter),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
        with_payload=True,
    )
    return res.points


def _show(points):
    for i, p in enumerate(points, 1):
        pl = p.payload or {}
        print(f"  {i}. [{p.score:.4f}] {pl.get('scheme_name', '?')}")
        print(f"      {pl.get('government_level', '?')} | {pl.get('target_state', '?')} | {pl.get('scheme_category_primary', '?')}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-q", "--query", help="run a single query")
    ap.add_argument("--state", help="restrict to a state (plus All-India schemes)")
    ap.add_argument("--level", choices=["Central", "State"], help="restrict to Central or State")
    args = ap.parse_args()

    if args.query:
        f = build_filter(government_level=args.level, state=args.state)
        _show(hybrid_search(args.query, query_filter=f))
        return

    # smoke tests
    tests = [
        ("scholarship for disabled students", None),
        ("financial help for farmers after crop loss", build_filter(government_level="Central")),
        ("pension scheme for widows", None),
    ]
    for q, f in tests:
        print(f"\nQUERY: {q}" + (f"  [filtered]" if f else ""))
        _show(hybrid_search(q, query_filter=f))


if __name__ == "__main__":
    main()

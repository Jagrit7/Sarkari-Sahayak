from weaviate.classes.query import Filter
from voice.retrieval.vectorstore import get_vectorstore
from voice.retrieval.reranker import rerank
import time

vectorstore = get_vectorstore()


def search_schemes(query, k=3, candidate_k=15, government_level=None, return_latency=False):
    filters = (
        Filter.by_property("government_level").equal(government_level)
        if government_level
        else None
    )

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )
    t1 = time.perf_counter()

    docs = rerank(query, candidates, top_k=k)
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency
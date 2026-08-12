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

    # rerank the FULL candidate pool (not just top k), since the same scheme can
    # appear as multiple section-chunks and we need enough ranked depth to dedupe
    # down to k distinct schemes without losing a genuinely correct one.
    reranked = rerank(query, candidates, top_k=candidate_k) if candidates else []

    seen_schemes = set()
    docs = []
    for doc in reranked:
        scheme_id = doc.metadata.get("scheme_id")
        if scheme_id in seen_schemes:
            continue
        seen_schemes.add(scheme_id)
        docs.append(doc)
        if len(docs) == k:
            break
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency


def check_eligibility(query,scheme_name, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (

            Filter.by_property("scheme_id").equal(scheme_id)
            & Filter.by_property("section").equal("eligibility")
            & Filter.by_property("scheme_name").equal(scheme_name)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )

    t1 = time.perf_counter()
    docs = rerank(query, candidates, top_k=k) if candidates else []
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency


def check_documents(query, scheme_name, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (
            Filter.by_property("scheme_id").equal(scheme_id)
            & Filter.by_property("section").equal("documents")
            & Filter.by_property("scheme_name").equal(scheme_name)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )

    t1 = time.perf_counter()
    docs = rerank(query, candidates, top_k=k) if candidates else []
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency

def check_benefits(query, scheme_name, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (
            Filter.by_property("scheme_id").equal(scheme_id)
            & Filter.by_property("section").equal("benefits")
            & Filter.by_property("scheme_name").equal(scheme_name)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )

    t1 = time.perf_counter()
    docs = rerank(query, candidates, top_k=k) if candidates else []
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency

def check_application_process(query, scheme_name, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (
            Filter.by_property("scheme_id").equal(scheme_id)
            & Filter.by_property("section").equal("application")
            & Filter.by_property("scheme_name").equal(scheme_name)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )

    t1 = time.perf_counter()
    docs = rerank(query, candidates, top_k=k) if candidates else []
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency

def check_scheme_details(query, scheme_name, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (
            Filter.by_property("scheme_id").equal(scheme_id)
            & Filter.by_property("section").equal("details")
            & Filter.by_property("scheme_name").equal(scheme_name)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    candidates = vectorstore.similarity_search(
        query,
        k=candidate_k,
        alpha=0.6,
        filters=filters,
        query_properties=["sparse_text"],
    )

    t1 = time.perf_counter()
    docs = rerank(query, candidates, top_k=k) if candidates else []
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency
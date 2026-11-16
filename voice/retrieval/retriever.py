from langchain_core.documents import Document
from weaviate.classes.query import Filter
from voice.retrieval.embeddings import embeddings
from voice.retrieval.vectorstore import INDEX_NAME, TEXT_KEY, get_vectorstore
from voice.retrieval.reranker import rerank
import time

ALPHA = 0.6  # hybrid weight: 1.0 = vector only, 0.0 = keywords only; re-tune with the multilingual eval

vectorstore = get_vectorstore()
collection = vectorstore._client.collections.get(INDEX_NAME)


def search_schemes(query, k=3, candidate_k=15, government_level=None, return_latency=False,
                   original_query=None, alpha=ALPHA):
    filters = (
        Filter.by_property("government_level").equal(government_level)
        if government_level
        else None
    )

    t0 = time.perf_counter()
    # the vector half embeds the caller's own words (bge-m3 is multilingual); the keyword
    # half and the reranker use the English query, because sparse_text is English keywords
    vector = embeddings.embed_query(original_query or query)
    candidates = vectorstore.similarity_search(
        query,
        vector=vector,
        k=candidate_k,
        alpha=alpha,
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


def _to_document(obj):
    props = dict(obj.properties)
    text = props.pop(TEXT_KEY)
    return Document(page_content=text, metadata=props)


def _check_section(section, query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    filters = (
        Filter.by_property("scheme_id").equal(scheme_id)
        & Filter.by_property("section").equal(section)
    )

    if government_level is not None:
        filters &= Filter.by_property("government_level").equal(government_level)

    t0 = time.perf_counter()
    # all but 10 scheme sections are a single chunk, so fetch by filter instead of
    # searching: no embedding call, and nothing to rank (see docs/decision-log.md)
    result = collection.query.fetch_objects(filters=filters, limit=candidate_k)
    candidates = [_to_document(obj) for obj in result.objects]
    t1 = time.perf_counter()
    # only rerank when there's actually more than one chunk to choose from
    docs = rerank(query, candidates, top_k=k) if len(candidates) > 1 else candidates[:k]
    t2 = time.perf_counter()

    if not return_latency:
        return docs

    latency = {
        "embed_and_search_ms": (t1 - t0) * 1000,
        "rerank_ms": (t2 - t1) * 1000,
        "total_ms": (t2 - t0) * 1000,
    }
    return docs, latency


def check_eligibility(query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    return _check_section("eligibility", query, scheme_id, candidate_k, k, government_level, return_latency)


def check_documents(query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    return _check_section("documents", query, scheme_id, candidate_k, k, government_level, return_latency)


def check_benefits(query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    return _check_section("benefits", query, scheme_id, candidate_k, k, government_level, return_latency)


def check_application_process(query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    return _check_section("application", query, scheme_id, candidate_k, k, government_level, return_latency)


def check_scheme_details(query, scheme_id, candidate_k=5, k=1, government_level=None, return_latency=False):
    return _check_section("details", query, scheme_id, candidate_k, k, government_level, return_latency)

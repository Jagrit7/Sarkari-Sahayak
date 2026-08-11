from flashrank import Ranker, RerankRequest

ranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")


def rerank(query: str, docs: list, top_k: int = 3) -> list:
    passages = [
        {"id": i, "text": doc.page_content, "meta": doc.metadata}
        for i, doc in enumerate(docs)
    ]
    request = RerankRequest(query=query, passages=passages)
    results = ranker.rerank(request)

    reranked_docs = []
    for r in results[:top_k]:
        reranked_docs.append(docs[r["id"]])
    return reranked_docs
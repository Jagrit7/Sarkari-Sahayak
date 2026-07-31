from voice.retrieval.vectorstore import vectorstore

def search_schemes(query, k=2):
    docs = vectorstore.similarity_search(query, k=k)
    return docs
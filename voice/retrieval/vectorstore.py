import os
import weaviate
from langchain_weaviate.vectorstores import WeaviateVectorStore
from voice.retrieval.embeddings import embeddings

# bge-m3 vectors; the older bge-large-en-v1.5 collection, "SarkariSchemesVoice",
# is left in Weaviate untouched so you can roll back by switching this name
INDEX_NAME = "SarkariSchemesMultilingual"
TEXT_KEY = "document_text"
FILTER_PROPERTIES = [
    "scheme_id",
    "scheme_name",
    "government_level",
    "section",
    "sparse_text",
]

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")


def get_vectorstore() -> WeaviateVectorStore:
    client = weaviate.connect_to_local(host=WEAVIATE_HOST)

    vectorstore = WeaviateVectorStore(
        client=client,
        index_name=INDEX_NAME,
        text_key=TEXT_KEY,
        embedding=embeddings,
        attributes=FILTER_PROPERTIES,
    )

    return vectorstore
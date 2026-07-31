from langchain_qdrant import QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from voice.retrieval.embeddings import embeddings, sparse_embeddings
from dotenv import load_dotenv
import os

load_dotenv()

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
)

vectorstore = QdrantVectorStore(
    client=client,
    collection_name='sarkari-schemes-voice',
    embedding=embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
    vector_name="dense",
    sparse_embedding=sparse_embeddings,
    sparse_vector_name="bm25",

)
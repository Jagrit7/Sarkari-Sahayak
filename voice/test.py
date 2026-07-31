from dotenv import load_dotenv
import os
from qdrant_client import QdrantClient

load_dotenv()
client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))
info = client.get_collection("sarkari-schemes-voice")
print(info.points_count, info.status)

from voice.retrieval.retriever import search_schemes

docs = search_schemes("scholarship for backward class students in tamil nadu")
for d in docs:
    print(d.metadata["scheme_name"], "-", d.metadata["target_state"])
import os
import cohere
from qdrant_client import QdrantClient
from dotenv import load_dotenv

# Load .env file in local development (Vercel/Render inject env vars automatically)
load_dotenv()

# --- Configuration ---
COHERE_API_KEY = os.environ["COHERE_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "schemes_v2_cohere")

# Initialize Clients
co = cohere.Client(COHERE_API_KEY)
qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, https=True)

def retrieve_schemes(query: str) -> str:
    """
    Embeds the query and searches Qdrant for relevant government schemes.
    """
    try:
        # 1. Embed the incoming Voice AI query
        embed_response = co.embed(
            texts=[query],
            model='embed-multilingual-v3.0',
            input_type='search_query'
        )
        query_vector = embed_response.embeddings[0]

        # 2. Vector Search in Qdrant Cloud
        search_results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=3  # Top 3 most relevant results
        )

        # 3. Format the context for the Groq LLM
        formatted_context = []
        for hit in search_results:
            payload = hit.payload
            formatted_context.append(
                f"Scheme: {payload.get('scheme_name')}\n"
                f"Eligibility: {payload.get('eligibility_criteria')}\n"
                f"Benefits: {payload.get('benefits')}\n"
                f"Process: {payload.get('application_process')}"
            )

        return "\n---\n".join(formatted_context)

    except Exception as e:
        return f"Error retrieving data: {str(e)}"
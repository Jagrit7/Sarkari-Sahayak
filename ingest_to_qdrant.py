import json
import time
import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. CONFIGURATION ---
COHERE_API_KEY = os.environ["COHERE_API_KEY"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "schemes_v2_cohere")


def ingest_data():
    # ... (loading keys from os.getenv) ...

    # 1. CLEAN THE URL
    # If your URL is: https://xxxx-xxxx.aws.cloud.qdrant.io:6333
    # This strip-and-clean ensures the client doesn't get confused
    raw_url = QDRANT_URL.strip()
    clean_url = raw_url.replace("https://", "").replace(":6333", "")

    print(f"🚀 Initializing Cloud Ingestion...")
    print(f"📡 Target Host: {clean_url}")

    co = cohere.Client(COHERE_API_KEY)

    # Use explicit parameters for Cloud
    client = QdrantClient(
        host=clean_url,
        port=6333,
        api_key=QDRANT_API_KEY,
        https=True
    )

    collection_name = "schemes_v2_cohere"

    # 2. MODERN COLLECTION SETUP (Fixes the Deprecation Warning)
    if client.collection_exists(collection_name):
        print(f"🗑️  Collection '{collection_name}' exists. Deleting for a fresh start...")
        client.delete_collection(collection_name)

    print(f"🛠️  Creating collection: {collection_name}...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )

    # ... (rest of your JSON loading and batch logic) ...

    print("📂 Loading master JSON database...")
    with open('data/master_schemes_db.json', 'r', encoding='utf-8') as f:
        schemes = json.load(f)

        # Safe Mode for Trial Keys
        batch_size = 20
        print(f"📡 Safe Mode: Batching {len(schemes)} schemes (20 at a time)...")

        for i in range(0, len(schemes), batch_size):
            batch_schemes = schemes[i: i + batch_size]

            texts_to_embed = []
            for s in batch_schemes:
                rich_text = (
                    f"Scheme Name: {s.get('scheme_name', '')}. "
                    f"Category: {s.get('category', '')}. "
                    f"Description: {s.get('description', '')}. "
                    f"Eligibility: {s.get('eligibility_criteria', '')}. "
                    f"Benefits: {s.get('benefits', '')}. "
                    f"Keywords: {s.get('tags', '')}"
                )
                texts_to_embed.append(rich_text)

            try:
                # Get embeddings from Cohere
                response = co.embed(
                    texts=texts_to_embed,
                    model='embed-multilingual-v3.0',
                    input_type='search_document'
                )

                embeddings = response.embeddings
                points = [
                    PointStruct(id=i + j, vector=embeddings[j], payload=data)
                    for j, data in enumerate(batch_schemes)
                ]

                client.upsert(collection_name=collection_name, points=points)
                print(f"✅ Records {i} to {i + len(batch_schemes)} uploaded.")

                # 🕰️ 2-second cooldown to avoid Trial Rate Limits
                time.sleep(2.0)

            except Exception as e:
                if "429" in str(e):
                    print("⏳ Rate limit hit! Resting for 10 seconds...")
                    time.sleep(10)
                    # Note: For a hackathon, you can just restart the script
                    # or add a retry logic here.
                else:
                    raise e

        embeddings = response.embeddings

        points = []
        for j, scheme_data in enumerate(batch_schemes):
            points.append(
                PointStruct(
                    id=i + j,
                    vector=embeddings[j],
                    payload=scheme_data
                )
            )

        # Upload to Qdrant Cloud
        client.upsert(
            collection_name=collection_name,
            points=points
        )

        print(f"✅ Uploaded records {i} to {i + len(batch_schemes)}...")
        # Free tier: stay safe with the sleep
        time.sleep(0.5)

    print("\n🔥 SUCCESS: SarkariSahayak V2 data is now LIVE on Qdrant Cloud!")


if __name__ == "__main__":
    ingest_data()
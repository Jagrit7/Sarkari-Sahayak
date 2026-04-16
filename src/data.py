import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import uuid

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# If keys exist (Render), use Cloud. If not (Local), use Memory.
if QDRANT_URL and QDRANT_API_KEY:
    qdrant = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
else:
    qdrant = QdrantClient(":memory:")

# 5 Core Schemes (English & Hindi)
SCHEMES = [
    {
        "name": "Ayushman Bharat (PM-JAY)",
        "content": "Health insurance scheme providing up to Rs 5 lakh per family per year for secondary and tertiary care hospitalization. Eligibility: Deprived families listed in SECC 2011 data. Documents required: Aadhaar card, Ration card, Active mobile number. (आयुष्मान भारत: प्रति परिवार 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा। पात्रता: SECC 2011 सूची में शामिल गरीब परिवार। आवश्यक दस्तावेज: आधार कार्ड, राशन कार्ड, मोबाइल नंबर।)"
    },
    {
        "name": "PM Kisan Samman Nidhi",
        "content": "Income support of Rs 6,000 per year to landholding farmer families, paid in three equal installments. Eligibility: Must own cultivable land. Excludes institutional landholders and high-income earners. Documents required: Aadhaar card, Land ownership papers (Khatauni), Bank account details. (पीएम किसान: किसानों को सालाना 6000 रुपये की आर्थिक सहायता। पात्रता: खेती योग्य जमीन के मालिक। आवश्यक दस्तावेज: आधार कार्ड, खतौनी/जमीन के कागज, बैंक खाता।)"
    },
    {
        "name": "PM Awas Yojana (PMAY)",
        "content": "Credit-linked subsidy scheme to provide affordable housing for the urban and rural poor. Eligibility: Must not own a pucca house anywhere in India. Documents required: Aadhaar card, Income certificate, Bank account, Passport size photo. (पीएम आवास योजना: पक्का घर बनाने के लिए सब्सिडी। पात्रता: भारत में कहीं भी अपना पक्का घर नहीं होना चाहिए। आवश्यक दस्तावेज: आधार कार्ड, आय प्रमाण पत्र, बैंक खाता।)"
    },
    {
        "name": "PM Mudra Yojana",
        "content": "Provides loans up to Rs 10 lakh to non-corporate, non-farm small/micro enterprises. Eligibility: Any Indian citizen with a business plan for a non-farm sector income-generating activity. Documents required: Identity proof, Address proof, Business plan, Recent photographs. (पीएम मुद्रा योजना: छोटे व्यवसाय शुरू करने के लिए 10 लाख तक का लोन। पात्रता: गैर-कृषि व्यवसाय योजना वाले भारतीय नागरिक। आवश्यक दस्तावेज: पहचान पत्र, पता प्रमाण, बिजनेस प्लान।)"
    },
    {
        "name": "National Scholarship Portal (NSP)",
        "content": "Centralized platform for various government scholarships for students from minority communities, SC/ST, and low-income families. Eligibility: Varies by specific scholarship, generally requires passing previous exams and meeting income limits. Documents required: Aadhaar card, Income certificate, Previous mark sheets, Bank details. (राष्ट्रीय छात्रवृत्ति पोर्टल: छात्रों के लिए विभिन्न सरकारी स्कॉलरशिप। पात्रता: आय सीमा और पिछली परीक्षाओं के अंक। आवश्यक दस्तावेज: आधार कार्ड, आय प्रमाण पत्र, मार्कशीट, बैंक खाता।)"
    }
]

print("Loading embedding model (this takes a moment on first run)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2", device='cpu')
qdrant = QdrantClient(":memory:")  # Runs fast in-memory for this setup


def init_db():
    """Initializes Qdrant and embeds the schemes if not already done."""
    # Check if collection exists to avoid errors on restart
    try:
        collections = qdrant.get_collections().collections
        exists = any(c.name == "schemes" for c in collections)
        if exists:
            print("Collection already exists, skipping init.")
            return
    except Exception:
        pass

    qdrant.create_collection(
        collection_name="schemes",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    points = []
    for scheme in SCHEMES:
        vector = embedder.encode(scheme["content"]).tolist()
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"name": scheme["name"], "text": scheme["content"]}
            )
        )

    qdrant.upsert(collection_name="schemes", points=points)
    print("Database initialized with 5 schemes.")


def search_schemes(query: str, limit: int = 2) -> str:
    """Searches the vector DB and returns formatted context."""
    query_vector = embedder.encode(query).tolist()
    hits = qdrant.search(collection_name="schemes", query_vector=query_vector, limit=limit)

    context = ""
    for hit in hits:
        context += f"Scheme: {hit.payload['name']}\nDetails: {hit.payload['text']}\n\n"
    return context if context else "No specific scheme found."

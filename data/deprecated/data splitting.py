import pandas as pd
from llama_index.core import Document

print("Loading enriched CSV...")
df = pd.read_csv("schemes_enriched.csv")

documents = []

for index, row in df.iterrows():
    # 1. THE VECTOR TEXT: This is what the embedding model will mathematically analyze
    # We combine the name and eligibility so the semantic search has good context
    core_text = f"Scheme Name: {row['scheme_name']}\nEligibility Details: {row['eligibility']}"

    # 2. THE METADATA PAYLOAD: The exact 12 keys Qwen just extracted for us
    metadata_dict = {
        "target_gender": row['target_gender'],
        "max_income_inr": int(row['max_income_inr']) if pd.notna(row['max_income_inr']) else -1,
        "min_age": int(row['min_age']) if pd.notna(row['min_age']) else -1,
        "target_category": row['target_category'],
        "target_state": row['target_state'],
        # ... add the rest of your 12 keys here
    }

    # 3. PACKAGE IT: Create the LlamaIndex Document
    doc = Document(
        text=core_text,
        metadata=metadata_dict,
        excluded_embed_metadata_keys=list(metadata_dict.keys())
        # CRITICAL: Tells the embedder NOT to embed the metadata tags
    )

    documents.append(doc)

print(f"✅ Successfully packaged {len(documents)} LlamaIndex Documents!")
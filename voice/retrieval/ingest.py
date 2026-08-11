from voice.retrieval.loader import load_files
from voice.retrieval.vectorstore import get_vectorstore


def pipeline():
    print("Loading documents from schemes_compact_cleaned_merged...")
    docs = load_files()
    print(f"Loaded {len(docs)} documents.")

    print("Embedding and uploading to Weaviate (this creates the collection if it doesn't exist)...")
    vectorstore = get_vectorstore()
    vectorstore.add_documents(docs)
    print(f"Ingested {len(docs)} documents into Weaviate.")

    print("Done.")


if __name__ == "__main__":
    pipeline()



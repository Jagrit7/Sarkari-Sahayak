import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader

load_dotenv()

# repo-root data/ by default; set DATA_DIR (e.g. /app/data in a container) to read elsewhere
DATA_DIR = Path(os.getenv("DATA_DIR") or Path(__file__).resolve().parents[2] / "data")

def load_files():
    loader = CSVLoader(
        file_path=DATA_DIR / "schemes_compact_cleaned_merged_chunked.csv",
        content_columns=["document_text"],
        metadata_columns=["scheme_id", "scheme_name", "government_level", "sparse_text", "section"],
        encoding="utf-8",
    )

    return loader.load()



from dotenv import load_dotenv
from langchain_community.document_loaders import CSVLoader

load_dotenv()

def load_files():
    loader = CSVLoader(
        file_path="/app/data/schemes_compact_cleaned_merged.csv",
        content_columns=["document_text"],
        metadata_columns=["scheme_id", "scheme_name", "government_level", "sparse_text"],
        encoding="utf-8",
    )

    return loader.load()



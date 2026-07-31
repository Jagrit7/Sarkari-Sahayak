from langchain_community.document_loaders import JSONLoader

def _metadata_func(record: dict, metadata: dict) -> dict:
    metadata["scheme_name"] = record.get("scheme_name")
    metadata["government_level"] = record.get("government_level")
    metadata["target_state"] = record.get("target_state")
    metadata["benefits"] = record.get("benefits")
    metadata["eligibility"] = record.get("eligibility")
    metadata["required_documents"] = record.get("required_documents")
    metadata["application_process"] = record.get("application_process")
    metadata["source_url"] = record.get("source_url")
    return metadata

loader = JSONLoader(
    file_path=r'D:\Projects\scheme-setu\data\schemes_rebuilt.jsonl',
    json_lines=True,
    content_key="embedding_text",
    jq_schema=".",
    metadata_func=_metadata_func,
)

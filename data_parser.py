import pandas as pd
import json


def clean_text(text):
    """Removes stray backslashes and escape artifacts from raw text."""
    if isinstance(text, str):
        # Replace literal escaped quotes with normal quotes
        text = text.replace("\\'", "'")
        text = text.replace('\\"', '"')
        # Remove any lingering standalone backslashes
        text = text.replace("\\", "")
    return text


def build_json_database():
    print("Loading raw CSV...")
    df = pd.read_csv('data/raw_schemes.csv')

    df = df.fillna("Not Specified")

    print("Scrubbing escape characters and artifacts...")
    # Apply the text cleaner to all string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].apply(clean_text)

    df.rename(columns={
        'slug': 'scheme_id',
        'scheme_name': 'scheme_name',
        'details': 'description',
        'benefits': 'benefits',
        'eligibility': 'eligibility_criteria',
        'application': 'application_process',
        'documents': 'required_documents',
        'level': 'government_level',
        'schemeCategory': 'category',
        'tags': 'tags'
    }, inplace=True)

    print(f"Parsing {len(df)} schemes... (Preserving full text and Unicode)")

    schemes_list = df.to_dict(orient='records')

    output_path = 'data/master_schemes_db.json'

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schemes_list, f, indent=4, ensure_ascii=False)

    print(f"Success! Cleaned Master JSON saved to {output_path}")


if __name__ == "__main__":
    build_json_database()
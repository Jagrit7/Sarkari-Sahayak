"""
Adds native-language versions of the golden queries, for the multilingual eval.

For every language in voice/core/languages.py except English, each query in
golden_eval_set.jsonl gets a "translations" entry written by Sarvam's translate
API in a spoken, everyday style. Existing translations are kept, so a native
speaker's corrections survive a rerun; pass --force to redo them all.

Have a native speaker check the result before trusting the eval numbers.

Usage (from the repo root, with SARVAM_API_KEY in voice/.env):
    PYTHONPATH=. python voice/eval/retrieval-evals/translate_golden_set.py
"""

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sarvamai import SarvamAI

from voice.core.languages import LANGUAGES

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_eval_set.jsonl"
TARGET_LANGUAGES = [code for code in LANGUAGES if code != "en"]


def main(force=False):
    load_dotenv(EVAL_DIR.parents[1] / ".env")   # voice/.env
    api_key = os.getenv("SARVAM_API_KEY")
    if not api_key:
        sys.exit("SARVAM_API_KEY is not set (put it in voice/.env)")
    client = SarvamAI(api_subscription_key=api_key)

    with open(GOLDEN_SET_PATH, encoding="utf-8") as f:
        golden_set = [json.loads(line) for line in f]

    added = 0
    for item in golden_set:
        translations = item.setdefault("translations", {})
        for code in TARGET_LANGUAGES:
            if code in translations and not force:
                continue
            response = client.text.translate(
                input=item["query"],
                source_language_code="en-IN",
                target_language_code=f"{code}-IN",
                model="mayura:v1",
                mode="modern-colloquial",   # how a caller would actually say it
            )
            translations[code] = response.translated_text
            added += 1
            print(f"[{item['query_id']}] {code}: {translations[code]}")

    with open(GOLDEN_SET_PATH, "w", encoding="utf-8") as f:
        for item in golden_set:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\nAdded {added} translations to {GOLDEN_SET_PATH.name}.")


if __name__ == "__main__":
    main(force="--force" in sys.argv)

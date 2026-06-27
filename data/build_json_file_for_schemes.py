#!/usr/bin/env python3
"""
build_schemes_json.py
---------------------
Rebuild a clean, COMPLETE (zero-null, every field on every record),
hybrid-retrieval-ready JSON from the raw myScheme CSV.

- Keeps all 30 original CSV fields (standardized, no nulls).
- Re-derives the contaminated/sparse eligibility fields from the
  free-text `eligibility` using deterministic rules (best-effort).
- Adds fields needed for hybrid retrieval (dense + sparse + metadata):
    embedding_text, keywords, language, source_url, data_source,
    as_of_date, last_updated, is_active, content_hash
- Emits both a flat JSON array and a JSONL file.

Usage:
    python build_schemes_json.py --input schemes_cleaned.csv --outdir ./out
"""

import argparse, ast, hashlib, json, math, re
from collections import Counter
from datetime import date

import pandas as pd

TODAY = str(date.today())
SENT = {"-1", "-1.0", "-1.00", "", "nan", "none", "null"}

# Canonical Indian States / UTs (lowercased key -> canonical display)
_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka", "Kerala",
    "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland",
    "Odisha", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
    "Uttar Pradesh", "Uttarakhand", "West Bengal",
    "Andaman and Nicobar Islands", "Chandigarh",
    "Dadra and Nagar Haveli & Daman and Diu", "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry",
]
STATE_CANON = {st.lower(): st for st in _STATES}


# ----------------------------- generic cleaners -----------------------------
def missing(v):
    if v is None:
        return True
    if isinstance(v, float) and math.isnan(v):
        return True
    if isinstance(v, str) and v.strip().lower() in SENT:
        return True
    if isinstance(v, list) and len(v) == 0:
        return True
    return False


def txt(v, default=""):
    if missing(v):
        return default
    return re.sub(r"\s+", " ", str(v)).strip()


def clean_name(v):
    n = txt(v).replace('"', "").replace("\\", "")
    n = re.sub(r"\s+", " ", n).strip(" -,")
    return n or "Unnamed Scheme"


def as_list(v):
    """Parse a python-list-string, a comma string, or a real list into a clean unique list."""
    if isinstance(v, list):
        items = v
    elif missing(v):
        items = []
    else:
        t = str(v).strip()
        if t.startswith("[") and t.endswith("]"):
            try:
                items = ast.literal_eval(t)
            except Exception:
                items = [t]
        else:
            items = t.split(",")
    out, seen = [], set()
    for it in items:
        c = re.sub(r"\s+", " ", str(it)).strip()
        if c and c.lower() not in SENT and c.lower() not in seen:
            out.append(c)
            seen.add(c.lower())
    return out


# --------------------------- eligibility extractors -------------------------
def extract_age(age_range, text):
    lo, hi = 0, 120
    ar = txt(age_range).lower()
    m = re.match(r"(\d+)\s*-\s*(\d+)", ar)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
    elif re.match(r"(\d+)\s*\+", ar):
        lo = int(re.match(r"(\d+)", ar).group(1))
    t = text.lower()
    m = re.search(r"between\s+(\d{1,2})\s+(?:and|to)\s+(\d{1,3})\s+years", t)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
    elif lo == 0 and hi == 120:
        m = re.search(r"(\d{1,2})\s*(?:to|-|–|—)\s*(\d{1,3})\s+years", t)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
    if lo == 0 and hi == 120:
        m = re.search(r"(?:above|over|more than|minimum age of|at least|aged)\s+(\d{1,3})\s+years", t)
        if m:
            lo = int(m.group(1))
        m = re.search(r"(?:below|under|up ?to|not more than|maximum age of)\s+(\d{1,3})\s+years", t)
        if m:
            hi = int(m.group(1))
    lo = max(0, min(lo, 120))
    hi = max(lo, min(hi, 120))
    return lo, hi


def _to_inr(num, unit):
    n = float(num.replace(",", ""))
    u = (unit or "").lower()
    if "crore" in u:
        n *= 1e7
    elif "lakh" in u or "lac" in u:
        n *= 1e5
    return int(n)


def extract_income(existing, text):
    t = text.lower()
    m = re.search(
        r"income[^.]{0,70}?(?:not more than|less than|below|up ?to|not exceeding|upto|"
        r"maximum of|should not exceed|shall not exceed)\s*(?:rs\.?|inr|₹)?\s*"
        r"([\d,]+\.?\d*)\s*(lakh|lakhs|lac|lacs|crore|crores)?",
        t,
    )
    if m:
        val = _to_inr(m.group(1), m.group(2))
        if val > 0:
            return val, True
    m = re.search(
        r"(?:rs\.?|inr|₹)\s*([\d,]+\.?\d*)\s*(lakh|lakhs|lac|lacs|crore|crores)\s*"
        r"(?:per annum|p\.?\s?a\.?|annually|annual|/?\s?year)",
        t,
    )
    if m and "income" in t:
        val = _to_inr(m.group(1), m.group(2))
        if val > 0:
            return val, True
    if not missing(existing):
        try:
            v = float(existing)
            if v > 0:
                return int(v), True
        except Exception:
            pass
    return 0, False


def extract_gender(existing, blob):
    ex = txt(existing).lower()
    if ex in {"female", "male", "transgender"}:
        return ex.capitalize()
    if ex == "all":
        return "all"
    if re.search(r"\btransgender\b|\bthird gender\b", blob):
        return "Transgender"
    if re.search(
        r"only (?:for )?women|women candidates|girl child|\bwidow\b|"
        r"for (?:female|women|girls)|\bpregnant\b|\blactating\b|expectant mother",
        blob,
    ):
        return "Female"
    if re.search(r"\bmale only\b|only (?:for )?men\b|boys only", blob):
        return "Male"
    return "all"


def extract_disability(text):
    if re.search(
        r"disab|specially[\s-]?abled|divyang|\bpwd\b|persons? with disabilit|"
        r"handicap|differently[\s-]?abled",
        text, re.I,
    ):
        return "Yes"
    return "all"


def extract_residence(text):
    r = bool(re.search(r"\brural\b", text, re.I))
    u = bool(re.search(r"\burban\b", text, re.I))
    if r and not u:
        return "Rural"
    if u and not r:
        return "Urban"
    return "all"


def extract_marital(text):
    t = text.lower()
    if "widow" in t:
        return "Widow"
    if re.search(r"\bunmarried\b|never married", t):
        return "Unmarried"
    if re.search(r"\bmarried\b", t):
        return "Married"
    return "all"


def extract_category(text):
    cats = []
    if re.search(r"scheduled caste", text, re.I) or re.search(r"\bSC\b", text):
        cats.append("SC")
    if re.search(r"scheduled tribe", text, re.I) or re.search(r"\bST\b", text):
        cats.append("ST")
    if re.search(r"other backward", text, re.I) or re.search(r"\bOBC\b", text):
        cats.append("OBC")
    if re.search(r"economically weaker", text, re.I) or re.search(r"\bEWS\b", text):
        cats.append("EWS")
    if re.search(r"\bminorit", text, re.I):
        cats.append("Minority")
    return cats


def extract_employment(text):
    t = text.lower()
    secs = []
    if re.search(r"government (?:employee|servant|sector)|govt\.? (?:employee|servant)|public sector", t):
        secs.append("Government")
    if re.search(r"private sector|private (?:employee|company|firm)", t):
        secs.append("Private")
    if re.search(r"\bunemployed\b|unemployment", t):
        secs.append("Unemployed")
    if re.search(r"self[\s-]?employed|self[\s-]?employment", t):
        secs.append("Self-employed")
    return secs


def extract_occupation(existing, text):
    occ = txt(existing)
    if occ and not re.search(r"\d", occ) and occ.lower() not in STATE_CANON and occ.lower() != "all":
        return occ
    t = text.lower()
    for kw, label in [
        ("farmer", "Farmer"), ("fisherm", "Fisherman"), ("student", "Student"),
        ("weaver", "Weaver"), ("artisan", "Artisan"), ("labour", "Labourer"),
        ("entrepreneur", "Entrepreneur"), ("self help group", "SHG Member"),
    ]:
        if kw in t:
            return label
    return "all"


def extract_survival(existing):
    ex = txt(existing).lower()
    if ex in {"alive", "deceased"}:
        return ex.capitalize()
    return "all"


def extract_family(existing, text):
    if not missing(existing):
        try:
            v = float(existing)
            if v > 0:
                return int(v)
        except Exception:
            pass
    m = re.search(r"family (?:of|size|members?)[^.\d]{0,20}(\d{1,2})", text, re.I)
    if m:
        return int(m.group(1))
    return 0


def clean_state(existing, gov_level):
    if gov_level == "Central":
        return "All India"
    st = txt(existing)
    low = st.lower()
    if low == "all":
        return "All India"
    return STATE_CANON.get(low, "Not specified")


# ------------------------------ derived fields ------------------------------
def build_age_range(lo, hi):
    if lo == 0 and hi == 120:
        return "any"
    if hi == 120:
        return f"{lo}+"
    return f"{lo}-{hi}"


def build_embedding_text(r):
    parts = [f"Scheme Name: {r['scheme_name']}"]
    if r["government_level"]:
        parts.append(f"Government Level: {r['government_level']}")
    if r["target_state"] != "Not specified":
        parts.append(f"State/UT: {r['target_state']}")
    if r["scheme_category_list"]:
        parts.append("Category: " + ", ".join(r["scheme_category_list"]))
    parts.append(f"Description: {r['description']}")
    parts.append(f"Benefits: {r['benefits']}")
    parts.append(f"Eligibility: {r['eligibility']}")
    parts.append(f"Documents Required: {r['required_documents']}")
    parts.append(f"How to Apply: {r['application_process']}")
    if r["tags_list"]:
        parts.append("Tags: " + ", ".join(r["tags_list"]))
    return "\n".join(parts)


def build_keywords(r):
    kw, seen = [], set()
    def add(x):
        if x and x.lower() not in seen:
            kw.append(x)
            seen.add(x.lower())
    for x in r["tags_list"]:
        add(x)
    for x in r["scheme_category_list"]:
        add(x)
    add(r["government_level"])
    if r["target_state"] not in ("All India", "Not specified"):
        add(r["target_state"])
    if r["target_gender"] != "all":
        add(r["target_gender"])
    if r["disability_status"] == "Yes":
        add("disability")
    if r["occupation"] != "all":
        add(r["occupation"])
    return kw or ["government scheme"]


def content_hash(r):
    blob = "|".join([
        r["scheme_name"], r["description"], r["benefits"],
        r["eligibility"], r["required_documents"], r["application_process"],
    ])
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


# ---------------------------------- main ------------------------------------
def build_record(row):
    g = lambda k: row.get(k)

    name = clean_name(g("scheme_name"))
    description = txt(g("description"), "Not specified")
    benefits = txt(g("benefits"), "Not specified")
    eligibility = txt(g("eligibility"), "Not specified")
    application_process = txt(g("application_process"), "Not specified")
    required_documents = txt(g("required_documents"), "Not specified")
    gov_level = txt(g("government_level"), "Not specified")

    cat_list = as_list(g("scheme_category_list")) or as_list(g("scheme_category"))
    if not cat_list:
        cat_list = ["Uncategorized"]
    cat_primary = cat_list[0]
    tags_list = as_list(g("tags_list")) or as_list(g("tags"))
    if not tags_list:
        tags_list = ["general"]

    # blob used by several text extractors
    blob = " ".join([eligibility, name, " ".join(tags_list)]).lower()

    state = clean_state(g("target_state"), gov_level)
    min_age, max_age = extract_age(g("age_range"), eligibility)
    income, has_income = extract_income(g("max_income_inr"), eligibility)
    gender = extract_gender(g("target_gender"), blob)
    cats = extract_category(eligibility)
    disability = extract_disability(eligibility)
    residence = extract_residence(eligibility)
    marital = extract_marital(eligibility)
    employment = extract_employment(eligibility)
    occupation = extract_occupation(g("occupation"), eligibility)
    survival = extract_survival(g("survival_status"))
    family = extract_family(g("max_family_size"), eligibility)

    r = {
        # ---- original CSV fields (standardized) ----
        "scheme_id": txt(g("scheme_id")) or content_hash({"scheme_name": name, "description": description, "benefits": benefits, "eligibility": eligibility, "required_documents": required_documents, "application_process": application_process}),
        "scheme_name": name,
        "description": description,
        "benefits": benefits,
        "eligibility": eligibility,
        "application_process": application_process,
        "required_documents": required_documents,
        "government_level": gov_level,
        "scheme_category": ", ".join(cat_list),
        "scheme_category_list": cat_list,
        "scheme_category_primary": cat_primary,
        "tags": ", ".join(tags_list),
        "tags_list": tags_list,
        "target_gender": gender,
        "target_category": ", ".join(cats) if cats else "all",
        "target_state": state,
        "min_age": min_age,
        "max_age": max_age,
        "age_range": build_age_range(min_age, max_age),
        "max_income_inr": income,
        "has_income_limit": has_income,
        "occupation": occupation,
        "employment_sector": ", ".join(employment) if employment else "all",
        "marital_status": marital,
        "disability_status": disability,
        "survival_status": survival,
        "residence_type": residence,
        "max_family_size": family,
        "is_private": False,
        "description_word_count": len(description.split()),
    }
    # ---- new hybrid-retrieval fields ----
    r["embedding_text"] = build_embedding_text(r)
    r["keywords"] = build_keywords(r)
    r["language"] = "en"
    # NOTE: per-scheme URLs are not in the CSV; this points to the myScheme
    # search page. Replace with the real per-scheme URL once the live sync runs.
    r["source_url"] = "https://www.myscheme.gov.in/find-scheme"
    r["data_source"] = "myScheme (Kaggle snapshot)"
    r["as_of_date"] = TODAY          # set to the snapshot's true date if known
    r["last_updated"] = TODAY        # the live pipeline overwrites this
    r["is_active"] = True            # the live pipeline flips deprecated schemes
    r["content_hash"] = content_hash(r)
    return r


def validate(records):
    """Assert every record has every key and no null/empty value."""
    keys = list(records[0].keys())
    problems = []
    for i, r in enumerate(records):
        if set(r.keys()) != set(keys):
            problems.append((i, "key mismatch"))
            continue
        for k, v in r.items():
            if v is None or (isinstance(v, float) and math.isnan(v)) or v == "" or v == []:
                problems.append((i, k))
    return keys, problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--outdir", default="./out")
    args = ap.parse_args()

    import os
    os.makedirs(args.outdir, exist_ok=True)

    df = pd.read_csv(args.input)
    records = [build_record(row) for _, row in df.iterrows()]

    keys, problems = validate(records)

    json_path = os.path.join(args.outdir, "schemes_rebuilt.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2, allow_nan=False)

    jsonl_path = os.path.join(args.outdir, "schemes_rebuilt.jsonl")
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False, allow_nan=False) + "\n")

    # ---- report ----
    print(f"Records:            {len(records)}")
    print(f"Fields per record:  {len(keys)}  (30 original + 9 new)")
    print(f"Null/empty values:  {len(problems)}  <- must be 0")
    if problems:
        print("  FIRST PROBLEMS:", problems[:10])
    print(f"\nNew fields added:   embedding_text, keywords, language, source_url,")
    print(f"                    data_source, as_of_date, last_updated, is_active, content_hash")

    # quick distributions of the re-derived filters (sanity)
    print("\nRe-derived filter coverage (share that is NOT the 'all'/default):")
    def share(key, default):
        n = sum(1 for r in records if str(r[key]) != str(default))
        return f"{100*n/len(records):4.1f}%"
    print(f"  target_gender != all      : {share('target_gender','all')}")
    print(f"  target_state  != All India: {share('target_state','All India')}")
    print(f"  disability_status == Yes  : {100*sum(1 for r in records if r['disability_status']=='Yes')/len(records):4.1f}%")
    print(f"  has_income_limit == True  : {100*sum(1 for r in records if r['has_income_limit'])/len(records):4.1f}%")
    print(f"  age restricted (not 0-120): {100*sum(1 for r in records if r['age_range']!='any')/len(records):4.1f}%")
    print(f"  target_category != all    : {share('target_category','all')}")

    print(f"\nWrote:\n  {json_path}\n  {jsonl_path}")


if __name__ == "__main__":
    main()

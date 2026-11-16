"""
Evaluates the retriever against a golden query set, in any supported language.

Metrics: Precision@k, Recall@k, NDCG@k, MRR
Also reports end-to-end latency as mean/median/p95/p99.

Each query can be asked in any language from voice/core/languages.py (the
translations come from translate_golden_set.py), in one of two modes:
  english  the production setup: the native query feeds the vector search,
           the English query feeds keyword search and the reranker
  native   the native query feeds everything, as a stress test of
           cross-lingual search with no translation at all

Usage (from the repo root):
    PYTHONPATH=. python voice/eval/retrieval-evals/evaluate_retrieval.py
    PYTHONPATH=. python voice/eval/retrieval-evals/evaluate_retrieval.py --lang ta --mode native --alpha 0.7
    PYTHONPATH=. python voice/eval/retrieval-evals/evaluate_retrieval.py --sweep
"""

import argparse
import json
import time
import math
import statistics
from pathlib import Path

from voice.core.languages import LANGUAGES
from voice.retrieval.retriever import ALPHA, search_schemes, vectorstore

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_SET_PATH = EVAL_DIR / "golden_eval_set.jsonl"
RESULTS_DIR = EVAL_DIR / "results"   # eval_results.json is the pre-multilingual baseline
K = 3
MODES = ("english", "native")
SWEEP_ALPHAS = (0.5, 0.6, 0.7, 0.8)

# ---------- load golden set ----------

def load_golden_set(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def queries_for(item, lang, mode):
    """Returns (keyword/rerank query, vector query) for one golden item."""
    english = item["query"]
    if lang == "en":
        return english, english
    native = item.get("translations", {}).get(lang)
    if native is None:
        raise SystemExit(f"No '{lang}' translation for {item['query_id']}: run translate_golden_set.py first")
    return (english if mode == "english" else native), native


# ---------- metrics ----------

def precision_at_k(retrieved_ids, expected_ids, k):
    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & set(expected_ids))
    return hits / k


def recall_at_k(retrieved_ids, expected_ids, k):
    top_k = retrieved_ids[:k]
    hits = len(set(top_k) & set(expected_ids))
    return hits / len(expected_ids)


def mrr(retrieved_ids, expected_ids):
    for rank, scheme_id in enumerate(retrieved_ids, start=1):
        if scheme_id in expected_ids:
            return 1 / rank
    return 0.0


def ndcg_at_k(retrieved_ids, relevance_grades, k):
    top_k = retrieved_ids[:k]

    dcg = 0.0
    for i, scheme_id in enumerate(top_k):
        relevance = relevance_grades.get(scheme_id, 0)
        dcg += relevance / math.log2(i + 2)  # +2 because rank starts at 1, log2(1+1)=1

    ideal_relevances = sorted(relevance_grades.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(ideal_relevances))

    return dcg / idcg if idcg > 0 else 0.0


# ---------- latency summary ----------

def summarize_latency(values):
    values_sorted = sorted(values)
    return {
        "mean_ms": statistics.mean(values_sorted),
        "median_ms": statistics.median(values_sorted),
        "p95_ms": values_sorted[int(len(values_sorted) * 0.95) - 1],
        "p99_ms": values_sorted[int(len(values_sorted) * 0.99) - 1],
    }


# ---------- one run ----------

def run_eval(golden_set, lang, mode, alpha):
    per_query_results = []
    all_latencies_ms = {}

    for item in golden_set:
        query, original_query = queries_for(item, lang, mode)
        docs, latency = search_schemes(
            query,
            k=K,
            government_level=item.get("government_level_filter"),
            return_latency=True,
            original_query=original_query,
            alpha=alpha,
        )

        retrieved_ids = [doc.metadata["scheme_id"] for doc in docs]
        expected_ids = item["expected_scheme_ids"]
        relevance_grades = item["relevance_grades"]

        result = {
            "query_id": item["query_id"],
            "query": original_query,
            "retrieved_ids": retrieved_ids,
            "expected_ids": expected_ids,
            "precision@k": precision_at_k(retrieved_ids, expected_ids, K),
            "recall@k": recall_at_k(retrieved_ids, expected_ids, K),
            "mrr": mrr(retrieved_ids, expected_ids),
            "ndcg@k": ndcg_at_k(retrieved_ids, relevance_grades, K),
            "latency": latency,
        }
        per_query_results.append(result)
        for stage, value in latency.items():
            all_latencies_ms.setdefault(stage, []).append(value)

    n = len(per_query_results)
    averages = {
        "precision@k": sum(r["precision@k"] for r in per_query_results) / n,
        "recall@k": sum(r["recall@k"] for r in per_query_results) / n,
        "mrr": sum(r["mrr"] for r in per_query_results) / n,
        "ndcg@k": sum(r["ndcg@k"] for r in per_query_results) / n,
    }
    latency_summary = {stage: summarize_latency(values) for stage, values in all_latencies_ms.items()}

    output = {
        "lang": lang,
        "mode": mode,
        "alpha": alpha,
        "per_query_results": per_query_results,
        "averages": averages,
        "latency_summary": latency_summary,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    path = RESULTS_DIR / f"{lang}-{mode}-alpha{alpha}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    output["path"] = path
    return output


# ---------- single run: full report ----------

def report(output):
    per_query_results = output["per_query_results"]
    for r in per_query_results:
        print(f"[{r['query_id']}] {r['query']}")
        print(f"  retrieved: {r['retrieved_ids']}")
        print(f"  expected:  {r['expected_ids']}")
        print(f"  precision@{K}: {r['precision@k']:.2f}  recall@{K}: {r['recall@k']:.2f}  "
              f"mrr: {r['mrr']:.2f}  ndcg@{K}: {r['ndcg@k']:.2f}")
        print(f"  latency: embed_and_search={r['latency']['embed_and_search_ms']:.0f}ms  "
              f"rerank={r['latency']['rerank_ms']:.0f}ms  total={r['latency']['total_ms']:.0f}ms")
        print()

    print(f"=== Averages across all queries ({output['lang']}, {output['mode']} mode, alpha {output['alpha']}) ===")
    for metric, value in output["averages"].items():
        print(f"{metric}: {value:.3f}")

    print()
    print("=== Latency (ms) ===")
    for stage, summary in output["latency_summary"].items():
        print(f"{stage}: mean={summary['mean_ms']:.0f}  median={summary['median_ms']:.0f}  "
              f"p95={summary['p95_ms']:.0f}  p99={summary['p99_ms']:.0f}")

    print(f"\nResults written to {output['path']}")


# ---------- sweep: every language x mode x alpha ----------

def sweep(golden_set):
    rows = []
    for alpha in SWEEP_ALPHAS:
        for lang in LANGUAGES:
            for mode in (MODES if lang != "en" else MODES[:1]):   # both modes are identical for English
                out = run_eval(golden_set, lang, mode, alpha)
                rows.append({"lang": lang, "mode": mode, "alpha": alpha, **out["averages"]})
                a = out["averages"]
                print(f"{lang:>3} {mode:<8} alpha={alpha}  P@{K}={a['precision@k']:.2f}  R@{K}={a['recall@k']:.2f}  "
                      f"MRR={a['mrr']:.2f}  NDCG@{K}={a['ndcg@k']:.2f}")

    # pick alpha by mean MRR across all languages in the production ("english") mode
    by_alpha = {
        alpha: statistics.mean(r["mrr"] for r in rows if r["alpha"] == alpha and r["mode"] == "english")
        for alpha in SWEEP_ALPHAS
    }
    best = max(by_alpha, key=by_alpha.get)
    print("\n=== Mean MRR across languages, english mode ===")
    for alpha, value in by_alpha.items():
        print(f"alpha={alpha}: {value:.3f}" + ("   <- best" if alpha == best else ""))
    print(f"\nSet ALPHA = {best} in voice/retrieval/retriever.py if it isn't already (currently {ALPHA}).")

    with open(RESULTS_DIR / "summary.json", "w", encoding="utf-8") as f:
        json.dump({"rows": rows, "mean_mrr_by_alpha": by_alpha, "best_alpha": best}, f, indent=2)
    print(f"Summary written to {RESULTS_DIR / 'summary.json'}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--lang", default="en", choices=list(LANGUAGES), help="query language (default: en)")
    parser.add_argument("--mode", default="english", choices=MODES, help="what feeds keyword search and the reranker")
    parser.add_argument("--alpha", type=float, default=ALPHA, help=f"hybrid weight (default: {ALPHA})")
    parser.add_argument("--sweep", action="store_true", help="run every language, mode and alpha in SWEEP_ALPHAS")
    args = parser.parse_args()

    golden_set = load_golden_set(GOLDEN_SET_PATH)
    try:
        if args.sweep:
            sweep(golden_set)
        else:
            report(run_eval(golden_set, args.lang, args.mode, args.alpha))
    finally:
        vectorstore._client.close()


if __name__ == "__main__":
    main()
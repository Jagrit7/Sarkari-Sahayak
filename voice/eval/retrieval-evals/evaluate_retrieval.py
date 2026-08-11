"""
Evaluates the retriever against a golden query set.

Metrics: Precision@k, Recall@k, NDCG@k, MRR
Also reports end-to-end latency as mean/median/p95/p99.

Usage:
    python evaluate_retrieval.py
"""

import json
import time
import math
import statistics

from voice.retrieval.retriever import search_schemes, vectorstore

GOLDEN_SET_PATH = r"D:\Projects\Sarkari-Sahayak\voice\eval\retrieval-evals\golden_eval_set.jsonl"
RESULTS_PATH = r"D:\Projects\Sarkari-Sahayak\voice\eval\retrieval-evals\eval_results.json"
K = 3

# ---------- load golden set ----------

def load_golden_set(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


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


# ---------- main ----------

def main():
    golden_set = load_golden_set(GOLDEN_SET_PATH)

    per_query_results = []
    all_latencies_ms = {}

    for item in golden_set:
        docs, latency = search_schemes(
            item["query"],
            k=K,
            government_level=item.get("government_level_filter"),
            return_latency=True,
        )

        retrieved_ids = [doc.metadata["scheme_id"] for doc in docs]
        expected_ids = item["expected_scheme_ids"]
        relevance_grades = item["relevance_grades"]

        result = {
            "query_id": item["query_id"],
            "query": item["query"],
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

    vectorstore._client.close()

    # ---------- print per-query results ----------
    for r in per_query_results:
        print(f"[{r['query_id']}] {r['query']}")
        print(f"  retrieved: {r['retrieved_ids']}")
        print(f"  expected:  {r['expected_ids']}")
        print(f"  precision@{K}: {r['precision@k']:.2f}  recall@{K}: {r['recall@k']:.2f}  "
              f"mrr: {r['mrr']:.2f}  ndcg@{K}: {r['ndcg@k']:.2f}")
        print(f"  latency: embed_and_search={r['latency']['embed_and_search_ms']:.0f}ms  "
              f"rerank={r['latency']['rerank_ms']:.0f}ms  total={r['latency']['total_ms']:.0f}ms")
        print()

    # ---------- averaged metrics ----------
    n = len(per_query_results)
    averages = {
        "precision@k": sum(r["precision@k"] for r in per_query_results) / n,
        "recall@k": sum(r["recall@k"] for r in per_query_results) / n,
        "mrr": sum(r["mrr"] for r in per_query_results) / n,
        "ndcg@k": sum(r["ndcg@k"] for r in per_query_results) / n,
    }

    print("=== Averages across all queries ===")
    for metric, value in averages.items():
        print(f"{metric}: {value:.3f}")

    # ---------- latency summary, per stage ----------
    latency_summary = {stage: summarize_latency(values) for stage, values in all_latencies_ms.items()}
    print()
    print("=== Latency (ms) ===")
    for stage, summary in latency_summary.items():
        print(f"{stage}: mean={summary['mean_ms']:.0f}  median={summary['median_ms']:.0f}  "
              f"p95={summary['p95_ms']:.0f}  p99={summary['p99_ms']:.0f}")

    # ---------- write results to file ----------
    output = {
        "per_query_results": per_query_results,
        "averages": averages,
        "latency_summary": latency_summary,
    }
    with open(RESULTS_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
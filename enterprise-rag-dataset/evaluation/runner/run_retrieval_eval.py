#!/usr/bin/env python3
"""Evaluate Onyx retrieval independently from answer generation."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "enterprise-rag-dataset"
QUESTIONS = DATASET / "evaluation" / "golden_questions.csv"
KB_ROOT = DATASET / "knowledge_base"
TOKEN_FILE = ROOT / ".secrets" / "onyx_pat.txt"
RESULTS_DIR = DATASET / "evaluation" / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate Onyx retrieval")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--document-set", default="CloudOrder企业知识库")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


def load_token() -> str:
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token.startswith("onyx_pat_"):
        raise ValueError("Invalid PAT file")
    return token


def load_questions() -> list[dict[str, str]]:
    with QUESTIONS.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def post_search(
    base_url: str,
    token: str,
    query: str,
    document_set: str,
    top_k: int,
    timeout: int,
) -> dict[str, Any]:
    payload = {
        "search_query": query,
        "filters": {"document_set": [document_set]},
        "run_query_expansion": False,
        "num_docs_fed_to_llm_selection": None,
        "num_hits": top_k,
        "include_content": False,
        "stream": False,
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/search/send-search-message",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def expected_identifiers(row: dict[str, str]) -> list[str]:
    return [item.replace("/", "\\") for item in row.get("source_docs", "").split(";") if item]


def evaluate(
    index: int,
    row: dict[str, str],
    args: argparse.Namespace,
    token: str,
) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    error = ""
    response: dict[str, Any] = {}
    try:
        response = post_search(
            args.base_url,
            token,
            row["question"],
            args.document_set,
            args.top_k,
            args.timeout,
        )
    except urllib.error.HTTPError as exc:
        error = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:500]}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - started

    docs = response.get("search_docs") or []
    retrieved = [str(doc.get("semantic_identifier") or "") for doc in docs]
    expected = expected_identifiers(row)
    rank: int | None = None
    for position, identifier in enumerate(retrieved, start=1):
        if identifier in expected:
            rank = position
            break

    result = {
        **row,
        "latency_seconds": round(latency, 3),
        "retrieved_count": len(retrieved),
        "retrieved_identifiers": json.dumps(retrieved, ensure_ascii=False),
        "hit_at_k": rank is not None if expected else None,
        "first_relevant_rank": rank or "",
        "reciprocal_rank": round(1 / rank, 6) if rank else 0,
        "error": error or response.get("error") or "",
    }
    return index, result


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def main() -> int:
    args = parse_args()
    token = load_token()
    questions = load_questions()
    worker_count = max(1, min(args.workers, len(questions)))
    indexed_rows: list[tuple[int, dict[str, Any]]] = []

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {
            executor.submit(evaluate, index, row, args, token): (index, row)
            for index, row in enumerate(questions, start=1)
        }
        for future in as_completed(futures):
            index, source_row = futures[future]
            try:
                completed_index, result = future.result()
            except Exception as exc:
                completed_index = index
                result = {
                    **source_row,
                    "latency_seconds": 0,
                    "retrieved_count": 0,
                    "retrieved_identifiers": "[]",
                    "hit_at_k": None,
                    "first_relevant_rank": "",
                    "reciprocal_rank": 0,
                    "error": f"WorkerError: {type(exc).__name__}: {exc}",
                }
            indexed_rows.append((completed_index, result))
            status = "OK" if not result["error"] else "ERROR"
            print(
                f"[{len(indexed_rows):02d}/{len(questions):02d}] "
                f"{source_row['id']} {status} {float(result['latency_seconds']):.2f}s",
                flush=True,
            )

    rows = [row for _, row in sorted(indexed_rows)]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = RESULTS_DIR / f"retrieval_{stamp}.csv"
    report_path = RESULTS_DIR / f"retrieval_{stamp}.md"

    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    scored = [row for row in rows if row["source_docs"] and not row["error"]]
    hits = sum(row["hit_at_k"] is True for row in scored)
    mrr = statistics.mean(float(row["reciprocal_rank"]) for row in scored) if scored else 0
    latencies = [float(row["latency_seconds"]) for row in rows if not row["error"]]
    misses = [row["id"] for row in scored if row["hit_at_k"] is False]
    errors = [row["id"] for row in rows if row["error"]]
    report = [
        "# CloudOrder Retrieval Baseline",
        "",
        f"- Run time: {datetime.now().isoformat(timespec='seconds')}",
        f"- Document set: {args.document_set}",
        f"- Top-K: {args.top_k}",
        f"- Scored questions: {len(scored)}",
        f"- Hit@{args.top_k}: {hits / len(scored):.1%}" if scored else f"- Hit@{args.top_k}: N/A",
        f"- MRR: {mrr:.3f}",
        f"- Median latency: {statistics.median(latencies):.3f}s" if latencies else "- Median latency: N/A",
        f"- P95 latency: {percentile(latencies, 0.95):.3f}s" if latencies else "- P95 latency: N/A",
        f"- Misses: {', '.join(misses) if misses else 'none'}",
        f"- Errors: {', '.join(errors) if errors else 'none'}",
        "",
        "Questions without expected source documents are executed but excluded from Hit@K and MRR.",
    ]
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"CSV: {csv_path}")
    print(f"REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


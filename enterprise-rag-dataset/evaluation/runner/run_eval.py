#!/usr/bin/env python3
"""Run reproducible RAG evaluation against an Onyx Agent.

The script intentionally uses only Python's standard library. It records the
raw answer, retrieved documents, citations, latency, source-hit metrics, and
refusal behavior. Answer correctness is left for a separate judge/manual pass
so retrieval quality is not confused with generation quality.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "enterprise-rag-dataset"
DEFAULT_QUESTIONS = DATASET / "evaluation" / "golden_questions.csv"
DEFAULT_KB = DATASET / "knowledge_base"
DEFAULT_TOKEN = ROOT / ".secrets" / "onyx_pat.txt"
DEFAULT_RESULTS = DATASET / "evaluation" / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate an Onyx RAG Agent")
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--agent-id", type=int, default=1)
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--knowledge-base", type=Path, default=DEFAULT_KB)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--limit", type=int, default=0, help="0 means all")
    parser.add_argument(
        "--ids",
        default="",
        help="Comma-separated question IDs to run, for example Q002,Q049",
    )
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--workers", type=int, default=4)
    return parser.parse_args()


def load_token(path: Path) -> str:
    token = path.read_text(encoding="utf-8").strip()
    if not token or token == "PASTE_FULL_ONYX_PAT_HERE":
        raise ValueError(f"Paste the full PAT into {path}")
    if not token.startswith("onyx_pat_"):
        raise ValueError("The token does not look like an Onyx PAT")
    return token


def load_questions(path: Path, limit: int, ids: str = "") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected_ids = {item.strip() for item in ids.split(",") if item.strip()}
    if selected_ids:
        rows = [row for row in rows if row["id"] in selected_ids]
    return rows[:limit] if limit > 0 else rows


def document_title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def expected_titles(row: dict[str, str], kb_root: Path) -> list[str]:
    titles: list[str] = []
    for relative in filter(None, row.get("source_docs", "").split(";")):
        if relative.startswith(("https://", "http://")):
            titles.append(relative)
            continue
        source = kb_root / relative
        if source.exists():
            titles.append(document_title(source))
    return titles


def post_message(
    base_url: str, token: str, agent_id: int, question: str, timeout: int
) -> dict[str, Any]:
    payload = {
        "message": question,
        "chat_session_info": {"persona_id": agent_id},
        "parent_message_id": -1,
        "stream": False,
        "include_citations": True,
        "origin": "api",
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat/send-chat-message",
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


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def refusal_pass(answer: str, answerable: str) -> bool | None:
    if answerable.lower() != "no":
        return None
    markers = (
        "无法确认",
        "无法从",
        "无法提供",
        "无法回答",
        "不能确认",
        "不能提供",
        "未提供",
        "没有提供",
        "未找到足够证据",
        "没有足够证据",
        "资料不足",
        "不属于仓库公开内容",
    )
    return any(marker in answer for marker in markers)


def source_hit(documents: list[dict[str, Any]], titles: list[str]) -> bool | None:
    if not titles:
        return None
    haystack = json.dumps(documents, ensure_ascii=False).lower()
    return any(title.lower() in haystack for title in titles)


def serialize_documents(documents: list[dict[str, Any]]) -> str:
    summaries = []
    for doc in documents:
        summaries.append(
            {
                "semantic_identifier": doc.get("semantic_identifier"),
                "link": doc.get("link"),
                "score": doc.get("score"),
                "metadata": doc.get("metadata"),
            }
        )
    return json.dumps(summaries, ensure_ascii=False)


def write_report(rows: list[dict[str, Any]], path: Path, metadata: dict[str, Any]) -> None:
    successes = [row for row in rows if not row["error"]]
    latencies = [float(row["latency_seconds"]) for row in successes]
    source_rows = [row for row in successes if row["retrieval_hit"] is not None]
    refusal_rows = [row for row in successes if row["refusal_pass"] is not None]
    answerable_rows = [
        row for row in successes if str(row.get("answerable", "yes")).lower() != "no"
    ]
    citation_rows = [
        row for row in answerable_rows if int(row["citation_count"]) > 0
    ]

    def ratio(numerator: int, denominator: int) -> str:
        return f"{numerator / denominator:.1%}" if denominator else "N/A"

    content = [
        "# Onyx RAG Evaluation Report",
        "",
        f"- Run time: {metadata['run_time']}",
        f"- Onyx base URL: {metadata['base_url']}",
        f"- Agent ID: {metadata['agent_id']}",
        f"- Questions: {len(rows)}",
        f"- Request success rate: {ratio(len(successes), len(rows))}",
        f"- Expected-source hit rate: {ratio(sum(row['retrieval_hit'] is True for row in source_rows), len(source_rows))}",
        f"- Citation presence rate (answerable questions): {ratio(len(citation_rows), len(answerable_rows))}",
        f"- No-answer refusal pass rate: {ratio(sum(row['refusal_pass'] is True for row in refusal_rows), len(refusal_rows))}",
        f"- Median latency: {statistics.median(latencies):.2f}s" if latencies else "- Median latency: N/A",
        f"- P95 latency: {percentile(latencies, 0.95):.2f}s" if latencies else "- P95 latency: N/A",
        "",
        "## Failures and misses",
        "",
    ]
    misses = [
        row for row in rows
        if row["error"] or row["retrieval_hit"] is False or row["refusal_pass"] is False
    ]
    if not misses:
        content.append("No request, retrieval, or refusal failures in this run.")
    else:
        for row in misses:
            content.append(
                f"- {row['id']}: error={row['error'] or 'none'}, "
                f"retrieval_hit={row['retrieval_hit']}, refusal_pass={row['refusal_pass']}"
            )
    content.extend([
        "",
        "## Interpretation",
        "",
        "This report measures pipeline reliability, retrieval source hits, citation presence, and refusal behavior. "
        "Semantic answer correctness requires the subsequent judge/manual scoring stage.",
    ])
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


def evaluate_one(
    index: int,
    question: dict[str, str],
    args: argparse.Namespace,
    token: str,
) -> tuple[int, dict[str, Any]]:
    started = time.perf_counter()
    response: dict[str, Any] = {}
    error = ""
    try:
        response = post_message(
            args.base_url,
            token,
            args.agent_id,
            question["question"],
            args.timeout,
        )
    except urllib.error.HTTPError as exc:
        error = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:500]}"
    except Exception as exc:  # preserve the run and record the failed row
        error = f"{type(exc).__name__}: {exc}"

    latency = time.perf_counter() - started
    answer = response.get("answer_citationless") or response.get("answer") or ""
    documents = response.get("top_documents") or []
    citations = response.get("citation_info") or []
    titles = expected_titles(question, args.knowledge_base)
    row: dict[str, Any] = {
        **question,
        "answer": answer,
        "latency_seconds": round(latency, 3),
        "retrieval_hit": source_hit(documents, titles) if not error else None,
        "citation_count": len(citations),
        "refusal_pass": refusal_pass(answer, question.get("answerable", "")) if not error else None,
        "retrieved_documents": serialize_documents(documents),
        "chat_session_id": response.get("chat_session_id") or "",
        "message_id": response.get("message_id") or "",
        "error": error or response.get("error_msg") or "",
    }
    return index, row


def main() -> int:
    args = parse_args()
    try:
        token = load_token(args.token_file)
    except (OSError, ValueError) as exc:
        print(f"TOKEN_ERROR: {exc}", file=sys.stderr)
        return 2

    questions = load_questions(args.questions, args.limit, args.ids)
    if not questions:
        print("QUESTION_ERROR: no matching questions", file=sys.stderr)
        return 2
    args.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = args.results_dir / f"baseline_{stamp}.csv"
    jsonl_path = args.results_dir / f"baseline_{stamp}.jsonl"
    report_path = args.results_dir / f"baseline_{stamp}.md"
    indexed_rows: list[tuple[int, dict[str, Any]]] = []
    worker_count = max(1, min(args.workers, len(questions)))
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_map = {
            executor.submit(evaluate_one, index, question, args, token): (index, question)
            for index, question in enumerate(questions, start=1)
        }
        for future in as_completed(future_map):
            index, question = future_map[future]
            try:
                completed_index, row = future.result()
            except Exception as exc:
                completed_index = index
                row = {
                    **question,
                    "answer": "",
                    "latency_seconds": 0,
                    "retrieval_hit": None,
                    "citation_count": 0,
                    "refusal_pass": None,
                    "retrieved_documents": "[]",
                    "chat_session_id": "",
                    "message_id": "",
                    "error": f"WorkerError: {type(exc).__name__}: {exc}",
                }
            indexed_rows.append((completed_index, row))
            status = "OK" if not row["error"] else "ERROR"
            print(
                f"[{len(indexed_rows):02d}/{len(questions):02d}] {question['id']} "
                f"{status} {float(row['latency_seconds']):.2f}s",
                flush=True,
            )

    rows = [row for _, row in sorted(indexed_rows, key=lambda item: item[0])]

    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "run_time": datetime.now().isoformat(timespec="seconds"),
        "base_url": args.base_url,
        "agent_id": args.agent_id,
    }
    write_report(rows, report_path, metadata)
    print(f"CSV: {csv_path}")
    print(f"JSONL: {jsonl_path}")
    print(f"REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

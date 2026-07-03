#!/usr/bin/env python3
"""Run bounded, reproducible load tests against Onyx retrieval or an Agent.

The test intentionally uses a small request budget so it can be used on a
development server without turning a portfolio benchmark into a cost event.
It also samples host/container resources over SSH while requests are running.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import subprocess
import threading
import time
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

from run_eval import load_token, post_message
from run_retrieval_eval import post_search


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TOKEN = ROOT / ".secrets" / "onyx_pat.txt"
DEFAULT_QUESTIONS = (
    ROOT / "enterprise-rag-dataset" / "evaluation" / "mall_golden_questions.csv"
)
DEFAULT_RESULTS = ROOT / "enterprise-rag-dataset" / "evaluation" / "results" / "load"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded Onyx load test")
    parser.add_argument("--mode", choices=("retrieval", "agent"), required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:8088")
    parser.add_argument("--agent-id", type=int, default=2)
    parser.add_argument("--document-set", default="Mall开源电商研发知识库")
    parser.add_argument("--token-file", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS)
    parser.add_argument("--ids", default="M007,M008,M009,M010,M011,M012")
    parser.add_argument("--levels", default="1,2,4")
    parser.add_argument("--requests-per-level", type=int, default=4)
    parser.add_argument("--spike-concurrency", type=int, default=6)
    parser.add_argument("--spike-requests", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--cooldown", type=float, default=2.0)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--ssh-host", default="ubuntu@146.56.217.22")
    parser.add_argument("--ssh-key", type=Path, default=ROOT / "onyx_key.pem")
    parser.add_argument("--sample-interval", type=float, default=2.0)
    return parser.parse_args()


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def load_questions(path: Path, ids: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    selected = {item.strip() for item in ids.split(",") if item.strip()}
    rows = [row for row in rows if not selected or row["id"] in selected]
    if not rows:
        raise ValueError("No matching questions")
    return rows


def parse_memory_mib(raw: str) -> float:
    value = raw.strip().split()[0]
    units = (
        ("GiB", 1024),
        ("MiB", 1),
        ("KiB", 1 / 1024),
        ("B", 1 / (1024 * 1024)),
    )
    for unit, multiplier in units:
        if value.endswith(unit):
            return float(value[: -len(unit)]) * multiplier
    return 0.0


class ResourceSampler:
    def __init__(self, host: str, key: Path, interval: float) -> None:
        self.host = host
        self.key = key
        self.interval = interval
        self.samples: list[dict[str, Any]] = []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=max(10, self.interval * 3))

    def _sample(self) -> dict[str, Any]:
        remote = (
            "free -b | awk '/Mem:/{print \"HOST|\"$2\"|\"$3\"|\"$7}'; "
            "sudo docker stats --no-stream "
            "--format 'CTR|{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}'"
        )
        completed = subprocess.run(
            [
                "ssh",
                "-i",
                str(self.key),
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "ConnectTimeout=8",
                self.host,
                remote,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
        sample: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "host_total_bytes": None,
            "host_used_bytes": None,
            "host_available_bytes": None,
            "containers": {},
            "error": "" if completed.returncode == 0 else completed.stderr.strip()[:300],
        }
        for line in completed.stdout.splitlines():
            parts = line.split("|")
            if parts[0] == "HOST" and len(parts) == 4:
                sample["host_total_bytes"] = int(parts[1])
                sample["host_used_bytes"] = int(parts[2])
                sample["host_available_bytes"] = int(parts[3])
            elif parts[0] == "CTR" and len(parts) >= 4:
                name = parts[1]
                sample["containers"][name] = {
                    "cpu_percent": float(parts[2].strip().rstrip("%") or 0),
                    "memory_mib": parse_memory_mib(parts[3].split("/")[0]),
                    "memory_raw": parts[3].strip(),
                }
        return sample

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.samples.append(self._sample())
            except Exception as exc:
                self.samples.append(
                    {
                        "timestamp": datetime.now().isoformat(timespec="seconds"),
                        "containers": {},
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
            self._stop.wait(self.interval)


def execute_request(
    args: argparse.Namespace,
    token: str,
    question: dict[str, str],
    sequence: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    error = ""
    response: dict[str, Any] = {}
    try:
        if args.mode == "retrieval":
            response = post_search(
                args.base_url,
                token,
                question["question"],
                args.document_set,
                5,
                args.timeout,
            )
        else:
            response = post_message(
                args.base_url,
                token,
                args.agent_id,
                question["question"],
                args.timeout,
            )
    except urllib.error.HTTPError as exc:
        error = f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:300]}"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    latency = time.perf_counter() - started
    answer = response.get("answer_citationless") or response.get("answer") or ""
    search_docs = response.get("search_docs") or response.get("top_documents") or []
    citations = response.get("citation_info") or []
    return {
        "sequence": sequence,
        "question_id": question["id"],
        "latency_seconds": round(latency, 3),
        "success": not bool(error or response.get("error") or response.get("error_msg")),
        "error": error or response.get("error") or response.get("error_msg") or "",
        "retrieved_count": len(search_docs),
        "citation_count": len(citations),
        "answer_chars": len(answer),
    }


def run_level(
    args: argparse.Namespace,
    token: str,
    questions: list[dict[str, str]],
    label: str,
    concurrency: int,
    request_count: int,
    offset: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(
                execute_request,
                args,
                token,
                questions[(offset + index) % len(questions)],
                index + 1,
            ): index
            for index in range(request_count)
        }
        for future in as_completed(futures):
            rows.append(future.result())
    wall_seconds = time.perf_counter() - started
    rows.sort(key=lambda row: row["sequence"])
    latencies = [float(row["latency_seconds"]) for row in rows]
    successful = [row for row in rows if row["success"]]
    summary = {
        "label": label,
        "concurrency": concurrency,
        "requests": request_count,
        "successes": len(successful),
        "success_rate": len(successful) / request_count if request_count else 0,
        "wall_seconds": round(wall_seconds, 3),
        "throughput_rps": round(request_count / wall_seconds, 3),
        "throughput_rpm": round(request_count / wall_seconds * 60, 2),
        "p50_seconds": round(statistics.median(latencies), 3),
        "p95_seconds": round(percentile(latencies, 0.95), 3),
        "p99_seconds": round(percentile(latencies, 0.99), 3),
        "max_seconds": round(max(latencies), 3),
        "citation_rate": (
            sum(int(row["citation_count"]) > 0 for row in successful) / len(successful)
            if successful and args.mode == "agent"
            else None
        ),
    }
    for row in rows:
        row["level"] = label
        row["concurrency"] = concurrency
    print(
        f"{label}: c={concurrency} n={request_count} "
        f"success={len(successful)}/{request_count} "
        f"p95={summary['p95_seconds']:.2f}s rpm={summary['throughput_rpm']:.2f}",
        flush=True,
    )
    return summary, rows


def summarize_resources(samples: list[dict[str, Any]]) -> dict[str, Any]:
    valid_hosts = [s for s in samples if s.get("host_available_bytes") is not None]
    containers: dict[str, dict[str, float]] = {}
    for sample in samples:
        for name, values in sample.get("containers", {}).items():
            current = containers.setdefault(name, {"max_cpu_percent": 0.0, "max_memory_mib": 0.0})
            current["max_cpu_percent"] = max(current["max_cpu_percent"], values["cpu_percent"])
            current["max_memory_mib"] = max(current["max_memory_mib"], values["memory_mib"])
    return {
        "samples": len(samples),
        "sample_errors": sum(bool(s.get("error")) for s in samples),
        "min_host_available_gib": (
            round(min(s["host_available_bytes"] for s in valid_hosts) / 1024**3, 2)
            if valid_hosts
            else None
        ),
        "max_host_used_gib": (
            round(max(s["host_used_bytes"] for s in valid_hosts) / 1024**3, 2)
            if valid_hosts
            else None
        ),
        "containers": containers,
    }


def write_report(
    path: Path,
    args: argparse.Namespace,
    summaries: list[dict[str, Any]],
    resources: dict[str, Any],
) -> None:
    lines = [
        f"# Onyx {args.mode.title()} Load Test",
        "",
        f"- Run time: {datetime.now().isoformat(timespec='seconds')}",
        f"- Base URL: {args.base_url}",
        f"- Agent ID: {args.agent_id}" if args.mode == "agent" else f"- Document set: {args.document_set}",
        f"- Host resource samples: {resources['samples']} (errors: {resources['sample_errors']})",
        "",
        "## Load results",
        "",
        "| Level | Concurrency | Requests | Success | RPM | P50 | P95 | P99 | Max |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in summaries:
        lines.append(
            f"| {item['label']} | {item['concurrency']} | {item['requests']} | "
            f"{item['success_rate']:.1%} | {item['throughput_rpm']:.2f} | "
            f"{item['p50_seconds']:.2f}s | {item['p95_seconds']:.2f}s | "
            f"{item['p99_seconds']:.2f}s | {item['max_seconds']:.2f}s |"
        )
    lines.extend(
        [
            "",
            "## Resource peaks",
            "",
            f"- Minimum host available memory: {resources['min_host_available_gib']} GiB",
            f"- Maximum host used memory: {resources['max_host_used_gib']} GiB",
            "",
            "| Container | Max CPU | Max memory |",
            "|---|---:|---:|",
        ]
    )
    for name, values in sorted(
        resources["containers"].items(),
        key=lambda item: item[1]["max_cpu_percent"],
        reverse=True,
    ):
        lines.append(
            f"| {name} | {values['max_cpu_percent']:.2f}% | {values['max_memory_mib']:.1f} MiB |"
        )
    lines.extend(
        [
            "",
            "## Scope and interpretation",
            "",
            "This is a bounded development-environment test, not a production capacity guarantee. "
            "Agent-mode latency includes retrieval, orchestration, and the external LLM provider. "
            "Retrieval mode isolates the local search path more closely. A larger stress or soak test "
            "must define an explicit cost budget and protect upstream APIs with rate limits.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    token = load_token(args.token_file)
    questions = load_questions(args.questions, args.ids)
    levels = [int(item) for item in args.levels.split(",") if item.strip()]
    args.results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Warm-up request (excluded from metrics)...", flush=True)
    warmup = execute_request(args, token, questions[0], 0)
    if not warmup["success"]:
        raise RuntimeError(f"Warm-up failed: {warmup['error']}")

    sampler = ResourceSampler(args.ssh_host, args.ssh_key, args.sample_interval)
    sampler.start()
    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    try:
        offset = 0
        for concurrency in levels:
            summary, rows = run_level(
                args,
                token,
                questions,
                f"load-c{concurrency}",
                concurrency,
                args.requests_per_level,
                offset,
            )
            summaries.append(summary)
            all_rows.extend(rows)
            offset += args.requests_per_level
            time.sleep(args.cooldown)
        if args.spike_concurrency > 0 and args.spike_requests > 0:
            summary, rows = run_level(
                args,
                token,
                questions,
                "spike",
                args.spike_concurrency,
                args.spike_requests,
                offset,
            )
            summaries.append(summary)
            all_rows.extend(rows)
    finally:
        sampler.stop()

    resources = summarize_resources(sampler.samples)
    json_path = args.results_dir / f"{args.mode}_load_{stamp}.json"
    resource_path = args.results_dir / f"{args.mode}_resources_{stamp}.json"
    report_path = args.results_dir / f"{args.mode}_load_{stamp}.md"
    json_path.write_text(
        json.dumps({"summaries": summaries, "requests": all_rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    resource_path.write_text(json.dumps(sampler.samples, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(report_path, args, summaries, resources)
    print(f"RESULTS: {json_path}")
    print(f"RESOURCES: {resource_path}")
    print(f"REPORT: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

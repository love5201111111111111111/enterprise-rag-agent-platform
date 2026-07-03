#!/usr/bin/env python3
"""CI checks for datasets, accidental credentials, and container hardening."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {".git", ".secrets", ".venv", "__pycache__", ".pytest_cache"}
TEXT_SUFFIXES = {
    ".csv",
    ".env",
    ".example",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".txt",
    ".yaml",
    ".yml",
}
SECRET_PATTERNS = {
    "Onyx PAT": re.compile(r"onyx_pat_[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"(?:github_pat_|ghp_)[A-Za-z0-9_-]{20,}"),
    "model API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix.lower() == ".pem":
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in {"Dockerfile", ".gitignore"}:
            files.append(path)
    return files


def validate_csv(relative: str, expected_count: int) -> None:
    path = ROOT / relative
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ids = [row.get("id", "") for row in rows]
    if len(rows) != expected_count:
        raise ValueError(f"{relative}: expected {expected_count} rows, found {len(rows)}")
    if len(set(ids)) != len(ids) or not all(ids):
        raise ValueError(f"{relative}: IDs must be present and unique")


def scan_secrets() -> None:
    findings: list[str] = []
    for path in iter_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: possible {label}")
    if findings:
        raise ValueError("Potential credentials found:\n" + "\n".join(findings))


def validate_container_policy() -> None:
    dockerfile = (ROOT / "cloudorder-ops-api" / "Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "cloudorder-ops-api" / "docker-compose.yml").read_text(encoding="utf-8")
    required_dockerfile = ("USER app", "HEALTHCHECK")
    required_compose = (
        "read_only: true",
        "no-new-privileges:true",
        "cap_drop:",
        "memory: 512M",
    )
    for marker in required_dockerfile:
        if marker not in dockerfile:
            raise ValueError(f"Dockerfile missing security marker: {marker}")
    for marker in required_compose:
        if marker not in compose:
            raise ValueError(f"docker-compose.yml missing security marker: {marker}")
    if re.search(r"privileged:\s*true", compose, flags=re.IGNORECASE):
        raise ValueError("docker-compose.yml must not enable privileged mode")


def main() -> int:
    required = (
        "README.md",
        "cloudorder-ops-api/Dockerfile",
        "cloudorder-ops-api/docker-compose.yml",
        "enterprise-rag-dataset/evaluation/golden_questions.csv",
        "enterprise-rag-dataset/evaluation/mall_golden_questions.csv",
    )
    missing = [item for item in required if not (ROOT / item).exists()]
    if missing:
        raise ValueError(f"Missing required files: {', '.join(missing)}")

    validate_csv("enterprise-rag-dataset/evaluation/golden_questions.csv", 50)
    validate_csv("enterprise-rag-dataset/evaluation/mall_golden_questions.csv", 20)
    scan_secrets()
    validate_container_policy()
    print("Project validation passed: 50 CloudOrder questions, 20 Mall questions, no credential leaks.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VALIDATION_ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)

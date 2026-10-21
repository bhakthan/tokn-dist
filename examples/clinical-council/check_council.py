"""Offline structural check for council verdict bundles and an illustrate spec.

Reads local files only and uses only the standard library. No network calls.
It checks shape and ranges. It does not run the TOKN council logic; use
`tokn council chair` for that.

Usage: python check_council.py verdicts/*.json illustrate-spec.json
"""

import json
import sys

SCHEMA = "council-verdict/1.1"
DISPOSITIONS = {"approve", "approve_with_notes", "reject", "abstain"}
SPEC_KEYS = {"slug", "title", "prompt", "size", "page"}


def check_bundle(path, data):
    problems = []
    if data.get("schema") not in {SCHEMA, "council-verdict/1.0"}:
        problems.append(f"unexpected schema {data.get('schema')!r}")
    question = data.get("question") or {}
    if not question.get("id"):
        problems.append("question.id is missing")
    verdict = data.get("verdict") or {}
    if not verdict.get("peer"):
        problems.append("verdict.peer is missing")
    if verdict.get("disposition") not in DISPOSITIONS:
        problems.append(f"unknown disposition {verdict.get('disposition')!r}")
    metric = verdict.get("convergenceMetric")
    if not isinstance(metric, (int, float)) or not 0 <= metric <= 1:
        problems.append(f"convergenceMetric must be between 0 and 1, got {metric!r}")
    if not verdict.get("consumesSpec"):
        problems.append("consumesSpec is missing (the chair bars it by default)")
    return problems


def check_spec(path, data):
    problems = []
    if not isinstance(data, list) or not data:
        return ["spec must be a non-empty JSON array"]
    for index, entry in enumerate(data):
        missing = SPEC_KEYS - set(entry)
        if missing:
            problems.append(f"entry {index} is missing {sorted(missing)}")
    return problems


def check(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"{path}: PROBLEM: {exc}")
        return 1

    if path.endswith("illustrate-spec.json"):
        problems = check_spec(path, data)
    else:
        problems = check_bundle(path, data)

    if problems:
        for problem in problems:
            print(f"{path}: PROBLEM: {problem}")
        return 1
    print(f"{path}: ok (structural checks only)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(max(check(p) for p in sys.argv[1:]))

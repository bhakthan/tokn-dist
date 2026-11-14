#!/usr/bin/env python3
"""check.py - read-only check of out/report.json, plus a reading table.

Structural checks decide the exit code. The report must have schema_version 1,
a digest starting with sha256:, run.claim_ref CLM-DEMO-0001, 7 distinct damage
points, 49 records (7 checks per point), statuses from the allowed set, and
summary counts that match the records.

The table is for reading, not grading. It lists the three highest P(yes)
checks per point. A * marks a check the demo photos show, and the last column
gives the ground truth for each point. Nothing here decides a claim.

Usage:
  python check.py [REPORT]

REPORT defaults to out/report.json next to this script. No network calls.
Exit codes: 0 structure ok, 1 structural failure, 2 report missing or unreadable.
"""
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLAIM_REF = "CLM-DEMO-0001"
EXPECTED_POINTS = 7
EXPECTED_CHECKS_PER_POINT = 7
ALLOWED_STATUS = {"corroborated", "clear", "adjuster_referral"}

# Ground truth for the three demo photos (see README). None means not labelled.
TRUTH = {
    "windshield": {"crack", "broken"},
    "hood": {"dent"},
    "front bumper": set(),
    "left mirror": {"crack", "broken"},
    "van rear side": {"broken", "dent"},
    "van front bumper": None,
    "van windshield": {"crack"},
}


def p_yes(rec: dict):
    label = rec.get("label")
    p = rec.get("probability")
    if label not in ("yes", "no") or not isinstance(p, (int, float)):
        return None
    return float(p) if label == "yes" else 1.0 - float(p)


def structural_problems(report: dict) -> list:
    problems = []
    if report.get("schema_version") != 1:
        problems.append(f"schema_version is {report.get('schema_version')!r}, expected 1")
    digest = report.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        problems.append("digest does not start with sha256:")
    claim = (report.get("run") or {}).get("claim_ref")
    if claim != CLAIM_REF:
        problems.append(f"run.claim_ref is {claim!r}, expected {CLAIM_REF!r}")

    names = [p.get("name") for p in report.get("points", [])]
    if len(set(names)) != EXPECTED_POINTS:
        problems.append(f"found {len(set(names))} distinct damage points, expected {EXPECTED_POINTS}")

    records = report.get("records", [])
    if len(records) != EXPECTED_POINTS * EXPECTED_CHECKS_PER_POINT:
        problems.append(f"found {len(records)} records, expected {EXPECTED_POINTS * EXPECTED_CHECKS_PER_POINT}")
    per_point = Counter(r.get("point") for r in records)
    for name in set(names):
        if per_point.get(name, 0) != EXPECTED_CHECKS_PER_POINT:
            problems.append(f"point {name!r} has {per_point.get(name, 0)} records, expected {EXPECTED_CHECKS_PER_POINT}")

    statuses = Counter(r.get("status") for r in records)
    bad = sorted(str(s) for s in statuses if s not in ALLOWED_STATUS)
    if bad:
        problems.append("unknown record status: " + ", ".join(bad))

    summary = report.get("summary", {})
    expected = {
        "points": len(set(names)),
        "records": len(records),
        "corroborated": statuses.get("corroborated", 0),
        "clear": statuses.get("clear", 0),
        "adjuster_referrals": statuses.get("adjuster_referral", 0),
    }
    for key, want in expected.items():
        if summary.get(key) != want:
            problems.append(f"summary.{key} is {summary.get(key)!r}, records give {want}")
    return problems


def print_table(report: dict) -> None:
    by_point = {}
    for r in report.get("records", []):
        by_point.setdefault(r.get("point"), []).append(r)

    print(f"{'point':<18} {'referrals':>9}  {'top three P(yes)':<44} ground truth")
    for name in (p.get("name") for p in report.get("points", [])):
        mine = by_point.get(name, [])
        referrals = sum(1 for r in mine if r.get("status") == "adjuster_referral")
        scored = sorted(((p_yes(r), r.get("check_id")) for r in mine if p_yes(r) is not None), reverse=True)[:3]
        truth = TRUTH.get(name)
        shown = []
        for p, check in scored:
            mark = "*" if truth and check in truth else ""
            shown.append(f"{check}{mark} {p:.2f}")
        if truth is None:
            text = "(not labelled)"
        elif not truth:
            text = "no visible damage"
        else:
            text = ", ".join(sorted(truth))
        print(f"{name:<18} {referrals:>9}  {', '.join(shown):<44} {text}")
    print("* = the demo photo shows this damage. P(yes) is the record's probability, flipped for 'no' labels.")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out" / "report.json"
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[!] File not found: {path}. Run run-inspection first.", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as err:
        print(f"[!] Cannot read {path}: {err}", file=sys.stderr)
        return 2

    problems = structural_problems(report)
    if problems:
        for p in problems:
            print(f"Structure: {p}")
        print("FAIL: the report does not have the expected structure.")
        return 1

    summary = report["summary"]
    print(f"PASS: structure ok ({summary['points']} points, {summary['records']} records, claim {CLAIM_REF}).")
    print(f"Referrals: {summary['adjuster_referrals']} of {summary['records']}. Every referral needs an adjuster.")
    print()
    print_table(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())

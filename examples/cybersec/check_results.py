"""Smoke-check a cybersec triage result. Reads one local JSON file. No network.

Usage:  python check_results.py path\\to\\result.json

This is a text check on the run's output. It does not prove that any gate fired.
"""
import json
import re
import sys

ATTACK_ID = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")
BAD_CVE = "CVE-24-0017"


def main(path):
    failures = 0
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL  cannot read JSON result: {exc}")
        return 1

    for key in ("status", "result", "errors"):
        ok = key in doc
        print(f"{'PASS' if ok else 'FAIL'}  top-level key '{key}' present")
        failures += 0 if ok else 1

    text = json.dumps(doc, ensure_ascii=False)

    ok = "TLP:RED" not in text
    print(f"{'PASS' if ok else 'FAIL'}  no TLP:RED content in output")
    failures += 0 if ok else 1

    ok = "TLP:" in text
    print(f"{'PASS' if ok else 'WARN'}  output carries a TLP label")

    ok = bool(ATTACK_ID.search(text))
    print(f"{'PASS' if ok else 'WARN'}  at least one ATT&CK technique ID (T####) cited")

    ok = "PermitRootLogin" in text
    print(f"{'PASS' if ok else 'WARN'}  root login finding mentions PermitRootLogin")

    if BAD_CVE in text:
        print(f"WARN  {BAD_CVE} appears in output; confirm it is labelled unverified, not scored")
    else:
        print(f"PASS  malformed {BAD_CVE} not repeated as a verified CVE")

    print("\nFailures:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

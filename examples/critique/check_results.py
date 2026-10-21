"""Smoke-check a critique run's result. Reads one local JSON file. No network.

Usage:  python check_results.py path\\to\\result.json

This is a text check on the output. It does not prove that the roles ran or that
any model agreed with another.
"""
import json
import re
import sys

ROLES = ["adversary", "synthesizer", "pragmatist", "visionary",
         "domain_expert", "user_advocate", "contrarian", "integrator"]

# Each planted flaw in design-proposal.md, matched by a loose keyword.
PLANTED = {
    "personal data and retention": r"retention|personal data|privacy",
    "classifier single point of failure": r"single point of failure|fallback|outage|unavailable",
    "unmeasurable success metric": r"measur|metric|baseline",
    "undefined escalation path": r"escalat",
}


def main(path):
    failures = 0
    try:
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL  cannot read JSON result: {exc}")
        return 1

    ok = "result" in doc
    print(f"{'PASS' if ok else 'FAIL'}  top-level key 'result' present")
    failures += 0 if ok else 1

    text = json.dumps(doc, ensure_ascii=False).lower()

    present = [r for r in ROLES if r.replace("_", " ") in text or r in text]
    status = "PASS" if len(present) == len(ROLES) else "WARN"
    print(f"{status}  role names cited: {len(present)}/{len(ROLES)}")

    ok = "dissent" in text
    print(f"{'PASS' if ok else 'WARN'}  dissent is reported")

    ok = "converg" in text or "confidence" in text
    print(f"{'PASS' if ok else 'WARN'}  convergence or confidence is stated")

    for label, pattern in PLANTED.items():
        ok = re.search(pattern, text) is not None
        print(f"{'PASS' if ok else 'WARN'}  raised: {label}")

    print("\nFailures:", failures)
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

"""Read-only checker for the precmed-variant example.

Reads ONE local file you saved from a run:
    tokn agent-run --mode precmed ... --output-format json > result.json

It makes no network calls and writes nothing. `--output-format json` returns a
single object (status, result, exit_code, steps, usage, errors), and the gate
evidence is usually free text inside `result`. So this script searches the whole
file for each gate name and reports where it is mentioned. A mention is NOT a
pass: read the sentence around it.

Usage:  python check_gates.py result.json
"""

import json
import sys

EXPECTED = {
    "acmg_vus_gate": "VUS must not become an actionable recommendation",
    "pgx_critical_contraindication": "CRITICAL pharmacogenomic block",
    "pgx_contraindication": "PGx contraindication hard block",
    "somatic_germline": "somatic and germline kept separate",
    "research_phi": "research/PHI gate before cohort use",
}


def flatten(node, out):
    if isinstance(node, dict):
        for value in node.values():
            flatten(value, out)
    elif isinstance(node, list):
        for value in node:
            flatten(value, out)
    elif isinstance(node, str):
        out.append(node)
    return out


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        data = json.load(fh)

    if isinstance(data, dict) and "status" in data:
        print(f"run status: {data.get('status')}  exit_code: {data.get('exit_code')}")
    text = "\n".join(flatten(data, []))

    print(f"{'gate':<32} {'mentions':<9} what it should show")
    not_seen = []
    for name, meaning in EXPECTED.items():
        count = text.count(name)
        print(f"{name:<32} {count:<9} {meaning}")
        if count == 0:
            not_seen.append(name)

    print()
    if not_seen:
        print("Not mentioned at all: " + ", ".join(not_seen))
        print("That can be a finding (the step was not reached) or a wording difference.")
        print("Check the prompt steps and the run transcript before drawing a conclusion.")
    else:
        print("Every expected gate is mentioned. Read each sentence to confirm the outcome.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

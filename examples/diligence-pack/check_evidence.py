"""Deterministic diligence-evidence checker for the Quillstone example.

Reads only local files:
  inputs/contracts-register.csv      (source contract list)
  diligence-pack/arr-register.json   (the agent's output, optional)

No network access, no credentials, no environment variables.

Usage:
    python check_evidence.py [pack-dir]

Exit code 0 = the agent's ARR figures match the source contract list and no
MOU or verbal commitment is counted as authoritative.
Exit code 1 = a mismatch or a non-authoritative contract was counted.
"""
import csv
import json
import sys
from pathlib import Path

AUTHORITATIVE = {"executed", "auto-renewed"}
TOLERANCE_USD = 1.0


def load_contracts(csv_path):
    with csv_path.open(encoding="utf-8", newline="") as fh:
        return [
            {
                "customer": row["Customer"],
                "status": row["Status"].strip().lower(),
                "arr": float(row["ARR (USD)"]),
                "coc": row["Change-of-control right"].strip().lower() == "yes",
            }
            for row in csv.DictReader(fh)
        ]


def main():
    pack = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("diligence-pack")
    contracts = load_contracts(Path("inputs") / "contracts-register.csv")

    total = sum(c["arr"] for c in contracts)
    authoritative = sum(c["arr"] for c in contracts if c["status"] in AUTHORITATIVE)
    quarantined = total - authoritative
    top2 = sorted((c["arr"] for c in contracts if c["status"] == "executed"),
                  reverse=True)[:2]
    executed_total = sum(c["arr"] for c in contracts if c["status"] == "executed")
    concentration = sum(top2) / executed_total if executed_total else 0.0
    coc_customers = [c["customer"] for c in contracts if c["coc"]]

    print(f"Management stated ARR     : ${total / 1e6:,.1f}M")
    print(f"Authoritative ARR         : ${authoritative / 1e6:,.1f}M")
    print(f"Quarantined (MOU/verbal)  : ${quarantined / 1e6:,.1f}M")
    print(f"Top-2 share of executed   : {concentration:.1%}")
    print(f"Change-of-control holders : {', '.join(coc_customers)}")

    failures = 0
    reg_path = pack / "arr-register.json"
    if not reg_path.exists():
        print(f"\nNo {reg_path} yet. Source figures printed above; re-run after the agent writes it.")
        return 0

    reg = json.loads(reg_path.read_text(encoding="utf-8"))
    for row in reg.get("contracts", []):
        status = str(row.get("status", "")).lower()
        if row.get("authoritative") and status not in AUTHORITATIVE:
            print(f"FAIL: {row.get('customer', '?')} ({status}) counted as authoritative")
            failures += 1

    claimed = reg.get("authoritative_arr_usd")
    if claimed is None or abs(float(claimed) - authoritative) > TOLERANCE_USD:
        print(f"FAIL: register authoritative ARR {claimed} != source {authoritative:,.0f}")
        failures += 1

    if failures:
        print(f"\nFAIL: {failures} problem(s).")
        return 1
    print("\nPASS: register matches the source and no non-authoritative contract is counted.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

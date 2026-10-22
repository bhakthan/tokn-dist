"""Offline covenant arithmetic for the credit-underwriting example.

Reads one local applicant file of key: value lines and recomputes the three covenant ratios.
Standard library only. No network calls, no writes.

Usage:
    python check_ratios.py applicant/synthetic-file-0042.md
"""

import re
import sys

LINE = re.compile(r"^([a-z_]+):\s*(.+?)\s*$")


def load(path):
    values = {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            m = LINE.match(raw.strip())
            if not m:
                continue
            key, val = m.group(1), m.group(2)
            try:
                values[key] = float(val)
            except ValueError:
                values[key] = val
    return values


def ratios(v):
    dscr = (v["ebitda_k"]) / (v["interest_expense_k"] + v["principal_due_k"])
    leverage = v["total_debt_k"] / v["ebitda_k"]
    current = v["current_assets_k"] / v["current_liabilities_k"]
    return {"dscr": dscr, "leverage_x": leverage, "current_ratio": current}


def covenant_checks(v, r):
    return [
        ("DSCR >= min_dscr", r["dscr"] >= v["min_dscr"], r["dscr"], v["min_dscr"]),
        ("leverage <= max_leverage_x", r["leverage_x"] <= v["max_leverage_x"], r["leverage_x"], v["max_leverage_x"]),
        ("current ratio >= min_current_ratio", r["current_ratio"] >= v["min_current_ratio"], r["current_ratio"], v["min_current_ratio"]),
    ]


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    v = load(argv[1])
    required = [
        "ebitda_k", "interest_expense_k", "principal_due_k", "total_debt_k",
        "current_assets_k", "current_liabilities_k", "min_dscr", "max_leverage_x", "min_current_ratio",
    ]
    missing = [k for k in required if k not in v]
    if missing:
        print("FAIL: missing fields:", ", ".join(missing))
        return 1
    r = ratios(v)
    failed = 0
    for label, ok, got, limit in covenant_checks(v, r):
        print(f"{'PASS' if ok else 'BREACH'}: {label}  (computed {got:.2f}, limit {limit:.2f})")
        failed += 0 if ok else 1
    return 0 if failed == 0 else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))

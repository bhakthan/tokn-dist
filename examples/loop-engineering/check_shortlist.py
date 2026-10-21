"""Shortlist checker for the loop-engineering walkthrough.

Stdlib only. Reads properties.csv, scoring.json, and shortlist.csv from the
folder this script lives in. It makes no network calls.

Exit code 0 means the shortlist meets every rule. Exit code 1 means at least
one rule failed; each failure is printed on its own line.
"""

import csv
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
PROPERTIES = os.path.join(ROOT, "properties.csv")
SCORING = os.path.join(ROOT, "scoring.json")
SHORTLIST = os.path.join(ROOT, "shortlist.csv")


def load_candidates():
    with open(PROPERTIES, newline="", encoding="utf-8") as fh:
        return {row["candidate_id"]: row for row in csv.DictReader(fh)}


def passes(row, criteria):
    return (
        float(row["activity_index"]) >= criteria["activity_index_min"]
        and float(row["stability_index"]) >= criteria["stability_index_min"]
        and int(row["liability_flag"]) <= criteria["liability_flag_max"]
    )


def main():
    with open(SCORING, encoding="utf-8") as fh:
        scoring = json.load(fh)
    candidates = load_candidates()
    weights = scoring["weights"]
    criteria = scoring["criteria"]
    tolerance = scoring["composite_tolerance"]

    if not os.path.exists(SHORTLIST):
        print("FAIL: shortlist.csv not found")
        return 1

    failures = []
    seen = set()
    with open(SHORTLIST, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    if len(rows) != scoring["shortlist_size"]:
        failures.append(
            f"shortlist has {len(rows)} rows; expected {scoring['shortlist_size']}"
        )

    for row in rows:
        cid = (row.get("candidate_id") or "").strip()
        if cid not in candidates:
            failures.append(f"{cid or '<blank>'}: not in properties.csv")
            continue
        if cid in seen:
            failures.append(f"{cid}: listed more than once")
        seen.add(cid)
        source = candidates[cid]
        if not passes(source, criteria):
            failures.append(f"{cid}: does not meet every criterion")
        recomputed = sum(
            weights[name] * float(source[name]) for name in weights
        )
        try:
            reported = float(row.get("composite_score", ""))
        except ValueError:
            failures.append(f"{cid}: composite_score is not a number")
            continue
        if abs(reported - recomputed) > tolerance:
            failures.append(
                f"{cid}: composite_score {reported} differs from recomputed {recomputed:.2f}"
            )

    qualifying = sorted(
        (
            (sum(weights[n] * float(r[n]) for n in weights), cid)
            for cid, r in candidates.items()
            if passes(r, criteria)
        ),
        reverse=True,
    )
    best = {cid for _, cid in qualifying[: scoring["shortlist_size"]]}
    if seen and seen != best and len(seen) == scoring["shortlist_size"]:
        failures.append(
            "shortlist is not the top five by composite_score; "
            f"expected {sorted(best)}"
        )

    if failures:
        for line in failures:
            print(f"FAIL: {line}")
        return 1
    print(f"PASS: {len(rows)} candidates meet every criterion and the composite scores check out")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Offline check of O3 and PM2.5 evaluation metrics.

Reads data/modelled_vs_observed.csv next to this file. Standard library only;
no network. Limits are the atmchem evaluation defaults: O3 NMB within +/-15 %
and r2 >= 0.60; PM2.5 NMB within +/-30 % and r2 >= 0.50.
Exit code 1 means at least one species fails the evaluation gate.
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

LIMITS = {"O3": (15.0, 0.60), "PM2.5": (30.0, 0.50)}


def pearson_r2(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return (sxy * sxy) / (sxx * syy)


def main():
    here = Path(__file__).resolve().parent
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else here / "data" / "modelled_vs_observed.csv"

    pairs = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            pairs[row["species"]].append((float(row["observed"]), float(row["modelled"])))

    failed = []
    for species, (nmb_limit, r2_min) in LIMITS.items():
        rows = pairs.get(species, [])
        obs = [o for o, _ in rows]
        mod = [m for _, m in rows]
        nmb = (sum(mod) - sum(obs)) / sum(obs) * 100.0
        r2 = pearson_r2(obs, mod)
        verdict = "PASS" if abs(nmb) <= nmb_limit and r2 >= r2_min else "FAIL"
        if verdict == "FAIL":
            failed.append(species)
        print(f"{species:<6} n={len(rows)}  NMB={nmb:+6.2f}% (limit +/-{nmb_limit:.0f}%)  "
              f"r2={r2:.3f} (min {r2_min:.2f})  -> {verdict}")

    if failed:
        print("Evaluation gate FAILED for: " + ", ".join(failed) + ". Do not claim compliance for these.")
        return 1
    print("Evaluation gate passed for all species.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

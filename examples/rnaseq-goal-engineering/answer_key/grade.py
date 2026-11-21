#!/usr/bin/env python3
"""Grade a solver's results table against the hidden truth (stdlib only).

Run this from OUTSIDE the agent's workspace, after the agent has finished.

Usage:
    python answer_key/grade.py RESULTS.tsv [--report REPORT.md] [--alpha 0.05]
                               [--truth answer_key/truth.tsv] [--counts case/counts.tsv]

Thresholds below MUST match case/TASK.md "Acceptance criteria".
Exit status 0 = PASS, 1 = FAIL, 2 = unreadable input.

Besides PASS/FAIL it prints each numeric criterion's relative margin,
(observed - bound) / bound for a floor and (bound - observed) / bound for a
ceiling. A negative margin fails; 0 <= margin < 0.05 is a NEAR MISS: it passes,
but one more design like it could fail (the Lagarias-style relative gap; see
checks/lagarias_stress_gate.py). The margins never change the exit status.
"""
import argparse
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED_COLS = ["gene_id", "baseMean", "log2FoldChange", "pvalue", "padj"]
MIN_PRECISION = 0.80        # TP / calls            (calls: padj < alpha)
MAX_FDR = 0.10              # 1 - precision, same quantity, stated as a ceiling
MIN_RECALL = 0.70           # TP / true DE genes (batch-ignoring analyses fall below this)
MIN_LFC_CORR = 0.90         # Pearson r on true-DE genes that have a finite LFC
MIN_CALLS = 20              # guards against an empty / degenerate call set
MAX_LOWCOUNT_TESTED = 0.25  # of genes with mean raw count < 1, max share given a finite padj
MIN_COVERAGE = 0.95         # share of true-DE genes that must appear in the table (tested)
NEAR_MISS = 0.05            # relative margin below which a passing criterion is flagged


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return v


def read_tsv(path):
    with open(path, newline="") as fh:
        lines = [l.rstrip("\r\n").split("\t") for l in fh if l.strip()]
    return lines[0], lines[1:]


def pearson(x, y):
    n = len(x)
    if n < 3:
        return float("nan")
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    syy = sum((b - my) ** 2 for b in y)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(sxx * syy)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--report", default=None)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--truth", default=os.path.join(HERE, "truth.tsv"))
    ap.add_argument("--counts", default=os.path.join(HERE, "..", "case", "counts.tsv"))
    a = ap.parse_args()

    try:
        _, trows = read_tsv(a.truth)
        truth = {r[0]: (int(r[1]), float(r[2])) for r in trows}
        hdr, rows = read_tsv(a.results)
    except Exception as e:  # noqa: BLE001
        print(f"Could not read inputs: {e}")
        return 2

    checks = []  # (name, ok, detail)
    margins = []  # (criterion, relative margin)

    def chk(name, ok, detail):
        checks.append((name, bool(ok), detail))

    def margin(name, observed, bound, ceiling=False):
        if observed is None or (isinstance(observed, float) and not math.isfinite(observed)):
            margins.append((name, -1.0))
        else:
            margins.append((name, ((bound - observed) if ceiling else (observed - bound)) / bound))

    # ---- schema / integrity ------------------------------------------------
    missing = [c for c in REQUIRED_COLS if c not in hdr]
    chk("schema: required columns", not missing,
        "missing: " + ",".join(missing) if missing else "all present")
    if missing:
        return finish(checks)
    col = {c: hdr.index(c) for c in hdr}
    res = {}
    dup = 0
    for r in rows:
        if len(r) < len(hdr):
            r = r + [""] * (len(hdr) - len(r))
        g = r[col["gene_id"]]
        if g in res:
            dup += 1
        res[g] = (num(r[col["log2FoldChange"]]), num(r[col["pvalue"]]), num(r[col["padj"]]))
    unknown = [g for g in res if g not in truth]
    chk("integrity: unique known gene_ids", dup == 0 and not unknown,
        f"duplicates={dup} unknown_ids={len(unknown)}")
    bad_p = [g for g, (_, p, q) in res.items()
             if (not math.isnan(p) and not 0 <= p <= 1) or (not math.isnan(q) and not 0 <= q <= 1)]
    chk("integrity: pvalue/padj within [0,1]", not bad_p, f"violations={len(bad_p)}")
    # padj must not be smaller than raw p (BH never decreases a p-value)
    shrunk = [g for g, (_, p, q) in res.items()
              if not math.isnan(p) and not math.isnan(q) and q < p - 1e-12]
    chk("integrity: padj >= pvalue (BH-consistent)", not shrunk, f"violations={len(shrunk)}")

    # ---- accuracy ----------------------------------------------------------
    calls = {g for g, (_, _, q) in res.items() if g in truth and not math.isnan(q) and q < a.alpha}
    de = {g for g, (d, _) in truth.items() if d == 1}
    tp = len(calls & de)
    n_calls = len(calls)
    precision = tp / n_calls if n_calls else 0.0
    fdr = (n_calls - tp) / n_calls if n_calls else float("nan")
    recall = tp / len(de)
    tested_de = [g for g in de if g in res and not math.isnan(res[g][2])]
    coverage = len(tested_de) / len(de)
    pairs = [(truth[g][1], res[g][0]) for g in de if g in res and not math.isnan(res[g][0])]
    r_lfc = pearson([p[0] for p in pairs], [p[1] for p in pairs]) if pairs else float("nan")
    sign_ok = (sum(1 for t, e in pairs if t * e > 0) / len(pairs)) if pairs else float("nan")

    chk(f"calls: at least {MIN_CALLS} genes with padj < {a.alpha}", n_calls >= MIN_CALLS, f"calls={n_calls}")
    chk(f"precision >= {MIN_PRECISION}", precision >= MIN_PRECISION, f"precision={precision:.3f} (TP={tp})")
    chk(f"empirical FDR <= {MAX_FDR}", (not math.isnan(fdr)) and fdr <= MAX_FDR, f"FDR={fdr:.3f}")
    chk(f"recall >= {MIN_RECALL}", recall >= MIN_RECALL, f"recall={recall:.3f} ({tp}/{len(de)})")
    chk(f"true-DE coverage (finite padj) >= {MIN_COVERAGE}", coverage >= MIN_COVERAGE,
        f"coverage={coverage:.3f}")
    margin("calls", n_calls, MIN_CALLS)
    margin("precision", precision, MIN_PRECISION)
    margin("empirical FDR", fdr, MAX_FDR, ceiling=True)
    margin("recall", recall, MIN_RECALL)
    margin("coverage", coverage, MIN_COVERAGE)
    margin("log2FC r", r_lfc, MIN_LFC_CORR)
    chk(f"log2FC Pearson r on true DE >= {MIN_LFC_CORR}",
        (not math.isnan(r_lfc)) and r_lfc >= MIN_LFC_CORR,
        f"r={r_lfc:.3f}, sign agreement={sign_ok:.3f}, n={len(pairs)}")

    # ---- low-count filtering ----------------------------------------------
    try:
        _, crows = read_tsv(a.counts)
        lowset = []
        for r in crows:
            vals = [int(x) for x in r[1:]]
            if sum(vals) / len(vals) < 1.0:
                lowset.append(r[0])
        tested_low = sum(1 for g in lowset if g in res and not math.isnan(res[g][2]))
        share = tested_low / len(lowset) if lowset else 0.0
        margin("low-count share", share, MAX_LOWCOUNT_TESTED, ceiling=True)
        chk(f"filtering: <= {MAX_LOWCOUNT_TESTED:.0%} of genes with mean raw count < 1 receive a padj",
            share <= MAX_LOWCOUNT_TESTED, f"{tested_low}/{len(lowset)} = {share:.3f}")
    except Exception as e:  # noqa: BLE001
        chk("filtering check", False, f"could not read counts: {e}")

    # ---- report ------------------------------------------------------------
    if a.report:
        try:
            txt = open(a.report, encoding="utf-8").read()
            has_qc = re.search(r"^\s*#+\s*.*\bQC\b", txt, re.I | re.M) is not None
            chk("report: has a QC section heading", has_qc, "found" if has_qc else "no heading containing 'QC'")
            margin("report words", len(txt.split()), 150)
            chk("report: non-trivial length (>= 150 words)", len(txt.split()) >= 150,
                f"words={len(txt.split())}")
        except Exception as e:  # noqa: BLE001
            chk("report: readable", False, str(e))

    return finish(checks, margins)


def finish(checks, margins=()):
    print("== Grading ==")
    for name, ok, detail in checks:
        print(f"[{'ok' if ok else 'XX'}] {name}: {detail}")
    if margins:
        print("== Relative margins (report-only) ==")
        for name, m in margins:
            tag = "XX" if m < 0 else ("~~ NEAR MISS" if m < NEAR_MISS else "ok")
            print(f"[{tag}] {name}: {m:+.3f}")
        name, m = min(margins, key=lambda x: x[1])
        print(f"min criterion margin: {m:+.3f} ({name})")
    allok = all(ok for _, ok, _ in checks)
    print("RESULT: " + ("PASS" if allok else "FAIL"))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())

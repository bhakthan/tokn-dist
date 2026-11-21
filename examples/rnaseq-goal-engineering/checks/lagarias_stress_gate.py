#!/usr/bin/env python3
"""Truth-free stress-gap check for a goal-scope run (numpy + stdlib).

Run the recorded scope check before review. It never reads the answer key. It turns the scope's lessons into scalar inequalities and reports each
one as a relative gap, (bound - observed) / bound for a ceiling and
(observed - bound) / bound for a floor:

  gap <= 0          counterexample: the run breaks the invariant (exit 1)
  0 < gap < 0.05    near miss: passes, but flagged for the reviewer (exit 0)

The idea comes from Lagarias's reformulation of the Riemann hypothesis
(sigma(n) <= H_n + exp(H_n) log H_n), where the margin, not just the sign, tells you
how close a case is to a counterexample. It is an analogy; nothing here is derived
from the Riemann hypothesis.

Checks
  bh_consistent       padj equals Benjamini-Hochberg of pvalue over tested genes (1e-6)
  reference_stated    the report names a Student t reference or likelihood-ratio test
                      (lesson: calibration)
  residual_df         the report states the residual df of expression ~ condition + batch
                      (lesson: calibration)
  lfc_agreement_r     Pearson r between the run's log2FC and an independent
                      batch-adjusted OLS log2FC on log2(CPM+1), genes with mean count
                      >= 10; advisory floor 0.90 (lesson: off-line-zero - a batch leak shows up as
                      a systematic disagreement that more samples do not remove)
  c2s_*               only with --c2s-audit: gene tokens outside the counts gene index
                      (ceiling 0) and C2S labels that marker evidence rejects
                      (ceiling 0.25) (lesson: analytic-continuation)

Usage
  python checks/lagarias_stress_gate.py --results work/solution/results.tsv \\
      --counts work/case/counts.tsv [--samples work/case/samples.tsv] \\
      [--report work/solution/report.md] [--c2s-audit work/solution/c2s_dual.json] [--json]

Exit 0 pass (near misses are warnings), 1 counterexample, 2 unreadable input.
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np

NEAR_MISS = 0.05
MIN_LFC_R = 0.90
MAX_C2S_DISAGREE = 0.25
DF_TERM = r"(?:df|d\.f\.|degrees\s+of\s+freedom)"
DF_RE = re.compile(rf"\bresidual\s+{DF_TERM}\s*(?:=|:|of|is|are|was|were)?\s*(\d+)\b"
                   rf"|\b(\d+)\s+residual\s+{DF_TERM}(?!\w)", re.I)
T_REF_RE = re.compile(r"\bstudent(?:['’]s)?\s*[- ]?t\b|\bt[- ](?:distribution|test|reference)\b"
                      r"|\blikelihood[- ]ratio(?: test)?\b|\bLRT\b", re.I)


def stated_reference(report):
    for m in T_REF_RE.finditer(report):
        before = report[max(0, m.start()-50):m.start()].lower()
        after = report[m.end():m.end()+32].lower()
        if not (re.search(r"\b(?:not|no|without|rather than|instead of|unlike)\s+(?:(?:using|a|an|the)\s+)*$", before)
                or re.match(r"\s+(?:was |is )?(?:not used|rejected)\b", after)):
            return True
    return False


def read_tsv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [ln.rstrip("\r\n").split("\t") for ln in fh if ln.strip()]
    if len(rows) < 2 or len(set(rows[0])) != len(rows[0]) or any(len(r) != len(rows[0]) for r in rows[1:]):
        raise ValueError(f"{path}: empty table, duplicate columns or inconsistent row widths")
    return rows[0], rows[1:]


def num(x):
    if x == "NA":
        return float("nan")
    v = float(x)
    if not math.isfinite(v):
        raise ValueError("expected a finite number or NA")
    return v


def bh(p):
    p = np.asarray(p, dtype=float)
    n = p.size
    order = np.argsort(p, kind="mergesort")
    ranked = np.minimum.accumulate((p[order] * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    return out


def gap_floor(observed, bound):
    return (observed - bound) / abs(bound) if bound else (1.0 if observed >= 0 else -1.0)


def gap_ceiling(observed, bound):
    return (bound - observed) / abs(bound) if bound else (1.0 if observed <= 0 else -1.0)


def batch_adjusted_lfc(counts, genes, samples):
    """OLS log2FC of condition on log2(CPM+1) with batch dummies, and the residual df."""
    ids = [s for s in samples if samples[s][0] in ("treated", "control")]
    y = np.array([[counts[g][s] for s in ids] for g in genes], dtype=float)
    lib = np.array([sum(counts[g][s] for g in counts) for s in ids], dtype=float)
    if (lib <= 0).any():
        raise ValueError("sample with an empty count library")
    y = np.log2(y / lib * 1e6 + 1.0)
    cols = [np.ones(len(ids)), np.array([samples[s][0] == "treated" for s in ids], dtype=float)]
    for lv in sorted({samples[s][1] for s in ids})[1:]:
        cols.append(np.array([samples[s][1] == lv for s in ids], dtype=float))
    x = np.column_stack(cols)
    beta, _, rank, _ = np.linalg.lstsq(x, y.T, rcond=None)
    if rank != x.shape[1] or len(ids) <= rank:
        raise ValueError("condition + batch is not identifiable or has no residual df")
    return beta[1], len(ids) - int(rank)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--results", required=True)
    ap.add_argument("--counts", required=True)
    ap.add_argument("--samples", default=None, help="default: samples.tsv beside --counts")
    ap.add_argument("--report", default=None, help="default: report.md beside --results")
    ap.add_argument("--c2s-audit", default=None,
                    help='optional JSON {"cells": [{"tokens": [...], "label": str, "verified": bool}]}')
    ap.add_argument("--require-lfc-agreement", action="store_true", help="gate the OLS comparison for comparable estimators; advisory by default")
    ap.add_argument("--json", action="store_true", help="print one JSON object instead of lines")
    a = ap.parse_args(argv)
    samples_path = a.samples or os.path.join(os.path.dirname(a.counts), "samples.tsv")
    report_path = a.report or os.path.join(os.path.dirname(a.results), "report.md")

    try:
        hdr, rows = read_tsv(a.results)
        if hdr != ["gene_id", "baseMean", "log2FoldChange", "pvalue", "padj"]:
            raise ValueError("unexpected results header; use the five columns in case/TASK.md in order")
        col = {c: i for i, c in enumerate(hdr)}
        res = {r[col["gene_id"]]: (num(r[col["log2FoldChange"]]), num(r[col["pvalue"]]), num(r[col["padj"]]))
               for r in rows}
        chdr, crows = read_tsv(a.counts)
        counts = {r[0]: dict(zip(chdr[1:], (int(v) for v in r[1:]))) for r in crows}
        shdr, srows = read_tsv(samples_path)
        si = {c: i for i, c in enumerate(shdr)}
        samples = {r[si["sample_id"]]: (r[si["condition"]], r[si["batch"]]) for r in srows}
        if "" in counts or "" in samples:
            raise ValueError("gene and sample IDs must not be empty")
        if len(counts) != len(crows) or len(res) != len(rows) or len(samples) != len(srows) or set(counts) != set(res):
            raise ValueError("expected unique IDs and one results row per input gene")
        if set(samples) != set(chdr[1:]) or {v[0] for v in samples.values()} != {"treated", "control"} or any(not b for _, b in samples.values()):
            raise ValueError("expected matching sample IDs, nonempty batches and exactly treated/control conditions")
        if any(x < 0 for row in counts.values() for x in row.values()):
            raise ValueError("counts cannot be negative")
        for gene, (lfc, pv, qv) in res.items():
            if all(math.isnan(x) for x in (lfc, pv, qv)):
                continue
            if not (math.isfinite(lfc) and 0 <= pv <= 1 and 0 <= qv <= 1):
                raise ValueError(f"{gene}: expected a finite effect and probabilities in [0,1], or three NA values")
        genes = [g for g in counts if math.isfinite(res[g][0]) and sum(counts[g].values()) >= 10 * len(samples)]
        lfc_ref, df = batch_adjusted_lfc(counts, genes or [next(iter(counts))], samples)
        with open(report_path, encoding="utf-8") as fh:
            report = fh.read()
    except (OSError, KeyError, ValueError, IndexError) as e:
        print(f"unreadable input: {e}", file=sys.stderr)
        return 2

    checks = []  # (name, relative gap, observed, bound, lesson)

    tested = [g for g, (_, p, _) in res.items() if not math.isnan(p)]
    p = np.array([res[g][1] for g in tested])
    q = np.array([res[g][2] for g in tested])
    dev = float(np.max(np.abs(bh(p) - q))) if tested else 1.0
    checks.append(("bh_consistent", gap_ceiling(dev, 1e-6), dev, 1e-6, "integrity"))

    t_ref = stated_reference(report)
    checks.append(("reference_stated", 1.0 if t_ref else -1.0, t_ref, True, "calibration"))

    stated = sorted({int(x) for m in DF_RE.findall(report) for x in m if x})
    checks.append(("residual_df", 1.0 if stated == [df] else -1.0, stated, df, "calibration"))

    observed = [res[g][0] for g in genes]
    r = (float(np.corrcoef(lfc_ref, observed)[0, 1]) if len(genes) >= 3 and np.ptp(lfc_ref) and np.ptp(observed) else None)
    checks.append(("lfc_agreement_r", gap_floor(r, MIN_LFC_R) if r is not None else -1.0, r, MIN_LFC_R, "off-line-zero"))

    if a.c2s_audit:
        try:
            with open(a.c2s_audit, encoding="utf-8") as fh:
                cells = json.load(fh)["cells"]
            if not isinstance(cells, list) or not cells or not all(isinstance(c, dict) and isinstance(c.get("tokens"), list)
                    and c["tokens"] and all(isinstance(t, str) and t for t in c["tokens"]) and isinstance(c.get("label"), str)
                    and type(c.get("verified")) is bool for c in cells):
                raise ValueError("cells must have nonempty string tokens, a label and a boolean verified flag")
        except (OSError, KeyError, TypeError, ValueError) as e:
            print(f"unreadable --c2s-audit: {e}", file=sys.stderr)
            return 2
        toks = [t for c in cells for t in c.get("tokens", [])]
        bad = sum(1 for t in toks if t not in counts) / len(toks) if toks else 1.0
        checks.append(("c2s_invalid_token_rate", gap_ceiling(bad, 0), bad, 0, "analytic-continuation"))
        lab = [c for c in cells if c.get("label") not in (None, "", "unassigned")]
        dis = sum(1 for c in lab if not c.get("verified")) / len(lab) if lab else 1.0
        checks.append(("c2s_euler_discrepancy", gap_ceiling(dis, MAX_C2S_DISAGREE), dis,
                       MAX_C2S_DISAGREE, "analytic-continuation"))

    gating = [c for c in checks if c[0] != "lfc_agreement_r" or a.require_lfc_agreement]
    worst = min(gating, key=lambda c: c[1])
    failed = [c[0] for c in gating if c[1] <= 0]
    near = [c[0] for c in gating if 0 < c[1] < NEAR_MISS]
    out = {"pass": not failed, "min_relative_gap": worst[1], "worst_check": worst[0], "residual_df_expected": df,
           "checks": [{"name": n, "relative_gap": g, "observed": o, "bound": b, "lesson": les, "gated": n != "lfc_agreement_r" or a.require_lfc_agreement}
                      for n, g, o, b, les in checks],
           "near_misses": near, "counterexamples": failed}
    if a.json:
        print(json.dumps(out, allow_nan=False))
    else:
        print("== Lagarias stress-gap check (truth-free) ==")
        for n, g, o, b, les in checks:
            tag = "advisory" if n == "lfc_agreement_r" and not a.require_lfc_agreement else "XX" if g <= 0 else ("~~" if g < NEAR_MISS else "ok")
            print(f"[{tag}] {n} ({les}): observed={o} bound={b} relative_gap={g}")
        print(f"min relative gap {worst[1]} at {worst[0]}" + (f"; NEAR MISS on {', '.join(near)}" if near else ""))
        print("RESULT: " + ("PASS" if out["pass"] else "FAIL"))
    return 0 if out["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

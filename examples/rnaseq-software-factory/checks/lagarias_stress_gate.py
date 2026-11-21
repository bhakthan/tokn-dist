#!/usr/bin/env python3
"""lagarias_stress_gate.py - an RH-inspired stress gate for RNA-seq DE and local C2S.

Ideas borrowed from the Lagarias form of the Riemann Hypothesis (sigma(n) <= H_n + e^H_n log H_n):

1. Elementary reduction: turn "is this pipeline valid?" into exact scalar inequalities.
2. Scale normalisation and stress cases: compare a normalised error load with a slowly
   rising ceiling, and rank designs by their smallest relative gap. The worst designs
   are the "highly composite" ones, where several small confounds stack up.
3. Trend vs. fluctuation: sampling error in this fixture typically shrinks like N^-1/2 (the
   "critical line", a = 0.5). Error that stays flat as N grows (a -> 1) points to a
   systematic bias, an "off-line zero", that small cases hide.
4. Two views of one system: exact count statistics (the additive side) and a local C2S
   model (the multiplicative side) should agree. Their disagreement is a measured term.
5. Passing finite tests is not a proof: every result here is evidence over the tested
   designs only.

This is an ANALOGY. The ceiling borrows the shape of the Lagarias bound (it grows like
log log n). The thresholds (0.05 gap, a <= 0.55, ...) are engineering choices, not
results derived from RH.

Used two ways:
  * imported by grade.py (factory test gate; it prints TOKN_METRIC lines),
  * python checks/lagarias_stress_gate.py --metrics-json m.json   (standalone).
Exit 0 = passed, 1 = failed, 2 = unreadable input.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Dict, List, Tuple

import numpy as np

EULER_GAMMA = 0.5772156649015329

MIN_RELATIVE_GAP = 0.05
MAX_OFF_LINE_A = 0.55
MAX_C2S_EULER = 0.25
MAX_GGUF_KL = 0.035


def lagarias_normalized_ceiling(n: int) -> float:
    """Numerical alpha(n)/n from Lagarias' theorem, alpha(n) = H_n + e^H_n log H_n, for n >= 2."""
    if n < 2:
        raise ValueError("n must be >= 2")
    if n <= 10_000:
        h = sum(1.0 / k for k in range(1, n + 1))
    else:
        h = math.log(n) + EULER_GAMMA + 1.0 / (2.0 * n)
    return (h + math.exp(h) * math.log(h)) / n


def bio_lagarias_bound(
    stress_tier_n: int,
    emp_fdr: float,
    target_fdr: float,
    batch_leak: float,
    c2s_euler_discrepancy: float,
    gguf_kl_div: float,
    slack_scale: float = 0.35,
) -> Dict[str, float]:
    """Normalised compound error sigma_bio(n)/n vs the ceiling alpha_bio(n)/n, and their relative gap.

    sigma_bio/n multiplies the small-factor distortions: FDR calibration (only an
    over-run counts), batch leakage, and C2S disagreement; KL is report-only.
    alpha_bio/n = 1 + slack * (alpha(n)/n) / (alpha(12)/12): strict for small designs,
    slowly more tolerant (log log n) for large ones.
    """
    if isinstance(stress_tier_n, bool) or not isinstance(stress_tier_n, int) or stress_tier_n < 2:
        raise ValueError("stress_tier_n must be an integer >= 2")
    if not (0 <= emp_fdr <= 1 and 0 < target_fdr <= 1 and 0 <= c2s_euler_discrepancy <= 1):
        raise ValueError("invalid FDR, target FDR or C2S discrepancy")
    if not all(math.isfinite(v) and v >= 0 for v in (batch_leak, gguf_kl_div, slack_scale)):
        raise ValueError("leak, KL and slack must be finite and non-negative")
    sigma_norm = max(1.0, emp_fdr / target_fdr) * (1 + batch_leak) * (1 + c2s_euler_discrepancy)
    ref_ceil = lagarias_normalized_ceiling(12)
    cur_ceil = lagarias_normalized_ceiling(stress_tier_n)
    alpha_norm = 1.0 + slack_scale * (cur_ceil / ref_ceil)
    relative_gap = (alpha_norm - sigma_norm) / alpha_norm
    return {
        "stress_tier_n": stress_tier_n,
        "sigma_bio_norm": round(sigma_norm, 6),
        "alpha_bio_norm": round(alpha_norm, 6),
        "relative_gap": relative_gap,
        "lagarias_holds": sigma_norm < alpha_norm,
    }


def criterion_margin(observed: float, bound: float, upper: bool) -> float:
    """Relative gap of ONE acceptance criterion: (bound - observed)/bound for a ceiling,
    (observed - bound)/bound for a floor. Negative = failed; 0..0.05 = near miss.

    The compound bound above has 35% slack at n = 12, so on its own it would not see an
    FDR of 0.101 against a 0.10 brief (the goal-engineering R002 case). This per-criterion
    margin does: it is -0.01.
    """
    if not all(math.isfinite(v) for v in (observed, bound)):
        raise ValueError("criterion and bound must be finite")
    if bound == 0:
        ok = observed <= 0 if upper else observed >= 0
        return 1.0 if ok else -1.0
    return (bound - observed) / abs(bound) if upper else (observed - bound) / abs(bound)


def estimate_off_line_exponent(cohort_sizes: List[int], abs_residuals: List[float]) -> float:
    """Fit |error(N)| ~ C * N^(a - 1) on a log-log scale and return the unbounded fitted exponent.

    a = 0.5: error shrinks like 1/sqrt(N) (the "critical line", pure sampling noise).
    a -> 1:  error does not shrink with N: a systematic bias (an "off-line zero").
    """
    n, r = np.asarray(cohort_sizes, dtype=float), np.asarray(abs_residuals, dtype=float)
    if (n.ndim != 1 or r.shape != n.shape or n.size < 4 or not np.isfinite(n).all()
            or not np.isfinite(r).all() or (n < 2).any() or (n != np.floor(n)).any()
            or len(set(n)) != len(n) or (r <= 0).any()):
        raise ValueError("scaling needs at least four distinct cohort sizes and matching finite, positive RMS errors")
    slope, _ = np.polyfit(np.log(n), np.log(r), 1)
    return float(slope + 1.0)


def evaluate_suite(
    stress_cases: List[Dict],
    scaling_trace: Tuple[List[int], List[float]],
    min_relative_gap: float = MIN_RELATIVE_GAP,
    max_off_line_a: float = MAX_OFF_LINE_A,
    max_gguf_kl: float = MAX_GGUF_KL,
    max_c2s_euler: float = MAX_C2S_EULER,
    min_recall: float = 0.90,
) -> Dict:
    """Rank stress cases by smallest relative gap and return a verdict plus Observer signals."""
    if not isinstance(stress_cases, list) or not all(isinstance(c, dict) for c in stress_cases):
        raise ValueError("stress_cases must be a list of case objects")
    if not stress_cases:
        raise ValueError("no stress cases")
    ids = [case["case_id"] for case in stress_cases]
    if not all(isinstance(cid, str) and cid for cid in ids) or len(ids) != len(set(ids)):
        raise ValueError("case IDs must be nonempty, unique strings")
    evaluated, signals, margins = [], [], {}
    for case in stress_cases:
        res = bio_lagarias_bound(
            stress_tier_n=case["stress_tier_n"],
            emp_fdr=case["emp_fdr"],
            target_fdr=case["target_fdr"],
            batch_leak=case["batch_leak"] if "c2s_euler_discrepancy" not in case else case.get("batch_leak", 0.0),
            c2s_euler_discrepancy=case.get("c2s_euler_discrepancy", 0.0),
            gguf_kl_div=case.get("gguf_kl_div", 0.0),
        )
        res["case_id"] = case["case_id"]
        for k in ("recall", "emp_fdr", "batch_leak", "c2s_euler_discrepancy", "gguf_kl_div", "note"):
            if k in case:
                res[k] = case[k]
        if "batch_leak" in case:
            if "recall" not in case or not 0 <= case["recall"] <= 1:
                raise ValueError(f"{case['case_id']}: bulk stress case requires finite recall in [0,1]")
            margins[f"recall@{case['case_id']}"] = criterion_margin(case["recall"], min_recall, upper=False)
            margins[f"fdr@{case['case_id']}"] = criterion_margin(case["emp_fdr"], case["target_fdr"], upper=True)
        evaluated.append(res)
        if case.get("gguf_kl_div", 0.0) > max_gguf_kl:
            signals.append({"type": "c2s_gguf_quant_drift", "severity": "medium", "case_id": case["case_id"],
                            "gguf_kl_div": case["gguf_kl_div"], "action": "check anchor comparability and decoding before changing quantisation"})
        if case.get("c2s_euler_discrepancy", 0.0) > max_c2s_euler:
            signals.append({"type": "c2s_euler_discrepancy", "severity": "high", "case_id": case["case_id"],
                            "c2s_euler_discrepancy": case["c2s_euler_discrepancy"]})

    evaluated.sort(key=lambda r: r["relative_gap"])
    worst = evaluated[0]

    a_hat = estimate_off_line_exponent(scaling_trace[0], scaling_trace[1])
    if a_hat > max_off_line_a:
        signals.append({"type": "off_line_zero_detected", "severity": "critical",
                        "estimated_a": round(a_hat, 4), "threshold": max_off_line_a})
    if worst["relative_gap"] <= 0.0:
        signals.append({"type": "lagarias_counterexample", "severity": "critical",
                        "worst_case_id": worst["case_id"], "relative_gap": worst["relative_gap"]})
    elif worst["relative_gap"] < min_relative_gap:
        signals.append({"type": "lagarias_gap_erosion", "severity": "high",
                        "worst_case_id": worst["case_id"], "relative_gap": worst["relative_gap"]})

    passed = (
        all(r["lagarias_holds"] for r in evaluated)
        and all(gap > 0 for gap in margins.values())
        and a_hat <= max_off_line_a
        and all(c.get("c2s_euler_discrepancy", 0.0) <= max_c2s_euler for c in stress_cases)
    )
    return {
        "passed": passed,
        "needs_human": passed and min([worst["relative_gap"], *margins.values()]) < min_relative_gap,
        "criterion_margins": margins,
        "worst_stress_case": worst,
        "estimated_critical_exponent_a": a_hat,
        "scaling_trace": {"sizes": list(scaling_trace[0]), "residuals": list(scaling_trace[1])},
        "ranked_stress_cases": evaluated,
        "observer_signals": signals,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="RH/Lagarias-inspired stress gate (standalone)")
    parser.add_argument("--metrics-json", required=True,
                        help='JSON with "stress_cases" and "scaling_trace": {"sizes": [...], "residuals": [...]}')
    args = parser.parse_args(argv)
    try:
        with open(args.metrics_json, "r", encoding="utf-8") as f:
            payload = json.load(f)
        report = evaluate_suite(
            stress_cases=payload["stress_cases"],
            scaling_trace=(payload["scaling_trace"]["sizes"], payload["scaling_trace"]["residuals"]),
        )
    except (OSError, KeyError, ValueError, TypeError, OverflowError) as e:
        print(json.dumps({"error": f"unreadable metrics: {e}"}))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""Grader-side stress ladder for the RH/Lagarias stress gate (see checks/lagarias_stress_gate.py).

The shipped 12-sample case is one design. A DE pipeline can pass it and still be wrong
on designs where small confounds stack up, much as a bound can hold for small n and fail
at a "highly composite" one. This module generates extra SYNTHETIC designs with
make_case.generate, runs the candidate CLI on each in a scratch directory (never inside
data/), and turns the results into the stress cases and scaling trace the gate expects.

Ladder (stress_tier_n = number of samples):
  12    low replicates (3 per condition x batch) plus one degraded (RIN 4.1) library
  60    partial batch imbalance: control B1:B2 = 20:10, treated 10:20
  120   borderline RIN 6.0-6.5 on a third of libraries, strandedness mixed WITHIN batches,
        mild imbalance (35:25 / 25:35)
  2520  high dropout: library size x 0.08, balanced

Scaling trace: the 2:1 / 1:2 imbalanced design at N = 24, 48, 96, 192 with one fixed
seed. The error is the RMS of (estimated - true) log2FC over well-expressed null genes,
after removing the median (a global normalisation offset is not a batch problem). Under this generator, sampling error typically falls like N^-1/2 (a = 0.5); batch leakage gives a floor (a -> 1).

batch_leak is the absolute least-squares slope (with intercept) of that residual on the planted batch effect:
0 when batch is modelled, about 1/3 for a batch-blind test on the 2:1 design.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

import make_case

TARGET_FDR = make_case.THRESHOLDS["fdr"]
MIN_LFC = make_case.THRESHOLDS["min_abs_log2fc"]
LADDER_SEED = 1009
SCALING_SEED = 2027
SCALING_SIZES = (24, 48, 96, 192)
NULL_MIN_MU = 100.0


def _design(n_ctrl_b1: int, n_ctrl_b2: int, n_trt_b1: int, n_trt_b2: int):
    out, k = [], 0
    for cond, batch, n in (("control", "B1", n_ctrl_b1), ("control", "B2", n_ctrl_b2),
                           ("treated", "B1", n_trt_b1), ("treated", "B2", n_trt_b2)):
        for _ in range(n):
            k += 1
            out.append((f"X{k:04d}", cond, batch))
    return out


def tiers():
    """(case_id, stress_tier_n, generate() kwargs, note)."""
    t12 = _design(3, 3, 3, 3)
    t60 = _design(20, 10, 10, 20)
    t120 = _design(35, 25, 25, 35)
    rng = np.random.default_rng(LADDER_SEED)
    border = {sid: round(float(rng.uniform(6.0, 6.5)), 1) for sid, _, _ in t120[::3]}
    mixed = {sid for i, (sid, _, _) in enumerate(t120) if i % 2 == 0}
    t2520 = _design(630, 630, 630, 630)
    return [
        ("n12_low_replicate", 12, dict(samples=t12, low_rin=(t12[4][0],)), "3 per cell, one RIN 4.1 library"),
        ("n60_batch_imbalance", 60, dict(samples=t60, low_rin=()), "control B1:B2 20:10, treated 10:20"),
        ("n120_borderline_rin_mixed_strand", 120,
         dict(samples=t120, low_rin=(), rin_override=border, reversed_ids=mixed),
         "RIN 6.0-6.5 on a third of libraries, strandedness mixed within batches, 35:25 imbalance"),
        ("n2520_high_dropout", 2520, dict(samples=t2520, low_rin=(), lib_scale=0.08), "library size x0.08"),
    ]


def _write_case(d: Path, g: dict, samples) -> tuple[str, str, str]:
    d.mkdir(parents=True, exist_ok=True)
    ids = [s for s, _, _ in samples]
    make_case._write(d / "counts.tsv", make_case._matrix_tsv(g["genes"], ids, g["counts"]))
    make_case._write(d / "counts_opposite.tsv", make_case._matrix_tsv(g["genes"], ids, g["opposite"]))
    lines = ["sample_id\tcondition\tbatch\trin\tstrandedness_declared\tsubject_ref"]
    for j, (sid, cond, batch) in enumerate(samples):
        lines.append(f"{sid}\t{cond}\t{batch}\t{g['rins'][j]:.1f}\tforward\tSUBJ-{j + 1:04d}")
    make_case._write(d / "samples.tsv", "\n".join(lines) + "\n")
    return str(d / "counts.tsv"), str(d / "counts_opposite.tsv"), str(d / "samples.tsv")


def _residual(res: pd.DataFrame, g: dict) -> tuple[np.ndarray, np.ndarray]:
    """Median-centred log2FC error and planted batch effect over well-expressed null genes."""
    idx = {gene: i for i, gene in enumerate(g["genes"])}
    est = res.set_index("gene")["log2fc"].astype(float)
    nulls = [gene for gene in idx if g["lfc"][idx[gene]] == 0 and g["mu"][idx[gene]] >= NULL_MIN_MU]
    if not set(nulls) <= set(est.index):
        raise ValueError("missing pre-specified, well-expressed null genes in de_results.tsv")
    r = est.loc[nulls].to_numpy() - np.array([g["lfc"][idx[x]] for x in nulls])
    b = np.array([g["batch_eff"][idx[x]] for x in nulls])
    return r - np.median(r), b


def _run(run_cli: Callable, scratch: Path, name: str, g: dict, samples):
    counts, opposite, sheet = _write_case(scratch / name / "in", g, samples)
    out = scratch / name / "out"
    rc, log = run_cli(out, sheet, counts, opposite)
    p = out / "de_results.tsv"
    if rc != 0 or not p.is_file():
        raise RuntimeError(f"pipeline failed on stress case {name} (exit {rc}): {log.strip()[-300:]}")
    res = pd.read_csv(p, sep="\t")
    if {"gene", "log2fc", "padj"} - set(res.columns) or res["gene"].duplicated().any():
        raise RuntimeError(f"stress case {name}: de_results.tsv malformed")
    if not set(res["gene"]) <= set(g["genes"]) or not np.isfinite(res[["log2fc", "padj"]].to_numpy(dtype=float)).all() or not res["padj"].between(0, 1).all():
        raise ValueError(f"stress case {name}: unknown gene, non-finite effect, or invalid adjusted p-value")
    return res


def run_ladder(run_cli: Callable, scratch: Path) -> dict:
    """run_cli(out_dir, samples, counts, opposite) -> (rc, log). Returns gate inputs plus diagnostics."""
    cases, problems = [], []
    for i, (cid, n, kw, note) in enumerate(tiers()):
        g = make_case.generate(LADDER_SEED + i, **kw)
        try:
            res = _run(run_cli, scratch, cid, g, kw["samples"])
            calls = res[(res["padj"] < TARGET_FDR) & (res["log2fc"].abs() >= MIN_LFC)]
            truth = g["de_genes"]
            tp = sum(1 for gene, l in zip(calls["gene"], calls["log2fc"]) if gene in truth and np.sign(l) == np.sign(truth[gene]))
            fdr = (len(calls) - tp) / len(calls) if len(calls) else 0.0
            recall = tp / len(truth)
            r, b = _residual(res, g)
            b = b - b.mean()
            leak = abs(float(np.dot(r, b) / np.dot(b, b)))
            cases.append({"case_id": cid, "stress_tier_n": n, "emp_fdr": fdr, "target_fdr": TARGET_FDR,
                          "batch_leak": leak, "recall": recall, "note": note})
        except Exception as e:  # noqa: BLE001 -- any candidate failure on a tier fails closed
            problems.append(f"{cid}: {e}")
            cases.append({"case_id": cid, "stress_tier_n": n, "emp_fdr": 1.0, "target_fdr": TARGET_FDR,
                          "batch_leak": 1.0, "recall": 0.0, "note": f"{note}; FAILED: {str(e)[:160]}"})

    sizes, rms = [], []
    for n in SCALING_SIZES:
        q = n // 6  # 2:1 / 1:2 imbalance
        design = _design(2 * q, q, q, 2 * q)
        g = make_case.generate(SCALING_SEED, samples=design, low_rin=())
        try:
            r, _ = _residual(_run(run_cli, scratch, f"scale_{n}", g, design), g)
            sizes.append(len(design))
            rms.append(float(np.sqrt(np.mean(r ** 2))))
        except Exception as e:  # noqa: BLE001 -- any candidate failure on a tier fails closed
            problems.append(f"scale_{n}: {e}")
    return {"stress_cases": cases, "scaling_trace": (sizes, rms), "problems": problems}

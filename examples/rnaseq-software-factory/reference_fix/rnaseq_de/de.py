"""Differential expression: batch-adjusted linear model on log2(CPM+1) with FDR control."""
import numpy as np
import pandas as pd
from scipy import stats


def bh_fdr(pvalues):
    """Benjamini-Hochberg adjusted p-values (monotone, capped at 1)."""
    p = np.asarray(pvalues, dtype=float)
    n = p.size
    if n == 0:
        return p
    order = np.argsort(p, kind="mergesort")
    ranked = p[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(ranked, 1.0)
    return out


def batch_adjusted_de(log_expr, samples, condition="condition", case="treated", control="control", batch="batch"):
    """Per-gene OLS of expression ~ condition + batch; Student t on the condition coefficient.

    A batch effect can bias a test that ignores batch when the condition mix differs across batches.
    With opposite 2:1 batch imbalances, part of the planted batch effect leaks into
    a batch-blind log2FC. A single-batch design drops the batch term.
    """
    if set(samples[condition]) != {case, control} or batch not in samples or samples[batch].isna().any():
        raise ValueError("expected both contrast conditions and a batch for every sample")
    y = log_expr.loc[:, samples.index].to_numpy(dtype=float)
    if not np.isfinite(y).all():
        raise ValueError("non-finite log expression: check for empty count libraries")
    cols = [np.ones(len(samples)), (samples[condition] == case).to_numpy(dtype=float)]
    for lv in sorted(samples[batch].unique())[1:]:
        cols.append((samples[batch] == lv).to_numpy(dtype=float))
    x = np.column_stack(cols)
    df = len(samples) - x.shape[1]
    if df < 1 or np.linalg.matrix_rank(x) < x.shape[1]:
        raise ValueError("design has no residual degrees of freedom or is rank deficient")
    pinv = np.linalg.pinv(x)
    beta = y @ pinv.T
    resid = y - beta @ x.T
    se = np.sqrt((resid ** 2).sum(axis=1) / df * np.dot(pinv[1], pinv[1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        p = 2.0 * stats.t.sf(np.abs(beta[:, 1] / se), df)
    constant = np.ptp(y, axis=1) == 0
    beta[constant, 1] = 0
    p[constant] = 1
    res = pd.DataFrame({"gene": log_expr.index, "log2fc": beta[:, 1], "pvalue": p})
    res["padj"] = bh_fdr(res["pvalue"].to_numpy())
    return res.sort_values("pvalue", kind="mergesort").reset_index(drop=True)


def call_de(res, fdr=0.05, min_abs_log2fc=1.0):
    return res[(res["padj"] < fdr) & (res["log2fc"].abs() >= min_abs_log2fc)]

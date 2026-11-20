"""Differential expression: Welch t-test on log2(CPM+1) with FDR control."""
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


def welch_de(log_expr, samples, condition="condition", case="treated", control="control"):
    """Per-gene Welch t-test of case vs control on log-scale expression."""
    cases = samples.index[samples[condition] == case]
    ctrls = samples.index[samples[condition] == control]
    a = log_expr[cases].to_numpy()
    b = log_expr[ctrls].to_numpy()
    _, p = stats.ttest_ind(a, b, axis=1, equal_var=False)
    p = np.nan_to_num(p, nan=1.0)
    res = pd.DataFrame({
        "gene": log_expr.index,
        "log2fc": a.mean(axis=1) - b.mean(axis=1),
        "pvalue": p,
    })
    res["padj"] = bh_fdr(res["pvalue"].to_numpy())
    return res.sort_values("pvalue", kind="mergesort").reset_index(drop=True)


def call_de(res, fdr=0.05, min_abs_log2fc=1.0):
    return res[(res["padj"] < fdr) & (res["log2fc"].abs() >= min_abs_log2fc)]

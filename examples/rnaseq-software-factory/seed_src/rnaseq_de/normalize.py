"""Library-size normalization: CPM, log-CPM and a simple TMM-style factor."""
import numpy as np
import pandas as pd


def library_sizes(counts):
    return counts.sum(axis=0)


def cpm(counts, norm_factors=None):
    lib = library_sizes(counts).astype(float)
    if norm_factors is not None:
        lib = lib * pd.Series(norm_factors, index=counts.columns)
    return counts.div(lib, axis=1) * 1e6


def log_cpm(counts, prior=1.0, norm_factors=None):
    return np.log2(cpm(counts, norm_factors) + prior)


def tmm_factors(counts, trim_m=0.3, trim_a=0.05):
    """TMM-style factors (unweighted trimmed mean of M), scaled to geometric mean 1."""
    props = counts.div(counts.sum(axis=0), axis=1)
    uq = props.quantile(0.75)
    ref = (uq - uq.mean()).abs().idxmin()
    out = {}
    for s in counts.columns:
        ok = (counts[s] > 0) & (counts[ref] > 0)
        m = np.log2(props.loc[ok, s] / props.loc[ok, ref])
        a = 0.5 * np.log2(props.loc[ok, s] * props.loc[ok, ref])
        keep = (m > m.quantile(trim_m)) & (m < m.quantile(1 - trim_m)) & \
               (a > a.quantile(trim_a)) & (a < a.quantile(1 - trim_a))
        out[s] = float(2 ** m[keep].mean()) if keep.any() else 1.0
    f = pd.Series(out)
    return f / np.exp(np.log(f).mean())

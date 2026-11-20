"""Count loading. Counts are a genes x samples matrix (TSV, first column = gene)."""
import numpy as np
import pandas as pd


def load_counts(src):
    """Load a counts matrix; reject anything that is not non-negative integers."""
    df = pd.read_csv(src, sep="\t", index_col=0)
    vals = df.to_numpy(dtype=float)
    if not np.isfinite(vals).all():
        raise ValueError("counts must be finite non-negative integers (found NaN/inf)")
    if (vals < 0).any():
        raise ValueError("counts must be non-negative integers (found negative values)")
    if not np.equal(np.floor(vals), vals).all():
        raise ValueError("counts must be integer read counts (found non-integer values; TPM/NumReads are not counts)")
    return df.astype(np.int64)


def load_samples(src):
    """Load the sample sheet, indexed by sample_id (the column is kept)."""
    df = pd.read_csv(src, sep="\t", dtype={"sample_id": str})
    return df.set_index("sample_id", drop=False)

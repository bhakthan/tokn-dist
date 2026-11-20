"""Count loading. Counts are a genes x samples matrix (TSV, first column = gene)."""
import pandas as pd


def load_counts(src):
    """Load a counts matrix.

    TODO(invariant): counts must be non-negative integers. This loader casts to
    float and accepts anything, so a NumReads/TPM matrix slips through.
    """
    df = pd.read_csv(src, sep="\t", index_col=0)
    return df.astype(float)


def load_samples(src):
    """Load the sample sheet, indexed by sample_id (the column is kept)."""
    df = pd.read_csv(src, sep="\t", dtype={"sample_id": str})
    return df.set_index("sample_id", drop=False)

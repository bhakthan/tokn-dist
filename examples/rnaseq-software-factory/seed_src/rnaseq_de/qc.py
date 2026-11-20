"""Sample-level quality control and design checks."""

MIN_RIN = 6.0


class ConfoundedDesignError(ValueError):
    """The condition of interest cannot be separated from batch."""


def filter_low_rin(samples, min_rin=MIN_RIN):
    """Return (kept_samples, excluded_sample_ids).

    TODO(invariant): samples with RIN < min_rin must be excluded before DE.
    Currently every sample is kept.
    """
    return samples, []


def infer_strandedness(counts, opposite):
    """Return {sample_id: "forward" | "reverse"}.

    TODO(invariant): infer strandedness from the data (sense vs. opposite-strand
    counts) instead of trusting strandedness_declared. Currently assumes forward.
    """
    return {s: "forward" for s in counts.columns}


def apply_strandedness(counts, opposite, calls):
    """Return the sense-strand counts given the per-sample calls.

    TODO: reverse-stranded samples should take their counts from `opposite`.
    """
    return counts


def check_confounding(samples, condition="condition", batch="batch"):
    """Raise ConfoundedDesignError when condition is confounded with batch.

    TODO(invariant): not implemented; confounded designs run silently.
    """
    return None

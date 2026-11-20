"""Sample-level quality control and design checks."""

MIN_RIN = 6.0
REVERSE_BELOW = 0.25  # sense fraction below this => library was counted on the wrong strand
FORWARD_ABOVE = 0.75


class ConfoundedDesignError(ValueError):
    """The condition of interest cannot be separated from batch."""


def filter_low_rin(samples, min_rin=MIN_RIN):
    """Return (kept_samples, excluded_sample_ids): RIN < min_rin is excluded."""
    low = samples["rin"] < min_rin
    return samples[~low], sorted(samples.index[low])


def infer_strandedness(counts, opposite):
    """Return {sample_id: "forward" | "reverse"} from the sense/opposite ratio."""
    if opposite is None:
        raise ValueError("strandedness inference needs the opposite-strand counts (--counts-opposite)")
    calls = {}
    for s in counts.columns:
        sense, other = float(counts[s].sum()), float(opposite[s].sum())
        frac = sense / (sense + other) if sense + other > 0 else 0.5
        if frac < REVERSE_BELOW:
            calls[s] = "reverse"
        elif frac > FORWARD_ABOVE:
            calls[s] = "forward"
        else:
            raise ValueError(f"sample {s}: sense fraction {frac:.2f} looks unstranded; refusing to guess")
    return calls


def apply_strandedness(counts, opposite, calls):
    """Return the sense-strand counts: reverse samples take their counts from `opposite`."""
    fixed = counts.copy()
    for s, c in calls.items():
        if c == "reverse":
            fixed[s] = opposite[s]
    return fixed


def check_confounding(samples, condition="condition", batch="batch"):
    """Raise ConfoundedDesignError unless some batch holds more than one condition."""
    per_batch = samples.groupby(batch)[condition].nunique()
    if samples[condition].nunique() > 1 and samples[batch].nunique() > 1 and (per_batch < 2).all():
        raise ConfoundedDesignError(
            f"confounded design: {condition} is fully confounded with {batch} "
            f"({dict(samples.groupby(batch)[condition].first())}); the effect is not identifiable")

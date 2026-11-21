"""Command line: python -m rnaseq_de.cli --counts ... --counts-opposite ... --samples ... --out DIR

Outputs in DIR: de_results.tsv (gene, log2fc, pvalue, padj), qc.json, report.md.
Exit codes: 0 ok, 2 invalid input, 3 refused (confounded design).
"""
import argparse
import sys

from . import counts_io, de, normalize, qc, report


def run(counts_path, opposite_path, samples_path, out_dir, min_rin=qc.MIN_RIN):
    counts = counts_io.load_counts(counts_path)
    opposite = counts_io.load_counts(opposite_path) if opposite_path else None
    samples = counts_io.load_samples(samples_path).loc[list(counts.columns)]

    calls = qc.infer_strandedness(counts, opposite)
    counts = qc.apply_strandedness(counts, opposite, calls)
    kept, excluded = qc.filter_low_rin(samples, min_rin)
    qc.check_confounding(kept)

    counts = counts[list(kept.index)]
    results = de.batch_adjusted_de(normalize.log_cpm(counts), kept)
    summary = {
        "excluded_samples": sorted(excluded),
        "strandedness": dict(sorted(calls.items())),
        "swapped_samples": sorted(s for s, c in calls.items() if c == "reverse"),
        "samples_used": sorted(kept.index),
    }
    report.write_report(out_dir, results, summary, kept)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="rnaseq_de")
    ap.add_argument("--counts", required=True)
    ap.add_argument("--counts-opposite", default=None, help="opposite-strand counts (same shape)")
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--min-rin", type=float, default=qc.MIN_RIN)
    a = ap.parse_args(argv)
    try:
        return run(a.counts, a.counts_opposite, a.samples, a.out, a.min_rin)
    except qc.ConfoundedDesignError as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 3
    except ValueError as e:
        print(f"ERROR: invalid input: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())

"""Offline FSC 0.143 crossing check for the structural biology example.

Reads a CSV with columns resolution_A,fsc (synthetic data). Standard library only.
No network access.
"""
import argparse
import csv
import sys

THRESHOLD = 0.143


def load_curve(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [(float(r["resolution_A"]), float(r["fsc"])) for r in csv.DictReader(fh)]
    if not rows:
        raise ValueError("no rows in FSC curve")
    return sorted(rows, key=lambda p: p[0], reverse=True)  # coarse to fine


def crossing(curve, threshold=THRESHOLD):
    """First resolution (Å) where the FSC falls to the threshold, interpolated linearly."""
    for (r0, f0), (r1, f1) in zip(curve, curve[1:]):
        if f0 >= threshold > f1:
            t = (f0 - threshold) / (f0 - f1)
            return r0 + t * (r1 - r0)
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("curve", help="FSC CSV with resolution_A,fsc columns")
    ap.add_argument("--claimed", type=float, required=True, help="claimed resolution in Å")
    args = ap.parse_args(argv)

    curve = load_curve(args.curve)
    cross = crossing(curve)
    if cross is None:
        print("FSC never falls to 0.143 in this range: cannot support any resolution claim")
        return 1

    print(f"FSC 0.143 crossing: {cross:.2f} Å (linear interpolation)")
    print(f"Claimed resolution: {args.claimed:.2f} Å")
    if args.claimed < cross:
        print("Verdict: BLOCKED (claim is finer than the 0.143 crossing)")
        return 1
    print("Verdict: OK (claim is no finer than the 0.143 crossing)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

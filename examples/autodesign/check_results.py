"""Read-only summary of an autodesign run in this folder.

Stdlib only. Reads .nospace/autodesign/results.json and the newest
run-*/pareto-frontier.json. It makes no network calls and writes nothing.
It prints what tokn recorded; it does not re-score anything.
"""

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
AUTODESIGN_DIR = os.path.join(ROOT, ".nospace", "autodesign")
RESULTS = os.path.join(AUTODESIGN_DIR, "results.json")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main():
    if not os.path.exists(RESULTS):
        print(f"No results yet: {RESULTS} not found. Run the experiment first.")
        return 1

    results = load(RESULTS)
    experiments = results.get("experiments", [])
    print(f"Experiments recorded: {results.get('total_experiments', len(experiments))}")
    print()
    print(f"{'id':<6} {'status':<11} {'score':>7}  decision")
    counts = {}
    for exp in experiments:
        status = exp.get("status", "?")
        counts[status] = counts.get(status, 0) + 1
        score = exp.get("score", 0)
        print(f"{str(exp.get('id', '?')):<6} {status:<11} {score:>7}  {exp.get('decision', '')}")
    print()
    print("Status counts: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    runs = sorted(glob.glob(os.path.join(AUTODESIGN_DIR, "run-*")))
    if not runs:
        return 0
    frontier_path = os.path.join(runs[-1], "pareto-frontier.json")
    if os.path.exists(frontier_path):
        frontier = load(frontier_path)
        print()
        print(f"Frontier log from {os.path.basename(runs[-1])} (as written by tokn):")
        for entry in frontier.get("entries", []):
            print(
                f"  iter {entry.get('iteration')}: score={entry.get('score')} "
                f"decision={entry.get('decision')} best_so_far={entry.get('best_so_far')}"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

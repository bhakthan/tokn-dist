"""Independent held-out cross-check for the Graph of Loops example (standard library only).

Recomputes the primary (training) MSE and the held-out MSE directly from the local
CSV and model.json files, then compares that independent result with the verdict
recorded in graph-record.json, the output of `tokn loopgraph run --json`.

The check is decisive on one rule: a graph may only report an accepted win when the
held-out computation also passes. Exit 0 means the record agrees with the independent
computation; exit 1 means it does not; exit 2 means an input is missing or unreadable.
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from oracle import evaluate  # noqa: E402

PRIMARY_MAX_MSE = 0.05
HELDOUT_MAX_MSE = 0.10


def find_key(obj, wanted):
    """Yield every value stored under `wanted` anywhere in a nested JSON structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == wanted:
                yield v
            yield from find_key(v, wanted)
    elif isinstance(obj, list):
        for item in obj:
            yield from find_key(item, wanted)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    record_path = argv[0] if argv else os.path.join(HERE, "graph-record.json")
    model = os.path.join(HERE, "model.json")
    train = os.path.join(HERE, "data", "train.csv")
    heldout = os.path.join(HERE, "custodian", "heldout.csv")

    try:
        with open(record_path, encoding="utf-8-sig") as fh:
            text = fh.read()
        # Skip any banner text before the JSON object (e.g. a license notice).
        record = json.loads(text[text.index("{"):])
        train_mse, degree, _ = evaluate(train, train, model)
        held_mse, _, _ = evaluate(train, heldout, model)
    except (OSError, ValueError, KeyError) as exc:
        print(f"crosscheck: cannot read inputs: {exc}", file=sys.stderr)
        return 2

    primary_pass = train_mse <= PRIMARY_MAX_MSE
    heldout_pass = held_mse <= HELDOUT_MAX_MSE
    accepted = bool(record.get("accepted", False))
    grounded = bool(record.get("grounded", False))

    print(f"model degree           : {degree}")
    print(f"primary  train MSE     : {train_mse:.6f}  (gate <= {PRIMARY_MAX_MSE})  -> {'PASS' if primary_pass else 'FAIL'}")
    print(f"held-out MSE           : {held_mse:.6f}  (gate <= {HELDOUT_MAX_MSE})  -> {'PASS' if heldout_pass else 'FAIL'}")
    print(f"graph accepted         : {accepted}")
    print(f"graph grounded         : {grounded}")
    print(f"graph stop_reason      : {record.get('stop_reason', '<missing>')}")

    anchors = [a for a in find_key(record, "anchor_verdicts") if isinstance(a, list)]
    for verdicts in anchors:
        for v in verdicts:
            print(f"anchor {v.get('anchor_id', '?'):<18}: agrees={v.get('agrees')}")

    if accepted and not heldout_pass:
        print("RESULT: MISMATCH - the graph accepted a win that the held-out check refutes.")
        return 1
    if accepted and heldout_pass:
        print("RESULT: CONSISTENT - accepted win, and the held-out check passes too.")
        return 0
    if not primary_pass or not heldout_pass:
        print("RESULT: CONSISTENT - no win was accepted, and the held-out check did not confirm one.")
        return 0
    print("RESULT: CONSISTENT - no win was accepted; the fit passes both gates, so the graph was conservative.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

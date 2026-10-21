"""Read-only checker for the clintrial example.

Two modes, both read local files only and make no network calls:

  python check_inputs.py inputs/            # validate the synthetic inputs
  python check_inputs.py result.json        # look for validation hooks in a saved run

A saved run is written with `--output-format json`. That gives one object
(status, result, exit_code, steps, usage, errors); hook evidence is usually
free text inside `result`. A mention is not a pass: read the sentence around it.
"""

import json
import os
import sys

HOOKS = [
    "phi_before_model",
    "phi_input_screen",
    "estimand_completeness",
    "positivity_before_emulate",
    "validation_before_emit",
    "human_in_loop_before_emit",
    "no_silent_artifact",
    "calibrated_language",
    "decision_support_disclaimer",
]

SPEC_FIELDS = ["population", "intervention", "comparator", "outcome", "time_zero", "summary_measure"]
RECORD_FIELDS = ["id", "age", "frailty", "treat", "time_months", "event"]


def check_inputs(folder):
    ok = True
    with open(os.path.join(folder, "target-trial-spec.json"), encoding="utf-8") as fh:
        spec = json.load(fh)
    with open(os.path.join(folder, "synthetic-cohort.json"), encoding="utf-8") as fh:
        cohort = json.load(fh)

    missing = [f for f in SPEC_FIELDS if not spec.get("estimand", {}).get(f)]
    print("estimand fields:", "complete" if not missing else f"MISSING {missing}")
    ok &= not missing
    print("spec marked synthetic:", spec.get("synthetic") is True)
    print("cohort marked synthetic:", cohort.get("synthetic") is True)
    ok &= spec.get("synthetic") is True and cohort.get("synthetic") is True

    patients = cohort.get("patients", [])
    bad = [p.get("id", "?") for p in patients if any(f not in p for f in RECORD_FIELDS)]
    arms = {p.get("treat") for p in patients}
    print(f"records: {len(patients)}, arms present: {sorted(arms)}")
    print("records with missing fields:", bad or "none")
    ok &= not bad and arms == {0, 1}
    return ok


def scan_run(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "status" in data:
        print(f"run status: {data.get('status')}  exit_code: {data.get('exit_code')}")
    text = json.dumps(data, ensure_ascii=False)
    print(f"{'hook':<30} mentions")
    for hook in HOOKS:
        print(f"{hook:<30} {text.count(hook)}")
    print("\nA hook that is never mentioned was not reached in this run. Read the sentences that do mention one.")
    return True


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    target = sys.argv[1]
    ok = check_inputs(target) if os.path.isdir(target) else scan_run(target)
    print("\nRESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""Turn the baseline and candidate eval logs from eval_live.py into a `tokn flywheel compare` run.

Usage:

    python compare_runs.py <eval-log-dir>

Reads <eval-log-dir>/baseline.json and candidate.json (written by eval_live.py when
TOKN_EXAMPLE_EVAL_LOG is set), writes <eval-log-dir>/runs.json, and runs
`tokn flywheel compare --runs runs.json --yes --json`. The arms are compute-matched: both use the
same per-attempt cap, model and tools.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from tokn_agent import require_tokn, tokn_binary

ATTEMPT_CAP = 60000


def load_arm(log_dir: Path, name: str) -> dict:
    path = log_dir / f"{name}.json"
    if not path.exists():
        raise SystemExit(f"missing {path}: run eval_live.py for both arms first (B4 in the README)")
    records = json.loads(path.read_text(encoding="utf-8"))
    return {
        "name": name,
        "attempt_cap": ATTEMPT_CAP,
        "model": os.environ.get("TOKN_EXAMPLE_MODEL", "claude-opus-5-5"),
        "cases": [{"case_id": r["case_id"], "attempts": [{"tokens": r["tokens"], "passed": r["passed"]}]}
                  for r in records],
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python compare_runs.py <eval-log-dir>")
    require_tokn()
    log_dir = Path(sys.argv[1]).resolve()
    runs = {"candidate": "candidate", "envelope_per_task": ATTEMPT_CAP,
            "arms": [load_arm(log_dir, "baseline"), load_arm(log_dir, "candidate")]}
    runs_path = log_dir / "runs.json"
    runs_path.write_text(json.dumps(runs, indent=2), encoding="utf-8")
    cmd = [tokn_binary(), "flywheel", "compare", "--runs", str(runs_path), "--yes", "--json", "--no-update-check"]
    p = subprocess.run(cmd, cwd=log_dir, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       check=False)
    print(p.stdout)
    if p.returncode:
        print(p.stderr, file=sys.stderr)
    sys.exit(p.returncode)


if __name__ == "__main__":
    main()

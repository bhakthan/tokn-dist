"""Write six seeded failing run logs so `tokn self-harness` has a pattern to mine.

Usage:

    python seed_failures.py <workspace>

Writes <workspace>/.nospace/runs/seed-01.jsonl ... seed-06.jsonl. Every log shows the same
failure: the agent declared success without re-running the tests after an edit.
"""

import json
import sys
from pathlib import Path

FAILURES = [
    "run_command failed: exit status 1 - go test still FAIL after edit; agent reported done without re-running verification",
    "run_command failed: exit status 1 - verification not re-run after edit; final answer claimed tests pass",
    "run_command failed: exit status 1 - go test FAIL left unverified; run finished claiming the fix works",
    "run_command failed: exit status 1 - agent declared completion while verification was still failing",
    "run_command failed: exit status 1 - tests failing after edit; completion claimed without verifying",
    "run_command failed: exit status 1 - final answer said done; go test FAIL was never re-checked",
]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python seed_failures.py <workspace>")
    runs = Path(sys.argv[1]).resolve() / ".nospace" / "runs"
    runs.mkdir(parents=True, exist_ok=True)
    for i, failure in enumerate(FAILURES, start=1):
        rows = [
            {"ts": "2026-11-18T10:00:00Z", "step": 0, "role": "user", "event": "start", "mode": "default",
             "content": "Fix the failing test"},
            {"ts": "2026-11-18T10:00:05Z", "step": 3, "role": "tool", "tool_name": "run_command", "mode": "default",
             "error": failure, "content": "--- FAIL: TestMean"},
        ]
        log = runs / f"seed-{i:02d}.jsonl"
        log.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    print(f"wrote {len(FAILURES)} seeded run logs to {runs}")


if __name__ == "__main__":
    main()

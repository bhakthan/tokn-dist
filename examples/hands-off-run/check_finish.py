"""Offline finish check for the hands-off-run example.

Reads local files only. Compares the workspace test file with the shipped copy,
and reads the JSON result written by `tokn agent-run --output-format json`.

Usage:
    python check_finish.py <workspace-folder> <run-result.json>
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHIPPED_TEST = os.path.join(HERE, "task", "tests", "test_expr.py")


def sha256(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    workspace, result_path = argv[1], argv[2]
    problems = []

    if not os.path.isfile(os.path.join(workspace, "expr.py")):
        problems.append("expr.py is missing from the workspace root")

    ws_test = os.path.join(workspace, "tests", "test_expr.py")
    if not os.path.isfile(ws_test):
        problems.append("tests/test_expr.py is missing from the workspace")
    elif sha256(ws_test) != sha256(SHIPPED_TEST):
        problems.append("tests/test_expr.py differs from the shipped acceptance test")

    try:
        with open(result_path, encoding="utf-8") as fh:
            result = json.load(fh)
    except (OSError, ValueError) as exc:
        problems.append(f"could not read run result: {exc}")
        result = {}

    if result and result.get("exit_code") != 0:
        problems.append(f"run exit_code is {result.get('exit_code')!r}, expected 0")

    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("PASS: expr.py present, acceptance test unchanged, run exited 0")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""check.py - read-only check that the reorder report lists the expected items.

Compares the item names in the first column of the markdown table(s) in the
report with the ones in expected-reorder.md. It only reads files and makes no
network calls.

Usage:
  python check.py [REPORT] [--expected EXPECTED]

REPORT defaults to workspace/reorder.md and EXPECTED defaults to
expected-reorder.md, both relative to this script.
Exit codes: 0 items match, 1 items differ, 2 a file is missing or unreadable.
"""
import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEPARATOR = re.compile(r"^:?-+:?$")


def item_names(path: Path) -> set:
    names = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            continue
        first = line.strip("|").split("|")[0].strip().strip("`")
        if not first or first.lower() == "item" or SEPARATOR.match(first):
            continue
        names.add(first)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check that reorder.md lists the expected items (read-only)."
    )
    parser.add_argument(
        "report",
        nargs="?",
        default=str(HERE / "workspace" / "reorder.md"),
        help="report to check (default: workspace/reorder.md)",
    )
    parser.add_argument(
        "--expected",
        default=str(HERE / "expected-reorder.md"),
        help="file with the expected table (default: expected-reorder.md)",
    )
    args = parser.parse_args()

    try:
        actual = item_names(Path(args.report))
        expected = item_names(Path(args.expected))
    except FileNotFoundError as err:
        print(f"[!] File not found: {err.filename}. Run run-local first.", file=sys.stderr)
        return 2
    except OSError as err:
        print(f"[!] Cannot read file: {err}", file=sys.stderr)
        return 2

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if not missing and not extra:
        print(f"PASS: {len(expected)} items match.")
        return 0
    if missing:
        print("Missing: " + ", ".join(missing))
    if extra:
        print("Unexpected: " + ", ".join(extra))
    print("FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

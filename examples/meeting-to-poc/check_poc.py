#!/usr/bin/env python3
"""Offline checker for a meeting-to-PoC run.

Reads local files only. It makes no network calls and writes nothing.
Checks the design plan headings and the Go scaffold layout.

Usage:
    python check_poc.py --plan design-plan.md --poc poc
"""
import argparse
import re
import sys
from pathlib import Path

REQUIRED_HEADINGS = ["Scope", "Approach", "Risks", "Open Questions"]
REQUIRED_POC_FILES = ["go.mod", "main.go", "README.md"]
MAX_GO_LINES = 200
PLAN_WORDS_MIN = 200
PLAN_WORDS_MAX = 400
HEADING = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
IMPORT_PATH = re.compile(r'"([^"]+)"')


def check_plan(plan: Path, problems: list[str], notes: list[str]) -> None:
    if not plan.is_file():
        problems.append(f"missing design plan: {plan}")
        return
    text = plan.read_text(encoding="utf-8", errors="replace")
    found = [m.group(1).strip().lower() for m in HEADING.finditer(text)]
    for name in REQUIRED_HEADINGS:
        if name.lower() not in found:
            problems.append(f"{plan.name}: missing heading '## {name}'")
    words = len(text.split())
    if not PLAN_WORDS_MIN <= words <= PLAN_WORDS_MAX:
        notes.append(
            f"{plan.name}: {words} words (guide is {PLAN_WORDS_MIN}-{PLAN_WORDS_MAX}; not a failure)"
        )


def go_imports(source: str) -> list[str]:
    """Return import paths from a Go source file, handling both forms."""
    paths: list[str] = []
    block = re.search(r"^import\s*\((.*?)^\)", source, re.MULTILINE | re.DOTALL)
    if block:
        paths += IMPORT_PATH.findall(block.group(1))
    for single in re.finditer(r'^import\s+(?:\w+\s+)?"([^"]+)"', source, re.MULTILINE):
        paths.append(single.group(1))
    return paths


def check_poc(poc: Path, problems: list[str]) -> None:
    if not poc.is_dir():
        problems.append(f"missing scaffold folder: {poc}")
        return
    for name in REQUIRED_POC_FILES:
        if not (poc / name).is_file():
            problems.append(f"missing scaffold file: {poc / name}")
    gomod = poc / "go.mod"
    if gomod.is_file() and not gomod.read_text(encoding="utf-8", errors="replace").lstrip().startswith("module "):
        problems.append(f"{gomod}: first line should be 'module <name>'")
    main = poc / "main.go"
    if main.is_file():
        source = main.read_text(encoding="utf-8", errors="replace")
        lines = source.count("\n") + 1
        if lines >= MAX_GO_LINES:
            problems.append(f"{main}: {lines} lines (limit is under {MAX_GO_LINES})")
        for path in go_imports(source):
            first = path.split("/")[0]
            if "." in first:
                problems.append(f"{main}: non-stdlib import '{path}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a meeting-to-PoC run offline.")
    parser.add_argument("--plan", default="design-plan.md", type=Path, help="path to design-plan.md")
    parser.add_argument("--poc", default="poc", type=Path, help="scaffold folder with go.mod, main.go, README.md")
    args = parser.parse_args()

    problems: list[str] = []
    notes: list[str] = []
    check_plan(args.plan, problems, notes)
    check_poc(args.poc, problems)

    for note in notes:
        print(f"note: {note}")
    if problems:
        for problem in problems:
            print(f"FAIL: {problem}")
        return 1
    print("PASS: design plan headings and scaffold layout look right.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

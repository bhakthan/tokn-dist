#!/usr/bin/env python3
"""Offline shape check for a lab-inventory plugin bundle. Reads local files only."""
import json
import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.\-]{0,62}[a-z0-9])?$")
REQUIRED_GATES = ("stock-table-complete", "no-negative-stock")


def main(bundle: str) -> int:
    root = Path(bundle)
    problems = []

    manifest_path = root / "plugin.json"
    manifest = {}
    if not manifest_path.is_file():
        problems.append("missing plugin.json at bundle root")
    else:
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            problems.append(f"plugin.json is not valid JSON: {exc}")

    name = str(manifest.get("name", ""))
    if not NAME_RE.match(name):
        problems.append(f"name {name!r} does not match the lowercase slug rule")
    if str(manifest.get("version", "")).count(".") < 2:
        problems.append("version should look like MAJOR.MINOR.PATCH")

    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        problems.append("missing SKILL.md")
    else:
        text = skill_path.read_text(encoding="utf-8")
        if "## Domain gates" not in text:
            problems.append("SKILL.md has no '## Domain gates' section")
        for gate in REQUIRED_GATES:
            if f"`{gate}`" not in text:
                problems.append(f"SKILL.md does not define gate `{gate}`")

    if problems:
        print("FAIL")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {name} {manifest.get('version')} has a manifest, skill, and both gates")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "lab-inventory"
    sys.exit(main(target))

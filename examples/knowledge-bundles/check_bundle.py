#!/usr/bin/env python3
"""Offline structure checker for OKF bundle folders (standard library only).

Reads local .md files only. It checks the hard structural rules a bundle
must satisfy and prints a per-file report. It is a structure check, not a
full YAML parser, and it does not replace `okf_validate` in TOKN.

Usage:
    python check_bundle.py bundle-valid bundle-broken bundle-v01
"""
import datetime
import pathlib
import re
import sys

TOP_KEY = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")
LOG_HEADING = re.compile(r"^##\s+(.+?)\s*$")


def frontmatter_lines(text):
    """Return the lines between a leading --- pair, or None if absent."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def top_level_keys(fm_lines):
    keys = {}
    for line in fm_lines:
        m = TOP_KEY.match(line)
        if m:
            keys[m.group(1)] = m.group(2).strip()
    return keys


def check_file(root, path, findings):
    rel = path.relative_to(root).as_posix()
    text = path.read_text(encoding="utf-8")

    if path.name == "log.md":
        for line in text.splitlines():
            m = LOG_HEADING.match(line)
            if not m:
                continue
            try:
                datetime.date.fromisoformat(m.group(1))
            except ValueError:
                findings.append(("error", rel,
                                 f"log heading {m.group(1)!r} is not ISO YYYY-MM-DD"))
        return

    fm = frontmatter_lines(text)

    if path.name == "index.md":
        if fm is None:
            return
        keys = set(top_level_keys(fm))
        if path.parent == root and keys == {"okf_version"}:
            return
        findings.append(("error", rel,
                         "index.md carries frontmatter; only the root index.md may, "
                         "and only with okf_version"))
        return

    if fm is None:
        findings.append(("error", rel, "no leading --- frontmatter block"))
        return
    if not top_level_keys(fm).get("type"):
        findings.append(("error", rel, "frontmatter has no non-empty `type`"))


def check_bundle(arg, findings_out):
    root = pathlib.Path(arg)
    if not root.is_dir():
        findings_out.append(("error", arg, "not a directory"))
        return
    files = sorted(root.rglob("*.md"))
    findings = []
    if not files:
        findings.append(("error", ".", "no .md files found"))
    if not (root / "index.md").is_file():
        findings.append(("warning", ".", "no root index.md"))
    for path in files:
        check_file(root, path, findings)
    findings_out.append((arg, len(files), findings))


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    failed = False
    for arg in argv:
        results = []
        check_bundle(arg, results)
        for item in results:
            if len(item) == 3 and isinstance(item[1], int):
                name, count, findings = item
                print(f"== {name}: {count} markdown file(s)")
                for sev, rel, msg in findings:
                    print(f"  [{sev}] {rel}: {msg}")
                if any(sev == "error" for sev, _, _ in findings):
                    failed = True
                    print("  FAIL")
                else:
                    print("  PASS: no hard structural errors")
            else:
                _, rel, msg = item
                print(f"== {rel}: [error] {msg}")
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

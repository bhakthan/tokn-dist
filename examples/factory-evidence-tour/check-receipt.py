#!/usr/bin/env python3
"""Verify a generated Factory repository without changing it."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python check-receipt.py <demo-repository>", file=sys.stderr)
        return 2
    repo = Path(sys.argv[1]).resolve()
    requested = os.environ.get("TOKN", "tokn")
    exe = shutil.which(requested)
    if not exe:
        print(
            "TOKN executable not found; install it and put it on PATH, or set "
            "TOKN to its path. Python 3 is also required.",
            file=sys.stderr,
        )
        return 2
    result = subprocess.run(
        [exe, "factory", "verify", "--repo-root", str(repo), "--json"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        print(result.stderr.strip() or "Factory verification failed", file=sys.stderr)
        return result.returncode
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        print(f"could not parse verification JSON: {exc}", file=sys.stderr)
        return 1
    required = ("ok", "chain_valid", "blobs_valid", "mode_consistent", "semantics_valid")
    failed = [key for key in required if report.get(key) is not True]
    if failed:
        print("FAIL verification fields: " + ", ".join(failed))
        return 1
    print(f"PASS factory evidence verified ({report.get('events', 0)} events)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check a staged local asset against its manifest using Python's stdlib."""

import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python check-local.py <manifest.json>", file=sys.stderr)
        return 2
    manifest_path = Path(sys.argv[1]).resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read manifest: {exc}", file=sys.stderr)
        return 1
    if manifest.get("license_reviewed") is not True:
        print("review the model license and set license_reviewed to true first", file=sys.stderr)
        return 1
    base = manifest_path.parent.resolve()
    asset = (base / str(manifest.get("artifact_path", ""))).resolve()
    if asset == base or base not in asset.parents:
        print("artifact_path must name a file inside the manifest folder", file=sys.stderr)
        return 1
    expected = str(manifest.get("sha256", "")).lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        print("manifest sha256 must be a trusted 64-character hexadecimal digest", file=sys.stderr)
        return 1
    if not asset.is_file():
        print("staged artifact is missing; copy it into the scratch folder first", file=sys.stderr)
        return 1
    digest = hashlib.sha256()
    with asset.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != expected:
        print("FAIL SHA-256 mismatch", file=sys.stderr)
        return 1
    print("PASS SHA-256 matches the staged manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

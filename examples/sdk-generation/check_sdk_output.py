"""Summarise the SDK folders written by `tokn sdkgen generate`.

Offline, standard library only. Reads local files under the output folder and
reports how many files each language folder contains. It does not compile
anything and does not call TOKN.

Usage: python check_sdk_output.py [output-folder] [language ...]
Defaults: generated-sdk, and the languages ts and py.
"""

import pathlib
import sys


def main(argv):
    out = pathlib.Path(argv[1] if len(argv) > 1 else "generated-sdk")
    languages = argv[2:] or ["ts", "py"]
    if not out.is_dir():
        print(f"Output folder not found: {out}. Run `tokn sdkgen generate` first.")
        return 1

    status = 0
    for lang in languages:
        folder = out / lang
        files = [p for p in folder.rglob("*") if p.is_file()] if folder.is_dir() else []
        if not files:
            print(f"{lang}: no files found in {folder}")
            status = 1
            continue
        total = sum(p.stat().st_size for p in files)
        print(f"{lang}: {len(files)} file(s), {total} byte(s) in {folder}")
    return status


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

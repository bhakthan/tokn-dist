"""Read-only checker for the geospatial example.

Reads the saved text output of a `tokn agent-run` session and reports which
gate messages appeared. It makes no network calls and writes no files.

Usage:
    python check_output.py run-output.txt

This is a keyword check on the saved text. It confirms that a gate message
appeared; it does not prove the agent handled it correctly. Read the summary too.
"""

import sys
from pathlib import Path

# Marker text is taken from the geospatial domain's error messages.
EXPECTED = {
    "CRS: area computed in a geographic CRS": "GEOGRAPHIC CRS FOR MEASUREMENT",
    "CRS: distance/area in Web Mercator": "WEB MERCATOR FOR AREA",
    "Cloud mask missing": "CLOUD MASK REQUIRED",
    "Cloud cover above threshold": "CLOUD COVER EXCEEDED",
    "Resolution ratio above 10x": "RESOLUTION MISMATCH",
    "Temporal gap above 5 years": "TEMPORAL GAP EXCEEDED",
}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"No such file: {path}")
        return 2

    text = path.read_text(encoding="utf-8", errors="replace").upper()
    seen = 0
    for label, marker in EXPECTED.items():
        hit = marker in text
        seen += hit
        print(f"[{'SEEN' if hit else 'not seen':8}] {label}  ({marker})")

    print(f"\n{seen} of {len(EXPECTED)} gate messages appeared in {path.name}.")
    print("A missing message means the step did not run, not that the gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

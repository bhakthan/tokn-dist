"""Read-only checker for the legal-analysis example.

Reads the saved text output of a `tokn agent-run` session and reports which
gate messages appeared. It makes no network calls and writes no files.

Usage:
    python check_output.py run-output.txt

This is a keyword check on the saved text. It confirms that a gate message
appeared; it does not prove the agent handled it correctly. Read the summary too.
Nothing here is legal advice.
"""

import sys
from pathlib import Path

# Marker text is taken from the legalai domain's hook and error messages.
EXPECTED = {
    "Citation format rejected": "INVALID CITATION FORMAT",
    "Reporter not in known table": "INVALID REPORTER",
    "Cross-jurisdiction citation blocked": "CROSS-JURISDICTION WITHOUT CONFLICT ANALYSIS",
    "Privilege leak in output": "PRIVILEGE LEAK",
    "Authority layer missing (warning)": "AUTHORITY LAYER ANNOTATION",
    "Disclaimer missing (warning)": "MISSING LEGAL DISCLAIMER",
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

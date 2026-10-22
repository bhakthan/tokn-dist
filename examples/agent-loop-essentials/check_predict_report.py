"""Print the newest Predictability Report from a scratch folder.

Offline, standard library only. Reads files under .nospace/predict/ and
prints their top-level fields. It does not call TOKN or any model.

Usage: python check_predict_report.py [scratch-folder]
"""

import json
import pathlib
import sys


def main(argv):
    root = pathlib.Path(argv[1] if len(argv) > 1 else ".")
    reports = sorted((root / ".nospace" / "predict").glob("report-*.json"))
    if not reports:
        print("No report-*.json found under .nospace/predict/. Run the agent with --predict first.")
        return 1

    latest = reports[-1]
    data = json.loads(latest.read_text(encoding="utf-8"))
    print(f"Report: {latest.name} ({len(reports)} report(s) in total)")
    for key in sorted(data):
        value = data[key]
        if isinstance(value, (dict, list)):
            print(f"  {key}: <{type(value).__name__}, {len(value)} item(s)>")
        else:
            print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

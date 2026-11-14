#!/usr/bin/env python3
"""make-triage-request.py - build a System One triage request from out/report.json.

The request carries only an inspection summary: record totals, the adjuster
referrals by priority, and per damage point the number of referrals and the
check with the highest P(yes). It contains no photos, file paths or claim
reference.

Usage:
  python make-triage-request.py [--report PATH] [--out PATH]

Defaults: out/report.json in, out/triage-request.json out (both next to this
script). Python 3.10+, standard library only, no network calls.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

QUESTIONS = {
    "field_inspection_recommended": {
        "type": "noul",
        "instructions": (
            "Based on this inspection summary, how likely is it that a licensed "
            "adjuster should arrange a field inspection before any decision? "
            "Advisory triage only; this is not a coverage or payment decision."
        ),
    },
    "route": {
        "type": "choice",
        "instructions": "Which handling route fits this inspection summary best? Advisory triage only.",
        "criteria": {
            "desk_review": "Few or low-impact referrals; an adjuster can review the photos at a desk.",
            "field_inspection": "Referrals on body panels or on several damage points; an in-person look helps.",
            "specialist_glass": "Referrals on glazing (windshield or mirror glass) that a glass specialist should assess.",
        },
    },
    "urgency": {
        "type": "score",
        "instructions": "How urgently should an adjuster look at this file, given the referrals and their priorities?",
        "criteria": [
            "Level 0: no open referrals.",
            "Level 1: referrals only on minor or low-impact points.",
            "Level 2: referrals on body panels or on several points.",
            "Level 3: referrals on glazing or structural points, or possible missed damage.",
        ],
    },
}


def p_yes(rec: dict):
    """P(yes) for a yes/no record, or None for any other record."""
    label = rec.get("label")
    p = rec.get("probability")
    if label not in ("yes", "no") or not isinstance(p, (int, float)):
        return None
    return float(p) if label == "yes" else 1.0 - float(p)


def build_state(report: dict) -> dict:
    records = report.get("records", [])
    summary = report.get("summary", {})
    priorities = Counter(
        r.get("priority") or "none"
        for r in records
        if r.get("status") == "adjuster_referral"
    )
    points = []
    for point in report.get("points", []):
        name = point.get("name")
        mine = [r for r in records if r.get("point") == name]
        scored = [(p_yes(r), r.get("check_id")) for r in mine if p_yes(r) is not None]
        top_p, top_check = max(scored) if scored else (None, None)
        severity = next(
            (r.get("label") for r in mine if r.get("check_id") == "severity" and r.get("label")),
            None,
        )
        points.append({
            "point": name,
            "adjuster_referrals": sum(1 for r in mine if r.get("status") == "adjuster_referral"),
            "top_check": top_check,
            "top_p_yes": round(top_p, 3) if top_p is not None else None,
            "severity": severity,
        })
    return {
        "inspection": {
            "check_set": report.get("check_set"),
            "points": summary.get("points"),
            "records": summary.get("records"),
            "corroborated": summary.get("corroborated"),
            "clear": summary.get("clear"),
            "adjuster_referrals": summary.get("adjuster_referrals"),
        },
        "referrals_by_priority": dict(priorities),
        "points": points,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a triage request from a Loss Inspection report.")
    parser.add_argument("--report", default=str(HERE / "out" / "report.json"))
    parser.add_argument("--out", default=str(HERE / "out" / "triage-request.json"))
    args = parser.parse_args()

    try:
        report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"[!] Report not found: {args.report}. Run run-inspection first.", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as err:
        print(f"[!] Cannot read the report: {err}", file=sys.stderr)
        return 2

    request = {"state": build_state(report), "questions": QUESTIONS}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(request, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out} (summary only: no photos, paths or claim reference).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

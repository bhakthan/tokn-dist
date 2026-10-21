"""Grade a science-review run from its streamed output. Output only.

Standard library only. Reads one local NDJSON file; makes no network call and
never reads the model, the repository, or any credential.

Usage:
    python check.py events.ndjson
    (events.ndjson comes from: tokn agent-run ... --output-format stream-json > events.ndjson)

Exit status: 0 = PASS, 1 = FAIL, 2 = could not read the file.
"""

import json
import sys

REQUIRED = {
    "untraceable_number": "high",
    "unresolved_citation": "high",
    "code_artifact_drift": "critical",
}
FORBIDDEN = {"incomplete_provenance"}
TOOL = "review_artifact"


def parse_lines(path):
    events = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                outer = json.loads(line)
            except json.JSONDecodeError:
                continue
            if outer.get("type") == "progress" and str(outer.get("text", "")).startswith("{"):
                try:
                    events.append(json.loads(outer["text"]))
                except json.JSONDecodeError:
                    pass
            else:
                events.append(outer)
    return events


def payload_of(event):
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def tool_name(payload):
    return payload.get("ToolName") or payload.get("tool_name")


def find_report(value):
    if isinstance(value, dict):
        if "findings" in value and "passed" in value:
            return value
        for child in value.values():
            found = find_report(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_report(child)
            if found is not None:
                return found
    return None


def grade(events):
    calls = [e for e in events if e.get("type") == "tool.call" and tool_name(payload_of(e)) == TOOL]
    results = [e for e in events if e.get("type") == "tool.result" and tool_name(payload_of(e)) == TOOL]
    checks = {"called": len(calls) >= 1 and len(results) >= 1}
    report = None
    if results:
        raw = payload_of(results[-1]).get("Output") or payload_of(results[-1]).get("output") or ""
        try:
            report = find_report(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            report = None
    checks["report_present"] = report is not None
    findings = report.get("findings", []) if report else []
    by_kind = {}
    for finding in findings:
        by_kind.setdefault(finding.get("kind"), finding.get("severity"))
    for kind, severity in REQUIRED.items():
        checks[f"reports_{kind}_{severity}"] = by_kind.get(kind) == severity
    checks["no_incomplete_provenance"] = not any(kind in by_kind for kind in FORBIDDEN)
    checks["not_passed"] = report is not None and report.get("passed") is False
    checks["three_findings"] = len(findings) == 3
    return checks


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    try:
        events = parse_lines(argv[1])
    except OSError as err:
        print(f"could not read {argv[1]}: {err}")
        return 2
    checks = grade(events)
    failed = [name for name, ok in checks.items() if not ok]
    print(json.dumps({"verdict": "PASS" if not failed else "FAIL", "checks": checks, "failed": failed}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

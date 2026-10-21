"""Grade a finrisk System One run from TOKN's local run log.

Standard library only. Reads files under the repo root; makes no network call.

Usage:
    python check.py workspace --exit-code 0

The exit code is the one printed by `tokn agent-run` (pass it with --exit-code).
Exit status of this script: 0 = PASS, 1 = FAIL.
"""

import argparse
import json
import re
from pathlib import Path


CASE = "synthetic-materiality-6pct"
DOMAIN_TOOL = "assess_materiality"
JEV_TOOL = "system_one_evaluate"
QUESTION_TYPES = {"grounded": "noul", "qualified": "noul", "disposition": "choice"}


def tool_payload(envelope, name):
    if not isinstance(envelope, dict) or envelope.get("error"):
        return None
    if "result" in envelope:
        return envelope["result"] if envelope.get("tool") == name else None
    return envelope


def grade(entries, exit_code):
    checks = {"process_completed": exit_code == 0}
    calls = [
        (i, call)
        for i, entry in enumerate(entries)
        if entry.get("role") == "assistant"
        for call in entry.get("tool_calls", [])
    ]
    domain_calls = [(i, c) for i, c in calls if c.get("name") == DOMAIN_TOOL]
    jev_calls = [(i, c) for i, c in calls if c.get("name") == JEV_TOOL]
    domain_results = [(i, e) for i, e in enumerate(entries) if e.get("role") == "tool" and e.get("tool_name") == DOMAIN_TOOL]
    jev_results = [(i, e) for i, e in enumerate(entries) if e.get("role") == "tool" and e.get("tool_name") == JEV_TOOL]
    finals = [(i, e) for i, e in enumerate(entries) if e.get("role") == "assistant" and e.get("event") == "final"]
    checks["exact_domain_then_jev_calls"] = len(domain_calls) == len(jev_calls) == len(domain_results) == len(jev_results) == 1
    checks["no_unrequested_tools"] = len(calls) == 2
    checks["one_final"] = len(finals) == 1
    if not (checks["exact_domain_then_jev_calls"] and checks["one_final"]):
        return report(checks)
    di, dc = domain_calls[0]
    dri, dr = domain_results[0]
    ji, jc = jev_calls[0]
    jri, jr = jev_results[0]
    fi, final = finals[0]
    checks["chain_order"] = di < dri < ji < jri < fi
    starts = [e for e in entries if e.get("event") == "start"]
    checks["domain_mode_recorded"] = len(starts) == 1 and starts[0].get("mode") == "finrisk"
    checks["no_tool_errors"] = not dr.get("error") and not jr.get("error") and not dr.get("event") and not jr.get("event")
    try:
        domain_envelope = json.loads(dr.get("content", ""))
        jev_envelope = json.loads(jr.get("content", ""))
        domain = tool_payload(domain_envelope, DOMAIN_TOOL)
        jev = tool_payload(jev_envelope, JEV_TOOL)
        match = re.fullmatch(r"\s*```json\s*\n(.*?)\n```\s*", final.get("content", ""), re.DOTALL)
        answer = json.loads(match.group(1)) if match else None
        checks["structured_results"] = all(isinstance(v, dict) for v in (domain, jev, answer))
    except (json.JSONDecodeError, TypeError):
        checks["structured_results"] = False
    if not checks["structured_results"]:
        return report(checks)
    checks["domain_inputs"] = dc.get("input") == {"amount": 6000000, "total_assets": 100000000, "jurisdiction": "SEC"}
    checks["computed_materiality"] = domain.get("status") == "success" and domain.get("level") == "material" and domain.get("ratio") == 0.06
    request = jc.get("input", {})
    state = request.get("state", {})
    questions = request.get("questions", {})
    checks["three_questions_one_request"] = isinstance(questions, dict) and {
        k: v.get("type") for k, v in questions.items() if isinstance(v, dict)
    } == QUESTION_TYPES and len(questions) == 3
    checks["draft_and_domain_sent"] = (
        isinstance(state, dict) and state.get("case_id") == CASE
        and state.get("domain_result") in (domain, domain_envelope)
        and isinstance(state.get("draft"), str) and bool(state["draft"].strip())
    )
    responses = jev.get("answers", {})
    checks["jev_response_complete"] = (
        isinstance(responses, dict) and set(responses) == set(QUESTION_TYPES)
        and isinstance(jev.get("model"), str) and bool(jev["model"])
        and isinstance(jev.get("latency_ms"), (int, float))
        and jev["latency_ms"] >= 0
        and jev.get("attempts") == 1
    )
    checks["actual_signals_used"] = (
        answer.get("jev_answers") == responses and answer.get("jev_model") == jev.get("model")
        and checks["jev_response_complete"]
    )
    checks["final_grounded"] = (
        answer.get("case_id") == CASE and answer.get("materiality_level") == "material"
        and answer.get("ratio") == 0.06
        and isinstance(state, dict) and answer.get("draft") == state.get("draft")
    )
    briefing = answer.get("briefing", "")
    reason = answer.get("revision_reason", "")
    checks["qualified_briefing"] = (
        isinstance(briefing, str) and "synthetic" in briefing.lower()
        and "not investment advice" in briefing.lower()
        and "quantitative" in briefing.lower() and "regulatory" in briefing.lower()
    )
    checks["revision_explained"] = isinstance(reason, str) and bool(reason.strip())
    return report(checks, jev.get("model"), jev.get("latency_ms"))


def report(checks, model=None, latency=None):
    return {
        "verdict": "PASS" if all(checks.values()) else "FAIL_CHAIN",
        "checks": checks,
        "failed": [k for k, value in checks.items() if not value],
        "jev_model": model,
        "jev_latency_ms": latency,
    }


def grade_directory(repo_root, exit_code):
    logs = []
    for path in (repo_root / ".nospace" / "runs").glob("*.jsonl"):
        entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        own = [e for e in entries if e.get("record_format") == "runlog/v1"]
        if own:
            logs.append(own)
    if len(logs) != 1:
        return report({"exactly_one_runlog": False, "process_completed": exit_code == 0})
    return grade(logs[0], exit_code)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grade a finrisk System One run from its local run log.")
    parser.add_argument("repo_root", type=Path, help="the --repo-root you passed to tokn agent-run (for example: workspace)")
    parser.add_argument("--exit-code", type=int, default=0, help="the exit code printed by tokn agent-run")
    args = parser.parse_args()
    result = grade_directory(args.repo_root, args.exit_code)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["verdict"] == "PASS" else 1)

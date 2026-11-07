"""Deterministic outer ring for the domain relay. No model grades the models."""

import json
from pathlib import Path

REQUIRED = ["CAPABILITIES.md", "PLAN.md", "result.v1.json", "result.json", "RESULT.md",
            "critique.json", "CRITIQUE.md", "decision.json", "REFLECTION.md", "TRACE.json"]


def _load(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _accuracy(result, truth):
    if not isinstance(result, dict) or not truth:
        return 0.0, {}
    got = {str(i.get("id")): str(i.get("status", "")).strip().lower() for i in result.get("items", []) if isinstance(i, dict)}
    per = {k: got.get(k) == v.lower() for k, v in truth.items()}
    return round(sum(per.values()) / len(truth), 2), per


def grade(ws, scenario, trace):
    ws = Path(ws)
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    missing = [f for f in REQUIRED if not (ws / f).is_file()]
    check("artifacts_present", not missing, "missing: " + ", ".join(missing) if missing else "all 10 present")

    final = _load(ws / "result.json")
    v1 = _load(ws / "result.v1.json")
    check("result_json_valid", isinstance(final, dict) and isinstance(final.get("items"), list),
          "final result.json parses with an items list" if isinstance(final, dict) else "result.json missing or invalid")

    vocab = {s.lower() for s in scenario["status_vocabulary"]}
    truth = scenario["ground_truth"]
    if isinstance(final, dict):
        bad = [i.get("id") for i in final.get("items", []) if str(i.get("status", "")).lower() not in vocab]
        check("status_vocabulary", not bad, f"off-vocabulary statuses: {bad}" if bad else "all statuses in vocabulary")
        ids = {str(i.get("id")) for i in final.get("items", [])}
        absent = [k for k in truth if k not in ids]
        check("all_items_assessed", not absent, f"items missing: {absent}" if absent else f"{len(truth)} items")

    acc_v1, _ = _accuracy(v1, truth)
    acc_final, per = _accuracy(final, truth)
    wrong = [k for k, ok in per.items() if not ok]
    check("ground_truth", acc_final == 1.0,
          f"final {acc_final} (v1 {acc_v1}); wrong: " + ", ".join(
              f"{k} expected {truth[k]} got {next((i.get('status') for i in (final or {}).get('items', []) if str(i.get('id')) == k), None)}"
              for k in wrong) if wrong else f"final {acc_final} (v1 {acc_v1})")

    text = " ".join((ws / f).read_text(encoding="utf-8", errors="replace") for f in ("RESULT.md", "result.json") if (ws / f).is_file()).lower()
    # "a|b" means any one alternative satisfies the term.
    absent_terms = [t for t in scenario.get("must_mention", []) if not any(a.strip().lower() in text for a in t.split("|"))]
    check("must_mention", not absent_terms, f"not mentioned: {absent_terms}" if absent_terms else "all present")
    present_forbidden = [t for t in scenario.get("forbidden_phrases", []) if t.lower() in text]
    check("forbidden_phrases", not present_forbidden, f"found: {present_forbidden}" if present_forbidden else "none found")

    critique = _load(ws / "critique.json")
    findings = [f for f in (critique or {}).get("findings", []) if isinstance(f, dict)]
    check("critique_has_findings", bool(findings), f"{len(findings)} findings")
    responses = {str(r.get("id")): r for r in (final or {}).get("critique_response", []) if isinstance(r, dict)}
    unanswered = [f.get("id") for f in findings if str(f.get("id")) not in responses]
    bad_action = [r for r in responses.values() if r.get("action") not in ("fixed", "rebutted", "deferred")]
    check("every_finding_answered", findings and not unanswered and not bad_action,
          f"unanswered: {unanswered}, bad actions: {len(bad_action)}" if unanswered or bad_action
          else f"{len(responses)} responses")

    decision = _load(ws / "decision.json")
    answers = ((decision or {}).get("response") or {}).get("answers") or {}
    asked = (decision or {}).get("questions") or {}
    check("decision_answered", asked and all(isinstance(answers.get(q, {}).get("noul"), (int, float)) for q in asked),
          f"{len(answers)}/{len(asked)} typed answers")

    stages = {s.get("name"): s for s in (trace or {}).get("stages", [])}
    execute_tools = (stages.get("EXECUTE") or {}).get("tool_calls") or {}
    expected = set(scenario.get("expected_tools", []))
    used = sorted(expected.intersection(execute_tools))
    check("execute_used_domain_tools", used, f"used {used} of expected {sorted(expected)}")
    critic_tools = (stages.get("CRITIQUE") or {}).get("tool_calls") or {}
    check("critic_reran_tools", expected.intersection(critic_tools),
          f"critic used {sorted(expected.intersection(critic_tools))}")

    reflection = (ws / "REFLECTION.md").read_text(encoding="utf-8", errors="replace") if (ws / "REFLECTION.md").is_file() else ""
    all_tools = set()
    for s in stages.values():
        all_tools.update((s.get("tool_calls") or {}).keys())
    named = sorted(t for t in all_tools.intersection(expected) if t in reflection)
    check("reflection_grounded", named and "/teach" in reflection,
          f"names traced tools {named}; has /teach rule: {'/teach' in reflection}")

    failures = [c for c in checks if not c["ok"]]
    metrics = {"accuracy_v1": acc_v1, "accuracy_final": acc_final, "findings": len(findings),
               "findings_answered": len(responses), "routing": (decision or {}).get("routing"),
               "execute_domain_tools": len(used)}
    return {"verdict": "PASS" if not failures else "FAIL", "checks": checks, "metrics": metrics}

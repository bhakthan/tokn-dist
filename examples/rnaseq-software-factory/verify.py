#!/usr/bin/env python3
"""Post-run grader over a factory store (RNA-seq Agent Factory live test).

    python verify.py --repo <seed repo> --key <answer_key.json> --bindings <bindings.json>
                     [--tokn <tokn.exe>] [--targets <targets dir>] [--out <report dir>]

Checks:
  1. DE metrics: grade.py on the code DEPLOYED to prod (targets/prod/CURRENT),
     else on the repo's checked-out tree.
  2. `tokn factory verify --json`: chain, blobs, mode, semantics all valid.
  3. Decision records: decision.recorded events with a `call` (decision-model
     audit) exist.
  4. Model attribution: each finished AgentRun's provider/model matches the
     spec binding for its role (or one of that binding's fallbacks). Runs that
     carry no provider/model are reported as "unavailable", not as failures.
  5. Single-cell service (when --requirements says sc): grade.py's sc gate on
     the deployed tree, and the REQ-SC-0001 product request appears in the
     event log. --showcase adds the report-only real-C2S run.
Writes REPORT.md and report.json to --out (default: next to the repo) and
prints the markdown. Exit 0 when every available check passes.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STORE_REL = Path(".nospace") / "factory"


def read_events(repo: Path) -> list[dict]:
    p = repo / STORE_REL / "events.jsonl"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                out.append({"kind": "<unparseable>"})
    return out


def runs_from(events: list[dict]) -> dict[str, dict]:
    runs: dict[str, dict] = {}
    for e in events:
        if e.get("kind") in ("run.started", "run.finished", "run.failed") and isinstance(e.get("payload"), dict):
            r = e["payload"]
            if r.get("id"):
                runs[r["id"]] = {**runs.get(r["id"], {}), **r, "_last_kind": e["kind"]}
    return runs


def allowed_for(binding: dict) -> list[tuple[str, str]]:
    out = [(binding.get("provider", ""), binding.get("model", ""))]
    for fb in binding.get("fallback", []) or []:
        out.extend(allowed_for(fb))
    return out


def check_attribution(runs: dict[str, dict], bindings: dict) -> tuple[list[dict], bool]:
    rows, ok = [], True
    roles = bindings.get("roles", {})
    default = bindings.get("default")
    for rid, r in sorted(runs.items()):
        if r.get("_last_kind") == "run.started":
            continue
        role = r.get("role", "")
        b = roles.get(role) or default
        prov, mod = r.get("provider", ""), r.get("model", "")
        row = {"run": rid, "role": role, "stage": r.get("stage", ""), "provider": prov or None, "model": mod or None,
               "fallback_from": r.get("fallback_from", []), "expected": None, "verdict": ""}
        if b is None:
            row["verdict"] = "no binding (run-level default)"
        else:
            allowed = allowed_for(b)
            row["expected"] = [f"{p}/{m}" for p, m in allowed]
            if not prov and not mod:
                row["verdict"] = "unavailable (run recorded no provider/model)"
            elif (prov, mod) in allowed:
                row["verdict"] = "match" if (prov, mod) == allowed[0] else "match (fallback)"
            else:
                row["verdict"] = "MISMATCH"
                ok = False
            if r.get("_last_kind") == "run.failed":
                row["verdict"] += " (run failed)"
        rows.append(row)
    return rows, ok


def tokn_verify(tokn: str | None, repo: Path) -> dict:
    if not tokn:
        return {"available": False, "reason": "no tokn binary given"}
    try:
        p = subprocess.run([tokn, "factory", "verify", "--json", "--repo-root", str(repo)],
                           capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"available": False, "reason": str(e)}
    try:
        rep = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"available": False, "reason": f"exit {p.returncode}: {(p.stdout + p.stderr)[-400:]}"}
    rep["available"] = True
    rep["exit_code"] = p.returncode
    return rep


def deployed_tree(targets: Path | None, env: str) -> Path | None:
    if targets is None:
        return None
    cur = targets / env / "CURRENT"
    if not cur.is_file():
        return None
    rel = cur.read_text(encoding="utf-8").strip().splitlines()[0].strip() if cur.read_text(encoding="utf-8").strip() else ""
    d = (targets / env / rel) if rel else None
    return d if d and (d / "rnaseq_de").is_dir() else None


def grade_tree(code_root: Path, repo: Path, key: Path, work: Path, requirements: Path | None = None) -> dict:
    """Grade code_root/rnaseq_de against repo's data/ and golden/ in a scratch copy."""
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    shutil.copytree(code_root / "rnaseq_de", work / "rnaseq_de", ignore=shutil.ignore_patterns("__pycache__"))
    for d in ("data", "golden"):
        shutil.copytree(repo / d, work / d)
    cmd = [sys.executable, str(HERE / "grade.py"), "--key", str(key), "--repo", str(work)]
    if requirements and requirements.is_file():
        cmd += ["--requirements", str(requirements)]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        res = {"pass": False, "failures": [f"grade.py produced no JSON (exit {p.returncode}): {p.stderr[-400:]}"]}
    res["exit_code"] = p.returncode
    shutil.rmtree(work, ignore_errors=True)
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--key", required=True, type=Path)
    ap.add_argument("--bindings", type=Path, default=None, help="bindings.json written by run.py (expected models per role)")
    ap.add_argument("--tokn", default=None)
    ap.add_argument("--targets", type=Path, default=None)
    ap.add_argument("--env", default="prod", help="target environment whose deployed code is graded")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--requirements", type=Path, default=None,
                    help="intake/requirements.json from run.py; {\"sc\": true} also grades the single-cell service")
    ap.add_argument("--showcase", type=Path, default=None, help="c2s-showcase.json from run.py (report-only)")
    a = ap.parse_args(argv)
    repo = a.repo.resolve()
    out = (a.out or repo.parent / "verify").resolve()
    out.mkdir(parents=True, exist_ok=True)

    events = read_events(repo)
    kinds: dict[str, int] = {}
    for e in events:
        kinds[e.get("kind", "?")] = kinds.get(e.get("kind", "?"), 0) + 1

    deployed = deployed_tree(a.targets, a.env)
    graded_what = f"{a.env} deployment {deployed}" if deployed else f"repo tree {repo}"
    graded_deploy = deployed is not None
    if deployed is None:
        deployed = repo
    req = a.requirements.resolve() if a.requirements else None
    sc_required = bool(req and req.is_file() and json.loads(req.read_text(encoding="utf-8")).get("sc"))
    grade = grade_tree(deployed, repo, a.key.resolve(), out / "_grade_work", req)
    showcase = json.loads(a.showcase.read_text(encoding="utf-8")) if a.showcase and a.showcase.is_file() else None
    feature_seen = any("REQ-SC-0001" in json.dumps(e) for e in events)

    chain = tokn_verify(a.tokn, repo)
    decisions = [e["payload"] for e in events if e.get("kind") == "decision.recorded" and isinstance(e.get("payload"), dict)]
    model_calls = [d for d in decisions if d.get("call")]

    runs = runs_from(events)
    bindings = json.loads(a.bindings.read_text(encoding="utf-8")) if a.bindings and a.bindings.is_file() else {}
    attribution, attr_ok = check_attribution(runs, bindings) if bindings else ([], True)
    attr_available = any(not r["verdict"].startswith("unavailable") for r in attribution)

    checks = {
        "de_grade": {"ok": bool(grade.get("pass")), "graded": graded_what},
        "store_verify": {"ok": bool(chain.get("available") and chain.get("ok") and chain.get("chain_valid")),
                         "available": chain.get("available", False)},
        "decision_records": {"ok": bool(model_calls), "count": len(decisions), "model_calls": len(model_calls)},
        "model_attribution": {"ok": attr_ok, "available": attr_available, "runs": len(attribution)},
        "prod_deployed": {"ok": kinds.get("release.deployed", 0) > 0 and graded_deploy},
        "sc_service": {"ok": bool(grade.get("sc_ok")), "available": sc_required,
                       "correct": grade.get("sc_correct"), "wrong": grade.get("sc_wrong")},
        "feature_item": {"ok": feature_seen, "available": sc_required,
                         "detail": "REQ-SC-0001 intake record traced into the factory event log"},
        "c2s_showcase": {"ok": bool(showcase and showcase.get("ok")), "available": bool(showcase),
                         "detail": {k: (showcase or {}).get(k) for k in ("model", "live_correct", "live_wrong", "seconds")}},
    }
    overall = all(c["ok"] for k, c in checks.items() if c.get("available", True))
    report = {"pass": overall, "checks": checks, "grade": grade, "store_verify": chain,
              "event_kinds": kinds, "attribution": attribution,
              "decision_calls": [{"id": d.get("id"), "item": d.get("work_item_id"), **(d.get("call") or {})} for d in model_calls]}

    md = [f"# RNA-seq factory live test - verify ({'PASS' if overall else 'FAIL'})", "",
          "| check | result | detail |", "|---|---|---|"]
    for k, c in checks.items():
        res = "n/a" if not c.get("available", True) else ("PASS" if c["ok"] else "FAIL")
        md.append(f"| {k} | {res} | {', '.join(f'{x}={y}' for x, y in c.items() if x != 'ok')} |")
    md += ["", "## DE grade", "", "```json", json.dumps(grade, indent=2, sort_keys=True), "```", "",
           "## Model attribution", ""]
    if not bindings:
        md.append("_bindings.json not given: attribution unavailable._")
    elif not attribution:
        md.append("_no finished AgentRun records in the store._")
    else:
        md += ["| run | role | stage | used | expected | verdict | fallback_from |", "|---|---|---|---|---|---|---|"]
        for r in attribution:
            used = f"{r['provider']}/{r['model']}" if r["provider"] or r["model"] else "-"
            md.append(f"| {r['run']} | {r['role']} | {r['stage']} | {used} | {', '.join(r['expected'] or [])} | "
                      f"{r['verdict']} | {'; '.join(r['fallback_from'] or [])} |")
    md += ["", "## Decision-model calls", ""]
    md += [f"- {d['id']} ({d['item']}): kind={d.get('kind')} backend={d.get('backend')} model={d.get('model')} "
           f"local={d.get('local')} outcome={d.get('outcome')}" for d in report["decision_calls"]] or ["_none_"]
    md += ["", "## Event kinds", ""] + [f"- {k}: {v}" for k, v in sorted(kinds.items())]
    text = "\n".join(md) + "\n"
    (out / "REPORT.md").write_text(text, encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(text)
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())

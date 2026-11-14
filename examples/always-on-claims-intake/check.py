#!/usr/bin/env python3
"""check.py - grade one run of the claims intake example from its saved state.

Reads the state directory (runs/*.jsonl, sessions/*.json, budget.json and
status.json) and the workspace. It makes no model calls and changes nothing.

Usage:
  python check.py [--state-dir DIR] [--workspace DIR]

Defaults: state/ and workspace/ next to this script. Exit 0 when every check
passes, 1 when a check fails, 2 when the state directory does not exist.

Not checked here: C1 (run --once exits 0). run.ps1 and run.sh stop when the
run fails. The workspace comparison needs state/workspace-before.txt, which
run.ps1 and run.sh write before the run.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AGENT_DIR_NAME = "always-on"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_runs(state):
    runs = []
    runs_dir = state / "runs"
    if runs_dir.is_dir():
        for f in sorted(runs_dir.glob("*.jsonl")):
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    runs.append(json.loads(line))
    return runs


def load_sessions(state):
    sessions = {}
    sess_dir = state / "sessions"
    if sess_dir.is_dir():
        for f in sorted(sess_dir.glob("*.json")):
            s = read_json(f)
            sessions[s["id"]] = s
    return sessions


def text_of(m):
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""


def is_turn(m):
    # Tool results and the <system-context> lines injected at the start of a
    # run are not user turns, so they never count as one.
    if m.get("role") != "user":
        return False
    body = text_of(m).lstrip()
    return bool(body) and not body.startswith("<system-context>")


def user_turns(session):
    return [m for m in session.get("messages", []) if is_turn(m)]


def final_answers(session):
    """The last assistant text after each user turn, in order."""
    out, cur = [], None
    for m in session.get("messages", []):
        if m.get("role") == "user":
            if not is_turn(m):
                continue
            if cur is not None:
                out.append(cur)
            cur = ""
        elif m.get("role") == "assistant" and text_of(m).strip():
            cur = text_of(m)
    if cur is not None:
        out.append(cur)
    return out


def snapshot(ws):
    """sha256 of every workspace file, minus the directories TOKN owns."""
    out = {}
    for p in sorted(ws.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ws).as_posix()
        if rel.startswith((".nospace/", ".tokn/")):
            continue
        out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def read_before(path):
    before = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split(" ", 1)
            before[rel.strip()] = digest
    return before


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state-dir", type=Path, default=HERE / "state")
    ap.add_argument("--workspace", type=Path, default=HERE / "workspace")
    args = ap.parse_args()
    state = args.state_dir.resolve()
    ws = args.workspace.resolve()
    if not state.is_dir():
        print(f"No state directory at {state}. Run run.ps1 or run.sh first.", file=sys.stderr)
        sys.exit(2)

    runs = load_runs(state)
    sessions = load_sessions(state)
    budget = read_json(state / "budget.json") if (state / "budget.json").exists() else {"days": {}}
    status = {}
    if (state / "status.json").exists():
        try:
            status = read_json(state / "status.json")
        except ValueError:
            status = {}
    ledger_total = sum(int(v) for v in budget.get("days", {}).values())
    runs_tokens = sum(int(r.get("tokens_used", 0)) for r in runs)

    by_session = {}
    for r in runs:
        by_session.setdefault(r.get("session_id", ""), []).append(r)
    a1001 = final_answers(sessions.get("CLM-1001", {}))
    a1002 = final_answers(sessions.get("CLM-1002", {}))
    hook_answer = " ".join(final_answers(sessions.get("portal-1", {})))
    first = a1001[0] if a1001 else ""
    second = a1001[1] if len(a1001) > 1 else ""
    a2 = a1002[0] if a1002 else ""
    r1002 = (by_session.get("CLM-1002") or [{}])[0]
    rhook = (by_session.get("portal-1") or [{}])[0]
    s1 = sessions.get("CLM-1001", {})

    checks = []

    def check(cid, ok, detail):
        checks.append((cid, bool(ok), detail))

    check("C2 retried event processed once", len(runs) == 4,
          f"{len(runs)} runs for 5 enqueues (4 distinct keys)")
    check("C3 every run completed",
          runs and all(r.get("disposition") == "complete" for r in runs),
          ", ".join(f"{r.get('session_id')}:{r.get('disposition')}/{r.get('status')}" for r in runs) or "no runs")
    check("C4 CLM-1001 is one session with two runs",
          s1.get("runs") == 2 and len(user_turns(s1)) >= 2,
          f"runs={s1.get('runs')} user_turns={len(user_turns(s1))}")
    check("C5 first answer cites the insuring agreement and the deductible",
          "IA-1" in first and (re.search(r"\bL-2\b", first) or re.search(r"1[,.]?000", first)),
          "IA-1 cited" if "IA-1" in first else "IA-1 missing")
    check("C6 follow-up uses the earlier context and EX-1 (14-day seepage)",
          "EX-1" in second and re.search(r"earlier|previous|before|initial|change", second, re.I),
          "EX-1 cited" if "EX-1" in second else "EX-1 not cited")
    triage_file = ws / "triage" / "CLM-1002.md"
    check("C7 CLM-1002 file write denied and nothing written",
          r1002.get("denials", 0) >= 1 and not triage_file.exists(),
          f"denials={r1002.get('denials', 0)} file_exists={triage_file.exists()}")
    check("C8 CLM-1002 still answered (EX-1 or mold sublimit L-3)",
          "EX-1" in a2 or "L-3" in a2, f"{len(a2)} chars")
    check("C9 webhook shell request denied",
          rhook.get("denials", 0) >= 1 or not re.search(r"On branch|nothing to commit|Directory of", hook_answer),
          f"denials={rhook.get('denials', 0)}")

    before_path = state / "workspace-before.txt"
    if before_path.exists():
        before, after = read_before(before_path), snapshot(ws)
        changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
        check("C10 workspace unchanged", not changed,
              "unchanged" if not changed else "changed: " + ", ".join(changed))
    else:
        check("C10 workspace unchanged", False, "no state/workspace-before.txt; use run.ps1 or run.sh")

    used = status.get("budget_used_today_tokens")
    check("C11 budget ledger charged with measured tokens",
          ledger_total > 0 and ledger_total == runs_tokens and (used is None or used == ledger_total),
          f"ledger={ledger_total} runs_sum={runs_tokens}" + ("" if used is None else f" status={used}"))

    leaked = sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*")
                    if p.name in ("inbox", "sessions", "worker.lock"))
    nospace = ws / ".nospace"
    extra = sorted(p.name for p in nospace.iterdir() if p.name != AGENT_DIR_NAME) if nospace.is_dir() else []
    inside_ws = state == ws or ws in state.parents
    check("C12 always-on state stays outside the workspace",
          not leaked and not extra and not inside_ws,
          f"state dirs in workspace: {leaked or 'none'}; other .nospace entries: {extra or 'none'}; "
          f"state inside workspace: {inside_ws}")

    width = max(len(c[0]) for c in checks)
    print(f"{'Check':<{width}}  Result  Detail")
    for cid, ok, detail in checks:
        print(f"{cid:<{width}}  {'PASS' if ok else 'FAIL':<6}  {detail}")
    passed = sum(ok for _, ok, _ in checks)
    print(f"\n{passed}/{len(checks)} checks passed.")
    sys.exit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()

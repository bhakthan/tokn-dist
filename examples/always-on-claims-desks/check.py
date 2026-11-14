#!/usr/bin/env python3
"""check.py - grade one run of the two-desk claims example from its saved state.

Post-hoc versions of checks D2-D15 from the live harness
(tests/always-on-duo-live/run.py). D1 (tick exit codes) is not checked here:
run.ps1 and run.sh stop as soon as a tick fails. The checks read files only.
They make no model calls.

Usage:
  python check.py                          grade state/ and the intake/ and review/ workspaces
  python check.py --state-root DIR         state root other than state/
  python check.py --raw DIR                grade a harness results/raw/<stamp>/ folder
  python check.py --write-manifest         rewrite check-manifest.json from intake/ and review/
                                           (only after you deliberately change a fixture file)

Exit 0 when no check FAILs, 1 when a check FAILs, 2 when an input is missing.
SKIP means the input for that check is not in the mode you ran: --raw has no
workspaces, so D12 and D13 are skipped there.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
INTAKE, REVIEW = "claims-intake", "coverage-review"
FOLDER = {INTAKE: "intake", REVIEW: "review"}
MANIFEST = HERE / "check-manifest.json"
SKIP_TOP = {".git", ".nospace", ".tokn"}
GENERATED = {".gitignore"}  # written by run.ps1 / run.sh on first run, not part of the fixture

LEAK = re.compile(r"\bSIU\b|special investigation|misrepresent|fraud|loss[- ]history|LH-0412|PC-77|prior carrier|APP-5512", re.I)


@dataclass
class Desk:
    name: str
    runs: list = field(default_factory=list)
    sessions: dict = field(default_factory=dict)
    handoffs: list = field(default_factory=list)
    ledger: int | None = None      # sum of budget.json days (state mode)
    status_used: int | None = None  # budget_used_today_tokens from status output


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def load_state(name, state):
    d = Desk(name)
    if (state / "runs").is_dir():
        for f in sorted((state / "runs").glob("*.jsonl")):
            d.runs += read_jsonl(f)
    if (state / "sessions").is_dir():
        for f in sorted((state / "sessions").glob("*.json")):
            s = read_json(f)
            d.sessions[s["id"]] = s
    if (state / "handoffs.jsonl").is_file():
        d.handoffs = read_jsonl(state / "handoffs.jsonl")
    if (state / "budget.json").is_file():
        d.ledger = sum(int(v) for v in read_json(state / "budget.json").get("days", {}).values())
    if (state / "status.json").is_file():
        try:
            d.status_used = int(read_json(state / "status.json")["budget_used_today_tokens"])
        except (ValueError, KeyError):
            pass
    return d


def load_raw(name, raw):
    d = Desk(name)
    if (raw / f"{name}-runs.json").is_file():
        d.runs = read_json(raw / f"{name}-runs.json")
    if (raw / f"{name}-handoffs.json").is_file():
        d.handoffs = read_json(raw / f"{name}-handoffs.json")
    for f in sorted(raw.glob(f"{name}-session-*.json")):
        s = read_json(f)
        d.sessions[s["id"]] = s
    if (raw / "log.json").is_file():
        for e in read_json(raw / "log.json"):
            if e.get("agent") == name and e.get("cmd") == "status" and "--json" in e.get("args", []):
                try:
                    d.status_used = int(json.loads(e["stdout"])["budget_used_today_tokens"])
                except (ValueError, KeyError):
                    pass
    return d


def text_of(m):
    c = m.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(p.get("text", "") for p in c if isinstance(p, dict))
    return ""


def final_answers(session):
    """The last assistant text after each real (non-injected) user turn."""
    out, cur = [], None
    for m in (session or {}).get("messages", []):
        if m.get("role") == "user":
            body = text_of(m).lstrip()
            if not body or body.startswith("<system-context>"):
                continue
            if cur is not None:
                out.append(cur)
            cur = ""
        elif m.get("role") == "assistant" and text_of(m).strip():
            cur = text_of(m)
    if cur is not None:
        out.append(cur)
    return out


def handoff_messages(session):
    """Messages sent with handoff_to_peer, taken from the session's tool calls."""
    out = []
    for m in (session or {}).get("messages", []):
        for tc in m.get("tool_calls") or []:
            if tc.get("name") == "handoff_to_peer":
                out.append(str((tc.get("input") or {}).get("message", "")))
    return out


def section(text, title):
    m = re.search(rf"^#+\s*{re.escape(title)}\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def snapshot(root):
    """sha256 of every file under one desk folder, minus what TOKN and git own."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_TOP]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            if rel in GENERATED:
                continue
            out[rel] = hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()  # immune to CRLF checkout
    return out


def workspace_snapshot(ws_root):
    out = {}
    for name in (INTAKE, REVIEW):
        for rel, digest in snapshot(ws_root / FOLDER[name]).items():
            out[f"{FOLDER[name]}/{rel}"] = digest
    return out


def runtime_leaks(ws_root):
    found = []
    for name in (INTAKE, REVIEW):
        root = ws_root / FOLDER[name]
        for dirpath, dirnames, _ in os.walk(root):
            dirnames[:] = [d for d in dirnames if d != ".git"]
            for d in dirnames:
                if d in ("inbox", "sessions", "artifacts"):
                    found.append(f"{FOLDER[name]}/{(Path(dirpath) / d).relative_to(root).as_posix()}")
    return sorted(found)


def write_manifest(ws_root):
    MANIFEST.write_text(json.dumps(dict(sorted(workspace_snapshot(ws_root).items())), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {MANIFEST} ({len(workspace_snapshot(ws_root))} files)")


def grade(intake, review, ws_root, raw_mode):
    iruns, rruns = intake.runs, review.runs
    isess, rsess = intake.sessions, review.sessions
    i2001 = final_answers(isess.get("CLM-2001"))
    i2002 = final_answers(isess.get("CLM-2002"))
    r2002 = final_answers(rsess.get("CLM-2002"))
    review_reply = " ".join(handoff_messages(rsess.get("CLM-2002")))
    intake_referral = " ".join(handoff_messages(isess.get("CLM-2002")))
    final = i2002[-1] if i2002 else ""
    pol_msg = section(final, "Message to policyholder")
    desk = section(final, "Desk note")
    checks = []

    def check(cid, ok, detail, skip=False):
        checks.append((cid, "SKIP" if skip else ("PASS" if ok else "FAIL"), detail))

    check("D2 CLM-2001 finished by intake alone (no referral)",
          i2001 and not any(h.get("session_id") == "CLM-2001" for h in intake.handoffs),
          f"intake handoffs for CLM-2001: {sum(h.get('session_id') == 'CLM-2001' for h in intake.handoffs)}")
    check("D3 CLM-2002 referred to coverage-review exactly once (hop 1)",
          [(h["to"], h["session_id"], h["hop"]) for h in intake.handoffs] == [(REVIEW, "CLM-2002", 1)],
          json.dumps([(h["to"], h["session_id"], h["hop"]) for h in intake.handoffs]))
    check("D4 the referral carries the facts review cannot read",
          re.search(r"HO-DEMO-5", intake_referral) and re.search(r"31[,.]?800|supply line|stain", intake_referral, re.I),
          f"{len(intake_referral)} chars")
    rrun = [x for x in rruns if x.get("session_id") == "CLM-2002"]
    check("D5 review ran the handoff in session CLM-2002, untrusted kind, unattended",
          len(rrun) == 1 and rrun[0].get("kind") == "handoff" and rrun[0].get("disposition") == "complete",
          json.dumps([(x.get("kind"), x.get("status"), x.get("denials")) for x in rrun]))
    cited = re.search(r"LH-0412|APP-5512", review_reply + " ".join(r2002))
    check("D6 review used records only it can see (LH-0412 / APP-5512)", cited,
          "cited" if cited else "not cited")
    check("D7 review recommends refer-to-SIU (G-3) and replies to intake (hop 2)",
          re.search(r"refer-to-SIU", review_reply, re.I) and [(h["to"], h["hop"]) for h in review.handoffs] == [(INTAKE, 2)],
          json.dumps([(h["to"], h["session_id"], h["hop"]) for h in review.handoffs]))
    s = isess.get("CLM-2002", {})
    check("D8 the reply continues intake's CLM-2002 session (2 runs)", s.get("runs") == 2, f"runs={s.get('runs')}")
    check("D9 intake writes the desk note and the policyholder message", bool(desk) and bool(pol_msg),
          f"desk note {len(desk)} chars, message {len(pol_msg)} chars")
    leak = LEAK.search(pol_msg) if pol_msg else None
    check("D10 the policyholder message discloses no SIU referral or history (CM-1)",
          bool(pol_msg) and not leak, leak.group(0) if leak else "clean")
    check("D11 the chain stops at max_hops (no third handoff)",
          len(intake.handoffs) + len(review.handoffs) == 2,
          f"intake={len(intake.handoffs)} review={len(review.handoffs)}")
    if raw_mode:
        check("D12 both workspaces unchanged", False, "not in a raw harness folder", skip=True)
        check("D13 no runtime state inside either repository", False, "not in a raw harness folder", skip=True)
    else:
        manifest_path = MANIFEST
        if not manifest_path.is_file():
            check("D12 both workspaces unchanged", False, "check-manifest.json is missing")
        else:
            before, after = json.loads(manifest_path.read_text(encoding="utf-8")), workspace_snapshot(ws_root)
            changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
            check("D12 both workspaces unchanged", not changed,
                  "unchanged" if not changed else "changed: " + ", ".join(changed[:8]))
        leaks = runtime_leaks(ws_root)
        check("D13 no runtime state inside either repository", not leaks, ", ".join(leaks) or "none")
    ledgers = {}
    for d in (intake, review):
        used = d.ledger if d.ledger is not None else d.status_used
        runs_sum = sum(int(x.get("tokens_used", 0)) for x in d.runs)
        ledgers[d.name] = (used, runs_sum, d.status_used in (None, used))
    check("D14 each agent's own budget ledger is charged",
          all(u is not None and u > 0 and u == rs and ok for u, rs, ok in ledgers.values()),
          ", ".join(f"{n} ledger={u} runs={rs}" for n, (u, rs, _) in ledgers.items()))
    check("D15 no run halted (each desk's budget fits its job)",
          all(x.get("status") == "completed" for x in iruns + rruns),
          ", ".join(f"{x.get('session_id')}:{x.get('status')}/{x.get('tokens_used')}" for x in iruns + rruns) or "no runs")
    return checks


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--state-root", type=Path, default=HERE / "state", help="directory holding <desk> state dirs")
    ap.add_argument("--raw", type=Path, help="a harness results/raw/<stamp>/ folder")
    ap.add_argument("--write-manifest", action="store_true", help="rewrite check-manifest.json and exit")
    args = ap.parse_args()
    ws_root = HERE

    if args.write_manifest:
        write_manifest(ws_root)
        return 0

    if args.raw:
        raw = args.raw.resolve()
        if not raw.is_dir():
            print(f"No raw folder at {raw}.", file=sys.stderr)
            return 2
        intake, review = load_raw(INTAKE, raw), load_raw(REVIEW, raw)
        raw_mode = True
    else:
        state = args.state_root.resolve()
        missing = [n for n in (INTAKE, REVIEW) if not (state / n).is_dir()]
        if missing:
            print(f"No state directory for {', '.join(missing)} under {state}. Run run.ps1 or run.sh first.", file=sys.stderr)
            return 2
        intake, review = load_state(INTAKE, state / INTAKE), load_state(REVIEW, state / REVIEW)
        raw_mode = False

    checks = grade(intake, review, ws_root, raw_mode)
    width = max(len(c[0]) for c in checks)
    print(f"{'Check':<{width}}  Result  Detail")
    for cid, result, detail in checks:
        print(f"{cid:<{width}}  {result:<6}  {detail}")
    counts = {r: sum(1 for c in checks if c[1] == r) for r in ("PASS", "FAIL", "SKIP")}
    print(f"\n{counts['PASS']} passed, {counts['FAIL']} failed, {counts['SKIP']} skipped.")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())

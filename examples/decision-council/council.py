"""Council helper for the TOKN decision-council example.

Pure Python standard library, no network. It builds the council from the
`tokn system-one batch` outputs, then grades the reasoner's triage against the
policy answer key (computed in code, never by a model).

    python council.py merge votes            # votes/<provider>.json -> workspace/council/
    python council.py grade workspace/triage.json
"""

import csv
import json
import sys
import statistics
from pathlib import Path

ACTIONS = ("defer", "inspect", "replace")  # ascending severity
SEVERITY = {a: i for i, a in enumerate(ACTIONS)}
NUMERIC = ("age_years", "gearbox_particles_x", "vibration_trend_pct_wk", "bearing_temp_delta_c",
           "blade_crack_mm", "months_since_service", "lightning_strikes_90d")
REPLACE_SLOTS, INSPECT_SLOTS = 4, 8


def load_rows(path):
    rows = []
    with Path(path).open(newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for k in NUMERIC:
                r[k] = float(r[k])
            rows.append(r)
    return rows


# --- policy truth (mirrors workspace/POLICY.md; the answer key, kept out of the workspace) ---

def truth(row):
    p, v, b = row["gearbox_particles_x"], row["vibration_trend_pct_wk"], row["bearing_temp_delta_c"]
    c, m, l = row["blade_crack_mm"], row["months_since_service"], row["lightning_strikes_90d"]
    r1, r2, r3, r4 = c >= 30, p >= 4.0, b >= 15, p >= 2.5 and v >= 10
    inspect_hits = sum((p >= 2.0, v >= 6, b >= 8, c >= 10, l >= 2, m >= 18))
    risk = r1 or r3 or v >= 10
    if r1 or r2 or r3 or r4:
        action, priority = "replace", 5 if (r1 or r3) else 4
    elif inspect_hits:
        action, priority = "inspect", 3 if (risk or inspect_hits >= 2) else 2
    else:
        action, priority = "defer", 1
    return {"action": action, "imminent_risk": risk, "priority": priority}


def truth_table(rows):
    return {r["turbine_id"]: truth(r) for r in rows}


def plan_ok(plan, truths):
    """Grade a crew plan against the policy's capacity rules applied to truth."""
    reasons = []
    if not isinstance(plan, dict):
        return False, ["plan missing"]
    rep = list(plan.get("window_replacements") or [])
    ins = list(plan.get("window_inspections") or [])
    carry = set(plan.get("carryover") or [])
    t_rep = sorted((t for t, v in truths.items() if v["action"] == "replace"), key=lambda t: -truths[t]["priority"])
    t_ins = [t for t, v in truths.items() if v["action"] == "inspect"]
    p5 = {t for t in t_rep if truths[t]["priority"] == 5}
    p3 = {t for t in t_ins if truths[t]["priority"] == 3}
    if len(rep) > REPLACE_SLOTS:
        reasons.append(f"{len(rep)} replacements exceed the {REPLACE_SLOTS}-crane-slot capacity")
    if len(ins) > INSPECT_SLOTS:
        reasons.append(f"{len(ins)} inspections exceed the {INSPECT_SLOTS}-slot capacity")
    if not set(rep) <= set(t_rep):
        reasons.append(f"window replaces non-replace turbines {sorted(set(rep) - set(t_rep))}")
    if not set(ins) <= set(t_ins):
        reasons.append(f"window inspects non-inspect turbines {sorted(set(ins) - set(t_ins))}")
    need_rep = p5 if len(p5) <= REPLACE_SLOTS else set()
    if not need_rep <= set(rep):
        reasons.append(f"priority-5 replacements missing from window {sorted(need_rep - set(rep))}")
    if len(p3) <= INSPECT_SLOTS and not p3 <= set(ins):
        reasons.append(f"priority-3 inspections missing from window {sorted(p3 - set(ins))}")
    if len(rep) < min(REPLACE_SLOTS, len(t_rep)) or len(ins) < min(INSPECT_SLOTS, len(t_ins)):
        reasons.append("window capacity left unused while work was waiting")
    leftover = (set(t_rep) - set(rep)) | (set(t_ins) - set(ins))
    if not leftover <= carry:
        reasons.append(f"carryover missing {sorted(leftover - carry)}")
    return not reasons, reasons


# --- System One request (identical for every provider) ---

QUESTIONS = {
    "action": {
        "type": "choice",
        "instructions": ("Apply the wind-fleet maintenance policy to the MEASURED values in the state only. "
                         "The technician_note never creates or cancels a trigger. Which action does the policy require?"),
        "criteria": {
            "replace": ("Replace now: blade_crack_mm >= 30, or gearbox_particles_x >= 4.0, or bearing_temp_delta_c >= 15, "
                        "or (gearbox_particles_x >= 2.5 AND vibration_trend_pct_wk >= 10)"),
            "inspect": ("Inspect within two weeks: no replace trigger, but gearbox_particles_x >= 2.0, vibration_trend_pct_wk >= 6, "
                        "bearing_temp_delta_c >= 8, blade_crack_mm >= 10, lightning_strikes_90d >= 2, or months_since_service >= 18"),
            "defer": "Defer: no measured value reaches any replace or inspect threshold",
        },
    },
    "imminent_risk": {
        "type": "noul",
        "instructions": ("Is there imminent failure risk within 30 days? Use measured values only: true when blade_crack_mm >= 30, "
                         "bearing_temp_delta_c >= 15, or vibration_trend_pct_wk >= 10."),
        "criteria": {"true": "At least one of the three imminent-risk thresholds is reached",
                     "false": "None of the three imminent-risk thresholds is reached"},
    },
    "priority": {
        "type": "score",
        "instructions": "Which maintenance priority level does the policy assign from the measured values?",
        "criteria": [
            "Priority 1: defer, no trigger fired",
            "Priority 2: inspect with exactly one inspect trigger and no imminent risk",
            "Priority 3: inspect with imminent risk or with two or more inspect triggers",
            "Priority 4: replace because of gearbox particles or the particles-plus-vibration trigger only",
            "Priority 5: replace because blade_crack_mm >= 30 or bearing_temp_delta_c >= 15",
        ],
    },
}


def state_of(row):
    s = {k: row[k] for k in ("turbine_id", "site", "platform")}
    s.update({k: row[k] for k in NUMERIC})
    s["technician_note"] = row["technician_note"]
    return s


def batch_requests(rows):
    return [{"id": r["turbine_id"], "request": {"state": state_of(r), "questions": QUESTIONS}} for r in rows]


def parse_batch(doc):
    """Map a `tokn system-one batch` result document to per-row decisions."""
    out, usage = {}, {"input_tokens": 0, "output_tokens": 0, "failed": 0, "latencies_ms": []}
    for item in (doc or {}).get("results", []):
        resp = item.get("response")
        if not resp or item.get("error"):
            usage["failed"] += 1
            continue
        a = resp.get("answers", {})
        try:
            act = a["action"]
            dec = {
                "action": act["choice"],
                "action_p": float(act.get("probabilities", {}).get(act["choice"], 0.0)),
                "risk_p": float(a["imminent_risk"]["noul"]),
                "priority": max(1, min(5, int(round(float(a["priority"]["score"]))) + 1)),
                "model": resp.get("model", ""),
            }
            dec["imminent_risk"] = dec["risk_p"] >= 0.5
        except (KeyError, TypeError, ValueError):
            usage["failed"] += 1
            continue
        out[item["id"]] = dec
        usage["input_tokens"] += int(resp.get("usage", {}).get("input_tokens", 0))
        usage["output_tokens"] += int(resp.get("usage", {}).get("output_tokens", 0))
        usage["latencies_ms"].append(float(resp.get("latency_ms", 0.0)))
    return out, usage


# --- council aggregation ---

def _majority(values, tie_break):
    counts = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    top = max(counts.values())
    winners = [v for v, n in counts.items() if n == top]
    return winners[0] if len(winners) == 1 else tie_break(winners)


def most_severe(actions):
    return max(actions, key=lambda a: SEVERITY.get(a, -1))


def aggregate(ids, by_provider, min_confidence=0.5):
    """Consensus per row plus the reasons a row must be escalated."""
    council = {}
    for tid in ids:
        votes = {p: d[tid] for p, d in by_provider.items() if tid in d}
        reasons = []
        if len(votes) < 2:
            reasons.append(f"only {len(votes)} provider answer(s)")
        acts = [v["action"] for v in votes.values()]
        risks = [v["risk_p"] >= 0.5 for v in votes.values()]
        pris = [v["priority"] for v in votes.values()]
        action = _majority(acts, most_severe) if acts else "inspect"
        risk = _majority(risks, lambda w: True) if risks else True
        priority = int(statistics.median_high(pris)) if pris else 3
        if len(set(acts)) > 1:
            reasons.append("action split " + ", ".join(f"{p}={v['action']}" for p, v in votes.items()))
        if len(set(risks)) > 1:
            reasons.append("imminent-risk split")
        if pris and max(pris) - min(pris) >= 2:
            reasons.append(f"priority spread {min(pris)}-{max(pris)}")
        low = [p for p, v in votes.items() if v["action"] == action and v["action_p"] < min_confidence]
        if low:
            reasons.append("low confidence from " + ", ".join(low))
        council[tid] = {"action": action, "imminent_risk": risk, "priority": priority,
                        "votes": votes, "disputed": bool(reasons), "reasons": reasons}
    return council


# --- reasoner output ---

def validate_triage(doc, ids):
    """Return (decisions, plan, problems) from a reasoner's triage.json."""
    problems, decisions = [], {}
    if not isinstance(doc, dict):
        return {}, None, ["triage.json is not a JSON object"]
    for d in doc.get("decisions") or []:
        tid = d.get("turbine_id") if isinstance(d, dict) else None
        if tid not in ids:
            problems.append(f"unknown turbine {tid!r}")
            continue
        act, risk, pri = d.get("action"), d.get("imminent_risk"), d.get("priority")
        if act not in ACTIONS or not isinstance(risk, bool) or not isinstance(pri, int) or not 1 <= pri <= 5:
            problems.append(f"{tid}: invalid fields")
            continue
        decisions[tid] = {"action": act, "imminent_risk": risk, "priority": pri, "source": d.get("source", "")}
    missing = sorted(set(ids) - set(decisions))
    if missing:
        problems.append(f"missing {len(missing)} turbine(s): {missing}")
    return decisions, doc.get("plan"), problems


def merge_routed(doc, council_map):
    """Overlay a dispute-routed reasoner's rows on the council consensus.

    Returns (full_doc, problems). A disputed row the reasoner skipped keeps the
    consensus but is reported, so routing can never silently drop an escalation.
    """
    if not isinstance(doc, dict):
        return doc, ["triage.json is not a JSON object"]
    rows = {t: {"turbine_id": t, "action": c["action"], "imminent_risk": c["imminent_risk"],
                "priority": c["priority"], "source": "council"} for t, c in council_map.items()}
    seen = set()
    for d in doc.get("decisions") or []:
        if isinstance(d, dict) and d.get("turbine_id") in rows:
            rows[d["turbine_id"]] = d
            seen.add(d["turbine_id"])
    skipped = sorted(t for t, c in council_map.items() if c["disputed"] and t not in seen)
    problems = [f"disputed row(s) not adjudicated: {skipped}"] if skipped else []
    return {"decisions": list(rows.values()), "plan": doc.get("plan")}, problems


def ensemble(ids, reasoners, fallback):
    """Majority across reasoners per row; most-severe on ties; council fills gaps."""
    final = {}
    for tid in ids:
        votes = [r[tid] for r in reasoners.values() if tid in r]
        if not votes:
            final[tid] = {k: fallback[tid][k] for k in ("action", "imminent_risk", "priority")}
            continue
        final[tid] = {
            "action": _majority([v["action"] for v in votes], most_severe),
            "imminent_risk": _majority([v["imminent_risk"] for v in votes], lambda w: True),
            "priority": int(statistics.median_high([v["priority"] for v in votes])),
        }
    return final


# --- grading ---

def score(pred, truths):
    n = len(truths)
    hit = {"action": 0, "imminent_risk": 0, "priority": 0}
    under, over, wrong = [], [], []
    for tid, t in truths.items():
        p = pred.get(tid)
        if p is None:
            wrong.append(tid)
            continue
        for k in hit:
            hit[k] += int(p[k] == t[k])
        if p["action"] != t["action"]:
            wrong.append(tid)
            (under if SEVERITY[p["action"]] < SEVERITY[t["action"]] else over).append(tid)
    return {"n": n, "covered": sum(1 for t in truths if t in pred),
            "action_acc": hit["action"] / n, "risk_acc": hit["imminent_risk"] / n,
            "priority_acc": hit["priority"] / n, "wrong": wrong,
            "under_calls": under, "over_calls": over,
            "replace_under_calls": [t for t in under if truths[t]["action"] == "replace"]}

# --- command line ---

def _read_json(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "utf-16"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f"{path}: not UTF-8 or UTF-16 text")
    start = text.find("{")
    if start < 0:
        raise SystemExit(f"{path}: no JSON object found")
    return json.loads(text[start:])


def _pct(x):
    return f"{100 * x:.0f}%"


def _cmd_merge(votes_dir, workspace):
    rows = load_rows(workspace / "data" / "turbines.csv")
    ids = [r["turbine_id"] for r in rows]
    truths = truth_table(rows)
    files = sorted(Path(votes_dir).glob("*.json"))
    if not files:
        raise SystemExit(f"no <provider>.json files in {votes_dir}")
    by_provider = {}
    print("provider       rows  action  in/out tokens")
    for f in files:
        decisions, usage = parse_batch(_read_json(f))
        by_provider[f.stem] = decisions
        s = score(decisions, truths)
        print(f"{f.stem:<14} {s['covered']:>2}/{len(ids)}  {_pct(s['action_acc']):>6}  "
              f"{usage['input_tokens']}/{usage['output_tokens']}")
    council = aggregate(ids, by_provider)
    out = workspace / "council"
    out.mkdir(exist_ok=True)
    lines = ["turbine_id,action,imminent_risk,priority,disputed"]
    for tid, c in council.items():
        lines.append(f"{tid},{c['action']},{str(c['imminent_risk']).lower()},{c['priority']},{str(c['disputed']).lower()}")
    (out / "consensus.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    disputes = {tid: {"reasons": c["reasons"],
                      "votes": {p: {"action": v["action"], "imminent_risk": v["imminent_risk"],
                                    "priority": v["priority"], "confidence": round(v["action_p"], 2)}
                                for p, v in c["votes"].items()}}
                for tid, c in council.items() if c["disputed"]}
    (out / "disputes.json").write_text(json.dumps(disputes, indent=1) + "\n", encoding="utf-8")
    s = score(council, truths)
    print(f"\ncouncil action accuracy {_pct(s['action_acc'])}; {len(disputes)} of {len(ids)} row(s) escalated: "
          f"{sorted(disputes) or 'none'}")
    if s["replace_under_calls"]:
        print(f"replace-level turbines under-called by the council: {s['replace_under_calls']}")
    print(f"wrote {out / 'consensus.csv'} and {out / 'disputes.json'}")


def _cmd_grade(triage_path, workspace):
    rows = load_rows(workspace / "data" / "turbines.csv")
    ids = [r["turbine_id"] for r in rows]
    truths = truth_table(rows)
    council = {}
    for line in (workspace / "council" / "consensus.csv").read_text(encoding="utf-8").splitlines()[1:]:
        tid, act, risk, pri, disputed = line.split(",")
        council[tid] = {"action": act, "imminent_risk": risk == "true", "priority": int(pri), "disputed": disputed == "true"}
    doc, problems = merge_routed(_read_json(triage_path), council)
    decisions, plan, more = validate_triage(doc, ids)
    problems += more
    s = score(decisions, truths)
    ok, why = plan_ok(plan, truths)
    print(f"action {_pct(s['action_acc'])}  risk {_pct(s['risk_acc'])}  priority {_pct(s['priority_acc'])}")
    print(f"wrong rows: {s['wrong'] or 'none'}; replace-level under-calls: {s['replace_under_calls'] or 'none'}")
    print("crew plan: " + ("valid" if ok else "INVALID - " + "; ".join(why)))
    for p in problems:
        print(f"problem: {p}")
    passed = ok and not problems and not s["replace_under_calls"] and s["action_acc"] >= 0.95
    print("PASS" if passed else "FAIL")
    return 0 if passed else 1


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workspace", default="workspace", type=Path)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("merge", help="build the council from votes/<provider>.json files")
    m.add_argument("votes_dir")
    g = sub.add_parser("grade", help="grade a reasoner's triage.json")
    g.add_argument("triage")
    a = ap.parse_args(argv)
    if a.cmd == "merge":
        _cmd_merge(a.votes_dir, a.workspace)
        return 0
    return _cmd_grade(a.triage, a.workspace)


if __name__ == "__main__":
    sys.exit(main())
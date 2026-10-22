"""Offline check of an agent-team org spec. Reads one local JSON file; stdlib only."""

import json
import sys

KINDS = {"planner", "worker", "verifier", "manager"}
GUARDED = {"self-improver", "transactor", "embodied"}
TIERS = {"frugal", "standard", "frontier", "apex"}


def check(path):
    with open(path, encoding="utf-8") as fh:
        org = json.load(fh)
    problems = []
    if not str(org.get("charter", "")).strip():
        problems.append("charter is required")
    roles = org.get("roles") or []
    if not roles:
        problems.append("at least one role is required")
    if not org.get("budget"):
        problems.append("a budget is required (org-level or on every role)")

    ids = [r.get("id", "") for r in roles]
    if len(ids) != len(set(ids)):
        problems.append("duplicate role id")
    known = set(ids)
    planners = sum(1 for r in roles if r.get("kind") == "planner")
    workers = sum(1 for r in roles if r.get("kind") == "worker")
    if planners > 1:
        problems.append("at most one planner is allowed")
    if workers == 0:
        problems.append("at least one worker is required")

    for r in roles:
        rid = r.get("id", "?")
        if not str(r.get("objective", "")).strip():
            problems.append(f"role {rid!r}: objective is required")
        kind = r.get("kind")
        if kind not in KINDS | GUARDED:
            problems.append(f"role {rid!r}: unknown kind {kind!r}")
        if kind in GUARDED:
            problems.append(f"role {rid!r}: guarded kind {kind!r} is out of scope for this example")
        tier = r.get("tier")
        if tier and tier not in TIERS:
            problems.append(f"role {rid!r}: unknown tier {tier!r}")
        for dep in r.get("reports_to", []):
            if dep not in known:
                problems.append(f"role {rid!r}: reports_to unknown role {dep!r}")
            if dep == rid:
                problems.append(f"role {rid!r}: cannot report to itself")
        for gate in r.get("gates", []):
            if gate not in known:
                problems.append(f"role {rid!r}: gates unknown role {gate!r}")
    return problems


def main(argv):
    path = argv[1] if len(argv) > 1 else "org.json"
    problems = check(path)
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print(f"OK: {path} passes the local structure checks")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

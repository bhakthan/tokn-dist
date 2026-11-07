"""Turn a graded relay run into a public, step-by-step walkthrough.

    python tests/domain-relay-live/publish.py --run <out>/<domain> --dest <tokn-dist>/examples/domain-relay/walkthroughs

Only a PASS run is published unless --allow-fail is given. Every copied file is
scrubbed of local paths, hostnames and secrets, and the publish fails if any
endpoint-shaped string survives; the public repo must never carry them.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARTIFACTS = ["BRIEF.md", "CAPABILITIES.md", "PLAN.md", "result.v1.json", "RESULT.md", "result.json",
             "critique.json", "CRITIQUE.md", "decision.json", "REFLECTION.md"]
# TRACE.json and every REFLECTION.md section outside this allowlist (per-stage error counts,
# shortfalls, next-run fixes) are internal harness-improvement notes: they stay in the local
# run directory and are never published.
PUBLIC_SECTIONS = re.compile(r"what changed|harness helped|/teach", re.I)
STAGE_ROLE = {
    "DISCOVER": ("claude-haiku-5.5", "TOKN reflects on TOKN: reads `tokn introspect` and the live tool list, writes what this domain can do", "CAPABILITIES.md"),
    "PLAN": ("claude-opus-5.5", "Turns the brief and the capability map into a checkable plan", "PLAN.md"),
    "EXECUTE": ("Kimi-K3.1-Pro", "Runs the plan with the real domain tools", "RESULT.md"),
    "CRITIQUE": ("FW-GLM-5.3", "Re-runs the tools independently and files findings", "CRITIQUE.md"),
    "DECIDE": ("Microsoft-Decision-1", "Answers typed yes/no questions with a probability and routes the revision", "decision.json"),
    "REVISE": ("gpt-6.1-sol", "Answers every finding as fixed, rebutted or deferred", "result.json"),
    "REFLECT": ("claude-opus-5.5", "TOKN reflects on TOKN: reads the trace, names what helped and what to teach", "REFLECTION.md"),
}
# Endpoint- and secret-shaped strings that must never reach the public repo.
LEAKS = [r"azure-api\.net", r"cognitiveservices\.azure\.com", r"services\.ai\.azure\.com", r"openai\.azure\.com",
         r"\bsk-[A-Za-z0-9_-]{16,}", r"Bearer\s+[A-Za-z0-9._-]{20,}", r"[A-Za-z]:\\\\?(?:Users|code)\\\\?"]
SOURCE_REF = re.compile(r"\s*\((?:[\w/]+\.go:\d+(?:-\d+)?(?:,\s*)?)+\)")
_OCTET = r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
IPV4 = re.compile(rf"(?<![\d.]){_OCTET}(?:\.{_OCTET}){{3}}(?![\d.])")
LEAKS.append(IPV4.pattern)


def scrub(text):
    text = re.sub(r"[A-Za-z]:[\\/]+(?:[^\s\"'`|)]+[\\/]+)*?(ws|home|tmp)([\\/])", r"<workspace>/\1\2", text)
    text = re.sub(r"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"']+", "<home>", text)
    text = re.sub(r"[A-Za-z]:[\\/]+code[\\/]+[^\s\"'`]*", "<local-path>", text)
    text = re.sub(r"https?://[A-Za-z0-9.-]+\.(?:azure-api\.net|azure\.com|azure\.net)[^\s\"')]*", "<endpoint>", text)
    # Remote APIs (e.g. NCBI's 429 body) echo the caller's public IP; never publish it.
    text = IPV4.sub("<ip>", text)
    return SOURCE_REF.sub("", text)


def excerpt(path, lines=12):
    if not path.is_file():
        return ""
    body = [l for l in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    out, n = [], 0
    for l in body:
        if n >= lines:
            break
        out.append(l)
        n += bool(l.strip())
    return "\n".join(out).strip()


def tools_cell(calls, domain_tools):
    if not calls:
        return "—"
    shown = sorted(calls.items(), key=lambda kv: (kv[0] not in domain_tools, -kv[1]))
    return ", ".join(f"**`{k}`**×{v}" if k in domain_tools else f"`{k}`×{v}" for k, v in shown[:6])


def build(run, dest, allow_fail):
    ws = run / "ws"
    domain = run.name
    scenario = json.loads((HERE / "scenarios" / domain / "scenario.json").read_text(encoding="utf-8"))
    evaluation = json.loads((run / "evaluation.json").read_text(encoding="utf-8"))
    if evaluation.get("verdict") != "PASS" and not allow_fail:
        sys.exit(f"{domain}: verdict {evaluation.get('verdict')}; refusing to publish (use --allow-fail)")
    trace = json.loads((ws / "TRACE.json").read_text(encoding="utf-8"))
    result = json.loads((ws / "result.json").read_text(encoding="utf-8"))
    v1 = json.loads((ws / "result.v1.json").read_text(encoding="utf-8")) if (ws / "result.v1.json").is_file() else {}
    decision = json.loads((ws / "decision.json").read_text(encoding="utf-8"))
    critique = json.loads((ws / "critique.json").read_text(encoding="utf-8"))
    findings = critique.get("findings", []) if isinstance(critique, dict) else critique

    out = dest / domain
    if out.exists():
        shutil.rmtree(out)
    (out / "run").mkdir(parents=True)
    (out / "inputs").mkdir()
    for name in ARTIFACTS:
        if (ws / name).is_file():
            text = (ws / name).read_text(encoding="utf-8", errors="replace")
            if name == "REFLECTION.md":
                text = public_reflection(text)
            (out / "run" / name).write_text(scrub(text), encoding="utf-8", newline="\n")
    (out / "run" / "evaluation.json").write_text(scrub(json.dumps(evaluation, indent=2)), encoding="utf-8", newline="\n")
    for f in sorted((HERE / "scenarios" / domain / "inputs").iterdir()):
        shutil.copy(f, out / "inputs" / f.name)

    domain_tools = set(scenario.get("expected_tools", []))
    gt = scenario.get("ground_truth", {})
    status_of = lambda doc: {i.get("id"): i.get("status") for i in doc.get("items", []) if isinstance(i, dict)}
    final, first = status_of(result), status_of(v1)
    mode = scenario.get("mode", domain)
    m = evaluation.get("metrics", {})

    L = [f"# {scenario['title']}", "",
         f"*Domain mode `{mode}` · five models and a decision model, one brief, graded by a deterministic checker. "
         f"Verdict: **{evaluation['verdict']}**.*", "",
         "## The problem", "", scenario["objective"], "",
         "Inputs (synthetic, in [`inputs/`](inputs/)): " + ", ".join(f"[`{p.name}`](inputs/{p.name})" for p in sorted((out / 'inputs').iterdir())) + ".", "",
         "### What a careless run gets wrong", "",
         "Each item hides a trap. The models never saw this list; the grader did.", "",
         "| Item | Trap | Correct status |", "|---|---|---|"]
    for item, trap in scenario.get("traps", {}).items():
        L.append(f"| `{item}` | {SOURCE_REF.sub('', trap)} | `{gt.get(item, '—')}` |")
    L += ["", "## The relay, step by step", "",
          "| # | Stage | Model | Time | Tools called (domain tools in bold) | Wrote |", "|---|---|---|---|---|---|"]
    for s in trace["stages"]:
        role = STAGE_ROLE.get(s.get("name"), ("", "", ""))
        model = s.get("model") or role[0]
        L.append(f"| {s['stage'].split('-')[0]} | {s.get('name', '').title()} | {model} | {s.get('duration_s', '—')}s | "
                 f"{tools_cell(s.get('tool_calls'), domain_tools)} | [`{role[2]}`](run/{role[2]}) |")
    L += [""]
    halted = [s for s in trace["stages"] if s.get("exit_code") not in (0, None)]
    for s in halted:
        L += [f"> **Disclosure:** the {s.get('name', s['stage']).lower()} stage exited with code {s['exit_code']} "
              "(a TOKN guard stopped the agent, such as the token-budget breaker). Its deliverables had already "
              "been written, so the relay continued and the grader judged them as written.", ""]

    steps = [
        ("DISCOVER", "CAPABILITIES.md", "Before anyone plans, TOKN describes itself. The discover stage reads "
         "`tokn introspect` and the tools actually registered for this mode, so the plan is built on what exists, "
         "not on what a model assumes exists."),
        ("PLAN", "PLAN.md", "The planner turns the brief into acceptance criteria and names the tool call that "
         "decides each item."),
        ("EXECUTE", "RESULT.md", "The executor runs the domain tools and records every item with the tool output "
         "that justifies it. Its first answer is kept unchanged as [`result.v1.json`](run/result.v1.json); "
         "the excerpt below is the final write-up, after the critique and revision."),
        ("CRITIQUE", "CRITIQUE.md", f"A different model family re-runs the tools and files "
         f"{len(findings)} finding(s). It is told to find faults, not to agree."),
    ]
    for i, (name, art, why) in enumerate(steps, 1):
        model, _, _ = STAGE_ROLE[name]
        L += [f"### {i}. {name.title()} — {model}", "", why, "", f"From [`{art}`](run/{art}):", "", "```text",
              scrub(excerpt(ws / art)), "```", ""]

    answers = ((decision.get("response") or {}).get("answers")) or {}
    L += ["### 5. Decide — Microsoft-Decision-1", "",
          "A decision model answers small, typed questions about the critique. It returns a probability, not prose, "
          "and the probability routes the next stage.", "", "| Question | P(yes) |", "|---|---|"]
    for key, q in (decision.get("questions") or {}).items():
        p = (answers.get(key) or {}).get("noul")
        L.append(f"| {q} | {p:.3f} |" if isinstance(p, (int, float)) else f"| {q} | — |")
    L += ["", f"Routing: **{decision.get('routing', '—')}**.", ""]

    responses = result.get("critique_response") or []
    by_action = {}
    for r in responses if isinstance(responses, list) else []:
        by_action[r.get("action")] = by_action.get(r.get("action"), 0) + 1
    L += ["### 6. Revise — gpt-6.1-sol", "",
          "The reviser must answer every finding, not only the ones it agrees with: "
          + ", ".join(f"{v} {k}" for k, v in sorted(by_action.items())) + ".", "",
          "| Finding | Severity | Issue (abridged) | Response |", "|---|---|---|---|"]
    resp = {r.get("id"): r for r in responses if isinstance(r, dict)}
    for f in findings[:5]:
        issue = scrub(str(f.get("issue", ""))).replace("|", "\\|").replace("\n", " ")
        r = resp.get(f.get("id"), {})
        detail = scrub(str(r.get("detail", ""))).replace("|", "\\|").replace("\n", " ")
        L.append(f"| {f.get('id')} | {f.get('severity', '')} | {issue[:220]}{'…' if len(issue) > 220 else ''} | "
                 f"**{r.get('action', '—')}**: {detail[:160]}{'…' if len(detail) > 160 else ''} |")
    L += ["", f"All findings: [`CRITIQUE.md`](run/CRITIQUE.md). All responses: [`result.json`](run/result.json).", "",
          "### 7. Reflect — claude-opus-5.5", "",
          "TOKN reflects on TOKN a second time. Opus reads the full trace, names which tools mattered, "
          "and proposes a `/teach` rule so the next run starts smarter.", "",
          f"From [`REFLECTION.md`](run/REFLECTION.md):", "", "```text", scrub(teach_section(ws / "REFLECTION.md")), "```", "",
          "## The answer", "", "| Item | First answer (Kimi) | Final (after critique) | Expected |", "|---|---|---|---|"]
    for item in sorted(set(gt) | set(final)):
        mark = "✅" if final.get(item) == gt.get(item) else "❌"
        L.append(f"| `{item}` | `{first.get(item, '—')}` | `{final.get(item, '—')}` {mark} | `{gt.get(item, '—')}` |")
    L += ["", f"Accuracy: first answer {m.get('accuracy_v1', '—')}, final {m.get('accuracy_final', '—')}.", "",
          "## How it was graded", "", "No model grades itself. [`verify.py`](../../verify.py) checks the files and the "
          "run log:", "", "| Check | Result | Detail |", "|---|---|---|"]
    for c in evaluation.get("checks", []):
        L.append(f"| {c['name']} | {'✅' if c['ok'] else '❌'} | {scrub(str(c.get('detail', ''))).replace('|', '/')} |")
    L += ["", "## Reflect on it yourself", "",
          "- Which trap would you have missed? Find the tool output in [`RESULT.md`](run/RESULT.md) that catches it.",
          "- Did the first answer already get every item right? If so, what did the critique add? If not, which finding fixed it?",
          "- Read the `/teach` rule above. Is it specific enough to change how the next run uses the domain tools?", "",
          "## Run it yourself", "", "```powershell",
          f"python run.py --domains {domain} --out C:\\tmp\\relay-{domain}", "```", "",
          "Set up `.env` and the prerequisites first; see the [relay README](../../README.md).", ""]
    (out / "README.md").write_text("\n".join(L), encoding="utf-8", newline="\n")

    for f in out.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8", errors="replace")
            for pat in LEAKS:
                if re.search(pat, text):
                    shutil.rmtree(out)
                    sys.exit(f"{domain}: {f.name} still matches {pat!r}; nothing published")
    print(f"published {domain} -> {out}")


def public_reflection(text):
    """Keep only the title and the allowlisted sections: what changed, what helped, the /teach rule."""
    parts = re.split(r"(?m)^(?=#{1,2} )", text)
    keep = [p.splitlines()[0] + "\n\n" for p in parts if p.startswith("# ")]
    keep += [p for p in parts if p.startswith("## ") and PUBLIC_SECTIONS.search(p.splitlines()[0])]
    return "".join(keep).rstrip() + "\n"


def teach_section(path):
    text = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    m = re.search(r"^#+[^\n]*/teach[^\n]*\n(.*?)(?=^#+ |\Z)", text, re.M | re.S)
    return (m.group(0) if m else text[:1200]).strip()[:1800]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path, action="append", help="<out>/<domain> of a graded run")
    ap.add_argument("--dest", required=True, type=Path)
    ap.add_argument("--allow-fail", action="store_true")
    a = ap.parse_args()
    for run in a.run:
        build(run.resolve(), a.dest.resolve(), a.allow_fail)


if __name__ == "__main__":
    main()

"""Domain relay live test: five models and a decision model work one domain brief together.

Stage 0 DISCOVER  claude-haiku-5-5   reads TOKN's own introspect slice -> CAPABILITIES.md
Stage 1 PLAN      claude-opus-5-5    -> PLAN.md
Stage 2 EXECUTE   Kimi-K3.1-Pro      calls the domain tools -> result.json, RESULT.md
Stage 3 CRITIQUE  FW-GLM-5.3         re-runs tools -> critique.json, CRITIQUE.md
Stage 4 DECIDE    Microsoft-Decision-1 typed noul gate over result + critique -> decision.json
Stage 5 REVISE    gpt-6.1-sol        answers every finding -> final result.json, RESULT.md
Stage 6 REFLECT   claude-opus-5-5    TOKN reflecting on TOKN, reads TRACE.json -> REFLECTION.md
Stage 7 GRADE     verify.py          deterministic outer ring, never a model

Every agent stage runs `tokn agent-run --mode <domain>` in an isolated home and workspace.
Credentials are read by exact name from .env (beside run.py when standalone, the repo root
inside the TOKN source checkout) or the process environment, and are scrubbed from every
saved artifact. Inside the source checkout, output must be under artifacts/.
"""

import argparse
import concurrent.futures as cf
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.parse

import verify

HERE = Path(__file__).resolve().parent
# Inside the TOKN source checkout the harness uses a dev build; standalone (the public
# example) it uses the installed `tokn` and the user's own license.
IN_REPO = len(HERE.parents) > 1 and (HERE.parents[1] / "environment-manager").is_dir()
REPO = HERE.parents[1] if IN_REPO else HERE
ENV_FILE = REPO / ".env"
SCENARIOS = HERE / "scenarios"
PROMPTS = HERE / "prompts"
DEV_BUILD = REPO / "artifacts" / "domain-trio-live" / "dev-build"


def default_binary():
    if IN_REPO:
        return DEV_BUILD / "tokn-dev.exe"
    found = shutil.which("tokn")
    return Path(found) if found else Path("tokn")


def default_license():
    if IN_REPO:
        return DEV_BUILD / "dev-license.json"
    if os.environ.get("TOKN_LICENSE_FILE"):
        return Path(os.environ["TOKN_LICENSE_FILE"])
    home = os.environ.get("TOKN_HOME") or str(Path.home() / ".tokn")
    return Path(home) / "license.json"

# Endpoints and keys come only from .env or the environment (see .env.example); never hard-code them.
NEEDED = ("RELAY_GATEWAY_URL", "RELAY_FOUNDRY_URL", "APIM_KEY", "FAST_API_KEY",
          "DECISION_API_ENDPOINT", "DECISION_API_KEY")

PASSTHROUGH = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "PROGRAMFILES", "PROGRAMFILES(X86)",
               "PROGRAMDATA", "PROCESSOR_ARCHITECTURE", "LANG", "SSL_CERT_FILE", "SSL_CERT_DIR",
               "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY"}


def models(secrets):
    """Model roster: provider flag plus the env each one needs."""
    GATEWAY = secrets["RELAY_GATEWAY_URL"].rstrip("/")
    FOUNDRY = secrets["RELAY_FOUNDRY_URL"].rstrip("/")
    gateway_openai = lambda name: {
        "provider": "azure-openai", "env": {
            "AZURE_OPENAI_ENDPOINT": f"{GATEWAY}/openai/v1", "AZURE_OPENAI_API_KEY": secrets["APIM_KEY"],
            "AZURE_OPENAI_DEPLOYMENT": name, "AZURE_OPENAI_USE_DEFAULT_CREDENTIAL": "false"}}
    anthropic = {"provider": "anthropic", "env": {
        "ANTHROPIC_BASE_URL": f"{GATEWAY}/anthropic", "ANTHROPIC_API_KEY": secrets["FAST_API_KEY"]}}
    return {
        "claude-haiku-5-5": anthropic,
        "claude-opus-5-5": anthropic,
        "Kimi-K3.1-Pro": gateway_openai("Kimi-K3.1-Pro"),
        "FW-GLM-5.3": gateway_openai("FW-GLM-5.3"),
        "gpt-6.1-sol": {"provider": "azure-openai", "env": {
            "AZURE_OPENAI_ENDPOINT": FOUNDRY, "AZURE_OPENAI_DEPLOYMENT": "gpt-6.1-sol",
            "AZURE_OPENAI_AD_TOKEN": secrets["AZURE_OPENAI_AD_TOKEN"], "AZURE_OPENAI_API_KEY": "",
            "AZURE_OPENAI_USE_DEFAULT_CREDENTIAL": "false"}},
    }


STAGES = [
    # (id, name, prompt file, model, artifacts the stage must produce)
    ("0-discover", "DISCOVER", "discover.md", "claude-haiku-5-5", ["CAPABILITIES.md"]),
    ("1-plan", "PLAN", "plan.md", "claude-opus-5-5", ["PLAN.md"]),
    ("2-execute", "EXECUTE", "execute.md", "Kimi-K3.1-Pro", ["result.json", "RESULT.md"]),
    ("3-critique", "CRITIQUE", "critique.md", "FW-GLM-5.3", ["critique.json", "CRITIQUE.md"]),
    ("4-decide", "DECIDE", None, "Microsoft-Decision-1", ["decision.json"]),
    ("5-revise", "REVISE", "revise.md", "gpt-6.1-sol", ["result.json", "RESULT.md"]),
    ("6-reflect", "REFLECT", "reflect.md", "claude-opus-5-5", ["REFLECTION.md"]),
]


def fetch_ad_token():
    """Fresh Entra token for gpt-6.1-sol. Tokens last about an hour and a full relay runs for
    hours, so run_agent calls this per stage instead of reusing the start-up token."""
    az = shutil.which("az")
    if not az:
        raise SystemExit("Azure CLI missing (needed for gpt-6.1-sol): winget install Microsoft.AzureCLI, "
                         "brew install azure-cli, or https://aka.ms/InstallAzureCLIDeb; then az login.")
    out = subprocess.run([az, "account", "get-access-token", "--resource", "https://cognitiveservices.azure.com",
                          "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True,
                         encoding="utf-8", timeout=90, check=False)
    if out.returncode or not out.stdout.strip():
        raise SystemExit("Azure authentication failed; run az login (or set AZURE_OPENAI_AD_TOKEN) and retry.")
    return out.stdout.strip()


def read_secrets():
    values = {}
    env_file = ENV_FILE
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key in NEEDED:
                values[key] = value.strip().strip("\"'")
    for key in NEEDED:
        if os.environ.get(key):
            values[key] = os.environ[key]
    missing = [k for k in NEEDED if not values.get(k)]
    if missing:
        raise SystemExit(
            "Missing credentials: " + ", ".join(missing) + ".\n"
            f"Copy .env.example to {ENV_FILE} and fill it in. "
            "The relay needs ALL of: RELAY_GATEWAY_URL + RELAY_FOUNDRY_URL (model endpoints), APIM_KEY (gateway for Kimi-K3.1-Pro and FW-GLM-5.3), FAST_API_KEY "
            "(Anthropic gateway for Claude Opus 5.5 and Haiku 5.5), DECISION_API_ENDPOINT + DECISION_API_KEY "
            "(Microsoft-Decision-1), and an Azure CLI login (az login) for gpt-6.1-sol. Add them to .env and retry.")
    token = os.environ.get("AZURE_OPENAI_AD_TOKEN", "") or fetch_ad_token()
    values["AZURE_OPENAI_AD_TOKEN"] = token
    return values


def scrub(text, secrets):
    for value in secrets.values():
        if value and len(value) > 8:
            text = text.replace(value, "***")
            host = urllib.parse.urlsplit(value).hostname if value.startswith("http") else None
            if host:
                text = text.replace(host, "<redacted-host>")
    return text


def base_env(home, tmp, license_file):
    env = {k: v for k, v in os.environ.items() if k.upper() in PASSTHROUGH}
    env.update({
        "HOME": str(home), "USERPROFILE": str(home),
        "APPDATA": str(home / "AppData" / "Roaming"), "LOCALAPPDATA": str(home / "AppData" / "Local"),
        "TMP": str(tmp), "TEMP": str(tmp), "TMPDIR": str(tmp),
        "TOKN_NO_REGISTER": "1", "TOKN_NO_UPDATE_CHECK": "1", "TOKN_LICENSE_QUIET": "1",
        "TOKN_LICENSE_FILE": str(license_file),
    })
    return env


def introspect_slice(binary, env, cwd, domain):
    """TOKN's own self-description for this domain, from `tokn introspect`.

    Curated rather than dumped: a raw introspect slice is ~40 KB of unrelated
    commands, and its free-text descriptions trip TOKN's own injection scanner
    (rule L2-003 on "unrestricted", L3-006 on a literal tool-call tag), which
    blocked the Scout from reading it in the first pilot.
    """
    out = subprocess.run([str(binary), "introspect"], cwd=cwd, env=env, capture_output=True, text=True,
                         encoding="utf-8", timeout=60, check=False)
    try:
        full = json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"error": "tokn introspect did not return JSON", "stderr": out.stderr[-400:]}
    agent_run = next((c for c in full.get("commands", []) if c.get("name") == "agent-run"), {})
    modes = agent_run.get("modes", [])
    return {
        "source": "tokn introspect (curated by the relay driver)",
        "version": full.get("version"), "contract_version": full.get("contract_version"),
        "mode": next((m for m in modes if m.get("name") == domain), None),
        "domain_modes_available": sorted(m["name"] for m in modes if m.get("category") == "domain"),
        "agent_run_flags": sorted(f.get("name", "") for f in agent_run.get("flags", [])),
    }


def newest_runlog(ws, before):
    runs = ws / ".nospace" / "runs"
    logs = sorted(set(runs.glob("*.jsonl")) - before, key=lambda p: p.stat().st_mtime) if runs.is_dir() else []
    return logs[-1] if logs else None


def summarize_runlog(path):
    tools, errors, blocked = {}, 0, 0
    final = ""
    if not path:
        return {"tool_calls": tools, "tool_errors": errors, "blocked_or_denied": blocked, "final": final}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload = rec.get("payload") or {}
        name = rec.get("tool_name") or payload.get("ToolName")
        if rec.get("role") == "tool" or rec.get("type") == "tool.result":
            if name:
                tools[name] = tools.get(name, 0) + 1
            content = str(rec.get("content") or "")
            if payload.get("Error") or '"error"' in content[:200]:
                errors += 1
            if payload.get("Blocked") or payload.get("Denied") or "blocked" in content[:200].lower():
                blocked += 1
        if rec.get("event") == "final":
            final = str(rec.get("content") or "")[:600]
    return {"tool_calls": tools, "tool_errors": errors, "blocked_or_denied": blocked, "final": final}


def render(prompt_name, values):
    text = (PROMPTS / prompt_name).read_text(encoding="utf-8")
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


READ_ONLY_NOTE = """

## Read-only authority
This domain's authority scope denies `write_file` and every other mutating tool, by design: a
security reviewer must never change what it reviews. Do NOT try to work around the denial (no
shell redirects, no scripts that write files). Instead, put the COMPLETE content of every
deliverable named above in your final answer, each wrapped exactly like this:

=== FILE: NAME.ext ===
...full file content...
=== END FILE ===

The relay driver writes those blocks into the workspace for the next stage. Anything outside
the blocks is treated as commentary. Your final answer has an output-token cap of roughly
8,000 tokens, so keep commentary to two sentences and every file tight (under ~12,000
characters in total); a block cut off by the cap reaches the next stage marked as truncated.
"""

FILE_BLOCK = re.compile(r"^=== FILE: ([A-Za-z0-9_.\-]+) ===\r?\n(.*?)(?:^=== END FILE ===|\Z)", re.M | re.S)


def materialize_files(ws, text):
    """Write `=== FILE: x ===` blocks from a read-only stage's final answer.

    Names are restricted to bare file names, so a block can never escape the workspace."""
    written = []
    for match in FILE_BLOCK.finditer(text or ""):
        name, body = match.group(1), match.group(2)
        truncated = not match.group(0).rstrip().endswith("=== END FILE ===")
        if name.startswith(".") or name in ("BRIEF.md", "TRACE.json"):
            continue
        body = body.strip()
        if body.startswith("```"):
            body = body.split("\n", 1)[1] if "\n" in body else ""
            body = body.rsplit("```", 1)[0]
        if truncated:
            body += "\n\n[TRUNCATED: the final answer hit the output-token cap before this file ended]"
        (ws / name).write_text(body.strip() + "\n", encoding="utf-8")
        written.append(name + (" (truncated)" if truncated else ""))
    return written


def rate_limited(ctx, stage):
    """True when the stage died on gateway 429s rather than on its own work."""
    log = ctx["root"] / "logs" / f"{stage}.stderr.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    return "rate limited (429)" in text and "context deadline exceeded" in text


def run_agent(ctx, stage, prompt_text, model, max_steps):
    roster = ctx["models"][model]
    env = dict(ctx["env"])
    env.update(roster["env"])
    if "AZURE_OPENAI_AD_TOKEN" in roster["env"] and not os.environ.get("AZURE_OPENAI_AD_TOKEN"):
        token = fetch_ad_token()
        env["AZURE_OPENAI_AD_TOKEN"] = token
        ctx["secrets"][f"_ad_token_{stage}"] = token
    prompt_file = ctx["root"] / "prompts" / f"{stage}.md"
    prompt_file.write_text(prompt_text, encoding="utf-8")
    before = set((ctx["ws"] / ".nospace" / "runs").glob("*.jsonl")) if (ctx["ws"] / ".nospace" / "runs").is_dir() else set()
    cmd = [str(ctx["binary"]), "agent-run", "--mode", ctx["mode"],
           "--model-provider", roster["provider"], "--model-name", model,
           "--repo-root", str(ctx["ws"]), "--prompt-file", str(prompt_file),
           "--max-steps", str(max_steps), "--token-budget", str(ctx["token_budget"]),
           "--step-timeout", "240s", "--run-timeout", f"{ctx['timeout']}s",
           "--no-confirm", "--no-stream", "--mcp-disabled", "--output-format", "json"]
    started = time.monotonic()
    try:
        proc = subprocess.run(cmd, cwd=ctx["ws"], env=env, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=ctx["timeout"] + 60, check=False)
        code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, str(exc.stdout or ""), str(exc.stderr or "")
    elapsed = round(time.monotonic() - started, 1)
    logs = ctx["root"] / "logs"
    (logs / f"{stage}.stdout.log").write_text(scrub(stdout, ctx["secrets"]), encoding="utf-8")
    (logs / f"{stage}.stderr.log").write_text(scrub(stderr, ctx["secrets"]), encoding="utf-8")
    usage, status, final = {}, None, ""
    start = stdout.find("{")
    if start >= 0:
        try:
            parsed = json.loads(stdout[start:])
            usage, status = parsed.get("usage") or {}, parsed.get("status")
            final = parsed.get("result") or ""
        except json.JSONDecodeError:
            usage = {}
    if ctx.get("read_only"):
        written = materialize_files(ctx["ws"], final)
        if written:
            (logs / f"{stage}.materialized.txt").write_text("\n".join(written), encoding="utf-8")
    runlog = newest_runlog(ctx["ws"], before)
    if runlog:
        shutil.copy(runlog, logs / f"{stage}.runlog.jsonl")
    summary = summarize_runlog(runlog)
    return {"stage": stage, "model": model, "exit_code": code, "status": status, "duration_s": elapsed,
            "tokens": usage.get("tokens"), "steps": usage.get("steps"), "cost_usd": usage.get("cost_usd"),
            **summary}


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def run_decision(ctx, scenario):
    ws = ctx["ws"]
    result = load_json(ws / "result.json") or {}
    critique = load_json(ws / "critique.json") or {}
    state = {
        "domain": ctx["domain"],
        "items": [{k: i.get(k) for k in ("id", "status", "rationale")} for i in result.get("items", [])],
        "gates": result.get("gates", []),
        "findings": [{k: f.get(k) for k in ("id", "item", "severity", "issue")} for f in critique.get("findings", [])],
    }
    questions = {"needs_revision": {"type": "noul", "instructions":
                 "Do the critique findings show at least one item whose status is wrong or unsupported, so the result must be revised before it is used?"}}
    for qid, text in scenario.get("decision_questions", {}).items():
        questions[qid] = {"type": "noul", "instructions": text}
    request = {"state": state, "questions": questions}
    req_file = ctx["root"] / "decision-request.json"
    req_file.write_text(json.dumps(request, indent=2), encoding="utf-8")
    env = dict(ctx["env"])
    env.update({"SYSTEMONE_BACKEND": "microsoft", "DECISION_API_ENDPOINT": ctx["secrets"]["DECISION_API_ENDPOINT"],
                "DECISION_API_KEY": ctx["secrets"]["DECISION_API_KEY"], "DECISION_API_MODEL": "decision-1"})
    started = time.monotonic()
    proc = subprocess.run([str(ctx["binary"]), "system-one", "evaluate", "--file", str(req_file), "--run-timeout", "120s"],
                          cwd=ws, env=env, capture_output=True, text=True, encoding="utf-8", timeout=180, check=False)
    (ctx["root"] / "logs" / "4-decide.stderr.log").write_text(scrub(proc.stderr, ctx["secrets"]), encoding="utf-8")
    response = None
    start = proc.stdout.find("{")
    if start >= 0:
        try:
            response = json.loads(proc.stdout[start:])
        except json.JSONDecodeError:
            response = None
    decision = {"model": "Microsoft-Decision-1", "questions": {k: v["instructions"] for k, v in questions.items()},
                "response": response, "exit_code": proc.returncode}
    probs = {k: (v or {}).get("noul") for k, v in ((response or {}).get("answers") or {}).items()}
    revise = (probs.get("needs_revision") or 0) >= 0.5 or any(
        f.get("severity") == "blocking" for f in critique.get("findings", []))
    decision["routing"] = "full-revision" if revise else "light-revision"
    (ws / "decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    return {"stage": "4-decide", "model": "Microsoft-Decision-1", "exit_code": proc.returncode,
            "duration_s": round(time.monotonic() - started, 1), "probabilities": probs,
            "routing": decision["routing"], "tokens": ((response or {}).get("usage") or {}),
            "tool_calls": {}, "tool_errors": 0, "blocked_or_denied": 0}


def run_domain(domain, args, secrets):
    scenario_dir = SCENARIOS / domain
    scenario = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    mode = scenario.get("mode", domain)
    root = args.out / domain
    ws, home, tmp = root / "ws", root / "home", root / "tmp"
    resume = args.resume_from
    if resume:
        if not ws.is_dir():
            raise SystemExit(f"--resume-from needs an existing workspace at {ws}")
        env = base_env(home, tmp, args.license_file)
    else:
        for d in (ws, home, tmp, root / "prompts", root / "logs"):
            d.mkdir(parents=True)
        shutil.copy(scenario_dir / "brief.md", ws / "BRIEF.md")
        shutil.copytree(scenario_dir / "inputs", ws / "inputs")
        env = base_env(home, tmp, args.license_file)
        (ws / "tokn-self").mkdir()
        (ws / "tokn-self" / "introspect-slice.json").write_text(
            json.dumps(introspect_slice(args.binary, env, ws, mode), indent=2), encoding="utf-8")
        doc = REPO / "docs" / "implementation" / f"{domain}.md"
        if doc.is_file():
            text = doc.read_text(encoding="utf-8", errors="replace")
            if len(text) > 30_000:
                text = text[:30_000] + "\n\n[truncated by the relay driver at 30 KB]\n"
            (ws / "tokn-self" / "DOMAIN-README.md").write_text(text, encoding="utf-8")
    ctx = {"domain": domain, "mode": mode, "root": root, "ws": ws, "env": env, "binary": args.binary,
           "timeout": args.stage_timeout, "secrets": secrets, "models": models(secrets),
           "token_budget": args.token_budget, "read_only": bool(scenario.get("read_only"))}
    vocab = ", ".join(scenario["status_vocabulary"])
    values = {"DOMAIN": domain, "STATUS_VOCAB": vocab, "DECISION_ROUTING": ""}
    trace = {"domain": domain, "title": scenario.get("title"), "stages": []}
    v1_snapshot = ws.parent / "result.v1.json"
    if (ws / "result.v1.json").is_file() and not v1_snapshot.is_file():
        shutil.move(ws / "result.v1.json", v1_snapshot)
    if resume:
        prior = load_json(ws / "TRACE.json") or {}
        trace["stages"] = [s for s in prior.get("stages", []) if int(s["stage"].split("-")[0]) < resume]
        trace["resumed_from"] = resume
        decision = load_json(ws / "decision.json") or {}
        if decision.get("routing") and resume > 4:
            probs = {k: (v or {}).get("noul") for k, v in (((decision.get("response") or {}).get("answers")) or {}).items()}
            values["DECISION_ROUTING"] = (
                f"{decision['routing']} (Decision-1 needs_revision probability {probs.get('needs_revision')}). "
                + ("Re-verify every item, not only the ones named in findings." if decision["routing"] == "full-revision"
                   else "The gate judged the result sound; still answer every finding."))
    started = time.monotonic()
    for stage, name, prompt, model, _ in STAGES:
        if args.stages and stage.split("-")[0] not in args.stages:
            continue
        if resume and int(stage.split("-")[0]) < resume:
            continue
        stage_started = time.time()
        print(f"[{domain}] {stage} {model} ...", flush=True)
        if name == "DECIDE":
            info = run_decision(ctx, scenario)
            values["DECISION_ROUTING"] = (
                f"{info['routing']} (Decision-1 needs_revision probability "
                f"{info['probabilities'].get('needs_revision')}). "
                + ("Re-verify every item, not only the ones named in findings." if info["routing"] == "full-revision"
                   else "The gate judged the result sound; still answer every finding."))
        else:
            if name == "REVISE" and (ws / "result.json").is_file() and not v1_snapshot.is_file():
                shutil.copy(ws / "result.json", v1_snapshot)
            if name == "REFLECT":
                # The snapshot lives outside the workspace until now: left in
                # place, critics flagged it as a stray file and revisers deleted it.
                if v1_snapshot.is_file():
                    shutil.copy(v1_snapshot, ws / "result.v1.json")
                (ws / "TRACE.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
            steps = scenario.get("max_steps", {}).get(name.lower(), 30 if name in ("EXECUTE", "CRITIQUE", "REVISE") else 10)
            produced = next(s[4] for s in STAGES if s[0] == stage)
            text = render(prompt, values)
            if ctx["read_only"]:
                text += READ_ONLY_NOTE
            info = run_agent(ctx, stage, text, model, steps)
            # A shared gateway quota (HTTP 429 until the step timeout fires) says
            # nothing about the model or TOKN, so it is waited out rather than
            # spending the stage's one recorded retry on it.
            for waits, wait in enumerate((120, 300, 600), 1):
                if fresh(ws, produced, stage_started) or not rate_limited(ctx, stage):
                    break
                print(f"[{domain}] {stage} rate-limited by the gateway; waiting {wait}s", flush=True)
                time.sleep(wait)
                info = run_agent(ctx, stage, text, model, steps)
                info["rate_limit_waits"] = waits
            if not fresh(ws, produced, stage_started):
                # One recorded retry: a first attempt that ends without its deliverable
                # (e.g. empty tool arguments, then a governance stop) is a finding the
                # reflection should see, not a silent pass or an immediate abort.
                print(f"[{domain}] {stage} produced no {produced}; retrying once", flush=True)
                first = info
                logs = ctx["root"] / "logs"
                for suffix in ("stderr.log", "stdout.log", "runlog.jsonl"):
                    p = logs / f"{stage}.{suffix}"
                    if p.is_file():
                        p.replace(logs / f"{stage}.attempt1.{suffix}")
                retry_note = (f"\n\n## Retry\nA previous attempt ended without writing {', '.join(produced)} "
                              f"(last output: {(first.get('final') or 'none')[:200]}). "
                              "Every tool call MUST include its arguments, e.g. read_file needs {\"path\": \"...\"}. "
                              f"Write {', '.join(produced)} before anything optional.\n")
                info = run_agent(ctx, stage, text + retry_note, model, steps)
                info["retried_after"] = {k: first.get(k) for k in
                                         ("exit_code", "status", "steps", "tool_calls", "tool_errors", "duration_s")}
            if name == "EXECUTE" and (ws / "result.json").is_file():
                shutil.copy(ws / "result.json", v1_snapshot)
        info["name"] = name
        trace["stages"].append(info)
        print(f"[{domain}] {stage} exit={info['exit_code']} {info['duration_s']}s tools={info.get('tool_calls')}", flush=True)
        produced = next(s[4] for s in STAGES if s[0] == stage)
        if not fresh(ws, produced, stage_started):
            print(f"[{domain}] {stage} did not produce {produced}; stopping this domain", flush=True)
            trace["aborted_at"] = stage
            break
    trace["elapsed_s"] = round(time.monotonic() - started, 1)
    (ws / "TRACE.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    report = verify.grade(ws, scenario, trace)
    (root / "evaluation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return domain, report, trace


def fresh(ws, names, since):
    """True when every deliverable exists AND was written during this stage. Revise must
    rewrite result.json; execute's copy already being there is not a revision."""
    return all((ws / n).is_file() and (ws / n).stat().st_mtime >= since - 1 for n in names)


def license_ok(binary, license_file, cwd):
    env = base_env(cwd, cwd, license_file)
    out = subprocess.run([str(binary), "license", "status", "--json"], cwd=cwd, env=env, capture_output=True,
                         text=True, encoding="utf-8", timeout=30, check=False)
    try:
        status = json.loads(out.stdout)
    except json.JSONDecodeError:
        return False, "license status returned no JSON"
    feats = set(status.get("features", []))
    if status.get("verify_error") or not feats.intersection({"*", "domains:*"}):
        return False, status.get("explanation") or status.get("verify_error") or "no domain feature"
    return True, ""


def write_summary(args, results):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [f"# Domain relay live results — {stamp}", "",
             "Roster: Haiku 5.5 (discover) → Opus 5.5 (plan) → Kimi-K3.1-Pro (execute) → FW-GLM-5.3 (critique) → "
             "Microsoft-Decision-1 (gate) → gpt-6.1-sol (revise) → Opus 5.5 (reflect) → verify.py (grade)", "",
             "| Domain | Verdict | v1 accuracy | Final accuracy | Findings | Answered | Gate routing | Execute tools | Minutes |",
             "|---|---|---|---|---|---|---|---|---|"]
    for domain, report, trace in sorted(results, key=lambda r: r[0]):
        m = report.get("metrics", {})
        lines.append(f"| {domain} | **{report['verdict']}** | {m.get('accuracy_v1')} | {m.get('accuracy_final')} | "
                     f"{m.get('findings')} | {m.get('findings_answered')} | {m.get('routing')} | "
                     f"{m.get('execute_domain_tools')} | {round(trace.get('elapsed_s', 0) / 60, 1)} |")
    lines += ["", "## Failed checks", ""]
    for domain, report, _ in sorted(results, key=lambda r: r[0]):
        for check in report.get("checks", []):
            if not check["ok"]:
                lines.append(f"- **{domain}** `{check['name']}`: {check['detail']}")
    (HERE / "results").mkdir(exist_ok=True)
    path = HERE / "results" / f"SUMMARY-{stamp}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--domains", default="", help="Comma-separated scenario names (default: all)")
    parser.add_argument("--out", type=Path, required=True, help="Absolute, not-yet-existing output directory")
    parser.add_argument("--binary", type=Path, default=default_binary())
    parser.add_argument("--license-file", type=Path, default=default_license())
    parser.add_argument("--parallel", type=int, default=3)
    parser.add_argument("--stage-timeout", type=int, default=900)
    parser.add_argument("--token-budget", type=int, default=4_000_000,
                        help="Per-stage token budget; with history, a long execute stage resends ~90K tokens per turn")
    parser.add_argument("--resume-from", type=int, default=0,
                        help="Rerun stages N.. in an existing --out (e.g. 5 after an expired token killed revise)")
    parser.add_argument("--stages", default="", help="Comma-separated stage numbers to run (debug only)")
    args = parser.parse_args()
    if not args.out.is_absolute() or (args.out.exists() != bool(args.resume_from)):
        parser.error("--out must be an absolute directory: not-yet-existing, or existing with --resume-from.")
    args.out = args.out.resolve()
    if IN_REPO and args.out.is_relative_to(REPO) and not args.out.is_relative_to(REPO / "artifacts"):
        parser.error("Inside this checkout, runtime output must be under artifacts/.")
    if not args.binary.is_file() or not args.license_file.is_file():
        if IN_REPO:
            parser.error("Domain modes need a licensed binary. Build one with tests\\system-one-domain-live\\prepare-dev.ps1 "
                         "(dev binary + dev license) or pass --binary/--license-file. Also required: Python 3.11+, az login.")
        parser.error(f"Need the tokn binary ({args.binary}) and a license file ({args.license_file}). "
                     "Install tokn from the releases page and put it on PATH, then start the trial once with "
                     "`tokn license trial` (domain modes need trial or higher), or pass --binary/--license-file.")
    args.binary, args.license_file = args.binary.resolve(), args.license_file.resolve()
    args.stages = [s for s in args.stages.split(",") if s]
    domains = [d for d in args.domains.split(",") if d] or sorted(p.name for p in SCENARIOS.iterdir() if (p / "scenario.json").is_file())
    unknown = [d for d in domains if not (SCENARIOS / d / "scenario.json").is_file()]
    if unknown:
        parser.error("No scenario for: " + ", ".join(unknown))
    args.out.mkdir(parents=True, exist_ok=bool(args.resume_from))
    ok, why = license_ok(args.binary, args.license_file, args.out)
    if not ok:
        raise SystemExit(f"License preflight failed ({why}); no inference started.")
    secrets = read_secrets()
    results = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.parallel)) as pool:
        futures = {pool.submit(run_domain, d, args, secrets): d for d in domains}
        for fut in cf.as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as exc:  # one domain's crash must not hide the others' results
                d = futures[fut]
                results.append((d, {"verdict": "ERROR", "checks": [{"name": "driver", "ok": False, "detail": repr(exc)}],
                                    "metrics": {}}, {}))
            print(f"[{results[-1][0]}] verdict={results[-1][1]['verdict']}", flush=True)
    summary = write_summary(args, results)
    print(f"summary: {summary}")
    return 0 if all(r[1]["verdict"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

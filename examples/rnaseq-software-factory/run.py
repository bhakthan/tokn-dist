#!/usr/bin/env python3
"""TOKN Agent Factory example: an RNA-seq differential-expression pipeline, end to end.

    python run.py --profile offline                 # no models: fixture + grader self-test
    python run.py --profile trio   [--approve-prod]  # Opus + gpt-6-astra + decision model
    python run.py --profile hybrid [--approve-prod]  # + HF coder, local ollama (data_boundary: local)

Every run writes to out/<timestamp>/ (gitignored): seed/ (the candidate git repo,
with the factory store in seed/.nospace/factory), answer_key.json and intake/
(both OUTSIDE the candidate), targets/{dev,staging,prod}, logs and verify/REPORT.md.

Preflight lists EVERY missing dependency at once with install commands and
exits 2 before anything runs. Production approval is never automatic: without
--approve-prod the run stops at the prod gate and prints the approve command.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_ROOT = HERE / "out"
sys.path.insert(0, str(HERE))


def _mc():
    import make_case  # lazy: numpy may be missing until preflight has reported it
    return make_case

DEFAULTS = {
    "FACTORY_OPUS_MODEL": "claude-opus-5-5",
    "FACTORY_ASTRA_MODEL": "gpt-6-astra",
    "FACTORY_DECISION_BACKEND": "azure",
    "FACTORY_HF_CODER_MODEL": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "FACTORY_OLLAMA_MODEL": "qwen2.5-coder:7b",
}
PY_PKGS = ["numpy", "pandas", "scipy", "pytest"]
OS = platform.system()


def log(msg: str) -> None:
    print(f"[run {datetime.now():%H:%M:%S}] {msg}", flush=True)


def banner(msg: str) -> None:
    line = "!" * 78
    print(f"\n{line}\n!! {msg}\n{line}\n", flush=True)


def load_dotenv(path: Path) -> None:
    """KEY=VALUE lines from ./.env; never overrides the environment."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def setting(name: str) -> str:
    return os.environ.get(name, "").strip() or DEFAULTS.get(name, "")


# ── install hints ───────────────────────────────────────────────────────────

def hint(win: str, mac: str, linux: str) -> str:
    return {"Windows": win, "Darwin": mac}.get(OS, linux)


GIT_HINT = hint("winget install Git.Git", "xcode-select --install  (or: brew install git)", "sudo apt install git")
AZ_HINT = hint("winget install Microsoft.AzureCLI", "brew install azure-cli",
               "curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash") + "; then `az login`"
OLLAMA_HINT = hint("winget install Ollama.Ollama", "brew install ollama",
                   "curl -fsSL https://ollama.com/install.sh | sh") + "; then start it (`ollama serve`)"
TOKN_HINT = ("download tokn v0.3.115+ from https://github.com/bhakthan/tokn-dist/releases/latest "
             "and put it on PATH (or pass --tokn / set TOKN_BIN)")


# ── tokn discovery ──────────────────────────────────────────────────────────

def tokn_candidates(explicit: str | None) -> list[Path]:
    exe = "tokn.exe" if OS == "Windows" else "tokn"
    c = [Path(explicit)] if explicit else []
    if os.environ.get("TOKN_BIN"):
        c.append(Path(os.environ["TOKN_BIN"]))
    c += [OUT_ROOT / "bin" / exe, HERE / exe]
    if shutil.which("tokn"):
        c.append(Path(shutil.which("tokn")))
    return c


def find_tokn(explicit: str | None) -> tuple[Path | None, list[str]]:
    """First candidate whose `factory --help` works; notes explain the rejects."""
    notes = []
    for p in tokn_candidates(explicit):
        if not p.is_file():
            if explicit and p == Path(explicit):
                notes.append(f"--tokn {p} does not exist")
            continue
        try:
            r = subprocess.run([str(p), "factory", "--help"], capture_output=True, text=True, timeout=60,
                               env=tokn_env({}))
        except (OSError, subprocess.TimeoutExpired) as e:
            notes.append(f"{p}: {e}")
            continue
        if r.returncode == 0 and "Available Commands" in r.stdout and "approve" in r.stdout:
            return p.resolve(), notes
        notes.append(f"{p} has no `factory` command (stale build)")
    return None, notes


def tokn_env(extra: dict[str, str]) -> dict[str, str]:
    env = dict(os.environ)
    env.update({"TOKN_NO_REGISTER": "1", "TOKN_NO_UPDATE_CHECK": "1", "TOKN_LICENSE_QUIET": "1"})
    env.update(extra)
    return env


# ── preflight ───────────────────────────────────────────────────────────────

def anthropic_creds() -> dict[str, str]:
    """ANTHROPIC_API_KEY, plus ANTHROPIC_BASE_URL for an Anthropic-compatible gateway."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        out = {"ANTHROPIC_API_KEY": os.environ["ANTHROPIC_API_KEY"]}
        if os.environ.get("ANTHROPIC_BASE_URL"):
            out["ANTHROPIC_BASE_URL"] = os.environ["ANTHROPIC_BASE_URL"]
        return out
    return {}


def az_token() -> str | None:
    az = shutil.which("az")
    if not az:
        return None
    try:
        r = subprocess.run([az, "account", "get-access-token", "--resource", "https://cognitiveservices.azure.com",
                            "--query", "accessToken", "-o", "tsv"], capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def ollama_models() -> tuple[bool, list[str], str]:
    exe = shutil.which("ollama")
    if not exe:
        return False, [], "missing"
    try:
        r = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as e:
        return True, [], str(e)
    if r.returncode != 0:
        return True, [], (r.stderr or r.stdout).strip()[:200]
    names = [ln.split()[0] for ln in r.stdout.splitlines()[1:] if ln.strip()]
    return True, names, ""


DECISION_REQS = {
    # backend: (required vars, Entra-capable)
    "azure": (["AZURE_OPENAI_ENDPOINT"], True),
    "microsoft": (["DECISION_API_ENDPOINT"], True),
    "compatible": (["SYSTEMONE_BASE_URL", "SYSTEMONE_MODEL"], False),
    "openai": (["OPENAI_API_KEY"], False),
    "gemini": (["GEMINI_API_KEY"], False),
    "jev": (["JEV_API_KEY"], False),
    "local": ([], False),
}


def preflight(profile: str, tokn_arg: str | None) -> dict:
    """Collects every problem, prints them all with install commands, exits 2 if any."""
    problems: list[str] = []
    ctx: dict = {}

    missing_py = [p for p in PY_PKGS if importlib.util.find_spec(p) is None]
    if missing_py:
        problems.append(f"Python packages missing: {', '.join(missing_py)} (fixture generator, pipeline and grader). "
                        f"Install: \"{sys.executable}\" -m pip install {' '.join(missing_py)}")
    if sys.version_info < (3, 10):
        problems.append(f"Python >= 3.10 required (found {platform.python_version()}).")

    tokn, notes = find_tokn(tokn_arg)
    ctx["tokn"] = tokn
    if profile == "offline":
        ctx["tokn_notes"] = notes
    else:
        if tokn is None:
            problems.append("A tokn binary with the `factory` command was not found"
                            + (f" ({'; '.join(notes)})" if notes else "") + f". {TOKN_HINT}")
        if not shutil.which("git"):
            problems.append(f"git is missing (the candidate is a git repo; every role works in a git worktree). Install: {GIT_HINT}")
        if importlib.util.find_spec("yaml") is None:
            problems.append(f"PyYAML missing (run.py reads the rendered models section to grade model attribution). "
                            f"Install: \"{sys.executable}\" -m pip install pyyaml")

        ant = anthropic_creds()
        ctx["anthropic"] = ant
        if not ant:
            problems.append("Anthropic credentials missing (architect/implementer roles, Opus). Set ANTHROPIC_API_KEY "
                            "(+ANTHROPIC_BASE_URL for a gateway), in the shell or "
                            f"{HERE / '.env'} (see profiles/{profile}.env.example).")

        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        if not endpoint:
            problems.append("AZURE_OPENAI_ENDPOINT is not set (gpt-6-astra: product/reviewer/test/release roles).")
        if os.environ.get("AZURE_OPENAI_API_KEY"):
            ctx["azure_auth"] = {"AZURE_OPENAI_API_KEY": os.environ["AZURE_OPENAI_API_KEY"]}
        else:
            tok = az_token()
            if tok:
                ctx["azure_auth"] = {"AZURE_OPENAI_AD_TOKEN": tok}
            elif not shutil.which("az"):
                problems.append(f"No Azure OpenAI auth: set AZURE_OPENAI_API_KEY, or install the Azure CLI and sign in. Install: {AZ_HINT}")
            else:
                problems.append("No Azure OpenAI auth: AZURE_OPENAI_API_KEY is unset and the Azure CLI is not signed in "
                                "for https://cognitiveservices.azure.com. Run `az login` (or set AZURE_OPENAI_API_KEY).")
        if not setting("FACTORY_ASTRA_MODEL"):
            problems.append("FACTORY_ASTRA_MODEL (Azure deployment name for gpt-6-astra) is empty.")

        backend = setting("FACTORY_DECISION_BACKEND").lower()
        ctx["decision_backend"] = backend
        if backend not in DECISION_REQS:
            problems.append(f"FACTORY_DECISION_BACKEND={backend!r} is not one of {', '.join(DECISION_REQS)}.")
        else:
            need, entra = DECISION_REQS[backend]
            miss = [k for k in need if not os.environ.get(k)]
            if miss:
                problems.append(f"Decision backend {backend!r} (review-gate decision model) needs: {', '.join(miss)}.")
            if entra and backend == "azure" and not os.environ.get("AZURE_OPENAI_API_KEY") and "azure_auth" not in ctx:
                problems.append("Decision backend 'azure' needs AZURE_OPENAI_API_KEY or a signed-in Azure CLI (Entra).")
            if entra and backend == "microsoft" and not os.environ.get("DECISION_API_KEY") and az_token() is None:
                problems.append("Decision backend 'microsoft' needs DECISION_API_KEY or a signed-in Azure CLI (Entra).")

        if profile == "hybrid":
            if not os.environ.get("HF_TOKEN"):
                problems.append("HF_TOKEN is not set (implementer runs an open-weights coder on Hugging Face). "
                                "Create one at https://huggingface.co/settings/tokens and export HF_TOKEN.")
            present, names, err = ollama_models()
            want = setting("FACTORY_OLLAMA_MODEL")
            if not present:
                problems.append(f"ollama is missing (test/observer roles run locally, data_boundary: local). Install: {OLLAMA_HINT}; "
                                f"then `ollama pull {want}`")
            elif err:
                problems.append(f"ollama is installed but not answering (`ollama list`: {err}). Start it: `ollama serve`; "
                                f"then `ollama pull {want}`")
            elif not any(n == want or n == f"{want}:latest" for n in names):
                problems.append(f"ollama model {want!r} is not pulled (have: {', '.join(names) or 'none'}). Run: ollama pull {want}")
            ob = os.environ.get("OLLAMA_BASE_URL", "")
            if ob and not any(h in ob for h in ("localhost", "127.0.0.1", "[::1]")):
                problems.append(f"OLLAMA_BASE_URL={ob} is not loopback; data_boundary: local roles require a loopback endpoint.")

    if problems:
        print(f"Preflight failed for --profile {profile}; nothing was run. Fix ALL of these, then retry:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(2)
    return ctx


# ── helpers ─────────────────────────────────────────────────────────────────

def tree_hash(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()}


def grade(repo: Path, key: Path, requirements: Path | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(HERE / "grade.py"), "--key", str(key), "--repo", str(repo)]
    if requirements:
        cmd += ["--requirements", str(requirements)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    try:
        return r.returncode, json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return r.returncode, {"error": (r.stdout + r.stderr)[-600:]}


def pytest_counts(repo: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"], cwd=repo,
                       capture_output=True, text=True, timeout=900)
    tail = [ln for ln in r.stdout.splitlines() if ln.strip()][-1:] or ["(no output)"]
    shutil.rmtree(repo / ".pytest_out", ignore_errors=True)
    return r.returncode, tail[0]


def overlay_fix(repo: Path) -> None:
    for sub in ("rnaseq_de", "tests"):
        for f in (HERE / "reference_fix" / sub).glob("*.py"):
            shutil.copy2(f, repo / sub / f.name)


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def git_init(repo: Path) -> str:
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.name", "rnaseq-software-factory")
    git(repo, "config", "user.email", "rnaseq-software-factory@example.invalid")
    git(repo, "config", "core.autocrlf", "false")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "seed: synthetic RNA-seq DE pipeline (generated fixture)")
    return git(repo, "rev-parse", "HEAD")


def render(template: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        template = template.replace("{{" + k + "}}", v)
    return template


def render_spec(profile_models: str, run_dir: Path, tokn: Path | None, key: Path) -> tuple[str, str]:
    """Returns (factory.yaml text, rendered models fragment)."""
    models = render((HERE / "spec" / f"models.{profile_models}.yaml").read_text(encoding="utf-8"), {
        "OPUS_MODEL": setting("FACTORY_OPUS_MODEL"),
        "ASTRA_MODEL": setting("FACTORY_ASTRA_MODEL"),
        "HF_CODER_MODEL": setting("FACTORY_HF_CODER_MODEL"),
        "OLLAMA_MODEL": setting("FACTORY_OLLAMA_MODEL"),
        "DECISION_BACKEND": setting("FACTORY_DECISION_BACKEND"),
        "DECISION_MODEL": os.environ.get("FACTORY_DECISION_MODEL", "").strip(),
    })
    # No FACTORY_DECISION_MODEL: drop the key so each decision backend uses its
    # own default (Decisions models differ from chat models such as gpt-6-astra).
    models = models.replace(", model: ''", "")
    spec = render((HERE / "spec" / "factory.yaml").read_text(encoding="utf-8"), {
        "PYTHON": sys.executable,
        "GRADE_PY": str(HERE / "grade.py"),
        "ANSWER_KEY": str(key),
        "TOKN": str(tokn) if tokn else "tokn",
        "TARGETS": str(run_dir / "targets"),
        "APPROVER": factory_actor(),
        "INTAKE_DIR": str(run_dir / "intake"),
        "REQUIREMENTS": str(run_dir / "intake" / "requirements.json"),
        "MODELS": models,
    })
    return spec, models


def factory_actor() -> str:
    """Mirrors factoryActor() in factory_cmd.go: the OS user name, domain stripped."""
    import getpass
    u = getpass.getuser()
    return u.replace("\\", "/").rsplit("/", 1)[-1]


CANON = {"azure": "azure-openai", "foundry": "azure-openai", "hf": "huggingface"}


def bindings_json(models_yaml: str) -> dict:
    import yaml  # preflight requires it for live profiles

    def canon(b):
        if not isinstance(b, dict):
            return b
        out = dict(b)
        out["provider"] = CANON.get(str(b.get("provider", "")).lower(), str(b.get("provider", "")).lower())
        out["fallback"] = [canon(f) for f in b.get("fallback", []) or []]
        return out

    m = (yaml.safe_load(models_yaml) or {}).get("models", {})
    return {"default": canon(m["default"]) if m.get("default") else None,
            "roles": {r: canon(b) for r, b in (m.get("roles") or {}).items()},
            "decisions": m.get("decisions", {})}


class Tokn:
    def __init__(self, exe: Path, repo: Path, logdir: Path, env: dict[str, str]):
        self.exe, self.repo, self.logdir, self.env, self.n = exe, repo, logdir, env, 0

    def __call__(self, *args: str, timeout: int = 7200, check: bool = False) -> subprocess.CompletedProcess:
        self.n += 1
        cmd = [str(self.exe), "factory", *args, "--repo-root", str(self.repo)]
        log("$ tokn factory " + " ".join(args))
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=self.env, cwd=self.repo)
        name = f"{self.n:03d}-{'-'.join(a for a in args[:2] if not a.startswith('-'))}.log"
        (self.logdir / name).write_text(f"$ {' '.join(cmd)}\nexit {r.returncode}\n--- stdout\n{r.stdout}\n--- stderr\n{r.stderr}",
                                        encoding="utf-8")
        if check and r.returncode != 0:
            raise SystemExit(f"tokn factory {' '.join(args)} failed (exit {r.returncode}); see {self.logdir / name}\n{r.stderr[-800:]}")
        return r


def jparse(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        for ln in reversed(text.splitlines()):
            try:
                return json.loads(ln)
            except json.JSONDecodeError:
                continue
    return None


# ── offline profile ─────────────────────────────────────────────────────────

def run_offline(args, ctx, run_dir: Path) -> int:
    results: dict = {"profile": "offline", "checks": {}}
    ok = True

    def check(name: str, passed: bool, detail) -> None:
        nonlocal ok
        ok &= passed
        results["checks"][name] = {"ok": passed, "detail": detail}
        log(f"{'PASS' if passed else 'FAIL'}  {name}: {detail if isinstance(detail, str) else json.dumps(detail)}")

    hashes = []
    for i in (1, 2):
        d = run_dir / f"det{i}"
        _mc().make_case(d / "seed", d / "answer_key.json", args.seed, d / "intake")
        hashes.append({"seed": tree_hash(d / "seed"), "key": tree_hash(d)["answer_key.json"],
                       "intake": tree_hash(d / "intake")})
    check("make_case deterministic", hashes[0] == hashes[1],
          f"seed {args.seed}: {len(hashes[0]['seed'])} files + key + intake identical across two runs")
    shutil.rmtree(run_dir / "det2", ignore_errors=True)
    seed, key = run_dir / "det1" / "seed", run_dir / "det1" / "answer_key.json"

    rc, g = grade(seed, key)
    check("grader FAILS on seed", rc == 1 and g.get("pass") is False,
          {k: g.get(k) for k in ("recall", "precision", "rin_filtered", "strandedness_detected", "confounded_refused", "pii_clean")})
    rc, t = pytest_counts(seed)
    check("pytest fails on seed", rc != 0, t)

    fixed = run_dir / "fixed"
    shutil.copytree(seed, fixed)
    overlay_fix(fixed)
    rc, g2 = grade(fixed, key)
    check("grader PASSES on seed+reference_fix", rc == 0 and g2.get("pass") is True,
          {k: g2.get(k) for k in ("recall", "precision", "rin_filtered", "strandedness_detected", "confounded_refused", "pii_clean", "data_intact")})
    rc, t = pytest_counts(fixed)
    check("pytest passes on seed+reference_fix", rc == 0, t)

    # Loop 3: once product asks for the single-cell service, the same gate must
    # fail the prototype and pass the hardened reference.
    req = run_dir / "requirements.sc.json"
    req.write_text(json.dumps({"sc": True}) + "\n", encoding="utf-8")
    sc_keys = ("sc_prompts_exact", "sc_no_ids_on_wire", "sc_lq_exact", "sc_doublets_ok", "sc_correct",
               "sc_wrong", "sc_guardrail", "sc_fail_closed", "sc_input_validation", "sc_isg_recall", "sc_false_calls")
    bulk_only = run_dir / "bulkfix-scseed"
    shutil.copytree(seed, bulk_only)
    for f in (HERE / "reference_fix" / "rnaseq_de").glob("*.py"):
        if not f.name.startswith("sc"):
            shutil.copy2(f, bulk_only / "rnaseq_de" / f.name)
    rc, g3 = grade(bulk_only, key, req)
    check("grader FAILS the single-cell prototype once sc is required", rc == 1 and g3.get("sc_ok") is False,
          {k: g3.get(k) for k in sc_keys})
    shutil.rmtree(bulk_only, ignore_errors=True)
    rc, g4 = grade(fixed, key, req)
    check("grader PASSES the hardened single-cell reference", rc == 0 and g4.get("sc_ok") is True,
          {k: g4.get(k) for k in sc_keys})

    tokn = ctx.get("tokn")
    if tokn is None:
        note = "; ".join(ctx.get("tokn_notes") or []) or "no candidate found"
        log(f"SKIP  spec validation: no tokn with `factory` ({note}). {TOKN_HINT}")
        results["checks"]["spec validate"] = {"ok": None, "detail": f"skipped: {note}"}
    elif not shutil.which("git"):
        log("SKIP  spec validation: git missing")
        results["checks"]["spec validate"] = {"ok": None, "detail": "skipped: git missing"}
    else:
        for prof in ("trio", "hybrid"):
            repo = run_dir / f"spec-{prof}"
            shutil.copytree(seed, repo)
            spec, _ = render_spec(prof, run_dir, tokn, key)
            (repo / "factory.yaml").write_text(spec, encoding="utf-8")
            git_init(repo)
            env = tokn_env({"TOKN_FACTORY_ENV_DIR": str(run_dir / "envdir-unused")})
            r = subprocess.run([str(tokn), "factory", "validate", "--json", "--repo-root", str(repo)],
                               capture_output=True, text=True, timeout=120, env=env)
            rep = jparse(r.stdout) or {}
            errs = [f for f in rep.get("findings", []) if str(f.get("severity", "")).lower() == "error"]
            check(f"spec validate ({prof} models)", r.returncode == 0 and rep.get("valid") is True,
                  {"valid": rep.get("valid"), "digest": rep.get("digest"), "errors": errs,
                   "findings": len(rep.get("findings", []))} if rep else (r.stdout + r.stderr)[-400:])

    (run_dir / "offline-report.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    log(f"offline {'PASSED' if ok else 'FAILED'}; report: {run_dir / 'offline-report.json'}")
    return 0 if ok else 1


# ── live profiles ───────────────────────────────────────────────────────────

def write_profiles(envdir: Path, profile: str, ctx: dict) -> None:
    """Credential profiles named by the spec's models bindings ($TOKN_FACTORY_ENV_DIR/<name>.env)."""
    envdir.mkdir(parents=True, exist_ok=True)

    def put(name: str, kv: dict[str, str]) -> None:
        (envdir / f"{name}.env").write_text("".join(f"{k}={v}\n" for k, v in kv.items() if v), encoding="utf-8")

    azure = {"AZURE_OPENAI_ENDPOINT": os.environ.get("AZURE_OPENAI_ENDPOINT", ""), **ctx.get("azure_auth", {})}
    put("anthropic-gateway", ctx["anthropic"])
    put("azure-astra", azure)
    backend = ctx["decision_backend"]
    need, _ = DECISION_REQS.get(backend, ([], False))
    dec = {k: os.environ.get(k, "") for k in need}
    for k in ("AZURE_OPENAI_API_KEY", "DECISION_API_KEY", "DECISION_API_MODEL", "SYSTEMONE_API_KEY"):
        if os.environ.get(k):
            dec[k] = os.environ[k]
    put("decision", dec)
    if profile == "hybrid":
        put("hf", {"HF_TOKEN": os.environ.get("HF_TOKEN", ""), "HF_BASE_URL": os.environ.get("HF_BASE_URL", "")})
        put("ollama-local", {"OLLAMA_BASE_URL": os.environ.get("OLLAMA_BASE_URL", "")})


def append_incident(intake: Path) -> None:
    pending = (intake / "incident.pending.jsonl").read_text(encoding="utf-8")
    with (intake / "incidents.jsonl").open("a", encoding="utf-8") as f:
        f.write(pending)


def append_feature_request(intake: Path) -> None:
    """Product asks for the single-cell service: the grader starts requiring it, then the request lands."""
    (intake / "requirements.json").write_text(json.dumps({"sc": True}) + "\n", encoding="utf-8")
    pending = (intake / "request.pending.jsonl").read_text(encoding="utf-8")
    with (intake / "requests.jsonl").open("a", encoding="utf-8") as f:
        f.write(pending)


LLAMA_HINT = ("llama.cpp's llama-server is needed to serve the C2S-Scale GGUF locally.\n"
              "  Windows: winget install ggml.llamacpp\n  macOS:   brew install llama.cpp\n"
              "  Linux:   download a release from https://github.com/ggml-org/llama.cpp/releases\n"
              "Model (pick one, ~1.6 GB / ~10 GB), e.g. with the Hugging Face CLI (pip install -U huggingface_hub):\n"
              "  hf download mradermacher/C2S-Scale-Gemma-2-2B-GGUF C2S-Scale-Gemma-2-2B.Q4_K_M.gguf --local-dir <dir>\n"
              "Then set FACTORY_C2S_GGUF=<dir>\\C2S-Scale-Gemma-2-2B.Q4_K_M.gguf, or pass --c2s-url for a server you run.")


class C2SServer:
    """Starts llama-server on loopback for the real-model showcase; stops it on exit. No-op with --c2s-url."""

    def __init__(self, url: str, gguf: str, port: int):
        self.url, self.gguf, self.port, self.proc, self.sha256 = url, gguf, port, None, ""

    def __enter__(self):
        if self.url or not self.gguf:
            return self
        exe = os.environ.get("FACTORY_LLAMA_SERVER", "").strip() or shutil.which("llama-server")
        gg = Path(self.gguf)
        if not exe or not gg.is_file():
            missing = [n for n, ok in (("llama-server", exe), (f"GGUF {gg}", gg.is_file())) if not ok]
            raise SystemExit(f"C2S showcase needs: {', '.join(missing)}\n{LLAMA_HINT}")
        h = hashlib.sha256()
        with gg.open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 22), b""):
                h.update(chunk)
        self.sha256 = h.hexdigest()
        pin = os.environ.get("FACTORY_C2S_SHA256", "").strip().lower()
        if pin and pin != self.sha256:
            raise SystemExit(f"GGUF sha256 {self.sha256} does not match FACTORY_C2S_SHA256 {pin}; refusing to run "
                             "an unpinned model")
        self.url = f"http://127.0.0.1:{self.port}"
        log(f"starting llama-server ({gg.name}, sha256 {self.sha256[:12]}...) on {self.url}")
        self.proc = subprocess.Popen([exe, "-m", str(gg), "--host", "127.0.0.1", "--port", str(self.port),
                                      "-c", "8192", "--parallel", "2"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        import urllib.request
        for _ in range(180):
            if self.proc.poll() is not None:
                raise SystemExit(f"llama-server exited with {self.proc.returncode} while loading {gg.name}")
            try:
                with urllib.request.urlopen(self.url + "/health", timeout=2) as r:
                    if r.status == 200:
                        return self
            except OSError:
                pass
            time.sleep(1)
        raise SystemExit("llama-server did not become healthy within 180 s")

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.proc.kill()


def c2s_showcase(args, repo: Path, key: Path, requirements: Path, out: Path) -> dict | None:
    """Grade the shipped service once against the REAL C2S model (report-only evidence)."""
    if not (args.c2s_url or os.environ.get("FACTORY_C2S_GGUF", "").strip()):
        log("C2S showcase skipped: set FACTORY_C2S_GGUF or pass --c2s-url to run the shipped service on the real model")
        return None
    with C2SServer(args.c2s_url, os.environ.get("FACTORY_C2S_GGUF", "").strip(),
                   int(os.environ.get("FACTORY_C2S_PORT", "8091"))) as srv:
        r = subprocess.run([sys.executable, str(HERE / "grade.py"), "--key", str(key), "--repo", str(repo),
                            "--requirements", str(requirements), "--c2s-url", srv.url],
                           capture_output=True, text=True, timeout=7200)
    res = jparse(r.stdout) or {"error": (r.stdout + r.stderr)[-600:]}
    res["model_sha256"] = srv.sha256 or "external server (not hashed)"
    res["model"] = Path(srv.gguf).name if srv.gguf and not args.c2s_url else args.c2s_url
    lw = res.get("live_wrong")
    res["ok"] = "error" not in res and isinstance(lw, (int, float)) and lw <= 0.05
    res["seconds"] = res.get("live_seconds")
    out.write_text(json.dumps(res, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    log(f"C2S showcase: live_correct={res.get('live_correct')} live_wrong={res.get('live_wrong')} "
        f"live_unassigned={res.get('live_unassigned')} in {res.get('live_seconds')} s -> {out}")
    return res


# Gate reasons that only report a passing check; anything else is an escalation.
_INFO_REASONS = {"implementation produced changes"}


def blast_radius_only(gate: dict) -> bool:
    """True when every escalation on the gate is a blast-radius overrun (unknown reasons -> False)."""
    esc = [r for r in gate.get("reasons") or [] if r not in _INFO_REASONS]
    return bool(esc) and all(r.startswith(("blast radius:", "integration blast radius:")) for r in esc)


def run_live(args, ctx, run_dir: Path) -> int:
    tokn: Path = ctx["tokn"]
    seed, key, intake = run_dir / "seed", run_dir / "answer_key.json", run_dir / "intake"
    logs, envdir = run_dir / "logs", run_dir / "envdir"
    resuming = args.resume is not None
    if resuming:
        head = subprocess.run(["git", "rev-list", "--max-parents=0", "HEAD"], cwd=seed, capture_output=True,
                              text=True, check=True).stdout.split()[0]
        log(f"resuming {run_dir} (seed @ {head[:12]})")
    else:
        logs.mkdir(parents=True)
        for e in ("dev", "staging", "prod"):
            (run_dir / "targets" / e).mkdir(parents=True)

        _mc().make_case(seed, key, args.seed, intake)
        spec, models = render_spec(args.profile, run_dir, tokn, key)
        (seed / "factory.yaml").write_text(spec, encoding="utf-8")
        (run_dir / "bindings.json").write_text(json.dumps(bindings_json(models), indent=2) + "\n", encoding="utf-8")
        head = git_init(seed)
        (intake / "ci-replay.jsonl").write_text(json.dumps(_mc().ci_replay_record(head), sort_keys=True) + "\n",
                                                encoding="utf-8")
        (intake / "incidents.jsonl").write_text("", encoding="utf-8")
        (intake / "requests.jsonl").write_text("", encoding="utf-8")
        log(f"seed repo {seed} @ {head[:12]}; answer key and intake kept outside it")

    write_profiles(envdir, args.profile, ctx)
    # Role runs use the spec's models: bindings (per-role credential profile
    # from TOKN_FACTORY_ENV_DIR); --model-provider/--model-name below only
    # apply to a role with no binding chain.
    env = tokn_env({"TOKN_FACTORY_ENV_DIR": str(envdir), **ctx["anthropic"], **ctx.get("azure_auth", {})})
    tk = Tokn(tokn, seed, logs, env)
    summary: dict = {"profile": args.profile, "run_dir": str(run_dir), "head": head, "ticks": [],
                     "prod_approved": False, "incident_appended": False, "feature_appended": False, "stopped": "",
                     "blast_radius_approved": []}
    prev = run_dir / "run-summary.json"
    if resuming and prev.is_file():
        old = json.loads(prev.read_text(encoding="utf-8"))
        for k in ("ticks", "prod_approved", "blast_radius_approved"):
            summary[k] = old.get(k, summary[k])
    if resuming:
        summary["incident_appended"] = bool((intake / "incidents.jsonl").read_text(encoding="utf-8").strip())
        rq = intake / "requests.jsonl"
        summary["feature_appended"] = rq.is_file() and bool(rq.read_text(encoding="utf-8").strip())
    try:
        if not resuming:
            v = jparse(tk("validate", "--json").stdout) or {}
            if not v.get("valid"):
                print(json.dumps(v, indent=2))
                raise SystemExit("rendered factory.yaml did not validate; see logs/")
            log(f"spec digest {v['digest']} - approving the test's own spec as the operator ({factory_actor()})")
            tk("approve", v["digest"], "--comment", "rnaseq-software-factory: approve generated test spec", check=True)

        run_flags = ["--once", "--json", "--runtime", "tokn", "--run-timeout", "0",
                     "--model-provider", "anthropic", "--model-name", setting("FACTORY_OPUS_MODEL")]
        if args.max_steps:
            run_flags += ["--max-steps", str(args.max_steps)]
        idle = 0
        for tick in range(1, args.max_ticks + 1):
            t0 = time.time()
            r = tk("run", *run_flags)
            rep = jparse(r.stdout) or {}
            st = jparse(tk("status", "--json").stdout) or {}
            items = st.get("items", []) or []
            states = {i.get("id"): f"{i.get('stage')}/{i.get('state')}" for i in items}
            summary["ticks"].append({"tick": tick, "exit": r.returncode, "secs": round(time.time() - t0, 1),
                                     "report": rep, "items": states})
            log(f"tick {tick}: exit={r.returncode} items={states}")
            if tick == 1 and not items:
                log("WARNING: the observer drafted nothing from intake/ci-replay.jsonl; look for 'observer:' lines in logs/")

            prod_gate = [g for g in st.get("pending_gates", []) or [] if g.get("environment") == "prod"]
            other_human = [g for g in st.get("pending_gates", []) or [] if g.get("environment") != "prod"]
            if prod_gate:
                g = prod_gate[0]
                if not args.approve_prod:
                    summary["stopped"] = f"prod gate {g.get('id')} waits for a human"
                    banner(f"PROD GATE {g.get('id')} for {g.get('work_item_id')} awaits a human. Not approving "
                           f"(no --approve-prod). Approve yourself:\n!!   \"{tokn}\" factory approve {g.get('id')} "
                           f"--repo-root \"{seed}\" --comment \"...\"\n!! then re-run ticks: \"{tokn}\" factory run --once "
                           f"--repo-root \"{seed}\"")
                    break
                banner(f"--approve-prod: APPROVING PRODUCTION gate {g.get('id')} for {g.get('work_item_id')} "
                       f"as {factory_actor()} (logged to the factory store and {logs})")
                tk("approve", g["id"], "--comment", "rnaseq-software-factory --approve-prod (operator-requested)", check=True)
                summary["prod_approved"] = True
                continue
            if other_human:
                g = other_human[0]
                if args.approve_blast_radius and blast_radius_only(g):
                    banner(f"--approve-blast-radius: APPROVING {g.get('stage')} gate {g.get('id')} for "
                           f"{g.get('work_item_id')} as {factory_actor()}; reasons: {g.get('reasons')}")
                    tk("approve", g["id"], "--comment",
                       "rnaseq-software-factory --approve-blast-radius (operator reviewed the oversized change)", check=True)
                    summary["blast_radius_approved"].append({"gate": g.get("id"), "reasons": g.get("reasons")})
                    continue
                summary["stopped"] = f"gate {g.get('id')} ({g.get('stage')}) needs a human"
                banner(f"Gate {g.get('id')} at {g.get('stage')} needs a human decision; run.py never approves "
                       f"non-prod human gates. Inspect: \"{tokn}\" factory status --repo-root \"{seed}\"")
                break

            deployed_prod = (run_dir / "targets" / "prod" / "CURRENT").is_file()
            if deployed_prod and not summary["incident_appended"]:
                append_incident(intake)
                summary["incident_appended"] = True
                log("v1 is in prod: appended GENERATED incident INC-RNASEQ-0001 to intake/incidents.jsonl")
                idle = 0
                continue
            active = [i for i in items if i.get("state") in ("READY", "RUNNING", "DRAFT")]
            if not active:
                idle += 1
                if summary["incident_appended"] and idle >= 2:
                    if not args.no_feature and not summary["feature_appended"]:
                        append_feature_request(intake)
                        summary["feature_appended"] = True
                        log("incident loop settled: product request REQ-SC-0001 appended to intake/requests.jsonl; "
                            "the grader now requires the single-cell (C2S) service")
                        idle = 0
                        continue
                    summary["stopped"] = ("all items settled after the feature loop" if summary["feature_appended"]
                                          else "all items settled after the incident loop")
                    break
                if not summary["incident_appended"] and idle >= 3:
                    summary["stopped"] = "no active items and nothing reached prod"
                    break
            else:
                idle = 0
        else:
            summary["stopped"] = f"--max-ticks {args.max_ticks} reached"

        for name, a in (("verify", ["verify", "--json"]), ("status-slo", ["status", "--slo", "--json"]),
                        ("doctor", ["doctor", "--json"]), ("events", ["events", "--json"])):
            (run_dir / f"{name}.json").write_text(tk(*a).stdout, encoding="utf-8")
    finally:
        shutil.rmtree(envdir, ignore_errors=True)  # credential profiles never outlive the run

    (run_dir / "run-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    log(f"stopped: {summary['stopped']}")
    vargs = []
    if summary["feature_appended"]:
        c2s_showcase(args, seed, key, intake / "requirements.json", run_dir / "c2s-showcase.json")
        vargs = ["--requirements", str(intake / "requirements.json"), "--showcase", str(run_dir / "c2s-showcase.json")]
    vr = subprocess.run([sys.executable, str(HERE / "verify.py"), "--repo", str(seed), "--key", str(key),
                         "--bindings", str(run_dir / "bindings.json"), "--tokn", str(tokn),
                         "--targets", str(run_dir / "targets"), "--out", str(run_dir / "verify"), *vargs],
                        timeout=3600)
    log(f"artifacts: {run_dir}  (verify/REPORT.md)")
    return vr.returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", choices=["offline", "trio", "hybrid"], default="offline")
    ap.add_argument("--approve-prod", action="store_true",
                    help="approve the production release gate when it opens (logged loudly); default: stop there")
    ap.add_argument("--approve-blast-radius", action="store_true",
                    help="approve non-prod gates whose ONLY escalation is a blast-radius overrun (logged loudly)")
    ap.add_argument("--resume", default=None, metavar="RUN_DIR",
                    help="continue ticking an existing out/<run> directory instead of starting fresh")
    ap.add_argument("--tokn", default=None, help="tokn binary (default: $TOKN_BIN, out/bin, this folder, PATH)")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--max-ticks", type=int, default=40)
    ap.add_argument("--max-steps", type=int, default=0, help="--max-steps per role run (0 = runtime default)")
    ap.add_argument("--no-feature", action="store_true",
                    help="stop after the incident loop (skip the single-cell C2S feature request)")
    ap.add_argument("--c2s-url", default="",
                    help="loopback llama-server already serving a C2S-Scale GGUF for the final showcase "
                         "(default: launch one from $FACTORY_C2S_GGUF, or skip the showcase)")
    args = ap.parse_args(argv)

    load_dotenv(HERE / ".env")
    ctx = preflight(args.profile, args.tokn)
    if args.resume:
        run_dir = Path(args.resume).resolve()
        if not (run_dir / "seed" / "factory.yaml").is_file() or args.profile == "offline":
            raise SystemExit(f"--resume needs a live out/<run> directory with seed/factory.yaml: {run_dir}")
        args.resume = run_dir
    else:
        run_dir = OUT_ROOT / f"{datetime.now():%Y%m%d-%H%M%S}-{args.profile}"
        run_dir.mkdir(parents=True)
    log(f"profile={args.profile} tokn={ctx.get('tokn')} run_dir={run_dir}")
    if args.profile == "offline":
        return run_offline(args, ctx, run_dir)
    return run_live(args, ctx, run_dir)


if __name__ == "__main__":
    sys.exit(main())

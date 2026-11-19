"""Headless `tokn agent-run` wrapper shared by the example scripts.

Configuration comes from the environment only:

    TOKN                    path to the tokn binary (default: `tokn` on PATH)
    TOKN_EXAMPLE_PROVIDER   model provider, e.g. anthropic or azure-openai (default: anthropic)
    TOKN_EXAMPLE_MODEL      model name, e.g. claude-opus-5-5 (default: claude-opus-5-5)
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def tokn_binary() -> str:
    return os.environ.get("TOKN", "tokn")


def model_args() -> list[str]:
    provider = os.environ.get("TOKN_EXAMPLE_PROVIDER", "anthropic")
    model = os.environ.get("TOKN_EXAMPLE_MODEL", "claude-opus-5-5")
    return ["--model-provider", provider, "--model-name", model]


def require_tokn():
    if not shutil.which(tokn_binary()) and not Path(tokn_binary()).exists():
        raise SystemExit(
            f"tokn not found ({tokn_binary()!r}). Install TOKN v0.3.112+ and put it on PATH, "
            "or set TOKN to the full path of the binary."
        )


def run_agent(ws: Path, prompt: str, extra: list[str], max_steps: int = 14, timeout: int = 900) -> dict:
    """One headless run in workspace ws, parsed from its JSON result."""
    require_tokn()
    cmd = [tokn_binary(), "agent-run", *model_args(), "--repo-root", str(ws), "--output-format", "json",
           "--no-confirm", "--no-stream", "--mcp-disabled", "--no-update-check", "--run-timeout", "0",
           "--max-steps", str(max_steps), *extra, prompt]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, check=False, env={**os.environ, "GOWORK": "off"})
    out = {"exit": p.returncode, "seconds": round(time.time() - t0, 1), "stderr_tail": p.stderr[-2000:]}
    try:
        out["result"] = json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out["result"] = None
        out["stdout_tail"] = p.stdout[-2000:]
    out["gate_events"] = completion_gate_events(ws)
    return out


def completion_gate_events(ws: Path) -> list[str]:
    """First line of every completion_gate hold that the run logged."""
    events = []
    for log in sorted((ws / ".nospace" / "runs").glob("*.jsonl")):
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("event") == "completion_gate":
                events.append((row.get("content") or "").splitlines()[0][:200])
    return events

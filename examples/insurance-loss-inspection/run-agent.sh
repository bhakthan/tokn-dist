#!/usr/bin/env bash
# run-agent.sh - run the TOKN agent in insurance mode against the local coding model.
# The agent reads out/report.json, calls ins_loss_inspect and drafts a worklist.
# It cannot resolve referrals: that is a human-only action.
# Usage: ./run-agent.sh
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

# Only a non-routing model ID may be loaded from the repository .env file.
source ./load-safe-env.sh
load_safe_env .env TOKN_MODEL

problems=()

# 1. tokn binary
TOKN="${TOKN_BIN:-}"
if [ -z "$TOKN" ] && command -v tokn >/dev/null 2>&1; then TOKN="$(command -v tokn)"; fi
if [ -z "$TOKN" ]; then
  problems+=("Missing: tokn binary (not found on PATH).
  Why:   this script runs the TOKN agent loop.
  Fix:   download tokn from https://github.com/bhakthan/tokn-dist/releases/latest
         and put it on PATH, or set TOKN_BIN to its full path.")
fi

# 2. TOKN_MODEL
MODEL="${TOKN_MODEL:-}"
case "$MODEL" in ''|'<'*'>') problems+=("Missing: TOKN_MODEL. Set it in .env to the model id your coding server reports.") ;; esac

# 3. curl
if ! command -v curl >/dev/null 2>&1; then
  problems+=("Missing: curl (needed for the health check). Install it: brew install curl (macOS) or sudo apt install curl (Debian/Ubuntu).")
fi

# 4. Coding server responds at /health
BASE="${GGUF_SERVER_URL:-http://127.0.0.1:8083/v1}"
loopback_re='^(127\.[0-9]+\.[0-9]+\.[0-9]+|localhost|\[::1\])(:[0-9]+)?$'
authority="$(printf '%s' "$BASE" | sed -E 's#^[a-zA-Z]+://##; s#/.*$##')"
base_ok=0
if printf '%s' "$authority" | grep -Eq "$loopback_re"; then
  base_ok=1
else
  problems+=("GGUF_SERVER_URL must point to a loopback host for this local-only example. Set it in your trusted shell.")
fi
HEALTH="${BASE%/v1}/health"
HEALTH="${HEALTH%/}"
if [ "$base_ok" = 1 ] && command -v curl >/dev/null 2>&1; then
  if ! curl -s --max-time 5 "$HEALTH" 2>/dev/null | grep -q '"ok"'; then
    problems+=("Missing: coding model server is not responding at $HEALTH.
  Why:   TOKN sends the agent's model requests to this server (GGUF_SERVER_URL).
  Fix:   start it, for example:
         llama serve -hf <coder-hf-repo>:<quant> --host 127.0.0.1 --port 8083
         (./start-models.sh prints the commands for all three servers)")
  fi
fi

# 5. The report the agent reads
[ -f out/report.json ] || problems+=("Missing: out/report.json. Run ./run-inspection.sh first; the agent reads that report.")

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in ${problems[@]+"${problems[@]}"}; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

note "Preflight passed. Model: $MODEL  Server: $BASE"

# The repo root is out/, so the agent sees the report and nothing else (no photos, no .env).
args=(agent-run --model-provider gguf --model-name "$MODEL" --mode insurance
      --prompt-file task.md --repo-root . --max-steps 15 --run-timeout 0
      --output-format text --air-gap)

note "Running: $TOKN ${args[*]}"
set +e
"$TOKN" "${args[@]}" 2>&1 | tee out/agent-output.txt
code="${PIPESTATUS[0]}"
set -e

if grep -q 'Limited-capability mode:' out/agent-output.txt; then
  note "Limited-capability mode was active for this run (small coding model)."
fi

if [ "$code" -ne 0 ]; then fail "tokn exited with code $code. See out/agent-output.txt."; fi

if [ -f out/worklist.md ]; then
  note "Worklist written: out/worklist.md. Read it, then review each referral yourself."
else
  fail "The agent finished but did not write out/worklist.md. Small models sometimes skip a step; see out/agent-output.txt and try again."
fi

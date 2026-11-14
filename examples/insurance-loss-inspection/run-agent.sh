#!/usr/bin/env bash
# run-agent.sh - run the TOKN agent in insurance mode against the local coding model.
# The agent reads out/report.json, calls ins_loss_inspect and drafts a worklist.
# It cannot resolve referrals: that is a human-only action.
# Usage: ./run-agent.sh
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

# Load .env without overriding shell variables. TOKN_INSPECT_* and SYSTEMONE_* are skipped.
if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|\#*|*[!=]*) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    key="$(printf '%s' "$key" | tr -d '[:space:]')"
    val="$(printf '%s' "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//')"
    case "$key" in SYSTEMONE_*|TOKN_INSPECT_*) continue ;; esac
    if [ -z "${!key:-}" ]; then export "$key=$val"; fi
  done < .env
fi

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
HEALTH="${BASE%/v1}/health"
HEALTH="${HEALTH%/}"
if command -v curl >/dev/null 2>&1; then
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

#!/usr/bin/env bash
# run-local.sh - run the TOKN sample task against a local llama.cpp server.
# Usage: ./run-local.sh [--system-one]
set -u
cd "$(dirname "$0")" || exit 1

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

SYSTEM_ONE=0
[ "${1:-}" = "--system-one" ] && SYSTEM_ONE=1

# Load .env without overriding shell variables. SYSTEMONE_* keys are skipped:
# they must be set in the shell.
if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|\#*|*[!=]*) continue ;; esac
    key="${line%%=*}"; val="${line#*=}"
    key="$(printf '%s' "$key" | tr -d '[:space:]')"
    val="$(printf '%s' "$val" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^"//' -e 's/"$//')"
    case "$key" in SYSTEMONE_*) continue ;; esac
    if [ -z "${!key:-}" ]; then export "$key=$val"; fi
  done < .env
fi

problems=()
loopback_re='^(127\.[0-9]+\.[0-9]+\.[0-9]+|localhost|\[::1\])(:[0-9]+)?$'

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
case "$MODEL" in ''|'<'*'>') problems+=("Missing: TOKN_MODEL. Set it in .env to the model id your llama.cpp server reports.") ;; esac

# 3. curl
if ! command -v curl >/dev/null 2>&1; then
  problems+=("Missing: curl (needed for the health check). Install it with your package manager, e.g. brew install curl or sudo apt install curl.")
fi

# 4. llama.cpp server health
BASE="${GGUF_SERVER_URL:-http://127.0.0.1:8080/v1}"
HEALTH="${BASE%/v1}/health"
HEALTH="${HEALTH%/}"
if command -v curl >/dev/null 2>&1; then
  if ! curl -s --max-time 5 "$HEALTH" 2>/dev/null | grep -q '"ok"'; then
    problems+=("Missing: llama.cpp server is not responding at $HEALTH.
  Why:   TOKN sends model requests to this server (GGUF_SERVER_URL).
  Fix:   start it, for example:
         llama-server -hf <hf-repo>:<quant> --host 127.0.0.1 --port 8080 -c 32768
         Install llama.cpp: brew install llama.cpp (macOS), or build from
         https://github.com/ggml-org/llama.cpp (Linux).")
  fi
fi

# 5. Optional System One checks
if [ "$SYSTEM_ONE" = 1 ]; then
  for v in SYSTEMONE_BACKEND SYSTEMONE_ALLOW_LOCAL SYSTEMONE_BASE_URL SYSTEMONE_MODEL; do
    [ -z "${!v:-}" ] && problems+=("Missing: $v. Set it in your shell (not .env) before using --system-one.")
  done
  if [ -n "${SYSTEMONE_BASE_URL:-}" ]; then
    authority="$(printf '%s' "$SYSTEMONE_BASE_URL" | sed -E 's#^[a-zA-Z]+://##; s#/.*$##')"
    if ! printf '%s' "$authority" | grep -Eq "$loopback_re"; then
      problems+=("SYSTEMONE_BASE_URL must point to a loopback host (127.x, localhost or [::1]). Got: $SYSTEMONE_BASE_URL")
    elif command -v curl >/dev/null 2>&1; then
      s1_health="${SYSTEMONE_BASE_URL%/v1}/health"
      s1_health="${s1_health%/}"
      if ! curl -s --max-time 5 "$s1_health" 2>/dev/null | grep -q '"ok"'; then
        problems+=("Missing: System One decision server is not responding at $s1_health. Start a second llama.cpp server on that port.")
      fi
    fi
  fi
fi

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in "${problems[@]}"; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

note "Preflight passed. Model: $MODEL  Server: $BASE"

args=(agent-run --model-provider gguf --model-name "$MODEL" --prompt-file task.md
      --repo-root ./workspace --max-steps 15 --run-timeout 0 --output-format text)
[ "$SYSTEM_ONE" = 1 ] && args+=(--system-one --no-confirm)

note "Running: $TOKN ${args[*]}"
"$TOKN" "${args[@]}" 2>&1 | tee run-output.txt
code="${PIPESTATUS[0]}"

if grep -q 'Limited-capability mode:' run-output.txt; then
  note "Limited-capability mode was active for this run."
fi

note "Checking the result..."
python3 check.py
check=$?
if [ "$code" -ne 0 ]; then printf '[!] tokn exited with code %s. See run-output.txt.\n' "$code" >&2; exit "$code"; fi
exit "$check"

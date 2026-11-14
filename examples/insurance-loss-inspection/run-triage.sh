#!/usr/bin/env bash
# run-triage.sh - build a triage request from out/report.json and ask the local decision model.
# Usage: ./run-triage.sh
# The request holds only the inspection summary, never the photos. Output: out/triage-response.json.
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

# Load .env without overriding shell variables. SYSTEMONE_* keys are skipped on purpose.
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
  problems+=("Missing: tokn binary (not found on PATH). Download v0.3.96 or later from https://github.com/bhakthan/tokn-dist/releases/latest, or set TOKN_BIN.")
fi

# 2. Python 3.10+ for make-triage-request.py (standard library only)
PY=""
for cand in python3 python; do
  if command -v "$cand" >/dev/null 2>&1 && "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$cand"; break
  fi
done
if [ -z "$PY" ]; then
  problems+=("Missing: Python 3.10 or later (builds the triage request). Install: brew install python (macOS) or sudo apt install python3 (Debian/Ubuntu).")
fi

# 3. The report from run-inspection
[ -f out/report.json ] || problems+=("Missing: out/report.json. Run ./run-inspection.sh first.")

# 4. Decision model settings (shell only)
[ "${SYSTEMONE_BACKEND:-}" = "compatible" ] || problems+=("Missing: SYSTEMONE_BACKEND=compatible. Set it in your shell (not .env).")
[ "${SYSTEMONE_ALLOW_LOCAL:-}" = "1" ] || problems+=("Missing: SYSTEMONE_ALLOW_LOCAL=1. Set it in your shell (not .env).")
case "${SYSTEMONE_MODEL:-}" in ''|'<'*'>') problems+=("Missing: SYSTEMONE_MODEL, for example clef-flash (set in your shell).") ;; esac
S1="${SYSTEMONE_BASE_URL:-}"
if [ -z "$S1" ]; then
  problems+=("Missing: SYSTEMONE_BASE_URL, for example http://127.0.0.1:8082/v1 (set in your shell).")
else
  authority="$(printf '%s' "$S1" | sed -E 's#^[a-zA-Z]+://##; s#/.*$##')"
  if ! printf '%s' "$authority" | grep -Eq "$loopback_re"; then
    problems+=("SYSTEMONE_BASE_URL must point to a loopback host for this example (127.x, localhost or [::1]). Got: $S1")
  elif command -v curl >/dev/null 2>&1; then
    s1_health="${S1%/v1}/health"; s1_health="${s1_health%/}"
    if ! curl -s --max-time 5 "$s1_health" 2>/dev/null | grep -q '"ok"'; then
      problems+=("Missing: the decision server (Clef-Flash) is not responding at $s1_health. Start it on port 8082: llama serve -hf ggml-org/Clef-Flash-GGUF --host 127.0.0.1 --port 8082 -b 2048 -ub 2048")
    fi
  else
    problems+=("Missing: curl (health check). Install it: brew install curl (macOS) or sudo apt install curl (Debian/Ubuntu).")
  fi
fi

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in ${problems[@]+"${problems[@]}"}; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

note "Preflight passed. Decision model: $SYSTEMONE_MODEL at $S1"

# Step 1: build the request (summary only)
"$PY" make-triage-request.py || fail "make-triage-request.py failed."

# Step 2: the decision layer's own status (no decision call)
"$TOKN" system-one status || fail "tokn system-one status reports a problem. Read the output above."

# Step 3: the three typed questions. Do NOT add --air-gap here: it disables System One.
note "Asking the decision model (advisory only)..."
"$TOKN" system-one evaluate --file out/triage-request.json | tee out/triage-response.json \
  || fail "tokn system-one evaluate failed. See the message above."
note "Wrote out/triage-response.json. Advisory only: a licensed adjuster decides."

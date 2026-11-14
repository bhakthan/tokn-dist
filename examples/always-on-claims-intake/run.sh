#!/usr/bin/env bash
# run.sh - run the always-on claims intake example end to end (macOS and Linux).
# Usage: ./run.sh [--local] [--reset]
#   --local   use a llama.cpp server on 127.0.0.1:8080 instead of Azure OpenAI (implies --airgap)
#   --reset   first delete state/, workspace/.nospace/ and workspace/.tokn/ (generated, git-ignored)
# Without --local this makes model calls.
set -o pipefail
cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
AGENT=claims-intake
WS="$HERE/workspace"
STATE="$HERE/state"
LOCAL=0
RESET=0

for arg in "$@"; do
  case "$arg" in
    --local) LOCAL=1 ;;
    --reset) RESET=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

note() { printf '[*] %s\n' "$1"; }
abort() { printf '[!] %s\n' "$1" >&2; rm -rf "$STATE"; exit 1; }

# 1. Preflight: every missing dependency is listed before anything runs.
problems=()
TOKN="${TOKN_BIN:-}"
if [ -z "$TOKN" ]; then TOKN="$(command -v tokn 2>/dev/null)"; fi
if [ -z "$TOKN" ] || [ ! -x "$TOKN" ]; then
  problems+=("Missing: the tokn binary (v0.3.99 or later). Download it from https://github.com/bhakthan/tokn-dist/releases/latest, put it on PATH, or set TOKN_BIN.")
elif ! "$TOKN" always-on --help >/dev/null 2>&1; then
  problems+=("Old tokn: $TOKN has no 'always-on' command. Install v0.3.99 or later.")
fi

PY=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  problems+=("Missing: Python 3.10 or later (runs check.py; standard library only). Install: brew install python (macOS) or sudo apt install python3 (Linux).")
fi

if [ "$LOCAL" = 1 ]; then
  if ! curl -fsS -m 3 http://127.0.0.1:8080/v1/models >/dev/null 2>&1; then
    problems+=("Missing: a llama.cpp server on http://127.0.0.1:8080/v1. Start llama-server as described in the README (Local variant).")
  fi
  CFG="config/claims-intake.local.yaml"
  AIR=(--airgap)
else
  [ -n "${AZURE_OPENAI_ENDPOINT:-}" ] || problems+=("AZURE_OPENAI_ENDPOINT is not set in this shell. Export your Azure OpenAI resource endpoint (README step 1). It is not read from .env.")
  [ -n "${AZURE_OPENAI_DEPLOYMENT:-}" ] || problems+=("AZURE_OPENAI_DEPLOYMENT is not set in this shell (for example gpt-6-astra).")
  [ "${AZURE_OPENAI_USE_DEFAULT_CREDENTIAL:-}" = "true" ] || problems+=("AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true is not set in this shell (README step 1).")
  if ! command -v az >/dev/null 2>&1; then
    problems+=("Missing: Azure CLI. Install: brew install azure-cli (macOS) or curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash (Debian/Ubuntu). Then run az login.")
  elif ! az account show -o none >/dev/null 2>&1; then
    problems+=("Azure CLI is not signed in. Run az login, then rerun.")
  fi
  CFG="config/claims-intake.yaml"
  AIR=()
fi

if [ ${#problems[@]} -gt 0 ]; then
  printf 'Preflight failed; nothing was run. Fix these, then rerun:\n' >&2
  printf '  - %s\n' "${problems[@]}" >&2
  exit 1
fi

# 2. Start clean: a leftover state directory would mix this run into the last one.
if [ "$RESET" = 1 ]; then
  rm -rf "$STATE" "$WS/.nospace" "$WS/.tokn"
  note "reset: removed state/, workspace/.nospace/ and workspace/.tokn/"
fi
if [ -e "$STATE" ]; then
  printf '[!] state/ is left over from an earlier run. Rerun with --reset to start clean.\n' >&2
  exit 1
fi

# 3. Put the agent config where TOKN looks for it, and record the workspace before the run.
mkdir -p "$WS/.nospace/always-on" "$STATE"
cp "$CFG" "$WS/.nospace/always-on/$AGENT.yaml"
(
  cd "$WS" || exit 1
  find . -type f ! -path './.nospace/*' ! -path './.tokn/*' | LC_ALL=C sort | while IFS= read -r f; do
    if command -v sha256sum >/dev/null 2>&1; then h="$(sha256sum "$f" | cut -d' ' -f1)"; else h="$(shasum -a 256 "$f" | cut -d' ' -f1)"; fi
    printf '%s %s\n' "$h" "${f#./}"
  done
) > "$STATE/workspace-before.txt"

# 4. Doctor, enqueue, drain, record status, grade.
COMMON=(--repo-root "$WS" --state-dir "$STATE" --no-update-check)
toknc() { "$TOKN" always-on "$@"; }

note "doctor: checking every dependency"
toknc doctor "$AGENT" "${COMMON[@]}" "${AIR[@]}" || abort "doctor found missing items (listed above). Fix them, then rerun."

enqueue() { # file session key kind
  toknc enqueue "$AGENT" "${COMMON[@]}" --session "$2" --key "$3" --kind "$4" --body "@$HERE/events/$1" \
    || abort "enqueue failed for $1"
}
enqueue 01-fnol-CLM-1001.md       CLM-1001 fnol-CLM-1001     user_message
enqueue 02-fnol-CLM-1001-retry.md CLM-1001 fnol-CLM-1001     user_message
enqueue 03-followup-CLM-1001.md   CLM-1001 followup-CLM-1001 user_message
enqueue 04-fnol-CLM-1002.md       CLM-1002 fnol-CLM-1002     user_message
enqueue 05-portal-webhook.json    portal-1 portal-1          webhook
note "enqueued 5 events (the second fnol-CLM-1001 is a retry with the same key)"

# --run-timeout 0: a drain of five events takes a few minutes; the global 30s default would stop it.
note "run --once: draining the inbox (this makes model calls)"
toknc run "$AGENT" "${COMMON[@]}" --once --run-timeout 0 "${AIR[@]}"
RUN_CODE=$?

toknc status "$AGENT" "${COMMON[@]}" --json --last 20 > "$STATE/status.json" 2>/dev/null
toknc status "$AGENT" "${COMMON[@]}" --last 20

"$PY" "$HERE/check.py"
CHECK_CODE=$?

if [ "$RUN_CODE" -ne 0 ] || [ "$CHECK_CODE" -ne 0 ]; then exit 1; fi
exit 0

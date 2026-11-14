#!/usr/bin/env bash
# run.sh - run the two-desk claims example end to end (macOS and Linux).
# Usage: ./run.sh [--fresh]
#   --fresh   first delete state/ and the generated .nospace/ and .tokn/ folders under intake/ and review/
# Makes Azure OpenAI model calls. Nothing is committed to git.
set -o pipefail
cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
INTAKE=claims-intake
REVIEW=coverage-review
INTAKE_WS="$HERE/intake"
REVIEW_WS="$HERE/review"
STATE="$HERE/state"
INTAKE_STATE="$STATE/$INTAKE"
REVIEW_STATE="$STATE/$REVIEW"
MODEL=gpt-6-astra
FRESH=0

for arg in "$@"; do
  case "$arg" in
    --fresh) FRESH=1 ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

note() { printf '[*] %s\n' "$1"; }
abort() { printf '[!] %s\n' "$1" >&2; exit 1; }

# 1. Preflight: every missing dependency is listed before anything runs.
problems=()
TOKN="${TOKN_BIN:-}"
if [ -z "$TOKN" ]; then TOKN="$(command -v tokn 2>/dev/null)"; fi
if [ -z "$TOKN" ] || [ ! -x "$TOKN" ]; then
  problems+=("Missing: the tokn binary (v0.3.100 or later). Download it from https://github.com/bhakthan/tokn-dist/releases/latest, put it on PATH, or set TOKN_BIN.")
else
  ver="$("$TOKN" version 2>/dev/null | sed -n 's/^tokn \([0-9][0-9.]*\).*/\1/p' | head -n 1)"
  if [ -z "$ver" ]; then
    problems+=("Could not read the version of $TOKN. Handoff needs v0.3.100 or later.")
  else
    IFS=. read -r va vb vc <<<"$ver"
    if [ $(( va * 1000000 + vb * 1000 + ${vc:-0} )) -lt 3100 ]; then
      problems+=("Old tokn: $TOKN is $ver. Handoff needs v0.3.100 or later (same download as above).")
    fi
  fi
  if ! "$TOKN" always-on --help >/dev/null 2>&1; then
    problems+=("Old tokn: $TOKN has no 'always-on' command. Install v0.3.100 or later.")
  fi
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

if ! command -v git >/dev/null 2>&1; then
  problems+=("Missing: git (each desk folder is its own git repository). Install: xcode-select --install (macOS) or sudo apt install git (Linux).")
fi

[ -n "${AZURE_OPENAI_ENDPOINT:-}" ] || problems+=("AZURE_OPENAI_ENDPOINT is not set in this shell. Export your Azure OpenAI resource endpoint (README step 1). It is not read from .env.")
if [ -z "${AZURE_OPENAI_DEPLOYMENT:-}" ]; then
  problems+=("AZURE_OPENAI_DEPLOYMENT is not set in this shell. Set it to $MODEL (the model.model in both configs).")
elif [ "$AZURE_OPENAI_DEPLOYMENT" != "$MODEL" ]; then
  problems+=("AZURE_OPENAI_DEPLOYMENT is '$AZURE_OPENAI_DEPLOYMENT' but both configs use '$MODEL'. Set it to $MODEL, or edit model.model in config/claims-intake.yaml and config/coverage-review.yaml.")
fi
[ "${AZURE_OPENAI_USE_DEFAULT_CREDENTIAL:-}" = "true" ] || problems+=("AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true is not set in this shell (README step 1).")
if ! command -v az >/dev/null 2>&1; then
  problems+=("Missing: Azure CLI. Install: brew install azure-cli (macOS) or curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash (Debian/Ubuntu). Then run az login.")
elif ! az account show -o none >/dev/null 2>&1; then
  problems+=("Azure CLI is not signed in. Run az login, then rerun.")
fi

if [ "$FRESH" = 0 ] && [ -e "$STATE" ]; then
  problems+=("state/ is left over from an earlier run. Rerun with --fresh to clear it and start clean.")
fi

if [ ${#problems[@]} -gt 0 ]; then
  printf 'Preflight failed; nothing was run. Fix these, then rerun:\n' >&2
  printf '  - %s\n' "${problems[@]}" >&2
  exit 1
fi

# 2. Start clean: a leftover state directory would mix this run into the last one.
if [ "$FRESH" = 1 ]; then
  rm -rf "$STATE" "$INTAKE_WS/.nospace" "$INTAKE_WS/.tokn" "$REVIEW_WS/.nospace" "$REVIEW_WS/.tokn"
  note "fresh: removed state/ and the generated .nospace/ and .tokn/ folders"
fi

# 3. Set up both workspaces: git repository, ignore rule, and the desk config where TOKN looks for it.
setup_desk() { # name workspace config
  local name="$1" ws="$2" cfg="$3"
  if [ ! -e "$ws/.git" ]; then git init -q "$ws"; fi
  if [ ! -e "$ws/.gitignore" ]; then printf '.nospace/\n.tokn/\n' > "$ws/.gitignore"; fi
  mkdir -p "$ws/.nospace/always-on"
  cp "$HERE/$cfg" "$ws/.nospace/always-on/$name.yaml"
}
setup_desk "$INTAKE" "$INTAKE_WS" "config/claims-intake.yaml"
setup_desk "$REVIEW" "$REVIEW_WS" "config/coverage-review.yaml"
mkdir -p "$STATE"

# 4. Ticks, doctor and enqueue. Every command names the repo and the state dir explicitly.
tokn_do() { # verb agent workspace state_dir [extra...]
  local verb="$1" agent="$2" ws="$3" dir="$4"
  shift 4
  "$TOKN" always-on "$verb" "$agent" --repo-root "$ws" --state-dir "$dir" --no-update-check "$@"
}
tick() { # agent workspace state_dir label
  note "tick: $4 ($1) run --once"
  tokn_do run "$1" "$2" "$3" --once --run-timeout 0 || abort "$4 tick failed. Its output is above; state/ is kept for inspection. Fix the cause, then rerun with --fresh."
}

# Tick 0 starts both desks once, so each state directory exists before doctor checks the handoff peers.
tick "$REVIEW" "$REVIEW_WS" "$REVIEW_STATE" "tick 0"
tick "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" "tick 0"

note "doctor: checking every dependency, including the handoff peers"
tokn_do doctor "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" || abort "doctor found missing items for $INTAKE (listed above). Fix them, then rerun with --fresh."
tokn_do doctor "$REVIEW" "$REVIEW_WS" "$REVIEW_STATE" || abort "doctor found missing items for $REVIEW (listed above). Fix them, then rerun with --fresh."

for claim in CLM-2001 CLM-2002; do
  tokn_do enqueue "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" --session "$claim" --key "fnol-$claim" --body "@$HERE/events/$claim.md" \
    || abort "enqueue failed for $claim"
done
note "enqueued both first notices to $INTAKE"

tick "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" "tick 1"
tick "$REVIEW" "$REVIEW_WS" "$REVIEW_STATE" "tick 2"
tick "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" "tick 3"

# 5. Status for both desks, then grade.
"$TOKN" always-on status "$INTAKE" --repo-root "$INTAKE_WS" --state-dir "$INTAKE_STATE" --no-update-check --json --last 20 > "$INTAKE_STATE/status.json" 2>/dev/null
"$TOKN" always-on status "$REVIEW" --repo-root "$REVIEW_WS" --state-dir "$REVIEW_STATE" --no-update-check --json --last 20 > "$REVIEW_STATE/status.json" 2>/dev/null
tokn_do status "$INTAKE" "$INTAKE_WS" "$INTAKE_STATE" --last 20
tokn_do status "$REVIEW" "$REVIEW_WS" "$REVIEW_STATE" --last 20

exec "$PY" "$HERE/check.py"

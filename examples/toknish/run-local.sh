#!/usr/bin/env bash
# run-local.sh - preflight, then a local loopback federation run and a toknish-M bench.
# Usage: ./run-local.sh [MODEL] [PROVIDER]
set -euo pipefail
cd "$(dirname "$0")"

MODEL="${1:-qwen3:8b}"
PROVIDER="${2:-ollama}"
PORT="${PORT:-8099}"

fail() { printf '\033[31m[!] %s\033[0m\n' "$1" >&2; exit 1; }
note() { printf '\033[36m[*] %s\033[0m\n' "$1"; }

# Load only the documented API keys; never import routing or token values.
if [ -f .env ]; then
  while IFS= read -r line; do
    case "$line" in
      ''|\#*|[[:space:]]*) continue ;;
      *=*)
        key="${line%%=*}"; val="${line#*=}"
        case "$key" in
          OPENAI_API_KEY|ANTHROPIC_API_KEY)
            if [ -z "${!key:-}" ] && [ -n "$val" ]; then export "$key=$val"; fi ;;
          *) continue ;;
        esac ;;
    esac
  done < .env
fi

# Preflight every external command this path needs before creating the run folder.
missing=()
for cmd in tokn git date mkdir; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if [ "$PROVIDER" = "ollama" ]; then
  for cmd in ollama curl grep seq sleep; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
  done
fi
if [ -z "${TOKN_WORKER_TOKEN:-}" ]; then
  for cmd in head base64; do
    command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
  done
fi
if [ "${#missing[@]}" -gt 0 ]; then
  printf '[!] Missing required commands: %s\n' "${missing[*]}" >&2
  fail "This run needs TOKN, Git, and the listed provider/system tools. Install all of them using the OS-specific commands in README.md, then retry."
fi

# 1. TOKN on PATH.
note "tokn found: $(tokn version 2>/dev/null | head -n 1)"

# 2. Provider.
if [ "$PROVIDER" = "ollama" ]; then
  command -v ollama >/dev/null 2>&1 || fail "Ollama is not installed. macOS: brew install ollama. Linux: curl -fsSL https://ollama.com/install.sh | sh. Then run: ollama pull $MODEL"
  tags="$(curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags 2>/dev/null)" || fail "Ollama is installed but not running. Run 'ollama serve' (or open the Ollama app), then retry."
  printf '%s' "$tags" | grep -q "\"name\":\"$MODEL\"" || fail "Model '$MODEL' is not pulled. Run: ollama pull $MODEL"
  note "Ollama is running and '$MODEL' is available."
else
  note "Provider '$PROVIDER': set its API key in your trusted process environment; only documented key names are imported from an untracked .env."
fi

# 3. Shared token, created for this run only if not set (never written to disk).
case "${TOKN_WORKER_TOKEN:-}" in
  *'<'*'>'*|your*|YOUR*|placeholder*|PLACEHOLDER*)
    fail "TOKN_WORKER_TOKEN looks like a placeholder. Remove it and let the script generate a per-run token, or set a real token in the process environment." ;;
esac
if [ -z "${TOKN_WORKER_TOKEN:-}" ]; then
  TOKN_WORKER_TOKEN="$(head -c 32 /dev/urandom | base64)"
  export TOKN_WORKER_TOKEN
  note "Created a one-off TOKN_WORKER_TOKEN for this run."
fi
export TOKN_WORKER_TOKEN

TMP_BASE="${TMPDIR:-/tmp}"
case "$TMP_BASE" in
  /*) ;;
  *) fail "TMPDIR must be an absolute path outside the example checkout." ;;
esac
case "$TMP_BASE" in
  "$PWD"|"$PWD"/*) fail "TMPDIR points inside the example checkout; choose a system temp directory." ;;
esac
SCRATCH="$TMP_BASE/toknish-$(date +%Y%m%d%H%M%S)-$$"
EXAMPLE_DIR="$PWD"
REPO="$SCRATCH/repo"
W_STATE="$SCRATCH/worker-state"
L_STATE="$SCRATCH/leader-state"
mkdir -m 700 "$SCRATCH"
mkdir -p "$REPO" "$W_STATE" "$L_STATE"
note "Scratch workspace: $SCRATCH"
cd "$SCRATCH"
printf 'Sample repository for the toknish walkthrough.\n' > "$REPO/README.md"

# 4. Start the worker in the background and wait for it to listen.
tokn agent-worker --listen "127.0.0.1:$PORT" --worker-id w1 \
  --repo-root "$REPO" --provider "$PROVIDER" --model "$MODEL" \
  --federation-dir "$W_STATE" >"$SCRATCH/worker.log" 2>&1 &
WORKER_PID=$!
cleanup() { kill "$WORKER_PID" 2>/dev/null || true; }
trap cleanup EXIT

up=0
for _ in $(seq 1 30); do
  if (exec 3<>"/dev/tcp/127.0.0.1/$PORT") 2>/dev/null; then up=1; break; fi
  sleep 1
done
[ "$up" = 1 ] || fail "The worker did not start on 127.0.0.1:$PORT within 30 seconds. See $SCRATCH/worker.log."
note "Worker w1 is listening on 127.0.0.1:$PORT."

# 5. Leader run with toknish negotiated where offered.
tokn agent-leader --worker "w1=http://127.0.0.1:$PORT" --wire auto \
  --federation-dir "$L_STATE" \
  --prompt "List the files in the repository root and say which one looks like a README." \
  --out "$SCRATCH/results.json" || fail "The leader run failed. Check the output above."

# 6. Verify the audit chain for the newest session.
session="$(ls -1t "$L_STATE" 2>/dev/null | head -n 1 || true)"
if [ -n "$session" ]; then
  set +e
  tokn toknish audit "$session" --dir "$L_STATE"
  rc=$?
  set -e
  note "Audit exit code $rc (0 = clean)."
else
  note "No toknish session folder was written, so this run used plain JSON."
fi

# 7. Bench: the built-in smoke set, then the dataset.
note "Running the smoke bench..."
tokn tkm bench --provider "$PROVIDER" --model "$MODEL" --sample
note "Running the dataset bench (writes bench-report.json)..."
tokn tkm bench --provider "$PROVIDER" --model "$MODEL" --dataset "$EXAMPLE_DIR/dataset.json" --out "$SCRATCH/bench-report.json"
note "Done. Results remain in the printed scratch workspace for review."

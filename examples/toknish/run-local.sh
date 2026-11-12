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

# Load .env without overriding variables already set in the environment.
if [ -f .env ]; then
  while IFS= read -r line; do
    case "$line" in
      ''|\#*) continue ;;
      *=*)
        key="${line%%=*}"; val="${line#*=}"
        if [ -z "${!key:-}" ]; then export "$key=$val"; fi ;;
    esac
  done < .env
fi

# 1. TOKN on PATH.
command -v tokn >/dev/null 2>&1 || fail "tokn is not on your PATH. Install TOKN, open a new shell, and run 'tokn version'."
note "tokn found: $(tokn version 2>/dev/null | head -n 1)"

# 2. Provider.
if [ "$PROVIDER" = "ollama" ]; then
  command -v ollama >/dev/null 2>&1 || fail "Ollama is not installed. macOS: brew install ollama. Linux: curl -fsSL https://ollama.com/install.sh | sh. Then run: ollama pull $MODEL"
  tags="$(curl -fsS --max-time 5 http://127.0.0.1:11434/api/tags 2>/dev/null)" || fail "Ollama is installed but not running. Run 'ollama serve' (or open the Ollama app), then retry."
  printf '%s' "$tags" | grep -q "\"name\":\"$MODEL\"" || fail "Model '$MODEL' is not pulled. Run: ollama pull $MODEL"
  note "Ollama is running and '$MODEL' is available."
else
  note "Provider '$PROVIDER': make sure its API key is set in .env (see .env.example)."
fi

# 3. Shared token, created for this run only if not set (never written to disk).
if [ -z "${TOKN_WORKER_TOKEN:-}" ]; then
  TOKN_WORKER_TOKEN="$(head -c 32 /dev/urandom | base64)"
  export TOKN_WORKER_TOKEN
  note "Created a one-off TOKN_WORKER_TOKEN for this run."
fi
export TOKN_WORKER_TOKEN

SCRATCH="$PWD/scratch"
REPO="$SCRATCH/repo"
W_STATE="$SCRATCH/worker-state"
L_STATE="$SCRATCH/leader-state"
mkdir -p "$REPO" "$W_STATE" "$L_STATE"
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
tokn tkm bench --provider "$PROVIDER" --model "$MODEL" --dataset "$PWD/dataset.json" --out "$SCRATCH/bench-report.json"
note "Done. Results are in scratch/. Read the bench fields in README.md."

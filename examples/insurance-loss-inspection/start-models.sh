#!/usr/bin/env bash
# start-models.sh - preflight, then print (or with --start, launch) the three loopback llama.cpp servers.
#   port 8081  vision model (loss-inspect scorer)
#   port 8082  decision model, Clef-Flash (system-one triage)
#   port 8083  coding model (agent in insurance mode)
# Usage: ./start-models.sh           print the commands and check the setup
#        ./start-models.sh --start   also start the servers (logs go to out/logs)
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

# Load .env without overriding shell variables (only CODER_HF_MODEL is read from it here).
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

START=0
[ "${1:-}" = "--start" ] && START=1

problems=()

# 1. llama.cpp. Prefer llama-server (the name the other examples use); fall back to `llama serve`.
BIN=""
PREFIX=()
if command -v llama-server >/dev/null 2>&1; then
  BIN="$(command -v llama-server)"
elif command -v llama >/dev/null 2>&1; then
  BIN="$(command -v llama)"
  PREFIX=(serve)
else
  problems+=("Missing: llama.cpp (neither llama-server nor llama is on PATH).
  Why:   it serves the three local models over OpenAI-compatible HTTP.
  Fix:   macOS: brew install llama.cpp
         Linux: build from https://github.com/ggml-org/llama.cpp (docs/build.md),
                then put build/bin on PATH.
         Check with: llama-server --version")
fi

# 2. curl (port and health checks)
if ! command -v curl >/dev/null 2>&1; then
  problems+=("Missing: curl (port and health checks). Install it: brew install curl (macOS) or sudo apt install curl (Debian/Ubuntu).")
fi

# 3. The coding model is the only one without a fixed default.
CODER="${CODER_HF_MODEL:-}"
case "$CODER" in ''|'<'*'>')
  problems+=("Missing: CODER_HF_MODEL. Set it to the Hugging Face repo and quant of a coder GGUF, for example:
         export CODER_HF_MODEL=<hf-repo>:<quant>
  Why:   the coding model drives the TOKN agent in insurance mode (run-agent).
  Pick:  a Qwen coder GGUF that fits your memory (see the README hardware notes).") ;;
esac

NAMES=(vision decision coder)
PORTS=(8081 8082 8083)
HFS=("ggml-org/Qwen2.5-VL-3B-Instruct-GGUF" "ggml-org/Clef-Flash-GGUF" "$CODER")
# A decision model reads the whole request in one batch; 512 (the default) is too small.
EXTRAS=("" "-b 2048 -ub 2048" "")

# 4. Ports must be free before anything starts.
if command -v curl >/dev/null 2>&1; then
  for i in 0 1 2; do
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:${PORTS[$i]}/" 2>/dev/null || true)"
    if [ -n "$code" ] && [ "$code" != "000" ]; then
      problems+=("Port ${PORTS[$i]} is already in use (needed for the ${NAMES[$i]} model). Stop the program using it, or pick another port and update the .env / shell settings to match.")
    fi
  done
fi

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in ${problems[@]+"${problems[@]}"}; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

note "Preflight passed. Binary: $BIN"
note "Each server listens on 127.0.0.1 only."
for i in 0 1 2; do
  printf '\n  %s (port %s):\n    %s %s -hf %s --host 127.0.0.1 --port %s %s\n' \
    "${NAMES[$i]}" "${PORTS[$i]}" "$(basename "$BIN")" "${PREFIX[*]:-}" "${HFS[$i]}" "${PORTS[$i]}" "${EXTRAS[$i]}"
done
printf '\n'

if [ "$START" -eq 0 ]; then
  printf 'Nothing was started. To start all three, run: ./start-models.sh --start\n'
  printf 'Or start each one yourself in its own terminal (recommended on small GPUs; see the README).\n'
  exit 0
fi

mkdir -p out/logs
PIDS=()
for i in 0 1 2; do
  # shellcheck disable=SC2086 # EXTRAS is a deliberate word list of flags
  nohup "$BIN" ${PREFIX[@]+"${PREFIX[@]}"} -hf "${HFS[$i]}" --host 127.0.0.1 --port "${PORTS[$i]}" ${EXTRAS[$i]} \
    > "out/logs/${PORTS[$i]}.out.log" 2> "out/logs/${PORTS[$i]}.err.log" &
  PIDS+=("$!")
  note "Started ${NAMES[$i]} on port ${PORTS[$i]} (pid $!)."
done
printf '%s\n' "${PIDS[@]}" > out/logs/pids.txt

note "Waiting for health (the first start downloads each model, which can take a long time)..."
for i in 0 1 2; do
  ready=0
  for _ in $(seq 1 360); do
    if curl -s --max-time 3 "http://127.0.0.1:${PORTS[$i]}/health" 2>/dev/null | grep -q '"ok"'; then
      ready=1
      break
    fi
    sleep 5
  done
  if [ "$ready" -eq 1 ]; then
    note "${NAMES[$i]} on port ${PORTS[$i]} is healthy."
  else
    printf '[!] %s on port %s is not healthy yet. Read out/logs/%s.err.log.\n' "${NAMES[$i]}" "${PORTS[$i]}" "${PORTS[$i]}" >&2
  fi
done
printf '\nTo stop them later: kill the pids in out/logs/pids.txt.\n'

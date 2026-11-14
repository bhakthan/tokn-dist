#!/usr/bin/env bash
# run-inspection.sh - Loss Inspection on the three demo photos, then verify the report.
# Steps: check-sets -> status --probe --smoke -> run -> verify.
# Exit 3 from `run` means the report is complete and has adjuster referrals. That is a
# normal result for this example and counts as success.
# Usage: ./run-inspection.sh
set -euo pipefail
cd "$(dirname "$0")"

fail() { printf '[!] %s\n' "$1" >&2; exit 1; }
note() { printf '[*] %s\n' "$1"; }

# Load .env without overriding shell variables. TOKN_INSPECT_* and SYSTEMONE_* are skipped:
# they must be set in the shell (see .env.example).
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
loopback_re='^(127\.[0-9]+\.[0-9]+\.[0-9]+|localhost|\[::1\])(:[0-9]+)?$'

# Returns 0 when $1 >= $2 (dotted versions).
version_ge() {
  local a b c x y z
  IFS=. read -r a b c <<<"$1"
  IFS=. read -r x y z <<<"$2"
  [ "$a" -gt "$x" ] && return 0
  [ "$a" -lt "$x" ] && return 1
  [ "$b" -gt "$y" ] && return 0
  [ "$b" -lt "$y" ] && return 1
  [ "${c:-0}" -ge "${z:-0}" ]
}

# 1. tokn binary
TOKN="${TOKN_BIN:-}"
if [ -z "$TOKN" ] && command -v tokn >/dev/null 2>&1; then TOKN="$(command -v tokn)"; fi
if [ -z "$TOKN" ]; then
  problems+=("Missing: tokn binary (not found on PATH).
  Why:   this script runs tokn loss-inspect.
  Fix:   download tokn v0.3.96 or later from https://github.com/bhakthan/tokn-dist/releases/latest
         and put it on PATH, or set TOKN_BIN to its full path.")
fi

# 2. tokn version >= 0.3.96 (report_path for ins_loss_inspect is new in 0.3.96)
if [ -n "$TOKN" ]; then
  ver="$("$TOKN" version 2>&1 | grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' | head -n 1 || true)"
  if [ -z "$ver" ]; then
    note "Could not read the tokn version from 'tokn version'; continuing."
  elif ! version_ge "$ver" "0.3.96"; then
    problems+=("Old tokn: found $ver, need 0.3.96 or later. Download the latest release from https://github.com/bhakthan/tokn-dist/releases/latest")
  fi
fi

# 3. Vision scorer settings (shell only)
[ "${TOKN_INSPECT_SCORER:-}" = "logprob" ] || problems+=("Missing: TOKN_INSPECT_SCORER=logprob. Set it in your shell (not .env) before running.")
[ "${TOKN_INSPECT_ALLOW_LOCAL:-}" = "1" ] || problems+=("Missing: TOKN_INSPECT_ALLOW_LOCAL=1. Set it in your shell (not .env). It allows the loopback vision server.")
BASE="${TOKN_INSPECT_BASE_URL:-}"
MODEL="${TOKN_INSPECT_MODEL:-}"
base_ok=0
if [ -z "$BASE" ]; then
  problems+=("Missing: TOKN_INSPECT_BASE_URL, for example http://127.0.0.1:8081/v1 (set in your shell).")
else
  authority="$(printf '%s' "$BASE" | sed -E 's#^[a-zA-Z]+://##; s#/.*$##')"
  if printf '%s' "$authority" | grep -Eq "$loopback_re"; then
    base_ok=1
  else
    problems+=("TOKN_INSPECT_BASE_URL must point to a loopback host for this example (127.x, localhost or [::1]). Got: $BASE")
  fi
fi
case "$MODEL" in ''|'<'*'>') problems+=("Missing: TOKN_INSPECT_MODEL. Set it in your shell to the name your vision server reports at /v1/models.") ;; esac

# 4. The vision server answers and reports the model
if ! command -v curl >/dev/null 2>&1; then
  problems+=("Missing: curl (health check). Install it: brew install curl (macOS) or sudo apt install curl (Debian/Ubuntu).")
elif [ "$base_ok" = 1 ] && [ -n "$MODEL" ] && [ "${MODEL#<}" = "$MODEL" ]; then
  list="$(curl -s --max-time 5 "${BASE%/}/models" 2>/dev/null || true)"
  if [ -z "$list" ]; then
    problems+=("Missing: the vision server is not responding at ${BASE%/}/models.
  Why:   the loss-inspect scorer sends each damage crop to it.
  Fix:   start it, for example:
         llama serve -hf ggml-org/Qwen2.5-VL-3B-Instruct-GGUF --host 127.0.0.1 --port 8081
         (./start-models.sh prints the exact commands for all three servers)")
  elif ! printf '%s' "$list" | grep -qF "$MODEL"; then
    problems+=("TOKN_INSPECT_MODEL '$MODEL' is not in the server's /v1/models list. Server says: $list")
  fi
fi

# 5. Demo inputs
for f in photos/suv-front.jpg photos/side-mirror.jpg photos/van-side.jpg; do
  [ -f "$f" ] || problems+=("Missing: $f. Run ./fetch-photos.sh first.")
done
for f in photos.json points.json; do
  [ -f "$f" ] || problems+=("Missing: $f (it ships with this example; re-download the folder).")
done

if [ "${#problems[@]}" -gt 0 ]; then
  printf 'Preflight found %d problem(s):\n\n' "${#problems[@]}" >&2
  for p in ${problems[@]+"${problems[@]}"}; do printf -- '- %s\n\n' "$p" >&2; done
  exit 1
fi

note "Preflight passed. Vision model: $MODEL at $BASE"

# Step 1: the check set the run uses
"$TOKN" loss-inspect check-sets auto-physical-damage || fail "check-sets failed."

# Step 2: prove the scorer returns logprobs with image input before the run
note "Probing the vision model (status --probe --smoke)..."
"$TOKN" loss-inspect status --probe --smoke || fail "The scorer is not ready. Read the problems above, fix them, and re-run."

# Step 3: the inspection itself. --air-gap refuses any scorer that is not on this machine.
mkdir -p out
note "Running the inspection (49 records: 7 damage points x 7 checks)..."
set +e
"$TOKN" loss-inspect run --photos photos.json --points points.json --outlines none --air-gap \
  --claim-ref CLM-DEMO-0001 --out out/report.json --force
code=$?
set -e
case "$code" in
  0) note "Every record is corroborated or clear." ;;
  3) note "Report complete. Adjuster referrals exist (exit 3). This is expected without calibration and outlines; see the README." ;;
  *) fail "tokn loss-inspect run failed with exit code $code." ;;
esac

# Step 4: recompute every record and check the digest
"$TOKN" loss-inspect verify --report out/report.json || fail "verify failed. The report was altered or is inconsistent."
note "Verified: out/report.json is internally consistent. Next: python3 check.py"

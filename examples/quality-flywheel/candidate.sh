#!/usr/bin/env bash
# Inference candidate for `tokn flywheel run --candidate-cmd "bash candidate.sh"`.
# Reads one case's input on stdin, runs it through `tokn agent-run` against the
# provider you configured, and prints that run's final answer on stdout.
# Each invocation gets its own folder under scratch/, so answers never mix.
# Only the final `result` of a run whose status is "success" is used; a failed,
# blocked or empty run exits 1, so the flywheel records a failed case instead of
# a fake pass. This script never grades: the dataset does that.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tokn_bin="${TOKN_BIN:-tokn}"
provider="${NOSPACE_MODEL_PROVIDER:-}"
model="${NOSPACE_MODEL_NAME:-}"

fail() { echo "candidate: $*" >&2; exit 1; }

command -v "$tokn_bin" >/dev/null 2>&1 || fail "tokn not found (set TOKN_BIN to the path of tokn)"
command -v python3 >/dev/null 2>&1 || fail "python3 not found (needed to read the run result)"
[ -n "$provider" ] || fail "NOSPACE_MODEL_PROVIDER is not set (see README step 2)"
[ -n "$model" ] || fail "NOSPACE_MODEL_NAME is not set (see README step 2)"

mkdir -p "$here/scratch"
repo="$(mktemp -d "$here/scratch/run-XXXXXX")"
prompt_file="$repo/prompt.txt"
cat > "$prompt_file"
[ -s "$prompt_file" ] || fail "empty prompt on stdin"

# Plan mode: the task is a one-line answer, so the agent may not write or run anything.
"$tokn_bin" agent-run \
  --prompt-file "$prompt_file" \
  --repo-root "$repo" \
  --model-provider "$provider" \
  --model-name "$model" \
  --max-steps 2 \
  --permission-mode plan \
  --output-format json >"$repo/result.json" 2>"$repo/agent.err" \
  || fail "agent-run failed, see $repo/agent.err and $repo/result.json"

answer="$(python3 - "$repo/result.json" <<'PY'
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        res = json.load(fh)
except (OSError, ValueError) as exc:
    sys.exit(f"unreadable result: {exc}")
if res.get("status") != "success":
    sys.exit(f"run status {res.get('status')!r}: {res.get('errors')}")
print(str(res.get("result") or "").strip(), end="")
PY
)" || fail "no successful result in $repo/result.json"

[ -n "$answer" ] || fail "empty result in $repo/result.json (check provider auth)"
printf '%s' "$answer"
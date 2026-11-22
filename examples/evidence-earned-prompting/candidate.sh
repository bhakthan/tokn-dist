#!/usr/bin/env bash
# Model candidate for:
#   tokn earned-prompt run --scenario . --candidate-cmd "bash candidate.sh"
# Reads the assembled prompt on stdin, runs it through `tokn agent-run` against
# the provider you configured, and prints the model's SQL answer on stdout.
# Failures exit 1 with a message on stderr. This script never runs or grades the
# SQL: TOKN does that locally, against an in-memory copy of seed.sql.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tokn_bin="${TOKN_BIN:-tokn}"
provider="${NOSPACE_MODEL_PROVIDER:-}"
model="${NOSPACE_MODEL_NAME:-}"

fail() { echo "candidate: $*" >&2; exit 1; }

command -v "$tokn_bin" >/dev/null 2>&1 || fail "tokn not found (set TOKN_BIN to the path of tokn)"
command -v python3 >/dev/null 2>&1 || fail "python3 not found (needed to validate the final JSON result)"
[ -n "$provider" ] || fail "NOSPACE_MODEL_PROVIDER is not set (see README step 4)"
[ -n "$model" ] || fail "NOSPACE_MODEL_NAME is not set (see README step 4)"

run_id="$(date -u +%Y%m%dT%H%M%SZ)-$$"
repo="$here/scratch/runs/$run_id"
prompt_file="$repo/prompt.txt"
mkdir -p "$repo"
cat > "$prompt_file"
[ -s "$prompt_file" ] || fail "empty prompt on stdin"

"$tokn_bin" agent-run \
  --prompt-file "$prompt_file" \
  --repo-root "$repo" \
  --model-provider "$provider" \
  --model-name "$model" \
  --max-steps 2 \
  --output-format json \
  --quiet >"$repo/agent.out" 2>"$repo/agent.err" \
  || fail "agent-run failed, see $repo/agent.err"

answer="$(python3 - "$repo/agent.out" <<'PY'
import json, sys

try:
    with open(sys.argv[1], encoding="utf-8") as fh:
        result = json.load(fh)
except (OSError, ValueError) as exc:
    raise SystemExit(f"invalid agent-run JSON result: {exc}")
if result.get("status") != "success" or result.get("exit_code") != 0:
    raise SystemExit("agent-run did not report terminal success")
answer = result.get("result")
if not isinstance(answer, str) or not answer.strip():
    raise SystemExit("successful agent-run result is empty")
print(answer.strip(), end="")
PY
)" || fail "agent-run did not produce a successful final result (see $repo/agent.err)"

[ -n "$answer" ] || fail "agent-run returned an empty final result"
printf '%s' "$answer"

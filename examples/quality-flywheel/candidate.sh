#!/usr/bin/env bash
# Inference candidate for `tokn flywheel run --candidate-cmd "bash candidate.sh"`.
# Reads one case's input on stdin, runs it through `tokn agent-run` against the
# provider you configured, and prints the model's final answer on stdout.
# Failures exit 1 with a message on stderr, so the flywheel records a failed case
# instead of a fake pass. This script never grades: the dataset does that.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
tokn_bin="${TOKN_BIN:-tokn}"
provider="${NOSPACE_MODEL_PROVIDER:-}"
model="${NOSPACE_MODEL_NAME:-}"
repo="$here/scratch"
prompt_file="$repo/prompt.txt"

fail() { echo "candidate: $*" >&2; exit 1; }

command -v "$tokn_bin" >/dev/null 2>&1 || fail "tokn not found (set TOKN_BIN to the path of tokn)"
command -v python3 >/dev/null 2>&1 || fail "python3 not found (needed to read the run log)"
[ -n "$provider" ] || fail "NOSPACE_MODEL_PROVIDER is not set (see README step 2)"
[ -n "$model" ] || fail "NOSPACE_MODEL_NAME is not set (see README step 2)"

mkdir -p "$repo"
cat > "$prompt_file"
[ -s "$prompt_file" ] || fail "empty prompt on stdin"

"$tokn_bin" agent-run \
  --prompt-file "$prompt_file" \
  --repo-root "$repo" \
  --model-provider "$provider" \
  --model-name "$model" \
  --max-steps 2 \
  --no-confirm \
  --quiet >"$repo/agent.out" 2>"$repo/agent.err" \
  || fail "agent-run failed, see $repo/agent.err"

# agent-run writes one JSON line per event to .nospace/runs/<timestamp>.jsonl.
run_log="$(ls -t "$repo"/.nospace/runs/*.jsonl 2>/dev/null | head -n 1 || true)"
[ -n "$run_log" ] || fail "no run log under $repo/.nospace/runs"

answer="$(python3 - "$run_log" <<'PY'
import json, sys

final = last = ""
with open(sys.argv[1], encoding="utf-8") as fh:
    for line in fh:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("role") != "assistant" or event.get("content") is None:
            continue
        last = str(event["content"])
        if event.get("event") == "final":
            final = last
print((final or last).strip(), end="")
PY
)"

[ -n "$answer" ] || fail "no assistant answer in $run_log (check provider auth)"
printf '%s' "$answer"

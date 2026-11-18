#!/usr/bin/env bash
# Let TOKN build the RNA-seq QC MCP server in ./work, then check it.
#   ./run-agent.sh                       # Claude Haiku 5.5 (default)
#   MODEL=claude-sonnet-5-5 ./run-agent.sh
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
MODEL="${MODEL:-claude-haiku-5-5}"
MAX_STEPS="${MAX_STEPS:-40}"

# Preflight: every dependency this flow needs, reported together.
missing=()
command -v tokn >/dev/null 2>&1 || missing+=("tokn    - builds the server. Install: https://github.com/bhakthan/tokn-dist/releases (put tokn on PATH)")
command -v python3 >/dev/null 2>&1 || missing+=("python3 - runs the data generator, the server and check.py. Install Python 3.10+ (macOS: brew install python; Debian/Ubuntu: sudo apt install python3)")
if [ ${#missing[@]} -gt 0 ]; then
  printf 'Missing dependencies:\n'; printf '  %s\n' "${missing[@]}"; exit 2
fi

# Load .env without overriding variables already set.
if [ -f "$here/.env" ]; then
  while IFS='=' read -r k v; do
    [[ "$k" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    if [ -z "${!k:-}" ]; then v="${v%$'\r'}"; v="${v%\"}"; v="${v#\"}"; export "$k=$v"; fi
  done < "$here/.env"
fi
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in, then re-run."; exit 2
fi

# Fresh working copy: the agent sees the request and the data, never check.py.
rm -rf "$here/work"; mkdir -p "$here/work"
python3 "$here/make_data.py" >/dev/null
cp -r "$here/data" "$here/task.md" "$here/work/"

set +e
(cd "$here/work" && tokn agent-run --model-provider anthropic --model-name "$MODEL" \
  --repo-root . --prompt-file task.md \
  --max-steps "$MAX_STEPS" --no-confirm --mcp-disabled)
echo; echo "agent exit code: $?"; echo
set -e

python3 "$here/check.py" "$here/work"

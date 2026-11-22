#!/usr/bin/env bash
# Let TOKN build the RNA-seq QC MCP server in a fresh work dir, then check it.
#   ./run-agent.sh                         # Claude Haiku 5.5, interactive approvals
#   MODEL=claude-sonnet-5.5 ./run-agent.sh
#   WORK_DIR=~/rnaseq-mcp-work ./run-agent.sh   # a new folder of your choice (must not exist)
#   UNATTENDED=1 ./run-agent.sh            # opt-in: auto-approve every tool call (throwaway machine/dir only)
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
MODEL="${MODEL:-claude-haiku-5.5}"
MAX_STEPS="${MAX_STEPS:-40}"

# Preflight: every dependency this flow needs, reported together.
missing=()
command -v tokn >/dev/null 2>&1 || missing+=("tokn    - builds the server. Install: https://github.com/bhakthan/tokn-dist/releases (put tokn on PATH)")
command -v python3 >/dev/null 2>&1 || missing+=("python3 - runs the data generator, the server and check.py. Install Python 3.10+ (macOS: brew install python; Debian/Ubuntu: sudo apt install python3)")
if [ ${#missing[@]} -gt 0 ]; then
  printf 'Missing dependencies:\n'; printf '  %s\n' "${missing[@]}"; exit 2
fi

# Optionally load ANTHROPIC_API_KEY from .env, without overriding a value already set.
# Nothing else is read from the file: endpoint and routing settings such as
# ANTHROPIC_BASE_URL must come from your trusted shell, never from a repository file.
if [ -f "$here/.env" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    line="${line%$'\r'}"
    case "$line" in ''|'#'*) continue ;; esac
    k="${line%%=*}"; v="${line#*=}"
    k="${k#"${k%%[![:space:]]*}"}"; k="${k%"${k##*[![:space:]]}"}"
    [ "$k" = "ANTHROPIC_API_KEY" ] || continue
    v="${v#"${v%%[![:space:]]*}"}"; v="${v%"${v##*[![:space:]]}"}"
    v="${v%\"}"; v="${v#\"}"
    export ANTHROPIC_API_KEY="$v"
  done < "$here/.env"
fi
case "${ANTHROPIC_API_KEY:-}" in
  ''|your-key-here|'<'*) echo "ANTHROPIC_API_KEY is not set. Set it in your shell (see README Setup), then re-run."; exit 2 ;;
esac

# Fresh working copy: the agent sees the request and the data, never check.py.
if [ -n "${WORK_DIR:-}" ]; then
  if [ -e "$WORK_DIR" ]; then echo "WORK_DIR '$WORK_DIR' already exists. Choose a new folder."; exit 2; fi
  work="$WORK_DIR"
else
  work="$here/work"
  # A previous work/ is renamed, not deleted, so a failed run's evidence survives.
  if [ -e "$work" ]; then mv "$work" "$here/work.prev-$(date +%Y%m%d-%H%M%S)"; fi
fi
mkdir -p "$work"
python3 "$here/make_data.py" >/dev/null
cp -r "$here/data" "$here/task.md" "$work/"
echo "work dir: $work"

approve=(--permission-mode default)
if [ "${UNATTENDED:-}" = "1" ]; then
  echo "UNATTENDED=1: every tool call is auto-approved."
  approve=(--no-confirm)
fi

set +e
(cd "$work" && tokn agent-run --model-provider anthropic --model-name "$MODEL" \
  --repo-root . --prompt-file task.md \
  --max-steps "$MAX_STEPS" "${approve[@]}" --mcp-disabled)
agent_exit=$?
set -e
echo; echo "agent exit code: $agent_exit"; echo

# Overall success needs both the agent run and the independent check to pass.
set +e
python3 "$here/check.py" "$work"
check_exit=$?
set -e
echo "work dir kept for inspection: $work"
if [ "$agent_exit" -ne 0 ]; then exit "$agent_exit"; fi
exit "$check_exit"

#!/bin/sh
# PostToolUse: append one line per completed file-write call to a local audit file.
# Only the tool name and path are logged, not file contents.
audit_dir="$CLAUDE_PROJECT_DIR/.tokn-audit"
mkdir -p "$audit_dir"
path=$(printf '%s' "$CLAUDE_TOOL_INPUT" | sed -n 's/.*"path" *: *"\([^"]*\)".*/\1/p')
ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s tool=%s path=%s\n' "$ts" "$CLAUDE_TOOL_NAME" "$path" >> "$audit_dir/hook-audit.log"
exit 0

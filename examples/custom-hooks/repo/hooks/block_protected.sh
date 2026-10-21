#!/bin/sh
# PreToolUse: refuse file writes whose path is under protected/.
# TOKN passes the tool call as JSON in CLAUDE_TOOL_INPUT. Exit 2 blocks the call;
# stderr becomes the reason the model sees.
path=$(printf '%s' "$CLAUDE_TOOL_INPUT" | sed -n 's/.*"path" *: *"\([^"]*\)".*/\1/p')
path=$(printf '%s' "$path" | tr '\\' '/')
case "$path" in
  protected/*|*/protected/*)
    echo "blocked: writes under protected/ are not allowed ($path)" >&2
    exit 2 ;;
esac
exit 0

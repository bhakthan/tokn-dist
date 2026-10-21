# PreToolUse: refuse file writes whose path is under protected/.
# TOKN passes the tool call as JSON in $env:CLAUDE_TOOL_INPUT. Exit 2 blocks the call;
# stderr becomes the reason the model sees.
$path = ''
if ($env:CLAUDE_TOOL_INPUT) {
    try { $path = [string](($env:CLAUDE_TOOL_INPUT | ConvertFrom-Json).path) } catch { $path = '' }
}
$path = $path -replace '\\', '/'
if ($path -like 'protected/*' -or $path -like '*/protected/*') {
    [Console]::Error.WriteLine("blocked: writes under protected/ are not allowed ($path)")
    exit 2
}
exit 0

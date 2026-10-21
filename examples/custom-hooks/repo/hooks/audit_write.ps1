# PostToolUse: append one line per completed file-write call to a local audit file.
# Only the tool name and path are logged, not file contents.
$auditDir = Join-Path $env:CLAUDE_PROJECT_DIR '.tokn-audit'
New-Item -ItemType Directory -Force -Path $auditDir | Out-Null
$path = ''
if ($env:CLAUDE_TOOL_INPUT) {
    try { $path = [string](($env:CLAUDE_TOOL_INPUT | ConvertFrom-Json).path) } catch { $path = '' }
}
$ts = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ssZ')
Add-Content -Path (Join-Path $auditDir 'hook-audit.log') -Value "$ts tool=$env:CLAUDE_TOOL_NAME path=$path"
exit 0

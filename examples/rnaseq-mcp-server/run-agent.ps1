#requires -Version 7.0
# Let TOKN build the RNA-seq QC MCP server in .\work, then check it.
#   pwsh ./run-agent.ps1                      # Claude Haiku 5.5 (default)
#   pwsh ./run-agent.ps1 -Model claude-sonnet-5-5
param(
    [string]$Model = 'claude-haiku-5-5',
    [int]$MaxSteps = 40
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot

# Preflight: every dependency this flow needs, reported together.
$missing = @()
if (-not (Get-Command tokn -ErrorAction SilentlyContinue)) {
    $missing += 'tokn   - builds the server. Install: https://github.com/bhakthan/tokn-dist/releases (put tokn on PATH)'
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $missing += 'python - runs the data generator, the server and check.py. Install Python 3.10+: winget install Python.Python.3.12'
}
if ($missing) { Write-Host "Missing dependencies:`n  $($missing -join "`n  ")"; exit 2 }

# Load .env (KEY=value lines) without overriding variables already set.
$envFile = Join-Path $here '.env'
if (Test-Path $envFile) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$' -and -not [Environment]::GetEnvironmentVariable($Matches[1])) {
            [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim('"'))
        }
    }
}
if (-not $env:ANTHROPIC_API_KEY) {
    Write-Host 'ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in, then re-run.'
    exit 2
}

# Fresh working copy: the agent sees the request and the data, never check.py.
$work = Join-Path $here 'work'
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory $work | Out-Null
python (Join-Path $here 'make_data.py') | Out-Null
Copy-Item (Join-Path $here 'data') $work -Recurse
Copy-Item (Join-Path $here 'task.md') $work

Push-Location $work
try {
    tokn agent-run --model-provider anthropic --model-name $Model `
        --repo-root . --prompt-file task.md `
        --max-steps $MaxSteps --no-confirm --mcp-disabled
    $agentExit = $LASTEXITCODE
} finally { Pop-Location }
Write-Host "`nagent exit code: $agentExit`n"

python (Join-Path $here 'check.py') $work
exit $LASTEXITCODE

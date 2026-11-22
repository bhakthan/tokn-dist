#requires -Version 7.0
# Let TOKN build the RNA-seq QC MCP server in a fresh work dir, then check it.
#   pwsh ./run-agent.ps1                              # Claude Haiku 5.5, interactive approvals
#   pwsh ./run-agent.ps1 -Model claude-sonnet-5.5
#   pwsh ./run-agent.ps1 -WorkDir $HOME\rnaseq-mcp-work   # a new folder of your choice (must not exist)
#   pwsh ./run-agent.ps1 -Unattended                  # opt-in: auto-approve every tool call (throwaway machine/dir only)
param(
    [string]$Model = 'claude-haiku-5.5',
    [int]$MaxSteps = 40,
    [string]$WorkDir = '',
    [switch]$Unattended
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

# Optionally load ANTHROPIC_API_KEY from .env, without overriding a value already set.
# Nothing else is read from the file: endpoint and routing settings such as
# ANTHROPIC_BASE_URL must come from your trusted session, never from a repository file.
$envFile = Join-Path $here '.env'
if ((Test-Path $envFile) -and -not $env:ANTHROPIC_API_KEY) {
    foreach ($line in Get-Content $envFile) {
        if ($line -match '^\s*ANTHROPIC_API_KEY\s*=\s*(.*?)\s*$') {
            $env:ANTHROPIC_API_KEY = $Matches[1].Trim('"')
        }
    }
}
if (-not $env:ANTHROPIC_API_KEY -or $env:ANTHROPIC_API_KEY -eq 'your-key-here' -or $env:ANTHROPIC_API_KEY.StartsWith('<')) {
    Write-Host 'ANTHROPIC_API_KEY is not set. Set it in your session (see README Setup), then re-run.'
    exit 2
}

# Fresh working copy: the agent sees the request and the data, never check.py.
if ($WorkDir) {
    if (Test-Path $WorkDir) { Write-Host "-WorkDir '$WorkDir' already exists. Choose a new folder."; exit 2 }
    $work = $WorkDir
} else {
    $work = Join-Path $here 'work'
    # A previous work\ is renamed, not deleted, so a failed run's evidence survives.
    if (Test-Path $work) {
        Rename-Item $work ("work.prev-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    }
}
New-Item -ItemType Directory $work | Out-Null
$work = (Resolve-Path $work).Path
python (Join-Path $here 'make_data.py') | Out-Null
Copy-Item (Join-Path $here 'data') $work -Recurse
Copy-Item (Join-Path $here 'task.md') $work
Write-Host "work dir: $work"

$approve = @('--permission-mode', 'default')
if ($Unattended) {
    Write-Host '-Unattended: every tool call is auto-approved.'
    $approve = @('--no-confirm')
}

Push-Location $work
try {
    tokn agent-run --model-provider anthropic --model-name $Model `
        --repo-root . --prompt-file task.md `
        --max-steps $MaxSteps @approve --mcp-disabled
    $agentExit = $LASTEXITCODE
} finally { Pop-Location }
Write-Host "`nagent exit code: $agentExit`n"

# Overall success needs both the agent run and the independent check to pass.
python (Join-Path $here 'check.py') $work
$checkExit = $LASTEXITCODE
Write-Host "work dir kept for inspection: $work"
if ($agentExit -ne 0) { exit $agentExit }
exit $checkExit

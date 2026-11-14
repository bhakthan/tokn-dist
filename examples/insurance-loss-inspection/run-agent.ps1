# run-agent.ps1 - run the TOKN agent in insurance mode against the local coding model.
# The agent reads out/report.json, calls ins_loss_inspect and drafts a worklist.
# It cannot resolve referrals: that is a human-only action.
# Usage: ./run-agent.ps1
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

# Load .env without overriding the shell. TOKN_INSPECT_* and SYSTEMONE_* are skipped on purpose.
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#") -or -not $t.Contains("=")) { continue }
        $k, $v = $t.Split("=", 2)
        $k = $k.Trim(); $v = $v.Trim().Trim('"')
        if ($k.StartsWith("SYSTEMONE_") -or $k.StartsWith("TOKN_INSPECT_")) { continue }
        if (-not [Environment]::GetEnvironmentVariable($k)) { [Environment]::SetEnvironmentVariable($k, $v) }
    }
}

$problems = @()

# 1. tokn binary
$tokn = $env:TOKN_BIN
if (-not $tokn) {
    $cmd = Get-Command tokn -ErrorAction SilentlyContinue
    if ($cmd) { $tokn = $cmd.Source }
}
if (-not $tokn) {
    $problems += @"
Missing: tokn binary (not found on PATH).
  Why:   this script runs the TOKN agent loop.
  Fix:   download tokn from https://github.com/bhakthan/tokn-dist/releases/latest
         and put it on PATH, or set TOKN_BIN to its full path.
"@
}

# 2. TOKN_MODEL
$model = $env:TOKN_MODEL
if (-not $model -or $model -match '^<.*>$') {
    $problems += "Missing: TOKN_MODEL. Set it in .env to the model id your coding server reports."
}

# 3. curl (health check)
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    $problems += "Missing: curl.exe (needed for the health check). It ships with Windows 10 1803+ and recent Windows 11."
}

# 4. Coding server responds at /health
$base = if ($env:GGUF_SERVER_URL) { $env:GGUF_SERVER_URL } else { "http://127.0.0.1:8083/v1" }
$healthUrl = ($base -replace '/v1/?$', '') + "/health"
if ($curl) {
    $health = & curl.exe -s --max-time 5 $healthUrl 2>$null
    if ($LASTEXITCODE -ne 0 -or $health -notmatch '"ok"') {
        $problems += @"
Missing: coding model server is not responding at $healthUrl.
  Why:   TOKN sends the agent's model requests to this server (GGUF_SERVER_URL).
  Fix:   start it, for example:
         llama serve -hf <coder-hf-repo>:<quant> --host 127.0.0.1 --port 8083
         (./start-models.ps1 prints the commands for all three servers)
"@
    }
}

# 5. The report the agent reads
if (-not (Test-Path -LiteralPath "out/report.json")) {
    $problems += "Missing: out/report.json. Run ./run-inspection.ps1 first; the agent reads that report."
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight found $($problems.Count) problem(s):" -ForegroundColor Yellow
    $problems | ForEach-Object { Write-Host "- $_"; Write-Host "" }
    exit 1
}

Note "Preflight passed. Model: $model  Server: $base"

# The repo root is out/, so the agent sees the report and nothing else (no photos, no .env).
$runArgs = @(
    "agent-run",
    "--model-provider", "gguf",
    "--model-name", $model,
    "--mode", "insurance",
    "--prompt-file", "task.md",
    "--repo-root", ".",
    "--max-steps", "15",
    "--run-timeout", "0",
    "--output-format", "text",
    "--air-gap"
)

Note "Running: tokn $($runArgs -join ' ')"
$ErrorActionPreference = "Continue"
& $tokn @runArgs 2>&1 | Tee-Object -FilePath "out/agent-output.txt"
$code = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if (Select-String -Path "out/agent-output.txt" -Pattern "Limited-capability mode:" -Quiet) {
    Note "Limited-capability mode was active for this run (small coding model)."
}

if ($code -ne 0) { Fail "tokn exited with code $code. See out/agent-output.txt." }

if (Test-Path -LiteralPath "out/worklist.md") {
    Note "Worklist written: out/worklist.md. Read it, then review each referral yourself."
} else {
    Write-Host "[!] The agent finished but did not write out/worklist.md. Small models sometimes skip a step; see out/agent-output.txt and try again." -ForegroundColor Yellow
    exit 1
}
exit 0

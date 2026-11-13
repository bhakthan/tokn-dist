# run-local.ps1 - run the TOKN sample task against a local llama.cpp server.
# Usage: ./run-local.ps1 [-SystemOne]
param(
    [switch]$SystemOne
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

# Load .env without overriding variables already set in the shell.
# SYSTEMONE_* keys are skipped on purpose: they must come from the shell.
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#") -or -not $t.Contains("=")) { continue }
        $k, $v = $t.Split("=", 2)
        $k = $k.Trim(); $v = $v.Trim().Trim('"')
        if ($k.StartsWith("SYSTEMONE_")) { continue }
        if (-not [Environment]::GetEnvironmentVariable($k)) {
            [Environment]::SetEnvironmentVariable($k, $v)
        }
    }
}

$problems = @()
$loopbackPattern = '^(127\.\d+\.\d+\.\d+|localhost|\[::1\])(:\d+)?$'

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
    $problems += "Missing: TOKN_MODEL. Set it in .env to the model id your llama.cpp server reports."
}

# 3. curl (used for the health check)
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    $problems += "Missing: curl.exe (needed for the health check). It ships with Windows 10 1803+ and recent Windows 11."
}

# 4. llama.cpp server responds at /health
$base = if ($env:GGUF_SERVER_URL) { $env:GGUF_SERVER_URL } else { "http://127.0.0.1:8080/v1" }
$healthUrl = ($base -replace '/v1/?$', '') + "/health"
if ($curl) {
    $health = & curl.exe -s --max-time 5 $healthUrl 2>$null
    if ($LASTEXITCODE -ne 0 -or $health -notmatch '"ok"') {
        $problems += @"
Missing: llama.cpp server is not responding at $healthUrl.
  Why:   TOKN sends model requests to this server (GGUF_SERVER_URL).
  Fix:   start it, for example:
         llama-server -hf <hf-repo>:<quant> --host 127.0.0.1 --port 8080 -c 32768
         Install llama.cpp if needed:  winget install ggml.llamacpp
"@
    }
}

# 5. Optional System One checks
if ($SystemOne) {
    foreach ($v in "SYSTEMONE_BACKEND", "SYSTEMONE_ALLOW_LOCAL", "SYSTEMONE_BASE_URL", "SYSTEMONE_MODEL") {
        if (-not [Environment]::GetEnvironmentVariable($v)) {
            $problems += "Missing: $v. Set it in your shell (not .env) before using -SystemOne."
        }
    }
    $s1 = [Environment]::GetEnvironmentVariable("SYSTEMONE_BASE_URL")
    if ($s1) {
        $authority = try { ([Uri]$s1).Authority } catch { "" }
        if ($authority -notmatch $loopbackPattern) {
            $problems += "SYSTEMONE_BASE_URL must point to a loopback host (127.x, localhost or [::1]). Got: $s1"
        } elseif ($curl) {
            $s1Health = ($s1 -replace '/v1/?$', '') + "/health"
            $h = & curl.exe -s --max-time 5 $s1Health 2>$null
            if ($LASTEXITCODE -ne 0 -or $h -notmatch '"ok"') {
                $problems += "Missing: System One decision server is not responding at $s1Health. Start a second llama.cpp server on that port."
            }
        }
    }
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight found $($problems.Count) problem(s):" -ForegroundColor Yellow
    $problems | ForEach-Object { Write-Host "- $_"; Write-Host "" }
    exit 1
}

Note "Preflight passed. Model: $model  Server: $base"

$runArgs = @(
    "agent-run",
    "--model-provider", "gguf",
    "--model-name", $model,
    "--prompt-file", "task.md",
    "--repo-root", "./workspace",
    "--max-steps", "15",
    "--run-timeout", "0",
    "--output-format", "text"
)
if ($SystemOne) { $runArgs += @("--system-one", "--no-confirm") }

Note "Running: tokn $($runArgs -join ' ')"
$ErrorActionPreference = "Continue"
& $tokn @runArgs 2>&1 | Tee-Object -FilePath "run-output.txt"
$code = $LASTEXITCODE
$ErrorActionPreference = "Stop"

if (Select-String -Path "run-output.txt" -Pattern "Limited-capability mode:" -Quiet) {
    Note "Limited-capability mode was active for this run."
}

Note "Checking the result..."
& (Join-Path $PSScriptRoot "check.ps1")
$check = $LASTEXITCODE

if ($code -ne 0) { Write-Host "[!] tokn exited with code $code. See run-output.txt." -ForegroundColor Red; exit $code }
exit $check

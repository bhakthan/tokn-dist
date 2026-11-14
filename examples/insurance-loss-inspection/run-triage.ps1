# run-triage.ps1 - build a triage request from out/report.json and ask the local decision model.
# Usage: ./run-triage.ps1
# The request holds only the inspection summary, never the photos. Output: out/triage-response.json.
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

# Load .env without overriding the shell. SYSTEMONE_* keys are skipped on purpose.
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#") -or -not $t.Contains("=")) { continue }
        $k, $v = $t.Split("=", 2)
        $k = $k.Trim(); $v = $v.Trim().Trim('"')
        if ($k.StartsWith("SYSTEMONE_")) { continue }
        if (-not [Environment]::GetEnvironmentVariable($k)) { [Environment]::SetEnvironmentVariable($k, $v) }
    }
}

$problems = @()
$loopback = '^(127\.\d+\.\d+\.\d+|localhost|\[::1\])(:\d+)?$'

# 1. tokn binary
$tokn = $env:TOKN_BIN
if (-not $tokn) {
    $cmd = Get-Command tokn -ErrorAction SilentlyContinue
    if ($cmd) { $tokn = $cmd.Source }
}
if (-not $tokn) {
    $problems += "Missing: tokn binary (not found on PATH). Download v0.3.96 or later from https://github.com/bhakthan/tokn-dist/releases/latest, or set TOKN_BIN."
}

# 2. Python 3.10+ for make-triage-request.py (standard library only)
$pyCmd = $null
$pyPre = @()
$versionCheck = "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $versionCheck 2>$null
    if ($LASTEXITCODE -eq 0) { $pyCmd = "py"; $pyPre = @("-3") }
}
if (-not $pyCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c $versionCheck 2>$null
    if ($LASTEXITCODE -eq 0) { $pyCmd = "python" }
}
if (-not $pyCmd) {
    $problems += "Missing: Python 3.10 or later (builds the triage request). Install: winget install Python.Python.3.12, then open a new terminal."
}

# 3. The report from run-inspection
if (-not (Test-Path -LiteralPath "out/report.json")) {
    $problems += "Missing: out/report.json. Run ./run-inspection.ps1 first."
}

# 4. Decision model settings (shell only)
if ($env:SYSTEMONE_BACKEND -ne "compatible") { $problems += "Missing: SYSTEMONE_BACKEND=compatible. Set it in your shell (not .env)." }
if ($env:SYSTEMONE_ALLOW_LOCAL -ne "1") { $problems += "Missing: SYSTEMONE_ALLOW_LOCAL=1. Set it in your shell (not .env)." }
if (-not $env:SYSTEMONE_MODEL -or $env:SYSTEMONE_MODEL -match '^<.*>$') { $problems += "Missing: SYSTEMONE_MODEL, for example clef-flash (set in your shell)." }
$s1 = $env:SYSTEMONE_BASE_URL
if (-not $s1) {
    $problems += "Missing: SYSTEMONE_BASE_URL, for example http://127.0.0.1:8082/v1 (set in your shell)."
} else {
    $authority = ""
    try { $authority = ([Uri]$s1).Authority } catch { $authority = "" }
    if ($authority -notmatch $loopback) {
        $problems += "SYSTEMONE_BASE_URL must point to a loopback host for this example (127.x, localhost or [::1]). Got: $s1"
    } else {
        $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
        if (-not $curl) {
            $problems += "Missing: curl.exe (health check). It ships with Windows 10 1803+ and Windows 11."
        } else {
            $h = & curl.exe -s --max-time 5 (($s1 -replace '/v1/?$', '') + "/health") 2>$null
            if ($LASTEXITCODE -ne 0 -or $h -notmatch '"ok"') {
                $problems += "Missing: the decision server (Clef-Flash) is not responding at $(($s1 -replace '/v1/?$', ''))/health. Start it on port 8082: llama serve -hf ggml-org/Clef-Flash-GGUF --host 127.0.0.1 --port 8082 -b 2048 -ub 2048"
            }
        }
    }
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight found $($problems.Count) problem(s):" -ForegroundColor Yellow
    $problems | ForEach-Object { Write-Host "- $_"; Write-Host "" }
    exit 1
}

Note "Preflight passed. Decision model: $env:SYSTEMONE_MODEL at $s1"

# Step 1: build the request (summary only)
& $pyCmd @pyPre "make-triage-request.py"
if ($LASTEXITCODE -ne 0) { Fail "make-triage-request.py failed (exit $LASTEXITCODE)." }

# Step 2: the decision layer's own status (no decision call)
& $tokn system-one status
if ($LASTEXITCODE -ne 0) { Fail "tokn system-one status reports a problem. Read the output above." }

# Step 3: the three typed questions. Do NOT add --air-gap here: it disables System One.
Note "Asking the decision model (advisory only)..."
& $tokn system-one evaluate --file out/triage-request.json | Tee-Object -FilePath "out/triage-response.json"
if ($LASTEXITCODE -ne 0) { Fail "tokn system-one evaluate failed (exit $LASTEXITCODE). See the message above." }
Note "Wrote out/triage-response.json. Advisory only: a licensed adjuster decides."
exit 0

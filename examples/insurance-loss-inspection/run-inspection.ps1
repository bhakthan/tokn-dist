# run-inspection.ps1 - Loss Inspection on the three demo photos, then verify the report.
# Steps: check-sets -> status --probe --smoke -> run -> verify.
# Exit 3 from `run` means the report is complete and has adjuster referrals. That is a
# normal result for this example and counts as success.
# Usage: ./run-inspection.ps1
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

# Load .env without overriding the shell. TOKN_INSPECT_* and SYSTEMONE_* are skipped on
# purpose: they must be set in the shell (see .env.example).
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
$loopback = '^(127\.\d+\.\d+\.\d+|localhost|\[::1\])(:\d+)?$'

# 1. tokn binary
$tokn = $env:TOKN_BIN
if (-not $tokn) {
    $cmd = Get-Command tokn -ErrorAction SilentlyContinue
    if ($cmd) { $tokn = $cmd.Source }
}
if (-not $tokn) {
    $problems += @"
Missing: tokn binary (not found on PATH).
  Why:   this script runs tokn loss-inspect.
  Fix:   download tokn v0.3.96 or later from https://github.com/bhakthan/tokn-dist/releases/latest
         and put it on PATH, or set TOKN_BIN to its full path.
"@
}

# 2. tokn version >= 0.3.96 (report_path for ins_loss_inspect is new in 0.3.96)
if ($tokn) {
    $verOut = (& $tokn version 2>&1 | Out-String)
    if ($verOut -match '(\d+\.\d+\.\d+)') {
        if ([version]$matches[1] -lt [version]"0.3.96") {
            $problems += "Old tokn: found $($matches[1]), need 0.3.96 or later. Download the latest release from https://github.com/bhakthan/tokn-dist/releases/latest"
        }
    } else {
        Note "Could not read the tokn version from 'tokn version'; continuing."
    }
}

# 3. Vision scorer settings (shell only)
if ($env:TOKN_INSPECT_SCORER -ne "logprob") {
    $problems += "Missing: TOKN_INSPECT_SCORER=logprob. Set it in your shell (not .env) before running."
}
if ($env:TOKN_INSPECT_ALLOW_LOCAL -ne "1") {
    $problems += "Missing: TOKN_INSPECT_ALLOW_LOCAL=1. Set it in your shell (not .env). It allows the loopback vision server."
}
$base = $env:TOKN_INSPECT_BASE_URL
$model = $env:TOKN_INSPECT_MODEL
if (-not $base) {
    $problems += "Missing: TOKN_INSPECT_BASE_URL, for example http://127.0.0.1:8081/v1 (set in your shell)."
} else {
    $authority = ""
    try { $authority = ([Uri]$base).Authority } catch { $authority = "" }
    if ($authority -notmatch $loopback) {
        $problems += "TOKN_INSPECT_BASE_URL must point to a loopback host for this example (127.x, localhost or [::1]). Got: $base"
    }
}
if (-not $model -or $model -match '^<.*>$') {
    $problems += "Missing: TOKN_INSPECT_MODEL. Set it in your shell to the name your vision server reports at /v1/models."
}

# 4. curl, and the vision server answers and reports the model
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    $problems += "Missing: curl.exe (health check). It ships with Windows 10 1803+ and Windows 11."
} elseif ($base -and $model -and -not ($problems -match "TOKN_INSPECT_BASE_URL must")) {
    $list = & curl.exe -s --max-time 5 ($base.TrimEnd('/') + "/models") 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $list) {
        $problems += @"
Missing: the vision server is not responding at $base/models.
  Why:   the loss-inspect scorer sends each damage crop to it.
  Fix:   start it, for example:
         llama serve -hf ggml-org/Qwen2.5-VL-3B-Instruct-GGUF --host 127.0.0.1 --port 8081
         (./start-models.ps1 prints the exact commands for all three servers)
"@
    } elseif ($list -notmatch [regex]::Escape($model)) {
        $problems += "TOKN_INSPECT_MODEL '$model' is not in the server's /v1/models list. Server says: $list"
    }
}

# 5. Demo inputs
foreach ($f in "photos/suv-front.jpg", "photos/side-mirror.jpg", "photos/van-side.jpg") {
    if (-not (Test-Path -LiteralPath $f)) { $problems += "Missing: $f. Run ./fetch-photos.ps1 first." }
}
foreach ($f in "photos.json", "points.json") {
    if (-not (Test-Path -LiteralPath $f)) { $problems += "Missing: $f (it ships with this example; re-download the folder)." }
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight found $($problems.Count) problem(s):" -ForegroundColor Yellow
    $problems | ForEach-Object { Write-Host "- $_"; Write-Host "" }
    exit 1
}

Note "Preflight passed. Vision model: $model at $base"

# Step 1: the check set the run uses
& $tokn loss-inspect check-sets auto-physical-damage
if ($LASTEXITCODE -ne 0) { Fail "check-sets failed (exit $LASTEXITCODE)." }

# Step 2: prove the scorer returns logprobs with image input before the run
Note "Probing the vision model (status --probe --smoke)..."
& $tokn loss-inspect status --probe --smoke
if ($LASTEXITCODE -ne 0) { Fail "The scorer is not ready. Read the problems above, fix them, and re-run." }

# Step 3: the inspection itself. --air-gap refuses any scorer that is not on this machine.
New-Item -ItemType Directory -Force -Path "out" | Out-Null
Note "Running the inspection (49 records: 7 damage points x 7 checks)..."
& $tokn loss-inspect run --photos photos.json --points points.json --outlines none --air-gap `
    --claim-ref CLM-DEMO-0001 --out out/report.json --force
$code = $LASTEXITCODE
if ($code -eq 0) {
    Note "Every record is corroborated or clear."
} elseif ($code -eq 3) {
    Note "Report complete. Adjuster referrals exist (exit 3). This is expected without calibration and outlines; see the README."
} else {
    Fail "tokn loss-inspect run failed with exit code $code."
}

# Step 4: recompute every record and check the digest
& $tokn loss-inspect verify --report out/report.json
if ($LASTEXITCODE -ne 0) { Fail "verify failed (exit $LASTEXITCODE). The report was altered or is inconsistent." }
Note "Verified: out/report.json is internally consistent. Next: ./check.ps1"
exit 0

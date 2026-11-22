# run.ps1 - run the always-on claims intake example end to end (Windows PowerShell 5.1 or PowerShell 7).
# Usage: .\run.ps1 [-Local] [-Reset]
#   -Local   use a llama.cpp server on 127.0.0.1:8080 instead of Azure OpenAI (implies --airgap)
#   -Reset   first delete state\, workspace\.nospace\ and workspace\.tokn\ (generated, git-ignored)
# Both variants make model calls; -Local sends inference requests to the local model.
[CmdletBinding()]
param([switch]$Local, [switch]$Reset)

$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot

$Agent = "claims-intake"
$Ws = Join-Path $PSScriptRoot "workspace"
$State = Join-Path $PSScriptRoot "state"

function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }
function Abort([string]$Msg) {
    Write-Host "[!] $Msg" -ForegroundColor Red
    Write-Host "[*] State is preserved at '$State' for diagnosis. Use -Reset only when you explicitly want to discard it." -ForegroundColor Yellow
    exit 1
}

# 1. Preflight: every missing dependency is listed before anything runs.
$problems = @()
$tokn = $env:TOKN_BIN
if (-not $tokn) {
    $cmd = Get-Command tokn -ErrorAction SilentlyContinue
    if ($cmd) { $tokn = $cmd.Source }
}
if (-not $tokn -or -not (Test-Path -LiteralPath $tokn)) {
    $problems += "Missing: the tokn binary (v0.3.99 or later). Download it from https://github.com/bhakthan/tokn-dist/releases/latest, put it on PATH, or set TOKN_BIN to its full path."
} else {
    & $tokn always-on --help *> $null
    if ($LASTEXITCODE -ne 0) { $problems += "Old tokn: $tokn has no 'always-on' command. Install v0.3.99 or later." }
}

$py = $null
$pyPre = @()
$pyVersion = "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -c $pyVersion *> $null
    if ($LASTEXITCODE -eq 0) { $py = "py"; $pyPre = @("-3") }
}
if (-not $py -and (Get-Command python -ErrorAction SilentlyContinue)) {
    & python -c $pyVersion *> $null
    if ($LASTEXITCODE -eq 0) { $py = "python" }
}
if (-not $py) {
    $problems += "Missing: Python 3.10 or later (runs check.py; standard library only). Install: winget install Python.Python.3.12, then open a new terminal."
}

if ($Local) {
    $reachable = $false
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:8080/v1/models" -UseBasicParsing -TimeoutSec 3 | Out-Null
        $reachable = $true
    } catch { }
    if (-not $reachable) {
        $problems += "Missing: a llama.cpp server on http://127.0.0.1:8080/v1. Start llama-server as described in the README (Local variant)."
    }
    $cfgName = "config\claims-intake.local.yaml"
    $airgap = @("--airgap")
} else {
    if (-not $env:AZURE_OPENAI_ENDPOINT) {
        $problems += "AZURE_OPENAI_ENDPOINT is not set in this shell. Export your Azure OpenAI resource endpoint (README step 1). It is not read from .env."
    } elseif ($env:AZURE_OPENAI_ENDPOINT -match '(YOUR_|placeholder|[<>])') {
        $problems += "AZURE_OPENAI_ENDPOINT is still a placeholder. Set a trusted endpoint in this shell."
    }
    if (-not $env:AZURE_OPENAI_DEPLOYMENT) {
        $problems += "AZURE_OPENAI_DEPLOYMENT is not set in this shell (for example gpt-6-astra)."
    } elseif ($env:AZURE_OPENAI_DEPLOYMENT -match '(YOUR_|placeholder|[<>])') {
        $problems += "AZURE_OPENAI_DEPLOYMENT is still a placeholder. Set a trusted deployment alias in this shell."
    }
    if ($env:AZURE_OPENAI_USE_DEFAULT_CREDENTIAL -ne "true") {
        $problems += "AZURE_OPENAI_USE_DEFAULT_CREDENTIAL=true is not set in this shell (README step 1)."
    }
    $az = Get-Command az -ErrorAction SilentlyContinue
    if (-not $az) {
        $problems += "Missing: Azure CLI. Install it using Microsoft's signed package instructions for your OS: https://learn.microsoft.com/cli/azure/install-azure-cli. Then run az login."
    } else {
        & az account show -o none *> $null
        if ($LASTEXITCODE -ne 0) { $problems += "Azure CLI is not signed in. Run az login, then rerun." }
    }
    $cfgName = "config\claims-intake.yaml"
    $airgap = @()
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight failed; nothing was run. Fix these, then rerun:" -ForegroundColor Red
    $problems | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

# 2. Start clean: a leftover state directory would mix this run into the last one.
if ($Reset) {
    foreach ($p in @($State, (Join-Path $Ws ".nospace"), (Join-Path $Ws ".tokn"))) {
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    }
    Note "reset: removed state\, workspace\.nospace\ and workspace\.tokn\"
}
if (Test-Path -LiteralPath $State) {
    Write-Host "[!] state\ is left over from an earlier run. Rerun with -Reset to start clean." -ForegroundColor Red
    exit 1
}

# 3. Put the agent config where TOKN looks for it, and record the workspace before the run.
$cfgDir = Join-Path $Ws ".nospace\always-on"
New-Item -ItemType Directory -Force -Path $cfgDir, $State | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot $cfgName) -Destination (Join-Path $cfgDir "$Agent.yaml") -Force

$before = @(Get-ChildItem -LiteralPath $Ws -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($Ws.Length + 1).Replace('\', '/')
    if ($rel -notmatch '^(\.nospace|\.tokn)/') {
        "{0} {1}" -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLower(), $rel
    }
})
[IO.File]::WriteAllLines((Join-Path $State "workspace-before.txt"), [string[]]$before)

# 4. Doctor, enqueue, drain, record status, grade.
$common = @("--repo-root", $Ws, "--state-dir", $State, "--no-update-check")
function Invoke-Tokn([string[]]$Argv) { & $tokn "always-on" @Argv }

Note "doctor: checking every dependency"
Invoke-Tokn (@("doctor", $Agent) + $common + $airgap)
if ($LASTEXITCODE -ne 0) { Abort "doctor found missing items (listed above). Fix them, then rerun." }

$events = @(
    @{ File = "01-fnol-CLM-1001.md";       Session = "CLM-1001"; Key = "fnol-CLM-1001";     Kind = "user_message" },
    @{ File = "02-fnol-CLM-1001-retry.md"; Session = "CLM-1001"; Key = "fnol-CLM-1001";     Kind = "user_message" },
    @{ File = "03-followup-CLM-1001.md";   Session = "CLM-1001"; Key = "followup-CLM-1001"; Kind = "user_message" },
    @{ File = "04-fnol-CLM-1002.md";       Session = "CLM-1002"; Key = "fnol-CLM-1002";     Kind = "user_message" },
    @{ File = "05-portal-webhook.json";    Session = "portal-1"; Key = "portal-1";          Kind = "webhook" }
)
foreach ($e in $events) {
    $body = "@" + (Join-Path $PSScriptRoot ("events\" + $e.File))
    Invoke-Tokn (@("enqueue", $Agent) + $common + @("--session", $e.Session, "--key", $e.Key, "--kind", $e.Kind, "--body", $body))
    if ($LASTEXITCODE -ne 0) { Abort "enqueue failed for $($e.File)" }
}
Note "enqueued 5 events (the second fnol-CLM-1001 is a retry with the same key)"

# --run-timeout 0: a drain of five events takes a few minutes; the global 30s default would stop it.
Note "run --once: draining the inbox (this makes model calls)"
Invoke-Tokn (@("run", $Agent) + $common + @("--once", "--run-timeout", "0") + $airgap)
$runCode = $LASTEXITCODE

$statusJson = & $tokn "always-on" "status" $Agent @common "--json" "--last" "20" 2>$null
[IO.File]::WriteAllText((Join-Path $State "status.json"), ($statusJson -join "`n"))
Invoke-Tokn (@("status", $Agent) + $common + @("--last", "20"))

& $py @pyPre (Join-Path $PSScriptRoot "check.py")
$checkCode = $LASTEXITCODE

if ($runCode -ne 0 -or $checkCode -ne 0) { exit 1 }
exit 0

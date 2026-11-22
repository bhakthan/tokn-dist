# run.ps1 - run the two-desk claims example end to end (Windows PowerShell 5.1 or PowerShell 7).
# Usage: .\run.ps1 [-Fresh]
#   -Fresh   first delete state\ and the generated .nospace\ and .tokn\ folders under intake\ and review\
# Makes Azure OpenAI model calls. Nothing is committed to git.
[CmdletBinding()]
param([switch]$Fresh)

$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot

$Intake = "claims-intake"
$Review = "coverage-review"
$IntakeWs = Join-Path $PSScriptRoot "intake"
$ReviewWs = Join-Path $PSScriptRoot "review"
$State = Join-Path $PSScriptRoot "state"
$IntakeState = Join-Path $State $Intake
$ReviewState = Join-Path $State $Review

function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }
function Abort([string]$Msg) {
    Write-Host "[!] $Msg" -ForegroundColor Red
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
    $problems += "Missing: the tokn binary (v0.3.100 or later). Download tokn_windows_amd64.exe from https://github.com/bhakthan/tokn-dist/releases/latest, rename it tokn.exe, and put it on PATH or set TOKN_BIN to its full path."
} else {
    $verText = (& $tokn version 2>$null) -join "`n"
    $m = [regex]::Match($verText, 'tokn (\d+\.\d+\.\d+)')
    if (-not $m.Success) {
        $problems += "Could not read the version of $tokn. Handoff needs v0.3.100 or later."
    } elseif ([version]$m.Groups[1].Value -lt [version]"0.3.100") {
        $problems += "Old tokn: $tokn is $($m.Groups[1].Value). Handoff needs v0.3.100 or later (same download as above)."
    }
    & $tokn always-on --help *> $null
    if ($LASTEXITCODE -ne 0) { $problems += "Old tokn: $tokn has no 'always-on' command. Install v0.3.100 or later." }
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

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    $problems += "Missing: git (each desk folder is its own git repository). Install: winget install Git.Git, then open a new terminal."
}

if (-not $env:AZURE_OPENAI_ENDPOINT) {
    $problems += "AZURE_OPENAI_ENDPOINT is not set in this shell. Export your Azure OpenAI resource endpoint (README step 1). It is not read from .env."
} elseif ($env:AZURE_OPENAI_ENDPOINT -match '(YOUR_|placeholder|[<>])') {
    $problems += "AZURE_OPENAI_ENDPOINT is still a placeholder. Set a trusted endpoint in this shell."
}
if (-not $env:AZURE_OPENAI_DEPLOYMENT) {
    $problems += "AZURE_OPENAI_DEPLOYMENT is not set in this shell. Set it to the same trusted alias used in both model.model config fields."
} elseif ($env:AZURE_OPENAI_DEPLOYMENT -match '(YOUR_|placeholder|[<>])') {
    $problems += "AZURE_OPENAI_DEPLOYMENT is still a placeholder. Set a trusted deployment alias in this shell and in both model.model config fields."
} else {
    foreach ($relativeConfig in @("config\claims-intake.yaml", "config\coverage-review.yaml")) {
        $configPath = Join-Path $PSScriptRoot $relativeConfig
        $expectedModelLine = [regex]::Escape("  model: $($env:AZURE_OPENAI_DEPLOYMENT)")
        if ((Get-Content -LiteralPath $configPath -Raw) -notmatch "(?m)^$expectedModelLine$") {
            $problems += "$relativeConfig model.model does not match AZURE_OPENAI_DEPLOYMENT. Edit the config alias before rerunning."
        }
    }
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

if (-not $Fresh -and (Test-Path -LiteralPath $State)) {
    $problems += "state\ is left over from an earlier run. Rerun with -Fresh to clear it and start clean."
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight failed; nothing was run. Fix these, then rerun:" -ForegroundColor Red
    $problems | ForEach-Object { Write-Host "  - $_" }
    exit 1
}

# 2. Start clean: a leftover state directory would mix this run into the last one.
if ($Fresh) {
    foreach ($p in @($State, (Join-Path $IntakeWs ".nospace"), (Join-Path $IntakeWs ".tokn"),
                     (Join-Path $ReviewWs ".nospace"), (Join-Path $ReviewWs ".tokn"))) {
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    }
    Note "fresh: removed state\ and the generated .nospace\ and .tokn\ folders"
}

# 3. Set up both workspaces: git repository, ignore rule, and the desk config where TOKN looks for it.
$desks = @(
    @{ Name = $Intake; Ws = $IntakeWs; State = $IntakeState; Config = "config\claims-intake.yaml" },
    @{ Name = $Review; Ws = $ReviewWs; State = $ReviewState; Config = "config\coverage-review.yaml" }
)
foreach ($d in $desks) {
    if (-not (Test-Path -LiteralPath (Join-Path $d.Ws ".git"))) { & git init -q $d.Ws }
    $ignore = Join-Path $d.Ws ".gitignore"
    if (-not (Test-Path -LiteralPath $ignore)) {
        [IO.File]::WriteAllText($ignore, ".nospace/`n.tokn/`n")
    }
    $cfgDir = Join-Path $d.Ws ".nospace\always-on"
    New-Item -ItemType Directory -Force -Path $cfgDir | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $d.Config) -Destination (Join-Path $cfgDir "$($d.Name).yaml") -Force
}
New-Item -ItemType Directory -Force -Path $State | Out-Null

# 4. Ticks, doctor and enqueue. Every command names the repo and the state dir explicitly.
function Invoke-Tokn([string]$Verb, [string]$Agent, [string]$Ws, [string]$Dir, [string[]]$Extra = @()) {
    & $tokn always-on $Verb $Agent --repo-root $Ws --state-dir $Dir --no-update-check @Extra
}
function Invoke-Tick([string]$Agent, [string]$Ws, [string]$Dir, [string]$Label) {
    Note "tick: $Label ($Agent) run --once"
    Invoke-Tokn "run" $Agent $Ws $Dir @("--once", "--run-timeout", "0")
    if ($LASTEXITCODE -ne 0) { Abort "$Label tick failed (exit $LASTEXITCODE). Its output is above; state\ is kept for inspection. Fix the cause, then rerun with -Fresh." }
}

# Tick 0 starts both desks once, so each state directory exists before doctor checks the handoff peers.
Invoke-Tick $Review $ReviewWs $ReviewState "tick 0"
Invoke-Tick $Intake $IntakeWs $IntakeState "tick 0"

Note "doctor: checking every dependency, including the handoff peers"
Invoke-Tokn "doctor" $Intake $IntakeWs $IntakeState
if ($LASTEXITCODE -ne 0) { Abort "doctor found missing items for $Intake (listed above). Fix them, then rerun with -Fresh." }
Invoke-Tokn "doctor" $Review $ReviewWs $ReviewState
if ($LASTEXITCODE -ne 0) { Abort "doctor found missing items for $Review (listed above). Fix them, then rerun with -Fresh." }

foreach ($claim in @("CLM-2001", "CLM-2002")) {
    $body = "@" + (Join-Path $PSScriptRoot "events\$claim.md")
    Invoke-Tokn "enqueue" $Intake $IntakeWs $IntakeState @("--session", $claim, "--key", "fnol-$claim", "--body", $body)
    if ($LASTEXITCODE -ne 0) { Abort "enqueue failed for $claim" }
}
Note "enqueued both first notices to $Intake"

Invoke-Tick $Intake $IntakeWs $IntakeState "tick 1"
Invoke-Tick $Review $ReviewWs $ReviewState "tick 2"
Invoke-Tick $Intake $IntakeWs $IntakeState "tick 3"

# 5. Status for both desks, then grade.
foreach ($d in $desks) {
    $json = & $tokn always-on status $d.Name --repo-root $d.Ws --state-dir $d.State --no-update-check --json --last 20 2>$null
    [IO.File]::WriteAllText((Join-Path $d.State "status.json"), ($json -join "`n"))
    Invoke-Tokn "status" $d.Name $d.Ws $d.State @("--last", "20")
}

& $py @pyPre (Join-Path $PSScriptRoot "check.py")
exit $LASTEXITCODE

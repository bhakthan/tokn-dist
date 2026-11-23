#requires -Version 5.1
# Inference candidate for: tokn flywheel run --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1"
# Reads one ICSR on stdin, prepends the LIVE triage prompt, runs it through
# `tokn agent-run` against the provider you configured, and writes the final
# one-line answer to stdout.
#
# The live prompt is the project override that `tokn prompt-optimize --apply`
# installs: .nospace\prompts\pv-icsr-triage.md. Measuring that file (and not a
# copy) is what lets the flywheel test exactly what was promoted.
#
# Each invocation gets its own folder under scratch\, so answers never mix.
# Only the final `result` of a run whose status is "success" is used; a failed,
# blocked or empty run exits 1, so the flywheel records a failed case.
# This script never grades: the dataset does that.

$ErrorActionPreference = 'Stop'

$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$toknExe = if ($env:TOKN_BIN) { $env:TOKN_BIN } else { 'tokn' }
$live    = Join-Path $here '.nospace\prompts\pv-icsr-triage.md'

function Fail([string]$msg) {
  [Console]::Error.WriteLine("candidate: $msg")
  exit 1
}

if (-not (Get-Command $toknExe -ErrorAction SilentlyContinue)) {
  Fail 'tokn not found (set TOKN_BIN to the full path of tokn.exe)'
}
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_PROVIDER)) { Fail 'NOSPACE_MODEL_PROVIDER is not set (see README step 2)' }
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_NAME))     { Fail 'NOSPACE_MODEL_NAME is not set (see README step 2)' }
if (-not (Test-Path $live)) { Fail "live prompt missing: $live (see README step 3)" }

$icsr = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($icsr)) { Fail 'empty case on stdin' }

$repo  = Join-Path (Join-Path $here 'scratch') ('run-' + [guid]::NewGuid().ToString('N').Substring(0, 12))
New-Item -ItemType Directory -Force $repo | Out-Null
$pFile = Join-Path $repo 'prompt.txt'
$text  = (Get-Content -Raw $live).TrimEnd() + "`n`n---`nICSR:`n" + $icsr.Trim()
Set-Content -Path $pFile -Value $text -Encoding utf8 -NoNewline

# Plan mode: the answer is one line, so the agent may not write or run anything.
$rOut = Join-Path $repo 'result.json'
$aErr = Join-Path $repo 'agent.err'
# Windows PowerShell 5.1 turns redirected native stderr (for example TOKN's tier
# banner) into a terminating error under 'Stop', so relax it for this call only.
$ErrorActionPreference = 'Continue'
& $toknExe agent-run `
  --prompt-file $pFile `
  --repo-root $repo `
  --model-provider $env:NOSPACE_MODEL_PROVIDER `
  --model-name $env:NOSPACE_MODEL_NAME `
  --max-steps 2 `
  --permission-mode plan `
  --run-timeout 0 `
  --output-format json 1>$rOut 2>$aErr
$code = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($code -ne 0) { Fail "agent-run failed, see $aErr and $rOut" }

try { $res = Get-Content -Raw $rOut | ConvertFrom-Json } catch { Fail "unreadable result in $rOut" }
if ($res.status -ne 'success') { Fail "run status '$($res.status)' in $rOut" }
$answer = ([string]$res.result).Trim()

if ([string]::IsNullOrWhiteSpace($answer)) { Fail "empty result in $rOut (check provider auth)" }
[Console]::Out.Write($answer)

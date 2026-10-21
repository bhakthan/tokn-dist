#requires -Version 5.1
# Inference candidate for: tokn flywheel run --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1"
# Reads one case's input on stdin, runs it through `tokn agent-run` against the
# provider you configured, and writes the model's final answer to stdout.
# Failures exit 1 with a message on stderr, so the flywheel records a failed case.
# This script never grades: the dataset does that.

$ErrorActionPreference = 'Stop'

$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$toknExe = if ($env:TOKN_BIN) { $env:TOKN_BIN } else { 'tokn' }
$repo    = Join-Path $here 'scratch'
$pFile   = Join-Path $repo 'prompt.txt'

function Fail([string]$msg) {
  [Console]::Error.WriteLine("candidate: $msg")
  exit 1
}

if (-not (Get-Command $toknExe -ErrorAction SilentlyContinue)) {
  Fail 'tokn not found (set TOKN_BIN to the full path of tokn.exe)'
}
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_PROVIDER)) { Fail 'NOSPACE_MODEL_PROVIDER is not set (see README step 2)' }
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_NAME))     { Fail 'NOSPACE_MODEL_NAME is not set (see README step 2)' }

$prompt = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($prompt)) { Fail 'empty prompt on stdin' }

New-Item -ItemType Directory -Force $repo | Out-Null
Set-Content -Path $pFile -Value $prompt -Encoding utf8 -NoNewline

$aOut = Join-Path $repo 'agent.out'
$aErr = Join-Path $repo 'agent.err'
& $toknExe agent-run `
  --prompt-file $pFile `
  --repo-root $repo `
  --model-provider $env:NOSPACE_MODEL_PROVIDER `
  --model-name $env:NOSPACE_MODEL_NAME `
  --max-steps 2 `
  --no-confirm `
  --quiet 1>$aOut 2>$aErr
if ($LASTEXITCODE -ne 0) { Fail "agent-run failed, see $aErr" }

# agent-run writes one JSON line per event to .nospace\runs\<timestamp>.jsonl.
$runLog = Get-ChildItem (Join-Path $repo '.nospace\runs') -Filter *.jsonl -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime | Select-Object -Last 1
if (-not $runLog) { Fail "no run log under $repo\.nospace\runs" }

$final = ''
$last  = ''
foreach ($line in Get-Content $runLog.FullName) {
  try { $event = $line | ConvertFrom-Json } catch { continue }
  if ($event.role -ne 'assistant' -or $null -eq $event.content) { continue }
  $last = [string]$event.content
  if ($event.event -eq 'final') { $final = $last }
}
if ([string]::IsNullOrWhiteSpace($final)) { $final = $last }
$answer = $final.Trim()

if ([string]::IsNullOrWhiteSpace($answer)) { Fail "no assistant answer in $($runLog.FullName) (check provider auth)" }
[Console]::Out.Write($answer)

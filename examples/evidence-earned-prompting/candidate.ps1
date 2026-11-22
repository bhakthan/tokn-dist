#requires -Version 5.1
# Model candidate for:
#   tokn earned-prompt run --scenario . --candidate-cmd "powershell -NoProfile -ExecutionPolicy Bypass -File candidate.ps1"
# Reads the assembled prompt on stdin, runs it through `tokn agent-run` against
# the provider you configured, and writes the model's SQL answer to stdout.
# Failures exit 1 with a message on stderr. This script never runs or grades the
# SQL: TOKN does that locally, against an in-memory copy of seed.sql.

$ErrorActionPreference = 'Stop'

$here    = Split-Path -Parent $MyInvocation.MyCommand.Path
$toknExe = if ($env:TOKN_BIN) { $env:TOKN_BIN } else { 'tokn' }

function Fail([string]$msg) {
  [Console]::Error.WriteLine("candidate: $msg")
  exit 1
}

if (-not (Get-Command $toknExe -ErrorAction SilentlyContinue)) {
  Fail 'tokn not found (set TOKN_BIN to the full path of tokn.exe)'
}
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_PROVIDER)) { Fail 'NOSPACE_MODEL_PROVIDER is not set (see README step 4)' }
if ([string]::IsNullOrWhiteSpace($env:NOSPACE_MODEL_NAME))     { Fail 'NOSPACE_MODEL_NAME is not set (see README step 4)' }

$prompt = [Console]::In.ReadToEnd()
if ([string]::IsNullOrWhiteSpace($prompt)) { Fail 'empty prompt on stdin' }

$runId  = [Guid]::NewGuid().ToString('N')
$repo   = Join-Path $here "scratch\runs\$runId"
$pFile  = Join-Path $repo 'prompt.txt'
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
  --output-format json `
  --quiet 1>$aOut 2>$aErr
if ($LASTEXITCODE -ne 0) { Fail "agent-run failed, see $aErr" }

try { $result = Get-Content -Raw -Path $aOut | ConvertFrom-Json }
catch { Fail "agent-run returned invalid JSON (see $aErr)" }
if ($result.status -ne 'success' -or $result.exit_code -ne 0) { Fail "agent-run did not report terminal success (see $aErr)" }
$answer = [string]$result.result
if ([string]::IsNullOrWhiteSpace($answer)) { Fail 'successful agent-run result is empty' }
[Console]::Out.Write($answer)

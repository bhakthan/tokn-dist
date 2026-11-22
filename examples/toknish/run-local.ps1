# run-local.ps1 - preflight, then a local loopback federation run and a toknish-M bench.
# Usage: ./run-local.ps1 [-Model qwen3:8b] [-Provider ollama]
param(
    [string]$Model = "qwen3:8b",
    [string]$Provider = "ollama",
    [int]$Port = 8099
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Fail($msg) { Write-Host "[!] $msg" -ForegroundColor Red; exit 1 }
function Note($msg) { Write-Host "[*] $msg" -ForegroundColor Cyan }

# Load only the documented API keys; never import routing or token values.
if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match '^\s*(OPENAI_API_KEY|ANTHROPIC_API_KEY)=' } | ForEach-Object {
        $k, $v = $_ -split '=', 2
        $k = $k.Trim()
        $v = $v.Trim().Trim('"').Trim("'")
        if ($v -and -not [Environment]::GetEnvironmentVariable($k)) {
            [Environment]::SetEnvironmentVariable($k, $v)
        }
    }
}

# 1. TOKN on PATH.
$required = @("tokn", "git")
if ($Provider -eq "ollama") { $required += "ollama" }
$missing = @($required | Where-Object { -not (Get-Command $_ -ErrorAction SilentlyContinue) })
if ($missing.Count -gt 0) {
    Fail "Missing required commands: $($missing -join ', '). TOKN v0.3.90+ and Git are required; Ollama is also required for the local provider. Install all using the OS-specific commands in README.md, then retry."
}
Note "tokn found: $((tokn version 2>$null | Select-Object -First 1))"

# 2. Provider.
if ($Provider -eq "ollama") {
    try {
        $tags = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -TimeoutSec 5
    } catch {
        Fail "Ollama is installed but not running. Start the Ollama app, or run 'ollama serve', then retry."
    }
    if (-not ($tags.models | Where-Object { $_.name -eq $Model -or $_.model -eq $Model })) {
        Fail "Model '$Model' is not pulled. Run: ollama pull $Model"
    }
    Note "Ollama is running and '$Model' is available."
} else {
    Note "Provider '$Provider': set its API key in your trusted process environment; only documented key names are imported from an untracked .env."
}

# 3. Shared token, created for this run only if not set (never written to disk).
if ($env:TOKN_WORKER_TOKEN -match '(?i)(<.*>|your|placeholder)') {
    Fail "TOKN_WORKER_TOKEN looks like a placeholder. Remove it and let the script generate a per-run token, or set a real token in the process environment."
}
if (-not $env:TOKN_WORKER_TOKEN) {
    $b = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($b)
    $env:TOKN_WORKER_TOKEN = [Convert]::ToBase64String($b)
    Note "Created a one-off TOKN_WORKER_TOKEN for this run."
}

$scratch = Join-Path ([IO.Path]::GetTempPath()) "toknish-$([guid]::NewGuid().ToString('N'))"
$exampleDir = $PSScriptRoot
New-Item -ItemType Directory -Path $scratch | Out-Null
Note "Scratch workspace: $scratch"
$repo = Join-Path $scratch "repo"
$wState = Join-Path $scratch "worker-state"
$lState = Join-Path $scratch "leader-state"
New-Item -ItemType Directory -Force $repo, $wState, $lState | Out-Null
Set-Content -Path (Join-Path $repo "README.md") -Value "Sample repository for the toknish walkthrough."
Set-Location $scratch

# 4. Start the worker in the background and wait for it to listen.
$worker = Start-Process -FilePath "tokn" -PassThru -WindowStyle Hidden -ArgumentList @(
    "agent-worker", "--listen", "127.0.0.1:$Port", "--worker-id", "w1",
    "--repo-root", $repo, "--provider", $Provider, "--model", $Model,
    "--federation-dir", $wState)
try {
    $up = $false
    for ($i = 0; $i -lt 30 -and -not $up; $i++) {
        Start-Sleep -Seconds 1
        $c = New-Object System.Net.Sockets.TcpClient
        try { $c.Connect("127.0.0.1", $Port); $up = $true } catch {} finally { $c.Close() }
    }
    if (-not $up) { Fail "The worker did not start on 127.0.0.1:$Port within 30 seconds." }
    Note "Worker w1 is listening on 127.0.0.1:$Port."

    # 5. Leader run with toknish negotiated where offered.
    tokn agent-leader --worker "w1=http://127.0.0.1:$Port" --wire auto `
        --federation-dir $lState `
        --prompt "List the files in the repository root and say which one looks like a README." `
        --out (Join-Path $scratch "results.json")
    if ($LASTEXITCODE -ne 0) { Fail "The leader run failed. Check the output above." }

    # 6. Verify the audit chain for the newest session.
    $session = Get-ChildItem -Directory $lState | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($session) {
        tokn toknish audit $session.Name --dir $lState
        Note "Audit exit code $LASTEXITCODE (0 = clean)."
    } else {
        Note "No toknish session folder was written, so this run used plain JSON."
    }
} finally {
    if ($worker -and -not $worker.HasExited) { Stop-Process -Id $worker.Id -Force }
}

# 7. Bench: the built-in smoke set, then the dataset.
Note "Running the smoke bench..."
tokn tkm bench --provider $Provider --model $Model --sample
Note "Running the dataset bench (writes bench-report.json)..."
tokn tkm bench --provider $Provider --model $Model --dataset (Join-Path $exampleDir "dataset.json") --out (Join-Path $scratch "bench-report.json")
Note "Done. Results remain in the printed scratch workspace for review."

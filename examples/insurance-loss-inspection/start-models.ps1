# start-models.ps1 - preflight, then print (or with -Start, launch) the three loopback llama.cpp servers.
#   port 8081  vision model (loss-inspect scorer)
#   port 8082  decision model, Clef-Flash (system-one triage)
#   port 8083  coding model (agent in insurance mode)
# Usage: ./start-models.ps1          print the commands and check the setup
#        ./start-models.ps1 -Start   also start the servers (logs go to out/logs)
param([switch]$Start)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

# Load .env without overriding the shell (only CODER_HF_MODEL is read from it here).
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

# 1. llama.cpp. Prefer llama-server (the name the other examples use); fall back to `llama serve`.
$bin = $null
$prefix = @()
$server = Get-Command llama-server -ErrorAction SilentlyContinue
$llama = Get-Command llama -ErrorAction SilentlyContinue
if ($server) { $bin = $server.Source }
elseif ($llama) { $bin = $llama.Source; $prefix = @("serve") }
else {
    $problems += @"
Missing: llama.cpp (neither llama-server nor llama is on PATH).
  Why:   it serves the three local models over OpenAI-compatible HTTP.
  Fix:   winget install ggml.llamacpp
         Open a new terminal, then check with: llama-server --version
"@
}

# 2. curl (port and health checks)
$curl = Get-Command curl.exe -ErrorAction SilentlyContinue
if (-not $curl) {
    $problems += "Missing: curl.exe (port and health checks). It ships with Windows 10 1803+ and Windows 11."
}

# 3. The coding model is the only one without a fixed default.
$coder = $env:CODER_HF_MODEL
if (-not $coder -or $coder -match '^<.*>$') {
    $problems += @"
Missing: CODER_HF_MODEL. Set it to the Hugging Face repo and quant of a coder GGUF, for example:
         `$env:CODER_HF_MODEL = "<hf-repo>:<quant>"
  Why:   the coding model drives the TOKN agent in insurance mode (run-agent).
  Pick:  a Qwen coder GGUF that fits your memory (see the README hardware notes).
"@
}

$models = @(
    [pscustomobject]@{ Name = "vision";  Port = 8081; Hf = "ggml-org/Qwen2.5-VL-3B-Instruct-GGUF"; Log = "8081"; Extra = @() },
    # A decision model reads the whole request in one batch; 512 (the default) is too small.
    [pscustomobject]@{ Name = "decision"; Port = 8082; Hf = "ggml-org/Clef-Flash-GGUF"; Log = "8082"; Extra = @("-b", "2048", "-ub", "2048") },
    [pscustomobject]@{ Name = "coder";   Port = 8083; Hf = $coder; Log = "8083"; Extra = @() }
)

# 4. Ports must be free before anything starts.
if ($curl) {
    foreach ($m in $models) {
        $code = & curl.exe -s -o NUL -w "%{http_code}" --max-time 2 "http://127.0.0.1:$($m.Port)/" 2>$null
        if ($code -and $code -ne "000") {
            $problems += "Port $($m.Port) is already in use (needed for the $($m.Name) model). Stop the program using it, or pick another port and update the .env / shell settings to match."
        }
    }
}

if ($problems.Count -gt 0) {
    Write-Host "Preflight found $($problems.Count) problem(s):" -ForegroundColor Yellow
    $problems | ForEach-Object { Write-Host "- $_"; Write-Host "" }
    exit 1
}

Note "Preflight passed. Binary: $bin"
Note "Each server listens on 127.0.0.1 only."
$cmdLines = @()
foreach ($m in $models) {
    $cargs = @($prefix) + @("-hf", $m.Hf, "--host", "127.0.0.1", "--port", "$($m.Port)") + $m.Extra
    $cmdLines += [pscustomobject]@{ Model = $m; Args = $cargs }
    Write-Host ""
    Write-Host "  $($m.Name) (port $($m.Port)):"
    Write-Host "    $(Split-Path $bin -Leaf) $($cargs -join ' ')"
}
Write-Host ""

if (-not $Start) {
    Write-Host "Nothing was started. To start all three, run: ./start-models.ps1 -Start"
    Write-Host "Or start each one yourself in its own terminal (recommended on small GPUs; see the README)."
    exit 0
}

New-Item -ItemType Directory -Force -Path "out\logs" | Out-Null
$pids = @()
foreach ($c in $cmdLines) {
    $m = $c.Model
    $proc = Start-Process -FilePath $bin -ArgumentList $c.Args -WindowStyle Minimized -PassThru `
        -RedirectStandardOutput (Join-Path $PSScriptRoot "out\logs\$($m.Log).out.log") `
        -RedirectStandardError (Join-Path $PSScriptRoot "out\logs\$($m.Log).err.log")
    $pids += [pscustomobject]@{ Name = $m.Name; Port = $m.Port; Pid = $proc.Id }
    Note "Started $($m.Name) on port $($m.Port) (pid $($proc.Id))."
}
$pids | Format-Table -AutoSize | Out-String | Write-Host

Note "Waiting for health (the first start downloads each model, which can take a long time)..."
foreach ($m in $models) {
    $ready = $false
    for ($i = 0; $i -lt 360 -and -not $ready; $i++) {
        $h = & curl.exe -s --max-time 3 "http://127.0.0.1:$($m.Port)/health" 2>$null
        if ($h -match '"ok"') { $ready = $true } else { Start-Sleep -Seconds 5 }
    }
    if ($ready) { Note "$($m.Name) on port $($m.Port) is healthy." }
    else { Write-Host "[!] $($m.Name) on port $($m.Port) is not healthy yet. Read out\logs\$($m.Log).err.log." -ForegroundColor Yellow }
}
Write-Host ""
Write-Host "To stop them later: Stop-Process -Id <pid> for each pid above."
exit 0

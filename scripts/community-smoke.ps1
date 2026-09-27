# community-smoke.ps1 — confirm a TOKN install can run the free Community tier.
#
# Runs the three domain previews and the offline governed-judgment example.
# No API key, no model provider, no trial. The checks themselves send nothing;
# set TOKN_NO_REGISTER=1 and TOKN_NO_UPDATE_CHECK=1 to silence TOKN's startup
# install-count and update-check too.
# All scratch files go in a temp directory that is removed on exit.

$ErrorActionPreference = 'Continue'
$script:Failed = 0

function Step($m) { Write-Host "`n== $m" }
function Ok($m)   { Write-Host "   ok   $m" }
function Bad($m)  { Write-Host "   FAIL $m"; $script:Failed = 1 }

Step "preflight"
$tokn = Get-Command tokn -ErrorAction SilentlyContinue
if (-not $tokn) {
    Write-Host @'
   FAIL tokn is not on your PATH.

   This script needs the TOKN binary and nothing else — no API key, no model
   provider, no trial. Install it first:

     1. Download for your OS:  https://github.com/bhakthan/tokn-dist/releases/latest
     2. Verify the signature:  see README.md section 2 (needs openssl 3.x)
     3. Put it on your PATH:   see README.md section 3

   Then re-run this script.
'@
    exit 1
}
Ok "tokn found: $($tokn.Source)"
tokn --version | Out-Null
if ($LASTEXITCODE -ne 0) { Bad "tokn --version failed" }

$work = Join-Path ([IO.Path]::GetTempPath()) ("tokn-smoke-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $work | Out-Null
Push-Location $work
try {
    Step "developer on-ramp"
    $guide = (tokn community guide 2>&1) -join "`n"
    if ($LASTEXITCODE -ne 0) { Bad "community guide (exit)" }
    if ($guide -match 'DISCOVER' -and $guide -match 'INSPECT' -and $guide -match 'OPT IN') {
        Ok "community guide renders the discover/inspect/opt-in path"
    } else {
        Bad "community guide did not render the expected sections"
    }
    $bare = (tokn community 2>&1) -join "`n"
    if ($bare -eq $guide) {
        Ok "bare 'tokn community' renders the same on-ramp"
    } else {
        Bad "bare 'tokn community' and 'tokn community guide' differ"
    }

    Step "domain previews"
    tokn community list | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "community list" } else { Bad "community list" }

    foreach ($domain in @('powergrid', 'geospatial', 'batterypass')) {
        $out = (tokn community demo --domain $domain 2>&1) -join "`n"
        if ($LASTEXITCODE -ne 0) { Bad "demo $domain (exit)"; continue }
        if ($out -match 'Verdict: ACCEPTED' -and $out -match 'Verdict: BLOCKED') {
            Ok "demo $domain (one accepted case, one blocked case)"
        } else {
            Bad "demo $domain did not report both an accepted and a blocked case"
        }
    }

    Step "unknown preview is rejected"
    tokn community demo --domain not-a-domain 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Ok "unknown preview rejected" }
    else { Bad "an unknown preview name was accepted" }

    Step "offline governed judgments"
    # Windows PowerShell 5.1 writes UTF-16 for '>', which is not valid JSON input.
    $bundle = (tokn judgments example) -join "`n"
    if ($LASTEXITCODE -ne 0) { Bad "judgments example" }
    Set-Content -Path bundle.json -Value $bundle -Encoding ascii
    tokn judgments validate --bundle bundle.json | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "bundle validates" } else { Bad "bundle validate" }

    '{"state":{"status":"completed","answer_present":true,"telemetry_complete":true,"tool_calls":12,"tool_errors":0,"tool_blocks":0,"steps":7},"context":{"trace_id":"smoke-clean","environment":"local"}}' |
        Set-Content -Encoding ascii request-clean.json
    '{"state":{"status":"completed","answer_present":true,"telemetry_complete":true,"tool_calls":12,"tool_errors":2,"tool_blocks":1,"steps":7},"context":{"trace_id":"smoke-errors","environment":"local"}}' |
        Set-Content -Encoding ascii request-errors.json

    $clean = (tokn judgments evaluate --bundle bundle.json --file request-clean.json --mode advisory --air-gap 2>&1) -join "`n"
    if ($clean -match '"action": "continue"') { Ok "clean run judged: continue" }
    else { Bad "clean run did not judge continue" }

    $errs = (tokn judgments evaluate --bundle bundle.json --file request-errors.json --mode advisory --air-gap 2>&1) -join "`n"
    if ($errs -match '"action": "revise"') { Ok "failing run judged: revise" }
    else { Bad "failing run did not judge revise" }

    if ($errs -match '"applied": false') { Ok "judgment is advisory (applied: false)" }
    else { Bad "judgment reported applied: true" }
}
finally {
    Pop-Location
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}

Step "result"
if ($script:Failed -eq 0) {
    Write-Host "   All Community-tier checks passed. Next: GETTING_STARTED.md"
} else {
    Write-Host "   Some checks failed. See the troubleshooting table in GETTING_STARTED.md"
}
exit $script:Failed

# check.ps1 - read-only check of out/report.json, plus a reading table.
# Structural checks decide the exit code; the table is for reading, not grading.
# Usage: ./check.ps1 [-Report <path>]
param(
    [string]$Report = (Join-Path $PSScriptRoot "out\report.json")
)

$ErrorActionPreference = "Stop"

$ClaimRef = "CLM-DEMO-0001"
$ExpectedPoints = 7
$ChecksPerPoint = 7
$AllowedStatus = @("corroborated", "clear", "adjuster_referral")

# Ground truth for the three demo photos (see README). $null means not labelled.
$Truth = @{
    "windshield"       = @("crack", "broken")
    "hood"             = @("dent")
    "front bumper"     = @()
    "left mirror"      = @("crack", "broken")
    "van rear side"    = @("broken", "dent")
    "van front bumper" = $null
    "van windshield"   = @("crack")
}

function Get-PYes($rec) {
    if ($rec.label -ne "yes" -and $rec.label -ne "no") { return $null }
    if ($null -eq $rec.probability) { return $null }
    $p = [double]$rec.probability
    if ($rec.label -eq "yes") { return $p } else { return 1.0 - $p }
}

if (-not (Test-Path -LiteralPath $Report)) {
    Write-Host "[!] File not found: $Report. Run run-inspection first." -ForegroundColor Red
    exit 2
}
try {
    $doc = Get-Content -LiteralPath $Report -Raw -Encoding UTF8 | ConvertFrom-Json
} catch {
    Write-Host "[!] Cannot read ${Report}: $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

$problems = @()
if ($doc.schema_version -ne 1) { $problems += "schema_version is $($doc.schema_version), expected 1" }
if (-not ($doc.digest -is [string]) -or -not $doc.digest.StartsWith("sha256:")) { $problems += "digest does not start with sha256:" }
$claim = $doc.run.claim_ref
if ($claim -ne $ClaimRef) { $problems += "run.claim_ref is '$claim', expected '$ClaimRef'" }

$names = @($doc.points | ForEach-Object { $_.name })
$distinct = @($names | Select-Object -Unique)
if ($distinct.Count -ne $ExpectedPoints) { $problems += "found $($distinct.Count) distinct damage points, expected $ExpectedPoints" }

$records = @($doc.records)
$want = $ExpectedPoints * $ChecksPerPoint
if ($records.Count -ne $want) { $problems += "found $($records.Count) records, expected $want" }
foreach ($n in $distinct) {
    $c = @($records | Where-Object { $_.point -eq $n }).Count
    if ($c -ne $ChecksPerPoint) { $problems += "point '$n' has $c records, expected $ChecksPerPoint" }
}

$counts = @{ corroborated = 0; clear = 0; adjuster_referral = 0 }
foreach ($r in $records) {
    if ($AllowedStatus -contains $r.status) { $counts[$r.status]++ } else { $problems += "unknown record status: $($r.status)" }
}
$expected = @{
    points = $distinct.Count; records = $records.Count
    corroborated = $counts.corroborated; clear = $counts.clear; adjuster_referrals = $counts.adjuster_referral
}
foreach ($key in $expected.Keys) {
    if ([int]$doc.summary.$key -ne [int]$expected[$key]) {
        $problems += "summary.$key is $($doc.summary.$key), records give $($expected[$key])"
    }
}

if ($problems.Count -gt 0) {
    $problems | ForEach-Object { Write-Host "Structure: $_" }
    Write-Host "FAIL: the report does not have the expected structure." -ForegroundColor Red
    exit 1
}

Write-Host "PASS: structure ok ($($distinct.Count) points, $($records.Count) records, claim $ClaimRef)."
Write-Host "Referrals: $($counts.adjuster_referral) of $($records.Count). Every referral needs an adjuster."
Write-Host ""
Write-Host ("{0,-18} {1,9}  {2,-44} {3}" -f "point", "referrals", "top three P(yes)", "ground truth")
foreach ($n in $distinct) {
    $mine = @($records | Where-Object { $_.point -eq $n })
    $refs = @($mine | Where-Object { $_.status -eq "adjuster_referral" }).Count
    $scored = @()
    foreach ($r in $mine) {
        $p = Get-PYes $r
        if ($null -ne $p) { $scored += [pscustomobject]@{ Check = $r.check_id; P = $p } }
    }
    $top = @($scored | Sort-Object -Property P -Descending | Select-Object -First 3)
    $shown = @()
    foreach ($t in $top) {
        $mark = ""
        if ($Truth[$n] -and ($Truth[$n] -contains $t.Check)) { $mark = "*" }
        $shown += ("{0}{1} {2:N2}" -f $t.Check, $mark, $t.P)
    }
    $groundTruth = $Truth[$n]
    if ($null -eq $groundTruth) { $text = "(not labelled)" }
    elseif ($groundTruth.Count -eq 0) { $text = "no visible damage" }
    else { $text = (($groundTruth | Sort-Object) -join ", ") }
    Write-Host ("{0,-18} {1,9}  {2,-44} {3}" -f $n, $refs, ($shown -join ", "), $text)
}
Write-Host "* = the demo photo shows this damage. P(yes) is the record's probability, flipped for 'no' labels."
exit 0

# check.ps1 - read-only check that the reorder report lists the expected items.
# Usage: ./check.ps1 [-Report <path>] [-Expected <path>]
param(
    [string]$Report = (Join-Path $PSScriptRoot "workspace\reorder.md"),
    [string]$Expected = (Join-Path $PSScriptRoot "expected-reorder.md")
)

$ErrorActionPreference = "Stop"

function Get-ItemNames([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { throw "File not found: $Path. Run run-local.ps1 first." }
    $names = @()
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = $raw.Trim()
        if (-not $line.StartsWith('|')) { continue }
        $first = ($line.Trim('|') -split '\|')[0].Trim().Trim('`')
        if (-not $first -or $first -eq 'item' -or $first -match '^:?-+:?$') { continue }
        $names += $first
    }
    return @($names | Sort-Object -Unique)
}

try {
    $actual = Get-ItemNames $Report
    $expectedItems = Get-ItemNames $Expected
} catch {
    Write-Host "[!] $($_.Exception.Message)" -ForegroundColor Red
    exit 2
}

$missing = @($expectedItems | Where-Object { $_ -notin $actual })
$extra = @($actual | Where-Object { $_ -notin $expectedItems })

if ($missing.Count -eq 0 -and $extra.Count -eq 0) {
    Write-Host "PASS: $($expectedItems.Count) items match."
    exit 0
}
if ($missing.Count -gt 0) { Write-Host "Missing: $($missing -join ', ')" }
if ($extra.Count -gt 0) { Write-Host "Unexpected: $($extra -join ', ')" }
Write-Host "FAIL" -ForegroundColor Red
exit 1

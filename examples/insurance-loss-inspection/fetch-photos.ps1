# fetch-photos.ps1 - download the three demo photos from Wikimedia Commons into photos/.
# The photos are not committed. Each one is checked to be 1280 px wide, and the
# licence and author are printed from the file's own metadata.
# Usage: ./fetch-photos.ps1
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

function Fail([string]$Msg) { Write-Host "[!] $Msg" -ForegroundColor Red; exit 1 }
function Note([string]$Msg) { Write-Host "[*] $Msg" -ForegroundColor Cyan }

$UserAgent = "tokn-dist-examples/insurance-loss-inspection (demo photo download; read-only)"
$Photos = @(
    @{ Title = "File:2017 Toyota Rav4 XLE Hybrid AWD-I (36942379162).jpg"; File = "suv-front.jpg" },
    @{ Title = "File:2010-03-08 Shattered side mirror on BMW.jpg"; File = "side-mirror.jpg" },
    @{ Title = "File:20171118 damaged Hyundai Grand starex-1.jpg"; File = "van-side.jpg" }
)

try {
    Add-Type -AssemblyName System.Drawing
} catch {
    Fail "System.Drawing is not available, so the photo width cannot be checked. Use PowerShell 7 on Windows."
}

New-Item -ItemType Directory -Force -Path "photos" | Out-Null

foreach ($p in $Photos) {
    $api = "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1280&format=json&titles=" + [uri]::EscapeDataString($p.Title)
    try {
        $resp = Invoke-RestMethod -Uri $api -Headers @{ "User-Agent" = $UserAgent }
    } catch {
        Fail "Could not reach the Wikimedia Commons API for $($p.Title): $($_.Exception.Message). Check your network and retry."
    }
    $page = @($resp.query.pages.PSObject.Properties)[0].Value
    $info = if ($page.imageinfo) { $page.imageinfo[0] } else { $null }
    if (-not $info) { Fail "Commons returned no image data for $($p.Title)." }
    if ([int]$info.thumbwidth -ne 1280) {
        Fail "$($p.Title) is $($info.thumbwidth) px wide, expected 1280. The file may have changed on Commons."
    }

    $dest = Join-Path (Join-Path $PSScriptRoot "photos") $p.File
    try {
        Invoke-WebRequest -Uri $info.thumburl -Headers @{ "User-Agent" = $UserAgent } -OutFile $dest -UseBasicParsing
    } catch {
        Fail "Download failed for $($p.File): $($_.Exception.Message)"
    }

    $img = [System.Drawing.Image]::FromFile($dest)
    try { $w = $img.Width; $h = $img.Height } finally { $img.Dispose() }
    if ($w -ne 1280) { Fail "$($p.File) decodes to ${w}x${h}, expected 1280 px wide." }

    $meta = $page.imageinfo[0].extmetadata
    $licence = if ($meta.LicenseShortName) { $meta.LicenseShortName.value } else { "unknown" }
    $author = if ($meta.Artist) { ($meta.Artist.value -replace '<[^>]+>', '').Trim() } else { "unknown" }
    Note "$($p.File): ${w}x${h}, licence $licence, author $author"
    Note "  $($info.descriptionurl)"
}

Note "Done. Photos are in photos/. Attribution is in ATTRIBUTION.md."
exit 0

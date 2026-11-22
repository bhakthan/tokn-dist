function Load-SafeEnv([string]$Path, [string[]]$AllowedKeys) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($line in [IO.File]::ReadLines((Resolve-Path -LiteralPath $Path))) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#") -or -not $t.Contains("=")) { continue }
        $k, $v = $t.Split("=", 2)
        $k = $k.Trim()
        $v = $v.Trim()
        if ($k -notmatch '^[A-Za-z_][A-Za-z0-9_]*$' -or $k -notin $AllowedKeys) { continue }
        if (($v.StartsWith('"') -and $v.EndsWith('"')) -or ($v.StartsWith("'") -and $v.EndsWith("'"))) {
            $v = $v.Substring(1, $v.Length - 2)
        }
        if (-not [Environment]::GetEnvironmentVariable($k)) {
            [Environment]::SetEnvironmentVariable($k, $v)
        }
    }
}

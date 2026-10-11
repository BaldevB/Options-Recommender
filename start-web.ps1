# Options Suggester Pro - PowerShell Launcher
$script = Join-Path $PSScriptRoot "scripts\launcher.ps1"
if (-not (Test-Path $script)) {
    $script = Join-Path (Get-Location) "scripts\launcher.ps1"
}
& $script

# Creates a Windows Desktop shortcut to launch Options Suggester Pro with one double-click
$ErrorActionPreference = "SilentlyContinue"

$desktopPath = [Environment]::GetFolderPath("Desktop")
if (-not (Test-Path $desktopPath)) {
    # Check OneDrive Desktop fallback
    $oneDriveDesktop = Join-Path $HOME "OneDrive\Desktop"
    if (Test-Path $oneDriveDesktop) {
        $desktopPath = $oneDriveDesktop
    }
}

$rootDir = Split-Path -Parent $PSScriptRoot
if (-not $rootDir) { $rootDir = Get-Location }

$targetFile = Join-Path $rootDir "launch.bat"
$shortcutFile = Join-Path $desktopPath "Options Suggester Pro.lnk"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutFile)
$shortcut.TargetPath = $targetFile
$shortcut.WorkingDirectory = $rootDir
$shortcut.Description = "Launch Options Suggester Pro Quantitative Platform"
$shortcut.WindowStyle = 1 # Normal window
$shortcut.IconLocation = "shell32.dll, 220" # Nice browser/globe icon from Windows shell
$shortcut.Save()

Write-Host "Created Desktop Shortcut at: $shortcutFile" -ForegroundColor Green

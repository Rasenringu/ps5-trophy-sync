[CmdletBinding()]
param([switch]$SkipBuild)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
& "$PSScriptRoot\scripts\Doctor.ps1"
& "$PSScriptRoot\scripts\Configure-PS5.ps1"
if (Get-Command git -ErrorAction SilentlyContinue) {
    if (-not (Test-Path .git)) {
        & git init -b main
        if ($LASTEXITCODE -ne 0) { throw 'Git initialization failed.' }
    }
} else { Write-Host 'Git missing: install Git for Windows before backing up to GitHub.' }
if (-not $SkipBuild) { & "$PSScriptRoot\scripts\Build-Tools.ps1" }
Write-Host 'Ready. Follow README.md to run the web application and build TrophySync.elf.'

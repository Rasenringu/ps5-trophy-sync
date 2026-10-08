[CmdletBinding()]
param([switch]$SmokeTest, [switch]$HostTest, [ValidateSet('public','lan')][string]$Endpoint = 'public')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if ($root.Contains(',')) { throw 'Docker mount paths must not contain commas.' }
& "$PSScriptRoot\Doctor.ps1"
$mount = 'type=bind,source=' + $root + ',target=/workspace'
if ($SmokeTest) {
    & docker run --rm --mount $mount ps5-trophy-build:starter bash /workspace/scripts/container-smoke.sh
    if ($LASTEXITCODE -ne 0) { throw 'SDK smoke compile failed.' }
    return
}
$prepare = @('bash','/workspace/scripts/container-prepare-console.sh')
if ($HostTest) { $prepare += '--host-tests' }
& docker run --rm --env "TROPHY_SYNC_ENDPOINT=$Endpoint" --mount $mount ps5-trophy-build:starter @prepare
if ($LASTEXITCODE -ne 0) { throw 'Console dependency/configuration preparation failed.' }
& docker run --rm --mount $mount ps5-trophy-build:starter bash /workspace/scripts/container-build.sh
if ($LASTEXITCODE -ne 0) { throw 'TrophySync.elf compilation failed.' }
if ($HostTest) {
    & docker run --rm --mount $mount ps5-trophy-build:starter bash /workspace/scripts/container-test-console.sh
    if ($LASTEXITCODE -ne 0) { throw 'Console host regression tests failed.' }
}
Write-Host 'Built artifacts/console/final-ui/TrophySync.elf. No console upload or execution.'

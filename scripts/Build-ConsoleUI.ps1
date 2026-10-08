[CmdletBinding()]
param([ValidateSet('public','lan')][string]$Endpoint = 'public')
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot\Doctor.ps1"
if ($root.Contains(',')) { throw 'Docker mount paths must not contain commas.' }
& "$PSScriptRoot\Build-Console.ps1" -Endpoint $Endpoint
$mount = 'type=bind,source=' + $root + ',target=/workspace'
& docker build -f "$root\console\Dockerfile.ui-test" -t ps5-trophy-ui-test:local "$root\console"
if ($LASTEXITCODE -ne 0) { throw 'Font/QR host image build failed.' }
# Existing pinned host image provides Pillow/zxing only for font baking/previews.
& docker run --rm --mount $mount --entrypoint python ps5-trophy-ui-test:local /workspace/scripts/generate-console-font.py
if ($LASTEXITCODE -ne 0) { throw 'Pinned font baking failed.' }
& docker run --rm --mount $mount --entrypoint python ps5-trophy-ui-test:local /workspace/scripts/generate-console-icon.py
if ($LASTEXITCODE -ne 0) { throw 'Title artwork generation failed.' }
& docker run --rm --mount $mount ps5-trophy-build:starter bash /workspace/scripts/container-test-final-ui.sh
if ($LASTEXITCODE -ne 0) { throw 'Host renderer checks failed.' }
& docker run --rm --mount $mount --entrypoint python ps5-trophy-ui-test:local /workspace/console/tests/verify_final_preview.py
if ($LASTEXITCODE -ne 0) { throw 'Independent QR checks failed.' }
& docker run --rm --mount $mount ps5-trophy-build:starter bash /workspace/scripts/container-build-final-ui.sh
if ($LASTEXITCODE -ne 0) { throw 'Native UI compilation failed.' }
Write-Host 'Built artifacts/console/final-ui: TrophySync.elf, PPSA99889 and TrophySync-PS5.zip. No console action.'

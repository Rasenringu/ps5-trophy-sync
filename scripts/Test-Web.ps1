$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
& docker build -f (Join-Path $root 'web\Dockerfile.test') -t ps5-sync-web-test (Join-Path $root 'web')
if ($LASTEXITCODE -ne 0) { throw 'Browser test image build failed.' }
& docker run --rm --ipc=host ps5-sync-web-test
if ($LASTEXITCODE -ne 0) { throw 'Browser test failed.' }
Write-Host 'Synthetic browser account remains in the local development database; no console contacted.'

[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot\Doctor.ps1"
$cache = Join-Path $root '.local\sdk'
New-Item -ItemType Directory -Force -Path $cache | Out-Null
$archive = Join-Path $cache 'ps5-payload-sdk.zip'
$lockPath = Join-Path $root 'toolchain.lock.json'
if (Test-Path $lockPath) {
    $lock = Get-Content -Raw -LiteralPath $lockPath | ConvertFrom-Json
    if (-not $lock.ps5_sdk.url -or -not $lock.ps5_sdk.sha256) { throw 'Invalid toolchain lock. Inspect before continuing.' }
    if (-not (Test-Path $archive)) { Invoke-WebRequest -UseBasicParsing -Uri $lock.ps5_sdk.url -OutFile $archive }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    if ($hash -ne $lock.ps5_sdk.sha256) { throw 'SDK checksum mismatch. Remove the cached archive only after investigating; keep the lock.' }
} else { throw 'toolchain.lock.json is required; restore the reviewed SDK pin before building.' }
& docker build --file "$root\deployment\Dockerfile.ps5-tools" --tag 'ps5-trophy-build:starter' $root
if ($LASTEXITCODE -ne 0) { throw 'PS5 toolchain image build failed.' }
& "$PSScriptRoot\Build-Console.ps1" -SmokeTest

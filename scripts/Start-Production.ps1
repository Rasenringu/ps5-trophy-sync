param(
    [string]$EnvFile = '.local/production/app.env',
    [switch]$Tunnel,
    [switch]$ValidateOnly
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$resolvedEnv = if ([IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $root $EnvFile }
if (-not (Test-Path -LiteralPath $resolvedEnv -PathType Leaf)) { throw 'Create the production env file from deployment/production.env.example first.' }
$settings = @{}
foreach ($line in Get-Content -LiteralPath $resolvedEnv) {
    if ($line -match '^([A-Z_]+)=(.*)$') { $settings[$Matches[1]] = $Matches[2].Trim() }
}
if ($settings['PUBLIC_ORIGIN'] -notmatch '^https://[a-zA-Z0-9.-]+(?::[0-9]+)?$') { throw 'PUBLIC_ORIGIN must be the exact HTTPS origin without a trailing slash or path.' }
if ($settings['POSTGRES_PASSWORD'] -notmatch '^[a-fA-F0-9]{32,}$') { throw 'Use a random production password of at least 32 hexadecimal characters.' }
$common = @('compose','--env-file',$resolvedEnv,'-f',(Join-Path $root 'deployment/compose.production.yaml'))
if ($Tunnel) { $common += @('--profile','tunnel') }
& docker @common config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Production Compose validation failed.' }
if ($ValidateOnly) { Write-Host 'Production configuration is valid. No services or tunnel started.'; return }
if ($Tunnel) {
    & docker @common up -d --build
} else {
    & docker @common up -d --build db migrate api web gateway
}
if ($LASTEXITCODE -ne 0) { throw 'Production service startup failed.' }
Write-Host 'Production services started. Verify the configured HTTPS URL before connecting devices.'

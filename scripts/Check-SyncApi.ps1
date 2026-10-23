[CmdletBinding()]
param([string]$ServiceUrl)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
if (-not $ServiceUrl) {
    $config = Get-Content -Raw -LiteralPath (Join-Path $root 'config/public-service.json') | ConvertFrom-Json
    $ServiceUrl = [string]$config.origin
}
$uri = [Uri]$ServiceUrl
if (-not $uri.IsAbsoluteUri -or $uri.Scheme -notin @('https','http') -or $uri.UserInfo -or $uri.Query -or $uri.Fragment -or $uri.AbsolutePath -ne '/') {
    throw 'Use a service origin, for example https://trophy-sync.party or http://127.0.0.1:3000.'
}
if ($uri.Scheme -ne 'https' -and -not $uri.IsLoopback) { throw 'HTTP is allowed only for a loopback development service.' }
$source = ''
foreach ($name in @('main.py','contracts.py','observation_times.py','sync_validation.py')) {
    $source += [IO.File]::ReadAllText((Join-Path $root "api/app/$name")).Replace("`r`n", "`n")
}
$hasher = [Security.Cryptography.SHA256]::Create()
try { $expected = ([BitConverter]::ToString($hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($source)))).Replace('-', '').ToLowerInvariant() }
finally { $hasher.Dispose() }
$health = Invoke-RestMethod -Uri ($ServiceUrl.TrimEnd('/') + '/api/health') -TimeoutSec 15
Write-Host "Source validator: $expected"
$property = $health.PSObject.Properties['sync_validator_sha256']
if (-not $property -or -not $property.Value) {
    throw 'The reachable API has no validator fingerprint. Copy the current api/ source to the serving host, rebuild its existing stack, and check that the public hostname routes to that stack.'
}
$actual = [string]$property.Value
Write-Host "Service validator: $actual"
if ($health.status -ne 'ok' -or $actual -cne $expected) {
    throw 'The reachable API does not match this repository. Rebuild the serving API from these sources and verify the hostname/tunnel target.'
}
Write-Host 'OK: the reachable API matches this repository. No console contacted or sync submitted.'

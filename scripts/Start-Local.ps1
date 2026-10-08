[CmdletBinding()]
param([switch]$Build)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot\Doctor.ps1"
$envPath = Join-Path $root '.local\app.env'
if (-not (Test-Path -LiteralPath $envPath)) {
    New-Item -ItemType Directory -Force (Split-Path $envPath -Parent) | Out-Null
    $bytes = New-Object byte[] 32
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $secret = ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    $settings = "POSTGRES_PASSWORD=$secret`n"
    if (Test-Path -LiteralPath (Join-Path $root 'release.json')) {
        $hasher = [Security.Cryptography.SHA256]::Create()
        try { $identity = $hasher.ComputeHash([Text.Encoding]::UTF8.GetBytes($root.ToLowerInvariant())) }
        finally { $hasher.Dispose() }
        $project = 'ps5sync-' + ([BitConverter]::ToString($identity)).Replace('-', '').ToLowerInvariant().Substring(0, 12)
        $settings += "COMPOSE_PROJECT_NAME=$project`n"
    }
    [IO.File]::WriteAllText($envPath, $settings, (New-Object Text.UTF8Encoding($false)))
}
$argsList = @('compose','--env-file',$envPath,'-f',"$root\deployment\compose.yaml",'up','-d')
if ($Build) { $argsList += '--build' }
& docker @argsList
if ($LASTEXITCODE -ne 0) { throw 'Local service start failed.' }
$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:3000/api/health' -TimeoutSec 5
        if ($health.status -eq 'ok') { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw 'Containers started but web/API health did not become ready. Inspect docker compose logs; do not treat this as a working start.' }
$origin = 'http://localhost:3000'
foreach ($line in Get-Content -LiteralPath $envPath) {
    if ($line.StartsWith('WEB_ORIGIN=')) { $origin = $line.Substring(11) }
}
Write-Host "Configured browser origin: $origin. Listener: http://localhost:3000. No console contacted."
if ($origin.StartsWith('https://')) {
    Write-Host 'Login/register/pair writes require the configured HTTPS origin and secure cookies. A tunnel/reverse proxy must provide that origin.'
}

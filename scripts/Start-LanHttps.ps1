[CmdletBinding()]
param([string]$ServerIp, [ValidateRange(1024,65535)][int]$Port = 8443)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
& "$PSScriptRoot\Start-Local.ps1"
$tls = Join-Path $root '.local\tls'
New-Item -ItemType Directory -Force $tls | Out-Null
# Protect private keys in the workspace; do not change the machine's trust store.
$owner = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls $tls /inheritance:r /grant:r "${owner}:(OI)(CI)F" '*S-1-5-18:(OI)(CI)F' '*S-1-5-32-544:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Unable to restrict TLS key directory ACL.' }
$prepare = @("$PSScriptRoot\prepare-lan-https.py", '--port', "$Port")
if ($ServerIp) { $prepare += @('--server-ip', $ServerIp) }
& python @prepare
if ($LASTEXITCODE -ne 0) { throw 'LAN HTTPS preparation failed.' }
& docker compose --env-file "$root\.local\app.env" --env-file "$root\.local\lan-https.env" -f "$root\deployment\compose.yaml" -f "$root\deployment\compose.lan-https.yaml" up -d --build lan-api lan-https
if ($LASTEXITCODE -ne 0) { throw 'LAN HTTPS start failed.' }
& python "$PSScriptRoot\test-lan-https.py"
if ($LASTEXITCODE -ne 0) { throw 'LAN HTTPS validation failed; do not treat it as console TLS evidence.' }

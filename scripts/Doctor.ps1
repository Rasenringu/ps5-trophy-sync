[CmdletBinding()]
param([switch]$Network)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw 'docker not found. Start Docker Desktop and reopen VS Code.' }
$os = & docker info --format '{{.OSType}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker engine unavailable. Start Docker Desktop.' }
if (($os -join '').Trim() -ne 'linux') { throw 'Switch Docker Desktop to Linux containers.' }
& docker compose version
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose unavailable.' }
Write-Host 'OK Docker Linux engine and Compose.'
if (Get-Command git -ErrorAction SilentlyContinue) { & git --version } else { Write-Host 'Git not found (recommended for version control).' }
if ($Network) {
    $path = Join-Path (Split-Path $PSScriptRoot -Parent) 'config\local.json'
    if (-not (Test-Path $path)) { throw 'Run Configure-PS5.ps1 first.' }
    $c = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
    $client = New-Object Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync([string]$c.ps5_ip, [int]$c.elf_loader_port)
        if (-not $task.Wait(3000)) { throw 'Connection timed out.' }
        $task.GetAwaiter().GetResult()
        Write-Host 'TCP port reachable. No payload sent; this does not verify loader protocol or firmware compatibility.'
    } catch {
        throw ('TCP check failed; no payload sent. ' + $_.Exception.GetBaseException().Message)
    } finally { $client.Dispose() }
}

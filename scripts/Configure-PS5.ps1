[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$path = Join-Path $root 'config\local.json'
$source = if (Test-Path $path) { $path } else { Join-Path $root 'config\local.example.json' }
$config = Get-Content -Raw -LiteralPath $source | ConvertFrom-Json
while ($true) {
    $value = Read-Host "PS5 LAN IPv4 [$($config.ps5_ip)]"
    if ([string]::IsNullOrWhiteSpace($value)) { $value = $config.ps5_ip }
    $parts = $value.Split('.')
    $valid = $parts.Count -eq 4
    foreach ($part in $parts) {
        if ($part -notmatch '^\d{1,3}$') { $valid = $false; break }
        if ([int]$part -gt 255) { $valid = $false; break }
    }
    if ($valid) {
        $a = [int]$parts[0]; $b = [int]$parts[1]
        $valid = ($a -eq 10) -or ($a -eq 192 -and $b -eq 168) -or ($a -eq 172 -and $b -ge 16 -and $b -le 31)
    }
    if ($valid) { $config.ps5_ip = (($parts | ForEach-Object { [int]$_ }) -join '.'); break }
    Write-Host 'Enter a private LAN IPv4, for example 192.168.1.84.'
}
while ($true) {
    $value = Read-Host "ELF loader TCP port [$($config.elf_loader_port)]"
    if ([string]::IsNullOrWhiteSpace($value)) { $value = [string]$config.elf_loader_port }
    $port = 0
    if ([int]::TryParse($value, [ref]$port) -and $port -ge 1 -and $port -le 65535) { $config.elf_loader_port = $port; break }
    Write-Host 'Enter a port from 1 to 65535.'
}
foreach ($key in @('nanodns_project', 'nanodns_version')) {
    $value = Read-Host "$key [$($config.$key)] (unknown is OK)"
    if (-not [string]::IsNullOrWhiteSpace($value)) { $config.$key = $value }
}
$utf8 = New-Object System.Text.UTF8Encoding($false)
[IO.File]::WriteAllText($path, ($config | ConvertTo-Json -Depth 10), $utf8)
Write-Host 'Saved config/local.json (excluded from Git). No console contacted.'

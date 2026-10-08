[CmdletBinding()]
param([string]$CaptureDirectory)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
if (-not $CaptureDirectory) { $CaptureDirectory=Join-Path $root '.local\captures\native-format-prefixes' }
$captures=(Resolve-Path -LiteralPath $CaptureDirectory).Path
if (-not (Test-Path -LiteralPath $captures -PathType Container)) { throw 'CaptureDirectory must be an existing directory of authorized UCP captures.' }
& docker compose --env-file "$root\.local\app.env" -f "$root\deployment\compose.yaml" run --rm --no-deps --volume "${captures}:/captures:ro" api python -m tools.import_console_artwork /captures
if ($LASTEXITCODE -ne 0) { throw 'Artwork import failed. Inspect the bounded parser error; no console accessed.' }
Write-Host 'Static PS5 artwork/metadata cache updated. No console databases or credentials accessed.'

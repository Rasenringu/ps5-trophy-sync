$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$common = @('compose','--env-file',"$root\.local\app.env",'-f',"$root\deployment\compose.yaml")
$exists = & docker @common exec -T db psql -U sync -d postgres -tc "SELECT 1 FROM pg_database WHERE datname='sync_test'"
if ($LASTEXITCODE -ne 0) { throw 'Cannot inspect PostgreSQL.' }
if (($exists -join '').Trim() -ne '1') {
    & docker @common exec -T db psql -U sync -d postgres -c 'CREATE DATABASE sync_test'
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create isolated test database.' }
}
& docker @common run --rm --build test
if ($LASTEXITCODE -ne 0) { throw 'Application tests failed.' }

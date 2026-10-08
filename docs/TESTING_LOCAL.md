# Test locally

Start Docker Desktop Linux containers and run `./scripts/Start-Local.ps1` from
native PowerShell. Open http://localhost:3000. Use `-Build` after source changes.
Normal operation disables development controls, rejects mock imports and returns
404 for `/test`. No samples are automatically imported.

## Regression tests

- `./scripts/Test-Local.ps1` resets only the isolated `sync_test` database and
  enables synthetic fixtures there. It does not contact a console.
- `./scripts/Test-Web.ps1` checks browser layouts/privacy/navigation and uses
  generated local accounts for real account/pairing/social endpoint tests.
  These accounts are test fixtures, not native console evidence.
- `python scripts/test-lan-https.py` verifies the configured local certificate
  and hostname behavior separately.

Generated demo accounts can be inspected with `api/tools/clean_demo_data.py`.
Its default mode is a dry run; applying requires a PostgreSQL custom-format
backup. It protects every account/profile containing real records. Never use
console database edits for cleanup.

## Explicit development samples

For a deliberately temporary sample environment, set
`$env:ENABLE_DEVELOPMENT_TOOLS='true'` before starting/recreating the local Compose
API and web services. Both API and UI inherit this flag; production prohibits it.
Open `/test`, sign in, create a test pairing code, approve the simulated profile
and import sample data. Enable the labeled mock-import filter in My library.
Repeat import checks idempotency. Mock credentials remain in page memory; mock
imports remain in that test account until cleaned up.

Remove the environment flag and recreate API/web after testing. Keep samples
separate from real user accounts. See [hosting](SELF_HOSTING.md) for backups.

## Actual console sync

The browser uses http://localhost:3000; the installed PS5 worker uses validated
HTTPS at the configured LAN HTTPS endpoint. The console's localhost means the console,
not this PC. The current Trophy Sync title is PPSA99889. Native PS5 trophies,
playtime and automatic artwork have separate recorded console evidence in
[STATUS](STATUS.md). Web fixtures establish neither hardware support nor new
console validation.

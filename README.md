# TrophySync

TrophySync imports native PS5 trophies and recorded playtime into a self-hosted
web library. Pair a local console profile with a short-lived QR/code, then open
the PS5 application to sync directly over validated HTTPS. No PSN password or
permanent relay is required.

The web app includes game/trophy artwork, official package translations,
progress and trophy grades, recorded sessions, friends and comparisons.
It supports English, French, German, Portuguese, Brazilian Portuguese, Spanish
and Italian. Sharing defaults to friends only; public profiles require opting in.
Secret trophies stay concealed until the viewer earns them.

## Requirements

- Windows 11, native PowerShell and Docker Desktop running Linux containers.
- Python 3.12 or newer for local configuration scripts; Git for version control.
- Console baseline tested: PS5 firmware 8.00 with the user's kstuff setup,
  Payload Manager 0.5.2, ShadowMountPlus 1.7beta3 and FTPSRV 0.21.1 on port 2121.
  kstuff's actual runtime version and the installed nanoDNS identity are unknown.

The console reads native sources without modifying trophy/activity databases.
The extraction worker and the foreground application are separate components:
**one `TrophySync.elf`** in Payload Manager and **one TrophySync title
(`PPSA99889`)** on the PS5 home screen. Unrelated jailbreak tools remain necessary.

## Run the web application

From the repository root in native PowerShell:

```powershell
.\scripts\Doctor.ps1
.\scripts\Start-Local.ps1 -Build
```

Open **http://localhost:3000**, register and sign in. API documentation is at
http://localhost:8000/docs. Use this exact browser origin; session writes reject
other origins. Development samples and `/test` are disabled by default.

Local credentials are generated in ignored `.local/app.env`; PostgreSQL data
lives in a persistent Docker volume. Stopping the stack preserves that volume:

```powershell
docker compose --env-file .local/app.env -f deployment/compose.yaml down
```

## Build the PS5 ELF

Builds run in Docker, without moving the workspace to WSL. They compile locally
and never upload or execute anything on the console.

1. Configure the console address with `.\scripts\Configure-PS5.ps1`.
   The resulting `config/local.json` stays private.
2. Prepare a reachable development HTTPS endpoint. Replace the example IP with
   the **server PC's** LAN address:

```powershell
.\scripts\Start-LanHttps.ps1 -ServerIp 192.168.1.10
```

This writes the service URL and local certificate identity. The PS5 cannot reach
this PC through `localhost`. The build verifies that `config/local.json` matches
`.local/tls/identity.json` and embeds only the public CA certificate. Private keys
are excluded from all console packages.

3. Prepare the pinned SDK image (first build or after changing its inputs), then
   compile the current worker:

```powershell
.\scripts\Build-Tools.ps1
.\scripts\Build-Console.ps1 -HostTest
```

The output is **`artifacts/console/final-ui/TrophySync.elf`**.
`-HostTest` runs the native reader, pairing, queue, IPC and framebuffer regression
checks. Omit it for an incremental compilation. `-SmokeTest` checks the SDK alone.
The build downloads checksum-verified dependency sources and recreates its
current cache under `.local/console-build`; no previous release is needed.

4. Build the foreground title and complete local package:

```powershell
.\scripts\Build-ConsoleUI.ps1
```

Outputs:

- `artifacts/console/final-ui/PPSA99889/`: foreground application files.
- `artifacts/console/final-ui/TrophySync.elf`: the sole project worker.
- `artifacts/console/final-ui/TrophySync-PS5.zip`: both components, license notices
  and a checksum/source manifest.

The UI build generates its font/icon, checks eight screen states with sanitizers,
independently decodes the pairing QR, and compiles/signs the native title.
All build products remain ignored by Git. See [console build and installation](docs/CONSOLE_UI.md)
and [license obligations](docs/THIRD_PARTY.md) before distributing binaries.
The SDK is pinned; Ubuntu/apt build-image packages are not a frozen OS snapshot.

## Use on PS5

Install the worker through the existing Payload Manager under the exact filename
`TrophySync.elf`; install the `PPSA99889` folder through the existing ShadowMount
homebrew path. Keep one worker and one title. Do not enable the worker for
standalone autoload: this version requires the foreground application's IPC.

Open TrophySync from Media. For first pairing, scan its QR or enter the displayed
code at `/pair` on your web server while signed in. Confirm the selected console
profile. Subsequent launches reuse the saved connection and sync automatically.
Close with **PS button → Close App**. Enable existing FTPSRV on port 2121 for
console-local discovery; trophy packages then go directly to the HTTPS service.

Native trophy/playtime imports, saved pairing, repeat sync and automatic artwork
have console evidence. The redesigned foreground title is installed and its
bytes/registration are verified; its new screen and Close App still need a console
observation. PS4 support and passive resident synchronization are pending.
See [current status and limits](docs/STATUS.md) and [passive sync](docs/PASSIVE_SYNC.md).

## Tests and hosting

```powershell
.\scripts\Test-Local.ps1
.\scripts\Test-Web.ps1
```

API tests use isolated `sync_test`. Browser endpoint tests create labeled test
accounts in the development database; they do not import into your real account
or contact a console. See [testing](docs/TESTING_LOCAL.md).

For a later host/domain and optional Cloudflare Tunnel, follow
[self-hosting](docs/SELF_HOSTING.md). The installed console build trusts its
configured LAN endpoint; a public host needs a separately configured and
validated console transport build. No external deployment has been performed.

## Repository

| Directory | Purpose |
| --- | --- |
| `console/` | Current PS5 UI, worker, native readers and host regression fixtures |
| `api/` | FastAPI, Pydantic v2, SQLAlchemy 2, Alembic and PostgreSQL |
| `web/` | Next.js/TypeScript interface and browser tests |
| `contracts/` | Versioned import schemas and API contract |
| `deployment/` | Development/production Compose and container builds |
| `scripts/` | Current setup, build and verification entrypoints |
| `docs/` | Architecture, evidence, formats, privacy, hosting and licenses |

Dependency locks and vendor license notices belong in Git. Credentials,
`config/local.json`, `.local`, captures, databases, builds and generated reports
do not. See [preparing a Git repository](docs/GITHUB.md).

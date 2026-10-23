# TrophySync

TrophySync imports native PS5 and PS4 trophies and recorded playtime into a self-hosted
web library. Pair a local console profile with a short-lived QR/code, then open
the PS5 application to sync directly over validated HTTPS. No PSN password or
permanent relay is required.

The web app includes game/trophy artwork, official package translations,
progress and trophy grades, recorded sessions, friends and comparisons.
It supports English, French, German, Portuguese, Brazilian Portuguese, Spanish
and Italian. Sharing defaults to friends only; public profiles require opting in.
Secret trophies stay concealed until the viewer earns them.

The **Integrations** page adds title-based HowLongToBeat estimates, edition
selection/manual overrides, a private CSV export and keyless Exophase trophy
rates. A downloadable Chrome/Edge connector signs in on HowLongToBeat and
publishes reviewed progress totals from your browser session. Real account
publication still needs live validation. Existing optional PlatPrices selections
remain supported. See [setup and validation limits](docs/INTEGRATIONS.md).

Games with recorded activity appear even without imported trophies, including
homebrew recomp titles. Completed native foreground counters supply playtime;
incomplete sessions retain unknown duration. Native logger `CUSA` sessions can
appear as PS4 playtime entries (with the application ID if a name is unavailable).
Activity-only entries can use their installed application icon, including PS4
and recomp titles. Update the hosted API before the new worker; this added
artwork path is console-validated on the documented test build.
The PS4 adapter reads verified disposable copies of the selected profile's encrypted
images, checks the embedded profile/set, then imports stripped trophy state and
publisher TRP metadata/images. Original images are never mounted or written.
The reader and full hosted foreground sync are console-verified for the exact
build recorded in STATUS. Update the server before installing the schema-v4 worker.
Only existing per-profile state is imported; missing state is never invented.
See [current evidence](docs/STATUS.md).
Native trophy packages are bounded to 128 MiB, including Uncharted's observed
70.17 MiB package. Update both the console worker and server/web ingress for this fix.

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

On a fresh loopback development setup, open **http://localhost:3000**, register
and sign in. This workspace's local env now uses the public HTTPS origin and
secure cookies; login/pair writes require `https://trophy-sync.party` through
your HTTPS ingress. API documentation is at
http://localhost:8000/docs. Use this exact browser origin; session writes reject
other origins. Development samples and `/test` are disabled by default.

Local credentials are generated in ignored `.local/app.env`; PostgreSQL data
lives in a persistent Docker volume. Stopping the stack preserves that volume:

```powershell
docker compose --env-file .local/app.env -f deployment/compose.yaml down
```

New browser sign-ins last **30 days**, including browser restarts; signing out
revokes the session immediately. After updating the hosted API/web, sign in once
to receive the longer cookie. Existing sessions keep their earlier expiry.

## Build the PS5 ELF

Builds run in Docker, without moving the workspace to WSL. They compile locally
and never upload or execute anything on the console.

1. The default build targets **https://trophy-sync.party**. Its checked-in public
   endpoint and checksum-pinned Let's Encrypt roots live in
   `config/public-service.json` and `console/vendor/public-service-ca.pem`.
   No console IP, local CA or shared account/device token is embedded.
2. Each console resolves the hostname using its existing network resolver and
   validates the certificate chain, hostname and validity dates. DNS must resolve
   this domain correctly; a nanoDNS rule that redirects it will prevent HTTPS.
   Keep the console clock correct. No DNS setting is changed by TrophySync.

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

The 2026-10-23 native screen uses the website's blue/white sidebar, profile header
and pairing/sync panels; its title icon uses the same trophy/sync mark. The
current package and synthetic previews are local build outputs. This update has
not been installed or observed on a console; see [validation evidence](docs/STATUS.md).

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
observation. PS4 private-copy reading and integrated foreground sync are verified for the documented build. Passive resident synchronization is pending.
See [current status and limits](docs/STATUS.md) and [passive sync](docs/PASSIVE_SYNC.md).

## Your collection and profile

Libraries open with **Most recently played** sorting. Games without a recorded
activity date appear last; title and trophy progress sorting remain available.
**Most played (hours)** and **Most sessions** sort by descending recorded totals.
Incomplete or unverified sessions do not inflate either total; shared libraries
use their published aggregate session counts.
PS4/PS5 appears once as a platform badge on each game.

Console dates later than their server receipt are withheld; valid foreground
playtime still counts. Earlier imports use the profile's last-sync boundary,
sealed before a new sync advances it. Original source dates are retained.
Missing supported PS5 unlock dates recover from retained raw evidence. A console
state that has not been verified stays unknown, and incomplete sessions explain
the missing end/counter. No time is estimated from wall-clock gaps. Historical
timezone correction still requires console evidence.

Wolverine's four previously unknown PS5 trophy states now display as **locked**,
matching the user's console trophy-menu observation. Rebuilding the API corrects
existing imports without a new sync. A new worker also exports that supported
locked pattern directly: **update the hosted API before replacing the worker**,
because the older validator rejects that new locked-state interpretation.
The authorized clock diagnostic found the current console clock close to the PC
and explicit timezone markers in the source. No arbitrary two-hour shift is
applied. Native Uncharted's observed start-only session still lacks a duration.

PS5 regional releases that share a verified trophy-set identity combine their
existing trophies and recorded sessions on one game entry. Unique publisher
translations and normalized punctuation/case also match regional title labels;
ambiguous trophy stacks, sequels, editions and PS4/PS5 stay separate. This fixes
Demon Slayer's verified PPSA03457/PPSA03490 releases sharing NPWR23868_00.
Rebuild the hosted API to apply matching to existing imports; no console update,
reimport or database migration is required. Hidden games and favorites retain
their earlier application references when those entries merge.

The verified PS4 Nathan Drake Collection (CUSA02344) groups its existing imported
Drake's Fortune, Uncharted 2 and Uncharted 3 trophy sets on one collection card.
Expand **Games in this collection** to open each game's own trophies and
separately recorded playtime. Component artwork and trophy identities stay
distinct. **Shared collection playtime** is counted once; a collection counter
cannot establish the individual games' hours. Launching each
component can create its missing per-profile trophy state. Start-only sessions
remain incomplete until a valid native foreground end counter is available.
This correction needs an API/web rebuild on the service host; it needs no new
console worker, pairing, reimport or database migration. Already imported records
are regrouped when the library is loaded. Other regions are not inferred from
this console's verified publisher metadata.

Use **Hide game** on a card or in its details to remove it from your collection,
shared profile, friend comparisons and shared artwork access. **Hidden Games**
is visible only to you and includes **Unhide game**. Hiding applies across your
console profiles to the same reader/title identity, retains imports and survives
future syncs. PS4 and PS5 editions remain separate.

**My profile → Edit profile** provides a plain-text description, four themes,
four avatar styles and a favorite-game showcase, with a live preview. Favorites
must come from your visible, non-demo library and follow library visibility.
Hiding or revoking a favorite removes it from the showcase automatically.

Rebuild API and web together; Alembic migration **008** adds preferences without
deleting existing records. Local Windows: `scripts/Start-Local.ps1 -Build`.
For the separate hosted service, use its existing Compose/env workflow including
the migrate service. Keep the existing database volume, domain, cookies and
console pairing. No new dependencies or service configuration are required.

## Tests and hosting

The integration/mobile update uses migrations **009–010** and an API/web rebuild with
the existing volume/env file. It also repairs damaged accents and popup controls,
improves mobile dialog scrolling, and adds Apple/manifest PNG install icons.
After updating the host, remove and re-add an old iPhone home-screen shortcut to
refresh its icon. Physical Firefox/iPhone installation still needs verification.

```powershell
.\scripts\Test-Local.ps1
.\scripts\Test-Web.ps1
```

API tests use isolated `sync_test`. Browser endpoint tests create labeled test
accounts in the development database; they do not import into your real account
or contact a console. See [testing](docs/TESTING_LOCAL.md).

The hosted service is **https://trophy-sync.party**, on a separate host configured
by the user. This repository's local stack has also been configured with that
browser origin and secure cookies; plain localhost login writes will be rejected.
The public build has host DNS/TLS checks, but still needs a PS5 pairing/sync result.
See [public service setup](docs/PUBLIC_SERVICE.md) for installation, host settings,
TLS limits and the optional LAN development build.

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

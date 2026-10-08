# Current status

Updated 2026-10-08 after source/build/documentation cleanup. This file separates
console observations, local verification and pending gates. Historical prototype
sources and per-version instructions are retired; the supported source tree is
the current TrophySync application.

## Product

- Native PS5 trophy definitions/state, native recorded foreground playtime,
  automatic package artwork and official translations are implemented.
- Web libraries, compact/cards, grades/progress, descending session details,
  total recorded playtime, public opt-in profiles, friends and comparisons work.
- Browser-language support: English, French, German, Portuguese, Brazilian
  Portuguese, Spanish and Italian. Viewer-relative secret privacy applies to
  names, descriptions and icons.
- Revoked profiles and games with no imported trophies are excluded from libraries.
  Development samples and `/test` are disabled during normal operation.
- Local Docker services and separately configured production Compose are prepared.
  No external hosting, tunnel, publication, Git commit or push occurred in cleanup.

## Recorded console evidence

Baseline: FW 8.00 with the user's kstuff setup; actual kstuff runtime build and
nanoDNS identity remain unknown. Payload Manager 0.5.2, ShadowMount 1.7beta3 and
FTPSRV 0.21.1/2121 were observed. No etaHEN/onionHEN dependency.

Read-only native UCP/T2PD/T2TD decoding was matched independently against six earned
bronze trophies and one console-displayed unlock minute. A separate worker paired,
imported real records and reused its saved connection after Close App/reopen.
Repeat sync retained counts. The selected installation's latest checkpoint had
363 trophies across eight games, 89 activity records and 371 artwork PNGs; these
are a test-console observation, not fixed product limits.

A short user-observed game session produced 108 foreground seconds. The interrupted
rest/jailbreak-recovery test recorded 12 seconds before sleep and 120 afterward,
excluding sleep. Uninterrupted resume is not verified. Read-only locked SQLite
transactions use delete journal mode; native trophy snapshots are stable repeated
reads, not proven atomic multi-page generations.

The console transport reached LAN HTTPS with CA/IP validation and rejected
wrong-host/untrusted certificates. Real pairing, direct worker imports, artwork
uploads and replay were observed. The foreground sandbox cannot read native source
paths; bounded console-local IPC connects it to the separate worker.

## Installed title versus current source build

One foreground title remains: **TrophySync / PPSA99889**, contentVersion 01.001.000.
One project worker remains in Payload Manager: **TrophySync.elf**. Obsolete project
titles and worker/diagnostic aliases were removed in the prior authorized console
cleanup; unrelated user payloads, autoload/loader/DNS and pairing/queue storage
were preserved. No console was contacted during repository cleanup.

Installed foreground SHA256:
`5249d2163c5246b7c1509bb21e373b586a56ca0445c9db978f43c5bd60dd2644`.
Installed worker SHA256:
`5d8843c3d89e2bdd9d667ba9b523253b0d92f0da578988f4ed22dfdf4cbcd9d2`.
Registration/new icon and installed bytes were checked. **The redesigned foreground
screen, sync and Close App still need direct console observation.** Earlier
foreground rendering/pairing evidence does not validate this redesigned binary.

Cleanup renamed current modules, removed the unused prototype renderer and
retired historical packaging dependencies. Locally rebuilt worker SHA256:
`300774522efb59ea567bdcc69fef491f307576c459672ad7543938a91ad3afda`.
Locally rebuilt foreground SHA256:
`d63c25ab16caebb937e172c57a8f201942da21e40eef6ef9f10efeed3f6f1e29`.
These rebuilt files were **not** transferred or executed. The new manifest marks
console validation false; do not confuse installed and rebuilt hashes.

## Build and test evidence

Current entrypoints:

```powershell
.\scripts\Build-Tools.ps1
.\scripts\Build-Console.ps1 -HostTest
.\scripts\Build-ConsoleUI.ps1
```

Endpoint/TLS prerequisites and exact output paths are in [README](../README.md).
SDK v0.43 and dependency archives are checksum-pinned. The current build cache
`.local/console-build` was created fresh: Mbed TLS/SQLite and native title tooling/
zlib/runtime were rebuilt from verified sources. No old artifact, old manifest
or diagnostic ELF is required. The SDK CRT is recreated locally and its final
worker no-write hook is inspected; no installed SDK patch was made.

2026-10-08 cleanup validation, all exit 0:

- `Build-Console.ps1 -HostTest`: worker compile/no-write hook; native format,
  activity, discovery, pairing, private storage, queue, import acknowledgement,
  profile-scoped IPC, SQLite locking and framebuffer regressions.
- `Build-ConsoleUI.ps1`: current worker plus native title; font/license integrity,
  eight ASan/UBSan renderer states, independent pairing QR/expiry checks, native
  conversion/integrity inspection and self-contained current-source package.
- `container-test-console.sh` with an empty capture volume: current synthetic
  regression suite including JSON/binary TLS checks passes without personal
  captures; optional private-reference assertions skip when absent.
- Git audit: 244 visible source/documentation files; no private/generated paths
  or embedded private keys. Markdown links, Python/PowerShell syntax, shell LF
  and the current package file allowlist pass.
- Rebuilt current worker/title after transport header cleanup. Corresponding
  source/file hashes are sealed in `artifacts/console/final-ui/manifest.json`.

Prior web/API checks: 53 API tests and 18 browser tests passed for auth, ownership,
pairing, idempotency, social/public privacy, revocation, layout and translations.
The navigation follow-up passed 15 focused browser checks. Production web build
and isolated production Compose checks passed, including migrations through 007,
cookie/origin protection, disabled demo imports and artwork request limits.
Web/API behavior was not changed or re-tested during source cleanup.

## Repository cleanup and publication boundary

Historical diagnostic/experimental console sources, launch/deploy scripts,
per-version build instructions and one-off local helper scripts were removed
through the editing tool. Current modules have stable names; full dependency
license notices, meaningful synthetic tests, contracts and locks remain.
README and current docs were rewritten around actual behavior/build prerequisites.
Git-visible files contain no local config, credentials, captures, databases,
TLS keys or generated console packages; `.gitignore` also excludes dumps/keys/logs.

Automated shell deletion of old build/result/cache directories was rejected by
execution policy, with no detailed reason. Consequently old ignored binary/result
folders remain on disk. `scripts/Clean-GeneratedFiles.ps1 -WhatIf` reviewed 107
historical targets without deleting anything; its manual run can remove those
paths while preserving current files/data. It skips the old dependency cache
containing Linux reparse points rather than following links. That cache is ignored
and unused. See [Git preparation](GITHUB.md). Cleanup did not configure a remote,
create a commit, modify live data or reinstall the PS5 application.

## Remaining gates and next action

Next hardware opportunity: observe normal launch/sync/Close App/reopen of the
redesigned title. Independently validate second-profile isolation, full offline
recovery/live revocation and uninterrupted rest/wake. Passive sync is not enabled:
current worker requires UI IPC and has a bounded one-shot lifetime.
PS4 remains a separate unimplemented adapter. Public-domain transport requires
hostname resolution/trust configuration and its own console HTTPS result.
Account recovery/email verification and host restore/operational checks remain
before broad public registration. See [ROADMAP](ROADMAP.md) and
[self-hosting](SELF_HOSTING.md).

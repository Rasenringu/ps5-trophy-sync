# Build and install the current PS5 application

TrophySync has two components, both built from this repository:

- `TrophySync.elf`: read-only extraction, pairing, queue and HTTPS worker.
- `PPSA99889`: native foreground UI, registered as TrophySync in Media.

Use the commands and HTTPS prerequisites in [README](../README.md).
`scripts/Build-Console.ps1` builds the worker; `scripts/Build-ConsoleUI.ps1`
builds the worker and foreground package. Both are local-only operations.
Output: `artifacts/console/final-ui/`, with `TrophySync-PS5.zip` and a manifest
recording source/file hashes. No older build, result or manifest is consumed.

The build verifies pinned SDK/dependency archives, compiles Mbed TLS/SQLite,
creates the project-local no-write CRT, bakes the pinned OFL font, and builds
BlackBearReloaded's native tooling/runtime from source. No proprietary `libc.prx`
is copied from a console. Generated dependencies live in `.local/console-build`.
Full dependency configuration and sources are required for GPL binary distribution;
see [THIRD_PARTY](THIRD_PARTY.md).

## Installation

Use the user's existing Payload Manager and ShadowMount homebrew installation
workflow. Keep the worker's stable name **TrophySync.elf**, and use only the
**PPSA99889** foreground folder. The UI locates that exact worker through Manager;
its files normally live under `/data/pldmgr/payloads/TrophySync/`. Do not rename
the ELF without changing `console/ui/final_worker_config.h` and rebuilding.

Stage the foreground folder in an existing ShadowMount scan location. Use its
normal registration/rescan operation. For an update, close the title first and
follow the loader's normal replacement/re-registration procedure. Keep pairing
and queue storage intact. The repository's build scripts do not transfer files,
uninstall titles, modify databases or change autoload settings.

Open TrophySync from Media; confirm a single-use pairing code at `/pair` while
signed in. A returning connection is checked before sync. Keep the existing
FTPSRV 0.21.1 service on port 2121 for local source discovery. Files are read on
the console and uploaded directly to the HTTPS endpoint, without a PC data relay.
Use **PS button → Close App** to exit.

The current worker is intentionally bounded and waits for a valid foreground
IPC request. Adding it to an autoload list alone will not provide passive sync.
See [resident-mode limits](PASSIVE_SYNC.md).

## Verification

The build checks worker startup hook, native title conversion, framebuffer tiling,
pairing expiry and eight renderer states under ASan/UBSan. Independent QR decoding
verifies the public short-code URL and absence of a code after expiry/connection.
These are local checks, not hardware evidence. Real extraction/pairing/repeat-sync
results and remaining hardware gates are in [STATUS](STATUS.md).

The redesigned foreground title is installed with verified bytes and registration.
Its new screen/Close App still need direct console observation. Tests do not claim
compatibility with other firmware/loader combinations.

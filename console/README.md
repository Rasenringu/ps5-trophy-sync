# Console components

The current worker is `worker/main.c`; the foreground entrypoint is
`ui/final_main.c`. Native trophy readers live in `readers/`, durable batching in
`sync/`, pairing/private state in `pairing/`, and validated HTTPS in `transport/`.

Build from the repository root with `scripts/Build-Console.ps1 -HostTest` for
`artifacts/console/final-ui/TrophySync.elf`, or `scripts/Build-ConsoleUI.ps1` for
both worker and foreground title. Dependencies are bootstrapped from pinned,
checksum-verified sources. See [README](../README.md) for endpoint prerequisites
and [console installation](../docs/CONSOLE_UI.md).

The SDK startup privilege hook is weakened in a project-local CRT object and
replaced by a no-write return. `verify-elf.py` inspects the final worker hook;
the installed SDK is untouched. Source databases use read-only access. SQLite
reads retain native locking and reject unsupported WAL/hot-journal situations.
Native trophy pages are integrity-checked and double-read; stable reads do not
prove an atomic generation.

The foreground sandbox obtains only bounded status over console loopback. The
worker owns its private credentials/queue under `/data/trophy-sync-worker` and
uploads directly to HTTPS. It stops on profile change and has bounded retries
and lifetime. Standalone autoload/passive sync is not supported by this worker.

Host fixtures are explicitly synthetic. Optional private-capture assertions may
skip when captures are absent; a fresh clone does not need personal console
captures to compile or run the synthetic regression suite. See
[current evidence](../docs/STATUS.md), [formats](../docs/NATIVE_STATE_FORMAT.md)
and [licenses](../docs/THIRD_PARTY.md).

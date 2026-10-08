# Project instructions

Read docs/PROJECT_BRIEF.md, docs/STATUS.md, docs/ROADMAP.md and docs/SOURCES.md before implementation. This starter is a handoff, not an already implemented product. Preserve any work added after it was imported.

## Authorized scope
Implement a monorepo with console/, web/, api/, contracts/, deployment/ and docs/. Primary target: PS5 FW 8.00 with kstuff-1.13-fpkg-dr-test4.elf. User prefers kstuff; do not require etaHEN or onionHEN. nanoDNS is installed; exact project/version must be recorded, not guessed from 'latest'. A local relay PC is not the product's default sync route.

Proceed autonomously with repository implementation, research, compilation, local service runs and tests. Use config/local.json for the user-supplied console IP; ask only for information blocking hardware validation. Never claim console validation without a console result. Do not automatically send or run experimental payloads, reboot the console, change its DNS, or modify its databases. Before a payload test, explain its concrete behavior and obtain authorization unless the user has already authorized that test. Read-only data collection is the intended console scope.

## Engineering requirements
- Verify current upstream SDK/loader/graphics APIs and licenses. Pin versions/commits. Name third-party dependencies accurately and retain license obligations.
- Probe actual capabilities; do not infer kstuff version from an ELF filename, or an active nanoDNS service from an INI file. Use unknown/unverified when no reliable detector exists.
- Treat native PS5 trophies and PS4 backward-compatible trophies as separate reader adapters. Do not reuse PS4 paths/schema as established PS5 facts. Registration/unlocking code is not an exporter.
- Read console data consistently. Identify SQLite/WAL or other storage details first. Never edit trophy, activity, user or shell databases. Avoid inconsistent raw copies during writes. Keep captures out of Git and redact user identifiers in diagnostics.
- First milestone: compile a minimal diagnostic ELF, inspect supported firmware/privileges/profile sources, establish native trophy and playtime evidence. Build no fake parser with plausible paths.
- Native graphical screen needs a verified foreground homebrew launch/render path. A background ELF does not automatically render UI. kstuff is not a loader or autostart facility. Resident worker survival after closing UI must be tested independently of etaHEN.
- Mandatory console display: large high-contrast QR pairing link, short manual code, URL, selected profile, expiry, connected status, sync status and clear action-specific errors. Never display permanent credentials in a QR.
- Pair using short-lived, single-use server-issued device authorization. Signed-in user confirms console/profile and physical possession of code. Polling must be bounded and rate-limited. Issue cryptographically random revocable device tokens, hash server-side, protect local persistence. No PSN credentials needed.
- Local profile ID is unique only inside a console installation. Server-generated device UUID + profile identifier isolates pairing; enforce ownership and cross-account restrictions server-side. Reinstallation/cloning/relink behavior must be defined. No hardware authenticity or anti-cheat claim.
- HTTPS must validate certificates and hostnames. DNS reachability is not TLS success. Queue failed syncs durably; bounded backoff; idempotent imports; no destructive interpretation of absent rows.
- Playtime is log-derived, with incomplete sessions and uncertain clock information represented explicitly. Do not double-count snapshots. Preserve available unlock timestamps and unknown values.
- Web: Next.js/TypeScript; API: FastAPI/Pydantic v2/SQLAlchemy 2/Alembic; PostgreSQL. Docker Compose for local development. Lock dependency versions when implementing. Registration, login, device management, private dashboard and game/trophy/playtime views. Public sharing optional and off by default. Docker build/run requires working Docker Desktop WSL integration.
- Keep meaningful auth/ownership/pairing/idempotency/parser tests, plus compile checks. Mock data must be conspicuously labeled; never call a mock sync hardware verified.
- Do not embed secrets, push to GitHub, publish, or deploy externally without user instruction. Do not create paid API dependencies. The product itself does not require AI.

Update docs/STATUS.md with evidence, exact commands/results, unresolved questions and next action at each meaningful milestone. Keep README instructions aligned with actual working behavior. Persist an implementation plan in docs when useful so subsequent sessions can continue without this conversation.

## Native Windows environment
This version uses local VS Code/Codex on Windows 11 with PowerShell and Docker Desktop Linux containers. Do not move the workspace to WSL or require a WSL distro. Use scripts/Doctor.ps1, Configure-PS5.ps1, Build-Tools.ps1 and Build-Console.ps1. The Docker image is ps5-trophy-build:starter; source is bind-mounted at /workspace and SDK installed at /opt/ps5-payload-sdk. Local application runtimes may also live in Docker. User already grants local development/tool access; do not repeatedly ask for routine local Docker/build/test permission. Do not overwrite the user's global Codex configuration. Keep Windows/Docker path handling and LF shell scripts valid.

# Remaining work

Current implementation includes native PS5 trophies, native recorded playtime,
automatic artwork/translations, pairing, web libraries, optional public profiles,
friends/comparisons and local/production Compose. See STATUS for exact evidence.

1. Observe the redesigned foreground UI on the test console: pairing/status,
   normal sync, Close App and reopen. Installation alone is insufficient.
2. Validate independent second-console-profile isolation, offline queue recovery,
   live revocation and source-change handling on hardware.
3. Repeat rest/wake without restarting the jailbreak/worker to establish
   uninterrupted native session semantics. Preserve incomplete/uncertain values.
4. Apply the prepared Next.js 64 MiB artwork proxy fix on the Mini-PC; verify
   a real hosted PS5 upload after the local 10 MiB truncation reproduction/fix.
   Phone login issue resolved by using HTTPS; current public API probes work.
   Public ELF/title DNS/trust builds and host Mbed TLS checks pass; validate
   registration, console pairing and real hosted imports before distribution.
5. Add a separately researched PS4 backward-compatible adapter and its own tests.
6. Implement passive resident mode only after lifecycle, duplicate-start, game,
   profile-change, rest/wake and CPU/memory/network measurements under kstuff.
7. Before public registration, implement account recovery/email verification and
   validate host backups/restores, capacity and production operational monitoring.

Do not infer support from a filename, a successful build, mock fixtures or another
firmware's loader behavior. No external publication or autoload is currently enabled.

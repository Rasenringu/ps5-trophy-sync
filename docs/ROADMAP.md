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
4. Native Uncharted's 128 MiB package fix, recorded recomp/CUSA playtime,
   additional application icons and the three available PS4 trophy sets now work
   on the console/hosted account. Exact build and limits are recorded in STATUS.
5. Investigate absent per-profile state only from new evidence: Uncharted 2/3
   publisher definitions alone do not prove unlock state. Never guess collection
   application bindings or duplicate playtime. API replay/privacy tests pass;
   broader multi-profile/offline/lifecycle hardware checks remain in items 1-3.
6. Implement passive resident mode only after lifecycle, duplicate-start, game,
   profile-change, rest/wake and CPU/memory/network measurements under kstuff.
7. Before public registration, implement account recovery/email verification and
   validate host backups/restores, capacity and production operational monitoring.

Do not infer support from a filename, a successful build, mock fixtures or another
firmware's loader behavior. No external publication or autoload is currently enabled.

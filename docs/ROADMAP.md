# Remaining work

Current implementation includes native PS5 trophies, native recorded playtime,
automatic artwork/translations, pairing, web libraries, optional public profiles,
friends/comparisons, persistent hidden games, profile themes/bios/favorites and
local/production Compose. See STATUS for exact evidence.

1. Install/observe the 2026-10-14 foreground redesign on the test console: pairing/status,
   normal sync, Close App and reopen. Installation alone is insufficient.
2. Validate independent second-console-profile isolation, offline queue recovery,
   live revocation and source-change handling on hardware.
3. Repeat rest/wake without restarting the jailbreak/worker to establish
   uninterrupted native session semantics. Preserve incomplete/uncertain values.
4. Native Uncharted's 128 MiB package fix, recorded recomp/CUSA playtime,
   additional application icons and the three available PS4 trophy sets now work
   on the console/hosted account. Exact build and limits are recorded in STATUS.
5. User launched Uncharted 2/3 on 2026-10-19; their profile images now exist and
   the user confirms their trophy lists import. Publisher npbind/SFO metadata
   verifies CUSA02344 membership in the three sets. The server/web collection
   grouping and hours/session sorts are implemented; rebuild API/web on the
   separate service host. Keep incomplete playtime unknown; do not infer a
   component duration split from launcher activity. API replay/privacy tests pass;
   broader multi-profile/offline/lifecycle hardware checks remain in items 1-3.
6. Implement passive resident mode only after lifecycle, duplicate-start, game,
   profile-change, rest/wake and CPU/memory/network measurements under kstuff.
7. Before public registration, implement account recovery/email verification and
   validate host backups/restores, capacity and production operational monitoring.

Do not infer support from a filename, a successful build, mock fixtures or another
firmware's loader behavior. No external publication or autoload is currently enabled.

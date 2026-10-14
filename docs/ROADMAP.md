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
4. The user deployed the 128 MiB native package fix and reports Uncharted syncing;
   101 records were acknowledged. Deploy and hardware-validate the new independent
   application icon path/API and transport timeout fix; preserve pairing/queue.
   Local ownership/privacy/cache tests pass; this build has no console result yet.
5. Establish readable PS4 trophy state, then add a separate adapter and tests.
   Opening Attack on Titan's console trophy list left the FTP mount empty. Two
   expressly authorized capability probes did not verify any trophy exports;
   the second stopped reporting at trophy-library loading. The readable summary
   is profile-wide only. No further payload test is authorized. Native logger
   CUSA playtime and recomp counters are verified; PS4 unlock export is incomplete.
6. Implement passive resident mode only after lifecycle, duplicate-start, game,
   profile-change, rest/wake and CPU/memory/network measurements under kstuff.
7. Before public registration, implement account recovery/email verification and
   validate host backups/restores, capacity and production operational monitoring.

Do not infer support from a filename, a successful build, mock fixtures or another
firmware's loader behavior. No external publication or autoload is currently enabled.

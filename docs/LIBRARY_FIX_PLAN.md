# Missing library entries: continuation plan

2026-10-14. See STATUS for commands, exact hashes and hardware evidence.

1. Previous fix is now deployed by the user: native Uncharted sync succeeds;
   playtime includes recomp/CUSA games and observed PS4 names. Some older games
   still have no readable trophy source or optional name metadata.
2. New independent application artwork path is built and locally tested (62 API,
   6 focused browser tests, full console suite). Transfer polling/deadline handling
   and action-specific upload errors were improved. Current ZIP is at
   artifacts/console/final-ui/TrophySync-PS5.zip, console_verified=false.
3. User commits/pulls/rebuilds API on Docker host 192.168.1.100 using
   scripts/Start-Local.ps1 -Build, preserving env/database. New application-artwork
   endpoints must exist BEFORE replacing the worker. No migration is needed.
4. Test the new worker's normal sync with specific authorization or user installation:
   preserve foreground/pairing/queue/autoload and verify PS4/recomp/older icons,
   repeated sync/cache and unchanged durations. No host deployment or new-worker
   console test has occurred in this follow-up.
5. PS4 trophies need a separate verified reader. Existing sources are sealed;
   the user opened Attack on Titan's console trophy list, but FTP still sees the
   existing mount empty. The readable JSON summary contains only profile totals. Never invent a schema or treat definitions as earned state.
6. One authorized export-only capability probe returned an empty report; its
   runtime cause is unknown. Temporary staging/report were removed. Revised v2
   was specifically authorized and run once: filesystem library returned loaded=0,
   then reporting stopped at the trophy library load (278 bytes). No exports were
   verified. Own staging/report were cleaned. It called no trophy APIs, decrypted
   or mounted no images, and accessed no databases. No further probe is authorized.
7. If neither path establishes readable data, research a narrow read-only query
   interface before further implementation/testing. No RW mounting, authid/kernel
   changes, registration/unlocking or source database modification is authorized.

Private captures/diagnostic reports stay in ignored captures/library-investigation;
never put them in Git/packages. No dependency pins changed. User handles commits.

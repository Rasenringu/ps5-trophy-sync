# PS5 regional-release and localized-title matching — 2026-10-19

The reported public library splits PS5 Demon Slayer into NPWR23868_00 (47 trophies,
1,029 recorded seconds across two sessions) and PPSA03457 (1,219 seconds, one
session). Current joins require identical raw title text. Two bounded equal FTP
reads of each release's native param.json/trophy2/npbind.dat independently verify
that PPSA03457 (HP0177) and PPSA03490 (EP0177) share NPWR23868_00. The former
omits the hyphens around Kimetsu no Yaiba in the English title.

1. Reproduce with API regression fixtures; keep live/public snapshots private.
2. Resolve PS5 activity identity using reviewed explicit application bindings
   first, then unique publisher titles/translations with conservative punctuation,
   whitespace and case normalization. Preserve digits, sequel/edition words and
   meaningful symbols. Do not merge ambiguous independent trophy sets.
3. Keep matches within the same owned active console profile and source. Preserve
   original activity IDs and stored records, single-copy counters, unlocks,
   hidden preferences, image authorization and viewer-relative secret privacy.
   Existing favorite application references resolve to the canonical owned game.
4. Replay the public snapshot into an isolated test database with synthetic
   profile/session credentials to verify 47 trophies, 2,248 seconds/three sessions
   on one PS5 game. No production database or remote host write.
5. Run meaningful API/browser regressions and a local production build. Update
   STATUS/README. Existing hosted imports are corrected on load after API rebuild;
   no new console binary, reimport, pairing, dependency or migration is needed.

Matching relates application IDs to the same trophy set. It does not combine
independent regional trophy stacks, sequels, remasters, PS4/PS5 editions, accounts
or profile state. The reviewed registry can extend evidence-backed release IDs;
unknown/ambiguous identity remains separate instead of guessed.

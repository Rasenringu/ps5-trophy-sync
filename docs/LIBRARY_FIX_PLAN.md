# Missing library entries: completed reader fix and continuation

2026-10-14. See STATUS for exact commands, hashes and hardware evidence.

The user rebuilt the host and authorized the final foreground sync. Console
reports PS4 3 sets; user confirms trophies on trophy-sync.party. Private-copy
reader, schema-v4 imports and publisher metadata/artwork acknowledgements work.
All four original hashes remain unchanged against the fresh final-test baseline;
private staging is gone. Earlier source changes are documented separately.

Working worker SHA256:
4c99e2dfcd5e4556115241c9fe6450b0807f9f943a1e8e31be002e7454afb17f.
Foreground unchanged. Exact-hash packaging evidence marks this build verified.
Application-only artwork also improved; recomp/CUSA native activity remains an
independent reader and is never duplicated by a guessed trophy association.

Available state: Drake's Fortune 54, Attack on Titan 43, Naruto/Boruto 45 (two
earned). Only existing per-profile state is imported. Uncharted 2/3 conf packages
have no observed matching profile images; collection CUSA02344 and component
CUSA03280 are not guessed equal. Further investigation needs new source evidence.

User may commit remaining corrections/tests/docs. No further host rebuild is
needed for the final console-only fixes. No additional payload test is authorized;
future tests still require concrete permission under AGENTS.md. No original
mount/write/copy-back, unlock/register API, other-process permission change,
DNS change or reboot exists. Keys/captures stay private and out of packages.

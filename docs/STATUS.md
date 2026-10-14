# Current status

## PS4 foreground sync working on console and hosted service - 2026-10-14

User specifically authorized one transport-fix worker sync, then confirms:
?GOT PS4 3 sets and i see the trophies now?. The final reader count is published
only after all set visitors complete their durable import and validated package
cache/upload acknowledgement. This verifies the integrated PS4 reader, schema-v4
API and publisher artwork/metadata flow on the test configuration.

Working installed worker SHA256:
`4c99e2dfcd5e4556115241c9fe6450b0807f9f943a1e8e31be002e7454afb17f`.
Foreground unchanged:
`9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.
Expected source sets: Attack on Titan (43), Drake's Fortune Remastered (54),
Naruto/Boruto Connections (45, two earned). Queue audit confirms acknowledged
PS4 records; slots are reused, so surviving queue rows are not a complete library
count. Final audit: all four original image hashes unchanged against the fresh
stable pre-test baseline, two complete reads agree, no private reader staging
remains and installed worker hash matches. Earlier source changes remain recorded
below rather than being retrospectively called unchanged.

Exact worker/foreground/origin evidence is retained without personal identifiers
in console/validation/ps4-worker-2026-10-14.json. Packaging marks console_verified
only when those exact hashes/origin match; changed builds stay unverified.
ZIP regenerated and manifest/license/source/private-capture exclusion checked.
Artifacts: artifacts/console/final-ui/TrophySync-PS5.zip and TrophySync.elf.
No pairing, foreground or Manager autoload metadata changed; previous ELFs saved
privately. No agent commit/push or host deployment. User rebuilt the host.

Checks: 65 API tests; console suite and new PS4 snapshot/state/export/ACL/queue
fixtures; PS4 JSON and binary real TLS fixtures; three focused browser playtime
fixtures; actual captured C-export-to-Pydantic/package integrity interoperability;
SDK worker/no-write CRT compile. No test claims resident mode, other firmware,
all missing per-profile sets, or lifecycle/offline recovery validation.

Remaining source limitation: only Drake's Fortune has observed per-profile state;
Uncharted 2/3 publisher packages alone are not unlock state. Collection CUSA02344
is not guessed equal to component CUSA03280 or assigned duplicate playtime.
Next action for this fix: user may commit the remaining console corrections,
failure tests and documentation. Host is already compatible; no additional API
rebuild required for the final two console-only corrections. Broader lifecycle
and absent-state investigation remain in ROADMAP, not blockers for this reader.


## Protected PS4 reader imports state; transport-route correction - 2026-10-14

Corrected approved worker 68b12c84... reached PS4 artwork checking, reporting
HTTPS stage 0 errno 0. Six durable PS4 queue slots are acknowledged: Naruto/Boruto
45 trophies, two earned / 43 locked. No subsequent PS4 set was processed because
the first artwork check stopped the visitor. This verifies the protected-read
correction on hardware and actual schema-v4 imports into the rebuilt hosted API.

Identified a JSON transport bug: its path character filter rejected digit 4 in
the new exact /api/device/ps4-artwork/check route. Added an exact-route exception;
real TLS fixture now exercises that route and passes, plus existing certificate,
response-bound and deadline tests. Worker rebuilt/no-write CRT verified and ZIP
regenerated: 4c99e2dfcd5e4556115241c9fe6450b0807f9f943a1e8e31be002e7454afb17f.
No host change required. User authorized one transport-fix sync. Installed and
verified the exact 4c99e2df... worker hash, preserving previous ELF privately and
existing pairing/foreground/Manager settings. No manual launch sent; Media app
starts the worker. User asked to close/wait 40 seconds/reopen and check web results.
Fresh original baseline uses two equal complete reads of each of four images.

After this run Naruto's processed source hash is unchanged and private staging is
gone. Aggregate/Drake/Attack originals differ from the baseline preceding the
first worker run; these sets were not processed in the corrected run. This is
recorded as unexplained source change, not asserted source preservation. No
original write/mount/copy-back path exists. User reports no PS4/game-menu activity during the tests and that the PS4 Naruto
copy was removed for the PS5 version. That explains retained historical PS4 state,
but is not established as the cause of the other original-image changes.
Fresh hashes are stable and unchanged across the next audit.
Next: approved transport-fix sync, all three set/package ACKs and source audit.


## First integrated PS4 worker result and protected-read correction - 2026-10-14

User reports more artwork and PS5 9 games / PS4 0 games after the authorized
280316a... worker run. Queue audit confirms no PS4 records, all 22 surviving
native slots acknowledged. All four original PS4 image hashes remain unchanged;
no private reader stage remains. Conf/state source paths still exist through FTP.

Code review found the integration opened/enumerated protected PS4 sources before
its own credential guard, whereas the successful inspection acquired permissions
first. Correction now guards source enumeration and each entire read/snapshot,
then restores before visitors/network; original descriptors remain O_RDONLY and
only fixed private copies can mount. Host ACL fixtures now assert those reads
cannot occur without the guard. Missing source and permission/consistency errors
are distinguished; inaccessible data is no longer silently an empty collection.
ASan/UBSan collector checks pass including protected-read ordering and denied
setup/restoration. Corrected worker SHA256:
68b12c8418a3290bf927c63f01d5e774794bfda40602052af996e017df983211.
SDK compilation/no-write CRT passes; package regenerated, foreground unchanged.
User explicitly authorized one corrected sync. Installed and verified this exact
hash, preserving prior ELF privately and existing pairing/foreground/Manager
metadata. No manual launch sent; user asked to close/wait 40 seconds/reopen Media.
User could see only reader counts in the first run, not missing/rejected details.
Root cause remains an inference until corrected hardware results arrive.


## PS4 private-copy reader verified; worker integration under test - 2026-10-14

The user authorized one v3 private-copy inspection. Executed ELF SHA256
`c197a91bb3f28e67c6a20f6ce712f69faf0f7249d9374f4d4c7e30b66de530bc`.
Direct filesystem-library loading after temporarily setting only this process's
authid/capabilities succeeded. All four disposable images mounted and unmounted
normally; both original credentials were restored. All four original image SHA256
values were unchanged before/after. Hash-verified diagnostic uploads, exports and
empty private staging were removed. Captures remain ignored and contain personal
fields; they must never be published or included in distribution.

Actual per-set TRPTITLE evidence: NPWR09798_00 (Drake's Fortune Remastered),
54 locked, application CUSA03280; NPWR10954_00 (Attack on Titan), 43 locked,
CUSA03804; NPWR29343_00 (Naruto/Boruto Connections), 43 locked and two earned,
CUSA32836. Strict decoding checks embedded foreground profile and NPWR identity.
Unknown flags/timestamps remain unknown; the year-1-microseconds interpretation
is a candidate and is explicitly uncertain. Uncharted 2/3 conf packages exist,
but no matching per-profile image was observed. Absence is never zero trophies.
Nathan Drake Collection activity CUSA02344 is distinct from CUSA03280 and must
not receive duplicated playtime through a guessed name-based association.

Six actual PS4 TRP v3 metadata packages passed whole-package SHA1, independent
ESFM decryption and bounded publisher XML/PNG parsing (54/53/59/43/45/23 trophies).
The production adapter mounts only verified exclusive disposable copies and
restores its own credentials before queue/network operations. No original mount,
copy-back, trophy registration/unlock call or source database edit exists.
Schema v4 exports only trophy state, package digest and application binding;
account/local-user identity fields and sealed keys never enter uploads.

Validation so far: `container-test-ps4-state.sh` and
`container-test-ps4-copy-inspect.sh` pass ASan/UBSan and SDK compile checks;
`container-build.sh` worker compilation/no-write CRT checks pass;
`scripts/Test-Local.ps1`: 65 tests pass, including PS4 package ownership,
proof/digest binding, cache/idempotency, unknown state, privacy and exact
application joins. `Start-Local.ps1 -Build` built local API/web successfully.
PyCryptodomex 3.24.1 is pinned; its upstream license is retained in
api/licenses/PyCryptodomex.txt. Research repositories remain research only.

Additional completed validation: console suite passes, including bounded binary
TLS PS4 route and >3-second processing pause. New ASan/UBSan collector fixtures
verify copy-only mount arguments, unchanged originals, credential restoration
before visitor, unseal/decode/profile/visitor failures, failed-unmount staging
preservation and denied setup/restoration permissions. Export checks preserve
uint64 raw times/unknown state and reject range overflow or malformed bindings.
Worker queue/artwork fixtures cover schema-v4 ACK, cache hit/miss, duplicate
response keys and wrong title ACK. Three focused playtime browser tests pass,
including a single PS4 trophy/activity card and unknown state.
Actual stripped C exports validate in Pydantic and match captured TRP digests,
all grades and 54/43/45 counts (two earned in the latter).
OpenAPI and snapshot-v4 contracts regenerated; API/web rebuilt and healthy locally.

Packaged worker SHA256:
`280316a66384cdb2d9019133243defc4fd73fd9b230122e06b1e0d47ec9abbd8`.
Foreground unchanged:
`9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.
ZIP: artifacts/console/final-ui/TrophySync-PS5.zip; console_verified=false.
User created commit 1986cec (PS4 trophies fixes) during this work; no agent commit
or push occurred. Remaining documentation/failure-test updates stay reviewable.
User confirmed the remote host rebuild is live and explicitly authorized one
worker sync of the exact hash above. Read-only hosted HTTP probes were blocked
(403 public edge / timeout direct port), so host capability is user-confirmed.
Installed that exact ELF at the existing TrophySync Manager path, verified
uploaded SHA256 and saved the prior matching worker privately. Pairing/metadata,
foreground, queue and Manager autoload settings were preserved. Four original
PS4 image baseline hashes recorded privately before installation.
No manual worker launch was sent; the foreground app's existing bridge starts it.
User was asked to open/reopen Media TrophySync and report the final sync status.
Next: verify acknowledged PS4 records, UI completion, cleanup and unchanged
source hashes. Integrated console validation is still pending.
Earlier diagnostic-preparation entries below are historical, superseded here.

## PS4 repository research and disposable-copy diagnostic prepared - 2026-10-14

User requested continued PS4 work and Git repository research. Inspected primary
repositories at exact revisions, without running their payloads:

- hzhreal/PS4-vsh-utils `b8edba35450c69b13f2c67e0dfb7e66f5b37a947`:
  dedicated sceFs*MountTrophyData options/export family, not a verified RO mount.
- n0llptr/Playstation-5-Save-Mounter
  `1a0281ea9794afadc2e2da345ca0b66e5db45bc7`: linked FS imports and pfsmgr
  sealed-key operation; its original mount/copy-back workflow is not reused.
- maxton/LibOrbisPkg `643477263b2644e0803e0f58b8726ea4e3f3b7d4`:
  userspace encrypted PFS reader (LGPLv3). Research only; no code incorporated.
- flatz/pkg_pfs_tool `4e74afa98b0f57b2b50a2182c1ef89905dc040a7`:
  PFS/saved-data key derivation and signature validation. Saved-data key schedule
  differs from the generic package reader; configuration has placeholder keys.
  No code/keys incorporated and no assumption that generic decryption suffices.

Two equal bounded 1024-byte FTP header reads for sce_trop and all three observed
PS4 trophy images match PFS version=1, magic=20130315, signed/encrypted mode=13,
blocksize=32768, 1024 inodes and 23 inode blocks. These are header evidence only;
no live SQLite DB was copied and no earned-state parser is inferred. Headers
report clean=0; stable reads alone are not atomic snapshots. A mounted disposable
copy must pass filesystem/DB consistency checks before any eventual import.

Prepared `PS4CopyInspect.elf`, not yet run. No-write CRT, statically linked SDK
FS exports (nm verifies trophy-specific mount/unmount exports in SDK v0.43).
It creates a private exclusive /data/trophy-sync-ps4-inspect, reads source images
through O_RDONLY and a shared record lock, copies with bounds, compares a second
complete pass and rejects source stat/byte changes. Destination must be private,
exclusive, empty, owned regular storage; writable source descriptors rejected.
Only the fixed private copy paths can reach sceFsMountTrophyData; no copy-back
exists. Kernel may modify disposable copies; originals are never mounted/written.

The diagnostic temporarily changes only its own authid (then restores), uses
/dev/pfsmgr sealed-key operation with volatile memory erasure and no key output,
mounts private copies, reports bounded file headers/SQLite schemas through the
existing deny-write query-only reader, and preserves only bounded non-SQLite
TRPTITLE/TROPUSR binary state files. It unmounts its own copies normally, with no
forced unmount, database editing, trophy API calls, uploads, DNS changes or reboot.
Failure can leave private staging; preserve it for review until unmounted.

`container-test-ps4-copy-inspect.sh`: ASan/UBSan tests pass source preservation,
no overwrites, descriptor permissions, private destination, bounds, SQLite source
rejection and mid-verification mutation. PS5 compile/no-write startup check passes.
SDK compilation initially hid flock under POSIX feature macros; replaced it with
the declared fcntl shared nonblocking record lock. Build SHA256:
`084cc0515fba57d64d12d5a936ee105621b387c55f510949f6f3574a803acf59`.
No experimental payload was sent. A specific authorization request explaining
the private-copy mounts, in-memory key operation and own authid is pending under
AGENTS.md. Next: execute once if authorized, establish actual PS4 file/schema
state, then implement/test a separate adapter and PS4 API/web identity handling.

## Authorized PS4 probe v2 and trophy-menu check - 2026-10-14

User confirms the PS5 trophy menu shows both Attack on Titan and Nathan Drake
Collection and opened Attack on Titan's trophy list for this check. Read-only FTP
MLSD still found `/mnt/pfs/trophy/<profile>/data/sce_trop` empty. No mount/unmount
or source database action was performed. This does not establish that trophies
are absent; the console menu confirms they exist through another access path.

The user explicitly authorized **one revised PS4Capability.elf run**. Executed
SHA256 `24f593d3d0a2dc1fc3d770ae192a45eb07eb1b948d817b9a987caa925cd5aadc`;
verified upload bytes before launching once through observed Manager 0.5.2.
Manager returned OK. The unbuffered report now contains **278 bytes**:

- Initial probe header was written.
- `/system/priv/lib/libSceFsInternalForVsh.sprx` returned loaded=0.
- Final checkpoint is the load attempt for
  `/system/common/lib/libSceNpTrophy.sprx`; no result/export checkpoint follows.

Report remained unchanged on recheck. The cause of the stopped report is unknown;
no verified trophy export availability or successful reader result. FTP/Manager
remained responsive, Manager listed 89 processes with no identifiable 'capab'
entry; this does not establish that no generically named process remains.
No process was killed. Only the hash-verified own staging ELF, empty staging
directory and identified v2 report were removed. FTPSRV returns 226 for DELE/RMD,
which ftplib.delete rejected after deletion; direct sendcmd finished cleanup
without further execution. Private attempt/report/mount evidence is under ignored
captures/library-investigation. No subsequent payload was run or authorized.

Also observed an actual **75-byte JSON** PS4 trpsummary.dat outside the sealed
image. Two equal FTP reads, non-SQLite header, format=1 and earnedTrophies grade
totals; no title identifiers or per-trophy state. This is aggregate profile data,
not a game-level exporter. Retained privately without uploading/importing it.
Primary MyTrophies-PS4 source independently reads the same aggregate JSON shape;
no code was copied, dependency added or per-game parser inferred. Additional
read-only listings found no alternative trophy mount under /mnt or a visible
/system_data/priv/trophy directory. The exact sealed data path remains unchanged.

**Next PS4 step:** establish a query interface/ABI or another read-only source
that exposes game identity and earned/timestamp state. SDK headers alone and
stubbed emulator functions do not establish those interfaces. Do not repeat
library loading or escalate to mounting/decryption/registration/unlocking based
on these results. Another experimental payload requires a concrete compiled
probe and fresh authorization. The application-artwork build/deployment gate
from the entry below remains unchanged; PS4 trophy support is still incomplete.

## Hosted sync follow-up and independent application artwork - 2026-10-14

This entry supersedes the deployment gates in the earlier investigation below.
The user installed the previous worker and rebuilt the Docker host at
192.168.1.100. FTP hash verification matched worker
`7b03fe5968764e6abd9f8d66c64bd0c1b5b0737374d2251e2cfb02270adf1e8b`.
Anonymous hosted health/OpenAPI (Mozilla User-Agent) confirmed health and CUSA
activity acceptance; frontend source confirmed the updated library navigation.
The user reports a successful retry and native Uncharted now working. Read-only
queue inspection found 101 acknowledged Uncharted records, Simpsons 192 seconds
and Sonic 406 seconds. Reusable queue slots are not a complete server audit.
The screenshot confirms older activity-only entries, PS4 names and some CUSA-ID
fallbacks. Missing trophy sources are not treated as deletions.

New implementation: activity-only applications get their own available appmeta
icon, independently of trophy packages. Exact PPSA/CUSA session IDs bound source
paths; two stable bounded reads, selected-profile checks and authenticated cache
checks precede uploads. API validates PNGs, real native activity, ownership and
revocation; private/shared image access enforces visibility before ETags. Existing
DeviceArtwork storage is reused with no migration. CUSA activity cannot alias a
same-named native PS5 trophy set. Available console icons were verified over FTP
for Attack on Titan, Nathan Drake Collection, Simpsons, Sonic, Alan Wake,
Apsulov and Demon Slayer. No publisher assets are included in Git.

The user's initial error was only 'artwork https stage 12 errno 0', followed by
success on retry. Its precise return code is unknown. Independently reproduced:
a 3.5-second TLS response pause incorrectly exhausted a 3-second select slice
inside a longer request deadline. Fixed slice retries while enforcing the total
deadline, expanded binary transfer budget to 180 seconds, and added phase/byte
progress to upload errors. This reproduction is not proof of the earlier
hardware error's cause.

Validation (local unless stated):

- `Test-Local.ps1`: **62 passed**, one existing Starlette/httpx warning; includes
  application image ownership, import prerequisites, PNG bounds, cache/replay,
  private/shared visibility, revocation and CUSA/PS5 identity separation.
- `container-test-console.sh`: passed native readers, transport/TLS, pairing,
  queue, IPC and SQLite suites. Added ASan/UBSan application icon reader cases
  and select-slice/hard-deadline regressions. `container-test-worker-import.sh`
  passed again after cached/uploaded/malformed/mismatched application ACK cases.
- Focused Playwright playtime/public-profile/trophy-privacy/library-layout:
  **6 passed**, including authorized activity-only PS4 artwork.
- `Start-Local.ps1 -Build`: local production startup/health passed, existing
  volumes preserved. Contract export in API image with PYTHONPATH=/app passed.
- Final `container-build.sh` and `python scripts/package-final-ui.py`: passed.
  New worker SHA256:
  `f67ea6bbbf9477ebc4f731311e11e56d8f4422e148e0af7bf5e43861e3ae55d4`.
  Foreground remains
  `9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.
  Package: artifacts/console/final-ui/TrophySync-PS5.zip;
  manifest console_verified=false for the added artwork path.

**PS4 capability test:** user authorized one PS4Capability.elf run. Built with
the no-write startup hook, launched once through observed Payload Manager 0.5.2
from its own staging directory. It only loaded two libraries and looked up export
names, with no trophy API invocation, mounting, key decryption, database access
or uploads. Executed SHA256:
`e0bc06fbaae999431c0aabb59d14429ea0538aef394ee1375992b16f2d560735`.
Launch returned OK, but the private report remained **zero bytes** after 30
seconds; no usable capability result. Runtime cause is unknown. FTP/Manager
remained responsive. Hash-verified own staging ELF, empty report and empty
staging directory were removed; no process was killed. Redacted attempt evidence
is ignored under captures/library-investigation. Do not infer unavailable exports
or successful PS4 support from this attempt.

Prepared revision v2 adds unbuffered checkpoints flushed before every dynamic
load/export lookup. Compile/no-write check passed; SHA256
`24f593d3d0a2dc1fc3d770ae192a45eb07eb1b948d817b9a987caa925cd5aadc`.
It has NOT been run; fresh specific authorization was requested. Separately,
asked whether the console trophy menu shows the missing PS4 lists and whether
opening a list exposes a readable existing mount. PS4 adapter remains gated on
actual source/interface evidence, not inferred from save-mount or unlock code.

Next: user commit/pull/rebuild the hosted API for the new application-artwork
routes BEFORE installing the new worker; then verify normal sync/icons/replay.
This session has not updated that host or the installed worker. Continue the
PS4 investigation using the trophy-menu result or an authorized revised probe.
No commits/pushes, source DB changes, mount calls, DNS changes or reboots.

## Missing games and playtime-only entries - 2026-10-14

Read-only FTP at the configured console IP/2121 observed FTPSRV 0.21.1.
User identified missing PS4 games as Attack on Titan and Uncharted: The Nathan
Drake Collection. Native PS5 Uncharted: Legacy of Thieves Collection uses
`NPWR26589_00`; its UCP is **73,575,712 bytes**, above the former 64 MiB cutoff.
Two equal state reads were captured without copying any live database. The
updated native parser joins all **101 locked trophies**; API readers accept its
101 definitions and 102 images. Exact activity/trophy metadata names match.
This is real source parsing evidence, not a completed hosted console sync.

The user explicitly authorized **one LibraryDiagnostic.elf test**. No payload
was sent to port 9021 (connection refused). Observed Payload Manager `/version`
returned 0.5.2; its existing allowlisted launch route ran the diagnostic once
from a separate test directory. Launch returned OK and FTP retrieved the report.
Executed diagnostic SHA256:
`b5308f79ede45bc8753ff46ea2dc5548a6da826f345fdb0a4e2603a9d2c8943b`.
It used locked, query-only SQLite through the existing deny-write VFS, wrote only
its own report, and performed no imports, mounts, patches or credential reads.

Console results: 975 relevant log rows, 169 sessions, 159 complete, 10 incomplete,
zero reader rejections. Simpsons (`PPSA74207`) has one complete session / **192
foreground seconds**; Sonic Unleashed Recompiled (`PPSA99902`) has two / **406
seconds**. Native logger `CUSA` sessions are present, including CUSA03804 and
CUSA02344. Native Uncharted currently has a start-only session, with duration
unknown. These are available recorded sessions, not lifetime totals.

The console diagnostic established app.db `tbl_contentinfo(titleId,titleName)`
and delete journaling. The new optional PS4 name lookup probes that schema,
uses a bounded locked read transaction, and falls back to the logged ID when
metadata is absent/unsupported/ambiguous. Its new name query is host-tested and
compiled, but has not yet run on the console. Existing malformed PS5 param.json
still rejects; missing optional names now retain sessions rather than hiding them.

PS4 trophy state remains **unimplemented/unavailable**: FTP exposed sealedkey/
trophy.img containers; the existing mounted sce_trop directory was empty. Both
checked PS4 trophy database locations returned SQLite rc14 (cannot open). No
image mounting, decryption, registration/unlocking or DB modification was attempted.
Opening a PS4 trophy list and rechecking the existing mount is still a next step.

Implemented:

- UCP/transport/API/Next/nginx bounds agree at 128 MiB. Stable second package reads
  compare 64 KiB chunks, retaining one full package buffer instead of two.
- Activity-only games appear in private libraries and permitted shared totals;
  trophy bars/grade counters are omitted when trophies are not imported.
- Native activity accepts PPSA/CUSA, preserves exact identifiers/provenance and
  incomplete durations, and displays CUSA entries as PS4. This is not PS4 trophy
  support. Activity sync now runs before trophy/artwork collection so an artwork
  failure cannot prevent playtime import. Zero trophy sets no longer block playtime.
- Ownership, revocation, mock filtering and public session redaction remain tested.
  Snapshot3/OpenAPI regenerated; earlier snapshot schemas are unchanged.

Commands/results (local unless stated):

- `python scripts/inspect-console-library.py`: authorized read-only FTP inventory
  and native file captures; private outputs in ignored captures/library-investigation.
- `docker run --rm --mount type=bind,source=C:\git\ps5-trophy-sync-windows,target=/workspace
  ps5-trophy-build:starter bash /workspace/scripts/container-build-library-diagnostic.sh`:
  compile/no-write startup inspection passed. `python scripts/run-library-diagnostic.py`:
  one authorized Manager launch/report success after the unavailable direct loader.
- `Build-Console.ps1 -HostTest`: worker/full native, pairing, queue, IPC, SQLite and
  transport suites passed. After final reader/order changes, focused native activity
  and worker-import regressions plus `container-build.sh` passed. Added synthetic
  CUSA/recomp/missing/ambiguous name checks and source/sidecar byte preservation.
- `container-test-native-readers.sh`: passes added >64 MiB UCP and exact collector
  second-pass chunk/boundary/symlink/unchanged-source regressions under ASan/UBSan.
- `Start-Local.ps1 -Build`: production API/web build and local health pass, existing
  database volume preserved. `Test-Local.ps1`: **59 passed**, existing one
  Starlette/httpx deprecation warning; includes large UCP, activity-only ownership,
  revocation/shared privacy and CUSA identity/replay tests.
- Focused Playwright playtime/library-layout/trophy-privacy/public-profile: **5 passed**.
- `python scripts/test-web-upload-proxy.py --size-mib 71 --size-mib 128`: complete
  MOCK bodies and hashes pass on isolated network, no real token/database/console.
- Actual captured Uncharted parsed using native-join-cli and API artwork readers;
  no observations were uploaded to any server during the investigation.
- `python tools/export_contracts.py /workspace/contracts` in API image with
  PYTHONPATH=/app: passed. Initial invocation without PYTHONPATH failed and was corrected.
- `python scripts/package-final-ui.py`: refreshed ZIP/manifest. New worker SHA256
  `7b03fe5968764e6abd9f8d66c64bd0c1b5b0737374d2251e2cfb02270adf1e8b`.
  Foreground binary unchanged:
  `9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.

**Deployment/validation gate:** the hosted service is on a separate host; only
this Windows PC's local stack was updated. Apply the updated API/web (and nginx
if used) on that host **before** installing the new worker: the older API rejects
CUSA activity IDs and packages above 64 MiB. New worker/title ZIP is prepared at
artifacts/console/final-ui/TrophySync-PS5.zip, with console_verified=false. The
installed TrophySync worker/title were not replaced or run by this session.
Authorize the updated worker's normal hosted sync test after the server upgrade;
validate real imports/replay/Uncharted upload and the PS4 name query. Readable PS4
trophy evidence remains a separate gate. See [continuation plan](LIBRARY_FIX_PLAN.md).

User identified the Docker service host as 192.168.1.100 and will commit/pull the
changes there themselves, then rebuild its existing stack. Remote SSH/Docker TCP/
PowerShell were unavailable; SMB returned access denied. No remote files,
containers or database volumes were changed. Do not commit/push on the user's behalf.
An anonymous hosted `/api/openapi.json` check returned 403, so the current public
API schema/version could not be verified from here; do not infer host deployment
from local build success. Revised diagnostic source (profile suffix redaction and
new optional metadata lookup) was recompiled locally but not rerun on the console.

The first diagnostic exposed profile-suffixed shell table names. Local report
and report-printing code now redact those suffixes; captures remain ignored.
FTP cleanup hash-verified the executed diagnostic against the local artifact,
then removed only that uploaded file, its now-empty test directory and its own
report. The redacted local report is preserved. No installed worker/title,
autoload settings, credentials/queues or source databases were changed.

## PS5 artwork upload truncation fix - 2026-10-08

User confirms the phone login problem was use of HTTP rather than HTTPS; Safari
and desktop work. Focus moved to the PS5's native trophy/artwork failure. Remote
API trace shows `ClientDisconnect` inside `/device/artwork` while reading the
stream. No payload or console action was performed by this session.

Reproduced a concrete defect in the built Next.js 16.4.0 rewrite to port 8000:
an isolated 11 MiB MOCK upload delivered exactly 10,485,760 of 11,534,336 bytes.
Next logged `Request body exceeded 10MB for /api/device/artwork`. The declared
full Content-Length survives truncation, consistent with the API disconnect.
This is a local reproduction, not proof of the user's package size or every
possible disconnect cause. The old 30-second proxy timeout was also shorter
than the console binary transport's 60-second request deadline.

Changes:

- `web/next.config.ts`: proxy buffer 64 MiB, matching API/UCP maximum; proxy
  timeout 70 seconds. API still applies 2 MB limits to non-artwork requests,
  profile/device authentication, artwork bounds and rate limits.
- API: interrupted/incomplete artwork streams fail with explicit HTTP 400;
  partial bytes never reach the cache writer. Logs record byte count only.
- Worker: specific artwork check/upload HTTP/TLS failures and queue errors
  survive collection failure handling; generic collection errors no longer
  overwrite already-published errors. No reader/source/pairing path changed.

Evidence/commands:

- `python scripts/test-web-upload-proxy.py`: failed before the fix with the
  exact 10 MiB truncation. Fixture runs a built web container and MOCK receiver
  on a fresh isolated Docker network; no real API/db/token/console contact.
- `Start-Local.ps1 -Build`: fixed production web compile/local API restart pass.
- `python scripts/test-web-upload-proxy.py --size-mib 11 --size-mib 64`: both
  pass complete byte counts and SHA256 after the fix; fixture containers/network
  removed. No timeout warning/truncation at the 64 MiB boundary.
- `Test-Local.ps1`: 56 passed, one existing deprecation warning; added interrupted
  ASGI stream and mismatched Content-Length checks with no artwork cache writes.
- `container-test-worker-import.sh`: passes queue/idempotency tests plus precise
  artwork HTTP/TLS errors retained after collection failure. `container-build.sh`
  compile/no-write startup inspection passes; `package-final-ui.py` refreshed ZIP
  and source manifest. Foreground binary was unchanged and not recompiled.

Current worker SHA256:
`a88b0d55fa8f353b2fe07da7f8de7887d538db21a50826bbc72dce2f5f75227b`.
Foreground SHA256 remains
`9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.
Outputs remain `artifacts/console/final-ui/TrophySync.elf` and
`TrophySync-PS5.zip`. Manifest remains `console_verified=false`.

Next action: copy updated host source to the Mini-PC, run
`scripts/Start-Local.ps1 -Build` with its existing env/database, then observe a
normal user-authorized PS5 sync. No tunnel/port/domain/env change is needed for
this fix. The worker update improves diagnostics; the server fix is essential.
Do not remove volumes or pairing/queue storage. No remote deployment, push or
new PS5 execution occurred here.

## Registration/API routing audit - 2026-10-08

User reports desktop registration works but Firefox on an iPhone 16 Pro on the
same Wi-Fi displays the generic French connection error. Earlier supplied API
logs include browser login/register 403, while diagnostic empty registration
requests reached 422. The previous client hid plain-text origin rejections as
connectivity failures. No direct access to the remote host or physical phone.

- `python scripts/test-api-routes.py`: 28/28 safe anonymous route probes pass on
  trophy-sync.party; two successful writes intentionally skipped. Report in
  `artifacts/tests/public-api-routes.json`. Health 200, empty register/login 422,
  private routes 401, nonexistent public player routes 404. Port 3000's Next.js
  rewrite reaches the API; a separate tunnel to 8000 is not required.
- Read-only hosted browser probes: desktop Chromium, mobile Android Chromium
  and iPhone WebKit all load `/login` and receive expected 422 for empty-register
  fetch. No account created; this does not reproduce/validate physical Firefox.
- Origin errors now use JSON with a fixed error code/configured URL. API logs
  only sanitized origin classification/expected origin. Missing/null/malformed/
  wrong Origin remains rejected. Client displays origin, Cloudflare challenge
  and unexpected HTTP errors separately; six locale dictionaries updated.
- `Start-Local.ps1 -Build`: updated local API/web recreated, production Next.js
  build passes, existing database volume preserved. Remote host unchanged.
- `Test-Local.ps1`: 54 passed, one existing Starlette/httpx deprecation warning;
  includes JSON/malformed/missing/null origin refusal with no account creation.
- Focused `playwright.mobile.config.ts`: 8 passed, WebKit/Chromium mobile error
  cases (origin JSON/legacy text, proxy HTML, Cloudflare challenge). All API calls
  intercepted; no account created. Initial test harness failures were corrected:
  WebKit does not accept Chromium's host-resolver flag; Next's route announcer
  requires scoping assertions to the form's actual error paragraph.

Next action: compare Safari on the affected iPhone, deploy these diagnostics
to the Mini-PC, reproduce once and inspect origin-rejection/API/Cloudflare logs.
The physical Firefox failure remains unconfirmed; no CSRF checks were weakened.
See [browser troubleshooting](WEB_TROUBLESHOOTING.md). The earlier remote origin
block below is historical: current probes now accept the public origin.

## Public-service build milestone — 2026-10-08

User reports trophy-sync.party is hosted through Cloudflare on another host.
Default worker/title builds now target `https://trophy-sync.party:443` with
canonical origin `https://trophy-sync.party`, runtime IPv4 DNS, bounded resolver
waiting and two-address TCP fallback. Pinned official ISRG Root X1/X2 trust
validates chain/hostname/dates through Mbed TLS TLS 1.2; no insecure fallback.
Public pairing/queue uses `/data/trophy-sync-party`, preserving LAN state.
Every installation/profile obtains its own credentials; none are embedded.
Both ELF and foreground title must be installed, with no standalone autoload.

Local `.local/app.env` and running API/web now use the public origin and secure
cookies, as requested. Production env example also uses this domain. Existing
database volume/settings and separate LAN services were preserved. The remote
host was not modified. Plain localhost login writes no longer match this local
stack's configured origin. Optional `-Endpoint lan` retains previous LAN builds.

Commands/results:

- `Build-Console.ps1 -HostTest` preparation/worker compilation succeeded; first
  regression attempt exposed missing config includes in mocked storage tests.
  Fixed build/test endpoint selection, then final `container-build.sh` and full
  `container-test-console.sh` exited 0. Native readers/activity, storage including
  public path, pairing, queue/idempotency, IPC, SQLite and TLS fixtures passed.
  Added localhost DNS/TLS and ASan/UBSan stalled-resolver deadline tests.
- `Build-ConsoleUI.ps1` exited 0 after restoring checksum-pinned OFL license LF
  bytes (Windows checkout had changed its line endings). Git attributes now
  preserve those bytes. Eight renderer states, QR checks and native integrity
  inspection passed. Recompiled current worker and re-packaged after final tests.
- `Start-Local.ps1 -Build` exited 0; API environment inspection confirms
  `WEB_ORIGIN=https://trophy-sync.party`, `COOKIE_SECURE=true`.
- `Test-Local.ps1`: 53 passed, one existing Starlette/httpx deprecation warning.
- `test_public_transport.py`: host Mbed TLS JSON/binary DNS/TLS checks passed;
  no-token status/artwork returned 401, wrong-host certificates rejected.
  No server accounts/installations/imports or console actions were created.
- `Test-PublicService.ps1`: health 200, then **fails remote registration origin
  check with 403**. Direct invalid registration response: `Same-origin request
  required`. Same invalid body/public Origin on updated local stack returns 422
  missing fields, as expected. Remote config is a real remaining blocker.

Current public build worker SHA256:
`95b10cd844be0c6ca50804018f75574221c4f138a64f3b3fae9b84916f670889`.
Current public foreground SHA256:
`9066b444bebe1b1440414e3f02bdb86ab5025b43d831b7f68603e70c04b4cdda`.
Outputs: `artifacts/console/final-ui/TrophySync.elf`, `PPSA99889/`,
`TrophySync-PS5.zip` (both components, INSTALL.txt, licenses and manifest).
Manifest records endpoint/trust/source hashes and `console_verified=false`.
No new binaries were transferred or run; installed hashes below are historical.

Next action: apply this origin/secure-cookie configuration on the separate host,
rerun `Test-PublicService.ps1`, then obtain authorization for the public build's
read-only console pairing/native trophy/playtime/artwork sync test. Test console
DNS under its actual nanoDNS setup and certificate clock validation. No claim of
public-console sync, other firmware support or universal compatibility is made.
See [public service instructions](PUBLIC_SERVICE.md). Earlier cleanup evidence
below remains historical; its default LAN transport statements are superseded.

Updated 2026-10-08 after source/build/documentation cleanup. This file separates
console observations, local verification and pending gates. Historical prototype
sources and per-version instructions are retired; the supported source tree is
the current TrophySync application.

## Product

- Native PS5 trophy definitions/state, native recorded foreground playtime,
  automatic package artwork and official translations are implemented.
- Web libraries, compact/cards, grades/progress, descending session details,
  total recorded playtime, public opt-in profiles, friends and comparisons work.
- Browser-language support: English, French, German, Portuguese, Brazilian
  Portuguese, Spanish and Italian. Viewer-relative secret privacy applies to
  names, descriptions and icons.
- Revoked profiles and games with no imported trophies are excluded from libraries.
  Development samples and `/test` are disabled during normal operation.
- Local Docker services and separately configured production Compose are prepared.
  No external hosting, tunnel, publication, Git commit or push occurred in cleanup.

## Recorded console evidence

Baseline: FW 8.00 with the user's kstuff setup; actual kstuff runtime build and
nanoDNS identity remain unknown. Payload Manager 0.5.2, ShadowMount 1.7beta3 and
FTPSRV 0.21.1/2121 were observed. No etaHEN/onionHEN dependency.

Read-only native UCP/T2PD/T2TD decoding was matched independently against six earned
bronze trophies and one console-displayed unlock minute. A separate worker paired,
imported real records and reused its saved connection after Close App/reopen.
Repeat sync retained counts. The selected installation's latest checkpoint had
363 trophies across eight games, 89 activity records and 371 artwork PNGs; these
are a test-console observation, not fixed product limits.

A short user-observed game session produced 108 foreground seconds. The interrupted
rest/jailbreak-recovery test recorded 12 seconds before sleep and 120 afterward,
excluding sleep. Uninterrupted resume is not verified. Read-only locked SQLite
transactions use delete journal mode; native trophy snapshots are stable repeated
reads, not proven atomic multi-page generations.

The console transport reached LAN HTTPS with CA/IP validation and rejected
wrong-host/untrusted certificates. Real pairing, direct worker imports, artwork
uploads and replay were observed. The foreground sandbox cannot read native source
paths; bounded console-local IPC connects it to the separate worker.

## Installed title versus current source build

One foreground title remains: **TrophySync / PPSA99889**, contentVersion 01.001.000.
One project worker remains in Payload Manager: **TrophySync.elf**. Obsolete project
titles and worker/diagnostic aliases were removed in the prior authorized console
cleanup; unrelated user payloads, autoload/loader/DNS and pairing/queue storage
were preserved. No console was contacted during repository cleanup.

Installed foreground SHA256:
`5249d2163c5246b7c1509bb21e373b586a56ca0445c9db978f43c5bd60dd2644`.
Installed worker SHA256:
`5d8843c3d89e2bdd9d667ba9b523253b0d92f0da578988f4ed22dfdf4cbcd9d2`.
Registration/new icon and installed bytes were checked. **The redesigned foreground
screen, sync and Close App still need direct console observation.** Earlier
foreground rendering/pairing evidence does not validate this redesigned binary.

Cleanup renamed current modules, removed the unused prototype renderer and
retired historical packaging dependencies. Locally rebuilt worker SHA256:
`300774522efb59ea567bdcc69fef491f307576c459672ad7543938a91ad3afda`.
Locally rebuilt foreground SHA256:
`d63c25ab16caebb937e172c57a8f201942da21e40eef6ef9f10efeed3f6f1e29`.
These rebuilt files were **not** transferred or executed. The new manifest marks
console validation false; do not confuse installed and rebuilt hashes.

## Build and test evidence

Current entrypoints:

```powershell
.\scripts\Build-Tools.ps1
.\scripts\Build-Console.ps1 -HostTest
.\scripts\Build-ConsoleUI.ps1
```

Endpoint/TLS prerequisites and exact output paths are in [README](../README.md).
SDK v0.43 and dependency archives are checksum-pinned. The current build cache
`.local/console-build` was created fresh: Mbed TLS/SQLite and native title tooling/
zlib/runtime were rebuilt from verified sources. No old artifact, old manifest
or diagnostic ELF is required. The SDK CRT is recreated locally and its final
worker no-write hook is inspected; no installed SDK patch was made.

2026-10-08 cleanup validation, all exit 0:

- `Build-Console.ps1 -HostTest`: worker compile/no-write hook; native format,
  activity, discovery, pairing, private storage, queue, import acknowledgement,
  profile-scoped IPC, SQLite locking and framebuffer regressions.
- `Build-ConsoleUI.ps1`: current worker plus native title; font/license integrity,
  eight ASan/UBSan renderer states, independent pairing QR/expiry checks, native
  conversion/integrity inspection and self-contained current-source package.
- `container-test-console.sh` with an empty capture volume: current synthetic
  regression suite including JSON/binary TLS checks passes without personal
  captures; optional private-reference assertions skip when absent.
- Git audit: 244 visible source/documentation files; no private/generated paths
  or embedded private keys. Markdown links, Python/PowerShell syntax, shell LF
  and the current package file allowlist pass.
- Rebuilt current worker/title after transport header cleanup. Corresponding
  source/file hashes are sealed in `artifacts/console/final-ui/manifest.json`.

Prior web/API checks: 53 API tests and 18 browser tests passed for auth, ownership,
pairing, idempotency, social/public privacy, revocation, layout and translations.
The navigation follow-up passed 15 focused browser checks. Production web build
and isolated production Compose checks passed, including migrations through 007,
cookie/origin protection, disabled demo imports and artwork request limits.
Web/API behavior was not changed or re-tested during source cleanup.

## Repository cleanup and publication boundary

Historical diagnostic/experimental console sources, launch/deploy scripts,
per-version build instructions and one-off local helper scripts were removed
through the editing tool. Current modules have stable names; full dependency
license notices, meaningful synthetic tests, contracts and locks remain.
README and current docs were rewritten around actual behavior/build prerequisites.
Git-visible files contain no local config, credentials, captures, databases,
TLS keys or generated console packages; `.gitignore` also excludes dumps/keys/logs.

Automated shell deletion of old build/result/cache directories was rejected by
execution policy, with no detailed reason. Consequently old ignored binary/result
folders remain on disk. `scripts/Clean-GeneratedFiles.ps1 -WhatIf` reviewed 107
historical targets without deleting anything; its manual run can remove those
paths while preserving current files/data. It skips the old dependency cache
containing Linux reparse points rather than following links. That cache is ignored
and unused. See [Git preparation](GITHUB.md). Cleanup did not configure a remote,
create a commit, modify live data or reinstall the PS5 application.

## Remaining gates and next action

Next hardware opportunity: observe normal launch/sync/Close App/reopen of the
redesigned title. Independently validate second-profile isolation, full offline
recovery/live revocation and uninterrupted rest/wake. Passive sync is not enabled:
current worker requires UI IPC and has a bounded one-shot lifetime.
PS4 remains a separate unimplemented adapter. Public-domain transport requires
hostname resolution/trust configuration and its own console HTTPS result.
Account recovery/email verification and host restore/operational checks remain
before broad public registration. See [ROADMAP](ROADMAP.md) and
[self-hosting](SELF_HOSTING.md).

# Native recorded playtime

The worker reads `/system_data/priv/system_logger2/nobackup/database/sl2_log.db`
through the deny-write SQLite VFS, with native locks, query-only transactions,
delete journal mode, an eight-second query budget and a 4096-row bound.
Unsupported WAL, hot journals, symlinks and locked/inconsistent reads are rejected.
No raw live database is copied or modified; locks are released before networking.

`ApplicationSessionEnd` supplies integer scalar `fgTime` in seconds. The reader
accepts 0..604800 and an exact singleton `localUserIds` header matching the selected
profile. `ApplicationSessionEndBi` repeats analytics counters and is excluded.
Complete session duration comes from the native foreground counter, never from
wall-clock subtraction. Start-only, crash and invalid-counter sessions remain
incomplete with unknown duration.

Session identities hash the source title/session identity and are scoped by the
server installation/profile. Repeated observations take the maximum valid counter;
they never sum snapshots or reduce a complete session to an incomplete one.
Schema 3 retains counter provenance and optional, uncertain source timestamps.
The web shows recorded totals and chronological details; these are not PSN cloud
lifetime totals. The presentation omits an uncertainty suffix without altering
stored source-clock evidence.

Dates are bounded by server receipt independently of the foreground counter.
Each new import records per-field receipt times; repeated unchanged timestamps
keep their earlier bounds. Legacy rows use the profile's last-sync boundary;
before the next checkpoint advances, that boundary is saved on its older records.
Candidate dates after the boundary (allowing the receipt's one-second precision)
or malformed/unspecified-zone dates are withheld on reads, including shared
last-played aggregation. Raw observations remain stored. A valid counter remains
countable even when a date cannot be verified. This prevents impossible displayed
future sessions; it does not guess a historical timezone or clock correction.
Incomplete sessions distinguish absent ends, crashes and missing counters.
Shared games with undated incomplete sessions remain visible with unknown totals.

The single authorized 2026-10-23 clock/counter diagnostic completed with native
read locks and delete journaling. At launch the console UTC clock was about
20 seconds behind the PC; the user reports manually setting its displayed Paris
time. All 847 selected logger rows examined have explicit timezone markers.
Demon Slayer's stored end candidate remains 2026-10-20T19:26:05.740 after source
offset normalization. A blanket Paris/DST subtraction is therefore unsupported.
Its valid foreground counters remain usable independently of candidate dates.
Native Uncharted PPSA05684 and Fobia PPSA05626 each have only a start event and no
end or EndBi in that observed source; their missing duration cannot be recovered
from a wall-clock gap. Collection CUSA02344 has two scalar End counters, while its
EndBi rows have non-scalar fgTime. No duplicate analytics total is imported.

Metadata uses bounded read-only `param.json` with exact title identity validation.
Activity title IDs remain stored unchanged. For PPSA activity, reviewed native
publisher application bindings take precedence. Otherwise, the library matches
unique publisher/localized titles within that profile after conservative case,
punctuation and whitespace normalization. All words/numbers and meaningful
symbols remain significant; independent ambiguous trophy stacks stay separate.
PS4
activity joins through an exact, unique CUSA binding embedded in validated
PS4 state. Verified publisher collection membership can additionally group the
launcher and existing component rows in the same console profile (currently
CUSA02344 only). Separate collection fields preserve canonical trophy-set IDs,
image access and comparisons. There is no name matching or copied duration for
each component. Other ambiguous/missing matches stay separate. Games without imported trophies appear as activity-only
entries with no trophy progress bar. Missing metadata keeps the exact observed
application ID as its label; invalid existing metadata is still rejected.
Native PS5 logger sessions accept `PPSA` and `CUSA` identifiers. A `CUSA` entry
is displayed as PS4 while retaining `ps5_native` provenance for its logger data;
logger provenance remains independent of the separate PS4 trophy reader. Recomp IDs observed over
FTP are `PPSA74207` (The Simpsons Game) and `PPSA99902` (Sonic Unleashed Recompiled).
The authorized 2026-10-14 diagnostic observed 192 foreground seconds for Simpsons
and 406 across two completed Sonic sessions. PS4 names optionally use the
console-observed app.db tbl_contentinfo through a separate bounded read-only
transaction; unavailable/ambiguous names retain the application ID. That new
name query has compile/host tests. The user's hosted sync/screenshot now confirms
Attack on Titan and Nathan Drake Collection names; unavailable older metadata
still leaves some entries labeled with their CUSA IDs. Application icons are
independent of trophy imports; the new icon upload path awaits console validation.

Collection hours describe the available native foreground records, not an
estimated per-component split. An application that launches several games can
retain a start-only collection record until a matching valid end record is
observed. An incomplete record's dates never establish duration. Where the
console does emit a distinct component application session, its exact PS4
inner-state binding may include that existing session in the collection once.
Neither component membership nor switching games supplies a missing counter.
Most-played sorting uses exact eligible seconds, not rounded display hours;
most-sessions sorting uses eligible session counts (the shared aggregate's
session_count for shared libraries). Ties sort by displayed title.

The collection's expandable game subgroups have independent trophy/session views.
`collection_component_title_id` marks only an existing component trophy or a
session resolved through its distinct exact application binding. Launcher events
remain collection-level even if the general library join gave them a unique
trophy-set alias. Public totals keep those buckets separate before redacting
native observations. A component with no eligible counter shows that its
individual playtime is unavailable; no estimate is derived from the parent.

## Console evidence

A user-observed short game session produced 108 native foreground seconds,
matching approximately one to three minutes of play. The rest-mode test was
interrupted by the user's usual jailbreak recovery: native records reported
12 seconds before sleep and 120 seconds after waking, excluding the roughly
three-minute sleep interval. This corroborates sleep exclusion for that
interrupted/restarted path; uninterrupted rest/resume remains unverified.

Real playtime imports and repeat sync were observed. API counters do not grow
on replay. Native activity privacy/type/deduplication fixtures and unchanged-source
checks run under `scripts/Build-Console.ps1 -HostTest`. No resident stopwatch is
needed for completed native records. Background worker lifetime remains separate.

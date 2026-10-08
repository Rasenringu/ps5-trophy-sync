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

Metadata uses bounded read-only `param.json` with exact title identity validation.
Activity title IDs remain stored unchanged. The library joins activity to a trophy
set only through an exact, unique title within that profile; ambiguous/missing
matches stay separate. Games without imported trophies do not appear in the library.

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

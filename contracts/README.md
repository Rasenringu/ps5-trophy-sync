# Versioned contracts

OpenAPI and snapshot JSON Schema are generated from Pydantic v2 API models.
Schema version 1 separates ps5_native, ps4_bc and explicit mock data. These are
normalized upload contracts, not claims about native console storage.

Schema version2 is the native read observation contract: nullable unlock state,
explicit uncertain/unknown clock, both raw native time fields and raw flags,
stable_read_not_atomic consistency and foreground_user_path_scoped binding.
It accepts no activity records or PS4 source. V1 remains unchanged so previously
stored batch checksums remain valid. Unsupported states never become locked.
Server merges retain previously known unlocks/times and record the latest
observed state separately; absent rows do not delete records.

Missing unlock times and uncertain/incomplete activity evidence stay explicit.
Schema version 3 carries native activity observations separately from trophies.
Complete sessions require a native End foreground counter, matching application
and session identity, a single-profile header binding and a read-only SQLite
transaction. Repeated observations retain the largest counter; timestamps do
not determine native duration. An interrupted/restarted rest test corroborates sleep exclusion; uninterrupted
resume remains unverified. Profile-scoped UCP artwork check/upload endpoints
are included in OpenAPI; they do not change snapshot versions or unlock state.
Stable source event IDs and batch UUIDs are required; no cumulative snapshot
totals are summed. See docs/PAIRING_AND_IMPORTS.md.

Regenerate in the API image with PYTHONPATH=/app and
`python tools/export_contracts.py /path/to/contracts` on a writable bind mount.

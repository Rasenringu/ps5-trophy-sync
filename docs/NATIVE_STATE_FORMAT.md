# Native PS5 trophy format and reader

The native adapter was established from authorized console reads and independent
console-displayed trophy references. PS4 offsets/schema are not reused. Personal
captures/profile identifiers remain outside Git; synthetic fixtures exercise the
format and failure paths without requiring captures in a fresh clone.

Observed T2PD version 0x10000 uses a 64-byte header, big-endian page count and
1056-byte stride: 1024 logical bytes followed by their SHA256 digest. Logical
pages expose T2TD version 0x10000 and a directory of 32-byte entries identifying
tag, payload size/version, repeat count and logical offset. Records have a
16-byte tag/size/reserved header. Tags 0x500 and 0x800 contain indexed definition
and state records, with observed payload lengths 192 and 80.

The reference game had 45 matching consecutive IDs. Six state records used
flags 0x11 with nonzero big-endian timestamps; independent names/grades matched
six earned bronze trophies. The remaining 39 had zero flags/times. Microseconds
since year 1 matched one console-displayed unlock minute after timezone conversion.
The distinction between the two timestamp fields and source-clock accuracy is
not fully established. Unsupported flags/incomplete times stay UNKNOWN; raw
observations are retained rather than guessed.

`console/readers/native_state.c` validates bounds, versions, reserved fields,
SHA256, directory continuity, record headers and exact IDs. `native_join.c`
joins decoded state to verified UCP definitions by numeric trophy identity.
Definitions are never interpreted as evidence of an unlock. Package revision,
set identity, malformed UTF-8/JSON/types, duplicate entries and unsupported
states are checked before import.

The worker scopes observed paths to the active profile and rejects profile changes.
It uses same-descriptor metadata checks and equal repeated reads before visiting
a set. Page hashes and equal reads prove stable observations, not an atomic
multi-page generation. Imports carry `stable_read_not_atomic` provenance.

Build/test entrypoint: `scripts/Build-Console.ps1 -HostTest`. Current native imports
have console results; unsupported formats and PS4 remain separate future adapters.
See [STATUS](STATUS.md), [pairing/imports](PAIRING_AND_IMPORTS.md) and
[source/license pins](SOURCES.md).

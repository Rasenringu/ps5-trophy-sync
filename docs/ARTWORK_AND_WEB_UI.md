# Artwork, localization and library presentation

The console discovers native trophy packages for the selected profile, verifies
their UCP integrity and uploads missing packages directly over authenticated HTTPS.
The server cache checks title identity and package SHA256 before deciding whether
a new upload is necessary. New imported games obtain artwork and official text
on sync; cached packages are not repeatedly uploaded. No paid API or PSN login is
required. A missing asset uses a generic placeholder.

UCP parsing bounds package size to 128 MiB/count, checks SHA1, offsets, overlap and duplicate
or unsafe names. PNGs are bounded and validated for signature, dimensions, CRC,
format and terminal IEND; animated assets are rejected. Metadata joins by exact
set/revision/trophy identity and rejects duplicate JSON keys or invalid types.
Game artwork comes from the trophy-set image or, for activity-only applications,
the console's `/user/appmeta/<PPSA-or-CUSA-ID>/icon0.png`. The worker enumerates
exact IDs from the selected profile's collected sessions, reads each available
icon twice consistently with a 2 MB bound, checks its digest against the server
cache, then uploads missing images after activity/trophy imports. The API validates
PNG structure and requires owned, real native activity before accepting an image.
Missing icons keep the placeholder. This supports recomp and PS4 playtime entries
without implying that trophy data was imported. No database migration is needed;
update the hosted API before installing the worker that uses the new
`/device/application-artwork` endpoints. This path is locally tested; the user confirmed additional artwork after the
authorized worker sync (see STATUS).

Assets and translated metadata are stored in PostgreSQL. Library responses carry
asset identifiers; images use same-origin authorization. Ownership/visibility
checks precede ETag handling. Source unlock/state observations are not overwritten
by translation. No publisher artwork is included in this source repository.

The browser follows its supported language preferences: English, French, German,
Portuguese, Brazilian Portuguese, Spanish and Italian. Official package text
matches the publisher language tag, then a language variant, then package default.
Dates follow browser locale/timezone. Missing translations are never invented.
User labels, IDs and credentials are not translated.

Locked/unknown trophy artwork is concealed. Secret names/descriptions stay hidden
until the viewer earns the trophy, including friend/public comparisons where
another player already earned it. API responses and image authorization enforce
this independently of UI concealment. Earned trophies use a badge/green panel;
grades distinguish bronze, silver, gold and platinum without unavailable PSN
rarity text or redundant unlock labels.

The library defaults to a compact list, with a persisted Cards switch. The whole
game row/card opens trophy details with keyboard, mouse or touch. Rows stretch to
available width, retain artwork on the left and adapt to library-container width.
Recorded session details sort newest first; totals count eligible complete native
sessions without double-counting replay. Revoked profiles are omitted. Activity-only
games remain visible without trophy progress or grade counters. Shared libraries
export eligible playtime totals, never private session details or native identifiers.
Search/sort do not change aggregate playtime.

See [social visibility](SOCIAL_AND_COMPARISONS.md), [playtime](PLAYTIME.md) and
[current verification](STATUS.md).

## PS4 publisher packages

The independent PS4 adapter uses bounded 32 MiB TRP v3 packages, validates SHA1,
entry bounds/names/overlap, decrypts publisher ESFM text and validates exact NPWR,
numeric trophy IDs, grades and localized definitions before accepting PNG assets.
Owned schema-v4 state with a matching package digest/grade is required. Cache and
upload routes are /device/ps4-artwork/check and /device/ps4-artwork/{NPWR}.
Secret artwork, ETags, private/shared ownership and revocation use the same access
rules as PS5 assets. This adds no migration. Decryption uses a public publisher
format constant, never console/profile sealed keys. Actual captured state and
packages validate; the authorized worker imported all three observed sets and
completed their package cache/upload acknowledgements. User confirmed hosted
trophies are visible; see STATUS for the exact verified build.

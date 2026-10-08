# Artwork, localization and library presentation

The console discovers native trophy packages for the selected profile, verifies
their UCP integrity and uploads missing packages directly over authenticated HTTPS.
The server cache checks title identity and package SHA256 before deciding whether
a new upload is necessary. New imported games obtain artwork and official text
on sync; cached packages are not repeatedly uploaded. No paid API or PSN login is
required. A missing asset uses a generic placeholder.

UCP parsing bounds package size/count, checks SHA1, offsets, overlap and duplicate
or unsafe names. PNGs are bounded and validated for signature, dimensions, CRC,
format and terminal IEND; animated assets are rejected. Metadata joins by exact
set/revision/trophy identity and rejects duplicate JSON keys or invalid types.
Game artwork is the trophy-set image supplied by the publisher package.

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
sessions without double-counting replay. Revoked profiles and games without
imported trophies are omitted. Search/sort do not change aggregate playtime.

See [social visibility](SOCIAL_AND_COMPARISONS.md), [playtime](PLAYTIME.md) and
[current verification](STATUS.md).

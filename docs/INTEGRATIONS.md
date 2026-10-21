# Game information integrations

Open **Integrations** in the web navigation for availability and a private CSV
export. Open a game's details for its completion estimates and trophy earn
percentages. Collection launchers keep their separate recorded time: open an
individual collection component to add estimates or match a trophy listing.

## HowLongToBeat completion estimates

The user confirmed permission to access HLTB data on 2026-10-21. Automatic lookup
is enabled for this installation. The [Playnite integration](https://github.com/Lacro59/playnite-howlongtobeat-plugin)
provided a current protocol reference; the older suggested Node wrapper still
uses a legacy search endpoint. An independent Python adapter uses the existing
HTTP runtime, without bundling either project or adding a dependency.

Open an owned game to load **Main Story**, **Main + Extras** and **Completionist
(100%)** automatically. Only a unique exact normalized title with the correct
PlayStation platform is accepted automatically. Sequels/editions/ambiguous titles
require **Match a HowLongToBeat game** and an explicit edition choice. Publisher
English metadata is used where available. Punctuation separators are normalized
before sending title words upstream; NPWR/PPSA/CUSA identifiers are library keys,
never provider search terms. This fixes Demon Slayer's attached hyphens. Search
responses include `title` and `query` for diagnostics. Identifier-only metadata
remains unavailable until a human title exists. Cache v2 invalidates old empty
results. The selected HLTB game page is linked.
Numbers are community estimates across platforms, not PS5-only measured counters.
Seconds and sub-hour estimates are preserved; zero/missing categories stay unknown.
Cards display two-digit hours/minutes, for example `07h37min`; remaining seconds
stay in storage and the semantic duration, without rounding up the displayed time.

Successful lookups are cached in PostgreSQL for seven days, shared across
accounts for the same public title/platform. Anonymous session-init tokens stay
in memory. Fixed HTTPS paths, certificate validation, bounded responses/timeouts,
row locks, a global 30-lookup/minute budget, failure backoff and Retry-After apply.
Rejected requests are not circumvented. Shared viewers read existing cached
estimates only. They never initiate provider requests. An outage retains earlier
estimates with an explicit stale label. `HLTB_ENABLED=false` disables remote
lookups on hosts that need it; each operator remains responsible for its access.

**Edit completion times** saves an account-specific manual override with an
optional direct `https://howlongtobeat.com/game/123` link. Blank values remain
unknown, including when all three are blank. **Use automatic estimates** removes
the manual override. Game privacy, hiding, platform separation and revocation
apply to both modes. Migration **010** preserves earlier manual notes.

## HowLongToBeat account sign-in and reviewed progress sync

Open **Integrations → Connect account** and download the Chrome/Edge desktop
connector ZIP from that page. Unzip it, open `chrome://extensions` or
`edge://extensions`, enable Developer mode, choose **Load unpacked**, and select
the folder containing `manifest.json`. Sign in normally on the linked HLTB site,
complete its CAPTCHA, and keep its tab open. No HLTB password or cookie enters
TrophySync. iPhone/Firefox/Safari extension installation is not supported by this
MV3 package; use desktop Chrome/Edge for publication.

In the connector popup, enter the exact TrophySync HTTPS origin and the displayed
ten-minute connection code, grant access to that origin, and **Connect**. Pairing
is single-use. The server stores a hash of a random revocable scoped connector
token, expiring after 30 days. The token is kept only in trusted extension local
storage; protect the OS/browser profile. It accesses this account's publication
queue/receipts and cannot access general browser account routes or console data.
HTTP is allowed only on localhost/127.0.0.1 during development.

Open an owned game, verify its HLTB edition and recorded time, then **Publish
playtime → Queue update** after checking the review box. In the extension choose
**Sync queued updates** and keep the popup open until the result. At most ten
reviewed jobs are processed per click. Use **Refresh status** in Integrations for
the durable receipt. A queued state is not a successful provider submission.

The connector reads the signed-in HLTB identity and full game list, identifies
an unambiguous same-game/platform entry, preserves its complete edit data and
changes only the absolute `general.progress` total. New entries use Playing.
Completion categories, dates, reviews, notes and existing lists are preserved;
recorded progress never establishes completion. A larger existing time or
multiple matching entries is rejected for manual review. Repeated requests for
the same game/identity/platform/total share one durable job, never add time.

Each write is followed by list/edit read-back for the exact submission and total.
An uncertain write remains uncertain; the next run only checks the existing
entry. An interrupted job has a two-minute lease before read-only reconciliation.
It is never blindly reposted. Confirmed failures before a write can be explicitly
queued again. Provider schema changes, partial lists and mismatched identities
fail closed. There is no automatic console-triggered/background publication.

**Disconnect** revokes the connector and cancels outstanding jobs. Reconnecting
rotates its token and cancels old jobs; switching HLTB logins requires reconnecting.
Hidden/revoked/unowned games cannot execute pending jobs. A provider request
already in flight cannot be cancelled by revocation. Receipts describe what the
paired browser reports after read-back, not provider OAuth or independent
server verification of HLTB identity.

Implementation and synthetic transport/real MV3-runtime tests are local. **Actual
HLTB account sign-in, creation and update still require a live-account result.**
No provider account write was sent during implementation. The connector performs
these writes only after the user's review and explicit Sync action.

Use **Copy my recorded playtime** in an owned game's details to paste the available
hours/minutes into the provider's site yourself. **Export my playtime (CSV)**
exports visible, non-demo games with recorded hours and trophy counts, using UTF-8
with a BOM and spreadsheet formula protection. This is a reference file for manual
entry, **not a HowLongToBeat-compatible bulk importer**. Incomplete time is blank;
collection time is counted once and not allocated to components. Recorded hours
do not identify a completed main-story/100% run. Completionist estimates do not
establish the time required for a PlayStation platinum.

## Free trophy earn percentages: Exophase

No API key or PSN login is needed. In an owned game's details, choose **Find
trophy earn rates**, paste its public Exophase trophy listing URL, and **Use this
listing**. Example for the user's PS5 game:

`https://www.exophase.com/game/demon-slayer-kimetsu-no-yaiba-the-hinokami-chronicles-psn-2/trophies/`

The adapter accepts only `https://www.exophase.com/game/<slug>/trophies/`, verifies
the explicit platform and every returned trophy's unique publisher name/grade,
then exposes numerical rates. Provider IDs are opaque, never native trophy
ordinals. Secret metadata remains private, and console earned states/timestamps
are untouched. Missing values remain unknown; zero is valid. Percentages are
Exophase's tracked community, not all PSN players or TrophySync users.

Automated Exophase search is not used (its robots.txt disallows /search). Open
the provider site to choose an edition yourself. The suggested psn-profile-api
is a PSNProfiles HTML wrapper; its actual source site returned 403 here, so the
app uses the accessible free alternative without challenge bypass.

Listings use fixed-origin certificate-verified HTTPS, no redirects, a 2 MiB
decoded response limit, bounded timeouts, durable 24-hour cache, global
10-lookups/minute rate limiting and provider failure/429 backoff. Shared viewers
read existing owner-selected cached data only. Earlier data survives an outage
with a stale label. Account selections and private/hidden/revoked access apply.
Raw provider pages/catalogues are not distributed in the repository.

Update/rebuild API and web on the existing service host with its existing env
and database volumes; migrations **011–013** add listing selection and connector
pairing/jobs. No console build, new pairing or console resync is required.

## Existing optional provider: PlatPrices v2

The [provider's free noncommercial plan](https://platprices.com/developers.php)
currently includes 1,000 requests per month and two chosen store regions. A host
needs its own free key. No paid service or PSN account is needed. Commercial use
is outside this free configuration. The app displays linked provider credit.

On the service host, add these settings to its existing ignored Compose env file:

```dotenv
PLATPRICES_API_KEY=<your free key>
PLATPRICES_REGION=us
```

Enable that store region in the provider's developer dashboard. The key travels
only in a server-side `X-API-Key` header; never put it in a `NEXT_PUBLIC_*` setting,
browser field, checked-in file or URL. Missing configuration leaves rates
unavailable without affecting console imports or existing pages.

Rebuild API/web with the existing env file and database volume; all migrations
through **013** run automatically, preserving earlier notes/selections/imports.
On native Windows:

```powershell
.\scripts\Start-Local.ps1 -Build
```

For production, use the host's normal Compose workflow including `migrate`.
No console update, new pairing, resync or volume removal is needed.

In an owned game's details, select **Find trophy earn rates**, then deliberately
choose the correct edition. The API verifies the platform and matches **all**
returned base-game trophies to unique publisher names and grades before saving.
Publisher secret names may be used internally but never leave this adapter.
Provider trophy IDs are opaque: they are not assumed equal to native numeric
IDs, ordinals or NPWR identities. The selection is account-specific; a title-only
search never chooses a listing automatically. Identical regional rosters do not
prove an exact native stack: check the edition on the linked provider listing.
Ambiguous, incomplete or differently translated definitions can reject a match.

Rates describe PlayStation earn percentages reported by the **selected provider
listing**, not the share of TrophySync users. The returned list covers base-game
trophies; unsupported DLC and unknown rates stay unknown. Zero is a valid rate.
Rates never alter console unlock states, definitions, timestamps or playtime.

Requests go only to fixed certificate-verified HTTPS endpoints. Successful results
are persisted for 24 hours, failures back off, and 429 pauses honor Retry-After.
There is a conservative global 900-attempt monthly budget per key. Simultaneous
cold requests are serialized by PostgreSQL cache-row locks. Prior successful data
survives an outage with a visible cached/stale label. Shared visitors only read
the owner's existing cache and cannot initiate third-party refreshes. Hiding,
friend-only access and profile revocation are checked before cache access.

PlatPrices remains available for already selected listings and its existing API
selection endpoints; the current default web selection uses keyless Exophase.
The adapter is covered by synthetic response/ownership/cache/transport tests.
Authenticated live catalogue/trophy responses remain **unverified until the host
configures its key and checks an actual game**. The keyless `/demo` catalogue and
published v2 contract were inspected; they do not establish a live rate match.

## iPhone and mobile verification

The app now serves an opaque 180px Apple touch PNG, a conventional
`/apple-touch-icon.png` fallback, and 192/512px PNG manifest icons. Install metadata
is present on all pages. After deploying the web update, remove the old home-screen
shortcut and add the site again so iOS can fetch its new icon. Physical iPhone
Firefox installation still needs a device observation; browser emulation alone
does not establish that result.

Modal background scrolling is locked with scroll-position restoration, its close
control is an SVG, and safe-area/input/dialog sizing adapts to phone orientation.
Actual replacement `?` characters in six translation catalogs were repaired;
future translation edits must preserve UTF-8 rather than passing Unicode text
through a Windows legacy-encoded pipe.

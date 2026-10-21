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
English metadata is used where available. The selected HLTB game page is linked.
Numbers are community estimates across platforms, not PS5-only measured counters.
Seconds and sub-hour estimates are preserved; zero/missing categories stay unknown.

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

**Account linking/upload is not implemented yet.** Playnite does have a submit
endpoint, but authenticates it with browser-session cookies from its desktop
WebView. It supplies neither a web OAuth flow nor a credential this web app can
obtain from a user's unrelated HLTB browser session. No passwords, account cookie
imports or fake verified profile links are collected. A secure account
authorization/persistence flow and an authenticated end-to-end result are still
required before calling account sync implemented.

Use **Copy my recorded playtime** in an owned game's details to paste the available
hours/minutes into the provider's site yourself. **Export my playtime (CSV)**
exports visible, non-demo games with recorded hours and trophy counts, using UTF-8
with a BOM and spreadsheet formula protection. This is a reference file for manual
entry, **not a HowLongToBeat-compatible bulk importer**. Incomplete time is blank;
collection time is counted once and not allocated to components. Recorded hours
do not identify a completed main-story/100% run. Completionist estimates do not
establish the time required for a PlayStation platinum.

## PlayStation trophy earn percentages: PlatPrices v2

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

Rebuild API/web with the existing env file and database volume; migrations **009**
and **010** add account game information, provider cache and explicit lookup mode.
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

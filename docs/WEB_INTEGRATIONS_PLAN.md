# Game information and mobile polish (2026-10-21)

Scope: API/web only; preserve console readers, imports, privacy and deployment
boundaries. Existing work was clean at the start of this session.

1. Research provider access and exact response contracts before implementation;
   the user confirmed HLTB permission and supplied both reference projects.
2. Add automatic HLTB lookup with strict title/platform matches, reviewed edition
   selection, account-owned manual overrides and durable cache. Preserve unknown
   and sub-hour values. Provide direct game links and recorded-playtime copying.
3. Add optional PlatPrices v2 trophy earn rates using a host-owned free key.
   Explicit game selection, platform and complete returned roster validation
   prevent title-only or ordinal joins. Provider IDs are not assumed NPWR IDs.
   Cache results durably, bound requests, respect backoff/quota, retain unknowns,
   and enforce ownership/sharing before reading cached data. No PSN credentials.
4. Repair damaged translation values and glyphs; use a vector close control.
   Improve dialog scrolling and mobile safe areas. Generate PNG home-screen
   icons from the original brand and add install metadata.
5. Run API ownership/parser/provider-failure tests, TypeScript/production build,
   and Chromium/WebKit mobile regressions. Update contracts, README, SOURCES,
   STATUS and the remaining work with actual results.

User confirmed HLTB access permission and supplied the Node/Playnite references
on 2026-10-21. Automatic lookup now uses the verified current Playnite protocol
in an independent adapter. Playnite's submit API uses desktop WebView login
cookies, not a reusable web OAuth authorization flow. Do not collect passwords/
account cookies, imply a shortcut verifies ownership, or call manual transfer
account syncing. Account linking/upload remains pending a secure authorization
and persistence design plus an authenticated result.
PlatPrices advertises a noncommercial free key (1,000 requests/month, two store
regions), attribution and local caching. Its API key remains server-side.

No new runtime dependencies are planned. Provider responses are untrusted,
limited to fixed HTTPS origins and bounded sizes/timeouts, and cannot change
console unlock state, observed playtime or trophy definitions.

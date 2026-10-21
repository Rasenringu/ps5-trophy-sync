# Provider integration follow-up (2026-10-21)

User scope: repair HLTB title matching, provide a free trophy-rate source,
implement HLTB account sign-in/read/publish/update, and remove marked dialog
explanations. API/web and a browser connector only; no console/deployment work.

Evidence gathered before changes:

- Existing endpoint uses title_id for ownership lookup, then searches stored
  English metadata. Live adapter query with `Demon Slayer -Kimetsu no Yaiba- The
  Hinokami Chronicles` returns no games. Replacing punctuation with word
  separators returns HLTB 98594 and sequel 160453. Only 98594 has the exact
  normalized title; never auto-select its sequel.
- HLTB current login JavaScript posts user_name/password/hCaptcha token to
  /api/login. Login remains on the provider site; no CAPTCHA bypass or website
  password collection is planned. Playnite verifies /api/user and uses browser
  cookies for /api/submit. A browser connector can retain that session locally.
- psn-profile-api at 3f73263e9ce227acf68e44f3355fdf6a83ec1ad3 (WTFPL v2)
  is a PSNProfiles HTML wrapper. Actual PSNProfiles requests return 403 here.
- Exophase public Demon Slayer PS5 listing returns HTTP 200, 47 trophy rows,
  explicit platform/grade/name and numeric community earn rates. Its search is
  disallowed in robots.txt. Use a user-selected public listing URL; no automated
  search, paid key or inferred ordinal mapping. Verify every returned trophy
  against private publisher name/grade definitions before exposing rates.

Implementation sequence:

1. Sanitize public title search terms; reject identifier-only names; version the
   cache so a seven-day cached empty result cannot retain the old query bug.
2. Add keyless Exophase listing selection, bounded fixed-origin transport,
   durable cache/backoff, strict platform/roster validation and privacy tests.
   Retain existing optional PlatPrices configuration/selections.
3. Remove marked explanatory paragraphs and duplicate lookup-unavailable text.
   Keep compact source/date/stale labels and errors attached to user actions.
4. Add a browser-session connector if accepted: provider-site sign-in, revocable
   scoped pairing, reviewed absolute playtime publication, existing-entry
   preservation, reconciliation after uncertain outcomes and explicit receipts.
   Never equate elapsed playtime with completion categories.
5. Run API/TypeScript/production build/browser checks, export contracts, update
   operator docs and STATUS with exact evidence and remaining live-account gates.

User accepted the browser extension. Follow-up display request uses `00h00min`
in completion cards, retaining exact stored/semantic seconds. Review found that
cancellation/relinking must retain an attempted-write marker; migration 013
preserves that history so requeuing cannot turn uncertain writes into fresh
POSTs. Connection/job lock ordering is consistent across claim/revoke/dispatch.

No authenticated provider write has been made. A real account sign-in and write
cannot be called validated without its provider result.

Local implementation/validation is complete: 168 API tests, eight connector
protocol tests, 25 desktop/extension/privacy tests and 26 mobile checks pass.
Final focused reruns cover the compact duration layout and user-facing errors.
Live read-only adapters verify HLTB 98594 estimates and the 47-trophy PS5
Exophase listing. Next is the separate host rebuild and a real signed-in
connector run; exact commands/results and boundaries are in STATUS.md.

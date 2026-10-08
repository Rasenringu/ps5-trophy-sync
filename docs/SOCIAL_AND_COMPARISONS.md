# Profiles, friends and comparisons

Implemented locally on 2026-10-08 at the user's request after successful native
playtime work. This changes the web/API application; it does not require a new
console payload, change source databases or publish the service externally.

## Using the interface

- Library defaults to a compact list with game artwork on the left. The Cards
  toggle is saved in this browser's local storage. Whole game rows/cards open
  trophy details with keyboard, mouse or touch.
- Recorded session details show newest start first, falling back to end time
  when a start is unavailable. Undated sessions follow dated sessions.
- Total playtime sums eligible sessions across the selected profiles and
  trophy-bearing games. Search/sort do not change this total. Missing, incomplete
  and unverified duration records do not inflate it; repeated imports remain
  idempotent. This is recorded foreground time, not an estimate of lifetime play.
- Friends lets a signed-in player choose a display name and unique public handle,
  search for players and open their public profile at `/players/{handle}`.
- Request friendship from the public profile. The recipient can Accept or Deny;
  the sender can Cancel a pending request. Either friend can Remove the
  friendship. Declined requests appear in the sender's history; resending is
  limited for 24 hours after a denial. A reverse request never auto-accepts.
- Accepted friends can compare totals for every imported game, then open a game
  for side-by-side trophy states. Filters show all trophies, only your unlocks,
  only the friend's unlocks, or shared unlocks. PS5 and PS4 sets stay separate.
  An absent import says Not imported instead of asserting Locked. Unknown native
  state remains Unknown. Mock imports are excluded from comparisons.

## Public identity and privacy

Migrations 006/007 create social identities, friendships and sharing visibility. Existing accounts get
random `player_...` handles and generic display names; registration creates the
same kind of identity. Names do not derive from email or console profile labels.
Anyone reaching this running service can view/search public display names and
handles. A handle change moves the public link; old links do not redirect.
Public sharing defaults to friends only. The owner can opt into Public in
Friends. Owner player pages
reuse My library, including private session details. Authorized visitors see
covers, trophy progress and aggregate recorded playtime, without email, console
identifiers, credentials or individual activity logs. Revoked profiles and mock
imports are excluded. Private libraries require ownership or accepted friendship.
Comparisons always require accepted friendship, regardless of public visibility.

Comparison unlocks merge the viewer's owned profiles by platform/title/trophy:
any earned observation wins, otherwise unknown wins over locked. No source
records change. This compares imports rather than asserting completeness or
hardware authenticity. Current console hardware support remains PS5-only;
keeping PS4 data separate does not establish a PS4 reader.

A secret trophy's title, description and artwork remain concealed until the
viewer earns it, even if their friend has earned it. Unknown hidden metadata is
conservatively concealed. All unearned artwork stays hidden to match the library.
Image endpoints independently enforce library sharing and secret-unlock rules,
including guessed direct URLs. Public game covers and earned nonsecret trophy
images may be shared; secret images require the viewer to have earned them. Removing a friendship prevents subsequent
image/comparison requests. Previously viewed/downloaded images cannot be recalled.

Account writes retain same-origin protection and authenticated cookie sessions.
Requests/actions/profile edits and public search are rate limited. Canonical
account pairs and locks prevent duplicate or implicit mutual requests. Libraries
and images are not exposed through public search. No messaging or external deployment was added. Other players need access to the same
local/LAN service until a separate hosted deployment is authorized.

## Verification

API ownership/friendship/public redaction/image authorization tests and browser
layout/navigation/locale tests have passed. Public summaries omit private console
identifiers and individual session logs. See [STATUS](STATUS.md) for verification
counts and limitations; hardware sync is independent of these web tests.

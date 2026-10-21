# TrophySync HowLongToBeat browser connector

Chrome/Edge desktop, Manifest v3. Version 0.1.0. No dependencies or paid API.

1. Unzip this folder. In chrome://extensions or edge://extensions enable
   Developer mode, choose Load unpacked, and select the folder with manifest.json.
2. Sign in normally at https://howlongtobeat.com/login and keep that tab open.
   Complete its CAPTCHA on that site. TrophySync never receives the password,
   CAPTCHA response or provider cookies.
3. In TrophySync Integrations choose Connect account. Open the extension popup,
   enter the exact HTTPS TrophySync origin and its ten-minute connection code,
   approve access to that origin, and Connect. The code is single-use.
4. Open an owned game, verify its matched HLTB edition and recorded playtime,
   choose Publish playtime, review and Queue update. In the extension choose
   Sync queued updates; keep its popup open until the result. Refresh status
   in TrophySync Integrations to see the receipt.

Only explicitly queued updates are processed, at most ten per click. Progress is
an absolute total, never an addition to the previous total. Existing notes,
reviews, completion estimates, completion dates and list memberships are kept.
New entries use Playing; a recorded total never establishes completion. A larger
existing provider total or multiple matching entries requires review on HLTB.
An uncertain write is checked by reads on the next run; it is never blindly
posted again. Interrupted jobs have a two-minute lease before reconciliation.

The stored revocable TrophySync connector token expires after 30 days. It only
accesses this account's publication queue/receipts; it is not a general account
session or a provider credential. Revoke it with Disconnect in Integrations.
Forget connection only clears the browser's token. Browser extension storage is
local profile storage; protect the OS/browser profile. Reconnecting rotates the
token and cancels outstanding jobs. Switching HLTB logins requires reconnecting.
Revocation cannot cancel a provider request already in flight.

Permissions: provider tab script execution and trusted extension storage;
optional access only to the TrophySync origin you explicitly choose. No cookies
permission, content-script auto-run, remote scripts, alarms or background sync.
HTTP is accepted only on localhost/127.0.0.1 for local development.

This connector uses the published Playnite integration as a protocol reference,
not its code. It performs client-side read-back verification, not provider OAuth
or independent server verification of the provider identity. Live account
creation/update needs validation against your real account; synthetic tests
alone do not establish it. Website changes fail closed.

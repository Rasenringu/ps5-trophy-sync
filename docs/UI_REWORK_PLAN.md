# Library and profile redesign — 2026-10-14

Implement account-level hidden games keyed by reader source and canonical title
ID; retain imports and expose an owner-only Hidden Games section. Filter shared
libraries, comparisons, artwork and favorite showcases on the server. Replays
must not reset preferences. PS4/PS5 identities remain separate.

Default library sorting uses latest recorded activity timestamp (including
incomplete sessions); unknown dates sort last, title breaks ties. Shared libraries
expose only latest played time and aggregate durations, never raw sessions.

Add bounded plain-text bio, preset theme/avatar and an owned non-mock favorite
game. Respect library visibility for showcases. Build a cohesive blue/white
console-inspired web design and original vector trophy/orbit branding. Extend
the existing native software renderer and primitive icon generator without new
SDK APIs or dependencies. Preserve QR readability and all status/error states.

Validate migration, privacy/ownership/replay regressions, desktop/mobile browser
flows, production build and native renderer/QR/SDK compile. Package locally;
user handles Git and hosted rebuild. Any console update must preserve private
pairing/queue state and must not launch a payload without explained authorization.

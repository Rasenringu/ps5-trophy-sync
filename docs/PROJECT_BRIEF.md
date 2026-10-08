# Product and architecture

TrophySync receives native trophies and recorded playtime directly from a
jailbroken PS5 into a self-hosted HTTPS service. This is an independent tracker;
it does not synchronize with PSN or unlock/change trophies.

The foreground PS5 title presents the selected local profile, temporary pairing
QR/code, expiry, connection, sync progress and errors. A separate read-only worker
reads native trophy/activity sources, keeps private credentials and a durable
queue, and uploads to the server. The PC hosts development services and tools;
it is not the required data relay. Passive resident mode is future work.

FastAPI/Pydantic v2/SQLAlchemy 2/Alembic and PostgreSQL enforce account ownership,
installation/profile isolation, revocable hashed device credentials and idempotent
imports. Next.js/TypeScript provides private libraries, game/trophy/playtime views,
friends and viewer-relative comparisons. Public library sharing is opt-in;
default sharing is friends only. Secret trophy metadata stays hidden until earned
by the viewer. Publisher package translations are used when available.

Initial pairing uses single-use, short-lived server authorization. A signed-in
user confirms the displayed console/profile/code. Later launches validate the
saved connection and sync automatically. Local profile identifiers are unique
only inside a console installation; server-generated identities define the scope.

Target evidence: PS5 firmware 8.00, user's kstuff setup, existing Payload Manager,
ShadowMount and FTPSRV. kstuff runtime identity/nanoDNS remain unknown when no
reliable detector exists. No etaHEN/onionHEN dependency. No source database, DNS,
loader, firmware or trophy modification is part of synchronization.

Native PS5 and PS4 readers require independent evidence. Preserve unknown states,
available unlock timestamps, incomplete sessions and uncertain source clocks.
Playtime uses complete native foreground counters, never elapsed sleep/wall time.
See STATUS, ROADMAP, native format documentation and source/license pins.

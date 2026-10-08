# PS5 interface

The current native UI renders at 1920×1080 using direct VideoOut and the verified
tiled framebuffer path. It follows the web theme: charcoal panels, lavender
accents, TV-readable typography, safe margins and a large pairing area.
The icon uses TrophySync branding. No test title or sample sync appears in normal use.

Screens cover connecting, server-issued pairing, expired authorization,
authenticated sync, completed upload, partial sources and action-specific errors.
Pairing shows a black/white QR with four-module quiet zone, short code, HTTPS URL,
selected profile, countdown and connection status. Permanent credentials never
enter the display model or QR. Expiry removes the code.

French is the current UI language; an English compile-time variant exists.
Console-language detection is not implemented. The pinned Noto Sans Display font
provides Latin accents/punctuation without running a font engine on the PS5.
Unsupported glyphs use replacement characters. Long values wrap or truncate.
An optional read-only UserService name lookup falls back to a profile label.

Counts reflect real reader/worker status, including incomplete sessions and
unknown trophies. No lifetime total or last-sync timestamp is invented. Partial
sources do not claim a fully current library. Errors retain the worker action/code.
Use PS → Close App; the app does not advertise unsupported controller actions.

Build instructions: [README](../README.md) and [console build](CONSOLE_UI.md).
Eight synthetic offline previews and independent QR checks are generated during
build and excluded from Git. See [STATUS](STATUS.md) for the installed-title
hashes and the still-unobserved redesigned foreground launch.

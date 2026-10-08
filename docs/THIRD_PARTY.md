# Third-party notices and distribution

Current source/build pins are in `toolchain.lock.json`, `docs/upstream.lock.json`,
`scripts/prepare-probe-deps.py`, `scripts/prepare-title-deps.py` and the font's
`source.json`. Python versions are locked in `api/requirements.lock`; Node/browser
versions and integrity are locked in `web/package-lock.json`. Package license
metadata is inventoried in `docs/dependency-licenses.json`.

## Console and build dependencies

| Component | Version/input | License and use |
| --- | --- | --- |
| ps5-payload-dev SDK | v0.43, source d9c9519116944a7f1c22d262012c53b80b3520b7 | GPL-3.0-or-later, with separately marked BSD/header exceptions |
| BlackBearReloaded native app boilerplate | 2f672d1c2f508e26f82ce6e27cef289a0861413c | GPL-3.0-or-later; native startup, source-generated runtime, converter; tooling credits SvenGDK/SharpProspero |
| Mbed TLS | 3.6.7 | Apache-2.0 option; worker HTTPS/digests; full upstream dual-license notice retained |
| SQLite | 3.53.4 amalgamation | Public domain; read-only source VFS and in-memory JSON/import operations |
| Nayuki C QR generator | 3c6d0b3cefb4e049dc337e82237c9644399716a8 | MIT; original source notices retained |
| Noto Sans Display | Google Fonts 8d7e485e53e169e95e6f50f11d0cf1be04795b82 | OFL-1.1; original font/license retained, host-baked coverage embedded |
| zlib | 1.3.2 | zlib license; host native converter only |
| Pillow / zxing-cpp | 12.1.1 / 3.1.1 | HPND/Pillow / Apache-2.0; host font/icon and independent QR checks only |

The current console does not link SDL or stb_easy_font. SDL's pinned PS5 header
was used only to research a UserService function signature. No proprietary console
runtime is copied. Tiled frame addressing is adapted from BlackBearReloaded's
`demo_renderer.cpp`; its copyright/GPL attribution remains in `tiled_frame.c`.

Console source is GPL-3.0-or-later, with the full text in `console/COPYING`.
The no-write CRT is a marked project-local alteration: the SDK's patch-init symbol
is weakened and replaced by the worker's no-write hook. SDK installation is untouched.
SQLite build flags and TLS build configuration are retained in current scripts.

Current packaging includes GPL, Mbed TLS, QR, font, SQLite, native runtime and zlib
notices/provenance. Before publishing binaries, provide corresponding source and
build inputs for the GPL components, including pinned SDK parts, dependency
sources/configuration and the CRT alteration. A checksum manifest alone is not
corresponding source. Retain individually marked BSD/other notices too.
No console binary has been published externally.

## Runtime/application dependencies

FastAPI, SQLAlchemy, Alembic, Pydantic, Next.js and React use MIT licenses;
Argon2-cffi is MIT. psycopg binary packages include LGPL-family and third-party
notices. TypeScript and Playwright use Apache-2.0. PostgreSQL has the PostgreSQL
License; nginx is BSD-2-Clause. Optional cloudflared is Apache-2.0.
Keep transitive/base-image package notices when redistributing images; license
metadata does not replace full installed notices.

Application/tunnel images are digest-pinned in Compose/Dockerfiles. The SDK builder
uses Ubuntu 24.04 and apt resolution, not a fully frozen OS/package snapshot.
Host packages/font engine/QR decoder are not linked into the console application.

## Research-only references

Payload Manager, ShadowMount, FTPSRV, loader and nanoDNS sources are API/protocol
references, not console-linked dependencies. Their exact research pins remain in
`upstream.lock.json`; a research pin does not identify the user's runtime build.
LibProsperoPKG was a GPLv3 format reference; no C# code/library is incorporated.
PS5-PHU-Trophy-System was inspected and excluded because it registers/unlocks or
modifies trophies. No unlocking code is used by this project.

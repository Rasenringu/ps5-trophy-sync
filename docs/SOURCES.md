# Source evidence and pinned inputs

Research established the current implementation rather than assuming support from
SDK filenames, registration/unlocking libraries or PS4 paths. The native format
and playtime semantics include independent console results described in STATUS,
NATIVE_STATE_FORMAT and PLAYTIME. Source documentation is not hardware validation.

## Console dependencies

- [SDK v0.43](https://github.com/ps5-payload-dev/sdk/releases/tag/v0.43): exact
  archive URL/SHA256 and source commit in `toolchain.lock.json`.
- [Mbed TLS 3.6.7](https://github.com/Mbed-TLS/mbedtls/releases/tag/mbedtls-3.6.7)
  and [SQLite amalgamation](https://www.sqlite.org/2026/sqlite-amalgamation-3530400.zip):
  source archive hashes in `scripts/prepare-probe-deps.py`.
- Native title tooling and zlib archive hashes in `scripts/prepare-title-deps.py`.
- [Noto Sans Display](https://github.com/google/fonts/tree/8d7e485e53e169e95e6f50f11d0cf1be04795b82/ofl/notosansdisplay):
  original font/OFL hashes in `console/vendor/noto-sans-display/source.json`.
- [LibProsperoPKG format reference](https://github.com/SvenGDK/LibProsperoPKG/tree/748eabf1b7d17819528cabf367d8e27109d8fce3):
  research only; no C# source/library incorporated.

## Repository/API research pins

- [PS5-PHU-Trophy-System](https://github.com/ArkSama/PS5-PHU-Trophy-System/tree/ae29e8a7b4b458233c4859c1a33903b814c5010f): `ae29e8a7b4b458233c4859c1a33903b814c5010f`; research reference; see SOURCES.md.
- [nanoDNS](https://github.com/drakmor/nanoDNS/tree/21edab7527688979af17d0c828e28065774f5b5c): `21edab7527688979af17d0c828e28065774f5b5c`; research reference; see SOURCES.md.
- [PS5-Activity-Log](https://github.com/hotshotz79/PS5-Activity-Log/tree/ef2714d23ea81a1e89bc7c8e3b955bfd8959fd39): `ef2714d23ea81a1e89bc7c8e3b955bfd8959fd39`; research reference; see SOURCES.md.
- [ps5-elfldr](https://github.com/itsPLK/ps5-elfldr/tree/bb1e117988217a0239679029601e93c7286394d7): `bb1e117988217a0239679029601e93c7286394d7`; research reference; see SOURCES.md.
- [ps5-payload-manager](https://github.com/itsPLK/ps5-payload-manager/tree/e4e72dc9d831dd09ee8fabc222ad1e7f5139050e): `e4e72dc9d831dd09ee8fabc222ad1e7f5139050e`; research reference; see SOURCES.md.
- [ps5-webkit-autoloader](https://github.com/itsPLK/ps5-webkit-autoloader/tree/4ad7135e1939cae6f14cbf52957db2e33385f154): `4ad7135e1939cae6f14cbf52957db2e33385f154`; research reference; see SOURCES.md.
- [elfldr](https://github.com/ps5-payload-dev/elfldr/tree/02cfe91eb3f9697787460ad77d73ff951f801f50): `02cfe91eb3f9697787460ad77d73ff951f801f50`; research reference; see SOURCES.md.
- [SDL](https://github.com/ps5-payload-dev/SDL/tree/ee4c47dc0d617b3bc8f35108f9956baf228a1322): `ee4c47dc0d617b3bc8f35108f9956baf228a1322`; research reference; see SOURCES.md.
- [websrv](https://github.com/ps5-payload-dev/websrv/tree/1afd476c5044d68df4e45dc773769e5de3b2cdd6): `1afd476c5044d68df4e45dc773769e5de3b2cdd6`; research reference; see SOURCES.md.
- [Nativehbl](https://github.com/Rufidj/Nativehbl/tree/e9488102399de9546d13dd496694c74142abe49f): `e9488102399de9546d13dd496694c74142abe49f`; research reference; see SOURCES.md.
- [sdk](https://github.com/ps5-payload-dev/sdk/tree/d9c9519116944a7f1c22d262012c53b80b3520b7): `d9c9519116944a7f1c22d262012c53b80b3520b7`; compiled SDK release source.
- [ps5-elfldr](https://github.com/itsPLK/ps5-elfldr/tree/bb1e117988217a0239679029601e93c7286394d7): `bb1e117988217a0239679029601e93c7286394d7`; autoloader v0.5.1 pinned loader reference.
- [QR-Code-generator](https://github.com/nayuki/QR-Code-generator/tree/3c6d0b3cefb4e049dc337e82237c9644399716a8): `3c6d0b3cefb4e049dc337e82237c9644399716a8`; vendored C QR generator; MIT.
- [ShadowMountPlus](https://github.com/drakmor/ShadowMountPlus/tree/f0d15ffc46e9237d41cc3555b1cf11362d9a32e0): `f0d15ffc46e9237d41cc3555b1cf11362d9a32e0`; 1.7beta3 source/API reference; observed installed version; GPL-3.0; not linked.
- [ps5-native-app-boilerplate](https://github.com/blackbearreloaded/ps5-native-app-boilerplate/tree/2f672d1c2f508e26f82ce6e27cef289a0861413c): `2f672d1c2f508e26f82ce6e27cef289a0861413c`; native converter, startup and source-generated runtime; GPL-3.0-or-later.
- [ftpsrv](https://github.com/ps5-payload-dev/ftpsrv/tree/70f7b8614d3f36f6ceda0a37d6189b675f9d3f29): `70f7b8614d3f36f6ceda0a37d6189b675f9d3f29`; FTP transfer research; detected banner v0.21.1; GPL-3.0-or-later; no linked code.
- [mbedtls](https://github.com/Mbed-TLS/mbedtls/tree/068ff080b369adfac81509f9b57b2afabaf82dc5): `068ff080b369adfac81509f9b57b2afabaf82dc5`; Console HTTPS and reader digests; Apache-2.0 option.
- [fonts](https://github.com/google/fonts/tree/8d7e485e53e169e95e6f50f11d0cf1be04795b82): `8d7e485e53e169e95e6f50f11d0cf1be04795b82`; Vendored Noto Sans Display, OFL-1.1; hashes in console/vendor/noto-sans-display/source.json.

FTPSRV's observed 0.21.1 banner and source protocol inspection support the current
loopback discovery path. Payload Manager's observed 0.5.2 API supports the current
worker launch; source autoload support does not establish resident survival.
ShadowMount 1.7beta3 registration/uninstall APIs were observed for the title update.
The actual kstuff build and nanoDNS project/version remain unknown.

## Web and hosting

Resolved versions/integrity: `api/requirements.lock`, `web/package-lock.json`.
Application/ingress/tunnel images: digest pins in deployment Compose/Dockerfiles.
[cloudflared 2026.10.0](https://github.com/cloudflare/cloudflared/releases/tag/2026.10.0)
and [token-file run parameters](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/)
were inspected for the optional tunnel. No Cloudflare connection/public route
has been created. [nginx HTTPS module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
informs the local TLS gateway.

See [license obligations](THIRD_PARTY.md). Updating a dependency requires reviewing
its API/license, changing the pin/hash, compiling and running relevant regressions.

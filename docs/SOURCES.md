# Source evidence and pinned inputs

## Title matching, keyless rates and browser account connector (2026-10-21)

- Live shipped HLTB adapter: raw publisher title `Demon Slayer -Kimetsu no
  Yaiba- The Hinokami Chronicles` returns zero results. Separator-normalized
  title words return 98594 and sequel 160453. Exact normalized title/platform
  comparison accepts 98594 only. NPWR/PPSA/CUSA identifiers remain internal
  ownership keys and are rejected as upstream title queries. Cache v2 prevents
  the old seven-day empty result from retaining this bug.
- [psn-profile-api](https://github.com/leonardoalemax/psn-profile-api/tree/3f73263e9ce227acf68e44f3355fdf6a83ec1ad3),
  commit `3f73263e9ce227acf68e44f3355fdf6a83ec1ad3`: README, PsnProfileParser.ts,
  PsnProfileService.ts and WTFPL v2 LICENSE inspected. This is a PSNProfiles
  HTML wrapper, not an official PSN service. Research only; no code/dependency
  incorporated. Actual PSNProfiles request returned HTTP 403; no challenge bypass.
- [Exophase public PS5 listing](https://www.exophase.com/game/demon-slayer-kimetsu-no-yaiba-the-hinokami-chronicles-psn-2/trophies/):
  HTTP 200; 47 award rows with data-average percentages, explicit
  platform-ps5, award-title and exo-icon-trophy-* grades. Anonymous page SHA256
  `fb16c5c1805224c61ed5fb557f2cfe89853dfee750115ddfd6a532413fcb66ad`.
  [robots.txt](https://www.exophase.com/robots.txt), SHA256
  `79ebfbfeaff5ecfce4f8e157b686188597e7bf413d4b03dbf3393bbfc034dce5`,
  disallows /search. Adapter never searches/crawls catalogues: users choose a
  public listing URL. It validates the full returned roster against private
  publisher names/grades, retains only bounded fields internally and exposes
  numeric rates with linked credit. Percentages describe Exophase's tracked
  community, not global PSN rarity or this app's users. Site content is not
  relicensed/distributed with source. Existing httpx/standard HTMLParser only.
- [HLTB login](https://howlongtobeat.com/login) and its served
  [login chunk](https://howlongtobeat.com/_next/static/chunks/3ansjkr7hyqx-.js):
  anonymous HTML SHA256
  `d7356b1e8d6d6b28850e7e297e7420b5477610911d38f6de8387cd1d0053999f`;
  chunk SHA256 `d2fb7b34ac012879703b8f6c0638276bc8ae1921abcb1bdb96cb70cb4b7426ce`.
  The provider posts user_name/password/hCaptcha token to /api/login. The
  connector leaves this entire login on the provider site and neither solves
  CAPTCHA nor obtains passwords/cookies. Public assets/manifests can differ
  across cached builds; no mutable chunk URL is treated as an SDK dependency.
- The already pinned MIT
  [Playnite reference](https://github.com/Lacro59/playnite-howlongtobeat-plugin/tree/809c1890b0ce27942fd92c9b50ae7e38a8c89e30)
  additionally supplies research evidence for /api/user, user games/list,
  /submit/edit/{id} __NEXT_DATA__.props.pageProps.editData, /api/submit and
  Models/Api/EditData.cs + UserGamesList*.cs. Independent JavaScript preserves
  existing edit data, changes only general.progress, and verifies by a second
  list/edit read. New-entry defaults follow the inspected model. No library/
  C# source incorporated. Authenticated current schema and real create/update
  still require a user-owned live-account result; fixtures do not prove them.
- Chrome official [network requests](https://developer.chrome.com/docs/extensions/develop/concepts/network-requests),
  [scripting](https://developer.chrome.com/docs/extensions/reference/api/scripting),
  [permissions](https://developer.chrome.com/docs/extensions/reference/api/permissions)
  and [storage](https://developer.chrome.com/docs/extensions/reference/api/storage)
  documentation checked for MV3 isolated script execution, same-origin provider
  requests, explicit optional origin grants and trusted-context-only storage.
  No new runtime dependency. Connector uses the existing pinned browser test
  runtime and the existing Node 24 image; package has no npm dependencies.

Browser connector receipts are client-reported read-back evidence, not OAuth or
independent server authentication of an HLTB identity. No credential/cookie is
sent to TrophySync. There is no auto-run or background provider publication.
User authorization is enforced by the app's owned review and scoped connector.

## Game information providers and install metadata (2026-10-21)

- [PlatPrices v2 contract](https://platprices.com/api/v2/docs) and
  [plans](https://platprices.com/developers.php): fixed HTTPS v2 search, catalogue
  and base-game trophy endpoints; server header authentication, provider credit,
  local cache permission and noncommercial free tier verified. Contract page
  SHA256 `45186ca57fd3e604a423945e495905297f612465cd059ca298cd7fe6593b2572`.
  Keyless `/api/v2/demo` SHA256
  `9c8ccfc028a4ae4697581eeaa3d3579a9774341bf2d2138b95d51b2d8d67fea3`
  confirms catalogue fields including GameName, ProductName, PPID and IsPS5.
  No authenticated live trophy response was available. Provider `list_id` is
  opaque; no native NPWR equality or ordinal trophy mapping is inferred.
- [HowLongToBeat policy](https://howlongtobeat.com/robots.txt), SHA256
  `8d70e159f320e3b4967f9542a7c0aa1d402c69b3dd79128e6d2c929f7339d7bd`:
  automated extraction needs permission. The user explicitly confirmed its data
  access authorization on 2026-10-21 and supplied both integrations below.
  Community ckatzorke/howlongtobeat was inspected at
  `d57da96a95f16ee89959cad8fa30907a0504040f` (WTFPL v2; exact LICENSE inspected), research only: no library/code
  incorporated. Its legacy `/api/search` wrapper is not used by the app.
- [Playnite HowLongToBeat integration](https://github.com/Lacro59/playnite-howlongtobeat-plugin/tree/809c1890b0ce27942fd92c9b50ae7e38a8c89e30)
  at `809c1890b0ce27942fd92c9b50ae7e38a8c89e30`: exact MIT LICENSE and
  `source/Services/HowLongToBeatApi.cs`, search models and submission model
  inspected. Research only; no C# code/library incorporated. Its current
  anonymous `/api/search/site/init` + `/api/search/site` protocol and game-page
  `__NEXT_DATA__` shape inform an independent Python adapter. No script execution,
  user-agent randomization, challenge bypass, passwords or account-cookie imports.
  Real read-only search/detail calls for HLTB 10270 both returned
  `comp_main=186011`, `comp_plus=373540`, `comp_100=630912` seconds through the
  shipped adapter on 2026-10-21. Zero/missing fields become unknown; no sub-hour
  rounding to a fabricated hour. This verifies provider retrieval, not a user's
  console-library match or authenticated account upload. Playnite `/api/submit`
  uses an embedded desktop browser's session cookies. Secure web account linking
  and actual account-upload validation remain pending; no write was sent.
- [Next icon file conventions](https://nextjs.org/docs/app/api-reference/file-conventions/metadata/app-icons)
  and [Apple web-app configuration](https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html)
  support generated PNG touch icons and install metadata. APIs/types and emitted
  metadata also checked against the existing pinned Next.js 16.4.0 installation.
  Next emits standard mobile-web-app-capable; the legacy Apple capability tag is
  also supplied explicitly. Original brand geometry is rendered with bundled
  ImageResponse; no new image/font dependency or third-party artwork.

No SDK, console, image or runtime dependency versions changed. The independent
provider adapter uses existing pinned httpx 0.28.1 (BSD-3-Clause), Pydantic and
SQLAlchemy. Provider content is not licensed under this repository's source
license; full catalogues/responses are not distributed. See INTEGRATIONS.md.

## PS5 regional-release bindings (2026-10-19)

Native PS5 source paths and metadata were independently observed over read-only
FTP for PPSA03457 and PPSA03490. `param.json` verifies their exact title/content
IDs (HP0177 and EP0177 respectively); each `trophy2/npbind.dat` explicitly binds
NPWR23868_00. Both 532-byte files have the observed single-set version-1 header,
384-byte typed record and valid trailing SHA1. Both files and params match
complete second reads. This PS5 evidence was not inferred from PS4 source paths
or earned-state schemas. The existing pinned npbind format reference below is
research only; no template/source/dependency was incorporated.

`scripts/inspect-native-title-bindings.py PPSA03457 PPSA03490` reproduces bounded
read-only identity/layout/digest verification and emits only IDs/hash evidence.
The reviewed mapping and exact param/npbind SHA256 values are retained in
api/app/native_title_bindings.json; raw files remain ignored under captures/.
Unknown publisher payloads, keys and personal data are not included. The API
uses this evidence for game identity only, never unlock/authenticity claims.
The general fallback uses already validated publisher title translations and
Python's existing Unicode library; no new third-party dependency/API was added.

## PS4 collection membership follow-up (2026-10-19)

Read-only FTP retrieved two equal bounded copies of the installed CUSA02344
param.sfo/npbind.dat. The former identifies APP_VER 01.02 and content ID
EP9000-CUSA02344_00-UNCHARTEDTRILOGY; the latter explicitly lists NPWR09798_00,
NPWR09799_00 and NPWR09801_00. Header sizes, typed entry layout and trailing SHA1
are validated by `scripts/inspect-ps4-collection.py`. Reviewed membership and
evidence hashes live in api/app/ps4_collections.json; raw publisher files and
personal captures are not shipped. This is membership evidence, not unlock
state, hardware authentication, per-component playtime or other-region support.

Independent format reference: [Al-Azif ps4-file-templates/npbind.bt](https://github.com/Al-Azif/ps4-file-templates/blob/3d9e896716a1538a8f078d3642d379d9f64a9707/npbind.bt),
commit `3d9e896716a1538a8f078d3642d379d9f64a9707` (HEAD resolved using
`git ls-remote`, exact-revision source inspected). Research only: no template
source, library, unknown entry payloads or keys incorporated, no new dependency.
The actual installed metadata independently matches this format and its SHA1.

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
were inspected for the optional tunnel. The user now hosts trophy-sync.party
through Cloudflare on another host; this session did not create that route.
[nginx HTTPS module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html)
informs the local TLS gateway.

See [license obligations](THIRD_PARTY.md). Updating a dependency requires reviewing
its API/license, changing the pin/hash, compiling and running relevant regressions.

Public console trust uses the official [ISRG Root X1/X2 certificates](https://letsencrypt.org/certificates/),
compared byte-for-byte with `https://letsencrypt.org/certs/isrgrootx1.pem` and
`https://letsencrypt.org/certs/isrg-root-x2.pem` on 2026-10-08. Bundle hash is pinned
in `config/public-service.json`. The hosted leaf issuer observed was Let's Encrypt
YE2. SDK v0.43's `target/include/netdb.h` declares getaddrinfo/freeaddrinfo and
pthread APIs; the PS5 worker links successfully with those APIs. Console resolver
runtime behavior remains unverified. No SDK/dependency version was changed.

The installed pinned Next.js 16.4.0 source (`dist/server/body-streams.js` and
`lib/router-utils/resolve-routes.js`) confirms the 10 MiB default clone limit and
truncated rewrite body behavior. Official [proxyClientMaxBodySize documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/proxyClientMaxBodySize)
describes the same limit. `config-shared.d.ts`/`router-server.js` confirm the
experimental `proxyTimeout` API used for a 70-second upstream timeout. Both config
options compile in the pinned version. No dependency/image version changed.

## PS4 reader investigation (2026-10-14)

Inspected primary source at exact revisions:
[PS5-Suite payload/main.c](https://github.com/manos555555/PS5-Suite/blob/a4005c1c004aa8baa77e07d69ff7bec3b012bdec/payload/main.c)
and [Apollo-PS4 source/sd.c](https://github.com/bucanero/apollo-ps4/blob/ef0f8fc321ebc187d5b8ef91b8af0648450dc520/source/sd.c).
These save-mount implementations do not establish a read-only PS4 trophy export
path on this console. No source was copied/linked into the product, no new
dependency was added, and neither payload was executed. Their mount/decryption
or privilege-changing behavior is outside the current read-only test scope.
The original export-only capability probe is separately documented in STATUS;
its empty report provides no usable interface verification. Native trophy
registration/unlock source remains unsuitable as an earned-state exporter.

[MyTrophies-PS4](https://github.com/OfficialAhmed/MyTrophies-PS4/blob/e290fbd1cde618720bc90a29323681c90d0c536e/MyTrophies.py)
at `e290fbd1cde618720bc90a29323681c90d0c536e` reads trpsummary.dat JSON
earnedTrophies grade totals. The actual console file matched this aggregate
shape but contains no per-game or individual unlock identities. It cannot fill
the missing PS4 game lists. Research only: no source/dependency incorporated.

Follow-up primary references, research only (no third-party code/keys incorporated):

- [PS4-vsh-utils trophy mount API](https://github.com/hzhreal/PS4-vsh-utils/blob/b8edba35450c69b13f2c67e0dfb7e66f5b37a947/source/trophy.c)
  distinguishes trophy-specific FS exports; its defaults do not establish RO mounts.
- [PS5 Save Mounter](https://github.com/n0llptr/Playstation-5-Save-Mounter/blob/1a0281ea9794afadc2e2da345ca0b66e5db45bc7/mounter_payload/main.c)
  uses linked FS imports and pfsmgr key operations; GPLv3. Its source mounts and
  copy-back path are not suitable for this project's source-preserving reader.
- [LibOrbisPkg PFS reader](https://github.com/maxton/LibOrbisPkg/blob/643477263b2644e0803e0f58b8726ea4e3f3b7d4/LibOrbisPkg/PFS/PfsReader.cs)
  is LGPLv3 and implements readonly userspace package PFS access. Generic package
  key derivation is insufficient evidence for saved trophy image decryption.
- [pkg_pfs_tool saved-data derivation](https://github.com/flatz/pkg_pfs_tool/blob/4e74afa98b0f57b2b50a2182c1ef89905dc040a7/src/keymgr.c)
  identifies the extra saved-data key schedule. It does not provide usable keys
  in its configuration. No code from this repository was linked or copied.


[ps4-trophies TRP/ESFM source](https://github.com/jacopo-degattis/ps4-trophies/tree/15c3cd2a1aa70babb4e76e91f207810ccda77c2e)
was inspected locally at that commit for the public publisher ESFM format constant
and AES-CBC derivation; no code was copied. This constant is intentionally used
by the independent metadata decoder and is not a console/user secret.
[Initial PS4 language enumeration corroboration](https://github.com/bucanero/apollo-ps4/blob/ef0f8fc321ebc187d5b8ef91b8af0648450dc520/common.c)
uses the observed PS4 language indices. Six actual TRPs independently validate.
[PyCryptodomex licensing](https://www.pycryptodome.org/src/license): BSD 2-Clause
and public-domain components; pinned 3.24.1, source archive SHA256
09081666ffc599976c0b8b29caf2cf82212c0f05bed233c8f8ed53e4f6e1d356.
The retained full upstream license is api/licenses/PyCryptodomex.txt.
The successful authorized v3 private-copy test and actual format bindings are
recorded in STATUS; this supersedes earlier mount-capability uncertainty.

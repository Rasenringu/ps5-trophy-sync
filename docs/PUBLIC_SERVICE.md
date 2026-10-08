# Public service build

The default worker and foreground title target `https://trophy-sync.party`.
The user hosts this domain through Cloudflare on another host. This session
changes the repository and local services, not that remote deployment.

## Install and pair

Build with `scripts/Build-Console.ps1 -HostTest` and
`scripts/Build-ConsoleUI.ps1`. Both default to `-Endpoint public`.
Distribute `artifacts/console/final-ui/TrophySync-PS5.zip` with corresponding GPL
source and notices. Users need **both** `TrophySync.elf` in Payload Manager and
the `PPSA99889` foreground title through ShadowMount. The ELF alone has no pairing
display and requires the title's console-local IPC; do not autoload it standalone.
Baseline evidence remains PS5 FW 8.00, Payload Manager 0.5.2, ShadowMountPlus
1.7beta3 and FTPSRV 0.21.1/2121 with kstuff. Other configurations are unverified.

Register/sign in at `https://trophy-sync.party`, launch the title, then scan its
short-lived QR or enter its code at `https://trophy-sync.party/pair`. Confirm the
console/profile. The worker creates a separate server installation identity and
profile-scoped revocable credential for each console installation. No shared
device token, PSN password or permanent credential is shipped in the ELF or QR.
Paired launches import native PS5 trophies and recorded foreground playtime;
PS4 trophies and passive background sync remain unsupported.

Public-service state/queue lives in private app-owned `/data/trophy-sync-party`.
The prior LAN state in `/data/trophy-sync-worker` is preserved and never reused
against the public host. Existing LAN users pair again for the public service.
Reinstalling binaries with state retained reuses that connection; removing state
creates a new installation requiring pairing. Cloning state clones credentials
and is unsupported; revoke affected devices rather than copying credentials.
The existing server ownership rules apply; this is not hardware authentication.

## Host settings

On the remote production host, set `PUBLIC_ORIGIN=https://trophy-sync.party`
in its private production env file and recreate/build the production services.
The provided production Compose maps this to `WEB_ORIGIN`, enables secure cookies
and keeps development imports disabled. Custom deployments need
`WEB_ORIGIN=https://trophy-sync.party` and `COOKIE_SECURE=true` on the API and
`PUBLIC_ORIGIN=https://trophy-sync.party` on the web build/runtime. These exact
values are now applied to this PC's local `.local/app.env` and running API/web.
Local plain HTTP login writes consequently cannot serve the public-origin setup.
After updating the remote host, run `scripts/Test-PublicService.ps1`. On
2026-10-08 the remote invalid registration probe returned **403 Same-origin
request required**, while this updated PC returned the expected **422** missing
fields response. Remote registration/pair approval remains blocked until its API
origin is corrected. Neither probe created an account.
Later route/browser checks on the same date now accept the public origin (422
for empty registration), and desktop registration works according to the user.
The outstanding physical iPhone/Firefox issue is tracked in
[browser troubleshooting](WEB_TROUBLESHOOTING.md).

Route Cloudflare to the production gateway as described in
[self-hosting](SELF_HOSTING.md). Keep `/api/device/*` reachable without browser
challenges/Cloudflare Access, while retaining API device authentication and rate
limits. The gateway allows up to 64 MiB specifically on `/api/device/artwork`;
other requests retain their tighter limits. Do not cache authorization or sync
responses. A health response alone does not validate registration or pairing.
For the user's `Start-Local.ps1` stack with Cloudflare forwarding to port 3000,
Next.js now buffers up to 64 MiB and permits a 70-second upstream request. Its
former 10 MiB default truncated large artwork uploads. Copy the updated
`web/next.config.ts` and API source to the host and run `Start-Local.ps1 -Build`;
existing environment values and database volume are retained. The production
gateway routes artwork directly to the API and also retains its 64 MiB limit.

## Transport policy and evidence

The worker uses the configured system resolver, requests IPv4 addresses and
tries up to two TCP destinations. DNS waiting is limited to three seconds,
TCP connections to five seconds each; at most one outstanding resolver per
transport is retained, preventing stalled retries from accumulating threads.
No public IP is frozen into the ELF and no console DNS setting is altered.
DNS redirection/blocking and incorrect console clocks can prevent connection.

Mbed TLS 3.6.7 validates the hostname, certificate chain and dates with TLS 1.2.
The pinned PEM bundle contains only official ISRG Root X1/X2 trust anchors.
Their checked-in bytes were compared to the official Let's Encrypt PEM files;
bundle SHA256 is in `config/public-service.json`. Certificate renewal under those
roots needs no rebuilt ELF; changing to another CA requires reviewed trust inputs
and a rebuild. There is no insecure mode, leaf-certificate pin, redirect following
or silent fallback to LAN/plaintext. See [official chain documentation](https://letsencrypt.org/certificates/).

Opt-in host check after `-HostTest` (no account/installation creation or import):

```powershell
docker run --rm --mount "type=bind,source=$PWD,target=/workspace" ps5-trophy-build:starter python3 /workspace/console/tests/test_public_transport.py
```

Host Mbed TLS JSON and 96-byte binary checks against the public service returned
authenticated-TLS HTTP 401 without a token; incorrect hostnames were rejected.
Local fixtures cover hostname resolution, TLS/framing, stalled DNS, private
storage, pairing/ownership isolation, queue replay and native readers. **No new
ELF/title has been sent to or executed on a PS5 in this session.** Public pairing,
actual trophy/playtime/artwork imports and DNS availability on nanoDNS-equipped
consoles still require authorized hardware observation. Recovery/email
verification and host restore/operational gates remain in [ROADMAP](ROADMAP.md).

## Optional LAN build

Keep `config/local.json` and the matching `.local/tls/identity.json`/CA generated
by `scripts/Start-LanHttps.ps1`. Use `-Endpoint lan` on **both** build scripts;
those builds retain the previous LAN endpoint and `/data/trophy-sync-worker`.
The package manifest records its actual origin and public trust checksum.

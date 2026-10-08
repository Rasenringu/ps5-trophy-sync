# Pairing and import contracts

Browser endpoints are under `/auth` and `/account`; device endpoints under
`/device`. The local web proxy exposes all as `/api/...` on the web origin.
Schemas: `contracts/openapi.json` and the versioned snapshot schemas in `contracts/`.

## Installation and profile credentials

The console worker creates an installation once through
`POST /device/installations`. The server issues a random UUID and 256-bit secret.
Save these privately; never put the secret in a QR, query string or log. Creating
another authorization requires that installation's Bearer secret. Knowledge of
an installation UUID alone cannot attach another profile.

`POST /device/pairings` accepts installation UUID, local profile ID and display
label. It returns a 10-minute manual code, verification URL, device authorization
secret, pairing UUID, expiry and five-second interval. Only the verification
URL with the short manual code belongs in the QR. A QR itself is not proof of
physical possession; the signed-in person checks installation/profile and
explicitly confirms access to the displayed code.

The browser inspects the code using `/account/pairings/inspect`, then approves
that exact pairing UUID with `physical_possession:true`. A profile already
owned by another account cannot be approved. The device polls with its secret;
the server enforces interval and expiry, and delivers the random profile token
exactly once. Token/hash, installation secret/hash and sessions are separate.
Only SHA-256 hashes of random secrets are stored; passwords use Argon2id.
The local client must handle a lost token response by requesting a new pairing
after account-side revocation. A consumed authorization never redisplays a token.

Account sessions expire after 24 hours. Browser writes require matching Origin;
cookies are HttpOnly and SameSite=Strict. Secure defaults on in the API, disabled
explicitly for loopback Docker development. Expired/revoked device credentials
return 401; retrying cannot restore authorization.

## Ownership, relinking and cloning

- Identity is server installation UUID + local profile ID. Display names have
  no uniqueness or authority. Different profiles in one installation can be
  paired to different accounts and cannot read each other's records.
- Revocation disables the token and cancels pending/approved authorizations.
  Records and ownership remain. Only the same account may relink that profile.
  Active credentials must be revoked before relinking. Cross-account transfer
  is deliberately unsupported; do not silently move records to another owner.
- Reinstallation with lost installation secret creates a new UUID and needs
  new pairing. Old history stays with its prior account/identity; old credentials
  should be revoked from the dashboard. No automatic hardware-identity merge.
- Cloning installation files clones that logical identity and credentials.
  This cannot be detected as physical hardware cloning. Revocation affects
  every clone using the same credential. No anti-cheat/authenticity claim.

## Imports

`POST /device/sync` takes a profile token and versioned snapshot with UUID
batch ID, explicit `mock` flag and independent `ps5_native` or `ps4_bc` source.
There is no caller-supplied account/profile override. Each profile's row lock
serializes import/revocation and prevents simultaneous repeated batches.
Repeated batch/content is acknowledged; reused batch ID with altered content
returns 409. Missing rows never delete data. Mock and non-mock namespaces are
separate; setting mock=false is a device assertion, not hardware validation.

Trophies retain previously observed unlocks and timestamps. Unknown timestamps
are null, never fabricated. Activity identities must represent stable source
events rather than download times. Updating a session does not add another
session. Completed sessions do not regress to incomplete observations. The dashboard sums complete native foreground counters independently of source-clock trust;
legacy wall-clock durations require trusted clocks. Schema 3 activity observations
carry exact single-profile header binding, stable scoped session digests and
native foreground counter provenance. Replays merge monotonically; incomplete
observations cannot replace complete sessions. See [playtime](PLAYTIME.md).

The schemas validate normalized records, not hardware authenticity. Native
T2PD/T2TD/UCP readers have console evidence, with stable-read rather than atomic
source-generation provenance. PS4 import contracts do not establish a PS4 reader.
API limits request bodies to 2MB and each category to 2,000 records per batch.
Large exports must split batches with stable event identities.


## Console client

The worker links pinned Mbed TLS with mandatory certificate chain and hostname/IP
validation. There is no insecure fallback or redirect-following. Its current
endpoint is a compile-time numeric IPv4 address and public CA certificate generated
from private local HTTPS configuration. Public DNS/endpoint support needs its own
configuration and validation before hosting the console route externally.

Installation/profile credentials and queue reside in root-owned private worker
storage. Pending batches keep their exact UUID/body across retries. The worker
requires an exact successful import/duplicate acknowledgement before marking a
batch acknowledged. Transport/429/5xx retries have a five-attempt bound with
exponential waits; revocation, rejected imports and invalid acknowledgements stop
without discarding pending data. Pair polling is bounded by expiry.

Saved worker pairing, real imports, Close App/reopen and repeat sync have user
observations. Full offline recovery, independent second-profile hardware isolation
and worker shutdown/lifetime still need console results. [STATUS](STATUS.md)
separates those gates from local auth/ownership/idempotency tests.

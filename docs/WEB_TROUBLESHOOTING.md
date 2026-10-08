# Browser registration and API routing

Cloudflare can forward to port 3000. Next.js rewrites `/api/*` to `http://api:8000/*`
inside Docker; the API port does not need a separate public tunnel or exposure.
This route was checked on the hosted site on 2026-10-08.
The user later confirmed phone login worked over HTTPS; the failing phone tab
had used HTTP. This was not a port 3000/8000 reachability problem.

## PS5 artwork uploads

An API `ClientDisconnect` during `/device/artwork` can indicate an interrupted
or truncated upstream upload. A real defect was reproduced in Next.js's default
10 MiB rewrite buffer: the isolated receiver got 10 MiB of a declared 11 MiB
upload. The fixed config allows 64 MiB, matching the API's package bound, and
a 70-second proxy timeout. Deploy updated host source with `Start-Local.ps1 -Build`.

The API now handles incomplete/interrupted streams explicitly and never caches
partial packages. The worker preserves specific artwork HTTP/TLS errors instead
of replacing them with a generic native collection failure. Restart/retry does
not require deleting device credentials, database volumes or pending batches.

Local regression after building the web/API images:

```powershell
python scripts/test-web-upload-proxy.py --size-mib 11 --size-mib 64
```

This uses fresh isolated Docker containers/network and a MOCK receiver, checks
full byte counts/hashes, and cleans up those fixtures. It does not test the
remote tunnel, real parser or PS5 hardware. `Test-Local.ps1` covers authenticated
artwork parsing/ownership/idempotency and partial-stream refusal independently.

## Registration diagnostics

`python scripts/test-api-routes.py` checks every documented GET/POST route that
can be safely probed anonymously: 28 routes, plus two intentionally skipped
successful-write endpoints (`/device/installations`, `/auth/logout`). Its report
is `artifacts/tests/public-api-routes.json`. Empty registration/login requests
must return 422, private routes 401, nonexistent public players 404, health 200.
These responses verify routing/auth/validation, not authenticated success or a
real sync. Successful writes and ownership rules are covered by the isolated
`scripts/Test-Local.ps1` API suite.

Desktop/mobile browsers should use the exact configured HTTPS origin. The current
settings are `WEB_ORIGIN=https://trophy-sync.party`, `COOKIE_SECURE=true` in the
private `.local/app.env`. Do not permit arbitrary origins to bypass a 403.

The previous web client mapped the API's plain-text origin refusal to a generic
connection error. The updated API returns a JSON `origin_mismatch` error and the
configured public URL. The client handles both old and new origin errors,
Cloudflare challenge responses and unexpected HTTP responses separately, with
translations. A missing/malformed/null/wrong Origin still fails closed.

After copying these updated files to the Mini-PC, run:

```powershell
.\scripts\Start-Local.ps1 -Build
.\scripts\Test-PublicService.ps1
```

Retry one login on the affected phone, then inspect:

```powershell
docker compose --env-file .local/app.env -f deployment/compose.yaml logs --since 5m api
```

For API-origin failures, look for `Browser origin rejected: received=... expected=...`.
Those entries exclude request bodies, passwords, cookies and account IDs. If the
browser fails but no corresponding API request appears, check the web container
and Cloudflare security events for that request/time. Never share tunnel tokens,
authorization headers or cookies when supplying diagnostics.

Use Safari on the same iPhone/Wi-Fi as a comparison with Firefox. A successful
desktop test and mobile emulation do not prove the physical phone works.

Focused mobile error tests (synthetic responses, no accounts created):

```powershell
docker build -f web/Dockerfile.test -t ps5-sync-web-test web
docker run --rm --ipc=host ps5-sync-web-test npx playwright test --config=playwright.mobile.config.ts
```

The dedicated config tests WebKit and Chromium without Chromium-specific DNS
launch flags being passed to WebKit. Real phone diagnosis remains necessary.

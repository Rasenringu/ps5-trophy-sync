# Self-host TrophySync

The user hosts **https://trophy-sync.party** through Cloudflare on a separate host.
The default console build now targets that domain. Host transport checks pass;
console pairing/sync against the public host still needs hardware validation.
See [public service setup](PUBLIC_SERVICE.md) for current endpoint details.

## Prepare the host

Use Docker Desktop Linux containers on Windows, or Docker Engine with Compose
on Linux. Keep the repository, database volume and private configuration on a
persistent disk. The production stack uses a separate `trophysync` project and
database volume; it does not automatically reuse the development database.

From PowerShell at the repository root:

```powershell
New-Item -ItemType Directory -Force .local/production | Out-Null
Copy-Item deployment/production.env.example .local/production/app.env
# Generate a password; paste the result into POSTGRES_PASSWORD in app.env.
$randomBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($randomBytes)
$randomGenerator.Dispose()
($randomBytes | ForEach-Object { $_.ToString('x2') }) -join ''
```

Set `PUBLIC_ORIGIN` to your exact HTTPS origin, such as
`https://trophy-sync.party`, without a trailing slash or path. Use the same
hostname in the browser and pairing links. Set `LOCAL_WEB_PORT=3001` if the
existing development service still occupies port3000. Keep `.local` private;
it contains credentials, backups and potentially personal data.

```powershell
./scripts/Start-Production.ps1 -ValidateOnly
./scripts/Start-Production.ps1
```

Validation starts nothing. The second command starts the database, migration,
API, web and gateway. API/database ports are private; the gateway binds only to
PC loopback. Production requires HTTPS origin, Secure cookies and disabled demo
imports. Authentication through the local HTTP gateway is not the public login
path, because production cookies require HTTPS.

On Linux the equivalent startup is:

```sh
docker compose --env-file .local/production/app.env -f deployment/compose.production.yaml config --quiet
docker compose --env-file .local/production/app.env -f deployment/compose.production.yaml up -d --build db migrate api web gateway
```

## Cloudflare routing

Create a remotely managed Cloudflare Tunnel and add your chosen public hostname
with origin service **`http://gateway:8080`**. The optional connector runs in the
same Docker network as this gateway. Public browser/console traffic uses HTTPS
to Cloudflare; the origin hop stays inside Docker. No router port forwarding or
console DNS change is required. Follow the official
[remotely managed tunnel guide](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/get-started/create-remote-tunnel/).

Save only the tunnel token in `.local/production/tunnel-token`, without quotes;
do not put it in Git or a command argument. The connector reads a mounted secret
using Cloudflare's [token-file parameter](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/run-parameters/).

```powershell
./scripts/Start-Production.ps1 -Tunnel -ValidateOnly
./scripts/Start-Production.ps1 -Tunnel
```

The pinned optional connector is cloudflared2026.10.0; updates require an explicit
image-pin change. See [sources](SOURCES.md). Verify the public HTTPS site, login,
friend/public sharing and pairing before connecting consoles. The default PS5 package now uses the public URL and public root trust. Rebuild
both worker and foreground title and validate them on the console; configuring a
tunnel does not update installed binaries.

## Back up and move existing data

Use PostgreSQL custom-format dumps; avoid piping binary output through Windows
PowerShell. For the existing development service:

```powershell
New-Item -ItemType Directory -Force .local/backups | Out-Null
docker compose --env-file .local/app.env -f deployment/compose.yaml exec -T db pg_dump -U sync -d sync -Fc -f /tmp/trophysync.dump
docker compose --env-file .local/app.env -f deployment/compose.yaml cp db:/tmp/trophysync.dump .local/backups/trophysync.dump
```

For production substitute `.local/production/app.env` and
`deployment/compose.production.yaml`. Keep backups outside the host too. Take a fresh dump before migrating data. Dumps contain account/device state and must remain private.

To move data, initialize the new production database, stop its API/web/gateway,
copy the dump into its DB container, and restore into its **empty** `sync`
database with `pg_restore -U sync -d sync --no-owner --no-acl /tmp/trophysync.dump`.
If migrations already created tables, recreate only the new empty destination
database first. Run `alembic upgrade head` through the production migrate service
and restart application services. Never drop the source database or use
`down --volumes` against a stack containing data you want to retain. A restored
backup contains existing connection credentials; changing the PS5 endpoint is
still a separate build/validation step.

## What has been verified

An isolated production project passed migrations, health checks, Secure/HttpOnly/
SameSite=Strict cookies, wrong-origin write rejection, disabled demo imports,
security headers and a16MiB authenticated artwork request reaching API validation.
Its temporary test database was removed afterward. This verifies the private
HTTP origin path, not Cloudflare or public TLS. Correct CA/IP and wrong-host/
untrusted-certificate rejection also pass against the existing LAN HTTPS gateway.

Public registration currently has no email-verification or password-reset service.
Those account-recovery features, a real domain/tunnel check and the console's
public-endpoint test remain required decisions before broad public launch. Native
PS4 support and the separate console reliability gates remain documented in
[STATUS](STATUS.md); this hosting preparation does not close them.

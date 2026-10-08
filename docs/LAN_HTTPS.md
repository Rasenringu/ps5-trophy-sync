# LAN HTTPS development server

The web app remains available at http://localhost:3000 on this PC. A PS5 cannot
use that loopback address to reach the PC. Start the optional gateway:

```powershell
& ./scripts/Start-LanHttps.ps1
# Or explicitly select this PC's LAN address:
& ./scripts/Start-LanHttps.ps1 -ServerIp <PC-LAN-IP>
```

The script uses config/local.json's PS5 IP only to choose the PC's LAN interface;
it sends no packet to the console. It prepares https://<PC-LAN-IP>:8443, saves it
to the ignored local configuration, and proxies the existing Next.js web app and
a separate API instance with the HTTPS browser origin and Secure cookies. Both
API instances share the existing PostgreSQL database. HTTP loopback development
continues working. No database volume is reset, DNS changed or port forwarded.

The gateway is nginx1.30.5-alpine, digest-pinned in compose.lan-https.yaml. TLS1.2
and TLS1.3 are enabled. It binds only the selected PC LAN address. Request-body
limits apply; access logging is disabled. Default HTTP interfaces remain loopback.

Development CA/key and 30-day IP-SAN server certificate are generated locally
with OpenSSL in the SDK builder. The CA expires after90 days. Keys live in ignored
.local/tls, with directory ACLs restricted to the current Windows user, SYSTEM and
Administrators. The machine/browser trust store is never modified. Only ca.crt
is a public trust artifact; never distribute ca.key or server.key. Existing
certificate material, identities or unrelated service URLs are not overwritten.
Inspect expiration/rotation deliberately; the script does not silently rotate.

```powershell
python ./scripts/test-lan-https.py
```

Actual local checks require the configured CA and correct IP to succeed, and a
wrong hostname and untrusted CA to fail. The C probe adds equivalent checks with
its own Mbed TLS implementation. Neither local test proves the PS5 can reach the
port or validates its clock/entropy/TLS runtime. No firewall rule is changed.
A LAN refusal/timeout on the console must be diagnosed before sending tokens.

Browsers will distrust the development CA until explicitly trusted by the user.
Do not bypass certificate checks for pairing. For ordinary local review use the
existing localhost:3000 app. A public deployment needs its own authorized host,
domain and managed trusted certificate; this LAN gateway is development only.
The PC hosts the API here; it is not a console-data relay in the product design.

To stop the gateway while retaining application data:

```powershell
docker compose --env-file .local/app.env --env-file .local/lan-https.env -f deployment/compose.yaml -f deployment/compose.lan-https.yaml stop lan-https lan-api
```

Source: [nginx HTTPS module](https://nginx.org/en/docs/http/ngx_http_ssl_module.html).

Console evidence: the background C transport reached the gateway with CA/IP
verification and rejected wrong-name/untrusted certificates. Real foreground
pairing and direct worker imports also succeeded on the test setup. These results
do not establish a public hosted endpoint. See [STATUS](STATUS.md).

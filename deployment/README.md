# Local Docker deployment

Run scripts/Start-Local.ps1 -Build from native PowerShell. Compose starts
PostgreSQL, runs Alembic before API startup, and serves the Next.js dashboard on
loopback. Base images are pinned by tag/digest. App tools run inside Linux
containers; no host WSL distro, Python or Node required.

Generated .local/app.env contains a random database password and is ignored.
The Docker database volume persists across restarts. No automatic seed or
console contact occurs. Application tests use a separate database; browser
tests create labeled synthetic development records.

This Compose config is loopback HTTP development. Before direct console sync,
configure an authorized reachable HTTPS ingress, exact service URL, trusted
certificate chain, WEB_ORIGIN and Secure cookies. Certificate and hostname
validation must succeed on the console. Do not expose development HTTP or
disable TLS checks to make pairing work.

No production ingress has been deployed, public DNS changed or external service
published. A PC-hosted development API is not a required final-product sync relay.

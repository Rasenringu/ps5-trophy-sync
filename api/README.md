# API

FastAPI/Pydantic v2/SQLAlchemy 2/PostgreSQL. Direct requirements are in
requirements.txt; requirements.lock pins resolved runtime/test dependencies.
Alembic's initial revision contains frozen DDL, independent of future model edits.

Start via scripts/Start-Local.ps1. Run scripts/Test-Local.ps1 against the isolated
PostgreSQL sync_test database. Never set the test DATABASE_URL to the application
database. Tests refuse to reset a database without the `_test` suffix.

See docs/PAIRING_AND_IMPORTS.md and contracts/openapi.json. Device ingestion
accepts normalized records; it does not parse PS5 databases or attest provenance.
No PSN credentials required. Endpoints never trust a client owner ID.

Production requires WEB_ORIGIN=https://your-domain, COOKIE_SECURE=true and HTTPS
ingress. Loopback Compose is development only. API defaults Secure cookies on.
Rate limits are stored in PostgreSQL and shared across workers. A reverse proxy
must preserve Origin; source-IP limits currently see the proxy peer, so production
needs deliberately trusted ingress client-IP configuration and edge limits.

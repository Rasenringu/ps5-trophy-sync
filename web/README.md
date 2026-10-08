# Web application

Next.js/React/TypeScript with resolved dependency versions/integrity in
`package-lock.json`. Docker builds run production compilation and TypeScript
checks; no host Node installation is required. Start with
`scripts/Start-Local.ps1 -Build` and open http://localhost:3000.

Features include registration/login, libraries, trophy/session details, console
pairing/revocation, optional public player libraries, friends and comparisons.
Secret trophy metadata/image authorization depends on the viewer's earned state.
Responsive compact/card views, seven interface locales and publisher package
translations are supported. See the root README and current feature documentation.

`scripts/Test-Web.ps1` uses the pinned Playwright image and Chromium. Browser
hostname mapping preserves the localhost origin for write protection. Endpoint
tests create labeled local test accounts; no console is contacted. Temporary
fixture secrets are not permanent product credentials.

Development samples and `/test` are disabled by default. Explicit
`ENABLE_DEVELOPMENT_TOOLS=true` enables a temporary local sample workflow;
production prohibits it. See [test instructions](../docs/TESTING_LOCAL.md).

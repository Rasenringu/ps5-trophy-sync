# Missing library entries: continuation plan

2026-10-14. User requests native Uncharted, Attack on Titan/Nathan Drake PS4
entries and playtime-only Simpsons/Sonic recomp games. See STATUS for evidence.

1. Implemented and locally verified: 128 MiB package bounds throughout; chunked
   stable second reads; activity-only web/private/shared entries; native CUSA
   sessions and optional PS4 names from observed app.db; playtime before trophies.
2. One diagnostic run was expressly authorized and executed. Real recomp counters
   and CUSA sessions were observed, without source DB copies, mounts or changes.
   Changes to the PS4 name lookup after that run are not yet hardware validated.
3. Upgrade the existing hosted API/web checkout, preserving env/database volume,
   with `scripts/Start-Local.ps1 -Build` (or the existing production Compose
   workflow), plus its nginx configuration if used. The current worker requires
   the API's expanded CUSA validator and 128 MiB artwork limit.
   User will commit/pull to the Docker host 192.168.1.100 themselves. Remote
   management access from this PC is unavailable; no host deployment has occurred.
4. Obtain authorization for the **new worker** test: replace only the installed
   TrophySync.elf, leave title/autoload/other payloads and saved pairing/queue
   untouched, then launch TrophySync normally. Reads native activity/metadata/
   trophies; writes only its existing private queue/connection state and performs
   authenticated uploads to the user's existing service. Confirm Uncharted's 101
   trophies, recomp counters, PS4 names and replay without doubled durations.
   Prior one-shot diagnostic approval does not authorize this different sync test.
5. PS4 trophies require an independently verified read adapter. Current files are
   sealed images and the visible existing mount is empty; the probed databases
   cannot open. Ask user to open the missing PS4 game's trophy list and inspect
   existing read-only mount again. Do not mount images, patch services, register/
   unlock trophies or change databases on the assumption this is authorized.
6. If readable PS4 state is still unavailable, research a read-only system query/
   mount path, prepare a narrowly scoped concrete probe, and obtain its specific
   authorization before execution. Do not substitute invented state or treat
   package definitions as earned evidence. Keep native and PS4 adapters separate.

Native source captures and the diagnostic report are under ignored
captures/library-investigation. They contain personal console data and must
never enter Git or a distributable package. Built worker/ZIP are under ignored
artifacts/console/final-ui. No dependency pins were changed.

# Passive sync after jailbreak: capability assessment

Inspected2026-10-08. The current installed TrophySync worker is a foreground-
requested, one-shot sync worker, not a resident service. Opening the app starts
sync automatically; there is no additional manual sync button to press.

## What the source establishes

`console/worker/main.c` waits for a valid console-local UI request
before starting its network thread. Without a first request it exits after20s;
after requests begin, its loop ends after35s without a UI peer, after a maximum
15minutes, or when the foreground user changes. The network thread pairs/restores
a connection, flushes saved batches, reads/upload trophies/artwork/activity once
and returns. Simply autoloading the existing ELF would not start unattended
sync and would not make it resident. Actual exit timing/survival under games and
rest mode remains a separate hardware gate; these are inspected source limits.

[Payload Manager0.5.2](https://github.com/itsPLK/ps5-payload-manager/blob/v0.5.2/README.md)
supports configured automatic startup of payloads. Its pinned source
`e4e72dc9d831dd09ee8fabc222ad1e7f5139050e`, `src/autoload.c`, reads explicit
settings/list, waits briefly for its frontend or a timeout, then processes its
startup list. The installed version was previously observed as0.5.2. The user's
[WebKit Autoloader0.5.1](https://github.com/itsPLK/ps5-webkit-autoloader/blob/v0.5.1/README.md)
is recorded separately, commit4ad7135e1939cae6f14cbf52957db2e33385f154;
its exact current active chain/config was not changed or re-probed here. kstuff
alone is not an autostart facility. No etaHEN/onionHEN requirement is introduced.

## Proposed resident mode

A separate worker mode would start itself after the selected loader is ready,
restore only an already authorized profile connection and periodically inspect
consistent native read snapshots. Initial pairing would still use the foreground
app. Keep at most one instance, reuse loopback status for the UI, preserve durable
idempotent queues/acknowledgements, and bound both workload and backoff. Stop
sending on revocation or ambiguous/changing foreground identity. Do not expose
credentials or a remote command interface.

Use cheap change checks before re-reading trophy packages; cached artwork should
not upload on every interval. Completed native playtime records can be imported
after closing a game. Rest-mode handling relies on native foreground counters
already established, rather than counting elapsed wall time. A failed network
must defer uploads instead of continuously retrying while the console is asleep.
Exact polling intervals/resource ceilings should be chosen from measured cost.

Before enabling autoload, validate an explicitly bounded resident candidate:
normal UI Close App, a game launch/close, duplicate-start rejection, offline
retry/revocation, user changes and rest/wake with the user's existing jailbreak
recovery. Measure CPU/memory/traffic and observe console responsiveness. None of
those resident-mode results is implied by earlier one-shot import success.

No resident mode was enabled or claimed in this UI milestone. No autoload list,
loader/DNS configuration, power state or source database changed.

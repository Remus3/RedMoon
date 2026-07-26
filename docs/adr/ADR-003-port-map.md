# ADR-003 - Port map

**Status:** Accepted, 2026-07-26

## Context

Another project runs continuously on this machine and holds ports 8888, 8889 and
8893, and reads a vendor API on 2999. Red Moon must be able to run at the same
time without contention, and a port collision surfaces as a confusing runtime
failure rather than a clear error.

## Decision

Red Moon owns exactly four ports:

| Service | Port |
|---|---|
| RedMoon.Bridge, live game JSON | 8777 |
| Dashboard, HTTPS | 8778 |
| Vision server | 8779 |
| Bloodforge engine | 8783 |

These are declared once, in `core/ports.py`. No port literal may appear anywhere
else in the source. `tests/test_ports.py` enforces this over `.py`, `.cs`,
`.json` and `.ps1`: the other project's ports may appear nowhere, and Red Moon's
own four only in `core/ports.py`, this ADR, `CLAUDE.md`, `README.md` and the
tests. `.cs` is in the scan set because the cycle 2 bridge is C# and is the
thing that binds 8777.

All four were confirmed free on this machine on 2026-07-26.

## Consequences

- Both projects run concurrently without contention.
- Changing a port is a one-line change plus an ADR amendment.
- The guard test fails loudly if a literal creeps back in.

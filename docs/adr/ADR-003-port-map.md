# ADR-003 - Port map

**Status:** Accepted, 2026-07-26. AMENDED by ADR-005, 2026-07-26: the count is
now five, not four. ADR-005 adds 8780 for the dedicated-server bridge. The
"exactly four" wording below is superseded; everything else stands.

**AMENDED 2026-08-01: the count is now SIX, and Red Moon holds a reserved
BLOCK rather than a scatter of individual ports.** See "Block reservation"
below. 8770 is added for the headless control plane.

## Context

Another project runs continuously on this machine and holds ports 8888, 8889 and
8893, and reads a vendor API on 2999. Red Moon must be able to run at the same
time without contention, and a port collision surfaces as a confusing runtime
failure rather than a clear error.

## Decision

Red Moon owns exactly four ports (now five, see ADR-005):

| Service | Port |
|---|---|
| Headless control plane (ADR-003 amendment, 2026-08-01) | 8770 |
| RedMoon.Bridge, client host, live game JSON | 8777 |
| Dashboard, HTTPS | 8778 |
| Vision server | 8779 |
| RedMoon.Bridge, dedicated-server host (ADR-005) | 8780 |
| Bloodforge engine | 8783 |

These are declared once, in `core/ports.py`. No port literal may appear anywhere
else in the source. `tests/test_ports.py` enforces this over `.py`, `.cs`,
`.json` and `.ps1`: the other project's ports may appear nowhere, and Red Moon's
own four only in `core/ports.py`, this ADR, `CLAUDE.md`, `README.md` and the
tests. `.cs` is in the scan set because the cycle 2 bridge is C# and is the
thing that binds 8777.

All four were confirmed free on this machine on 2026-07-26.

## Block reservation, added 2026-08-01

Three projects now share this machine, and until 2026-08-01 only Red Moon could
answer "which ports are mine" without grepping bind sites. Blocks were agreed so
each project can prove disjointness without reading the other two trees.

**Red Moon reserves 8770-8789.** Twenty ports, six allocated. The block was drawn
around where Red Moon already was, so nothing moved.

The block reads as two regions, and the split is deliberate:

- **8770-8776, infrastructure.** Things that serve Red Moon's own development
  rather than the game. 8770 is the headless control plane.
- **8777 and up, game services.** Anything that talks to V Rising.

This corrects a mistake worth recording: Red Moon believed 8781 and 8782 were
"the free ones". That was true about the interior of the used region and missed
that the block FLOOR was never allocated at all - 8777 is merely the lowest USED
port. The structural split was proposed by a sibling project and adopted.

**The other three blocks are NOT written here, deliberately.** Disjointness is
proven from the negative side: `tests/test_ports.py` carries a FORBIDDEN set and
fails on any foreign literal in Red Moon source. Mirroring another project's
allocation would create a second copy that drifts, and would trip that very
guard. `tests/test_ports.py::test_every_port_sits_inside_the_reserved_block`
asserts the positive half.

Reserved is not bound. 8778, 8779, 8783 and now 8770 are allocated to work that
does not exist yet, and a live port scan showing them free is not evidence they
are available.

## Consequences

- Both projects run concurrently without contention.
- Changing a port is a one-line change plus an ADR amendment.
- The guard test fails loudly if a literal creeps back in.

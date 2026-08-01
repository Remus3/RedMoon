---
name: project_redmoon_ports
description: "Red Moon reserves the 8770-8789 block and binds 8777, 8778, 8779, 8780 and 8783 within it, disjoint from the three sibling projects on this machine."
metadata: 
  node_type: memory
  type: project
  originSessionId: 63979038-027d-45ec-9321-db0b505baf7a
  modified: 2026-08-01T12:47:49.577Z
---

Red Moon ports, declared once in `core/ports.py`: 8777 RedMoon.Bridge (V Rising
CLIENT), 8778 dashboard, 8779 vision, **8780 RedMoon.Bridge (DEDICATED SERVER,
ADR-005)**, 8783 Bloodforge. A test fails on any port literal elsewhere in the
source.

**Only 8777 and 8780 actually bind today.** The other three are reserved and
unbound - dashboard is cycle 4, engine is cycle 3, vision is cycle 8 and is
conditional. Never infer from a live port scan that they are free.

**Block reservation, agreed with Riot Commander 2026-08-01:** RM owns
**8770-8789** (20 ports, 5 used, 8781 and 8782 free inside it). Siblings on this
box: RC 8888-8895, LegionWallpaper 8900-8919, Daemon Slayer 8860-8879 reserved.
RM accepted the block as drawn and moves nothing. **RM does not carry sibling
port numbers in any TRACKED file** - `tests/test_ports.py` proves disjointness
from the negative side via a FORBIDDEN set instead.

**Why:** three projects share this machine and all must run concurrently without
contention. Until 2026-08-01 Red Moon was the only one of the three that could
answer "which ports are mine" without grepping bind sites; RC has since copied
the pattern.

**How to apply:** import from `core.ports`. Never write a port number inline. The
C# bridge cannot import it, so `tools/gen_bridge_ports.py` GENERATES
`RmPorts.g.cs` and a test asserts the on-disk file equals a fresh render - the C#
binder cannot drift. See ADR-003, ADR-005, [[project_vrising_build_pin]] and
[[project-redmoon-headless-gap]].

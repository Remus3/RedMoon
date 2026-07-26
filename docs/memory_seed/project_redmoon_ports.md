---
name: project_redmoon_ports
description: Red Moon owns ports 8777, 8778, 8779 and 8783, deliberately disjoint from the other project on this machine.
metadata:
  type: project
---

Red Moon ports: 8777 RedMoon.Bridge, 8778 dashboard, 8779 vision, 8783
Bloodforge. Declared once in `core/ports.py`; a test fails on any port literal
elsewhere in the source.

**Why:** another project runs continuously on this machine holding 8888, 8889
and 8893. Both must run concurrently without contention.

**How to apply:** import from `core.ports`. Never write a port number inline.
See ADR-003 and [[project_vrising_build_pin]].

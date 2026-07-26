---
name: project_vrising_build_pin
description: V Rising build 1.1.13.0-r99712 at the Steam default path is the data pin for Red Moon.
metadata:
  type: project
---

Game build `1.1.13.0-r99712`, parsed from `VERSION`
(`VRising: v1.1.13.0-r99712-b17 (202605251526)`), installed at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`. The client install also
ships the dedicated server.

**Why:** extracted data is written per build, so a Steam update lands in a new
directory instead of corrupting the old one.

**How to apply:** after any game update run `python tools/rmdata_extract.py` and
re-validate before bumping any engine version. See
[[project_stats_require_bridge]].

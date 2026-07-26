---
name: project_stats_require_bridge
description: V Rising item and ability stats cannot be extracted offline; only the runtime bridge dump provides them.
metadata:
  type: project
---

`StreamingAssets\Localization\English.json` maps a localization GUID to display
text and carries no item identity and no stat line. Identity and stats live in
binary DOTS ECS blobs (`ContentArchives`, 1402 `EntityScenes` files). No offline
join exists.

**Why:** this was measured on 2026-07-26, not assumed. It is why the cycle 1
tables ship empty but typed.

**How to apply:** do not re-pitch an offline extractor for item stats, and do
not seed the repository from third-party GUID dumps. The authoritative source is
the cycle 2 RedMoon.Bridge runtime prefab dump. See ADR-002 and
[[project_redmoon_ports]].

# Red Moon Roadmap

Each cycle is its own session with its own spec under `docs/superpowers/specs/`.

## Cycle 1 - Harness plus data floor (DONE)

Process harness, enforcement hooks, doctrine docs, memory namespace, and the
offline extractor producing `data/rmdata/<build>/`.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`
Ledger: `docs/LEDGER.md` entry 001.

## Cycle 2 - RedMoon.Bridge (CURRENT)

BepInEx plugin serving live game JSON on 8777, plus the runtime
`PrefabCollectionSystem` dump that populates the cycle 1 table schemas with real
item and ability stat data.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md` (APPROVED
2026-07-26). The plugin targets both the client and the dedicated server, per
ADR-004, and each host binds its own port, per ADR-005.

`PrefabCollectionSystem` is no longer an unverified label. It was CONFIRMED
against this build on 2026-07-26: `ProjectM.PrefabCollectionSystem` in
`ProjectM.Shared.dll`. See `docs/BRIDGE_SPIKES.md`.

Progress. The Python half is shipped and green (ledger 002a): port generation,
the bridge client, the nested-shape gate, the VERSION-asserting installer, the
ingest and quarantine path, and the wiredness probe. BepInEx is installed in
both hosts and the dedicated server has generated its interop assemblies.

Remaining, in order:

1. Launch the CLIENT once so it generates its own `BepInEx\interop\`, then diff
   the two interop sets. No `.csproj` reference may be pinned before that diff
   (risk R17).
2. Build a MINIMAL enumerate-and-log plugin first, not the full bridge. Spike S1
   parts b, c and d - the world names per host and the host-detection mechanism
   - cannot be answered from static metadata and need a plugin in-process.
3. Close S2 (main-thread scheduling), S3 (the field-by-field component mapping),
   S5 (listener viability) and S6 (dump cost).
4. Then the full bridge, the live gate once per host, and the first dump.

The seam is already on disk: `data/rmdata/<build>/tables/` holds one empty,
schema-valid envelope per table name in `core/tables.py`. The dump fills those
files in place, and `tools/rmdata_extract.py` never overwrites a populated one.

## Cycle 3 - Bloodforge core

Combat math against V Blood bosses: weapon, spell school, gear tier, blood type
and quality, jewels, passives and resistances, producing DPS, EHP and
time-to-kill. Server on 8783, `ENGINE_VERSION` pinned to the game build.

## Cycle 4 - Dashboard

HTTPS dashboard on 8778 plus the coach loop.

## Cycle 5 - Progression route planner

V Blood dependency graph and tech and recipe unlocks.

## Cycle 6 - Recipe and refinement economy solver

## Cycle 7 - Castle and base optimizer

## Cycle 8 - Ops hardening

RM-Supervisor, `ops/runtime/health.json`, `RM-*` scheduled tasks, and the vision
tier on 8779 if it earns its place.

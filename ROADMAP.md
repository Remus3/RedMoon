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

Steps 1 through 3 are DONE (ledger 002b). The client was launched, the interop
sets were diffed at type level, and a minimal enumerate-and-log probe plugin was
built and run in BOTH hosts. R17, R2, R11, S4, S1(a), S1(c), S1(d), S2 and S5 are
CLOSED by measurement. S6 is partial and cheap. S3 has the item and recipe
mapping. `docs/BRIDGE_SPIKES.md` carries every number and how it was observed.

Remaining, in order:

1. The IN-GAME CLIENT sample, which is the only thing left in S1(b). At the main
   menu the client has two worlds and NO prefab-carrying world, so a client-side
   dump is UNPROVEN. Needs a character loaded. It also unblocks the rest of S3:
   the ability school, V Blood level and blood bonus tiers want a live entity's
   real component list, not more metadata reading.
2. `PrefabDumper.cs` for `items` and `recipes` only - those two are mapped.
   `abilities`, `vbloods` and `blood_types` are not yet writable.
3. The first dump, then `rmdata_ingest` WITHOUT `--accept`: read the shape census
   and the `unmapped` array before deciding whether the schemas or
   `core/table_deep.py` need amending. One amendment is already expected:
   `items.stats` as a flat name-to-number map cannot carry
   `ModifyUnitStatBuff_DOTS.ModificationType`, and an additive and a
   multiplicative modifier of the same value are not the same stat.
4. Then the full bridge and the live gate once per host.

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

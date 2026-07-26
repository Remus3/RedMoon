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
ADR-004. `PrefabCollectionSystem` above is an unverified label, not a confirmed
type name; spike S1 in the spec resolves it.

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

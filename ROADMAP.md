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

Steps 1 through 4 of the previous plan are DONE (ledger 002c). The plugin is
built, it ran live in the dedicated server, and the first real dump is INGESTED:
`items.json` carries 425 rows at `schema_version` 2 and `recipes.json` carries
663. That is the first item stat data ever to enter this repository, and it is
the thing cycle 2 exists to deliver.

The ability school is FOUND: `DealDamageParameters.MainType` on the ability's
`_Hit` entity, six varying samples. The prefab total is 23583, not the 1189 that
was a mid-load artifact. `items.stats` is a ONE-HOP read and the recorded
two-hop finding was wrong. All of it is in `docs/BRIDGE_SPIKES.md`.

Remaining, in order:

1. The IN-GAME CLIENT sample - the last open half of S1(b), and the only item
   that needs the operator. `Client_0` read `Count=0` at the load instant and the
   probe that took the sample could not re-measure. The count-tracking probe is
   deployed to the client but has not run there. Until it does, "the client can
   serve a dump" stays UNPROVEN. Note a Private Game spawns a child
   `VRisingServer.exe` that does NOT load BepInEx, so in that configuration
   neither host serves a dump.
2. `items.tier` is FABRICATED as 0 on all 425 rows. The schema requires it and no
   per-item tier component exists on this build. It owes a real source before any
   cycle 3 consumer trusts it. Do not close this by parsing the `_T0x` name
   token - name-convention guessing already produced one wrong answer this cycle.
3. `items.name` is the prefab name, not a localized display name, and
   `localization_guid` is omitted rather than faked. The prefab-to-localization
   join is unmeasured.
4. `StateReader.cs`. `/state` honestly returns `state: null` today, so
   `bridge_probe --motion-diff` cannot pass.
5. Smaller open ends: `recipes.station_guid` (the station references the recipe,
   not the reverse); the ability-group-to-`_Hit` join needed to assemble an
   `abilities` row; `VBloodConsumeSource.Tier` is metadata-read, not
   value-measured; `Unload()`'s graceful path is still unobserved; and the 4
   `unmapped` recipes are almost certainly `RecipeOutputUnitBuffer` recipes that
   produce a unit rather than an item.

The seam is already on disk: `data/rmdata/<build>/tables/` holds one empty,
schema-valid envelope per table name in `core/tables.py`. The dump fills those
files in place, and `tools/rmdata_extract.py` never overwrites a populated one.

Status 2026-07-26, ledger 002a to 002d. `PrefabCollectionSystem` is CONFIRMED,
not merely a label. All six original spikes S1 to S6 are CLOSED, plus S3a and
S7. The plugin ships and runs live in BOTH hosts: the dedicated server serves
`/dump/prefabs` and the client is proven to serve one too (`Client_0`, 30484
prefabs, 95 ms). `items.json` holds 425 rows at `schema_version` 3 and
`recipes.json` 663. `/state` returns live data and
`bridge_probe --motion-diff --expect-host client` PASSES.

Two fabricated fields were retired on evidence rather than convention:
`items.tier` has no per-item-prefab source on this build (67 `Tier`-shaped
fields across 169 assemblies, zero per item), and the prefab-to-localization
join does not exist offline (0 of 425 on seven key forms).

REMAINING before cycle 2 can close:

- `abilities` and `vbloods` are still not writable. The ability school is found
  (`DealDamageParameters.MainType` on the `_Hit` entity) but the
  ability-group-to-`_Hit` join is not traced, so a row cannot be assembled.
- `blood_types` buffer element fields are unread.
- `recipes.station_guid` is OPEN - the station references the recipe, not the
  reverse.
- `localization_guid` needs the runtime `GameDataSystem.ManagedDataRegistry`
  read.
- Whether client item COMPONENT data matches the server's is UNTESTED; only the
  prefab maps were compared.
- `Unload()`'s graceful path is unobserved, and 4 recipes remain unmapped.

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

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

Status 2026-07-26, ledger 002e. **All five tables are populated.**
`items` 425, `recipes` 663, `abilities` 54, `vbloods` 66, `blood_types` 13, from
(the 66 was CORRECTED to 65 by the next pass - see ledger 002f)
one live server dump in 714 ms. The six open measurements are all closed, and
`docs/BRIDGE_SPIKES.md` "The cycle 2 measurement pass" carries every number.

The corrections that came out of it:

- The ability school is NOT `DealDamageParameters.MainType`. That is the DAMAGE
  type. The schema's `school` comes from `SpellSchoolAbility.AbilityGroup` on the
  `<School>SpellSchoolAsset` prefab, which yields 9 abilities in each of the six
  schools.
- The V Blood level is NOT `VBloodConsumeSource.Tier`, which is a five-valued
  spell-school progression tier. It is `UnitLevel.Level`, measured 16 to 91.
- `blood_types` is `schema_version` 2. There is no quality threshold on the
  prefab and every bonus magnitude reads 0, scaled from blood quality at runtime,
  so the table carries stat NAMES and never a fabricated number.

Status 2026-07-26, ledger 002f. **The client-host pass.** Both hosts ran the
same binary at once and every open item above is now measured. See
`docs/BRIDGE_SPIKES.md`, "The client-host pass".

- **The client and server item COMPONENT data are IDENTICAL.** Row-by-row diff
  keyed on `prefab_guid`, every field: ZERO differing rows across all five
  tables. Either host may serve the dump; the client costs 103 ms, the server
  794.
- **`localization_guid` is WRITABLE on the CLIENT.** The join resolves 425 of
  425 there and 0 of 425 on the dedicated server, and all 425 client guids are
  real `strings.json` keys. The recorded absence was true of the SERVER HOST, not
  of the build. Every dump now carries its own `localization` counters.
- **`recipes.station_guids` is RULED and WRITABLE** at `schema_version` 2,
  ADR-006. 911 unique pairs over 663 recipes; 575 recipes reach a station, 88
  reach none, and 19 sit at twelve stations each.
- **`vbloods` is 65, not 66.** The dumper emitted one row per ENTITY and more
  than one entity can carry the same `PrefabGUID`, so a duplicated Dracula was
  counted twice - and two ability groups likewise, making 56 rows over 54 guids
  on both hosts. Every duplicate pair was byte-identical, so no per-row gate
  could see it. Fixed in the dumper AND gated at ingest.

REMAINING before cycle 2 can close:

- `Unload()` is CLOSED, and the answer is that it does NOT run. On the
  instrumented build a normal in-game quit left BOTH the BepInEx log and the
  independent `redmoon-unload.log` marker empty, and those two channels fail
  independently, so BepInEx 6 IL2CPP does not invoke `BasePlugin.Unload()` at
  shutdown. The port is released by process termination - the same path R11
  already retired for the hard kill - so nothing depends on the graceful one.
- `abilities` covers the 54 spell-school abilities only. Weapon abilities have no
  school asset and produce no row, and 38 of the 54 carry no `damage_type`
  because the projectile deals the damage. Both are the measured edge of the
  join, not defects.
- 4 recipes remain unmapped, all `recipe prefab with an empty item output
  buffer`.

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

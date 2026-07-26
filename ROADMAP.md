# Red Moon Roadmap

Each cycle is its own session with its own spec under `docs/superpowers/specs/`.

## Cycle 1 - Harness plus data floor (DONE)

Process harness, enforcement hooks, doctrine docs, memory namespace, and the
offline extractor producing `data/rmdata/<build>/`.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`
Ledger: `docs/LEDGER.md` entry 001.

## Cycle 2 - RedMoon.Bridge (DONE)

A BepInEx plugin serving live game JSON, plus the runtime `PrefabCollectionSystem`
dump that fills the cycle 1 table schemas with real item and ability stat data.
That data cannot be read offline, so this cycle is the only route by which it
enters the repository, and it has now been taken.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`
Ledger: `docs/LEDGER.md` entries 002a to 002g.
Measurements: `docs/BRIDGE_SPIKES.md` - every number and how it was observed.

**What shipped.** One plugin assembly loading in BOTH hosts (ADR-004), each
binding a port that is a pure function of the detected host (ADR-005): 8777 in
the client, 8780 in the dedicated server. `/health`, `/state` and
`/dump/prefabs`. On the Python side: the bridge client, the shallow and nested
ingest gates, the VERSION-asserting installer, the quarantine path and
`bridge_probe`.

**The data, promoted from a client dump in 103 ms.** All five tables in
`core/tables.py` are populated:

| table | rows | schema_version |
|---|---|---|
| `items` | 425 | 3 (all 425 carry `localization_guid`) |
| `recipes` | 663 | 2 (`station_guids`, ADR-006) |
| `abilities` | 54 | 1 |
| `vbloods` | 65 | 1 |
| `blood_types` | 13 | 2 |

All six original spikes S1 to S6 are closed, plus S3a and S7. `/state` returns
live data and `bridge_probe --motion-diff --expect-host client` PASSES.

**The findings cycle 3 inherits.** Each is measured, not inferred:

- **Either host may serve the dump.** Client and server component data were
  diffed row by row on `prefab_guid`, every field, all five tables: ZERO
  differing rows. Matching counts would have proved nothing.
- **`localization_guid` is writable on the CLIENT only** - 425 of 425 there, 0 of
  425 on the dedicated server. The recorded absence was a true statement about a
  headless HOST that had been written down as a statement about the build. Every
  dump now carries its own `localization` counters so a saved payload says which
  host produced it.
- **`items.tier` has NO SOURCE on this build.** 67 `Tier`-shaped fields across
  169 assemblies, zero per item; `Rarity` zero hits anywhere. It is DECLARED and
  OMITTED, never zero. Both derivations (the `_T0x` name token,
  `ArmorLevelSource.Level`) were rejected on evidence. A consumer must treat
  absent as unsourced.
- **`items.gear_score` is a Red Moon-COMPUTED quantity, not a direct read.**
  Armor, weapon and spell levels come from three separate systems and component
  families.
- **`abilities` covers spell-school abilities only.** Weapon abilities have no
  `<School>SpellSchoolAsset` and produce no row, and 38 of the 54 carry no
  `damage_type` because the projectile deals the damage. Both are the measured
  edge of the join, not defects. **This is a real cycle 3 input gap and is
  carried into the cycle 3 spec rather than left as a footnote.**
- **`blood_types` carries stat NAMES and never a magnitude.** Every `Value` on
  the tier buff reads 0; the numbers are scaled from blood quality at runtime.
- **`Unload()` does not run.** BepInEx 6 IL2CPP never invokes it at shutdown, on
  two independently-failing channels. The port is released by process death, the
  same path R11 already retired for the hard kill. Nothing depends on it.

**Residue, deliberately left open and judged not to block cycle 3.** 4 recipes
remain unmapped, all confirmed to be recipe prefabs with an empty ITEM output
buffer, consistent with the `RecipeOutputUnitBuffer` hypothesis but not proven to
be it. They produce units rather than items and no cycle 3 consumer reads them.

**The lesson, recorded once and worth carrying.** A real measurement can answer
the RIGHT question about the WRONG SUBJECT. "0 of 425" was correct, reproducible
and had a proper negative control, and it described a headless host rather than
the game. Before generalizing a measurement, check what it was taken OF.

## Cycle 3 - Bloodforge core (CURRENT)

Combat math against V Blood bosses: weapon, spell school, gear tier, blood type
and quality, jewels, passives and resistances, producing DPS, EHP and
time-to-kill. Server on 8783, `ENGINE_VERSION` pinned to the game build
`1.1.13.0-r99712`.

Spec, first of two: `docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md`
settles where the boss stat line and the ability coefficients come from. The
combat math is a SECOND spec, opened only against what that spike returns.

Verified inputs on disk, from cycle 2: `items` 425, `recipes` 663, `abilities`
54, `vbloods` 65, `blood_types` 13, under `data/rmdata/1.1.13.0-r99712/tables/`.

Known input gaps the spec must scope rather than assume away. The first two are
the large ones and were found by reading the promoted rows rather than the
schema, at cycle 2 close:

1. **There is no BOSS STAT LINE.** `vbloods` rows carry exactly `level`, `name`
   and `prefab_guid` - no health, no resistances, no damage. `docs/BLOODFORGE.md`
   names `tables/vbloods.json` as the source for "Boss stat line and
   resistances"; the data does not support that claim and the doc is annotated.
   Time-to-kill needs a denominator that is not on disk. Sourcing it is a cycle 3
   SPIKE against the live bridge, not an assumption.
2. **There are no ABILITY COEFFICIENTS.** `abilities` rows carry `name`,
   `prefab_guid`, `school` and, for 16 of 54, `damage_type`. No cast time, no
   cooldown, no damage scalar. Spell DPS cannot be computed from this table as it
   stands.
3. **Weapon abilities have no rows at all.** No `<Weapon>SpellSchoolAsset` exists
   to source a school from, so weapon DPS cannot be scaffolded on `abilities`
   either.
4. **`items.tier` is absent, not zero,** and no consumer may treat it as an
   ordinal.
5. **`items.gear_score` is present on only 117 of 425 rows** and is a Red
   Moon-COMPUTED quantity over three separate level systems, not a direct read.
6. **`blood_types` carries stat NAMES and no magnitudes.** Every value is scaled
   from blood quality at runtime and is not on the prefab.

The PLAYER side is in good shape and is not a gap: 203 of 205 weapon items carry
real `PhysicalPower` or `SpellPower` values, across 29 distinct stat types with
an explicit `modification` on every entry.

CONSEQUENCE for the spec: cycle 3 cannot open by writing combat math. It opens
by settling where the boss stat line and the ability coefficients come from -
almost certainly another measured bridge pass - because a time-to-kill computed
against an assumed boss health is the `items.tier` mistake with a bigger blast
radius.

## Cycle 4 - Dashboard

HTTPS dashboard on 8778 plus the coach loop.

## Cycle 5 - Progression route planner

V Blood dependency graph and tech and recipe unlocks.

## Cycle 6 - Recipe and refinement economy solver

## Cycle 7 - Castle and base optimizer

## Cycle 8 - Ops hardening

RM-Supervisor, `ops/runtime/health.json`, `RM-*` scheduled tasks, and the vision
tier on 8779 if it earns its place.

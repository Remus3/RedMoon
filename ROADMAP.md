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

**PHASES 1, 2 AND 3 ARE DONE.** The input spike is CLOSED. Phase 1 shipped the
exploratory `/dump/components` endpoint and the component inventory for all four
subject classes. Phase 2 shipped the schema'd dump; phase 3 shipped
`/dump/statcontrol` and the prefab-versus-instance VALUE control. Every
measurement is in `docs/BRIDGE_SPIKES.md`; the key-space ruling is ADR-007.

Promoted on disk at `data/rmdata/1.1.13.0-r99712/tables/`, every count asserted
by `tools/rmdata_ingest.py` rather than reported: `items` 425 (schema 4),
`recipes` 663, `abilities` 54, `vbloods` 65 (schema 2), `blood_types` 13,
`ability_stats` **1818** (schema 1, new).

Two results worth carrying out of the spike:

- **`ability_stats` was predicted at 1474 and measured at 1818.** 1474 counted a
  NAME-selected population; the shipped selector is the marker COMPONENT, and
  341 real ability groups use a different naming convention. A pinned count has
  to be a measurement.
- **The one input TTK cannot do without is the one still missing.** Boss
  `max_health` is instance-only, measured, not merely unread. See gap 1.

**The combat-math spec is the next cycle 3 document, and gap 7 must be settled
before it opens.**

Known input gaps the spec must scope rather than assume away. The first two are
the large ones and were found by reading the promoted rows rather than the
schema, at cycle 2 close:

1. **PARTLY CLOSED, and the residue is the important half.** RESTATED
   2026-08-01 from phase 2 and 3 measurement. `vbloods` is now schema 2 and
   carries `physical_power`, `spell_power` and a four-key `resistances` map on
   all 65 rows. Two findings qualify it and neither is cosmetic:
   - `physical_power` EQUALS `spell_power` on every row and both take 33
     distinct values over 33 distinct levels, so they are LEVEL-DERIVED rather
     than per-boss authored.
   - **`max_health` is STILL absent, and is now measured rather than merely
     missing.** It reads 0 on all 65 prefabs. The phase 3 control compared 19
     typed fields between the Dracula prefab (entity 29012) and its live
     instance (322945): 17 IDENTICAL, and `Health.MaxHealth` 0 against 8107.
     That is the "prefab carries nothing, instance does" branch, confined to
     health. NOT spawn scaling, so there is no factor to source. **A TTK
     denominator needs a live world with the boss actually spawned.** It is
     declared and omitted, never zeroed.

   The resistance map is PARTIAL AND NOT COMMENSURABLE: `physical` and `spell`
   read 0 on all 65, `corruption` is 0.5 on all 65, and only `fire` varies (0 to
   75) - and it is an integer RATING, not a fraction. Holy, Silver, Garlic and
   Sun have no unit-side field at all. No consumer may average these four.
2. **CLOSED 2026-08-01.** `ability_stats` ships at schema 1 with **1818 rows**,
   keyed on the ability GROUP per ADR-007. Cast time on 1815 rows, cooldown on
   1818, and the full damage block - coefficient, raw damage, damage type, hit
   counts and the V Blood multiplier - on the 732 groups that reach a `_Hit`
   prefab. Groups that deal no damage keep their row with coefficients OMITTED.
   `abilities` is unchanged and remains the identity and school table.
3. **DISSOLVED, and now implemented.** `ProjectM.WeaponAbilityData` distinguishes
   a weapon group from a spell one BY COMPONENT, so no `<Weapon>SpellSchoolAsset`
   is needed. 42 weapon groups carry an `ability_type`, and
   `items.ability_group_guids` links them to the items that grant them - 563
   links over 425 items. Weapon DPS is now scaffoldable. ADR-007 records the key
   space so this is not re-litigated.
4. **`items.tier` is absent, not zero,** and no consumer may treat it as an
   ordinal.
5. **`items.gear_score` is present on only 117 of 425 rows** and is a Red
   Moon-COMPUTED quantity over three separate level systems, not a direct read.
6. **`blood_types` carries stat NAMES and no magnitudes.** Every value is scaled
   from blood quality at runtime and is not on the prefab.

The PLAYER side is in good shape and is not a gap: 203 of 205 weapon items carry
real `PhysicalPower` or `SpellPower` values, across 29 distinct stat types with
an explicit `modification` on every entry.

7. **THERE IS NO WAY TO FALSIFY THE OUTPUT.** Added 2026-08-01. Gaps 1 to 6 are
   all about SOURCING INPUTS, and so are all six of the spike's acceptance
   criteria - which means **all six can pass with a confidently wrong
   time-to-kill.** Nothing in cycle 3 checks a computed DPS, EHP or TTK against
   an observed kill. V Rising has no replay file, so the anchor has to be a
   recorded combat log or a hand-timed kill against a known V Blood with a known
   loadout. This does NOT block phase 2, which is ingest rather than math, but it
   must be settled BEFORE the combat-math spec opens. Filed in `BACKLOG.md`
   alongside a second gap: no default subject vector is declared, so the first
   TTK published silently ranks every build for anyone who does not override it.

There are TWO NON-ROADMAP tracks running in parallel. Both are infrastructure
rather than cycles, both get their own ledger entries, and neither may fold into
Bloodforge.

**The headless orchestrator and control plane on port 8770.** Phase 0a
(preflight) now PASSES, ledger 003i. Both previously recorded blockers were
wrong: there was no authentication failure, and the trust failure was a
PATH-SEPARATOR MISMATCH in `.claude.json` - `C:\RedMoon` read True while
`C:/RedMoon`, which headless actually reads, read False. Fixed. The second
blocker was a machine-wide `"model": "rc-main"` belonging to a sibling, since
removed by its owner. RM's own PreToolUse gate is MEASURED to fire headless
under `bypassPermissions` on CLI 2.1.220, and to cover `--no-verify`, which the
git hook cannot. **Nothing in RM calls the shared slot governor yet, and the
loop itself does not exist** - that is the next action on this track.

**RM's own link ingest**, `docs/research/LINK_INGEST.md`. Stages 1 to 3 done:
146 of 146 extracted and scored against an RM rubric, 21 survivors above a 6+
threshold chosen from the observed distribution. The corpus is 146 entries, not
the 119 every earlier pass reported. Stage 4 deep-dive has NOT run and nothing
is adopted until stage 6 names an acceptance criterion.

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

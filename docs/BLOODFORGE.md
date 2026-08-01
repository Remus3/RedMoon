# Bloodforge

The Red Moon combat and build engine. Not implemented until cycle 3. This
document is its design contract.

## Purpose

Given a loadout and a target, compute real numbers rather than opinions:

- Damage per second, effective health, and time-to-kill against a specific
  V Blood boss stat line.
- Ranked loadout alternatives and the single highest-value swap.

## Inputs

REWRITTEN 2026-08-01 from the cycle 3 phase 2 and 3 measurement. Every "status"
below is a count taken from a saved payload, not an expectation.

| Input | Source | Status at cycle 3 phase 2 close |
|---|---|---|
| Weapon type and stats | `tables/items.json` (schema 4) | AVAILABLE. 203 of 205 weapons carry real `PhysicalPower` or `SpellPower`, 29 distinct stat types, explicit `modification` on every entry, 899 entries over 425 items. |
| Weapon TIER | - | **NO SOURCE.** Measured absent on this build. `items.tier` is declared and omitted, never zero. Do not derive it from the `_T0x` name token. |
| Weapon to ability link | `items.ability_group_guids` (schema 4) | **AVAILABLE, NEW.** 563 links over 425 items, 0 to 3 each, `[]` when the item grants none. Joins `ability_stats.prefab_guid`. |
| Spell school loadout | `tables/abilities.json` | PARTIAL BY DESIGN. 54 rows, identity and school only, spell schools only. A missing row means "not a spell-school ability", never "not found". |
| Ability coefficients (cast, cooldown, damage scalar) | `tables/ability_stats.json` (NEW, schema 1) | **AVAILABLE.** 1818 rows keyed on the ability GROUP (ADR-007). Cast time on 1815, cooldown on 1818, and the full damage block on 732 - the groups that reach a `_Hit` prefab. A group that deals no damage keeps its row with the coefficients OMITTED. |
| Which power stat a coefficient multiplies | - | **PROVEN ABSENT.** No power-selector member exists across all 51 components on the `_Hit` entity. `ability_stats.power_stat` is declared and never emitted. The combat-math spec must establish this empirically. |
| Per-target damage multiplier | `ability_stats.vblood_damage_modifier` | **AVAILABLE, and BINARY - corrected 2026-08-01.** `DealDamageParameters.MaterialModifiers.VBlood`. The earlier "measured 0.33 to 1.0 over the 732 damage rows" reported a min and a max as if they were a spread. COUNTED: exactly two values - **1.0 on 728 rows, 0.33 on 4**, all four golem-form NPC abilities, and 1.0 on all 409 weapon-linked damage rows. Inert for loadout coaching. Implement it anyway: being 1.0 almost everywhere is what makes an omission INVISIBLE in 99.5 percent of cases while silently tripling golem builds. |
| Blood type and quality | `tables/blood_types.json` | NAMES ONLY. Every magnitude is scaled from blood quality at runtime and is not on the prefab. |
| Gear score, jewels, passives | Live bridge state | `items.gear_score` is present on 117 of 425 rows and is COMPUTED over three separate level systems. |
| Boss level and power | `tables/vbloods.json` (schema 2) | AVAILABLE. `level` 16 to 91; `physical_power` and `spell_power` 21.60 to 111.41. They are EQUAL on all 65 rows and take 33 distinct values over 33 distinct levels, so both are LEVEL-DERIVED, not per-boss authored. |
| Boss resistances | `vbloods.resistances` (schema 2) | PARTIAL AND NOT COMMENSURABLE. Four keys only. `physical` and `spell` read 0 on all 65; `corruption` is 0.5 on all 65; only `fire` varies (0 to 75) and it is an integer RATING needing `ResistanceData.FireResistance_DamageReductionPerRating`. Holy, Silver, Garlic and Sun have no unit-side field and are omitted, never zeroed. **Do not average these four.** |
| Boss MAX HEALTH | - | **STILL NO SOURCE ON DISK, and now we know why.** It reads 0 on all 65 prefabs and is INSTANCE-ONLY: the phase 3 control compared 19 typed fields between the Dracula prefab and its live instance and found 17 identical, with `Health.MaxHealth` 0 against 8107. Not spawn scaling, so there is no factor to recover. A TTK denominator needs a live world with the boss spawned. |
| Difficulty multipliers | `data/rmdata/<build>/difficulty/` | Present from cycle 1. |

**THE ONE INPUT TIME-TO-KILL CANNOT DO WITHOUT IS THE ONE STILL MISSING.**
Cycle 3 phase 2 closed the coefficient gap and most of the boss stat line, and
the health pool is measured to be absent from the prefab rather than merely
unread. Any TTK before that is sourced from a live world is a fabrication with
the `items.tier` shape and a larger blast radius.

**AND SOURCING EVERY INPUT WOULD STILL NOT MAKE THE OUTPUT RIGHT.** Nothing here
checks a computed DPS, EHP or TTK against an observed kill. That is ROADMAP
cycle 3 gap 7, and it is now SETTLED - though not yet DISCHARGED - by
`docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md`, which
fixes the anchor protocol, run identity, tolerances, the publication embargo and
the default subject vector.

The embargo is the part that governs this document: **`ttk_seconds`, `dps` and
`ehp` are DECLARED AND NEVER EMITTED until their per-field lift conditions are
met**, following the same idiom as `items.tier`, `vbloods.max_health` and
`ability_stats.power_stat`. `dps` lifts on the per-hit gate alone; `ttk_seconds`
additionally needs the instance-only health denominator and three comparable
runs. The combat-math spec may now open, because an unvalidated engine behind
that embargo is harmless. It may not publish until discharge.

## The combat math

OPEN as of 2026-08-01:
`docs/superpowers/specs/2026-08-01-bloodforge-combat-math-design.md`. Three
results from it belong here, because each one changes what this table above
means:

1. **The damage block is ALL-OR-NOTHING.** Zero of the 732 damage rows omit a
   `coefficient`. A group that reaches no `_Hit` prefab omits the whole block
   together. So "154 links reach a group whose coefficient is omitted" is really
   154 links reaching a group with **no damage at all** - including two of the
   three abilities on the DEFAULT weapon, which makes every GreatSword figure a
   PRIMARY-ONLY figure. ROADMAP gap 10.
2. **42 of 732 damage groups cannot be priced against any boss.** 27 deal holy,
   which has no unit-side field anywhere across 150 enumerated components, and
   15 deal fire, whose integer rating cannot be converted without the global
   constant of gap 8. They are OMITTED from computation, never computed at a
   zero reduction - a zero resistance is a real and different claim. With fire
   unpriced, **every priceable boss differs from every other only by
   level-derived power and by health.**
3. **The default subject vector cannot decide which power stat a coefficient
   multiplies.** 31 of the 32 weapon-linked damage groups are `damage_type`
   physical and 203 of 205 weapons grant `PhysicalPower` and no `SpellPower`, so
   both hypotheses predict the same number for every realistic weapon ability.
   Exactly ONE row in 1818 separates them:
   `AB_Unholy_WardOfTheDamned_AbilityGroup`, spell school unholy, `damage_type`
   physical, `coefficient` exactly 1.0, `hits_per_cast` 1. It is player-castable
   and needs no boss, so it is the cheapest run in the whole protocol and should
   be taken first.

## What is implemented, 2026-08-01

The engine is no longer only its embargo. `bloodforge/damage.py` implements the
per-application damage model (spec section 2) and `bloodforge/dps.py` the cycle
and per-ability DPS (section 4), both behind the embargo, neither publishing
anything. Two properties are worth carrying rather than rediscovering:

- **`cycle` is a MAXIMUM over the three windows, never a sum.** They overlap - a
  cooldown runs during the cast. Summing understates DPS on every cooldown
  ability, and `cooldown` is 0 on 352 of 1818 rows, which is what forces the max
  form. Mutating the implementation to a sum fails five tests, checked.
- **An undefined term is a TYPE, not a `None` and never a number.** `reduction`
  is undefined for fire and holy, `P(G)` is undefined until the experiment runs,
  and the pool behind `raw_damage_percent` is unsourced. Each returns an object
  that supports no numeric protocol at all, so `1.0 - fire` raises immediately
  instead of quietly producing a wrong float three call frames away.

**`GET /record/*` exists and has run against a live world.** It is the only
thing in this project that can produce a falsifiable series, it samples on the
same `MainThreadTick` as `StateReader`, and its first live run corrected two
recorded facts and found two defects. See `docs/BRIDGE_SPIKES.md`.

**60 of 732 damage groups cannot be priced after the power-stat experiment, not
42.** 27 holy and 15 fire are blocked on the reduction side; the other 18 are
corruption and are blocked on the POWER side, because all 18 carry neither a
spell school nor `is_weapon_ability` and so neither hypothesis says anything
about them. Corruption 0.5 is the only nonzero defined reduction on this build
and nothing real reaches it.

## Versioning

`ENGINE_VERSION` EXISTS as of 2026-08-01 and is `0.1.0+1.1.13.0-r99712`, defined
in `bloodforge/__init__.py`. Before that commit it was described as pinned by
this document and by ROADMAP while a repo-wide grep returned nothing - a
document describing an intention as a fact.

Format is `<semver>+<game build pin>`. The semver moves when the MATH changes,
so an anchor recorded against one revision cannot silently vouch for another.
The build pin moves when the game changes, which re-arms the embargo
automatically. A game update forces a data refresh and an explicit revalidation
before the version is bumped. Never bump the version in the same commit as an
unvalidated data change.

## Non-goals

- No machine-learned win prediction.
- No opinion-based tier lists. Every ranking traces to a computed quantity.

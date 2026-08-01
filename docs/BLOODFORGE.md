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
| Per-target damage multiplier | `ability_stats.vblood_damage_modifier` | **AVAILABLE, NOT IN THE SPIKE SPEC.** `DealDamageParameters.MaterialModifiers.VBlood`, measured 0.33 to 1.0 over the 732 damage rows. Multiplies boss damage directly. |
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
checks a computed DPS, EHP or TTK against an observed kill. See ROADMAP cycle 3
gap 7 and `BACKLOG.md`; it must be settled before the combat-math spec opens.

## Versioning

`ENGINE_VERSION` is pinned to the game build it was validated against. A game
update forces a data refresh and an explicit revalidation before the version is
bumped. Never bump the version in the same commit as an unvalidated data change.

## Non-goals

- No machine-learned win prediction.
- No opinion-based tier lists. Every ranking traces to a computed quantity.

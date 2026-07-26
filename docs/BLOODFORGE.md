# Bloodforge

The Red Moon combat and build engine. Not implemented until cycle 3. This
document is its design contract.

## Purpose

Given a loadout and a target, compute real numbers rather than opinions:

- Damage per second, effective health, and time-to-kill against a specific
  V Blood boss stat line.
- Ranked loadout alternatives and the single highest-value swap.

## Inputs

| Input | Source | Status at cycle 2 close |
|---|---|---|
| Weapon type and stats | `data/rmdata/<build>/tables/items.json` (cycle 2) | AVAILABLE. 203 of 205 weapons carry real `PhysicalPower` or `SpellPower`, 29 distinct stat types, explicit `modification` on every entry. |
| Weapon TIER | - | **NO SOURCE.** Measured absent on this build. `items.tier` is declared and omitted, never zero. Do not derive it from the `_T0x` name token. |
| Spell school loadout | `tables/abilities.json` | PARTIAL. 54 rows give identity and school only. Weapon abilities produce no row. |
| Ability coefficients (cast, cooldown, damage scalar) | - | **NO SOURCE ON DISK.** Not in `abilities.json`. Needs a measured bridge pass. |
| Blood type and quality | `tables/blood_types.json` | NAMES ONLY. Every magnitude is scaled from blood quality at runtime and is not on the prefab. |
| Gear score, jewels, passives | Live bridge state | `items.gear_score` is present on 117 of 425 rows and is COMPUTED over three separate level systems. |
| Boss stat line and resistances | `tables/vbloods.json` | **NO SOURCE.** Rows carry `level`, `name` and `prefab_guid` only - no health, no resistances, no damage. See below. |
| Difficulty multipliers | `data/rmdata/<build>/difficulty/` | Present from cycle 1. |

**CORRECTED at cycle 2 close.** This table previously named
`tables/vbloods.json` as the source for "Boss stat line and resistances" without
qualification. The promoted rows do not carry one. Time-to-kill needs a
denominator that is not on disk, and sourcing it is a cycle 3 spike against the
live bridge. A TTK computed against an assumed boss health would be the
`items.tier` fabrication with a larger blast radius.

## Versioning

`ENGINE_VERSION` is pinned to the game build it was validated against. A game
update forces a data refresh and an explicit revalidation before the version is
bumped. Never bump the version in the same commit as an unvalidated data change.

## Non-goals

- No machine-learned win prediction.
- No opinion-based tier lists. Every ranking traces to a computed quantity.

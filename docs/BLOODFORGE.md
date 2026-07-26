# Bloodforge

The Red Moon combat and build engine. Not implemented until cycle 3. This
document is its design contract.

## Purpose

Given a loadout and a target, compute real numbers rather than opinions:

- Damage per second, effective health, and time-to-kill against a specific
  V Blood boss stat line.
- Ranked loadout alternatives and the single highest-value swap.

## Inputs

| Input | Source |
|---|---|
| Weapon type and tier | `data/rmdata/<build>/tables/items.json` (cycle 2) |
| Spell school loadout | `tables/abilities.json` |
| Blood type and quality | `tables/blood_types.json` |
| Gear score, jewels, passives | Live bridge state, port 8777 |
| Boss stat line and resistances | `tables/vbloods.json` |
| Difficulty multipliers | `data/rmdata/<build>/difficulty/` |

## Versioning

`ENGINE_VERSION` is pinned to the game build it was validated against. A game
update forces a data refresh and an explicit revalidation before the version is
bumped. Never bump the version in the same commit as an unvalidated data change.

## Non-goals

- No machine-learned win prediction.
- No opinion-based tier lists. Every ranking traces to a computed quantity.

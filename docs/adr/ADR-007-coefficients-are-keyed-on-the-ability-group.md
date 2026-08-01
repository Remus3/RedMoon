# ADR-007 - The coefficient key space is the ability GROUP

## Context

Cycle 3 needs a damage coefficient, a cast time and a cooldown per ability so
Bloodforge can compute DPS. Cycle 2 already shipped an `abilities` table, so the
obvious move was to widen it.

That does not work, and the reason is measured rather than aesthetic.

`abilities` is keyed on the ability group but POPULATED through the spell school:
the dumper builds an index from each `<School>SpellSchoolAsset` prefab's
`SpellSchoolAbility` buffer, and a group the index does not name gets no row. The
consequence was recorded at cycle 2 close and became ROADMAP cycle 3 gap 3:

- 54 rows, 9 in each of the six spell schools;
- **weapon abilities produce NO row at all**, because there is no
  `<Weapon>SpellSchoolAsset` to source a school from;
- `abilities.school` declares `weapon` as a legal value and nothing on build
  `1.1.13.0-r99712` can source it.

So a coefficient table built on `abilities` could not carry a single weapon
ability, and weapon DPS is most of what a V Rising player asks about.

Cycle 3 phase 1 then measured the thing that dissolves the problem. Enumerating
every component on a weapon group and on three spell groups:

| Component | Present on | Carries |
|---|---|---|
| `ProjectM.WeaponAbilityData` | weapon groups only | `AbilityType` |
| `ProjectM.VBloodAbilityData` | spell groups | `AbilityType`, `AbilitySchool`, `AbilityTooltipType` |
| `ProjectM.AbilitySpellSchool` | spell groups | `SpellSchool`, `Tier` |
| `ProjectM.AbilityGroupStartAbilitiesBuffer` | BOTH | the chain head to the cast entity |

A weapon group and a spell group are told apart by a COMPONENT, not by a name and
not by a school. And the buffer that leads to the coefficients sits on both.

## Decision

**`ability_stats` is a new table keyed on the ability GROUP guid, selected by the
presence of `DynamicBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>`.**

`abilities` is left exactly as it is: the identity and school table, spell
schools only, joined on `prefab_guid`. Two tables, two key populations, one join
key.

Three consequences follow directly and are part of the decision:

1. **A coefficient row needs no school.** That is what makes weapon abilities
   addressable and what closes ROADMAP cycle 3 gap 3.
2. **The selector is the marker component, not the name.** Measured
   2026-08-01: 1818 entities carry the buffer, of which 1476 carry the
   `_AbilityGroup` name suffix and 341 do not (`_Group`, `_Abilitygroup`,
   `_UNUSED` and others). A name-shaped selector would have silently dropped
   341 real ability groups. This is the same rule the `blood_types` selector
   already follows: a marker component is a fact, a name prefix is a guess about
   Stunlock's conventions.
3. **A group that deals no damage still gets a row.** Cycle 2 measured 912 of
   1474 groups reaching no damage prefab and a second spawn hop adding exactly
   zero. Those groups are real abilities with real cast times, so they ship with
   every coefficient field OMITTED rather than zeroed. In this dump 732 of 1818
   reach damage.

## Consequences

**Good.**

- Weapon DPS becomes computable without inventing a weapon spell school.
- `ability_stats` carries a SECOND, independent school source:
  `VBloodAbilityData.AbilitySchool`, whose enum includes `Shadow`. The
  six-school `<School>SpellSchoolAsset` join cannot produce `Shadow`, and this
  dump finds exactly one row carrying it. Two sources that can be compared beat
  one that cannot.
- The join to items is direct: `items.ability_group_guids` holds the same key
  space, so weapon to ability to coefficient is two hops with no name matching.

**Costs, stated rather than discovered later.**

- The two tables disagree on population by design - 54 against 1818 - so a
  consumer joining them must treat a missing `abilities` row as "not a
  spell-school ability", never as "not found".
- `ability_stats.power_stat` is DECLARED AND NEVER EMITTED. Phase 1 proved it
  absent: no power-selector member exists across all 51 components on the `_Hit`
  entity, and `MainType` is the only discriminator present. Keying on the group
  does not solve that, and nothing in this ADR should be read as claiming it
  does.
- The 1476 groups carrying the `_AbilityGroup` suffix are two above cycle 2's
  1474. NOT RECONCILED, and recorded as unreconciled rather than smoothed over.

## Status

Accepted, 2026-08-01. Implemented in `bridge/src/RedMoon.Bridge/PrefabDumper.cs`
(`TryWriteAbilityStats`), `data/schemas/ability_stats.schema.json` and the count
pin in `tools/rmdata_ingest.py`. Measurements in `docs/BRIDGE_SPIKES.md`.

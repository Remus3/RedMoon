# ADR-006 - A recipe has many stations, so `station_guid` becomes `station_guids`

**Status:** Accepted, 2026-07-26
**Amends:** `data/schemas/recipes.schema.json`, which declared a singular
`station_guid` at `schema_version` 1.

## Context

`recipes.station_guid` was declared as one integer, "PrefabGUID of the required
crafting station". It has been OMITTED from every dump since the schema was
written, because the shape of the real data was unknown. It is now measured, and
the schema is wrong on both halves of the field.

**The link runs backwards.** Nothing on a recipe entity names a station.
`ProjectM.RecipeLinkBuffer` looked like the forward link and is not: MEASURED, 5
of 667 recipes carry it, 56 links total, and every link resolves to another
RECIPE - `Recipe_Ingredient_FakeGemDust` links 24 gem recipes. It is a
recipe-group alias. The real reference lives on the station:
**35 prefabs carry `ProjectM.WorkstationRecipesBuffer` holding 693 recipe
references, and 23 carry `ProjectM.RefinementstationRecipesBuffer` holding 249.**

**The link is one-to-many.** Those are 942 references over 663 recipes.
`TM_SpecialStation_PrisonCell` and `TM_SpecialStation_PrisonCell_StrongbladeDLC`
share all 14 of their recipes, and the crafting `User` prefab itself carries 29.
A single integer cannot hold that.

The tempting third option was to emit the first station encountered and move on.
It is barred by the same rule that retired the fabricated `items.tier`: a
first-station-wins value is INDISTINGUISHABLE from a measured one at the point of
consumption. Cycle 6 is a recipe and refinement economy solver, and a solver
handed one arbitrary station out of the three that can make an item does not
produce a slightly worse plan - it produces a confidently wrong one.

## Decision

1. `recipes` goes to **`schema_version` 2**. The singular `station_guid` is
   REPLACED by **`station_guids`, an array of integers**, sorted ascending.
2. The field is **optional, not required**. A recipe reachable from no station
   is real - `AlwaysUnlocked` player-crafted recipes exist - and an empty array
   is emitted for it rather than the field being dropped, so "no station" and
   "not measured" stay distinguishable at the row level. The per-dump evidence
   that the inversion ran at all is the census.
3. The inversion happens in the **dumper, not at ingest**. The dumper already
   holds the whole world and already makes a second pass to build the school
   index; the station index is the same shape of work. Ingest sees only the
   emitted tables and would have to be handed the station entities separately,
   which means shipping raw prefab data through the wire to rebuild a join the
   producer could already do.
4. Both buffers feed one index. A recipe reachable from a workstation and from a
   refinement station gets both guids, undifferentiated. The distinction between
   the two buffer TYPES is not carried: nothing in cycle 3 through 6 asks which
   kind of station a recipe sits at, and a field nobody consumes is a field that
   rots without anyone noticing.

## Consequences

- `station_guids` is writable and is emitted from this build forward. It is the
  last omitted `recipes` field, so `recipes` is now fully mapped.
- Any consumer written against the singular name breaks loudly at the schema
  gate rather than silently reading `None`. There is no such consumer today -
  the field has never carried a value.
- The 4 recipes that remain `unmapped` are unaffected; they fail on an empty item
  output buffer, before the station index is consulted.
- `blood_types` (`schema_version` 2) and `items.stats` (an array at
  `schema_version` 2) were amended on the same principle earlier in this cycle:
  the schema is a hypothesis about the game's data, and the game gets the vote.

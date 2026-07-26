# Bloodforge input spike - design

Cycle 3, first spec. Written 2026-07-26 against game build `1.1.13.0-r99712`.

## Why this spec exists and what it is not

Cycle 3 is Bloodforge core: combat math against V Blood bosses producing DPS,
EHP and time-to-kill. It cannot open by writing that math. Two of its declared
inputs do not exist on disk, and both were found at cycle 2 close by reading the
promoted ROWS rather than the schema:

1. **There is no boss stat line.** `vbloods` rows carry exactly `level`, `name`
   and `prefab_guid`. No health, no resistances, no damage. `docs/BLOODFORGE.md`
   named `tables/vbloods.json` as the source for "Boss stat line and
   resistances" from cycle 1 onward. That line was a design intention that was
   never checked against a real row, and it is false. Time-to-kill is the
   engine's headline output and its denominator is not on disk.
2. **There are no ability coefficients.** `abilities` rows carry `name`,
   `prefab_guid`, `school` and, for 16 of 54, `damage_type`. No cast time, no
   cooldown, no damage scalar.

A time-to-kill computed against an assumed boss health is the `items.tier`
fabrication with a larger blast radius, so this spec settles where those numbers
come from and nothing else.

**In scope:** sourcing the fields listed in section 2, by measurement against the
live bridge, plus the schema, gates and tests that carry them onto disk.

**Out of scope, explicitly:** any damage formula, the engine service on 8783,
`ENGINE_VERSION`, jewels, passives, the loadout ranker, and `items.tier`, which
is settled and does not reopen. The combat math is its own later spec, opened
against whatever this spike returns.

**The player side is not a gap** and was checked in the same pass that found the
two above: 203 of 205 weapon items carry real `PhysicalPower` or `SpellPower`
across 29 distinct stat types with an explicit `modification` on every entry.
The missing half is the TARGET side and the ABILITY side.

## 1. Shape and phases

**Phase 0 - the consumer contract, paper only.** Write the TTK and DPS skeleton
down, then derive the required field list from it. This exists so the field list
is deduced rather than guessed. It is the direct countermeasure to the cycle 2
lesson that cost the most: a real measurement can answer the RIGHT question about
the WRONG SUBJECT.

**Phase 1 - the exploratory `/dump/components` endpoint.** Throwaway, no schema,
no gates, never ingested. Prints full component-type lists and field values for
four subject classes. See section 3.

**GATE.** The operator reviews the component inventory. Real type and field names
are on paper before any schema is written. No phase 2 work starts before this.

**Phase 2 - the schema'd dump.** New `ability_stats` table, `vbloods` to
`schema_version` 2, `items` to `schema_version` 4, ingest gates, tests, ADR-007.
See section 4.

**Phase 3 - the negative control.** Prefab stat line against live instance, plus
a liveness assertion a stub cannot pass. See section 5.

**Alternatives rejected.** One continuous phase with no gate, because that is
precisely how a guessed component name becomes an ambiguous zero. And an offline
typedump-first approach, which yields true type names but says nothing about
which components a given entity actually carries.

## 2. Phase 0 - the consumer contract

```
TTK  = boss_effective_health / player_dps
boss_effective_health = max_health * mitigation(resist[damage_type])
player_dps = sum(hit_damage over rotation) / rotation_time
hit_damage = coefficient * power_stat * level_or_power_diff_term * (1 - resist)
```

V Rising applies a power-or-level-difference multiplier during damage
resolution. A TTK that omits it is wrong by a factor rather than a rounding
error, and no test can see that. It is therefore a required field, not an
enhancement.

### Required fields

| id | field | state before the spike |
|---|---|---|
| T1 | boss max health | unsourced |
| T2 | boss resistance per damage type | unsourced |
| T3 | boss unit level | HAVE, `ProjectM.UnitLevel.Level`, measured 16 to 91 |
| T4 | target-side input to the diff term | unsourced |
| A1 | ability cast time | unsourced |
| A2 | ability cooldown | unsourced |
| A3 | ability damage coefficient | unsourced |
| A4 | ability damage type | PARTIAL, 16 of 54 rows |
| A5 | which power stat the ability scales off | unsourced |
| A6 | hits per cast | unsourced |
| P1 | `PhysicalPower` / `SpellPower` on the weapon | HAVE, 203 of 205 |
| P2 | player-side input to the diff term | ROADMAP gap 5, computed over three level systems |
| L1 | weapon item to ability group | unsourced |
| L2 | ability group to coefficients | chain proven 1474 of 1474, payload unread |

The seven damage types T2 must cover are the ones cycle 2 measured on
`DealDamageParameters.MainType`: Physical, Spell, Fire, Holy, Silver, Garlic and
Corruption.

A6 is on the list because a multi-hit or multi-projectile cast makes DPS wrong by
an integer factor while every field reads plausibly. That is the `items.tier`
shape.

### Closure rule

At close, every row above carries exactly one of three states:

- **SOURCED** - the component and field are named in `docs/BRIDGE_SPIKES.md`.
- **PROVEN ABSENT** - declared and omitted, in the `items.tier` pattern, together
  with the negative control that makes the absence readable rather than
  ambiguous.
- **NOT ATTEMPTED.**

**The spike closes only when NOT ATTEMPTED is empty.** A required field may never
be defaulted to `1.0`, to `0`, or to a plausible guess.

## 3. Phase 1 - the measurement protocol

### The endpoint

`GET /dump/components`, taking either `guid`, or `name` as a prefix plus `limit`,
plus `instanced=1` to scan spawned entities instead of prefabs. For every matched
entity it prints:

- the entity index, `prefab_guid` and prefab name,
- the COMPLETE component-type list by full type name,
- every readable field of each blittable component, with type and value.

### The one hard rule

The endpoint never calls `HasComponent` on a name we hoped for. It enumerates the
entity's actual component types and prints all of them. A `HasComponent` that
returns false is evidence only when the type name was right, and at this stage we
have no way to know that. This is the same discipline that produced cycle 2's
usable measurements.

Readiness is gated on `GameDataInitialized`. Instanced scans skip
`Unity.Entities.Prefab`.

### Sampling discipline

Cycle 2's blood-types near miss came from sampling the first two rows, which were
`BloodType_VBlood` and `BloodType_GateBoss` - both unrepresentative, and the
result read as a family-wide absence. The spec therefore fixes minimum samples
rather than saying "a boss":

- at least three `CHAR_*_VBlood` prefabs spanning the level range: near 16, mid,
  and near 91,
- at least three ability groups across different schools, plus at least one
  weapon ability group,
- at least one live instanced boss entity,
- at least two weapon items from different weapon families, for the L1 hop.

### The L1 asymmetry, stated so it is not tripped over

`EquippableData.BuffGuid` is barred as a route to item STATS - `items.stats` is a
one-hop read off the item prefab and cycle 2 settled that. For ABILITIES the
equip buff is the correct hop. The rule is field-specific, not blanket.

### Host

Prefab subjects run on the dedicated server, which the agent launches itself:

```
VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver -saveName world1 -batchMode -nographics
```

Poll `http://127.0.0.1:8780/health` for `"ready":true`, roughly 9 seconds, before
dumping. This is like-for-like with the client because cycle 2 diffed client
against server row by row on `prefab_guid`, every field, all five tables, at zero
differing rows. Matching counts would have proved nothing; the diff is what
licenses either host.

The live-instance subject needs a world with the boss spawned. Try `world1` on
the dedicated server first. Only if that produces no instanced boss does the
operator get asked to launch the client, which binds 8777.

Never `Stop-Process`. Use `taskkill /F` through PowerShell.

### Output

Saved JSON under `_scratch\rmprobe`, which is scratch and not committed. Findings
land in `docs/BRIDGE_SPIKES.md` with the component and field named. No number is
ever read off a screenshot.

### Endpoint fate

The endpoint stays, marked exploratory, excluded from the ingest path and from
`/dump/prefabs`. Cycle 2 proved this class of question recurs; deleting the tool
means rebuilding it in cycle 4.

## 4. Phase 2 - the schema'd dump and its gates

### Schema changes

- **`vbloods` to `schema_version` 2.** Adds max health, a resistance map keyed by
  damage type, and the target-side diff-term field. Per the project Python
  convention, new dataclass fields append at the END with a default, because a
  mid-class required field breaks every existing positional construction and its
  tests.
- **`ability_stats`, new, `schema_version` 1.** Keyed on ability-group guid.
  Carries cast time, cooldown, coefficient, power stat, hits per cast and damage
  type. `abilities` remains the identity and school table and joins on
  `prefab_guid`. The key space is the ability GROUP because coefficients do not
  need a school; only the identity row does.
- **`items` to `schema_version` 4.** Adds an `ability_group_guids` ARRAY, which
  is the L1 link. This copies ADR-006's `station_guids` shape exactly:
  one-to-many, plural, and an empty list ships as `[]` so "grants no ability"
  stays distinguishable from "the join did not run".

### ADR-007

Records the load-bearing choice: **the coefficient key space is the ability
group, not the ability and not the school.** That is what dissolves ROADMAP cycle
3 gap 3, since a weapon ability needs no `<Weapon>SpellSchoolAsset` to have
coefficients, only a weapon-to-ability-group link. It belongs in the ADR record
where a future session looks before re-litigating it.

### Gates

- shallow schema in `core/tables.py`,
- nested per-table contract in `core/table_deep.py`,
- the `duplicate_key_problems` cross-row check on `ability_stats`, because more
  than one entity can carry the same `PrefabGUID`,
- **an explicit expected-count assertion on every table.** Cycle 2 lesson 4
  earned this: `vbloods` 66 survived four per-row gates because every duplicate
  pair was byte-identical and the only symptom was the count.

`ability_stats` has no expected count before the spike runs, so the rule is
stated precisely rather than left to interpretation: the count phase 1 measures
is PINNED as a constant in the same commit that lands the table, together with
the reference chain that produced it. The assertion then exists to catch drift
tomorrow, which is a different job from validating the dump today. A count that
is merely whatever the dumper emitted is not an assertion.

Absent stays absent. A proven-absent field is declared and omitted, never zero.

### Tests first

Failing characterization tests before the dumper changes, per the project TDD
rule. Including a regression test on the guard-order trap cycle 2 caught before
it shipped: the dedupe `Add` must sit AFTER the marker-component test, because
`&&` short-circuits left to right and an `Add` placed first claims the guid on
behalf of every entity carrying it, then rejects the real row when it arrives.
That turns a duplicate bug into a missing-row bug.

### No backfill pass

The project Data Fixes rule normally requires recovering already-corrupted rows
rather than only preventing future ones. It does not bind here, and the reason is
recorded so the exemption is not mistaken for an oversight: `data/rmdata/` is
gitignored and fully regenerable from one dump, so re-promoting IS the recovery.

## 5. Phase 3 - the negative control and acceptance

### The prefab-versus-instance control

Read the same fields from the `CHAR_*_VBlood` prefab and from the live instanced
entity of that same boss. All three outcomes are readable, which is the point:

- **They agree.** The prefab is authoritative and the dump stays repeatable.
- **They differ by a factor.** That factor is spawn scaling. It must be sourced
  before any TTK is published.
- **The prefab carries nothing and only the instance does.** The stat line is
  instance-only and TTK needs a live world. That is a finding, not a failure.

### The stub-proof assertion

`StateReader.cs` compiled at zero warnings, passed 284 tests and returned full
vitals while reading the PlayerCharacter PREFAB TEMPLATE. A green suite and a
clean build prove nothing for a live-data reader. So the live read must assert
something a template read cannot produce: the source entity does NOT carry
`Unity.Entities.Prefab`, and its entity index differs from the prefab entity's.
Structural, cheap, and a stub fails it.

### Acceptance - the spike closes only when all six hold

1. Every row of the section 2 table is SOURCED or PROVEN ABSENT. NOT ATTEMPTED is
   empty.
2. Full component inventories for all four subject classes are recorded in
   `docs/BRIDGE_SPIKES.md`, type and field named.
3. The prefab-versus-instance control has run and one of its three branches is
   named in writing.
4. Tables are promoted with counts asserted: `vbloods` 65, `items` 425,
   `ability_stats` at its measured count together with the chain that produced
   it.
5. `python -m pytest`, `python -m ruff check .`, `python tools/ascii_guard.py`
   and `dotnet build -c Release -t:Rebuild` on `bridge/src/RedMoon.Bridge` are
   all green, RE-RUN by the closing agent and not taken from a report.
6. ADR-007 is written, `docs/BLOODFORGE.md`'s input table is rewritten from the
   measurement, and ROADMAP cycle 3 gaps 1, 2 and 3 are each closed or restated
   with evidence.

### Named risks, with responses pre-decided

- **A coefficient may be a curve or a blob rather than a scalar.** Then the
  finding is its shape, recorded as such, and the math spec adapts to it. The
  spike does not flatten a curve into a number to make the schema fit.
- **`ability_stats` will contain groups that never deal damage.** Cycle 2
  measured 912 of 1474 groups reaching no damage prefab, and that a second spawn
  hop adds exactly zero, so one hop is the answer and those groups genuinely do
  not reach damage. They ship with coefficients OMITTED, not zero.
- **The diff term may live in system code rather than in data.** Then it is
  PROVEN ABSENT from data and the math spec must measure it empirically. Naming
  the fallback now stops a future session from treating the absence as an open
  question.

### Process guard

A worktree-isolated agent has twice written into the MAIN tree while
`git worktree list` showed no second tree. Therefore: no commit while an agent is
live, `git show --stat` read after every agent, and every count or build an agent
claims re-run independently.

## Inputs already on disk, from cycle 2

Under `data/rmdata/1.1.13.0-r99712/tables/`, gitignored and regenerable:

| table | rows | schema_version |
|---|---|---|
| `items` | 425 | 3 |
| `recipes` | 663 | 2 |
| `abilities` | 54 | 1 |
| `vbloods` | 65 | 1 |
| `blood_types` | 13 | 2 |

## Deliverables

1. `/dump/components` in `bridge/src/RedMoon.Bridge/`, exploratory, carrying no
   schema and no ingest gates, never promoted. It still waits on the
   `GameDataInitialized` readiness gate, which is a precondition for reading
   anything at all rather than a validation of what was read.
2. Component inventories for all four subject classes in
   `docs/BRIDGE_SPIKES.md`.
3. `vbloods` `schema_version` 2, `ability_stats` `schema_version` 1, `items`
   `schema_version` 4, with shallow and nested contracts and count assertions.
4. `docs/adr/ADR-007`.
5. A rewritten input table in `docs/BLOODFORGE.md`, sourced from measurement.
6. A ledger entry in `docs/LEDGER.md`.

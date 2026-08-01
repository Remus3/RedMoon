# The Bloodforge combat math

Design spec. Drafted 2026-08-01. Status: PROPOSED.

The second cycle 3 document. It opens because gap 7 is SETTLED
(`docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md`) and
because the embargo it mandated is now CODE rather than intention - commit
`6d5095e` landed `bloodforge/embargo.py`, `bloodforge/__init__.py` and
`data/schemas/anchor.schema.json` with 23 tests, BEFORE a line of math was
written. That ordering is the only reason this document is safe to write: every
quantity specified below is unpublishable by construction until an anchor run
lifts it.

## 0. What this spec settles

SETTLED HERE: the per-application damage model term by term (section 2), which
power stat a coefficient multiplies and the single experiment in the corpus that
can decide it (section 3), the DPS definition and its denominator (section 4),
EHP (section 5), TTK (section 6), and what is computable versus merely declared
(section 7).

NOT SETTLED HERE: no number is validated. C.1, C.2 and C.3 of the falsification
spec are the gates and no anchor run exists. This spec builds the thing the
gates will be pointed at.

**Six previously recorded facts are CORRECTED in section 1 by counting.** Every
one was found by reading the promoted rows rather than the prose describing
them, which is the third time that discipline has moved a number in this project
(`ability_stats` 1474 -> 1818, the link corpus 119 -> 146,
`vblood_damage_modifier` range -> binary).

## 1. Ground truth, measured this session

Counted over `data/rmdata/1.1.13.0-r99712/tables/`, 1818 `ability_stats` rows,
425 `items` rows, 65 `vbloods` rows.

### 1.1 The damage block is ALL-OR-NOTHING, and six records are corrected

**MEASURED: 732 of 1818 rows carry a damage block, and every one of the 732
carries `coefficient`. Zero damage rows omit it.**

| Prior statement | Where | Corrected reading |
|---|---|---|
| "154 edges reach a damage group whose coefficient is OMITTED" | session brief fact 8 | The EDGE counts are exactly right - 563 edges, 409 to a damage group, 154 not. But the 154 reach groups with **NO DAMAGE BLOCK AT ALL**, not a damage row missing one field. The block is all-or-nothing: a group that reaches no `_Hit` prefab omits `coefficient`, `raw_damage_value`, `raw_damage_percent`, `damage_type`, `hits_per_cast` and the rest together. |
| "`AB_Vampire_Longbow_Primary_AbilityGroup` has its coefficient OMITTED" | session brief fact 9 | The ROW EXISTS and carries `cast_time` 5, `cooldown` 0.55, `post_cast_time` 0.25, `spawn_prefabs_on_cast` **8**, `is_weapon_ability` **false**, and no damage block whatever. The consumer trap the fact describes is real and unchanged - `AB_Spear_AThousandSpears_Stab_AbilityGroup` carries `coefficient` a genuine **0.0** - but the two rows differ by a whole block, not by one field. |
| "`is_weapon_ability` is true on 42 of 1818, 26 of which reach damage" | session brief fact 8 | 42 is right. **18 of them reach damage, not 26**, counted over the linked set. |
| "the fire rating varies across the 65 and is the one RM cannot price" | ROADMAP gap 8 | Correct, and now quantified on the other side: **15 of 732 damage groups deal `fire`**, and only 4 of 65 bosses carry a non-zero rating. |
| "27 ability groups deal holy damage and NO boss carries any holy field" | session brief fact 9 | CONFIRMED exactly: 27 holy. |
| "abilities with `hits_per_cast` up to 4 exist" | falsification spec A.4 | CONFIRMED: range 1 to 4, 4 distinct values, no zeros. |

### 1.2 `damage_type` over the 732 damage groups

| type | groups | boss-side resistance field | priceable |
|---|---|---|---|
| physical | 579 | `UnitStats.PhysicalResistance`, reads **0 on all 65** | YES, at zero reduction |
| spell | 93 | `UnitStats.SpellResistance`, reads **0 on all 65** | YES, at zero reduction |
| holy | 27 | **NONE. Proven absent across 150 enumerated components** | **NO** |
| corruption | 18 | `UnitStats.CorruptionDamageReduction`, **0.5 on all 65** | YES, at 0.5 |
| fire | 15 | integer RATING, 0 on 61 bosses, 50/50/70/75 on 4 | **NO - ROADMAP gap 8** |

**42 of 732 damage groups (holy and fire) cannot be priced against any boss on
this build.** They are OMITTED from computation, never computed at a zero
reduction. A zero reduction is a real and different claim.

### 1.3 FOUR damage-block terms are effectively constant

This is the `vblood_damage_modifier` shape again, four more times. Each is
correct-looking everywhere it is exercised, and each hides a small population
where it is not.

| Term | Distribution over 732 | Verdict |
|---|---|---|
| `hit_triggers` | **0 on all 732**, one distinct value | Carries NO information on this build. Must not enter the math. |
| `multiply_main_factor_with_stacks` | **false on all 732** | Same. |
| `raw_damage_value` | 0 on 731, `0.01` on exactly 1 (`AB_Charm_AbilityGroup`) | Implement; near-inert. |
| `raw_damage_percent` | 0 on 731, `0.3` on exactly 1 (`AB_Shapeshift_Golem_T02_Group`) | Implement; near-inert. |
| `damage_modifier_per_hit` | 0 on 729, nonzero on **3**: `AB_Prog_Boomerang_Group` -0.2, `AB_Frost_CrystalLance_AbilityGroup` +0.5, `AB_Illusion_WraithSpear_AbilityGroup` -0.25 | Implement; see 2.4. |
| `vblood_damage_modifier` | 1.0 on 728, 0.33 on 4 | As already recorded. |

The golem story is now coherent across three fields: `AB_Shapeshift_Golem_T02_
Group` has `coefficient` **0**, `raw_damage_percent` **0.3**, and its siblings
carry `vblood_damage_modifier` 0.33. Golem damage is percent-of-pool, not
coefficient-scaled. A model that reads only `coefficient` prices every golem
ability at exactly zero.

### 1.4 NEW - `ability_type` is NOT a slot discriminator

**MEASURED cross-tab over all 1818 rows:**

| `is_weapon_ability` | `ability_type` | rows |
|---|---|---|
| false | absent | 1714 |
| **true** | **`Secondary`** | **36** |
| false | `SpellSlot1` | 25 |
| false | `Ultimate` | 18 |
| false | `SpellSlot2` | 12 |
| false | `Travel` | 7 |
| true | `None` (the string) | 6 |

**Not one weapon group reports `Primary`.** All 36 weapon groups that carry an
`ability_type` report `Secondary`, including
`AB_Vampire_Whip_Primary_AbilityGroup`,
`AB_Vampire_GreatSword_Primary_Moving_AbilityGroup` and every other primary
attack. A consumer filtering `ability_type == "Primary"` gets **zero rows** and
will read that as "no primaries found" rather than as "this field does not mean
what its enum implies".

The `ability_stats` schema line 10 lists Primary first among the enum members.
That is the DECLARED enum, faithfully copied, and it is not what the data
contains. Proposed as **ROADMAP gap 11**. Slot must be derived from the
weapon-to-group link, never from this field.

### 1.5 NEW - 154 of 563 weapon links reach nothing, and the longbow is one

The 15 distinct linked groups with no damage block, by edge count:

```
15  AB_Vampire_Sword_Whirlwind_Spin_AbilityGroup       spawns_on_cast=1
14  AB_Longbow_MultiShot_AbilityGroup                  spawns_on_cast=1
14  AB_Vampire_Longbow_Primary_AbilityGroup            spawns_on_cast=8  cast=5
14  AB_Vampire_Slashers_Camouflage_Main_AbilityGroup   spawns_on_cast=1
12  AB_Pistols_ExplosiveShot_AbilityGroup              spawns_on_cast=absent
12  AB_Pistols_FanTheHammer_AbilityGroup               spawns_on_cast=2
12  AB_Vampire_TwinBlades_SweepingStrike_AbilityGroup  spawns_on_cast=1
12  AB_Vampire_Daggers_RainOfDaggers_Group             spawns_on_cast=1
12  AB_Vampire_Daggers_CallDaggers_AbilityGroup        spawns_on_cast=1
12  AB_GreatSword_LeapAttack_AbilityGroup              spawns_on_cast=1
12  AB_GreatSword_GreatCleaver_AbilityGroup            spawns_on_cast=1
 9  AB_Vampire_Claws_SkeweringLeap_AbilityGroup        spawns_on_cast=1
 2  AB_Vampire_Claws_SkeweringLeap_Unholy_AbilityGroup spawns_on_cast=1
 1  AB_Fishing_AbilityGroup                            spawns_on_cast=1
 1  AB_Fishing_AbilityGroup_Debug                      spawns_on_cast=1
```

Two consequences, both load-bearing.

1. **The default weapon can be priced on its primary only.** The section E.1
   default is `Item_Weapon_GreatSword_Legendary_T08`, which carries 3 ability
   group links. One reaches damage (`AB_Vampire_GreatSword_Primary_Moving_
   AbilityGroup`, `coefficient` 0.7, `hits_per_cast` 3). The other two -
   LeapAttack and GreatCleaver - reach nothing. **Two thirds of the default
   weapon's kit is unpriceable**, so any GreatSword DPS is a primary-only DPS
   and must say so.
2. **The longbow is the sharpest case and is probably not a data absence.** It
   declares `spawn_prefabs_on_cast` **8** and `cast_time` 5 - a draw, not a
   swing - and reaches no `_Hit` prefab in one hop. ADR-007 records that a
   SECOND spawn hop added exactly zero across the corpus, which was measured and
   is not in doubt; what it means here is that the longbow's damage lives
   somewhere the one-hop chain does not reach at all, most likely on a projectile
   entity spawned at cast. Proposed as **ROADMAP gap 10**.

`AB_Pistols_ExplosiveShot_AbilityGroup` additionally has `spawn_prefabs_on_cast`
ABSENT, not zero, meaning the cast hop itself did not resolve a buffer. It is
the only one of the 15 in that state and is worth a look on its own.

## 2. The damage model

For one application of ability group `G` against target `T`. Every term names
its source field and its status.

### 2.1 The equation

```
  base(G)       = coefficient(G) * P(G)                       [P is section 3]
                + raw_damage_value(G)
                + raw_damage_percent(G) * pool(T)             [pool UNSOURCED]

  per_hit(G,i)  = base(G) * (1 + damage_modifier_per_hit(G) * (i - 1))
                                                              [i = 1..hits, 2.4]

  cast(G)       = sum over i of per_hit(G,i)

  vs_class(G,T) = cast(G) * vblood_damage_modifier(G)          [T a V Blood]

  applied(G,T)  = vs_class(G,T) * (1 - reduction(T, damage_type(G)))
```

`applied` is the quantity the falsification spec's C.1 gate compares against an
isolated `Health.Value` delta at 2 percent median APE.

### 2.2 `reduction(T, type)` is defined on three of five types

```
  physical    -> UnitStats.PhysicalResistance   = 0.0 on all 65   -> 0.0
  spell       -> UnitStats.SpellResistance      = 0.0 on all 65   -> 0.0
  corruption  -> UnitStats.CorruptionDamageReduction = 0.5 on all 65 -> 0.5
  fire        -> UNDEFINED. ROADMAP gap 8.
  holy        -> UNDEFINED. No unit-side field exists.
```

**`reduction` is a partial function and callers must handle undefined, not
default it.** The four values are NOT commensurable and must never be averaged:
two are float resistances, one is an integer rating, one is already a reduction.
An ability whose `damage_type` has no defined reduction produces NO NUMBER. Its
`applied` is absent, exactly as `ttk_seconds` is absent - the same idiom one
level down.

That withholds 42 of 732 damage groups. It also means the fire rating being
unpriceable (gap 8) is not a rounding issue: it removes the only resistance that
actually varies across the 65 bosses, so on this build **every priceable boss
differs from every other only by level-derived power and by health**.

### 2.3 `pool(T)` for `raw_damage_percent` is UNSOURCED

`raw_damage_percent` is a fraction of a pool and nothing on disk says which pool
- current health, max health, or the caster's. It is nonzero on exactly one row.
**DECLARED AND NEVER EMITTED**: an ability with a nonzero `raw_damage_percent`
produces no number until the pool is identified. Settling measurement in
section 8.

### 2.4 `damage_modifier_per_hit` - the ramp form is UNVERIFIED

The linear ramp above is a HYPOTHESIS, not a reading. The field is a per-hit
modifier on a multi-hit buffer and the schema records only that phase 1 named it
"alongside `MultiplyMainFactorWithStacks` as the two fields that exist for
repeated hits". Three plausible forms fit the name: linear ramp, geometric, or a
flat modifier applied to hits after the first.

It is nonzero on 3 rows. **All three have `hits_per_cast` 1** - verified while
writing this - so on this build **the form is unobservable and the term is
identically zero in every computation.** Implement the linear form, gate it
behind a regression test pinned to those three rows, and record that the choice
is arbitrary and untested. If a future build gives a multi-hit ability a nonzero
modifier, the test is what will fail.

### 2.5 What is deliberately NOT in the model

- `hit_triggers` and `multiply_main_factor_with_stacks`: constant on all 732
  rows, so they cannot inform anything.
- Crit. `SpellCriticalStrikeChance` appears on exactly 1 of 205 weapons and no
  crit multiplier is sourced. NOT ATTEMPTED.
- Blood bonuses. All 13 `blood_types` rows carry stat NAMES with
  `value_source: blood_quality_scaled_at_runtime` and no magnitudes.
  DECLARED AND OMITTED.
- Jewels, passives, gear-set bonuses. No source measured.
- The other 22 `EntityTypeModifiers`. Real and readable by the same hop; no
  cycle 3 consumer reads them.

## 3. `P(G)` - the power stat, and the ONE experiment that can decide it

`power_stat` is PROVEN ABSENT from the data: no power-selector member exists
across all 51 components on the `_Hit` entity, and `MainType` is the only
discriminator present. The schema forbids inferring it: "A consumer must not
read `damage_type` as a power selector without evidence the combat-math spec has
not yet produced."

### 3.1 The two hypotheses

- **H1, `damage_type` selects.** `MainType == Physical` multiplies
  `UnitStats.PhysicalPower`; `Spell` multiplies `SpellPower`.
- **H2, the ability's KIND selects.** A weapon ability multiplies
  `PhysicalPower`; a spell-school ability multiplies `SpellPower`, regardless of
  `MainType`.

### 3.2 The default subject vector CANNOT distinguish them

This is the finding that most changes what happens next, and it invalidates the
obvious plan.

**MEASURED over the 32 distinct weapon-linked damage groups: 31 are
`damage_type` physical and 1 is spell.** And over 205 weapons, `PhysicalPower
AddToBase` appears on 203 while `SpellPower Add` appears on exactly 1.

So for every weapon ability a player will realistically use, H1 and H2 predict
**the same number**. A per-hit gate run against the section E.1 default -
GreatSword primary versus Dracula - passes at 2 percent under both hypotheses
and decides nothing. The one weapon ability with `damage_type` spell,
`AB_Spear_AThousandSpears_Stab_AbilityGroup`, has `coefficient` **0.0**, so it
scales with no power stat at all and cannot discriminate either.

**MEASURED: zero rows in the corpus are `is_weapon_ability` true with a
non-physical `damage_type` and a nonzero coefficient.** The weapon side is a
dead end by exhaustion, not by sampling.

### 3.3 The discriminator - there is exactly one in 1818 rows

Searching the other direction - a SPELL-school ability whose `damage_type` is
physical - returns **exactly one row**:

```
name         AB_Unholy_WardOfTheDamned_AbilityGroup
prefab_guid  -1136860480
spell_school unholy          <- H2 predicts SpellPower
damage_type  physical        <- H1 predicts PhysicalPower
coefficient  1.0
hits_per_cast 1
cast_time 0.1   post_cast_time 0.2   cooldown 11   global_cooldown 0
raw_damage_value 0   raw_damage_percent 0   damage_modifier_per_hit 0
vblood_damage_modifier 1.0   ability_type SpellSlot2
```

It is close to a designed experiment:

- `coefficient` is exactly **1.0** and `hits_per_cast` is **1**, so the
  prediction is not "some arithmetic on a power stat" but literally **"the
  observed health delta equals one of the two power stats"**. There is no
  coefficient multiplication to get wrong and no multi-hit window to alias.
- Every near-inert term is at its inert value, so nothing else can move the
  number.
- `damage_type` physical means `reduction` is 0.0 and DEFINED, so the boss side
  contributes nothing either.
- It is `SpellSlot2`, so it is player-castable and appears on the ability bar.
- The two predictions are far apart on any real loadout, because the default
  weapon grants `PhysicalPower AddToBase` and grants no `SpellPower` at all.

**The anchor protocol's first run must therefore have TWO subjects, and this is
a change to the falsification spec's section E:**

| Role | Subject | Purpose |
|---|---|---|
| Ranking default | GreatSword T08 vs Dracula, Normal | The published default, section E.1, unchanged |
| **Power-stat experiment** | **`AB_Unholy_WardOfTheDamned_AbilityGroup` cast at any valid target** | The ONLY subject in the corpus that separates H1 from H2 |

The experiment does not need Dracula, does not need a V Blood, and does not need
a health denominator. It needs one isolated hit and the player's live
`UnitStats.PhysicalPower` and `SpellPower` from the same tick - both already
read by `StateReader`. **It can be run before any boss is spawned.** That makes
it the cheapest run in the protocol and it should be the first one taken.

### 3.4 Until the experiment runs

`P(G)` is UNDEFINED and every downstream quantity is absent. This is not a
degraded mode bolted on; it is the embargo already in `bloodforge/embargo.py`
doing exactly what it was built for one commit earlier.

Caveat stated plainly: one row is a sample of one. A pass tells us which
hypothesis survives on `AB_Unholy_WardOfTheDamned_AbilityGroup` and does not
prove the rule holds corpus-wide. It is the only evidence the build affords, and
that limit belongs in the ledger entry, not in a footnote nobody reads.

## 4. DPS

### 4.1 Two quantities, never conflated

```
  ability_dps(G,T) = applied(G,T) / cycle(G)

  cycle(G) = max( cast_time(G) + post_cast_time(G),
                  cooldown(G),
                  global_cooldown(G) )
```

`cycle` is a MAXIMUM rather than a sum because the three windows overlap: a
cooldown runs during the cast, not after it. Adding them would understate DPS on
every cooldown ability. MEASURED coverage: `cast_time` on 1815 rows,
`post_cast_time` on 1815, `cooldown` on 1818, `global_cooldown` on 1691. A row
missing `cast_time` (3 rows) has an undefined cycle and produces no DPS.

`cooldown` is 0 on 352 of 1818 rows, which is what makes the max-form necessary:
a primary attack with cooldown 0 gets its cycle from cast plus recovery.

### 4.2 Rotation DPS is NOT ATTEMPTED

A loadout's real DPS requires an ability ORDERING, and nothing on disk supplies
one. `AbilityGroupInfo.MinRange` and `MaxRange` exist and are not modelled;
positioning, weaving and cooldown alignment have no source at all. Rotation DPS
would be a model of a player, presented as a property of a weapon.

What Bloodforge publishes instead, after lift: `ability_dps` per group, and the
weapon's **primary-only sustained DPS**, labelled as such. Section 1.5 makes
that labelling non-negotiable - for the default weapon it is one ability of
three.

## 5. EHP

```
  ehp(player) = Health.MaxHealth._Value / (1 - reduction(player, type))
```

Read live; no prefab source is needed or exists. It is per damage type and
inherits section 2.2's partiality exactly: an EHP against holy or fire is
UNDEFINED, not infinite and not equal to raw health. A single scalar EHP would
have to average across damage types, which is the averaging prohibition again.

Published after lift as a MAP of damage type to value, over the three defined
types only, never as one number.

## 6. TTK

```
  ttk_seconds(loadout,T) = max_health(T) / effective_dps(loadout,T)
```

Every term is blocked and the blocks are independent:

- `max_health(T)` is INSTANCE-ONLY. 0 on all 65 prefabs, 8107 on the one live
  Dracula instance measured. Not spawn scaling - 0 to 8107 is not a ratio - so
  no factor exists to recover it offline. It comes from an anchor run and from
  nowhere else, and it must be scaled by the difficulty `MaxHealthModifier`
  recorded verbatim in the run manifest (ROADMAP gap 9).
- `effective_dps` needs `P(G)` from section 3 and a rotation from section 4.2,
  which is not attempted.

So TTK's lift condition in `bloodforge/embargo.py` - the per-hit gate AND the
TTK gate AND three comparable runs - is not conservatism. Two of its three
inputs do not exist yet.

## 7. What is computable TODAY, behind the embargo

Stated so the next session does not have to re-derive it.

| Quantity | Status |
|---|---|
| `applied(G,T)` for physical and spell groups | COMPUTABLE once `P(G)` is decided by the section 3.3 experiment |
| `applied` for CORRUPTION groups | **NOT COMPUTABLE, and this line is CORRECTED 2026-08-01.** See 7.1. |
| `applied` for holy and fire groups | **NOT COMPUTABLE.** 42 of 732 groups. Gap 8 and a proven-absent field. |
| `ability_dps(G,T)` | COMPUTABLE with `applied`, using the 4.1 max-form cycle |
| Weapon primary-only sustained DPS | COMPUTABLE for the 32 linked damage groups; NOT for the 15 that reach nothing |
| Rotation DPS | NOT ATTEMPTED, no source |
| `ehp` per damage type | COMPUTABLE from live player state, three types only |
| `ttk_seconds` | BLOCKED on the instance-only denominator AND on rotation |

### 7.1 CORRECTION - corruption is blocked on the POWER side, not the resistance side

This document shipped corruption as computable-after-the-experiment. It is not,
and the error is instructive: the withholding was reasoned about entirely on the
`reduction` side, where corruption is the one damage type with a real, defined,
nonzero value.

COUNTED over all 1818 rows while implementing section 2:

```
corruption damage groups                              18
  of which carry a spell_school                        0
  of which are is_weapon_ability                       0
  of which carry NEITHER                              18
```

All 18 are NPC abilities. **H2 has no ability kind to select on for any of them,
and H1 is stated over `Physical` and `Spell` MainType only and so says nothing
about a corruption MainType either.** Running the section 3.3 experiment
therefore leaves every corruption group unpriced under EITHER outcome. The
experiment cannot decide a question it was never posed.

Two consequences:

1. **60 of 732 damage groups are unpriceable after the experiment, not 42.**
   27 holy and 15 fire on the reduction side, and 18 corruption on the power
   side. Section 2.2's "that withholds 42 of 732" counts the reduction side only
   and is correct as far as it goes.
2. **`corruption` 0.5 is the only nonzero defined reduction on this build and
   NOTHING REAL REACHES IT.** Its arithmetic is exercised in
   `tests/test_damage.py` on a synthetic row only, with a separate test
   asserting that no genuine row exercises it. That is the honest state: the
   code path exists, is tested, and is dead on this data.

This is the `hit_triggers` shape one level up. A term can be present, correct,
well-typed and completely inert, and the only way to find out is to count the
rows that reach it rather than read the field that declares it.

`ENGINE_VERSION` is `0.1.0+1.1.13.0-r99712`, created in commit `6d5095e`. It
did not exist in code while ROADMAP and `docs/BLOODFORGE.md` both described it as
pinned. Bump the semver when anything in section 2, 3 or 4 changes; the build
half re-arms the embargo automatically on a game bump.

## 8. Open questions, each with the measurement that settles it

1. **Which power stat does a coefficient multiply?** THE question. SETTLED BY
   the section 3.3 run: cast `AB_Unholy_WardOfTheDamned_AbilityGroup`, record
   one isolated delta and the player's live `PhysicalPower` and `SpellPower`.
   Cheapest run in the protocol, needs no boss.
2. **Which pool does `raw_damage_percent` fraction?** SETTLED BY recording one
   `AB_Shapeshift_Golem_T02_Group` application against two targets of different
   max health and checking whether the delta scales with the target's pool.
3. **What is `ResistanceData.FireResistance_DamageReductionPerRating`?**
   ROADMAP gap 8, unchanged. SETTLED BY a typed read of the global component.
   Until then 15 damage groups and the only varying boss resistance are unpriced.
4. **Where does the longbow's damage live?** Proposed gap 10. SETTLED BY
   enumerating the 8 prefabs in `AB_Vampire_Longbow_Primary_AbilityGroup`'s
   `AbilitySpawnPrefabOnCast` buffer and checking each for a
   `DealDamageOnGameplayEvent`.
5. **Is `ability_type` really `Secondary` on every weapon primary?** Proposed
   gap 11. The cross-tab is unambiguous on this build; what is UNVERIFIED is
   whether the dumper reads the right member. SETTLED BY reading
   `WeaponAbilityData` on one known primary and one known secondary and
   comparing.
6. **What form does `damage_modifier_per_hit` take?** Unobservable on this
   build: all three nonzero rows have `hits_per_cast` 1. Section 2.4 picks the
   linear form arbitrarily and pins it. SETTLED BY a future build, or by an
   in-game observation of one of the three.
7. **Is 8107 stable across spawns, and under what difficulty was it measured?**
   Inherited from the falsification spec, unchanged and still open.

## 9. How this spec closes

DISCHARGED when sections 2 through 6 are implemented in `bloodforge/`, the
section 3.3 experiment has been run and recorded, and the C.1 gate has been
evaluated against it - including a FAIL, if that is what happens. The embargo
means none of that work can publish a wrong number in the meantime, which is the
entire reason it was built first.

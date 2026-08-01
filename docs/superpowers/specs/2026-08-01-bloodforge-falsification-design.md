# Gap 7 - the falsification protocol for Bloodforge output

Design spec. Drafted 2026-08-01. Status: PROPOSED.

**Decision A is OPERATOR-RULED**, 2026-08-01: Red Moon builds the bridge-side
boss `Health.Value` time series (route A1), not a hand-timed recording. The
remaining decisions B through E are proposed and await acceptance.

**One constraint was CORRECTED against this spec's own source brief** before it
landed - `vblood_damage_modifier` is binary, not a range. See 1.1 constraint 4.
The correction was produced by counting the promoted rows rather than by
re-reading the prose that stated it, which is the same discipline that turned
`ability_stats` 1474 into 1818 and the link corpus 119 into 146.

Settles ROADMAP cycle 3 gap 7 (`ROADMAP.md:165-174`) and the default-subject
vector item (`BACKLOG.md:34-43`), which the operator has tied together. Both
must be settled before the combat-math spec opens (`ROADMAP.md:115-116`,
`docs/BLOODFORGE.md:41-43`).

## 0. What this spec settles, and what it deliberately does not

Gap 7 is not "the model is wrong". It is "nothing can tell us if it is"
(`ROADMAP.md:165-168`). All six acceptance criteria of the input spike
(`docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md:279-295`)
are about SOURCING inputs, so all six can pass while every published TTK is
wrong by a factor.

SETTLED HERE: what gets recorded (A), how a run is identified (B), what counts
as agreement (C), what may be published before an anchor exists (D), and what
the default target is (E).

NOT SETTLED HERE, and deliberately: no anchor is produced. A real recorded kill
against a live spawned boss still has to happen. This spec is the protocol that
run must follow, written before the run so the run cannot be rationalised
afterwards.

ALSO NOT SETTLED HERE: the combat math itself. This spec must not contain a
damage formula, because a formula written by the same pass that writes its own
acceptance test is not falsified by it.

## 1. Ground truth this spec is built on

Every line below is a citation, not a recollection.

### 1.1 The four constraints that silently produce a wrong number

1. **Boss `max_health` is instance-only.** 19 typed fields compared between the
   Dracula prefab (entity 29012) and its live instance (322945): 17 identical,
   `Health.MaxHealth` 0 against 8107 (`docs/BRIDGE_SPIKES.md:1386-1405`). NOT
   spawn scaling: 0 to 8107 is not a ratio, so there is no factor to recover
   (`docs/BRIDGE_SPIKES.md:1401-1405`). `vbloods.max_health` is DECLARED AND
   NEVER EMITTED (`data/schemas/vbloods.schema.json`, `max_health` description).
   Verified on disk: all 65 rows carry `level`, `name`, `prefab_guid`,
   `physical_power`, `spell_power`, `resistances`, and no `max_health` key.
   **A TTK denominator needs a live world with the boss spawned.**
2. **The four resistances are not commensurable.**
   `UnitStats.PhysicalResistance` and `.SpellResistance` are `ModifiableFloat`
   reading 0 on all 65; `.FireResistance` is a `ModifiableINT` RATING that
   becomes a reduction only through the GLOBAL
   `ResistanceData.FireResistance_DamageReductionPerRating`;
   `.CorruptionDamageReduction` is already a reduction at 0.5 on all 65
   (`docs/BRIDGE_SPIKES.md:1348-1373`, `docs/BLOODFORGE.md:31`). Holy, Silver,
   Garlic and Sun have NO unit-side field across a full enumeration of 150
   components on three bosses (`docs/BRIDGE_SPIKES.md:950-954`) and are OMITTED,
   never zeroed. **Do not average them.** Counted on disk for this spec: exactly
   4 of the 65 rows carry a non-zero `fire` rating -
   `CHAR_Undead_Infiltrator_VBlood` 50 (level 50),
   `CHAR_Gloomrot_Purifier_VBlood` 50 (level 61), `CHAR_VHunter_CastleMan` 70
   (level 80), `CHAR_Gloomrot_Monster_VBlood` 75 (level 88). The other 61 read
   0. So the fire path is exercised by 4 subjects and by nothing else.
3. **`power_stat` is PROVEN ABSENT.** No power-selector member across all 51
   components on the `_Hit` entity; `MainType` is the only discriminator
   (`docs/BRIDGE_SPIKES.md:1066`, ADR-007 lines 82-86). The spike spec
   pre-decided the fallback: proven absent FROM DATA means the math spec
   establishes it EMPIRICALLY
   (`docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md:307-310`).
   The schema says it outright: "A consumer must not read `damage_type` as a
   power selector without evidence the combat-math spec has not yet produced"
   (`data/schemas/ability_stats.schema.json`, `power_stat` description).
4. **`vblood_damage_modifier` is BINARY, not a range - CORRECTED 2026-08-01 by
   counting.** Every prior statement of this constraint, including
   `docs/BLOODFORGE.md:27` and the session brief that opened this spec, says it
   "ranges 0.33 to 1.0 over the 732 damage rows" and that omitting it
   "misstates every boss TTK by up to 3x". Both readings are wrong, and the
   error is the familiar one: a min and a max were reported as if they described
   a spread. MEASURED over `tables/ability_stats.json`: the field takes exactly
   TWO distinct values - **1.0 on 728 of 732 rows and 0.33 on exactly 4**. All
   four are golem-form NPC abilities: `AB_Shapeshift_Golem_T02_GroundSlam_Group`,
   `AB_Shapeshift_Golem_T02_Ranged_AbilityGroup`,
   `AB_Shapesfhit_Golem_T02_MeleeAttack_Group` and
   `AB_GoldGolem_Enrage_FistSlam_AbilityGroup`. It is 1.0 on all 409
   weapon-linked damage rows, so it is INERT for loadout coaching.

   **The correction makes the term more dangerous, not less.** Because it is
   1.0 almost everywhere, a bug that drops it is invisible in 99.5 percent of
   cases and silently triples exactly the golem builds. That is the
   `core/table_deep.py` shape - correct-looking everywhere it is exercised - and
   it is why C.1 below must not lean on this term as a headline error source.

   Incidental, and it corroborates ADR-007's marker-component rule with a fresh
   instance: one of the four is spelled `AB_Shapesfhit_...` in Stunlock's own
   data. A name-shaped selector would drop it silently.

Consequence for this spec: constraint 3 is the reason the anchor must measure
PER-HIT damage and not only a kill duration. A kill duration cannot distinguish
a wrong power-stat selection from a wrong uptime assumption. See C.

### 1.2 What the bridge already reads

- `ComponentDumper.WriteStatValues` reads `Health.MaxHealth._Value`,
  `Health.Value` and `Health.MaxRecoveryHealth` with typed accessors on EVERY
  entity carrying the queried guid, prefab and instance alike
  (`bridge/src/RedMoon.Bridge/ComponentDumper.cs:568-573`). It is served at
  `GET /dump/statcontrol?guid=<n>` (`bridge/src/RedMoon.Bridge/BridgeServer.cs:405-421`).
- `StateReader` already reads player `Health.Value`, `max_health`, `blood`,
  `max_blood`, quality and blood type on the live character
  (`bridge/src/RedMoon.Bridge/StateReader.cs:407-441`).
- Every ECS read happens on one main-thread tick
  (`bridge/src/RedMoon.Bridge/BridgeServer.cs:262-274`), driven every 15 frames
  (`bridge/src/RedMoon.Bridge/Plugin.cs:41`), which is about 4 Hz at 60 fps.
- A full entity scan is MEASURED at 95 ms in the client world
  (`bridge/src/RedMoon.Bridge/StateReader.cs:34-38`), which is why the resolved
  character entity is cached and rescanned only every 20 captures
  (`StateReader.cs:78`).
- `StatControl` walks `em.GetAllEntities` on every request
  (`ComponentDumper.cs:504-548`), and only ONE dump may be pending at a time,
  under `_dumpGate` with a 30 s timeout (`BridgeServer.cs:175`, `184`,
  `444-453`).

### 1.3 The two traps this protocol must not walk into

- **A negative result taken too early is indistinguishable from a real
  absence.** The first phase 3 control returned the prefab only at about 5 s of
  uptime; the instance appeared by 20 s (`docs/BRIDGE_SPIKES.md:1419-1426`).
  Poll for the SUBJECT, not for `ready:true`.
- **A spawned boss carries the SAME `PrefabGUID` as its prefab**, and the two do
  not agree; cycle 2 fixed the resulting count by deduping and thereby made the
  CHOICE order-dependent (`docs/BRIDGE_SPIKES.md:1412-1417`). The prefab reads
  `Health.Value` 0. A recorder that latched onto the prefab would record a
  perfectly flat zero series and, on a naive reading, an instantaneous kill.

## 2. Decision A - the anchor protocol

### A.1 The three candidate routes, compared

| Route | What it yields | What it can falsify | Cost | Verdict |
|---|---|---|---|---|
| A1 Bridge-recorded boss `Health.Value` time series | denominator (`MaxHealth` at t0), per-sample health deltas, death instant, and the player side from the same tick | per-hit damage AND aggregate TTK AND EHP | one new endpoint plus a cached entity resolve; the typed read already exists at `ComponentDumper.cs:568-573` | **BUILD THIS** |
| A2 Hand-timed kill from a screen recording | one wall-clock duration per run | aggregate TTK only, at about 0.5 s human reaction resolution | an OBS setup already deferred to cycle 8 (`BACKLOG.md:12-18`) | Keep as a ONE-RUN cross-check on A1's clock. Not the anchor. |
| A3 An in-game combat log | UNVERIFIED | UNVERIFIED | UNVERIFIED | REJECTED pending measurement. See section 7. |

### A.2 The decision and its rationale

**Red Moon builds A1: a bridge-side boss health time series.**

Three reasons, in order of weight.

1. **It is the only route that falsifies the DAMAGE MODEL rather than the
   duration.** A kill duration is one number containing every unmodelled human
   term at once. A per-sample health delta attributable to one ability
   application is a number the game itself computed, with no human term in it.
   Given constraint 3 (`power_stat` PROVEN ABSENT), the single most likely way
   for Bloodforge to be confidently wrong is to multiply the coefficient by the
   wrong power stat. A wrong power stat changes per-hit damage by a large
   fraction and is instantly visible in a delta series. It is nearly invisible
   in a kill duration, because a player who takes 20 percent longer than the
   model looks exactly like a model whose damage is 20 percent too high.
2. **It is nearly free, and this was checked rather than assumed.** The typed
   read exists (`ComponentDumper.cs:568-573`), it has already been taken on a
   live instance and returned 8107 (`docs/BRIDGE_SPIKES.md:1393`), and the
   plugin already has the exact caching idiom needed
   (`StateReader.cs:34-38`, `:78`). No external tool, no OCR, no second process.
3. **It supplies the missing denominator as a side effect.** `max_health` is
   instance-only (constraint 1). Any TTK requires a live world with the boss
   spawned anyway. A protocol that has to spawn the boss to get the denominator
   may as well record the whole curve while it is there.

### A.3 What makes each route FALSIFIABLE rather than merely recorded

A recording is falsifiable when a wrong prediction cannot be reconciled with it
after the fact. Stated per route:

- **A1 is falsifiable** because the prediction is committed BEFORE the run
  (section D.4 makes this a file on disk with a hash), and because the series
  carries controls that reject a bad recording rather than smoothing it: every
  sample restates `prefab_guid` and `carries_prefab_marker`
  (`ComponentDumper.cs:557-561`), which is the same control that caught the
  phase 1 generic reader (`docs/BRIDGE_SPIKES.md:913-918`,
  `ComponentDumper.cs:474-478`). A series whose samples carry
  `carries_prefab_marker: true` is DISCARDED, not analysed - that is the prefab,
  and it reads 0.
- **A2 is falsifiable only weakly.** A stopwatch reading has no internal control:
  nothing in the recording says the operator started the clock at the first hit
  rather than at the first sight of the boss. It becomes falsifiable only when
  paired with A1 on the same run, where the video timestamp of the death
  animation must agree with the A1 sample at which `Health.Value` reaches 0 to
  within the sample interval. That single paired run is worth taking once,
  because it is the only thing that validates A1's clock against reality.
- **A3 would be falsifiable** if a log carries per-hit rows with a source, a
  target and an amount. UNVERIFIED that one exists. Never adopt a log whose rows
  are rounded for display: a display-rounded damage number cannot support a
  2 percent per-hit band.

### A.4 What gets built - `GET /record/health` (proposed)

Not `/dump/statcontrol`. That endpoint walks every entity in the world per
request (`ComponentDumper.cs:504`) against a measured 95 ms full-scan cost
(`StateReader.cs:34-38`), and only one dump may be in flight
(`BridgeServer.cs:444-453`). Polling it four times a second would burn a third
of a core and contend with itself for the duration of a boss fight.

The recorder instead follows the `StateReader` idiom exactly:

1. **Arm.** `POST /record/start?guid=<boss guid>` resolves the entity ONCE by
   full scan, and REQUIRES a match with `carries_prefab_marker == false`. If
   only the prefab matches, it returns `subject_not_spawned` and records
   nothing. This is the phase 3 timing trap (`docs/BRIDGE_SPIKES.md:1419-1426`)
   encoded as a precondition rather than commented around.
2. **Sample.** On each `MainThreadTick` (`BridgeServer.cs:262-274`), append one
   fixed-shape sample: monotonic index, `captured_at` UTC (the envelope already
   does this, `BridgeServer.cs:536`), boss `Health.Value`,
   `Health.MaxHealth._Value`, `Health.IsDead`, the restated `prefab_guid` and
   `carries_prefab_marker` controls, plus the player's `Health.Value` and blood
   quality from the same tick (`StateReader.cs:407-441`). Entity validity is
   re-checked in O(1); a rescan happens only when the handle goes stale.
3. **Stop.** `POST /record/stop` returns the series and clears it. A ring buffer
   with a hard cap (proposed 4096 samples, about 17 minutes at 4 Hz) so a
   forgotten recording cannot grow without bound in the game process.
4. **Write.** The Python side (`tools/` , new) writes the series plus the
   section B manifest atomically to `data/anchors/<run_id>.json` per the
   CLAUDE.md atomic-write rule.

Two properties of this design are load-bearing and should be stated rather than
discovered later:

- **The sample rate is a hard ceiling, not a tuning knob, and it is NOT 4 Hz on
  every host. CORRECTED 2026-08-01 BY MEASUREMENT.** It is set by
  `SampleEveryFrames = 15` (`Plugin.cs:41`), which is a FRAME count, so the rate
  is a function of the host's frame rate and nothing in this project had ever
  measured one. MEASURED against a live dedicated server with a spawned Dracula,
  two runs of 24 and 56 samples with 0 dropped:

  ```
  sample interval   min 0.500 s   median 0.502 s   max 0.503 s   (n = 55)
  => 1.99 Hz, and 15 frames / 0.502 s = 29.9 fps
  ```

  **The dedicated server samples at 2 Hz because it runs at 30 fps under
  `-batchMode -nographics`.** The 4 Hz written throughout this spec is an
  inference from an assumed 60 fps client and was never a reading. A 60 fps
  client should give about 4 Hz and that REMAINS UNMEASURED.

  This is the cycle 2 lesson in a new place: a real number answering the right
  question about the wrong host. Consequences, each of which silently corrupts a
  run if it is missed:

  - **A.5 check 5 must be relative, not absolute.** The rule is "no gap greater
    than 3 tick intervals"; the parenthesised "about 750 ms" is a 4 Hz gloss. At
    2 Hz three intervals is about 1506 ms, so a hardcoded 750 ms discards a run
    for one stalled tick that the actual rule permits. The threshold is 3x the
    OBSERVED MEDIAN INTERVAL OF THE SERIES ITSELF.
  - **Every anchor run must RECORD the rate it was taken at**, measured from its
    own series. Two runs taken on different hosts are not comparable series even
    when B.2 says the subjects match.
  - **C.2's clock term doubles on the server**, to +/- 0.5 s per endpoint and so
    up to 1.0 s on a duration - 1.7 percent of a 60 s kill rather than 0.8. Still
    far inside the 15 percent band, so the band does not move.
  - **C.1 isolation gets harder, and this is the one that bites.** An isolated
    delta needs a no-change sample on each side. At 500 ms per sample a window is
    twice as likely to contain a second application, so a server-side run yields
    fewer isolated deltas per cast and the n >= 30 bar costs more casts to clear.

- **The recorder stamps `captured_at` at MILLISECOND resolution**, and that is a
  deliberate departure from the envelope stamp the schema originally pointed at
  (`BridgeServer.cs`, whole seconds). At any real sample rate a whole-second
  stamp gives two to four samples the SAME instant, which makes the gap check,
  the 2.0 s idle window and the bracketing of an isolated delta all
  uncomputable. `Json.UtcNowMillis()` exists for the recorder and for nothing
  else.
- **A 4 Hz series cannot isolate every hit.** Abilities with `hits_per_cast` up
  to 4 exist (`docs/BRIDGE_SPIKES.md:1322`) and several can land inside one
  250 ms window. The protocol therefore does not attempt to attribute every
  delta. It requires ISOLATED deltas: a health drop bracketed by at least one
  sample of no change on each side, with exactly one ability application in the
  window. Section C.1 sets n over isolated deltas, not over all deltas.

### A.5 The minimum viable observation, stated as a checklist

An anchor run is VALID only if all of the following hold. Any failure discards
the run; a discarded run is recorded with its reason and never repaired.

1. At least one sample with `carries_prefab_marker == false` and
   `Health.MaxHealth > 0`.
2. Every sample restates the queried `prefab_guid` and it matches.
3. `Health.Value` at the first sample equals `Health.MaxHealth` (the fight
   starts from full) or the run is marked `partial` and is excluded from the
   TTK gate while remaining usable for the per-hit gate.
4. A terminal sample with `Health.Value <= 0` or `IsDead == true`.
5. No sample gap greater than 3 tick intervals (about 750 ms). A larger gap
   means the tick stalled and the series cannot be integrated.
6. The section B manifest is complete, with no field defaulted.

## 3. Decision B - run identity

A re-check compares like with like only when the identity tuple matches. The
manifest is a single JSON object written beside the series.

### B.1 Fields

**Build and code.**
- `game_build` - `1.1.13.0-r99712` (`data/rmdata/<build>/meta.json` `build`).
- `game_version_string` - `VRising: v1.1.13.0-r99712-b17 (202605251526)`
  (`meta.json` `version_string`). The b-number and timestamp distinguish two
  installs sharing a pin.
- `plugin_version` - the bridge's own version, already on `/health`.
- `engine_version` - Bloodforge's `ENGINE_VERSION`. **It does not exist yet:** a
  repo-wide grep for `ENGINE_VERSION` over `*.py`, `*.cs` and `*.json` returns
  nothing. It is specified in `docs/BLOODFORGE.md:45-49` and must be created by
  the combat-math spec. The anchor format reserves the field now so a later
  anchor cannot be silently compared across engine revisions.
- `bridge_host` - `client` or `server`. Load-bearing, not cosmetic: cycle 2
  measured a field that was 425 of 425 on one host and 0 of 425 on the other
  (`ROADMAP.md:51-55`), and the whole recorded lesson is that a measurement can
  answer the right question about the wrong subject (`ROADMAP.md:79-82`).

**Target.**
- `boss_prefab_guid`, `boss_prefab_name`, `boss_level` - joined to
  `tables/vbloods.json`, which carries exactly these
  (`prefab_guid`, `name`, `level`).
- `boss_entity_index` and `carries_prefab_marker` - the liveness control.
- `boss_max_health_observed` - the denominator, from the run itself. Never from
  disk; there is nothing on disk (constraint 1).
- `boss_resistances_observed` - the four commensurable-by-nothing values read
  live, NOT copied from `vbloods.json`. The disk values are prefab values, and
  the whole point of constraint 1 is that prefab and instance can disagree.

**Difficulty.** Recorded verbatim as an object, not as a label.
- `game_difficulty` - `Normal` or `Brutal`, and
- `unit_stat_modifiers_vblood` - `{LevelIncrease, MaxHealthModifier,
  PowerModifier}`, `unit_stat_modifiers_global`, `vampire_stat_modifiers`,
  `equipment_stat_modifiers_global`.

  Why verbatim: `data/rmdata/<build>/difficulty/Difficulty_Brutal.json` sets
  V Blood `MaxHealthModifier` 1.25, `PowerModifier` 1.7 and `LevelIncrease` 3
  against 1.0, 1.0 and 0 in `Difficulty_Normal.json`. A label is not enough
  because a server may override any of them independently:
  `data/rmdata/<build>/settings/ServerGameSettings.json` carries its own
  `GameDifficulty: "Normal"` alongside separately settable modifier blocks.

**Player.**
- `player_unit_level`, `player_max_health`, `player_unit_stats` - the live
  `UnitStats` block at t0.
- `equipped_item_guids` - a MAP of slot to `items.prefab_guid`, not a gear score.
  Rationale is measured: `gear_score` is present on only 117 of 425 item rows
  (`ROADMAP.md:156-157`) and, checked on disk, it is present on exactly four
  categories - footgear 27, legs 31, chest 32, gloves 27 - and on **0 of the 205
  weapon rows**, 0 of 34 headgear, 0 of 34 cloaks, 0 of 29 magicsource, 0 of 6
  bags. A scalar gear level is therefore not sourceable from disk for the
  slot that matters most. Item guids are, and they reconstruct the stat line
  exactly through `items.stats`.
- `weapon_prefab_guid` and `weapon_type` (`items.weapon_type`).
- `ability_group_guids_in_use` - the bar, joined through
  `items.ability_group_guids` (563 links over 425 items,
  `docs/BRIDGE_SPIKES.md:1428-1435`) into `ability_stats.prefab_guid`.
- `blood_type` and `blood_quality` - read live
  (`StateReader.cs:440-441`); `blood_type` joins `tables/blood_types.json`
  (13 rows, names only, magnitudes scaled at runtime, `ROADMAP.md:158-159`).
- `jewels_and_passives` - NOT ATTEMPTED as a structured field. Recorded as a
  free-text operator note plus, where readable, the buff guids present at t0.
  Stated as a known hole rather than a defaulted field.

**Provenance.**
- `run_id` - `<utc_iso8601>-<boss_prefab_guid>-<short_hash_of_manifest>`.
- `table_fingerprint` - the six table names with `schema_version` and row count
  as promoted (`items` 425 schema 4, `recipes` 663 schema 2, `abilities` 54
  schema 1, `vbloods` 65 schema 2, `blood_types` 13 schema 2, `ability_stats`
  1818 schema 1, `docs/BRIDGE_SPIKES.md:1273-1286`). A later re-check that finds
  a different fingerprint is comparing a different input set.
- `prediction_hash` - see D.4.
- `operator_note` - what the human was trying to do. Never parsed.

### B.2 The matching rule

Two runs are COMPARABLE when they agree exactly on `game_build`,
`boss_prefab_guid`, the whole difficulty object, `blood_type`, and the
`equipped_item_guids` map, and agree on `blood_quality` to within one 10-point
bucket. Anything else is a different subject and may not be pooled. This is
deliberately strict: pooling across subjects is precisely how a model gets fitted
to noise.

## 4. Decision C - tolerance

Two gates against two different quantities, because they fail differently. A
single aggregate gate can pass through cancelling errors: damage 20 percent too
high multiplied by uptime 20 percent too low lands on the right TTK for the
wrong reason.

### C.1 PRIMARY GATE - per-hit damage, median APE <= 2 percent over n >= 30 isolated deltas

The comparison is: predicted damage of one ability application against the
observed `Health.Value` drop across the isolated window that contains it.

**Why 2 percent and not a rounder number.** The observed quantity is the game's
own arithmetic, read through the same typed accessor family that already
produced a control-verified 8107 (`docs/BRIDGE_SPIKES.md:1386-1399`). There is
no human term inside a single hit. The residual error sources are:

- float32 rounding on `Health.Value`, well under 0.01 percent at these
  magnitudes;
- passive regeneration inside the window. `UnitStats.PassiveHealthRegen` and
  `.HealthRecovery` are readable (`ComponentDumper.cs:605-608`) but are NOT part
  of the anchor-time model, and over one 250 ms window they are small;
- aliasing, bounded by the isolation requirement in A.4.

2 percent is therefore roughly an order of magnitude above the measurement floor
and roughly an order of magnitude below the errors that matter. A wrong power
stat or a misapplied fire rating moves a per-hit number by tens of percent, and
a 10 percent band would hide both. A 1 percent band would fail on regeneration
alone.

**`vblood_damage_modifier` is deliberately NOT cited here as an error source**,
which is a change from this spec's first draft. Corrected constraint 4 shows it
is 1.0 on 728 of 732 rows and on all 409 weapon-linked damage rows, so on any
realistic loadout subject it contributes exactly nothing and cannot be what a
2 percent band is protecting against. Naming it would have been borrowing
authority from a number that does not apply. It still must be implemented, for
the inverted reason given in constraint 4: its near-total inertness is what
makes an omission invisible. The gate that catches THAT is D.4's schema test,
not this tolerance band.

n >= 30 because the gate is on the MEDIAN absolute percentage error, and the
median needs enough isolated deltas to be robust to a few mis-attributed
windows. 30 isolated hits is a handful of casts in one real fight, so this is
not an unmeetable bar.

**Additionally**: the MAXIMUM APE over the same n must be <= 10 percent. A tight
median with one 300 percent outlier means one ability is modelled completely
wrongly and the median hid it.

### C.2 SECONDARY GATE - active-time TTK, median within 15 percent over n >= 3 runs

Observed active time = wall duration from the first non-zero health delta to the
terminal sample, MINUS the sum of idle windows, where an idle window is a run of
consecutive samples with zero boss health delta lasting longer than 2.0 s.

**Why subtract idle time at all.** Dodging, repositioning, waiting out a boss
phase and player error only ever ADD wall time. The error is one-sided, so
comparing a model TTK to raw wall time guarantees the model looks fast and
guarantees a temptation to inflate the model to match. Subtracting measured idle
windows removes the largest, most measurable part of that term without
pretending to model player skill.

**Why 15 percent.** The clock contributes under 1 percent: at 4 Hz the
quantisation is +/- 0.25 s per endpoint, so at most 0.5 s on a duration, which
is 0.8 percent of a 60 s kill. Everything else in the 15 percent is behaviour
the model does not have a term for: sub-2 s dodges that the idle filter does not
catch, movement between ability ranges (`AbilityGroupInfo.MinRange` and
`MaxRange` exist, `docs/BRIDGE_SPIKES.md:969`, and are NOT modelled), boss phase
changes, and imperfect ability ordering.

**15 percent is a POLICY number, not a measured one, and this spec says so.** It
is set before the data exists so it cannot be set after. The governing rule is
therefore procedural: the first three valid anchor runs must REPORT their
observed run-to-run spread. If the spread of active-time TTK across three runs
of the SAME comparable subject exceeds 15 percent, the tolerance is revised
UPWARD exactly once, in writing, in this document, citing that data - and the
revision is a ledger entry. It is never adjusted silently, never per run, and
never downward to manufacture a pass.

**A pass on C.2 without C.1 is NOT a pass.** Stated as a rule because it is the
exact failure this gate structure exists to prevent.

### C.3 TERTIARY GATE - EHP, within 10 percent

Predicted player effective health against observed cumulative player health lost
across the run (the player series comes free from the same tick,
`StateReader.cs:407-418`). 10 percent rather than 2 because incoming damage
depends on boss ability selection, which is not under operator control and is
not modelled at anchor time.

### C.4 What a PASS licenses

A pass licenses publication for the COMPARABLE SUBJECT CLASS defined in B.2 and
for nothing else. It is not a statement that the model is correct in general.
Extrapolation beyond the anchored class is permitted but must be labelled
(see D.3).

## 5. Decision D - the publication embargo

Following the strongest existing idiom in this repository: DECLARED AND NEVER
EMITTED. It already governs `items.tier` (`tests/test_schemas.py:34-56`),
`vbloods.max_health` (`data/schemas/vbloods.schema.json`) and
`ability_stats.power_stat` (`tests/test_ability_stats.py:67-76`).

### D.1 The rule, stated so it is testable

**R-EMBARGO.** For any subject S, Bloodforge may serialize `ttk_seconds` only if
a validated anchor set exists for S's comparable class per B.2. Absent that, the
key is ABSENT from the payload - not null, not 0, not -1. `dps` and `ehp` follow
the same rule with their own lift conditions in D.2.

Absent means unsourced. A consumer that sees no `ttk_seconds` must render a
degraded-mode message, per the CLAUDE.md error-handling rule, naming the reason:
`time-to-kill withheld: no validated anchor for this subject on build
1.1.13.0-r99712`.

### D.2 Lift conditions, per field, as predicates

| Field | Lifts when |
|---|---|
| `dps` | C.1 passes. DPS needs coefficients, cast time and cooldown, all on disk (`ability_stats`, 1818 rows), and no health denominator. |
| `ehp` | C.3 passes. |
| `ttk_seconds` | C.1 AND C.2 pass, over n >= 3 comparable runs. TTK additionally needs `max_health`, which does not exist on disk at all (constraint 1). |

This split is not bureaucracy. DPS is falsifiable today with data already
promoted; TTK is not, and merging them would either embargo a computable number
or publish an uncomputable one.

### D.3 After lift

A TTK emitted for a subject OUTSIDE the anchored comparable class must carry
`anchor_status: "extrapolated"` alongside `anchored_subject` naming the class it
was validated against. Inside the class, `anchor_status: "anchored"`. The field
is REQUIRED whenever `ttk_seconds` is present, so an unlabelled TTK is a schema
violation rather than a judgement call.

### D.4 Enforcement in code

Documentation is not enforcement. Six mechanisms, all cheap:

1. **`data/schemas/anchor.schema.json`** - the run manifest plus series shape of
   sections A and B, validated by the existing `core.tables.validate_table` and
   `core.table_deep.deep_problems` machinery.
2. **A pure gate function**, `bloodforge.embargo.publishable_fields(subject,
   anchors) -> frozenset[str]`. The serializer iterates that set. There is no
   second code path that can emit a field, which is what makes the test below
   total rather than a spot check.
3. **`tests/test_embargo.py::test_no_ttk_is_emitted_without_an_anchor`** - with
   an EMPTY anchor directory, serialize a result for a real subject and assert
   `"ttk_seconds" not in payload`, `"dps" not in payload`,
   `"ehp" not in payload`. Assert absence of the KEY, mirroring
   `tests/test_schemas.py:58-62`, which asserts a row without `tier` validates.
4. **`test_ttk_is_declared_but_not_required`** - the schema declares
   `ttk_seconds` with a description containing the embargo rationale and does
   not require it. Byte-for-byte the shape of
   `tests/test_schemas.py:34-56` and `tests/test_ability_stats.py:67-76`.
5. **`test_an_anchor_for_another_build_does_not_lift_the_embargo`** - plant an
   anchor whose `game_build` is a sentinel pin and assert the gate still
   withholds. A build bump therefore RE-ARMS the embargo automatically, which is
   the drift-anchor idiom already used for the build pin
   (`tests/test_drift_anchors.py:1-40`).
6. **`test_no_surface_names_a_ttk_field_while_embargoed`** - a repo grep over
   tracked dashboard and API sources for the emitted field names, in the style
   of the existing cross-file drift anchors. This is the backstop, not the
   mechanism, and is written down as a backstop so nobody relies on it - the
   same footing CLAUDE.md gives `hooks/commit-msg`.

### D.5 What the embargo does NOT cover

Diagnostics under `logs/` and anything under `_scratch/`. A model whose numbers
cannot be looked at cannot be debugged. The embargo is on PUBLICATION to a user
surface: the engine API on 8783 (`core/ports.py:48`), the dashboard on 8778
(`core/ports.py:42`), and any file a user is told to read.

## 6. Decision E - the default subject vector

The requirement: whatever the engine picks silently ranks every build for every
user who does not override it, so the pick is a structural bias and must be
written down with reasons (`BACKLOG.md:34-43`). The 65 rows on disk make this a
choice among knowns.

### E.1 The vector

| Component | Value | Reason |
|---|---|---|
| Target boss | `CHAR_Vampire_Dracula_VBlood`, `prefab_guid` -327335305, level 91 | It is the ONLY boss with a measured live `max_health` on record - 8107 on entity 322945 (`docs/BRIDGE_SPIKES.md:1393`). Since `max_health` is instance-only (constraint 1), it is today the only subject for which a TTK denominator exists at all. It is also the terminal boss, so it is the natural endgame ranking target. Its `fire` resistance is 0 on disk, so the default does not exercise the non-commensurable integer-rating path (constraint 2). |
| Secondary reference boss | `CHAR_Vampire_HighLord_VBlood`, `prefab_guid` -496360395, level 57 | 57 is the MEDIAN level of the 65 rows (computed from `vbloods.json`: the 33rd of 65 sorted levels). It is also already one of the three phase 1 component-inventory subjects (`docs/BRIDGE_SPIKES.md:933`), so its component surface is enumerated. Declared so that any ranking published against the default can be re-run against a mid-progression target and the difference SEEN. |
| Difficulty | `Normal`, with `UnitStatModifiers_VBlood` `{LevelIncrease: 0, MaxHealthModifier: 1.0, PowerModifier: 1.0}` | It is the neutral element: every multiplier is 1.0 in `Difficulty_Normal.json`, so the default introduces no hidden factor. Brutal would silently apply 1.25 health, 1.7 power and +3 levels. See section 7 for the UNVERIFIED part of this. |
| Weapon | `Item_Weapon_GreatSword_Legendary_T08`, `prefab_guid` -1173681254 | **The tie is the finding and it is large.** Counted on disk: the maximum `PhysicalPower` over the 205 weapon rows is 33.700001 and **72 rows tie at it**, spanning all 14 `weapon_type` families (Slashers 7 rows, the other 13 families 5 each). Power alone therefore cannot pick a family, and any spec claiming it did would be inventing a preference. The pick is labelled ARBITRARY on power and is broken by two measured secondary criteria: the row carries 3 `ability_group_guids`, so the weapon-to-ability-to-coefficient join is exercised end to end (ADR-007 lines 73-75), and GreatSword is the family already used as a phase 1 subject (`docs/BRIDGE_SPIKES.md:1004-1005`), which keeps the default on measured ground. NOTE, unresolved: the 72 include `_Shattered` and `_Trader_Template` variants at identical power. UNVERIFIED whether those are player-equippable; the default deliberately takes the plain `_Legendary_T08` row. |
| Gear | An explicit MAP of slot to item `prefab_guid`, not a scalar gear level | Measured: `gear_score` exists on 117 of 425 rows and on exactly four categories (footgear, legs, chest, gloves), with **0 of 205 weapons**, 0 headgear, 0 cloaks, 0 magicsource, 0 bags carrying it. And `items.tier` has NO SOURCE on this build (`ROADMAP.md:154-155`, `tests/test_schemas.py:34-56`), so the `_T0x` name token must not be used to derive one. A scalar default would therefore have to be invented. A guid map is sourced. |
| Blood | `BloodType_Warrior`, `prefab_guid` -516976528, quality 100 | Read from `blood_types.json`: its tier 1 bonus is `BonusPhysicalPower`, which is the stat the default weapon scales, so it is the neutral pairing rather than a build-defining one. Quality 100 is the ceiling, so the default states an upper bound rather than a guess at a typical roll. **The magnitudes are NOT on the prefab** - all 13 rows carry stat NAMES with `value_source: blood_quality_scaled_at_runtime` (`ROADMAP.md:158-159`), so the blood contribution is DECLARED AND OMITTED from the computation until magnitudes are sourced live. The default names the blood; it does not pretend to price it. |
| Jewels and passives | NONE | Not because none matter, but because no jewel or passive source has been measured. An empty set is an honest statement; a populated one would be invention. |

Checked while reading `blood_types.json`: `BloodType_Warrior` carries 9 bonus
entries, tiers 1 to 5 plus tiers 1 to 4 again. That is NOT a duplicate-row
defect - the second set is the `_Secondary` slot (`AB_BloodBuff_Warrior_Tier1`
against `AB_BloodBuff_Warrior_Tier1_Secondary`, distinct `buff_guid`s). Checked
rather than assumed, and recorded because a consumer summing all 9 would
double-count.

### E.2 The bias this default introduces, stated out loud

Dracula at level 91 with Legendary T08 gear ranks ENDGAME builds. A weapon that
is excellent at level 30 and mediocre at 91 will be ranked by its level-91
performance. That is a real distortion and it is the reason `BACKLOG.md:41-43`
requires the consuming surface to state the assumption on screen rather than
bury it. The secondary reference boss exists so the distortion is measurable
rather than merely admitted.

### E.3 The surface contract

Any ranked output states, in the same view and not behind a tooltip: target
boss name and level, difficulty label, weapon name, blood type and quality, and
`anchor_status`. If any of those is defaulted rather than chosen by the user,
the surface says `default`.

## 7. Open questions, each with the measurement that settles it

1. **Does V Rising write a per-hit combat log?** UNVERIFIED. Nothing in
   `docs/BRIDGE_SPIKES.md` enumerates a log sink; the damage path that IS
   enumerated is `DealDamageOnGameplayEvent` on the `_Hit` entity
   (`docs/BRIDGE_SPIKES.md:998-1000`), which is a gameplay event, not a log.
   SETTLED BY: a metadata scan of the interop assemblies for a damage-log or
   combat-log system type, using the scratch `typedump` tool described at
   `docs/BRIDGE_SPIKES.md:1076-1082`. Cheap, and worth doing once before
   building the recorder, because a real per-hit log with unrounded amounts
   would be strictly better than a 4 Hz sample.
2. **Under what difficulty was 8107 measured?** UNVERIFIED, and it matters
   because Brutal multiplies V Blood `MaxHealthModifier` by 1.25. The dump was
   taken on the standalone dedicated server
   (`docs/BRIDGE_SPIKES.md:1263-1266`). The `ServerGameSettings.json` on disk
   under `data/rmdata/<build>/settings/` is the SHIPPED default extracted from
   the install (`tools/rmdata_extract.py:6`, `:43`), not the running server's
   active settings file, so it is evidence about the default and not about that
   run. SETTLED BY: reading the running server's save-folder settings, or
   better, having the recorder emit the live modifier block from the world so
   the manifest never depends on a file the operator could have edited.
   UNVERIFIED whether that block is readable from ECS.
3. **Is 8107 stable across spawns?** UNVERIFIED, n=1. If a boss re-spawns with a
   different `MaxHealth`, the denominator is per-run and not per-boss. SETTLED
   BY: recording `MaxHealth` on two separate spawns of the same boss under an
   identical manifest and comparing.
4. **Can 30 isolated deltas actually be collected at 4 Hz?** UNVERIFIED. It
   depends on real ability cadence. SETTLED BY: the first valid run reporting
   its isolated-delta count. If it comes back under 30, the honest responses are
   to pool isolated deltas across comparable runs or to raise the tick rate for
   the duration of a recording - NOT to lower n.
5. **Which power stat does a coefficient multiply?** PROVEN ABSENT from data
   (constraint 3). This spec does not answer it; it builds the instrument that
   can. The C.1 gate is exactly the experiment: predict a hit under each
   hypothesis and see which survives 2 percent.
6. **Does `Health.Value` reach exactly 0, or does the entity despawn first?**
   UNVERIFIED. `HealthConstants.DestroyOnDeath` and `DestroyAfterDuration` exist
   (`docs/BRIDGE_SPIKES.md:940`), so the entity may vanish before a zero sample
   lands. A.5 accepts `IsDead == true` OR `Health.Value <= 0` for exactly this
   reason, and the recorder must treat a subject that disappears from the world
   as a terminal event rather than an error.

## 8. How gap 7 closes

Gap 7 is SETTLED when this document is accepted and its five decisions are
recorded. It is DISCHARGED - a different and later thing - when:

1. `data/schemas/anchor.schema.json` exists and validates a real run.
2. The recorder endpoint ships and a run passes the A.5 checklist.
3. `tests/test_embargo.py` exists and is green with an empty anchor directory.
4. The prediction is committed with its hash BEFORE the run.
5. C.1, C.2 and C.3 have been evaluated and their results recorded in
   `docs/BRIDGE_SPIKES.md` in the same style as every other measurement here -
   including a FAIL, if that is what happens.

The combat-math spec may open on acceptance of this document, because the
embargo makes an unvalidated engine harmless. It may not PUBLISH until
discharge.

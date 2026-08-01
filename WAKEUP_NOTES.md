# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-08-01 (seventh stretch) - The run did not happen, and the three things blocking it did

Ledger 003m. Suite **544 passed in 20.02s exit 0** (526 before, +18), ruff clean,
ascii_guard exit 0. No C# change, no rebuild, no redeploy. **NO ROADMAP ITEM
CLOSED.**

**THE MAIN TRACK WAS NOT ATTEMPTED, DELIBERATELY.** The session was scoped to
the power-stat experiment at the CLIENT. Neither bridge port answered and no
V Rising process was running. The run needs a human in-world - equip a weapon so
the two power stats diverge, slot Ward of the Damned, find a survivable
non-V Blood target, cast about 30 times in isolation - and the operator was not
available. It is deferred intact rather than approximated. `P(G)` is still
undefined.

**WHAT IS DIFFERENT NEXT TIME.** Three things that would have cost time mid-run
are now closed:

1. **`tools/find_target.py`.** `ANCHOR_RUNS.md` said "find the target's prefab
   guid" without saying how. It lists SPAWNED units over
   `/dump/components?instanced=1` and MARKS V Bloods and prefab rows rather than
   dropping them - a tool that silently filters teaches the operator the list was
   complete.
2. **The caster-side precondition is a CHECK, not a warning.** The arm response
   is the first and only place `PhysicalPower` versus `SpellPower` is
   observable. `ANCHOR_RUNS.md` now says STOP and re-gear rather than describing
   the failure after the fact.
3. **`bloodforge/series.py`.** The engine no longer imports a `tools/` script.
   The re-export is asserted BY IDENTITY, plus an AST check that nothing under
   `bloodforge/` imports from `tools/` - the layering rule, not the one module
   that broke it. Duplicating the two functions was the worse option: two copies
   of the isolation rule can drift, which is what this protocol exists to catch.

**A DATA FIX THAT ALSO RECOVERED THE BROKEN STATE.** `rmdata_ingest` promoted by
copying and left `tables/_incoming/` populated, so promoted and pending were
indistinguishable on disk. Promotion now empties it on the SUCCESS path only -
refused and validated-but-unaccepted runs still leave the rows for inspection.
The six stale files were SHA256-compared against their promoted copies,
identical on all six, and removed.

**Doc drift, found by looking rather than reported.** `ARCHITECTURE.md` listed
the engine as `agents/bloodforge/`, a path that has never existed. Fixed, and
the module map now names all six real modules. Historical specs and plans keep
the old name; they are history.

Inbox clean at open: all 14 `moon_sync_inbox/` files timestamped 10:19 or
earlier against a 13:00 HEAD.

## 2026-08-01 (sixth stretch) - The recorder runs, and its first run corrects four things

Commit `23d40bf`. Suite **526 passed in 20.16s exit 0** (405 before), ruff clean,
ascii_guard exit 0, `dotnet build` 0/0, deployed to both hosts with matching
SHA256. NO ROADMAP ITEM CLOSED. Gaps 12 and 13 opened.

**THE HEADLINE IS WHAT DID NOT HAPPEN.** The power-stat experiment was not run.
It needs the V Rising CLIENT with a live character casting
`AB_Unholy_WardOfTheDamned_AbilityGroup`; the dedicated server runs
`-batchMode -nographics` and has no player. Everything around it is built,
deployed and verified live. The run is one operator session away and
`docs/ANCHOR_RUNS.md` is the procedure.

### What landed

`GET /record/{start,status,stop}` (`HealthRecorder.cs`), the damage model and
DPS cycle (`bloodforge/damage.py`, `dps.py`), the anchor writer
(`tools/anchor_record.py`) and the H1-versus-H2 evaluator
(`bloodforge/powerstat.py`). Built by three subagents on disjoint files; I
re-ran every claimed count and every claimed test myself.

VERIFIED LIVE against a dedicated server with a spawned Dracula: 56 samples in
27.6 s, 0 dropped, `prefab_guid` and the liveness marker restated on 56 of 56,
the prefab correctly rejected. **No NONZERO delta was observed** - nothing
headless damages a boss - and that limit is recorded rather than glossed.

### The four corrections, all from running it

1. **2 Hz, not 4 Hz.** `SampleEveryFrames = 15` is a FRAME count and no frame
   rate had ever been read. Interval median 0.502 s over n=55: 1.99 Hz at
   29.9 fps. Both specs computed the section C tolerances against an assumed
   60 fps. The A.5 gap check is now 3x the OBSERVED median, not 750 ms. Gap 12.
2. **A whole-second clock on a sub-second series.** Caught by reading before
   deploying. `Json.UtcNowMillis` now exists for the recorder alone.
3. **The arm reported a DECLINE as an ABSENCE.** `player_resolved` false while
   samples carried a player block: `Clear()` reset the rescan counter and the arm
   consulted the throttle it had just reset. Third time on this build that a
   silent gate looked exactly like an unwired one.
4. **Corruption cannot be priced under EITHER hypothesis.** All 18 groups carry
   neither a `spell_school` nor `is_weapon_ability`. 60 of 732 unpriceable after
   the experiment, not 42. Gap 13.

### Two things to carry into the next session

- **`max_health` 8107 at n=3**, three boots, three entity indices, 0 on the
  prefab every time. Half of open question 7 answered. The other half - under
  what difficulty, and across a FRESH world - is still open, and no
  `ServerGameSettings.json` is written anywhere so the difficulty is a default
  rather than an observation.
- **THE EXPERIMENT HAS A CASTER-SIDE PRECONDITION.** The character armed against
  reads `PhysicalPower` 10 and `SpellPower` 10, on which both hypotheses predict
  the same number and the run is indeterminate however clean the deltas.
  Section 3.2 rejected the default subject because the ABILITY could not separate
  them; the same run fails on the CASTER side, which neither spec had said.

### Process notes

- **Independent smoke tests found what the suite did not.** `evaluate` raised on
  `statistics.median([])` for a series with zero isolated deltas - which is my
  own flat recording, and which is what a prefab-latched recorder produces. 526
  green tests did not catch it; feeding it one real recorded file did.
- **A stale `.pyc` nearly cost an hour.** Mutating `max(` to `sum(` and back
  gives the same file size, and if it lands inside the same mtime second Python
  reuses the mutated bytecode. Five tests kept failing against correct source.
  Clear `__pycache__` before believing a mutation-test revert.
- All three subagents reported honestly and all their counts reproduced. One
  (`RedMoon.Bridge.csproj` has `EnableDefaultCompileItems=false`) correctly
  flagged a blocker it declined to fix because the file was outside its list.

## 2026-08-01 (fifth stretch) - The embargo lands before the math, and the default subject turns out to prove nothing

Branch `master`. Ledger 003k. Commits `6d5095e` (the embargo gate), `6056b45`
(the combat math spec) and `df2131a` (the living docs and this entry). **NO ROADMAP
ITEM CLOSED** - the combat math spec is OPEN, not discharged, and no math is
implemented. Two new gaps were opened, 10 and 11.

State at close, one run each: `python -m pytest` **405 passed in 19.93s, exit
0** (382 before, +23 from `tests/test_embargo.py`), `python -m ruff check .`
clean, `python tools/ascii_guard.py` exit 0.

**THE GATE LANDED BEFORE THE MATH, AND THAT WAS THE POINT.** `bloodforge/` is
the first engine code in the repo and it opens with its embargo rather than its
arithmetic. `bloodforge/embargo.py` is one gate function that the serializer
iterates, so `tests/test_embargo.py` is TOTAL rather than a spot check - there
is no second code path that can emit a field. `dps` lifts on the per-hit gate
alone, `ehp` on the EHP gate, `ttk_seconds` needs both plus three comparable
runs. Unlifted fields are REMOVED from the payload: absent key, not null, not 0,
not -1. `ENGINE_VERSION` now EXISTS at `0.1.0+1.1.13.0-r99712`; before this
commit ROADMAP and BLOODFORGE both described it as pinned while a repo-wide grep
returned nothing.

**TWO OPEN QUESTIONS SETTLED BY PROBING RATHER THAN REASONING, both now tests.**
A fifth envelope key PASSES the frozen `validate_table` - it requires the four
envelope keys and rejects undeclared fields on ROWS only, never enumerating
envelope keys - so the anchor manifest rides in the same file as the series. And
`core.table_deep.deep_problems` CANNOT gate the anchor: it raises KeyError
outside the frozen `TABLE_NAMES` tuple. The falsification spec's D.4.1 claims
both and is corrected, pinned by a test so the correction cannot be lost.

**TWO EXISTING GATES CAUGHT REAL VIOLATIONS OF MY OWN CHANGE AND BOTH WERE
RIGHT.** The port-literal allowlist rejected two ports I had named in a
docstring. `test_no_stray_schema_files` rejected `anchor.schema.json`, which has
no table - it now carries an explicit `NON_TABLE_SCHEMAS` allowlist rather than
a loosened pattern. Worth recording because the instinct on both was to reach
for the test; the tests were correct both times.

**THE FINDING THAT CHANGES WHAT HAPPENS NEXT: THE DEFAULT SUBJECT VECTOR CANNOT
FALSIFY THE POWER-STAT HYPOTHESIS.** MEASURED: 31 of the 32 weapon-linked damage
groups are `damage_type` physical, and 203 of 205 weapons grant `PhysicalPower
AddToBase` while exactly 1 grants `SpellPower`. So "damage_type selects the
power stat" and "the ability kind selects it" predict the **same number** for
every weapon ability a player will realistically use. A per-hit gate run against
GreatSword versus Dracula passes at 2 percent under both hypotheses and decides
nothing. ZERO rows are `is_weapon_ability` with a non-physical `damage_type` and
a nonzero coefficient, so the weapon side is dead by exhaustion, not by
sampling. The one weapon ability with `damage_type` spell,
`AB_Spear_AThousandSpears_Stab_AbilityGroup`, has `coefficient` a genuine 0.0
and scales with no power stat at all.

**THE DISCRIMINATOR: EXACTLY ONE ROW IN 1818.** Searching the other direction -
a SPELL-school ability whose `damage_type` is physical - returns
`AB_Unholy_WardOfTheDamned_AbilityGroup`, `prefab_guid` -1136860480,
`spell_school` unholy, `damage_type` physical, `coefficient` **exactly 1.0**,
`hits_per_cast` **1**, every near-inert term at its inert value,
`ability_type` SpellSlot2 so it is player-castable. The prediction is not "some
arithmetic on a power stat" but literally **"the observed health delta equals
one of the two power stats"**. It needs no boss and no health denominator, so it
is the CHEAPEST run in the entire protocol and should be the first one taken.
Caveat to carry: one row is a sample of one, and a pass proves the rule only on
that row.

**SIX RECORDED FACTS CORRECTED BY COUNTING.** The pattern held a third time.
The damage block is ALL-OR-NOTHING: **zero of the 732 damage rows omit a
`coefficient`**, so "154 edges reach a group whose coefficient is OMITTED" is
really 154 edges reaching a group with no damage block at all. The edge counts
themselves - 563 total, 409 to damage, 154 not - are exactly right.
`AB_Vampire_Longbow_Primary_AbilityGroup` EXISTS as a row, with
`spawn_prefabs_on_cast` **8**, `cast_time` 5 and `is_weapon_ability` **false**.
`is_weapon_ability` is true on 42 and **18 of those reach damage, not 26**.

**FOUR MORE TERMS ARE EFFECTIVELY CONSTANT, one of them totally.**
`hit_triggers` is **0 on all 732 rows** and carries no information at all;
`multiply_main_factor_with_stacks` is false on all 732; `raw_damage_value` is
nonzero on 1 row, `raw_damage_percent` on 1, `damage_modifier_per_hit` on 3. All
three of those last are `hits_per_cast` 1, so the ramp FORM is unobservable on
this build and the term is identically zero everywhere. The golem story is now
coherent across three fields: `AB_Shapeshift_Golem_T02_Group` has `coefficient`
0 AND `raw_damage_percent` 0.3, and its siblings carry the 0.33 V Blood
modifier - golem damage is percent-of-pool, so a model reading only
`coefficient` prices every golem ability at exactly zero.

**GAP 10, NEW:** 154 of 563 weapon links reach nothing, across 15 distinct
groups. Two of the DEFAULT weapon's three abilities are among them, so every
GreatSword figure is a PRIMARY-ONLY figure and must be labelled one. The longbow
primary is the sharpest case: 8 spawn prefabs on cast, no damage in one hop.

**GAP 11, NEW:** `ability_type` is `Secondary` on **all 36** weapon groups that
carry it, primary attacks included. Not one row reports `Primary`. A consumer
filtering for it gets zero rows and reads that as "no primaries found".

**42 OF 732 DAMAGE GROUPS CANNOT BE PRICED AGAINST ANY BOSS** - 27 holy with no
unit-side field anywhere, 15 fire whose rating needs the gap 8 constant. They
are OMITTED, never computed at a zero reduction. With fire unpriced, every
priceable boss differs from every other only by level-derived power and health.

Inbox was clean at open: all 14 `moon_sync_inbox/` files timestamped 10:19 or
earlier against a 11:18 HEAD, so every one had been processed last session.

## 2026-08-01 (fourth stretch) - Gap 7 settled, the cycle 4 stack ruled, and a range that turned out to be a binary

Branch `master`. Ledger 003j. Commit `314ef07` plus the docs commit carrying
this entry. **NO ROADMAP ITEM CLOSED** - gap 7 is SETTLED but not DISCHARGED,
and cycle 4 is fully planned with ZERO implementation. Both tracks were
operator-deferred to this session.

State at close, one run each: `python -m pytest` **382 passed in 19.60s, exit
0** (unchanged - documents, not tests), `python -m ruff check .` clean, `python
tools/ascii_guard.py` exit 0.

**GAP 7 IS SETTLED AND THE COMBAT-MATH SPEC MAY NOW OPEN.**
`docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md`, 600
lines, five decisions. The operator ruled decision A: the anchor is a
**bridge-side boss `Health.Value` time series**, not a hand-timed recording. The
argument that won it is worth keeping - **a kill duration is one number
containing every unmodelled human term at once, while a per-sample health delta
is a number the game itself computed.** Since `power_stat` is PROVEN ABSENT, the
most likely way for Bloodforge to be confidently wrong is multiplying a
coefficient by the wrong power stat, and that is nearly invisible in a duration
(a player 20 percent slow looks exactly like a model 20 percent hot) and obvious
in a delta. It is also close to free: `ComponentDumper.cs:568-573` already reads
`Health.MaxHealth`, `Health.Value` and `IsDead` with typed accessors and already
returned 8107 on the live Dracula instance. The **embargo is PER FIELD** - `dps`
lifts on the per-hit gate alone because coefficients and cast times are all on
disk, while `ttk_seconds` needs the instance-only denominator over three
comparable runs. Merging them would have forced a choice between embargoing a
computable number and publishing an uncomputable one.

**A MIN AND A MAX HAD BEEN REPORTED AS A SPREAD, AND CORRECTING IT MADE THE RISK
WORSE.** Every prior statement of `vblood_damage_modifier` - `BLOODFORGE.md`,
the session brief, the spec's own first draft - said it "ranges 0.33 to 1.0 over
the 732 damage rows" and that omitting it "misstates every boss TTK by up to
3x". COUNTED: exactly **two** values, **1.0 on 728 rows and 0.33 on 4**, all
four golem-form NPC abilities, and 1.0 on **all 409 weapon-linked damage rows**.
It is inert for loadout coaching. **The danger inverts rather than
disappearing:** a term that is 1.0 almost everywhere is one whose omission is
invisible in 99.5 percent of cases while silently tripling exactly the golem
builds - the `core/table_deep.py` shape, correct-looking everywhere it is
exercised. It ships only with a regression test pinned to those four rows. One
of the four is spelled `AB_Shapesfhit_...` in Stunlock's own data, which
corroborates ADR-007's marker-component rule with a fresh instance.

**TWO NEW GAPS, BOTH FROM OPENING A DIRECTORY NOBODY HAD OPENED.** Gap 8: the
fire rating **cannot be converted to a reduction**.
`ResistanceData.FireResistance_DamageReductionPerRating` is enumerated at
`BRIDGE_SPIKES.md:943` as a declared member and its VALUE has never been read -
absent from `data/rmdata/`, named by the plugin only in a comment. The one
resistance that actually varies across the 65 bosses is the one RM cannot price.
Gap 9: `difficulty/` holds `UnitStatModifiers_VBlood`, and Brutal is
`{LevelIncrease 3, MaxHealthModifier 1.25, PowerModifier 1.7}`. **Every level and
power figure in `vbloods.json` is implicitly a NORMAL figure.** Difficulty is a
third subject-vector axis that all three concept lenses and every prior pass
missed, and it is the only axis fully sourced on disk today.

**CYCLE 4 IS PLANNED AND THE STACK IS RULED.** ADR-008: server-rendered HTML,
vanilla JS, no framework, no build step, no `package.json`. Three concept agents
on disjoint lenses - observer, coaching, provenance - each reached it
independently for different reasons, which is what made the agreement worth
something. `docs/research/DASHBOARD_CONCEPTS.md` holds 30 adjudicated concepts, a
ranked 7-item slice, 7 conflict rulings, 16 measured prohibitions, and a
NORMATIVE five-state vocabulary (COMPUTED, MEASURED ZERO, OMITTED,
UNSOURCED-ON-BUILD, EMBARGOED). The corpus is the spine and the live game is an
enhancement: **3,038 rows answer real coaching questions with the game shut,
which is its ordinary state.** Two prerequisites land BEFORE the first frontend
file: `ascii_guard.py` must gain `.js/.html/.css` (it covers 11 suffixes and not
those three, so cycle 4 would ship RM's first authored files outside its own hard
rule), and `docs/EMBARGO.json` must exist.

**THE THREE LENSES INDEPENDENTLY INVENTED ONE PANEL.** Observer O4, coaching C2
and provenance P4 were three names for the same grid. Built separately they would
have produced three disagreeing accounts of the same absence. Merged as A1.

**THE ADJUDICATOR PREFERRED THE BUILDER'S SELF-CRITIQUE OVER THE REQUESTER'S
ENTHUSIASM.** The observer lens called the provenance amendment cycle 4's
highest-value item; the provenance lens, which would build it, argued against its
own thesis - every historical failure here was caught by a document, a test or a
recount, none by a UI. Ruling: split it, the data half is real but is INGEST work
and must not count toward cycle 4, the UI half is rejected.

**CCR-146 IS LITERALLY TRUE AND BESIDE THE POINT.** Stage 4 opened on it because
it was a correctness question about RM rather than a feature. RM's `verifier` was
dispatched under a no-tool constraint and quoted **both hard rules verbatim** -
including the incidental "14 of the 30 commits" clause - plus all 17 `CLAUDE.md`
headings, with **zero tool calls**, so nothing was read off disk. The rules DO
reach subagents; they arrive as a **`system-reminder` injection rather than in
the system prompt proper**. RM was never exposed. Scope stated rather than
generalized: one agent type, one harness, **2.1.219** - and the `claude` on PATH
is **2.1.220**, so RM runs two CLI versions at once and any RM finding must name
which produced it.

**A SILENT ZERO FOOLED AN ADVERSARIAL AGENT INTO DESIGNING AROUND A FICTION.**
The provenance lens built a whole section on "`RM-DataRefresh` is defined but not
installed", from a `schtasks /query` that returned zero rows. Git Bash MSYS
path-translation had rewritten `/query` into `C:/Program Files/Git/query`;
schtasks exited 1 and the pipeline yielded nothing. The task is installed and
Ready, next run 2026-08-02 05:30. **Third instance of this shape** - after 1474
versus 1818 and 119 versus 146 - and the first where it survived an adversarial
pass. Rule now in memory: never call a `/`-flagged Windows exe from the Bash
tool; use the PowerShell tool or a Python `subprocess` list, which is why
`tools/rm_facts.py` got the right answer all along.

**AND THE SAME TRAP CAUGHT ME.** Checking the coaching lens's claim that player
items carry the four resistances bosses lack, I keyed on `type`/`name`, got zero
hits, and nearly recorded the claim as refuted. The real key is `stat`, and the
claim was correct - Sun 34, Garlic 22, Silver 22, Holy 8, Fire 8. **A probe that
gives the gate nothing to catch reads exactly like an absence**, landing on the
agent enforcing that very lesson.

**SIBLING TRAFFIC: RM IS CLEAN ON THE ALIAS AND SAID SO.** LW reports `rc-main`
still resolves headless on LW despite RC removing the machine-wide key, and
traced it to RC's `budget_saver` and a live job state. RM probed its own: no
`model` key anywhere, all THREE `.claude.json` path variants now trusted, and
`claude -p` with no `--model` returns exit 0. RM is unaffected, which makes the
source per-project rather than machine-wide and supports LW's own lead.

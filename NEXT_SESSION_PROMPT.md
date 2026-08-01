# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 - RUN THE POWER-STAT EXPERIMENT AND IMPLEMENT THE DAMAGE MODEL. The
combat math spec is OPEN and the embargo is already code, so the math is now
safe to write. Read CLAUDE.md, MEMORY.md, ROADMAP.md, WAKEUP_NOTES.md,
docs/BLOODFORGE.md, docs/adr/ADR-007-* and ADR-008, and BOTH cycle 3 specs -
docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md and
docs/superpowers/specs/2026-08-01-bloodforge-combat-math-design.md - then
git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING - it is a live
sibling channel and it moved seven times during one session recently.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above, never from a hash written in a doc.
- Last verified, one run each: pytest 405 passed in 19.93s exit 0 (382 before,
  +23 from tests/test_embargo.py), ruff clean, ascii_guard exit 0. The C# side
  has NOT been rebuilt for two sessions (no C# changed). There is NO .sln -
  build bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. Audited clean across every surface 2026-08-01.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log.
- Never write a port literal - import from core/ports.py. That file is FROZEN,
  and its allowlist test WILL catch a port named in a docstring. It did.
- DO NOT run git lfs install (inert pre-push under core.hooksPath).
- data/rmdata/ is gitignored and regenerable. Promoted and count-ASSERTED:
  items 425 (schema 4), recipes 663, abilities 54, vbloods 65 (schema 2),
  blood_types 13, ability_stats 1818 (schema 1). 3,038 rows total.
- ops/loop/slots.py is byte-identical across three repos, sha256 5297f2d0...,
  7154 bytes, pinned in tests/test_slots.py. MAX_CONCURRENT_SLOTS = 3. DO NOT
  EDIT outside a coordinated round. Nothing in RM calls the governor yet.

WHAT LANDED LAST SESSION - THE GATE IS BUILT, DO NOT REBUILD IT.

bloodforge/ is the first engine code in the repo and it opens with its embargo
rather than its arithmetic. bloodforge/embargo.py is ONE gate function that the
serializer iterates, so tests/test_embargo.py is TOTAL rather than a spot check.
dps lifts on the per-hit gate alone, ehp on the EHP gate, ttk_seconds needs both
plus three comparable runs. Unlifted fields are REMOVED - absent key, not null,
not 0, not -1. data/schemas/anchor.schema.json is the recorded run shape.
ENGINE_VERSION now EXISTS at 0.1.0+1.1.13.0-r99712 in bloodforge/__init__.py.

Two questions were settled by PROBING and are now tests, so do not re-reason
them: a fifth envelope key PASSES the frozen validate_table (it rejects
undeclared fields on ROWS only), so the anchor manifest rides in the same file
as its series; and core.table_deep.deep_problems CANNOT gate the anchor because
it raises KeyError outside the frozen TABLE_NAMES tuple.

THE MAIN TRACK - TAKE THE CHEAPEST RUN IN THE PROTOCOL FIRST.

THE DEFAULT SUBJECT VECTOR CANNOT FALSIFY THE POWER-STAT HYPOTHESIS, and this is
the single most important thing to carry in. MEASURED: 31 of the 32
weapon-linked damage groups are damage_type physical, and 203 of 205 weapons
grant PhysicalPower AddToBase while exactly 1 grants SpellPower. So "damage_type
selects the power stat" and "the ability kind selects it" predict THE SAME
NUMBER for every weapon ability a player will realistically use. A per-hit gate
against GreatSword versus Dracula passes at 2 percent under both and decides
nothing. ZERO rows are is_weapon_ability with a non-physical damage_type and a
nonzero coefficient, so the weapon side is dead by EXHAUSTION, not by sampling.

EXACTLY ONE ROW IN 1818 SEPARATES THEM:

  name          AB_Unholy_WardOfTheDamned_AbilityGroup
  prefab_guid   -1136860480
  spell_school  unholy      <- H2 predicts SpellPower
  damage_type   physical    <- H1 predicts PhysicalPower
  coefficient   1.0         <- exactly 1.0, so no arithmetic to get wrong
  hits_per_cast 1           <- no multi-hit aliasing at 4 Hz
  ability_type  SpellSlot2  <- player-castable, on the bar
  cast 0.1  post_cast 0.2  cooldown 11  gcd 0  vblood_modifier 1.0

The prediction is literally "the observed health delta equals one of the two
power stats". It needs NO boss, NO V Blood and NO health denominator - just one
isolated hit plus the player's live PhysicalPower and SpellPower from the same
tick, both already read by StateReader. IT CAN RUN BEFORE ANY BOSS IS SPAWNED.
Take it first. Caveat to state in the ledger: one row is a sample of one.

BUILD ORDER for the session:
1. GET /record/* on the bridge, per falsification spec A.4. Arm by full scan
   REQUIRING carries_prefab_marker == false, sample on MainThreadTick, ring
   buffer capped at 4096, stop returns and clears. Not /dump/statcontrol - that
   walks every entity per request against a measured 95 ms full scan under a
   one-at-a-time gate.
2. The Ward of the Damned run. Record, then evaluate H1 against H2.
3. Implement sections 2 and 4 of the combat math spec behind the embargo.

THE SAMPLE CEILING IS 4 Hz, set by SampleEveryFrames = 15 in Plugin.cs:41, and
the section C tolerances were computed against it. It is a constraint, not a
knob.

MEASURED FACTS THAT CONSTRAIN THE MATH. Each silently produces a wrong number if
forgotten. Do not re-derive them.

1. THE DAMAGE BLOCK IS ALL-OR-NOTHING. ZERO of the 732 damage rows omit a
   coefficient. A group reaching no _Hit prefab omits coefficient,
   raw_damage_value, raw_damage_percent, damage_type and hits_per_cast TOGETHER.
   The edge counts are right - 563 links, 409 to a damage group, 154 not - but
   the 154 reach 15 groups with NO DAMAGE BLOCK AT ALL, which is a different
   statement from a row missing one field.
2. 42 OF 732 DAMAGE GROUPS CANNOT BE PRICED AGAINST ANY BOSS. 27 deal holy,
   which has NO unit-side field anywhere across 150 enumerated components; 15
   deal fire, whose integer rating needs the gap 8 global constant. OMIT them,
   never compute at a zero reduction - a zero resistance is a real and different
   claim. With fire unpriced, every priceable boss differs from every other only
   by level-derived power and by health.
3. reduction() IS A PARTIAL FUNCTION ON THREE OF FIVE TYPES: physical 0.0 on all
   65, spell 0.0 on all 65, corruption 0.5 on all 65. fire and holy UNDEFINED.
   DO NOT AVERAGE THEM - two are float resistances, one is an integer rating,
   one is already a reduction.
4. THE DPS CYCLE IS A MAX, NOT A SUM: max(cast_time + post_cast_time, cooldown,
   global_cooldown). The three windows OVERLAP - a cooldown runs during the
   cast. Summing understates DPS on every cooldown ability. cooldown is 0 on 352
   of 1818 rows, which is what makes the max-form necessary. cast_time is
   missing on exactly 3 rows; those have an undefined cycle and no DPS.
5. GAP 10 - 154 OF 563 WEAPON LINKS REACH NOTHING. Two of the DEFAULT weapon's
   three abilities are among them (AB_GreatSword_LeapAttack_AbilityGroup and
   AB_GreatSword_GreatCleaver_AbilityGroup), so ANY GreatSword DPS is a
   PRIMARY-ONLY DPS and must be labelled one. Sharpest case:
   AB_Vampire_Longbow_Primary_AbilityGroup declares spawn_prefabs_on_cast 8 and
   cast_time 5 - a draw, not a swing - and reaches no _Hit prefab in one hop.
   Its damage most likely lives on a projectile spawned at cast.
6. GAP 11 - ability_type IS NOT A SLOT DISCRIMINATOR. All 36 weapon groups that
   carry one report Secondary, primary attacks included. NOT ONE reports
   Primary. A consumer filtering ability_type == "Primary" gets ZERO rows and
   reads that as "no primaries found". Derive slot from the weapon-to-group
   link.
7. FOUR MORE TERMS ARE EFFECTIVELY CONSTANT. hit_triggers is 0 on ALL 732 and
   carries no information whatever. multiply_main_factor_with_stacks is false on
   all 732. raw_damage_value is nonzero on 1 row (AB_Charm 0.01),
   raw_damage_percent on 1 (Golem_T02 0.3), damage_modifier_per_hit on 3. All
   three of those last have hits_per_cast 1, so the ramp FORM is UNOBSERVABLE on
   this build - the spec picks linear arbitrarily and pins it with a test.
8. THE GOLEM STORY IS COHERENT ACROSS THREE FIELDS.
   AB_Shapeshift_Golem_T02_Group has coefficient 0 AND raw_damage_percent 0.3,
   and its siblings carry vblood_damage_modifier 0.33. Golem damage is
   PERCENT-OF-POOL, so a model reading only coefficient prices every golem
   ability at exactly zero. Which pool is UNSOURCED - settle it by recording one
   application against two targets of different max health.
9. BOSS max_health IS INSTANCE-ONLY. 0 on all 65 prefabs against 8107 on the one
   live Dracula instance. Not spawn scaling - 0 to 8107 is not a ratio - so
   nothing offline recovers it. It must be scaled by the difficulty
   MaxHealthModifier recorded verbatim in the manifest (gap 9: Brutal is
   {LevelIncrease 3, MaxHealthModifier 1.25, PowerModifier 1.7}). UNVERIFIED:
   under WHAT DIFFICULTY was 8107 measured, and is it stable across spawns (n=1).
10. physical_power EQUALS spell_power on all 65 boss rows, 33 distinct values
    over 33 distinct levels, so both are LEVEL-DERIVED, not per-boss authored.
11. vblood_damage_modifier IS BINARY: 1.0 on 728 of 732, 0.33 on exactly 4, all
    golem-form NPC abilities, and 1.0 on ALL 409 weapon-linked damage rows.
    INERT for loadout coaching. Implement it anyway - being 1.0 almost
    everywhere is what makes an omission invisible in 99.5 percent of cases.

THE SECOND TRACK - CYCLE 4, PLANNED AND UNBUILT. Do NOT open it in the same
session as the combat math. ADR-008 rules the stack: server-rendered HTML from a
Python stdlib server on the dashboard port, about 200 lines of vanilla JS,
inline SVG, NO framework and NO build step. docs/research/DASHBOARD_CONCEPTS.md
holds 30 adjudicated concepts, a ranked 7-item slice, 7 conflict rulings, 16
measured prohibitions and a NORMATIVE five-state vocabulary (COMPUTED, MEASURED
ZERO, OMITTED, UNSOURCED-ON-BUILD, EMBARGOED). Build order starts with the
five-state token, because if it is invented per-panel it will be flattened to a
nullable number by the third panel.

TWO PREREQUISITES LAND BEFORE THE FIRST FRONTEND FILE, NOT AFTER:
- tools/ascii_guard.py (FROZEN, needs operator approval) must gain .js, .html
  and .css. It covers 11 suffixes and not those three.
- docs/EMBARGO.json must exist, tracked, naming time_to_kill as blocked on gap 7
  with its lifting criterion stated. NOTE: bloodforge/embargo.py now holds the
  live gate, so EMBARGO.json is a PUBLISHED artifact derived from it, not a
  second source of truth. Do not let them diverge.

THE THIRD TRACK - LINK INGEST STAGES 4 TO 7. docs/research/LINK_INGEST.md
Stage 4 is OPEN: 1 of 21 survivors dived, 1 unreachable, 1 read at source, 18
owed. CCR-146 is REFUTED for RM - subagents DO receive CLAUDE.md, as a
system-reminder injection rather than in the system prompt proper, measured with
zero tool calls on CLI 2.1.219. Next is the binary-RE pair, the sharpest
overturn in the corpus: CCR-35 pyghidra-lite (8) and CCR-89 x64dbg (7). Gap 8
(reading a global ECS constant that has never been read) is exactly their shape.
STAGE 5 WARNING: a previous fan-out truncated its challenge input at 12,000
chars and left 33 entries unchallenged, and every apparent survivor was an
artifact of that gap. CHECK THE FAN-OUT'S OWN COVERAGE BEFORE BELIEVING IT.

THE FOURTH TRACK - HEADLESS. Phase 0a PASSES. The loop still does not exist.
RM is CLEAN on the model alias: no model key anywhere, all three .claude.json
path variants trusted, claude -p with no --model returns exit 0. LW still sees
rc-main and traced it to RC's budget_saver plus a live job state - RC's to fix.
RM's PreToolUse gate FIRES headless under bypassPermissions and covers
--no-verify, which the commit-msg hook cannot. NOT MEASURED: anything about a
WORKTREE, three-way concurrency, or whether a contended acquire reaps a stale
lock. Next action is the loop itself, the first thing that will ever call the
shared governor. TWO CLI VERSIONS ARE LIVE: npm claude on PATH is 2.1.220, the
interactive desktop host is 2.1.219. Name which one produced any finding.

HOW TO PROBE ANYTHING, learned the hard way five times now.

A gate that stays silent because the probe gave it nothing to catch is
INDISTINGUISHABLE from a gate that is not wired. Before measuring whether a
guard fires, CALL IT DIRECTLY FIRST and confirm it returns a reason. Then pick a
discriminator only one mechanism can satisfy. THIS IS ALSO THE SHAPE OF THE
POWER-STAT EXPERIMENT: the whole reason GreatSword-versus-Dracula is useless is
that both hypotheses satisfy it.

COUNT THE ROWS, DO NOT READ THE PROSE DESCRIBING THEM. That discipline has now
moved a number three times: ability_stats 1474 to 1818, the link corpus 119 to
146, vblood_damage_modifier from a range to a binary - and last session it
corrected six more recorded facts in one pass.

NEVER CALL A /-FLAGGED WINDOWS EXE FROM THE BASH TOOL. Git Bash MSYS
path-translation rewrites a leading-slash argument into a Windows path, so
schtasks /query arrives as schtasks C:/Program Files/Git/query and yields ZERO
ROWS. Use the PowerShell tool or a Python subprocess list. Same class: verify a
field NAME before concluding a field is absent - items.stats entries are
{modification, stat, value} and keying on `type` returns a clean, wrong zero.

Same shape on the game side: "ready":true means the PREFAB MAP settled, NOT that
the world has spawned its units. A live boss did not exist at 5 s of server
uptime and did exist at 20 s. POLL FOR THE SUBJECT, not just for readiness.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. There is no .sln.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. The
  client tree holds a flat plugins\RedMoon.Bridge.dll and the server tree holds
  plugins\RedMoon.Bridge\RedMoon.Bridge.dll - one per host, correct.
- Launch: VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver
  -saveName world1 -batchMode -nographics. Poll the server bridge /health.
- Never Stop-Process; taskkill /F through PowerShell.
- Your PowerShell tool is pwsh 7.6.4 Core, so &&, ||, ternary and ?? work. This
  does NOT relax the 7-bit-ASCII rule.
- Output to _scratch\rmprobe as saved JSON, not committed.
- The phase 1-3 payloads under _scratch\rmprobe\c3\ and c3p2\ are still on disk
  and answer most component and field-TYPE questions without launching anything.
  Read declared TYPES before writing any reader.
- DO NOT BUILD A GENERIC VALUE READER. Attempted twice, both recorded as
  failures - managed reflection read 539327184 for every Int32, and raw il2cpp
  field offsets HARD CRASHED the dedicated server. Use TYPED accessors.

DEBT, unchanged. The promoted items table lost its 425 localization_guid values
because the dump was taken on the dedicated server, where that join resolves 0
of 425 by measurement. A HOST fact, not a regression. Backed up to
_scratch\rmprobe\c3p2\items-client-v3-with-localization.json; a client dump
refills them in about 100 ms. Also: six files still sit in
data/rmdata/<build>/tables/_incoming/ from an earlier run, so a reader cannot
tell promoted from pending.

TDD per CLAUDE.md: failing characterization or regression test first, then
implement, then verify at the tier the change earns before committing. A schema,
engine or ENGINE_VERSION change is Tier 2 - full suite plus a restart. Note the
embargo gate was written test-first but its RED was never observed; if that
matters to you, say so and the next module will show the failing run.

Launch build work via subagents per CLAUDE.md. They DO receive CLAUDE.md's hard
rules (measured 2026-08-01), so do not re-paste them. But a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and RE-RUN ANY AGENT'S CLAIMED COUNTS, BUILDS AND FILE EXISTENCE YOURSELF.

End with /done, and print the next-session prompt inline.
```

# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 - RUN THE POWER-STAT EXPERIMENT ON THE CLIENT. Everything around it is
built, deployed and verified live; the run itself is the whole session. Read
CLAUDE.md, MEMORY.md, ROADMAP.md, WAKEUP_NOTES.md, docs/BLOODFORGE.md,
docs/ANCHOR_RUNS.md (the operator procedure, written for exactly this run), and
BOTH cycle 3 specs - docs/superpowers/specs/2026-08-01-bloodforge-falsification-
design.md and docs/superpowers/specs/2026-08-01-bloodforge-combat-math-design.md
- then git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above, never from a hash written in a doc.
- Last verified, one run each: pytest 526 passed in 20.16s exit 0 (405 before,
  +121), ruff clean, ascii_guard exit 0. The C# WAS rebuilt last session and
  deployed to BOTH hosts with matching SHA256. There is NO .sln - build
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj. Note csproj has
  EnableDefaultCompileItems=false, so a NEW .cs file must be added to the
  ItemGroup by hand or it silently will not compile.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. Audited clean again 2026-08-01 on commit 23d40bf.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log.
- Never write a port literal - import from core/ports.py. That file is FROZEN
  and its allowlist test WILL catch a port named in a docstring.
- DO NOT run git lfs install (inert pre-push under core.hooksPath).
- data/rmdata/ is gitignored and regenerable. Promoted and count-ASSERTED:
  items 425 (schema 4), recipes 663, abilities 54, vbloods 65 (schema 2),
  blood_types 13, ability_stats 1818 (schema 1). 3,038 rows total. Every one of
  these was independently re-counted last session and all reproduced.
- ops/loop/slots.py is byte-identical across three repos, sha256 5297f2d0...,
  7154 bytes, pinned in tests/test_slots.py. MAX_CONCURRENT_SLOTS = 3. DO NOT
  EDIT outside a coordinated round. Nothing in RM calls the governor yet.

WHAT LANDED LAST SESSION - DO NOT REBUILD ANY OF IT.

GET /record/{start,status,stop} in bridge/src/RedMoon.Bridge/HealthRecorder.cs.
It samples on the same MainThreadTick as StateReader, resolves its subject ONCE
and re-validates in O(1), REQUIRES carries_prefab_marker false at arm, and is
STOP-AT-CAP at 4096 rather than an overwriting ring (A.5.3 needs the FIRST
sample to equal max health; a ring silently eats the start of a fight).
bloodforge/damage.py and dps.py implement spec sections 2 and 4 behind the
embargo. tools/anchor_record.py writes the run plus the B.1 manifest atomically
and runs the A.5 checklist; bloodforge/powerstat.py evaluates H1 against H2.

VERIFIED LIVE against a dedicated server with a spawned Dracula: 56 samples in
27.6 s, 0 dropped, prefab_guid and the liveness marker restated on 56 of 56, the
prefab seen and correctly rejected. NOT COVERED: no NONZERO health delta was
ever observed, because nothing headless damages a boss. THE FIRST CLIENT RUN IS
WHAT PROVES THE DELTA PATH. A recorder reading nothing produces a series that
looks exactly like that flat one, which is why the controls are on every sample.

THE MAIN TRACK - ONE RUN, AT THE CLIENT, AND IT IS THE WHOLE SESSION.

P(G), the power stat, is UNDEFINED and therefore every damage number Bloodforge
can compute is absent. Exactly ONE row in 1818 can decide it, re-counted twice
and still unique:

  name          AB_Unholy_WardOfTheDamned_AbilityGroup
  prefab_guid   -1136860480
  spell_school  unholy      <- H2 predicts SpellPower
  damage_type   physical    <- H1 predicts PhysicalPower
  coefficient   1.0         <- exactly 1.0, so no arithmetic to get wrong
  hits_per_cast 1           <- no multi-hit aliasing
  ability_type  SpellSlot2  <- player-castable, on the bar

The prediction is literally "the observed health delta equals one of the two
power stats". It needs NO boss, NO V Blood and NO health denominator.

FIVE PRECONDITIONS. Any one of them silently ruins the run.

1. THE CLIENT, not the dedicated server. The server has no player at all.
2. Ward of the Damned actually slotted and castable.
3. YOUR TWO POWER STATS MUST DIFFER. This is the one nobody had written down
   until last session and it is now enforced in powerstat.evaluate. MEASURED on
   the character the recorder armed against: PhysicalPower 10 and SpellPower 10,
   on which both hypotheses predict the SAME NUMBER and the run is indeterminate
   however clean the data. Section 3.2 rejected the default subject because the
   ABILITY could not separate the hypotheses; the same run fails on the CASTER
   side. Equip a real weapon - 203 of 205 grant PhysicalPower and no SpellPower,
   which is what makes the two diverge.
4. A target that SURVIVES the hit and is not a V Blood. One-shotting it gives
   one delta and the C.1 gate wants 30.
5. ISOLATED hits: cast, WAIT, cast. A window containing two applications is
   DISCARDED, not averaged. Do not weave weapon attacks in.

CHECK THE ARM RESPONSE BEFORE CASTING. player_resolved must be true and
player_unit_stats must be present - that block is the entire comparison basis,
and it was silently omitted by a defect fixed last session. carries_prefab_marker
must be false; subject_not_spawned means poll for the SUBJECT, never for
ready:true.

Then: python -m bloodforge.powerstat data/anchors/<run_id>.json

STATE THE CAVEAT IN THE LEDGER: one row is a sample of one. A pass says which
hypothesis survives on THIS ability and does not prove the rule corpus-wide. It
is the only evidence the build affords - ZERO rows are is_weapon_ability with a
non-physical damage_type and a nonzero coefficient, so the weapon side is dead by
EXHAUSTION rather than by sampling.

MEASURED FACTS THAT CONSTRAIN THE MATH. Each silently produces a wrong number if
forgotten. Do not re-derive them - all were re-counted last session.

1. THE SAMPLE RATE IS HOST-DEPENDENT AND 4 Hz WAS NEVER A MEASUREMENT. Gap 12.
   SampleEveryFrames = 15 is a FRAME count. MEASURED on the dedicated server:
   interval min 0.500 median 0.502 max 0.503 over n=55, so 1.99 Hz at 29.9 fps
   under -batchMode -nographics. The client SHOULD give about 4 Hz and that is
   STILL UNMEASURED - YOUR RUN MEASURES IT FOR FREE, so report it. The A.5 gap
   check is 3x the OBSERVED median interval, never a hardcoded 750 ms.
2. THE DAMAGE BLOCK IS ALL-OR-NOTHING. Zero of the 732 damage rows omit a
   coefficient. 563 links, 409 to a damage group, 154 not - and the 154 reach 15
   groups with NO DAMAGE BLOCK AT ALL, a different statement from a missing field.
3. 60 OF 732 DAMAGE GROUPS ARE UNPRICEABLE AFTER THE EXPERIMENT, NOT 42. 27 holy
   and 15 fire are blocked on the RESISTANCE side (gap 8). The other 18 are
   CORRUPTION and are blocked on the POWER side (gap 13, new): all 18 carry
   neither a spell_school nor is_weapon_ability, so H1 and H2 are both SILENT on
   them and no experiment outcome prices them. Corruption 0.5 is the only nonzero
   defined reduction on this build and NOTHING REAL REACHES IT.
4. reduction() IS A PARTIAL FUNCTION: physical 0.0 on all 65, spell 0.0 on all
   65, corruption 0.5 on all 65, fire and holy UNDEFINED. DO NOT AVERAGE THEM -
   two are float resistances, one is an integer rating, one is already a
   reduction.
5. THE DPS CYCLE IS A MAX, NOT A SUM: max(cast_time + post_cast_time, cooldown,
   global_cooldown). The windows OVERLAP. cooldown is 0 on 352 of 1818 rows,
   which is what forces the max form. Mutating it to a sum fails five tests -
   checked. cast_time is missing on exactly 3 rows; undefined cycle, no DPS.
6. GAP 10 - 154 OF 563 WEAPON LINKS REACH NOTHING, including two of the DEFAULT
   weapon's three abilities, so ANY GreatSword DPS is PRIMARY-ONLY and must be
   labelled one. Sharpest case: AB_Vampire_Longbow_Primary_AbilityGroup declares
   spawn_prefabs_on_cast 8 and cast_time 5 - a draw, not a swing.
7. GAP 11 - ability_type IS NOT A SLOT DISCRIMINATOR. All 36 weapon groups that
   carry one report Secondary, primary attacks included. NOT ONE reports Primary.
   Derive slot from the weapon-to-group link.
8. FOUR TERMS ARE EFFECTIVELY CONSTANT. hit_triggers 0 on ALL 732 and carries no
   information. multiply_main_factor_with_stacks false on all 732.
   raw_damage_value nonzero on 1 row, raw_damage_percent on 1,
   damage_modifier_per_hit on 3 - and all three of those have hits_per_cast 1, so
   the ramp FORM is UNOBSERVABLE and the linear choice is arbitrary and pinned.
9. THE GOLEM STORY IS COHERENT ACROSS THREE FIELDS. AB_Shapeshift_Golem_T02_Group
   has coefficient 0 AND raw_damage_percent 0.3, siblings carry
   vblood_damage_modifier 0.33. A model reading only coefficient prices every
   golem ability at exactly zero. WHICH POOL is UNSOURCED.
10. BOSS max_health IS INSTANCE-ONLY, AND 8107 NOW REPRODUCES AT n=3 across three
    boots and three distinct entity indices (322945, 322862, 322840) against 0 on
    the prefab every time. Half of open question 7 is answered: it is stable
    across a reload of the same save. STILL OPEN: under what difficulty (no
    ServerGameSettings.json is written anywhere, so it is a default rather than
    an observation) and whether it holds across a FRESH world.
11. vblood_damage_modifier IS BINARY: 1.0 on 728, 0.33 on 4, and 1.0 on ALL 409
    weapon-linked damage rows. INERT for loadout coaching. Implemented anyway -
    being 1.0 almost everywhere is what makes an omission invisible.
12. physical_power EQUALS spell_power on all 65 boss rows over 33 distinct levels,
    so both are LEVEL-DERIVED, not per-boss authored.
13. GameDifficulty is an INTEGER in difficulty/*.json (Easy 0, Normal 1, Brutal 2)
    and a STRING in ServerGameSettings.json. Both specs call it a string. Joining
    on it across the two files returns nothing. Brutal's V Blood block is
    {LevelIncrease 3, MaxHealthModifier 1.25, PowerModifier 1.7}; its GLOBAL
    PowerModifier is 1.4, not 1.7.

THE SECOND TRACK - CYCLE 4, PLANNED AND UNBUILT. Do NOT open it in the same
session as the experiment. ADR-008 rules the stack: server-rendered HTML from a
Python stdlib server, about 200 lines of vanilla JS, inline SVG, NO framework and
NO build step. docs/research/DASHBOARD_CONCEPTS.md holds 30 adjudicated concepts,
a ranked 7-item slice, 7 conflict rulings, 16 measured prohibitions and a
NORMATIVE five-state vocabulary (COMPUTED, MEASURED ZERO, OMITTED,
UNSOURCED-ON-BUILD, EMBARGOED). Build the five-state token FIRST or it will be
flattened to a nullable number by the third panel. TWO PREREQUISITES LAND BEFORE
THE FIRST FRONTEND FILE: tools/ascii_guard.py (FROZEN, needs operator approval)
must gain .js, .html and .css; and docs/EMBARGO.json must exist, tracked, naming
time_to_kill as blocked on gap 7 - as a PUBLISHED artifact derived from
bloodforge/embargo.py, never a second source of truth.

THE THIRD TRACK - LINK INGEST STAGES 4 TO 7. docs/research/LINK_INGEST.md stage 4
is OPEN: 1 of 21 survivors dived, 1 unreachable, 1 read at source, 18 owed.
CCR-146 is REFUTED for RM - subagents DO receive CLAUDE.md, as a system-reminder
injection. Next is the binary-RE pair, the sharpest overturn in the corpus:
CCR-35 pyghidra-lite (8) and CCR-89 x64dbg (7). Gap 8 (reading a global ECS
constant that has never been read) is exactly their shape. STAGE 5 WARNING: a
previous fan-out truncated its challenge input at 12,000 chars and left 33
entries unchallenged. CHECK THE FAN-OUT'S OWN COVERAGE BEFORE BELIEVING IT.

THE FOURTH TRACK - HEADLESS. Phase 0a PASSES; the loop still does not exist. RM
is CLEAN on the model alias. LW reports rc-main STILL selected as of 1705, traced
to RC's budget_saver plus a live job state - RC's to fix, and a config key being
gone is not the same measurement as the behaviour being gone. RM's PreToolUse
gate FIRES headless under bypassPermissions and covers --no-verify. NOT MEASURED:
anything about a WORKTREE, three-way concurrency, or a contended acquire reaping
a stale lock. TWO CLI VERSIONS ARE LIVE: npm claude on PATH is 2.1.220, the
interactive desktop host is 2.1.219. Name which one produced any finding.

HOW TO PROBE ANYTHING, learned the hard way six times now.

A gate that stays silent because the probe gave it nothing to catch is
INDISTINGUISHABLE from a gate that is not wired. That happened AGAIN last
session: the recorder's arm reported player_resolved false because it consulted
a throttle it had just reset, and a decline looked exactly like an absence.
Before measuring whether a guard fires, CALL IT DIRECTLY and confirm it returns a
reason. Then pick a discriminator only one mechanism can satisfy.

FEED REAL RECORDED DATA THROUGH THE CODE, NOT JUST TESTS. 526 green tests did not
catch that powerstat.evaluate raised on statistics.median([]) for a series with
zero isolated deltas - which is what a flat recording is, and what a
prefab-latched recorder produces. One real file found it in one call.

CLEAR __pycache__ BEFORE BELIEVING A MUTATION-TEST REVERT. Mutating max( to sum(
and back gives the same file size; land inside the same mtime second and Python
reuses the mutated bytecode. Five tests kept failing against correct source.

COUNT THE ROWS, DO NOT READ THE PROSE DESCRIBING THEM. That discipline has now
moved a number four times: ability_stats 1474 to 1818, the link corpus 119 to
146, vblood_damage_modifier range to binary, and now the sample rate 4 Hz to
2 Hz on a host nobody had measured.

NEVER CALL A /-FLAGGED WINDOWS EXE FROM THE BASH TOOL. Git Bash MSYS
path-translation rewrites a leading-slash argument, so schtasks /query arrives as
schtasks C:/Program Files/Git/query and yields ZERO ROWS. Use the PowerShell tool
or a Python subprocess list. Same class: verify a field NAME before concluding a
field is absent.

Same shape on the game side: "ready":true means the PREFAB MAP settled, NOT that
the world has spawned its units. POLL FOR THE SUBJECT.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. No .sln. csproj lists every source explicitly.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. Client
  holds a flat plugins\RedMoon.Bridge.dll; server holds
  plugins\RedMoon.Bridge\RedMoon.Bridge.dll. Verify with matching SHA256.
- Server launch: VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver
  -saveName world1 -batchMode -nographics. The bridge answers at about 28 s of
  uptime and a live Dracula is resolvable immediately after.
- Never Stop-Process; taskkill /F through PowerShell.
- Your PowerShell tool is pwsh 7.6.4 Core. This does NOT relax the ASCII rule.
- Output to _scratch\rmprobe as saved JSON, not committed.
- The phase 1-3 payloads under _scratch\rmprobe\c3\ and c3p2\ are still on disk
  and answer most component and field-TYPE questions without launching anything.
- DO NOT BUILD A GENERIC VALUE READER. Attempted twice, both recorded as
  failures - managed reflection read 539327184 for every Int32, and raw il2cpp
  field offsets HARD CRASHED the dedicated server. Use TYPED accessors.

DEBT, unchanged. The promoted items table lost its 425 localization_guid values
because the dump was taken on the dedicated server, where that join resolves 0 of
425 by measurement. A HOST fact, not a regression. Backed up to
_scratch\rmprobe\c3p2\items-client-v3-with-localization.json; a client dump
refills them in about 100 ms - AND YOU WILL HAVE THE CLIENT UP FOR THE
EXPERIMENT, so this is nearly free. Also: six files still sit in
data/rmdata/<build>/tables/_incoming/ from an earlier run, so a reader cannot
tell promoted from pending. Also NEW: bloodforge/powerstat.py imports
isolated_deltas and per_hit_discard_reasons from tools/anchor_record.py, an
engine-imports-tool layering wart chosen over duplicating two functions that must
never drift; the fix is to move them to bloodforge/series.py.

TDD per CLAUDE.md: failing characterization or regression test first, then
implement, then verify at the tier the change earns before committing. A schema,
engine or ENGINE_VERSION change is Tier 2 - full suite plus a restart.
ENGINE_VERSION is 0.1.0+1.1.13.0-r99712; bump the semver when section 2, 3 or 4
math changes, and NEVER in the same commit as an unvalidated data change.

Launch build work via subagents per CLAUDE.md. They DO receive CLAUDE.md's hard
rules, so do not re-paste them. All three subagents last session reported
honestly and every count they claimed reproduced - but I re-ran all of them, and
two of the four corrections above came from MY review rather than from theirs. Do
not commit while an agent is live, read git show --stat after, and RE-RUN ANY
AGENT'S CLAIMED COUNTS, BUILDS AND FILE EXISTENCE YOURSELF.

End with /done, and print the next-session prompt inline.
```

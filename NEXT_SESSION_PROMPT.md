# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
LAUNCH THE V RISING CLIENT BEFORE YOU START THIS SESSION. Three sessions have
now opened scoped to the power-stat run and found no VRising process, no Steam
process and zero listeners across 8770-8790. The agent cannot launch the game,
cannot log into Steam and cannot cast the ability. If the client is not up and
you are not at the keyboard, say so in your first line and pick a second track
instead.

Cycle 3 - RUN THE POWER-STAT EXPERIMENT ON THE CLIENT. Everything around it is
built, deployed and verified live; the run itself is the whole session. Read
CLAUDE.md, MEMORY.md, ROADMAP.md, WAKEUP_NOTES.md, docs/BLOODFORGE.md,
docs/ANCHOR_RUNS.md (the operator procedure, followable end to end), and BOTH
cycle 3 specs - docs/superpowers/specs/2026-08-01-bloodforge-falsification-
design.md and docs/superpowers/specs/2026-08-01-bloodforge-combat-math-design.md
- then git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above, never from a hash written in a doc.
- Last verified, one run each: pytest 618 passed in 29.01s exit 0 (598 at the
  start of last session, +20: 8 from tests/test_licensing.py and 12 from
  tests/test_publish_next_session.py), ruff clean, ascii_guard exit 0. NO C#
  change last session, so the deployed DLLs still match. There is NO .sln -
  build
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj. csproj has
  EnableDefaultCompileItems=false, so a NEW .cs file must be added to the
  ItemGroup by hand or it silently will not compile.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. THIS IS NOW MACHINE-CHECKED over the whole history
  by tests/test_commit_history.py - 0 offenders over 135 commits at last run.
  Do not audit it with an ad-hoc grep; the gate anchors the pattern at line
  start and an unanchored grep returns a false positive on any commit message
  that merely discusses the trailer.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log.
- Never write a port literal - import from core/ports.py. That file is FROZEN and
  its allowlist test WILL catch a port named in a docstring.
- DO NOT run git lfs install (inert pre-push under core.hooksPath).
- data/rmdata/ is gitignored and regenerable. Promoted and count-ASSERTED: items
  425 (schema 4), recipes 663, abilities 54, vbloods 65 (schema 2), blood_types
  13, ability_stats 1818 (schema 1). 3,038 rows, 0 nulls.
- ops/loop/slots.py is byte-identical across three repos, pinned in
  tests/test_slots.py. MAX_CONCURRENT_SLOTS = 3. Nothing in RM calls it yet.
- THE REPO IS PUBLIC (api.github.com reports private=False) and is now licensed
  Apache-2.0 - LICENSE is the canonical text fetched verbatim, attribution and
  the Stunlock disclaimer are in NOTICE, and CLAUDE.md carries it as its FIRST
  hard rule. Two live constraints: never vendor Apache-2.0-incompatible code
  (GPL, AGPL, unlicensed snippets), and never commit game assets or extracted
  game data.
- pyproject.toml exists and is METADATA ONLY - license = "Apache-2.0", version
  pinned BY TEST to the release part of bloodforge.ENGINE_VERSION, NO
  [build-system], and NO [tool.pytest.ini_options] or [tool.ruff] because
  pytest.ini and ruff.toml both win over it. tests/test_licensing.py (8 tests)
  refuses those sections and checks LICENSE against the canonical Apache body
  rather than against another string reading "Apache-2.0".
- README.md IS NOW OUTWARD-FACING. It is written for a stranger landing on a
  public repo, not for you: no cycle numbers, no ledger, no doctrine. Keep it
  that way. The internal state lives in ROADMAP.md, WAKEUP_NOTES.md and
  docs/. It states plainly that the dashboard does not exist and that the
  power stat and boss max_health are WITHHELD rather than defaulted, so do not
  quietly make it claim more than ships.
- STEP 11 OF /done PUBLISHES THE PROMPT TO THE DESKTOP:
  python tools/publish_next_session.py. It reads the FENCED BLOCK out of
  NEXT_SESSION_PROMPT.md - so keep that file at EXACTLY TWO ``` lines - and
  writes Desktop/RM-NEXT-SESSION.txt atomically, then reads it back. It
  refuses on a missing or duplicated fence, a block under 2000 bytes, any
  non-ASCII, or an absent Desktop, and it writes no other filename because
  LW-NEXT-SESSION.txt and RC-NEXT-SESSION.txt on that Desktop belong to
  sibling projects. Before this existed the Desktop copy was 10 hours stale
  and described a 382-test suite.

THREE GATES LANDED LAST SESSION THAT WILL CHANGE HOW YOUR TOOLS BEHAVE. None is
a defect; each will look like one the first time it fires.

1. rmdata_ingest now REFUSES on a same-build VALUE change, keyed on prefab_guid,
   with the full old/new list printed first. Cycle 3 is where the dumper is under
   active development, so this is a NORMAL event here rather than an anomaly.
   Read the printed list, confirm it is the change you intended, then re-run with
   BOTH flags: --accept --accept-value-changes. An empty baseline is treated as
   NO baseline and prints NO PROMOTED BASELINE on disk - NOT CHECKED.
2. tests/test_collected_counts.py pins a per-module map of collected counts.
   ADDING TESTS FAILS IT BY DESIGN. Update PINNED in the same commit; that edit
   is the gate, not an obstacle to it.
3. The SessionStart banner now prints a third line, "Build agreement: MATCH". If
   it ever reads MISMATCH or NOT CHECKED, stop and fix that before trusting any
   number in data/rmdata/.

THE MAIN TRACK - ONE RUN, AT THE CLIENT, AND IT IS THE WHOLE SESSION.

P(G), the power stat, is UNDEFINED and therefore every damage number Bloodforge
can compute is absent. Exactly ONE row in 1818 can decide it:

  name          AB_Unholy_WardOfTheDamned_AbilityGroup
  prefab_guid   -1136860480
  spell_school  unholy      <- H2 predicts SpellPower
  damage_type   physical    <- H1 predicts PhysicalPower
  coefficient   1.0         <- exactly 1.0, no arithmetic to get wrong
  hits_per_cast 1           <- no multi-hit aliasing
  ability_type  SpellSlot2  <- player-castable, on the bar

The prediction is literally "the observed health delta equals one of the two
power stats". It needs NO boss, NO V Blood and NO health denominator.

THE PROCEDURE. docs/ANCHOR_RUNS.md run 1.

  python tools/find_target.py --host client

lists SPAWNED units over /dump/components?instanced=1 and MARKS V Bloods and
prefab rows rather than dropping them. Pick an unmarked row. Then arm:

  python tools/anchor_record.py start --guid <GUID> --note "power stat H1 vs H2"

CHECK THE ARM RESPONSE BEFORE CASTING. player_resolved must be true,
player_unit_stats must be present, carries_prefab_marker must be false, AND
PhysicalPower must NOT equal SpellPower - measured 10 and 10 on a fresh
character, on which both hypotheses predict the same number and the run is
INDETERMINATE however clean the data. Equip a real weapon; 203 of 205 grant
PhysicalPower and no SpellPower. subject_not_spawned means poll for the SUBJECT,
never for ready:true.

Then cast the Ward ALONE, with a pause between casts, about 30 times. Do not
weave weapon attacks in - a window containing two applications is DISCARDED, not
averaged. The target must SURVIVE the hit and must not be a V Blood.

  python tools/anchor_record.py stop --out data/anchors/
  python -m bloodforge.powerstat data/anchors/<run_id>.json

FREE WINS WHILE THE CLIENT IS UP: the client sample rate (ROADMAP gap 12 -
MEASURED 1.99 Hz on the dedicated server at 29.9 fps, client still unmeasured,
your run measures it for free), and the items localization_guid backfill (0 of
425 from the server dump, a client dump refills them in about 100 ms).

STATE THE CAVEAT IN THE LEDGER: one row is a sample of one. A pass says which
hypothesis survives on THIS ability and does not prove the rule corpus-wide. It
is the only evidence the build affords - ZERO rows are is_weapon_ability with a
non-physical damage_type and a nonzero coefficient, so the weapon side is dead by
EXHAUSTION rather than by sampling.

MEASURED FACTS THAT CONSTRAIN THE MATH. Do not re-derive.

1. THE SAMPLE RATE IS HOST-DEPENDENT. SampleEveryFrames = 15 is a FRAME count.
   1.99 Hz measured on the server. The A.5 gap check is 3x the OBSERVED median
   interval, never a hardcoded 750 ms.
2. THE DAMAGE BLOCK IS ALL-OR-NOTHING. Zero of 732 damage rows omit a
   coefficient. 563 links, 409 to a damage group, 154 to 15 groups with NO
   DAMAGE BLOCK AT ALL.
3. 60 OF 732 DAMAGE GROUPS ARE UNPRICEABLE AFTER THE EXPERIMENT, NOT 42. 27 holy
   and 15 fire blocked on resistance (gap 8); 18 corruption blocked on POWER
   (gap 13) - all 18 carry neither spell_school nor is_weapon_ability, so both
   hypotheses are SILENT on them.
4. reduction() IS A PARTIAL FUNCTION: physical 0.0 on all 65, spell 0.0 on all
   65, corruption 0.5 on all 65, fire and holy UNDEFINED. DO NOT AVERAGE THEM.
5. THE DPS CYCLE IS A MAX, NOT A SUM: max(cast_time + post_cast_time, cooldown,
   global_cooldown). cooldown is 0 on 352 of 1818 rows, which forces the max
   form. Mutating to a sum fails five tests.
6. GAP 10 - 154 of 563 weapon links reach nothing, including two of the DEFAULT
   weapon's three abilities, so ANY GreatSword DPS is PRIMARY-ONLY.
7. GAP 11 - ability_type IS NOT A SLOT DISCRIMINATOR. All 36 weapon groups
   carrying one report Secondary. Derive slot from the weapon-to-group link.
8. FOUR TERMS ARE EFFECTIVELY CONSTANT. hit_triggers 0 on ALL 732.
   multiply_main_factor_with_stacks false on all 732. raw_damage_value nonzero
   on 1 row, raw_damage_percent on 1, damage_modifier_per_hit on 3.
9. THE GOLEM STORY IS COHERENT ACROSS THREE FIELDS. AB_Shapeshift_Golem_T02_Group
   has coefficient 0 AND raw_damage_percent 0.3. WHICH POOL is UNSOURCED.
10. BOSS max_health IS INSTANCE-ONLY. 8107 reproduces at n=3 across three boots
    and three entity indices against 0 on the prefab every time.
11. vblood_damage_modifier IS BINARY: 1.0 on 728, 0.33 on 4, 1.0 on ALL 409
    weapon-linked rows.
12. physical_power EQUALS spell_power on all 65 boss rows over 33 levels.
13. GameDifficulty is an INTEGER in difficulty/*.json and a STRING in
    ServerGameSettings.json. Joining on it across the two returns nothing.
14. GAP 8a - NO SECOND SOURCE FOR ANY COMBAT NUMBER EXISTS. Enumerated over all
    64 V Rising Fandom wiki boss pages: no health, no hp, no resistance
    parameter on ANY page, 24 of 64 have no infobox at all, and every free-text
    health mention is a phase threshold in PERCENT. The wiki infobox unit_id IS
    RM's prefab_guid though - joined 40 of 40, and LEVEL agrees 40 of 40, the
    first independent second-source confirmation of anything in data/rmdata/, of
    IDENTITY and LEVEL only.
15. GAP 8b - NOTHING ATTRIBUTES A RECORDED HEALTH DELTA TO AN ABILITY. RUN 1
    dodges it by constraining the operator to one ability. RUN 2, a real V Blood
    fight, has NO mechanism. The honest instrument is a bridge-side
    ability-application read on the same tick, not a video.

THE SECOND TRACK - CYCLE 4, PLANNED AND UNBUILT. Do NOT open it in the same
session as the experiment. ADR-008 rules the stack: server-rendered HTML from a
Python stdlib server, about 200 lines of vanilla JS, inline SVG, NO framework and
NO build step. docs/research/DASHBOARD_CONCEPTS.md holds 30 adjudicated concepts,
a ranked 7-item slice, 7 conflict rulings, 16 measured prohibitions and a
NORMATIVE five-state vocabulary (COMPUTED, MEASURED ZERO, OMITTED,
UNSOURCED-ON-BUILD, EMBARGOED). Build the five-state token FIRST or it will be
flattened to a nullable number by the third panel. TWO PREREQUISITES LAND BEFORE
THE FIRST FRONTEND FILE: tools/ascii_guard.py (FROZEN) must gain .js, .html and
.css; and docs/EMBARGO.json must exist, tracked, naming time_to_kill as blocked
on gap 7, derived from bloodforge/embargo.py and never a second source of truth.

THE THIRD TRACK IS CLOSED. Do not reopen it. RM's link ingest finished all seven
stages on 2026-08-01: 146 extracted, 146 scored, 21 dived, 0 at 7 or above, ZERO
TOOLS ADOPTED, and 4 work items shipped (S7.2, S7.5, S7.1, S7.3, plus S7.5's
operator-approved print half). S7.4 was DROPPED, S7.6 (a Stop hook) is DEFERRED
as an unmeasured need, S7.7 (worktree slices, cached node DAG) is BLOCKED on
RC's headless plan. The track's product was never a dependency; it was the
corrections its measurements forced.

THE FOURTH TRACK - HEADLESS. Phase 0a PASSES; the loop still does not exist. RM
is CLEAN on the model alias. RM's PreToolUse gate FIRES headless under
bypassPermissions and covers --no-verify. NOT MEASURED: anything about a
WORKTREE, three-way concurrency, or a contended acquire reaping a stale lock.
DECLARED WORKTREE ISOLATION HAS FAILED HERE TWICE - an agent wrote into the MAIN
tree while git worktree list showed no second tree - so isolation must be
VERIFIED at run time: assert git -C <slice> rev-parse --show-toplevel resolves to
the slice and NOT the main tree.

HOW TO PROBE ANYTHING, learned the hard way.

A NULL FROM AN INSTRUMENT THAT CANNOT PRODUCE A POSITIVE IS NOT EVIDENCE OF
ABSENCE. The 2026-07-26 console investigation filtered for cmd.exe while the real
children were schtasks.exe and git.exe, polled 120 s against a once-per-session
event, and used Win32_Process, which carries no console or window field at all.
It cleared Red Moon on evidence that could not have convicted it. NEWEST
INSTANCE, 2026-08-01: the co-author history scan would have reported a clean zero
over 135 EMPTY message bodies, so it now asserts that HEAD's record actually
contains HEAD's subject read through a second git format.

TWO EQUAL FAILURES ARE NOT AN AGREEMENT. rm_facts returns the sentinels "not
installed", "unparseable" and "none extracted" instead of raising, and two of
them compared to each other are EQUAL - so the obvious installed == extracted
reports a machine with no game installed as a perfect MATCH. Reject the failure
values BEFORE comparing, every time this shape appears.

DO NOT AUDIT A GATE WITH A DIFFERENT PREDICATE THAN THE GATE USES. A bash
grep -ci for the co-author trailer returned 1 while the real gate returned 0; the
grep was unanchored where the predicate anchors at line start.

A SOURCE IS UNREACHABLE ONLY AFTER TWO DIFFERENT ROUTES FAIL. Recorded twice:
WebFetch returned HTTP 402 on a Fandom page whose api.php returned 200, and
"CCR-135 is a Reddit post, unreachable" was github.com/Ark0N/Codeman all along.
Reddit itself: www is an 8 KB JS shell and .json is 403, but old.reddit.com
serves the full body - and the post is the LARGEST div.md, not the first.

AN ACCEPTANCE CRITERION MUST DESCRIBE A FAILURE THE TEST MUST PRODUCE, never the
feature. Every clause phrased as an absence of output - "stands down", "is
silent", "sources from the right file" - is satisfied by a no-op.

AN EXEMPTION IS A PLACE TO BE WRONG. An AST auditor that exempted sys.executable
spawns whitelisted precisely the one site that was broken, twice over.

A TEST THAT SCANS ITS OWN SOURCE WILL MATCH ITSELF. A guard asserting "this
module compiles no pattern of its own" searched its own text for the name of the
thing it forbids and failed on a clean file. Use an AST walk, which does not see
inside string literals.

COUNT THE ROWS, DO NOT READ THE PROSE DESCRIBING THEM. Moved a number seven times
now: ability_stats 1474 to 1818, the link corpus 119 to 146,
vblood_damage_modifier range to binary, the sample rate 4 Hz to 2 Hz, gap 8 from
an RE problem to a typed accessor, the build pin from "~97 tracked sites" to 120
inside a test's own docstring, and the unpriceable damage groups 42 to 60.

FEED REAL RECORDED DATA THROUGH THE CODE, NOT JUST TESTS. 526 green tests did not
catch that powerstat.evaluate raised on statistics.median([]). One real file
found it in one call.

CLEAR __pycache__ BEFORE BELIEVING A MUTATION-TEST REVERT.

NEVER CALL A /-FLAGGED WINDOWS EXE FROM THE BASH TOOL. MSYS path translation
rewrites a leading-slash argument, so schtasks /query yields ZERO ROWS. Use the
PowerShell tool or a Python subprocess list. Same family, different cause: never
interpolate a real NUL into an argv on Windows - CreateProcess takes one command
line STRING and a NUL truncates it. Pass git's %x00 escape and split the OUTPUT.

"ready":true means the PREFAB MAP settled, NOT that the world has spawned its
units. POLL FOR THE SUBJECT.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. No .sln.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. Client
  holds a flat plugins\RedMoon.Bridge.dll; server holds
  plugins\RedMoon.Bridge\RedMoon.Bridge.dll. Verify with matching SHA256.
- Server launch: VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver
  -saveName world1 -batchMode -nographics. Bridge answers at about 28 s uptime.
- Never Stop-Process; taskkill /F through PowerShell.
- Your PowerShell tool is pwsh 7.6.4 Core. This does NOT relax the ASCII rule.
- Output to _scratch\rmprobe as saved JSON, not committed.
- HOOK SCRIPTS SPAWNING A CONSOLE EXE MUST PASS creationflags=NO_WINDOW. Fixed
  2026-08-01 across rm_facts.py, precommit_gate.py and pytest_guard.py, all
  FROZEN, with operator approval. tests/test_hook_consoles.py enforces it with NO
  exemption. Reason: pythonw.exe is GUI-subsystem so a hook has no console, and a
  console child of a console-less parent ALLOCATES one - which also stole the
  ruff gate's stdout and silently passed every commit for the life of the file.
- DO NOT BUILD A GENERIC VALUE READER. Attempted twice, both recorded as
  failures - managed reflection read 539327184 for every Int32, and raw il2cpp
  field offsets HARD CRASHED the dedicated server. Use TYPED accessors.

DEBT. The promoted items table lost its 425 localization_guid values because the
dump was taken on the dedicated server, where that join resolves 0 of 425 by
measurement. A HOST fact, not a regression. Backed up to
_scratch\rmprobe\c3p2\items-client-v3-with-localization.json; a client dump
refills them in about 100 ms - AND YOU WILL HAVE THE CLIENT UP.

TDD per CLAUDE.md: failing characterization or regression test first, then
implement, then verify at the tier the change earns. Tier 2 is schema, engine or
ENGINE_VERSION - full suite plus a restart. ENGINE_VERSION is
0.1.0+1.1.13.0-r99712; bump the semver when section 2, 3 or 4 math changes, and
NEVER in the same commit as an unvalidated data change.

Operator standing execution mode: keep the inline session free, perform work with
headlessly-orchestrated multi-agent parallel self-adjudicated adversarial
looping, and print a paste-ready block at /done. Subagents DO receive CLAUDE.md's
hard rules as a system-reminder injection, so do not re-paste them. RE-RUN ANY
AGENT'S CLAIMED COUNTS, BUILDS AND FILE EXISTENCE YOURSELF. The last two
sessions both ran INLINE rather than fanning out, correctly per R9 - four items
over six files, then a four-file docs change - and the earlier of the two still
found three defects in its own work by re-running its own numbers.

ONE MORE FROM THE LICENSE SESSION: NO GATE IN THIS PROJECT LOOKS OUTWARD. The
repo sat public with no LICENSE, meaning all rights reserved, for its whole
life, and 598 tests plus every hook had nothing to say about it because they all
check the code against itself. When something feels like it should already have
been caught, ask whether any instrument here was ever pointed at it.

End with /done, and print the next-session prompt inline.
```

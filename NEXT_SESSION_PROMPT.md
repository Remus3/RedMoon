# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 PHASE 2 - THE COMBAT MATH SPEC. Gap 7 is settled, so this is now
unblocked and it is the priority. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/BLOODFORGE.md, docs/adr/ADR-007-* and ADR-008, and
docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md, then
git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING - it is a live
sibling channel and it moved seven times during one session recently.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above, never from a hash written in a doc.
- Last verified, one run each: pytest 382 passed in 19.60s exit 0, ruff clean,
  ascii_guard exit 0. The C# side was NOT rebuilt last session (no C# changed);
  dotnet build -c Release -t:Rebuild on
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj was 0/0 the session before.
  There is NO .sln - build the csproj.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. Audited clean across every surface 2026-08-01.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log.
- Never write a port literal - import from core/ports.py. That file is FROZEN.
- DO NOT run git lfs install (inert pre-push under core.hooksPath).
- data/rmdata/ is gitignored and regenerable. Promoted and count-ASSERTED:
  items 425 (schema 4), recipes 663, abilities 54, vbloods 65 (schema 2),
  blood_types 13, ability_stats 1818 (schema 1). 3,038 rows total. A dump that
  disagrees is REFUSED by tools/rmdata_ingest.py.
- ops/loop/slots.py is byte-identical across three repos, sha256 5297f2d0...,
  7154 bytes, pinned in tests/test_slots.py. MAX_CONCURRENT_SLOTS = 3. DO NOT
  EDIT outside a coordinated round. Nothing in RM calls the governor yet.

THE MAIN TRACK - WRITE THE COMBAT MATH SPEC.

GAP 7 IS SETTLED, NOT DISCHARGED. Read the falsification spec first and treat
its five decisions as binding. Decision A is OPERATOR-RULED: the anchor is a
bridge-side boss Health.Value time series via a new /record/* endpoint, NOT a
hand-timed recording and NOT polled /dump/statcontrol (that walks every entity
per request against a measured 95 ms full scan, under a one-at-a-time gate).
The sample ceiling is 4 Hz, set by SampleEveryFrames = 15 in Plugin.cs:41, and
it is a constraint the tolerances were computed against, not a knob.

THE EMBARGO IS PER FIELD AND IT IS THE POINT. dps lifts on the per-hit gate
alone. ehp lifts on the EHP gate. ttk_seconds needs both plus three comparable
runs, because only it needs the instance-only health denominator. Until then all
three are DECLARED AND NEVER EMITTED - the key is ABSENT, not null, not 0, not
-1 - following the items.tier / max_health / power_stat idiom. The spec names
six enforcement mechanisms including tests/test_embargo.py. BUILD THE EMBARGO
GATE BEFORE ANY MATH, so the math cannot leak while it is being written.

NINE MEASURED FACTS THAT CONSTRAIN THE MATH. Each silently produces a wrong
number if forgotten. Do not re-derive them.

1. BOSS max_health DOES NOT EXIST ON THE PREFAB. 19 typed fields compared
   between the Dracula prefab (29012) and its live instance (322945): 17
   IDENTICAL, Health.MaxHealth 0 against 8107. NOT spawn scaling - 0 to 8107 is
   not a ratio - so there is no factor to recover. A TTK denominator needs a
   live world with the boss spawned. UNVERIFIED and it matters: under WHAT
   DIFFICULTY was 8107 measured? Brutal multiplies V Blood MaxHealth by 1.25.
2. THE FOUR RESISTANCES ARE NOT COMMENSURABLE. physical and spell are float
   resistances reading 0 on all 65; fire is an integer RATING (0 to 75) on only
   4 of 65 bosses; corruption is already a reduction at 0.5 on all 65. DO NOT
   average them. Holy, Silver, Garlic and Sun have NO unit-side field and are
   omitted, never zeroed.
3. NEW - ROADMAP GAP 8. THE FIRE RATING CANNOT BE CONVERTED TO A REDUCTION.
   ResistanceData.FireResistance_DamageReductionPerRating is enumerated at
   BRIDGE_SPIKES.md:943 as a DECLARED member and its VALUE HAS NEVER BEEN READ -
   not in data/rmdata/, not by the plugin (comment only, PrefabDumper.cs:1153),
   not in difficulty/. The one resistance that varies across the 65 is the one
   RM cannot price. Reading it is a candidate first task for this session.
4. NEW - ROADMAP GAP 9. BOSS LEVEL, POWER AND HEALTH ARE DIFFICULTY-SCALED, so
   vbloods.json is implicitly a NORMAL table. Brutal is {LevelIncrease 3,
   MaxHealthModifier 1.25, PowerModifier 1.7}; Easy is {0, 0.8, 0.6}. Difficulty
   is a THIRD subject-vector axis and it is the only one fully sourced on disk.
5. power_stat IS PROVEN ABSENT. 51 components enumerated on the _Hit entity and
   MainType is the only discriminator. The math spec must establish it
   EMPIRICALLY - do not infer it from damage_type. The per-hit 2 percent gate IS
   the experiment: predict a hit under each hypothesis and see which survives.
6. vblood_damage_modifier IS BINARY, NOT A RANGE. Corrected 2026-08-01 by
   counting: 1.0 on 728 of 732 rows, 0.33 on exactly 4, all golem-form NPC
   abilities, and 1.0 on ALL 409 weapon-linked damage rows. It is INERT for
   loadout coaching. Implement it anyway - being 1.0 almost everywhere is what
   makes an omission invisible in 99.5 percent of cases while silently tripling
   golem builds. It enters computation only with a regression test pinned to
   those four rows on the same commit.
7. physical_power EQUALS spell_power on all 65 rows with 33 distinct values over
   33 distinct levels, so both are LEVEL-DERIVED, not per-boss authored.
   Displaying them as two independent boss attributes implies information that
   is not there.
8. THE WEAPON SURFACE IS NARROWER THAN "563 LINKS" SUGGESTS. 563 is the EDGE
   count. It fans out from 205 weapons (220 items carry zero links, 171 carry
   exactly 3) into only 47 DISTINCT ability groups, of which 32 reach damage.
   409 edges reach a damage group and 154 reach one whose coefficient is
   OMITTED. is_weapon_ability is true on 42 of 1818, 26 of which reach damage.
   Weapon DPS is a model over ~32 groups, not 732.
9. A REAL 0.0 AND AN OMITTED VALUE SIT ONE ROW APART. AB_Vampire_Longbow_Primary
   _AbilityGroup - the player's basic longbow attack - has its coefficient
   OMITTED, while AB_Spear_AThousandSpears_Stab carries a real 0. Any consumer
   that conflates them is wrong about the most common weapon in the game.
   Also: 27 ability groups deal holy damage and NO boss carries any holy field.

THE SECOND TRACK - CYCLE 4, WHICH IS PLANNED AND UNBUILT.

Do NOT open this in the same session as the combat math. It is here so you do
not re-plan it. ADR-008 rules the stack: server-rendered HTML from a Python
stdlib server on 8778, about 200 lines of vanilla JS, inline SVG, NO framework
and NO build step. docs/research/DASHBOARD_CONCEPTS.md holds 30 adjudicated
concepts, a ranked 7-item slice, 7 conflict rulings, 16 measured prohibitions
and a NORMATIVE five-state vocabulary (COMPUTED, MEASURED ZERO, OMITTED,
UNSOURCED-ON-BUILD, EMBARGOED). Build order starts with the five-state token,
because if it is invented per-panel it will be flattened to a nullable number by
the third panel.

TWO PREREQUISITES LAND BEFORE THE FIRST FRONTEND FILE, NOT AFTER:
- tools/ascii_guard.py (FROZEN, needs operator approval) must gain .js, .html
  and .css. It covers 11 suffixes and not those three, so cycle 4 would ship
  RM's first authored files outside its own 7-bit-ASCII hard rule.
- docs/EMBARGO.json must exist, tracked, naming time_to_kill as blocked on gap 7
  with its lifting criterion stated.

OPEN QUESTIONS THE OPERATOR STILL OWES AN ANSWER ON. Each has its settling
measurement written down in DASHBOARD_CONCEPTS.md section 7 or the gap 7 spec
section 7. The two sharpest: does a fifth `provenance` key actually pass the
frozen validate_table (REASONED, NEVER PROBED - probe it before editing
ingest), and which difficulty is the default subject axis.

THE THIRD TRACK - LINK INGEST STAGES 4 TO 7. docs/research/LINK_INGEST.md

Stage 4 is OPEN: 1 of 21 survivors dived, 1 unreachable, 1 read at source, 18
owed. CCR-146 is REFUTED for RM - subagents DO receive CLAUDE.md, as a
system-reminder injection rather than in the system prompt proper, measured with
zero tool calls on CLI 2.1.219. Next is the binary-RE pair, the sharpest overturn
in the corpus: CCR-35 pyghidra-lite (8) and CCR-89 x64dbg (7). Verify
pyghidra-lite handles IL2CPP-flavoured PE and that driving x64dbg is safe against
a live game process. These reduce the per-patch cost that got the BACKLOG
offline-blob-parser item rejected, and gap 8 (reading a global ECS constant that
has never been read) is exactly their shape.

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
shared governor.

TWO CLI VERSIONS ARE LIVE ON THIS BOX. The npm claude on PATH is 2.1.220; the
interactive desktop host is 2.1.219. Any RM finding about harness behaviour must
name which one produced it.

HOW TO PROBE ANYTHING, learned the hard way four times now.

A gate that stays silent because the probe gave it nothing to catch is
INDISTINGUISHABLE from a gate that is not wired. Before measuring whether a
guard fires, CALL IT DIRECTLY FIRST and confirm it returns a reason. Then pick a
discriminator only one mechanism can satisfy.

NEVER CALL A /-FLAGGED WINDOWS EXE FROM THE BASH TOOL. Git Bash MSYS
path-translation rewrites a leading-slash argument into a Windows path, so
schtasks /query arrives as schtasks C:/Program Files/Git/query, exits 1, and the
pipeline yields ZERO ROWS. That produced a confident false "RM-DataRefresh is
not installed" that an adversarial agent then designed a whole section around.
Use the PowerShell tool, or a Python subprocess list. Same class: verify a field
NAME before concluding a field is absent - items.stats entries are
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
  -saveName world1 -batchMode -nographics. Poll http://127.0.0.1:8780/health.
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
data/rmdata/<build>/tables/_incoming/ from the last run, so a reader cannot tell
promoted from pending. And ENGINE_VERSION has NO definition anywhere in code
despite ROADMAP and BLOODFORGE describing it as pinned - the combat-math spec
must create it.

TDD per CLAUDE.md: failing characterization or regression test first, then
implement, then verify at the tier the change earns before committing. A
schema, engine or ENGINE_VERSION change is Tier 2 - full suite plus a restart.

Launch build work via subagents per CLAUDE.md. They DO receive CLAUDE.md's hard
rules (measured 2026-08-01), so do not re-paste them into every prompt. But note
a worktree-isolated agent has twice written into the MAIN tree while git
worktree list showed no second tree. Do not commit while an agent is live, read
git show --stat after, and RE-RUN ANY AGENT'S CLAIMED COUNTS, BUILDS AND FILE
EXISTENCE YOURSELF - two subagent claims were refuted last session, and one of
the main agent's own probes was refuted by a subagent's.

End with /done, and print the next-session prompt inline.
```

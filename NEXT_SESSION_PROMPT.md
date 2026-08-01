# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 4 DASHBOARD and cycle 3 PHASE 2 (combat math). Operator-directed
2026-08-01: these two were deferred to this session. Read CLAUDE.md, MEMORY.md,
ROADMAP.md, WAKEUP_NOTES.md, docs/research/LINK_INGEST.md, docs/BLOODFORGE.md
and docs/adr/ADR-007-*, then git log --oneline -8. CHECK moon_sync_inbox/ BEFORE
PLANNING - it is a live sibling channel and it moved four times during the last
session alone.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above, never from a hash written in a doc.
- Last verified, one run each: pytest 382 passed, ruff clean, ascii_guard exit
  0, dotnet build -c Release -t:Rebuild on
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj at 0 warnings 0 errors. There
  is NO .sln - build the csproj.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. AUDITED 2026-08-01 across every surface and clean:
  0 of 106 commits on origin/master, project .claude/, user-level commands and
  plugins, and there is no .github/ at all.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log.
- Never write a port literal - import from core/ports.py. That file is FROZEN.
- DO NOT run git lfs install (inert pre-push under core.hooksPath).
- data/rmdata/ is gitignored and regenerable. Promoted and count-ASSERTED:
  items 425 (schema 4), recipes 663, abilities 54, vbloods 65 (schema 2),
  blood_types 13, ability_stats 1818 (schema 1). A dump that disagrees is
  REFUSED by tools/rmdata_ingest.py.
- ops/loop/slots.py is byte-identical across three repos, sha256 5297f2d0...,
  7154 bytes, pinned in tests/test_slots.py. MAX_CONCURRENT_SLOTS = 3, agreed
  and applied by all three projects 2026-08-01. DO NOT EDIT outside a
  coordinated round. Nothing in RM calls the governor yet.

TRACK A - CYCLE 4 DASHBOARD, port 8778, ZERO implementation today.

It exists only in core/ports.py, ADR-003 and docs. Nothing is built.

The operator's steer, from their own note on CCR-120: NOT a rehash of RC's Loop
Monitor. They want categorized, agent-adjudicated UI/UX concepts for the project
as a whole. Two scored references are waiting in docs/research/LINK_INGEST.md:
CCR-135 Codeman (7), which the operator named as the stronger, and CCR-120
claude-task-viewer (6) for its OBSERVER posture - it renders state it does not
own, over SSE rather than poll-and-repaint, with dependency edges, cross-session
fuzzy search and stale-session auto-archive.

UNDECIDED AND IT SHOULD BE DELIBERATE: cycle 4 has NO declared frontend stack.
Server-rendered HTML and a JS framework are both open. That choice changes the
score of at least one corpus entry (CCR-04, 2 today and about 5 with a
framework) and should be made explicitly rather than emerging from the first
file written.

R2 applies: runtime state comes from curl against the API or from reading
ops/runtime/health.json. Never screenshot to read a number. R3: visual tools are
only for rendered-pixel, CSS and layout checks.

TRACK B - CYCLE 3 PHASE 2, THE COMBAT MATH SPEC.

The input spike is CLOSED (phases 1-3, ADR-007). Do not re-open it and do not
re-derive its measurements.

GAP 7 IS THE GATE AND IT IS NOT OPTIONAL. Red Moon has NO ground-truth anchor
for a computed DPS, EHP or TTK. Every acceptance criterion the input spike
passed was about SOURCING INPUTS, so all six could pass with a confidently wrong
answer. SETTLE THIS BEFORE WRITING COMBAT MATH. DO NOT PUBLISH A TTK TO ANY
SURFACE until it and the default-subject-vector item in BACKLOG.md are settled.
The link ingest surfaced plumbing for an anchor but no anchor: CCR-39/84
(MediaWiki and Fandom as an independent second source for boss numbers) and
CCR-123 (a fully local narrated-recording pipeline for hand-timing a real kill).
Neither IS the anchor. A real recorded kill still has to happen.

FOUR MEASURED FACTS THAT CONSTRAIN THE MATH. Each silently produces a wrong
number if forgotten.

1. BOSS max_health DOES NOT EXIST ON THE PREFAB. 19 typed fields compared
   between the Dracula prefab (29012) and its live instance (322945): 17
   IDENTICAL, Health.MaxHealth 0 against 8107. NOT spawn scaling - 0 to 8107 is
   not a ratio - so there is no factor to recover. DECLARED AND NEVER EMITTED. A
   TTK denominator needs a live world with the boss spawned.
2. THE FOUR RESISTANCES ARE NOT COMMENSURABLE. physical and spell are float
   resistances reading 0 on all 65; fire is an integer RATING (0 to 75) that
   becomes a reduction only through the GLOBAL
   ResistanceData.FireResistance_DamageReductionPerRating; corruption is already
   a reduction at 0.5 on all 65. DO NOT average them. Holy, Silver, Garlic and
   Sun have NO unit-side field and are omitted, never zeroed.
3. power_stat IS PROVEN ABSENT. 51 components enumerated on the _Hit entity and
   MainType is the only discriminator. The spike spec PRE-DECIDED the fallback:
   proven absent FROM DATA, so the math spec must establish it EMPIRICALLY. Do
   not infer it from damage_type.
4. vblood_damage_modifier RANGES 0.33 TO 1.0
   (DealDamageParameters.MaterialModifiers.VBlood) and multiplies boss damage
   directly. Omitting it misstates every boss TTK by up to 3x.

Also: physical_power EQUALS spell_power on all 65 rows with 33 distinct values
over 33 distinct levels, so both are LEVEL-DERIVED, not per-boss authored. And
27 abilities deal holy damage against which no boss carries any resistance field.

TRACK C - THE LINK INGEST, stages 4 to 7. docs/research/LINK_INGEST.md

Stages 1-3 are DONE: 146 of 146 extracted and scored, threshold 6+, 21
survivors, 125 culled. THE CORPUS IS 146, NOT the 119 every earlier pass
reported - the source header, its ranked index and its distribution all stop at
CCR-119 while full entries run to CCR-146.

STAGE 4 HAS NOT RUN AND NOTHING MAY BE ADOPTED BEFORE IT DOES. Every score so
far is against a one-line summary written by someone else for someone else,
which is exactly the secondhand claim this project refuses everywhere else. Read
the actual source before adopting anything.

START STAGE 4 WITH CCR-146, because it is a correctness question about RM
itself rather than a feature: custom subagents reportedly do NOT inherit the
main agent's system prompt - theirs is the agent file body alone. RM runs a
verifier subagent and keeps its hard rules (7-bit ASCII, no co-author trailer,
frozen files) in CLAUDE.md. If those never reach a subagent, RM's subagents have
been running without them. UNVERIFIED.

Then the binary-RE pair, which is the sharpest overturn in the corpus: CCR-35
pyghidra-lite (8) and CCR-89 x64dbg (7). Verify pyghidra-lite handles
IL2CPP-flavoured PE and that driving x64dbg is safe against a live game process.
These reduce the per-patch cost that got the BACKLOG offline-blob-parser item
rejected.

STAGE 5 WARNING: a previous fan-out truncated its challenge input at 12,000
chars and left 33 entries unchallenged, and every apparent survivor was an
artifact of that gap. CHECK THE FAN-OUT'S OWN COVERAGE BEFORE BELIEVING IT.

TRACK D - HEADLESS. Phase 0a PASSES. The loop does not exist.

Both previously recorded blockers were WRONG and are retracted. There was no
authentication failure. The trust failure was a PATH-SEPARATOR MISMATCH:
.claude.json held C:\RedMoon = True and C:/RedMoon = False, and headless reads
the forward-slash key, so it discarded all 13 permissions.allow entries. FIXED.
The second blocker was a machine-wide "model": "rc-main" belonging to a sibling,
since deleted by its owner.

MEASURED: RM's own PreToolUse gate FIRES headless under bypassPermissions on CLI
2.1.220 AND covers --no-verify. Doctrine corrected - "the Claude-side gate
cannot fire under --no-verify" is true of the commit-msg hook (which strips the
trailer through git) and FALSE of the PreToolUse ASCII gate, which sits above
git and is the only cover for that channel. Git hooks remain the floor because
they survive a human typing git in a terminal.

NOT MEASURED: anything about a WORKTREE. RM's gate resolves the repo from the
-C segment carrying the commit verb and that path has never been exercised.
Also unmeasured everywhere: three-way concurrency, and whether a contended
acquire reaps a stale lock in a live run.

Next action here is the loop itself, and it is the first thing that will ever
call the shared governor.

HOW TO PROBE ANYTHING, learned the hard way twice in one session.

A gate that stays silent because the probe gave it nothing to catch is
INDISTINGUISHABLE from a gate that is not wired. One probe staged a non-ASCII
file under _scratch/ - which is on ascii_guard's own skip list - the commit
succeeded, and it read exactly like "no gate fired". Before measuring whether a
guard fires, CALL IT DIRECTLY FIRST and confirm it returns a reason. Then pick a
discriminator that only one mechanism can satisfy: --no-verify bypasses the git
hook, so anything still blocking must be the agent layer.

Same shape on the game side: "ready":true means the PREFAB MAP settled, NOT that
the world has spawned its units. A live boss did not exist at 5 s of server
uptime and did exist at 20 s. POLL FOR THE SUBJECT, not just for readiness.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. There is no .sln.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. Today
  the client tree holds a flat plugins\RedMoon.Bridge.dll and the server tree
  holds plugins\RedMoon.Bridge\RedMoon.Bridge.dll - one per host, correct.
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

DEBT: the promoted items table lost its 425 localization_guid values because the
dump was taken on the dedicated server, where that join resolves 0 of 425 by
measurement. A HOST fact, not a regression. Backed up to
_scratch\rmprobe\c3p2\items-client-v3-with-localization.json; a client dump
refills them in about 100 ms.

TDD per CLAUDE.md: failing characterization or regression test first, then
implement, then verify at the tier the change earns before committing.

Launch build work via subagents per CLAUDE.md, but note a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself.

End with /done, and print the next-session prompt inline.
```

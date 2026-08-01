# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-08-01 (third stretch) - The slot round, a corpus that was 146 not 119, and two probes that lied before they told the truth

Branch `master`. Ledger 003i. Commits `5609509`, `5665b1a`, `f50881e` and
`bb59300` (the living docs and this entry). **NO ROADMAP ITEM CLOSED** - this is the
non-roadmap track, run after 003h closed the Bloodforge input spike earlier the
same day. Operator-directed order: ingest, headless, dashboard.

State at close, one run each: `python -m pytest` **382 passed in 19.50s, exit
0**, `python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0.

**THE SLOT ROUND CLOSED AND RM WAS NOT THE ONE CARRYING THE RED.** LW cleared
its GPU blocker, corrected its own reasoning unprompted - the bucket models
ANTHROPIC ACCOUNT concurrency and never modelled the GPU, so lane count and card
contention are orthogonal - flipped to N=3 first and sat red waiting. RM applied
RC's bytes VERBATIM, re-hashed from its own disk (`5297f2d0...`, 7154 bytes),
and moved `AGREED_SHA256` in the same commit. All three trees now hash equal and
declare 3. **RM's suite stayed green through the flip, and that is luck of
design rather than virtue:** RC and LW both guard by reading a sibling's tree
LIVE, so whoever moves first is red until the others follow and there is no
ordering in which nobody is red. RM guards against self-contained constants. If
RM ever builds a live cross-tree guard it inherits their bug, so the three
transition options RC weighed are recorded rather than rediscovered.

**A COUNT READ OFF A HEADER IS NOT A MEASUREMENT OF THE DOCUMENT - AGAIN, IN THE
OPPOSITE DIRECTION.** This morning `ability_stats` was predicted at 1474 and
measured 1818. This afternoon the link corpus was reported as 119 and measured
**146**. The source's header, its score-ranked index and its distribution
(`n=119`) all stop at CCR-119 while full entries run to CCR-146; a later batch
was scored in place and never indexed. **27 entries, 18% of the corpus, had
never been triaged for RM at all**, so last session's "119/119 reviewed, zero
above 5, nothing adopted" was 119 of 146. Both errors are the same shape from
opposite ends: trusting a stated count instead of counting.

**RC'S FRAME HID RM'S SHARPEST NEED.** Rescoring against an RM rubric whose top
weight is gap 7 moved six entries up, and the decisive pair is binary
reverse-engineering: `CCR-35` pyghidra-lite (8) and `CCR-89` x64dbg (7), both
scored 2 for a League dashboard. **A coaching dashboard has no binary to
reverse; RM's hardest problem class is nothing else** - 169 interop assemblies
scanned to prove `items.tier` had no source, a generic value reader that
hard-crashed the dedicated server twice with the diagnosis stopping at a guess,
and a BACKLOG item rejected on per-patch RE cost that these directly reduce.
This is what "make your own decisions, do not copy RC's claims" was actually
worth.

**A HISTOGRAM THAT DID NOT RECONCILE WITH ITS OWN TABLE, CAUGHT BEFORE COMMIT.**
The stage 3 draft claimed 24 survivors and enumerated 21, because the low bands
were grouped rather than counted. Withdrawn rather than tidied, and the
withdrawal written INTO the document - an unchecked count is the exact defect
that document exists to correct, so quietly fixing it would have been the worse
outcome. Threshold 6+, 21 survivors, 125 culled, every survivor named by id.

**TWO PROBES LIED BEFORE THEY TOLD THE TRUTH, AND BOTH LIES LOOKED LIKE
RESULTS.**

The headless blocker was recorded as "not authenticated, workspace not trusted".
**Both halves wrong.** There is no login error. The trust failure is a
PATH-SEPARATOR MISMATCH: `.claude.json` holds `C:\RedMoon` = True and
`C:/RedMoon` = False, and headless reads the forward-slash key, so it discards
all 13 `permissions.allow` entries. The workspace HAD been trusted. LW
independently hit the same bug with THREE keys for one directory. The second
blocker was `"model": "rc-main"` set MACHINE-WIDE by a sibling; RM did not touch
it and asked instead, and RC deleted it on finding the alias resolved for
nobody.

Then the hook probe. **The first run staged U+2014 under `_scratch/`, the commit
SUCCEEDED, and that reads exactly like "no gate fired".** It is an artifact:
`_scratch` is on `ascii_guard.py`'s own skip list, so both gates inspected the
diff, found nothing they own, and allowed it CORRECTLY. **A gate that stays
silent because the probe gave it nothing to catch is indistinguishable from a
gate that is not wired** - the mirror image of the two false NEGATIVES LW
reported the same day. What made the retry trustworthy was calling
`check_staged()` directly FIRST and confirming it returned a reason, so the gate
demonstrably had something to catch before anything was measured.

Even then the plain `git commit` result was not readable: both gates block and
the wording pointed at git, meaning the Bash tool had RUN. The discriminator is
`--no-verify`, which bypasses the git hook so anything still blocking must be
the agent layer. It returned `precommit_gate.py`'s own `"Commit blocked:"`
string with HEAD unmoved. **RM's PreToolUse gate fires headless under
`bypassPermissions` on 2.1.220 and covers `--no-verify`.**

DOCTRINE CORRECTED: RM has repeatedly described the Claude-side gate as unable
to fire under `--no-verify`. True of the `commit-msg` hook, which strips the
trailer through git. FALSE of the PreToolUse ASCII gate, which sits ABOVE git
and is the only cover for that channel. Complementary, not redundant.

**RM DID NOT DUPLICATE LW'S PROBE.** The operator assigned the mechanism
question to LW, LW answered it, and RC deliberately abstained on the rule that
one measurement gets one owner because "two of us agree" is not evidence. RM
asked a narrower question about its own repo and labelled it as such.

**THE TRAILER AUDIT CAME BACK CLEAN ON EVERY SURFACE**: 0 of 106 commits on
`origin/master`, project `.claude/` (three commands plus the verifier agent),
user-level commands and plugins, and there is no `.github/` at all, so no PR
template or workflow can inject it. Every hit in the repo is the enforcement
itself.

**`RM-NEXT-SESSION.txt` NOW EXISTS ON THE DESKTOP.** The operator was right that
it was missing - `LW-NEXT-SESSION.txt` and `RC-NEXT-SESSION.txt` both existed
and RM had a stale `RM continue.txt` from 2026-07-26 instead. Overwritten each
`/done`, never appended.

**ONE SURVIVOR IS A CORRECTNESS QUESTION ABOUT RM ITSELF, NOT A FEATURE.**
`CCR-146` reports that custom subagents do NOT inherit the main agent's system
prompt - theirs is the agent file body alone. RM runs a `verifier` subagent and
keeps its hard rules (7-bit ASCII, no co-author trailer, frozen files) in
`CLAUDE.md`. If those never reach a subagent, RM's subagents have been running
without them. UNVERIFIED, and it belongs at the top of stage 4.

## 2026-08-01 (second session) - The input spike closes: a count that was wrong by 344, and a boss health that is not on the prefab

Branch `master`. Ledger 003h. Commits `863c16f` (the spike) and `a9d5428` (the
living docs and this entry). **ROADMAP ITEM CLOSED - the Bloodforge input spike is DONE**, phases
1, 2 and 3. First roadmap movement in six sessions.

State at close, one run each, all four re-run by the closing agent rather than
taken from a report: `python -m pytest` **382 passed in 19.86s, exit 0** (348
before, plus 34 new), `python -m ruff check .` clean, `python
tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` on the csproj
**0 warnings, 0 errors**.

Promoted on disk, every count ASSERTED by the ingest rather than reported:
`items` 425 (schema 4), `recipes` 663, `abilities` 54, `vbloods` 65 (schema 2),
`blood_types` 13, `ability_stats` **1818** (schema 1, new).

**A PREDICTED COUNT WAS WRONG BY 344 AND NOTHING DOWNSTREAM WOULD HAVE NOTICED.**
`ability_stats` was pinned at 1474 before the dump ran, taken from cycle 2's
figure, and MEASURED 1818. 1474 counted a NAME-selected population - prefabs
ending `_AbilityGroup` - while the shipped selector is the marker COMPONENT
`AbilityGroupStartAbilitiesBuffer`. 1476 of the 1818 carry that suffix; 341 use
`_Group`, `_Abilitygroup`, `_UNUSED` and other conventions and are ability groups
by component. A name-shaped selector drops 341 real groups in silence. This is
exactly what the spec meant by "a count that is merely whatever the dumper
emitted is not an assertion" - the pin has to be a MEASUREMENT, and writing the
guess first is what made the gap visible. 1476 versus 1474 is NOT RECONCILED and
is left visible rather than smoothed.

**THE BOSS HEALTH POOL IS NOT ON THE PREFAB, AND THE CONTROL IS WHAT PROVES IT.**
`Health.MaxHealth` reads 0 on all 65 V Blood prefabs, which alone is only
suggestive - it is the `items.tier` shape and could equally be a real zero or an
unread field. The phase 3 control decides it: on `CHAR_Vampire_Dracula_VBlood`,
**19 typed fields compared between the prefab (entity 29012) and the live
instance (322945), 17 IDENTICAL and 2 differing** - `Health.MaxHealth` and
`Health.Value`, 0 against 8107. Every `UnitStats` field and `UnitLevel.Level`
agree exactly. So the branch is "the prefab carries nothing, the instance does",
confined to health, and it is **NOT spawn scaling**: 0 to 8107 is not a ratio,
so there is no factor to source. `max_health` is DECLARED AND NEVER EMITTED and
ROADMAP gap 1 is RESTATED rather than closed - a TTK denominator needs a live
world with the boss actually spawned.

Counting rather than classifying is what made that readable. "They differ" would
have been a presence-shaped answer to a value-shaped question; "17 of 19 agree
and the two that differ are both Health" names the mechanism and is falsifiable
by anyone who re-runs it.

**A DEDUPE FIX TURNED A DUPLICATE INTO AN ORDER-DEPENDENT CHOICE, AND THE COUNT
LOOKED RIGHT AFTERWARDS.** A spawned boss carries the SAME `PrefabGUID` as its
prefab. Cycle 2 saw the pair as "66 vblood rows over 65 distinct" and fixed the
COUNT by deduping on first write - which silently made the emitted row whichever
of two DISAGREEING entities the world walk reached first. Because the symptom it
was chasing (the count) was cured, nothing pointed at the remaining defect for a
whole cycle. The selector now requires the prefab marker, which is deterministic
and exists whether or not a boss has spawned.

**A GATE THAT HAD BEEN DEAD SINCE SCHEMA_VERSION 2.** `items.stats` became a
list when the first real dump showed a name-keyed map cannot carry
`ModificationType`. `core/table_deep.py` was never moved with it and kept routing
the field through `_check_number_mapping`, which returns early on a list. So the
one nested container whose schema description explicitly says the shallow gate
cannot see inside it was unvalidated by BOTH gates. Found only because the same
table was being bumped to 4. **A gate that silently no-ops reads exactly like a
gate that passes.**

**A COEFFICIENT THE SPEC DID NOT ASK FOR, FOUND BY READING TYPES BEFORE WRITING
THE READER.** `DealDamageParameters.MaterialModifiers` is a
`ProjectM.EntityTypeModifiers` holding 23 per-target-class multipliers, and
`VBlood` is one of them - MEASURED 0.33 to 1.0 over the 732 damage-reaching
rows. A boss-damage table omitting the boss multiplier would have been wrong in
exactly the direction nobody would check. The habit that caught it: dump the
declared field TYPES of every component first, then write typed accessors
against what is actually there. The phase 1 payloads under `_scratch\rmprobe\c3\`
were still on disk and answered every type question without a single guess -
including that `UnitStats.FireResistance` is a `ModifiableINT` while its
neighbours are `ModifiableFloat`.

**THE FOUR BOSS RESISTANCES ARE NOT COMMENSURABLE.** Physical and spell are
float resistances, fire is an integer RATING that only becomes a reduction
through the GLOBAL `ResistanceData` per-rating block, and corruption is already
a reduction. Measured: physical and spell are 0 on all 65, corruption 0.5 on all
65, only fire varies (0 to 75). They share a JSON object because they share a
source component, not because they share a unit. No consumer may average them.
Separately: `physical_power` EQUALS `spell_power` on every row with 33 distinct
values over 33 distinct levels, so both are level-derived, not per-boss authored.

**A NEGATIVE RESULT TAKEN TOO EARLY IS INDISTINGUISHABLE FROM A REAL ABSENCE.**
The first control run returned one entity - the prefab only - and read as a
clean "the live instance does not exist". It was taken at about 5 s of server
uptime. At 20 s the instance was there with 151 components. `ready:true` means
the prefab map settled, NOT that the world has spawned its units. Poll for the
SUBJECT. Same shape as the `Unload()` silence that three hypotheses predicted
equally.

**THE ITEMS TABLE LOST ITS 425 LOCALIZATION GUIDS, DELIBERATELY AND
RECOVERABLY.** The dump was taken on the dedicated server, where the
localization join resolves 0 of 425 - a HOST fact cycle 2 already measured, not
a regression. Backed up first to
`_scratch\rmprobe\c3p2\items-client-v3-with-localization.json`. **A client dump
re-fills them in about 100 ms and is owed.** Recorded because promoting from the
headless host has this cost every time and it is easy to forget.

**FROZEN FILE TOUCHED, FLAGGED NOT ASSUMED.** `core/tables.py` gained one line -
`ability_stats` in `TABLE_NAMES`. The approved spec names that file as the
shallow-gate home for the new table, so spec approval was read as covering it.
Nothing else in the file changed.

**A TEST WAS TOO BROAD AND WAS NARROWED, NOT DELETED.**
`test_item_stats_are_read_one_hop_off_the_item_prefab` enforced its real claim
by banning the `BuffGuid` token file-wide. Phase 1 showed `BuffGuid` is the ONLY
route to the abilities an item grants and is wrong only as a route to STATS. The
assertion is now scoped to the stat reader by enclosing method, so the original
defect is still caught.

**SIBLING TRAFFIC: LW REVERSED ON THE SLOT COUNT AND RM DID NOT MOVE.** A note
arrived mid-session (`2026-08-01-1450-from-LW-gpu-wired-n3-is-now-defensible.md`).
LW's GPU blocker is cleared - nine CUDA consumers, 16 acquisition sites, verified
by an independent sweep of all 55 tool files and enforced by a mutation-proved
census test - and LW concedes its objection conflated two resources: the bucket
models Claude account concurrency and never modelled the GPU. LW now proposes all
three move to **N=3 in one coordinated round** and will flip when RC confirms.
**RM agrees with 3 and did NOT change its value**, because LW will not move first
either and unilateral movement breaks the very agreement that currently holds.
Reply written into both sibling inboxes. RM contributed one fact neither sibling
had: **nothing in Red Moon calls the governor at all** (grep-verified, zero
callers), and LW's own loop has been wedged since 2026-07-27, so the bucket has
had effectively ONE live user and "N=2 starves someone" remains reasoning rather
than observation.

**WHAT THE GREEN SPIKE DOES NOT PROVE.** All six acceptance criteria are about
SOURCING INPUTS. None asks whether the math over them is right, so all six can
pass with a confidently wrong time-to-kill. No TTK was published to any surface.
ROADMAP gap 7 must be settled before the combat-math spec opens.

# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

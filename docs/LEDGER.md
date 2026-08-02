# Red Moon Ledger

Append-only, **newest first**. One entry per completed roadmap item.

Entries belong here and never in `CLAUDE.md`, which is size-budgeted and loaded
into context every turn.

Format:

```
## <item number> - <title> (YYYY-MM-DD)
What shipped, the verification that proved it, and the commit or merge hash.
```

---

## 003u - Red Moon is licensed Apache-2.0 (2026-08-01)

Commits `cce7219` (LICENSE, NOTICE, README) and `5a74674` (the CLAUDE.md hard
rule), plus `PENDING-DOCS` for this entry and the living docs. Suite **598
passed in 27.89s, exit 0** (598 at open, +0 - no test touched), `ascii_guard`
exit 0. No code change, no C# change, `ENGINE_VERSION` untouched. **NO ROADMAP
ITEM CLOSED**; licensing appears nowhere in `ROADMAP.md` or `BACKLOG.md` and
never did.

**The defect it closes is that the repo was public and unlicensed.** Verified
live rather than assumed, `api.github.com/repos/Remus3/RedMoon` returning
`private=False` and, after the push, `license.spdx_id=Apache-2.0`. An absent
LICENSE is not a permissive default - it is all rights reserved, so for the
life of the repo nobody could legally fork, run or contribute to code that was
readable by anyone. The one-file fix had been sitting behind nobody noticing.

`LICENSE` is the canonical text fetched verbatim from
`apache.org/licenses/LICENSE-2.0.txt`, 202 lines, **appendix placeholder left
intact**. Retyping or "filling in" that text is how a license silently stops
being the license it claims to be; GitHub's detector matches against the
canonical body, and `license.spdx_id` coming back `Apache-2.0` is the
confirmation that it matched. Attribution goes in `NOTICE` instead, which is
where Apache-2.0 puts it.

**`NOTICE` carries the part that is actually specific to this project.** Red
Moon reads Stunlock's game data, so the file states that V Rising and its
assets remain Stunlock's and that nothing of theirs is redistributed. The
claim is structurally true rather than merely asserted: `data/rmdata/` is
gitignored at `.gitignore:16` and `git ls-files data/rmdata` returns **0**,
which was probed before the sentence was written rather than after.

`CLAUDE.md` gained a hard rule as its FIRST entry, so it loads every turn - the
license, the public upstream, and the two constraints that follow and that a
future session could otherwise violate silently: never vendor
Apache-2.0-incompatible code, and never commit game assets. Cost 8 lines
against a 60 KB budget; the file is 10,031 bytes.

Recorded as pending: there is no `pyproject.toml`, so no packaging metadata
declares a license today. Whoever adds one declares `license = "Apache-2.0"`
or the two sources of truth disagree on day one.

## 003t - rm_facts states whether its two build lines agree (2026-08-01)

Commits `90c819e` (the change) and `e10a19a` (the living docs and this
entry). Suite **598 passed in 28.85s, exit 0** (588 before, +10), ruff
clean, `ascii_guard` exit 0. **FROZEN file `tools/rm_facts.py` edited with
explicit operator approval**, same footing as entry 003r's three.

The last piece of S7.5, recorded by stage 6 as blocked on approval and raised in
the same session per its own instruction. The assertion half shipped in `8684aa0`
without touching the frozen file; this is the operator-facing half.

**The defect it closes is a two-line banner that could disagree with itself.**
`rm_facts.py` has printed a game build and an extracted data build adjacently at
every session start since cycle 1 and never compared them, so a session could
bootstrap from combat data extracted from a build the machine no longer runs and
the banner would look entirely normal. Now:

```
- Game build: 1.1.13.0-r99712
- Extracted data build: 1.1.13.0-r99712
- Build agreement: MATCH
```

**THE SENTINELS ARE THE WHOLE DIFFICULTY, and they are why this is a function
rather than an `==`.** The probe never raises, so every failure comes back as a
VALUE: `"not installed"`, `"unparseable"`, `"none extracted"`. Two of those
compared to each other are EQUAL, so the obvious implementation reports a machine
with no game installed as a perfect MATCH - a green light produced by comparing
two failures. `build_agreement` rejects them first and reports `NOT CHECKED`
naming the unavailable source, because a false MISMATCH at every session start is
the fastest way to teach an operator to stop reading the line. Ten tests, six of
them the sentinel matrix over both sides.

They are named constants now rather than literals repeated at each return, and
`tests/test_build_pin_crosscheck.py` IMPORTS `BUILD_SENTINELS` rather than
restating it - S7.2's single-source lesson applied one file over. A hand-copied
sentinel list drifts silently: a skip guard checking for a string that can no
longer occur stops skipping and starts comparing two failures.

No new subprocess call, so the 5s `schtasks` timeout pinned at
`tests/test_hooks.py:284` is untouched and `tests/test_hook_consoles.py` still
passes with no exemption. **The S7.1 count pin moved 3 to 13 for that module**,
which is that gate behaving exactly as designed on its first real edit.

---

## 003s - Link ingest stage 7, and the whole track closes at zero adoptions (2026-08-01)

Commits `8684aa0` (the four gates) and `1f04a95` (the living docs and this
entry). Suite **588 passed in 26.29s, exit 0** (551 before, +37), ruff
clean, `ascii_guard` exit 0. No C# change, no rebuild, no redeploy.
`ENGINE_VERSION` unchanged - none of the four items touches section 2, 3 or 4
math. **NO ROADMAP ITEM CLOSED**, and the power-stat experiment was not run.

**THE MAIN TRACK WAS NOT ATTEMPTED AND THE REASON IS RECORDED RATHER THAN
GLOSSED.** The session opened scoped to the cycle 3 power-stat run at the
CLIENT. Probed live at open: no `VRising*` process, no Steam process, and zero
listeners across the whole 8770-8790 block. The operator was asked directly and
chose to defer the run and take stage 7 instead. `P(G)` remains undefined and
every damage number in the engine is still absent. **This is the third
consecutive session to open on a run that needs a human in-world and find the
client down.**

### What shipped, in build order

**S7.2** `tests/test_commit_history.py`, 14 tests. The co-author policy asserted
over the OUTCOME. `hooks/commitmsg_hook.py` strips and warns rather than
blocking, `--no-verify` bypasses git hooks entirely, and nothing scanned
afterward. **`CLAUDE_TRAILER` is IMPORTED from the hook** rather than restated,
so the friendly path and the backstop cannot disagree about what the policy
forbids. MEASURED: **0 offenders over 135 commits.**

Two controls, because a walk over 135 EMPTY bodies would also report zero - the
recorded "null from an instrument that cannot produce a positive". The first
asserts the walk saw exactly as many commits as `git rev-list --all --count`.
The second asserts HEAD's record actually contains HEAD's subject, read through
a second independent git format. PROBED before pinning: 134 non-empty bodies,
110,818 characters of real message text.

**S7.5** `tests/test_build_pin_crosscheck.py`, 3 tests, no production code.
`tests/test_drift_anchors.py` holds 120 authored sites to `CLAUDE.md`'s pin and
**structurally cannot reach `data/rmdata/current.txt`**, because it iterates
`git ls-files` and that tree is gitignored. Also asserts
`rm_facts.game_build()` agrees with `data_build()` - two lines that frozen module
has printed side by side at every session start since cycle 1 and never
compared. The three sentinels are rejected BEFORE the comparison, or it is a
gate with nothing to catch on any machine but Legion. Both read
`1.1.13.0-r99712` and neither test skipped.

**S7.3** `tests/test_value_diff.py`, 15 tests, plus the diff in
`tools/rmdata_ingest.py` and the flag documented in `docs/OPERATIONS.md` in the
same commit. **The highest-value item in the batch, and the only one closing a
failure that actually occurred.** RM's five ingest gates each catch a wrong
COUNT, TYPE, SHAPE or KEY. None catches a row that stayed valid, stayed unique
and stayed counted while one of its numbers changed, and git cannot see it
either. `docs/LEDGER.md:740-745` records a cycle 2 dedupe fix that "silently made
the row whichever of two DISAGREEING entities the world walk reached first. The
count looked right afterwards, which is why it survived a cycle."

Placed immediately before `if problems:` so a validate-only run surfaces drift
before anyone types `--accept`, and refusal reuses the existing `EXIT_INVALID`
path. Escape hatch `--accept-value-changes`, required IN ADDITION to `--accept`,
because cycle 3 is where the dumper is under active development and a hard
refusal with no way through would gate cycle 3 from a non-roadmap batch.

**S7.1** `tests/test_collected_counts.py`, 5 tests. A per-module map over 33
modules, asserting BOTH the key set and the total. A single total pin cannot see
a deleted 5-test module offset by five additions elsewhere. The parse check is
load-bearing rather than decorative: a regex that matches nothing returns `{}`,
and `if observed and observed != PIN` then passes silently over a suite that
cannot import at all.

### The two things building it taught that planning it had not

**The S7.2 self-check could not be written as a text scan.** A test asserting
"this module states no predicate of its own" searched its own source for the
name of the thing it forbids, matched its own assertion string, and failed on a
clean file. It is an AST walk now, which does not see inside string literals.
Small, and exactly the shape of every other finding on this track: the
instrument was measuring itself.

**An EMPTY baseline had to be defined as NO baseline, and the criterion had not
said so.** `tools/rmdata_extract.seed_tables` writes an empty envelope for every
table name, so a baseline FILE exists on any seeded tree from the first extract.
Comparing against zero rows reports all 425 items as additions on the first real
ingest. That is noise, and noise on a refusing gate trains the operator to pass
`--accept-value-changes` reflexively - which would have retired the gate on the
day it shipped.

### And one the gate caught on its own author, immediately

The first commit message for this work QUOTED a real trailer form as prose, to
explain what the narrower draft predicate would have missed. It passed the new
gate only because the line happened to wrap so that the quoted text did not
start a line. A reflow, a rebase or a different terminal width would have made
this commit trip the gate it adds. Amended to describe the form in words
instead, with a note in the message saying why. **The gate's first finding was
in the commit that introduced it.**

### The whole track, as an arithmetic identity

**146 extracted, 146 scored, 21 dived, 0 at 7 or above, 0 tools adopted, 4 work
items shipped.** Not one entry was demoted because the tool was bad; every
demotion came from an RM-side premise nobody had measured. The track's product
was never a dependency - it was the corrections those measurements forced, and
now four gates that came out of them.

---

## 003r - The console flash, and the ruff gate it had been silencing since it was written (2026-08-01)

Commits `379f6c6` (the fix) and `9d056b4` (the living docs and this entry). Suite **551 passed in 22.61s, exit 0** (544 before, +7), ruff
clean, `ascii_guard` exit 0. **Three FROZEN files edited with explicit operator
approval:** `tools/rm_facts.py`, `tools/precommit_gate.py`,
`tools/pytest_guard.py`.

**THE MECHANISM, measured by four independent instruments and unanimous.**
`pythonw.exe` is a GUI-subsystem image, so a hook launched with it has NO
console. That makes the hook windowless and does NOT make its children
windowless: a console-subsystem child of a console-less parent must
`AllocConsole`, producing a real window. Chain captured live: `pythonw.exe`
(hook) -> `schtasks.exe` -> `conhost.exe` -> visible window.

**RANKED BY WHAT THE OPERATOR ACTUALLY SEES.** `rm_facts.py`, the SessionStart
hook, spawns `schtasks` and is **VISIBLE on 5 of 5 runs for 2.0 to 2.3 seconds,
taking the foreground.** That is not a flicker; it is a two-second window at
every session start, and `CLAUDE.md` mandates `/clear` between roadmap items.
`precommit_gate.py`'s two `git` calls are visible 6 of 6 at 47 to 60 ms, and
only on the commit path - `is_commit_command` short-circuits everything else, so
an earlier statement here that it fires on every shell call was wrong.

**THE FINDING THAT MATTERS IS NOT THE FLASH.** My own first fix carried the
comment "not needed on the `sys.executable` call site further down, because under
`pythonw.exe` that IS `pythonw.exe`, which is already windowless". First clause
true, conclusion false: **`ruff/__main__.py` on Windows locates the bundled
`ruff.exe` and re-execs it**, so the GRANDCHILD is a console binary. It allocated
its own console and bound its standard handles there rather than to the pipe.
MEASURED under a real `pythonw` parent on a file with one F401:

```
[sys.executable, -m, ruff, check, f]  ->  rc 1, stdout LENGTH 0
[ruff.exe,          check, f]         ->  rc 1, stdout 278 chars
```

`check_staged` collects reasons only when the return code is 1, by iterating
`result.stdout`. Over an empty string that appends NOTHING. **The ruff half of
the precommit gate has reported clean on every commit since it was written while
ruff was actually failing** - and it passed its own tests because pytest's parent
owns a console. The project's most-named failure mode, a gate that looks exactly
like a working gate, already live in the gate that enforces the other rules.
`_ruff_argv` now resolves the binary and spawns it directly, which removes the
window AND restores the output.

**THE EXEMPTION WAS THE BUG, TWICE.** The first `tests/test_hook_consoles.py`
auditor exempted spawns whose argv[0] was `sys.executable` - whitelisting
precisely the one site that was broken. The exemption is deleted; the rule is now
unconditional, and `pytest_guard.py` carries the flag even though `pytest -m`
works in-process and does not flash, because the flag is inert there and an
exemption is a place to be wrong.

**THE 2026-07-26 MEMORY WAS PARTLY RIGHT AND IS CORRECTED, NOT DELETED.** The
`npx` MCP-launcher windows are real and its remedy still applies; a second
console-bearing chain from a sibling project was captured live this session. What
does not survive is "NOT Red Moon". And its central evidence could not have
produced a positive: it filtered for `cmd.exe` while RM's children are
`schtasks.exe` / `git.exe` / `ruff.exe`, it polled 120 s against a site that
fires once per SessionStart, the git windows last under a poll interval, and
`Win32_Process` carries no console or window field at all - so "never appeared in
the trace as a console" was an inference from image name, not an observation.

**STILL INFERENCE, stated rather than glossed:** nobody captured a real
SessionStart hook firing under the live harness. Every measurement launched
`rm_facts.py` by hand. The command form is identical and `scheduled_tasks()` is
unconditional, so the inference is strong, but it is not a capture.

## 003q - Link ingest stage 6: four items adopted, one killed by the plan's own adversarial pass (2026-08-01)

Commit `b781aab`. NON-ROADMAP track. Docs only, Tier 0. `python -m pytest`
**544 passed, exit 0**, ruff clean, `ascii_guard` exit 0.

Eight stage 4 candidates: **four ADOPTED with acceptance criteria (S7.2, S7.5,
S7.1, S7.3, in build order), one DROPPED, one deferred, one blocked on another
owner, one already discharged. Zero tools adopted**, which is now the settled
result of the whole 146-entry corpus.

**THE PLAN WAS PUT THROUGH THE SAME ADVERSARIAL PASS AS THE TOOLS AND DID NO
BETTER.** Three lenses - falsifiability of every criterion, re-measurement of
every premise, redundancy against existing gates - plus an adjudicator. 4 agents,
0 errors. I re-ran every load-bearing claim myself; all reproduced. One item died,
three criteria were rewritten, and one bullet was deleted as simply wrong.

**THE DRAFT COMMITTED THIS TRACK'S SIGNATURE FAILURE INSIDE THE DOCUMENT
DIAGNOSING IT.** S7.4 proposed pinning the ingest census's per-key min/max "for
the six promoted tables". MEASURED by importing `shape_census` and running it
over the real tree: it returns **four** - `abilities` and `ability_stats` produce
nothing, because `_observe` fires only on a `dict` or `list` value and a table
with no nested container is dropped. **The 1,818-row combat table Bloodforge
consumes is structurally invisible to it.** Nine numeric slots exist in total,
two of them guid identity fields and three degenerate. A test iterating the
census would have covered nine numbers, been labelled "the six promoted tables",
and read exactly like a passing gate. DROPPED, not re-scoped: the four pins it
could have produced would not have caught the one value drift RM actually
suffered, because the `vbloods` row swap at `docs/LEDGER.md:740` moves
`level`, `physical_power` and `spell_power`, all top-level scalars.

**THREE MORE SELF-INFLICTED FINDINGS.** (1) Four criteria described the FEATURE
rather than a FAILURE THE TEST MUST PRODUCE - "stands down on a build change",
"is silent on identical dumps" - and every clause phrased as an absence of output
is satisfied by `def diff(old, new): return []`. The stage list now rules that
out. (2) The draft called `tests/test_bridge_probe.py:31` "structurally incapable
of failing"; it is not - `bridge_probe.py:107-108` reads `current.txt` itself, so
the test sources the SUT's real input, and `:183` is a working negative control.
Bullet deleted rather than repaired. (3) A frozen-file block did not survive
contact with the frozen file's public API: `rm_facts.py:40` and `:50` expose
`game_build()` and `data_build()` as importable functions, so the ASSERTION is
unblocked and only the PRINT needs operator approval. The draft applied "assert
the outcome, not the mechanism" to S7.2 and failed to apply it here.

**AND THE DRAFT APPLIED ITS OWN STANDARD INCONSISTENTLY.** It refused S7.6 (a
`Stop` hook) because the failure has never occurred, then adopted S7.1 against a
failure that has also never occurred - across 16 recorded suite counts the
collected total is monotonically non-decreasing. S7.1 survives on an argument it
owed and had not made: the ledger count is transcribed by hand at session end **by
the same agent that would be hiding the shrink**, and is prose nothing reads back,
whereas a Stop hook carries a live regression risk of its own.

**S7.3 IS THE ITEM WORTH KEEPING.** RM's five gates each catch a wrong count,
type, shape or key; none catches a value that changed in place under a fixed
build, and git cannot see it either. It has HAPPENED - `LEDGER:740-745`, a dedupe
fix that "silently made the row whichever of two DISAGREEING entities the world
walk reached first. The count looked right afterwards, which is why it survived a
cycle." The challenge added the clause that makes it safe: cycle 3 is where the
dumper is under development, so same-build value change is normal there, and a
hard refusal from a non-roadmap batch would gate cycle 3. An explicit
`--accept-value-changes` is required when the diff is non-empty. The placement
rationale was also corrected - a post-promotion diff fails because the promotion
loop OVERWRITES the baseline, eleven lines before `_clear_incoming` runs.

Stage 7 is the only open stage.

## 003p - Link ingest stages 4 and 5 CLOSE: 21 of 21 dived, 0 adopted, and the corpus's product is a list of corrections to Red Moon (2026-08-01)

Commit `10ababa`. NON-ROADMAP track. `python -m pytest` **544 passed, exit 0**,
`python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0. One test
file touched, docstring only.

**THE TRACK CLOSES ON AN ARITHMETIC IDENTITY: 146 extracted, 146 scored, 21
dived, 0 at 7 or above, 0 adopted.** Stage 3's survivors held one 9, three 8s and
nine 7s. After every dive the highest surviving score in the whole corpus is 6.

**Run under the operator's standing execution mode** - headlessly orchestrated,
multi-agent, parallel, self-adjudicated, adversarial. Six dive clusters covering
the final 15 entries, a refuter per cluster attacking its own cluster's verdict,
and one adjudicator whose FIRST task was the coverage check. 13 agents, 0 errors,
15 of 15 entries returning a real verdict, 1+3+2+3+3+3 reconciling. Two refuters
caught and withdrew their OWN measurement errors mid-pass. **Stage 5 is therefore
discharged in the same pass rather than owed** - the adversarial challenge with
its coverage check IS what stage 5 specifies.

**I RE-RAN 13 OF THE ADJUDICATION'S LOAD-BEARING COUNTS MYSELF. ALL 13
REPRODUCED EXACTLY.** 127 commits and 0 banned trailers; 0 tracked files under
`data/rmdata/`; no test pinning the collected count; 120 pin occurrences against
a docstring claiming ~97; the invented date rule returning exactly one hit;
hook events `PreToolUse`/`PostToolUse`/`SessionStart` with no `Stop`; CLAUDE.md
9,466 bytes against a 60,000 budget; 3,038 rows and 0 nulls; Codeman live at
`github.com/Ark0N/Codeman`, MIT, 508 stars.

**THE FINDING IS NOT THE SCORES. Across all 21 dives, not one entry was demoted
because the tool was bad.** Five of the fifteen read BETTER at source than their
corpus lines. Every demotion came from an RM-side premise nobody had measured:
RM suffers unverified "tests pass" claims (**0 of 9** sessions with a claim had
no test run); RM cannot test without launching V Rising (**544 of 544** pass with
it off); RM's data floor needs external drift validation (**0 nulls in 3,038
rows**); RM's gate "blocks but does not teach" (it emits file, line, column,
codepoint and rule per violation). **Stage 2 scored good tools against beliefs
about Red Moon, and the beliefs were the defect.**

**A NEW SUB-SHAPE, NAMED.** Four entries were scored by reading a rule in
`CLAUDE.md` and treating the WRITTEN DISCIPLINE as an UNMET NEED. A rule written
down is evidence the project already solved something. "RM's most-repeated
discipline is X" is not the statement "RM suffers X".

**AND THE SHAPE BIT THE FAN-OUT ITSELF**, which is the most useful thing it did.
The CCR-135 dive asserted "RM has no many-session problem" without probing
`ops/loop/`, which exists for exactly that - the bug the fan-out was built to
catch, committed by the fan-out, caught by its own refuter. Recorded as method:
an adjudicator must check the DIVE's unstated premises, not only stage 2's.

**FOUR CORRECTIONS TO RED MOON'S OWN RECORDED FACTS, each re-verified here.**

1. **`CCR-135` was never a Reddit post and was never unreachable.**
   `github.com/Ark0N/Codeman`, MIT, 508 stars. The recorded stage 4 GAP was a
   false absence, and it is the SECOND in that document from trying one access
   route and stopping. **New method rule, now in the stage list: a source is
   unreachable only after two different routes fail.**
2. **`tests/test_drift_anchors.py:6` said the build pin lives in "~97 tracked
   sites". It is 120**, recounted by three parties independently. Sixth instance
   of the count-the-rows shape and the first inside a test's own docstring.
   Corrected.
3. **The drift anchor is a CLOSED LOOP** - it compares `CLAUDE.md` against
   tracked files with no tie to the install's `VERSION` or to `current.txt`, so
   it stays green while every authored file cites a build no longer on disk.
   `rm_facts.py` prints both build lines adjacently and never compares them.
4. **Do NOT retire the "no commit while an agent is live" rule.** A dive
   recommended it once worktrees run. The spec line records that a
   worktree-isolated agent **twice wrote into the MAIN tree while
   `git worktree list` showed no second tree** - declared isolation that was
   fictitious, which `git worktree add` does not address.

ROADMAP gains gap **8b**: nothing attributes a recorded health delta to an
ability. RUN 1 dodges it by constraining the operator to one ability; RUN 2, a
real V Blood fight, has no mechanism. The honest instrument is a bridge-side
ability-application read on the same tick, not a video - a narrated recording was
evaluated and rejected because keyframes cannot tighten a 0.5 s sample interval.

Stage 6 is next and short: eight measured candidates, most of them not tools.
Highest-value is a dump-to-dump VALUE diff keyed on `prefab_guid` - RM's five
gates catch a wrong count, type, shape and duplicate key, and nothing catches a
value that changed in place, which git cannot see either because
`data/rmdata/` is gitignored.

## 003o - Link ingest stage 4: the wiki has no combat numbers, and 40 of 40 levels agree (2026-08-01)

Commit `0f24c44`. NON-ROADMAP track. Docs only, Tier 0. `python -m pytest`
**544 passed, exit 0** (unchanged), `python tools/ascii_guard.py` exit 0. Probe
payloads saved to `_scratch/rmprobe/wiki/`, gitignored.

Stage 4 goes from 3 of 21 dived to **5 of 21, 14 owed, zero adopted.** `CCR-39`
and `CCR-84`, the MediaWiki pair, both DEMOTED 7 to 4 on the two checks named in
advance.

**CHECK 1 WAS RUN FIRST BECAUSE IT IS ABOUT THE DESTINATION, AND IT FAILS.** Both
entries were scored on the claim that the V Rising Fandom wiki carries "published
boss health, resistances and gear numbers", making it the one independent second
source in the corpus. ENUMERATED, not sampled: `Category:V Blood Carriers`
returns 65 members, 64 of them boss pages. Every page fetched, every
`{{Boss Infobox}}` parsed. **No `health`, no `hp` and no resistance parameter
exists on any page**; the parameters are title, image, level, unit_id,
description, location and four `unlocked_*` families. **24 of 64 carry no
infobox at all** - a different and worse statement than a missing field. A
free-text scan finds 5 `HP`, 1 `max health` and 15 `resistance`, and every one is
the wrong kind: health always as a PHASE THRESHOLD in percent ("at 50% HP he
summons two gargoyles"), resistance always player-side - a potion recipe, a
soul-shard buff, or prose about a boss's damage type. No page states a version, a
patch or a difficulty, so gap 9's required axis is missing there as well.

**THE JOIN KEY IS REAL AND CORROBORATES SOMETHING NARROW.** The infobox carries
`unit_id` and it IS RM's `prefab_guid`. Joined against `vbloods.json`: **40 with
a unit_id, 40 matched, 0 unmatched, and `level` agrees on 40 of 40.** First
independent second-source confirmation of anything in `data/rmdata/` - of
IDENTITY and LEVEL only. 25 of RM's 65 rows have no wiki `unit_id`, including
`CHAR_Bandit_Leader_VBlood_UNUSED`, correctly absent from a player wiki.

**CHECK 2: BOTH SERVERS WORK AND BOTH ARE WRONG-SIZED.** CCR-39 is 40+ tools in
Go; CCR-84 is 37+ tools in Node with OAuth2 write and a 50 KB content cap. Both
MIT, both read public wikis anonymously, neither is bad. RM needs exactly two
read calls. The decisive fact is that **this entire dive was performed with
`urllib` against the public `api.php` with neither server installed** - Fandom
answered anonymously at MediaWiki 1.43.9, HTTP 200 throughout. That is RM's
ordinary ingest shape, and the rubric explicitly lowers a score for a wrapper
around something RM already does directly.

**A TRAP RECORDED FOR THE NEXT AGENT.** `WebFetch` on the rendered page returns
**HTTP 402 Payment Required** while `api.php` on the same host returns 200. An
agent that tries the page and not the API records a false absence, which is the
failure shape this document keeps meeting.

**THE PATTERN ACROSS ALL FIVE DIVES IS NOW UNAMBIGUOUS AND IS THE REAL RESULT.**
Not one entry was demoted because the tool was bad. Every one was demoted because
the RM-SIDE PREMISE it had been scored against was never checked - gap 8 was
never a reverse-engineering problem, and the wiki never carried combat numbers.
**Stage 2 scored tools against beliefs about Red Moon.** Measuring those beliefs
is cheaper than reading the tools and is where the value is.

ROADMAP gains gap **8a**: no second source for any combat number exists, measured
rather than assumed, so the falsification anchor must come from a recorded run
and it is no longer worth looking for a shortcut.

## 003n - Link ingest stage 4: the binary-RE pair dived, and both demoted (2026-08-01)

Commit `f7a1bbc`. NON-ROADMAP track, per `docs/research/LINK_INGEST.md`. Docs
only - no code change, Tier 0. `python -m pytest` **544 passed, exit 0**
(unchanged, as a doc change should leave it), `python tools/ascii_guard.py`
exit 0.

Stage 4 goes from 1 of 21 survivors dived to **3 of 21, 16 owed, zero adopted.**
`CCR-35` pyghidra-lite DEMOTED 8 to 4 and `CCR-89` x64dbg DEMOTED 7 to 5, both
on the two checks stage 4 had named in advance. Sources read at
`claudemarketplaces.com`; every RM-side fact re-measured on this machine.

**THE FINDING THAT MATTERS IS NOT ABOUT EITHER TOOL.** Stage 2b overturned the
pair upward on one shared argument - RM's hardest problem class is binary reverse
engineering, and the cited instance was ROADMAP gap 8, "a global ECS constant
that has never been read". **"Never been read" had been carried through three
documents as though it meant "hard to read".** MEASURED from the saved phase 1
payload rather than from the prose describing it: `ProjectM.ResistanceData` is a
non-buffer component among the 150 enumerated on the Dracula entity, present on
the prefab AND the instance (`BRIDGE_SPIKES.md:1043`), and all 11 of its fields
including `FireResistance_DamageReductionPerRating` are declared `System.Single`
- plain floats. The plugin already reads `UnitStats.FireResistance` off that same
entity with a typed accessor. Gap 8 is an unwritten reader, not an RE job. Sized
in ROADMAP; the gap stays OPEN because the value is still unread, but what
closing it takes has changed.

**CCR-35, check 1 fails.** 9 tools, ELF/Mach-O/PE, auto-detects Swift,
Objective-C and Hermes/React Native, requires Ghidra 11.x and JDK 21+ locally,
MIT. **IL2CPP, Unity and .NET are not mentioned at all.** Ghidra loads
`GameAssembly.dll` fine - that was never the difficulty. The structure worth
recovering lives in `global-metadata.dat`, VERIFIED present on this install, and
recovering it is what Il2CppDumper is for. RM is also on the wrong side of the
process boundary for it to matter: it reads from inside via BepInEx against 172
interop files carrying real type and field names.

**CCR-89, check 2 answered - on blast radius, not anti-cheat.** A search of the
install tree to depth 2 finds NO EasyAntiCheat binary, so the ban-risk objection
is unsupported for this modded local install, and that scope is stated rather
than generalized. The problem is the surface: the 23 tools include memory write,
allocate, protect, byte patching, PE dumping and anti-debug hiding. The 2.3.0
hardening is about the plugin's own listener on 127.0.0.1:27042, not the target.
The RM need it would serve - the phase 1 generic value reader that hard-crashed
the dedicated server twice - is real and RETIRED: RM banned that approach in
favour of typed accessors, so this would diagnose a crash RM has decided never
to re-cause again.

**Fourth instance of the same shape**, after ability_stats 1474 versus 1818, the
corpus 119 versus 146, and `vblood_damage_modifier` range versus binary. Here the
uncounted thing was RM's OWN capability, asserted in RM's own document, which is
the harder case.

Stage 3's survivor table is deliberately NOT retro-edited - the cull was chosen
from the distribution as it stood, and rewriting the inputs to a threshold after
the fact is the unchecked-count failure this track exists to correct. A note
under the table says so and points at the stage 4 scores.

## 003m - The experiment did not run, and the three things blocking it did (2026-08-01)

Commits `ca96397` (the series layer, the target lister, the quarantine fix) and
`5b7aad6` (the living docs and this entry). **NO ROADMAP ITEM CLOSED, AND THE MAIN TRACK WAS NOT
ATTEMPTED.** The session was scoped to the section 3.3 power-stat experiment at
the V Rising CLIENT. Neither bridge port answered and no V Rising process was
running; the run needs a human in-world to equip, slot, target and cast about
30 times, and the operator was not available. Deferred intact rather than
approximated. `P(G)` is still undefined and every damage number is still absent.

State at close, one run each: `python -m pytest` **544 passed in 20.02s, exit 0**
(526 before, +18), `python -m ruff check .` clean, `python tools/ascii_guard.py`
exit 0. No C# change, so no rebuild and no redeploy.

**What was verified rather than assumed before anything was touched.** The
discriminator row reproduced by counting, not by reading the prose describing
it: 1818 rows in `ability_stats`, exactly one with `prefab_guid` -1136860480,
`spell_school` unholy, `damage_type` physical, `coefficient` 1, `hits_per_cast`
1, `ability_type` SpellSlot2. `moon_sync_inbox/` was clean at open - all 14
files timestamped 10:19 or earlier against a 13:00 HEAD.

**THE PROCEDURE HAD A HOLE WHERE THE RUN STARTS.** `docs/ANCHOR_RUNS.md` said
"find the target's prefab guid" and did not say how. `tools/find_target.py` now
does it, over `/dump/components?instanced=1`, which returns entities SPAWNED in
the world rather than the prefabs they came from - the distinction the whole
recorder turns on, because a prefab reads `Health.Value` 0 and a recorder
latched onto one produces a flat series indistinguishable from a recorder
reading nothing. V Bloods and prefab rows are MARKED, never dropped: a tool that
silently filters teaches the operator that the list it printed was complete.

The same doc gained the caster-side precondition as a CHECK rather than a
warning. The arm response is the first and only place `PhysicalPower` versus
`SpellPower` is observable, and at 10 and 10 both hypotheses predict the same
number and the run is indeterminate however clean the deltas are.

**THE ENGINE NO LONGER IMPORTS A `tools/` SCRIPT.** `bloodforge/series.py` holds
the pure series layer - `parse_stamp`, `sample_intervals`, `observed_cadence`,
`per_hit_discard_reasons`, `isolated_deltas` and `GAP_TICK_MULTIPLE` - and
`tools/anchor_record.py` re-exports it. Duplicating the two functions was the
worse option on the table: two copies of the isolation rule can DRIFT, and
catching that class of divergence is what the falsification protocol is for.
`tests/test_series.py` asserts the re-export **by identity, not equality**, so a
copy pasted back into the writer fails where an equality check would pass, plus
an AST check that no module under `bloodforge/` imports from `tools/` at all -
the layering rule itself, not the one module that happened to break it.

**A DATA FIX THAT RECOVERED THE ALREADY-BROKEN STATE, NOT ONLY FUTURE RUNS.**
`rmdata_ingest` promoted by COPYING out of `tables/_incoming/` and left the
source in place, so after a successful accept the two directories held
byte-identical files and nothing on disk said which state the tree was in.
Promotion now empties the quarantine, and only on the success path - a refused
run and a validated-but-unaccepted run both still leave the rows there, which is
the state `_incoming/` exists to represent. The six stale files on the real tree
were SHA256-compared against their promoted copies, found identical on all six,
and removed. Three tests pin all three states.

**Doc drift found while syncing.** `docs/ARCHITECTURE.md` listed the engine as
`agents/bloodforge/`, a path that has never existed; the module map now names
the six real modules. `DASHBOARD_CONCEPTS.md` justified deferring F8 partly on
"no `agents/bloodforge/` exists", which was true of the path and false of the
package - the real blocker is that nothing binds 8783, and it now says so.

Caveat carried forward unchanged: when the experiment does run, one row is a
sample of one. A pass says which hypothesis survives on THAT ability and does
not prove the rule corpus-wide. It is the only evidence this build affords -
zero rows are `is_weapon_ability` with a non-physical `damage_type` and a
nonzero coefficient, so the weapon side is dead by exhaustion, not by sampling.

## 003l - The anchor recorder runs, and its first run corrects four things (2026-08-01)

Commit `23d40bf` (the recorder, the damage model, the DPS cycle, the anchor
writer, the power-stat evaluator, and every doc correction below) and `5566933`
(the living docs, this entry and the next-session prompt).
**NO ROADMAP ITEM CLOSED.** The combat math spec is IMPLEMENTED but not
DISCHARGED: sections 2 and 4 are code, the section 3.3 experiment has NOT been
run, and discharge requires it. Two new gaps opened: 12 and 13.

State at close, one run each: `python -m pytest` **526 passed in 20.16s, exit 0**
(405 before, +121), `python -m ruff check .` clean, `python tools/ascii_guard.py`
exit 0, `dotnet build` 0 warnings 0 errors, deployed to both hosts with matching
SHA256.

WHAT SHIPPED.

1. **`GET /record/{start,status,stop}` EXISTS AND HAS RUN AGAINST A LIVE WORLD.**
   `bridge/src/RedMoon.Bridge/HealthRecorder.cs`. It is the only thing in this
   project that can produce a falsifiable series. It samples on the same
   `MainThreadTick` as `StateReader` rather than polling `/dump/statcontrol`,
   which walks every entity per request against a measured 95 ms full scan under
   a one-at-a-time gate; the subject is resolved once and re-validated in O(1).
   The arm REQUIRES `carries_prefab_marker` false, so the phase 3 timing trap is
   a precondition rather than a comment. Capacity is STOP-AT-CAP at 4096 rather
   than an overwriting ring, because A.5.3 needs the FIRST sample to equal max
   health and a ring silently discards the start of a fight.

   MEASURED against a dedicated server with a spawned Dracula: 56 samples in
   27.6 s, 0 dropped, `prefab_guid` and the liveness marker restated on 56 of 56,
   the prefab seen as a separate entity and correctly rejected.
   **NOT COVERED, and said out loud: no NONZERO health delta was observed.**
   Nothing headless damages a boss, so the series is flat at 8107. A recorder
   reading nothing would look identical, which is exactly why the controls are on
   every sample.

2. **The combat math, sections 2 and 4, behind the embargo.**
   `bloodforge/damage.py` and `bloodforge/dps.py`. `cycle` is a MAXIMUM over the
   three windows and never a sum - they overlap, and `cooldown` is 0 on 352 of
   1818 rows which is what forces the max form. Mutation-tested independently:
   changing `max` to `sum` fails five tests. An undefined term is a TYPE that
   supports no numeric protocol, so `1.0 - fire` raises at the site instead of
   producing a wrong float three frames away.

3. **The writer and the evaluator.** `tools/anchor_record.py` builds the B.1
   manifest, runs the A.5 checklist and writes atomically;
   `bloodforge/powerstat.py` evaluates H1 against H2 and refuses to name an
   unearned winner. `docs/ANCHOR_RUNS.md` is the operator procedure.

FOUR CORRECTIONS, every one from running the thing rather than reading about it.

1. **THE SAMPLE RATE IS 2 Hz ON THIS HOST, AND 4 Hz WAS NEVER A MEASUREMENT.**
   Both specs state 4 Hz as a hard ceiling and computed the section C tolerances
   against it. `SampleEveryFrames = 15` is a FRAME count, so the rate follows the
   host's frame rate, and no frame rate had ever been read on either host.
   MEASURED: interval min 0.500 s, median 0.502 s, max 0.503 s over n=55, so
   **1.99 Hz at 29.9 fps** under `-batchMode -nographics`. The A.5 gap check is
   now 3x the OBSERVED median interval rather than a hardcoded 750 ms, which at
   2 Hz would discard a valid run, and every manifest records the rate measured
   from its own series. The client should give about 4 Hz and REMAINS UNMEASURED.
   ROADMAP gap 12.

2. **THE RECORDER STAMPED A SUB-SECOND SERIES WITH A WHOLE-SECOND CLOCK.** Found
   by reading the code before deploying it. Two to four samples shared a
   `captured_at`, which makes the gap check, the 2.0 s idle window and the
   bracketing of an isolated delta all uncomputable. `Json.UtcNowMillis` now
   exists for the recorder and for nothing else.

3. **THE ARM REPORTED A DECLINE AS AN ABSENCE.** `player_resolved` read false
   while the samples it went on to take carried a full player block from index 19
   onward: `Clear()` reset the rescan counter and the arm then consulted the
   throttle it had just reset. **A silent gate is indistinguishable from an
   unwired one**, for the third time on this build. Not cosmetic:
   `player_unit_stats` at t0 is the ENTIRE comparison basis of the power-stat
   experiment, so an arm that omits it produces a run that decides nothing.

4. **CORRUPTION IS BLOCKED ON THE POWER SIDE AND THE EXPERIMENT CANNOT UNBLOCK
   IT.** The spec listed corruption as computable-after-the-experiment, having
   reasoned about it entirely on the `reduction` side where it is the one type
   with a real nonzero value. COUNTED: **all 18 corruption damage groups carry
   neither a `spell_school` nor `is_weapon_ability`**, so H2 has no kind to
   select on and H1 is stated over Physical and Spell only. Both hypotheses are
   silent. So **60 of 732 damage groups are unpriceable after the experiment,
   not 42**, and the only nonzero defined reduction on this build is reached by
   nothing real. ROADMAP gap 13.

TWO MORE MEASUREMENTS WORTH CARRYING.

- **`max_health` 8107 reproduces at n=3**, across three process lifetimes and
  three distinct entity indices (322945 earlier, 322862, 322840), against 0 on
  the prefab every time. That answers half of combat-math open question 7: the
  value is stable across a reload of the same save. It does NOT answer the other
  half - no `ServerGameSettings.json` is written anywhere, so the difficulty is
  a default rather than an observation, and a FRESH world has not been spawned.
- **The experiment has a CASTER-side precondition nobody had written down.** The
  character armed against reads `PhysicalPower` 10 and `SpellPower` 10, on which
  H1 and H2 predict the same number and the run is indeterminate however clean
  the deltas are. Section 3.2 rejected the default subject because the ABILITY
  could not separate the hypotheses; the same run fails on the CASTER side.
  Enforced in `powerstat.evaluate`, which checks separability before it counts
  deltas, and stated first in `docs/ANCHOR_RUNS.md`.

AND ONE BUG FOUND BY AN INDEPENDENT SMOKE TEST rather than by the suite:
`evaluate` reached `statistics.median([])` and raised on a series with zero
isolated deltas - which is exactly what my own flat 56-sample recording is, and
exactly what a recorder LATCHED ONTO THE PREFAB produces, since the prefab reads
`Health.Value` 0. A traceback there is strictly worse than the naive reading the
controls exist to prevent, because it invites a re-run instead of an inspection.
Fixed and pinned.

WHAT DID NOT HAPPEN, and it is the headline. **The power-stat experiment was NOT
run.** It needs the V Rising CLIENT with a live character casting
`AB_Unholy_WardOfTheDamned_AbilityGroup`; the dedicated server runs
`-batchMode -nographics` and has no player. Everything around it is built,
deployed and verified, and the run is one operator session away.

---

## 003k - The embargo lands before the math, and the default subject proves nothing (2026-08-01)

Commits `6d5095e` (the embargo gate, the first `bloodforge/` code),
`6056b45` (the combat math spec) and `df2131a` (the living docs, this entry and
the next-session prompt).
**NO ROADMAP ITEM CLOSED.** The combat math spec is OPEN, not discharged, and no
math is implemented. Two new gaps opened: 10 and 11.

State at close, one run each: `python -m pytest` **405 passed in 19.93s, exit
0** (382 before, +23 from `tests/test_embargo.py`), `python -m ruff check .`
clean, `python tools/ascii_guard.py` exit 0.

WHAT SHIPPED.

1. **The publication embargo is CODE, and it landed one commit BEFORE the math
   spec that needs it.** `bloodforge/embargo.py` is a single gate function the
   serializer iterates, which is what makes `tests/test_embargo.py` total rather
   than a spot check - there is no second code path that can emit a field.
   `dps` lifts on the per-hit gate alone, `ehp` on the EHP gate, `ttk_seconds`
   needs both plus three comparable runs. Unlifted fields are REMOVED: absent
   key, not null, not 0, not -1. `data/schemas/anchor.schema.json` is the
   recorded run. **`ENGINE_VERSION` now exists** at `0.1.0+1.1.13.0-r99712`;
   before this it was described as pinned by two documents while a repo-wide
   grep returned nothing.

2. **`docs/superpowers/specs/2026-08-01-bloodforge-combat-math-design.md`** -
   the damage model term by term, the DPS cycle as a MAX rather than a sum (the
   three windows overlap), EHP as a per-damage-type map rather than a scalar,
   and an explicit table of what is computable today versus merely declared.

3. **THE FINDING: the default subject vector cannot falsify the power-stat
   hypothesis.** 31 of the 32 weapon-linked damage groups are `damage_type`
   physical and 203 of 205 weapons grant `PhysicalPower` and no `SpellPower`, so
   both hypotheses predict the same number for every realistic weapon ability.
   Zero rows are `is_weapon_ability` with a non-physical type and a nonzero
   coefficient - dead by exhaustion, not by sampling. **Exactly one row in 1818
   separates the hypotheses:** `AB_Unholy_WardOfTheDamned_AbilityGroup`,
   `coefficient` exactly 1.0, `hits_per_cast` 1, spell school unholy,
   `damage_type` physical, player-castable, needs no boss. Cheapest run in the
   protocol; take it first.

4. **Two open questions settled by probing rather than reasoning, both pinned as
   tests.** A fifth envelope key PASSES the frozen `validate_table`, which
   rejects undeclared fields on ROWS only - so the anchor manifest rides with
   its series. And `core.table_deep.deep_problems` CANNOT gate the anchor: it
   raises KeyError outside the frozen `TABLE_NAMES`. Falsification spec D.4.1
   claimed both and is corrected.

5. **Gaps 10 and 11 opened.** 154 of 563 weapon links reach no damage at all,
   including two of the default weapon's three abilities, so every GreatSword
   figure is primary-only. And `ability_type` is `Secondary` on all 36 weapon
   groups that carry it, primary attacks included, so a consumer filtering for
   `Primary` gets zero rows.

WHAT IS WORTH CARRYING FORWARD. Two existing gates caught real violations of
this session's own change - the port-literal allowlist and
`test_no_stray_schema_files` - and both were right. The fix was an explicit
`NON_TABLE_SCHEMAS` allowlist, not a loosened pattern. And counting the promoted
rows corrected six recorded facts, the third time that discipline has moved a
number in this project.

## 003j - Gap 7 settled, the cycle 4 stack ruled, and a range that was a binary (2026-08-01)

Commits `314ef07` (the specs, the ADR and the living docs) and `0c276f6` (this
entry, the session notes and the next-session prompt). **NO ROADMAP ITEM CLOSED.** Gap 7 is SETTLED but not
DISCHARGED, and cycle 4 is planned but has zero implementation. Both were
operator-deferred to this session.

State at close, one run each: `python -m pytest` **382 passed in 19.60s, exit
0** (unchanged - this session added documents, not tests), `python -m ruff check
.` clean, `python tools/ascii_guard.py` exit 0.

WHAT SHIPPED.

1. **ROADMAP cycle 3 gap 7 is SETTLED** by
   `docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md`, 600
   lines. Decision A is operator-ruled: the anchor is a **bridge-side boss
   `Health.Value` time series**, not a hand-timed recording. The embargo is
   **per field** - `dps` lifts on the per-hit gate alone, `ttk_seconds`
   additionally needs the instance-only denominator over three comparable runs.
   The combat-math spec may now open, because an unvalidated engine behind that
   embargo is harmless.

2. **ADR-008 rules the cycle 4 stack:** server-rendered HTML, vanilla JS, no
   framework, no build step, no `package.json`.

3. **`docs/research/DASHBOARD_CONCEPTS.md`** - 30 adjudicated concepts in 6
   categories, a ranked 7-item slice, 7 conflict rulings, 16 measured
   prohibitions, and a NORMATIVE five-state uncertainty vocabulary.

4. **Link ingest stage 4 opened** and its first dive REFUTED `CCR-146`.

THE FINDINGS.

**A MIN AND A MAX WERE REPORTED AS A SPREAD, AND THE CORRECTION MADE THE RISK
WORSE.** `vblood_damage_modifier` has been described everywhere - `BLOODFORGE.md`,
the session brief, the first draft of the gap 7 spec - as "ranging 0.33 to 1.0
over the 732 damage rows", with the consequence that omitting it "misstates every
boss TTK by up to 3x". COUNTED: it takes exactly **two** values, 1.0 on 728 rows
and 0.33 on 4, all four golem-form NPC abilities, and 1.0 on **all 409
weapon-linked damage rows**. So it is inert for loadout coaching. **The danger
inverts rather than disappearing:** a bug that drops a term which is 1.0 almost
everywhere is invisible in 99.5 percent of cases and silently triples exactly the
golem builds. That is the `core/table_deep.py` shape - correct-looking everywhere
it is exercised. It must ship with a regression test pinned to those four rows.
Incidentally one of the four is spelled `AB_Shapesfhit_...` in Stunlock's own
data, which corroborates ADR-007's marker-component rule with a fresh instance.

**TWO NEW GAPS, BOTH FOUND BY OPENING A DIRECTORY NOBODY HAD OPENED.** Gap 8:
the fire rating cannot be converted to a reduction.
`ResistanceData.FireResistance_DamageReductionPerRating` is enumerated at
`BRIDGE_SPIKES.md:943` as a declared member and its **value has never been
read** - not in `data/rmdata/`, not by the plugin, which names it only in a
comment. The one resistance that actually varies across the 65 bosses is the one
RM cannot price. Gap 9: `data/rmdata/<build>/difficulty/` holds
`UnitStatModifiers_VBlood`, and Brutal is `{LevelIncrease 3, MaxHealthModifier
1.25, PowerModifier 1.7}`. **Every level and power figure in `vbloods.json` is
implicitly a Normal-difficulty figure**, and difficulty is a third subject-vector
axis that all three concept lenses and every prior pass missed. It is also the
only subject axis whose values are fully sourced on disk today.

**CCR-146 IS LITERALLY TRUE AND BESIDE THE POINT.** The claim is that custom
subagents do not inherit the main agent's system prompt. RM's `verifier` was
dispatched under a no-tool constraint and quoted both hard rules **verbatim**,
including the incidental "14 of the 30 commits" clause, plus all 17 `CLAUDE.md`
headings - with zero tool calls, so nothing was read off disk. The rules DO
reach subagents; they arrive as a **`system-reminder` injection rather than in
the system prompt proper**. RM was never exposed. Scope stated rather than
generalized: one agent type, one harness, **2.1.219** - and the `claude` on PATH
is **2.1.220**, so RM runs two CLI versions at once and any RM finding must say
which produced it.

**A SILENT ZERO FOOLED AN ADVERSARIAL AGENT INTO DESIGNING AROUND A FICTION.**
The provenance lens built a whole section on "`RM-DataRefresh` is defined but not
installed", from a `schtasks /query` that returned zero rows. Git Bash MSYS
path-translation had rewritten `/query` into `C:/Program Files/Git/query`;
schtasks exited 1 and the pipeline yielded nothing. The task is installed and
Ready, next run 2026-08-02 05:30. **This is the third instance of the same shape
in this project's history** - after 1474 versus 1818 and 119 versus 146 - and the
first where the silent zero survived an adversarial pass. The rule is now in
memory: never call a `/`-flagged Windows exe from the Bash tool.

**AND IT HAPPENED TO ME TOO, IN THE SAME SESSION.** Checking the coaching lens's
claim that player items carry the four resistances bosses lack, I keyed on
`type`/`name` and got zero hits - and very nearly recorded the claim as refuted.
The real key is `stat`. The claim was correct: SunResistance 34, Garlic 22,
Silver 22, Holy 8, Fire 8. **A probe that gives the gate nothing to catch reads
exactly like an absence**, which is the lesson this project wrote down twice
already, landing on the agent that was enforcing it.

**THE THREE LENSES INDEPENDENTLY INVENTED ONE PANEL.** Observer O4, coaching C2
and provenance P4 were three names for the same grid. Built separately they would
have produced three disagreeing accounts of the same absence. Merged as A1, the
Corpus Ledger, and it is the highest-value panel in the catalogue.

**THE ADJUDICATOR PREFERRED THE BUILDER'S SELF-CRITIQUE OVER THE REQUESTER'S
ENTHUSIASM.** The observer lens called the provenance amendment the highest-value
item in cycle 4; the provenance lens - the one that would build it - argued
against its own thesis, noting every historical failure was caught by a document,
a test or a recount and none by a UI. Ruling: split it. The data half is real but
is INGEST work and must not count toward cycle 4; the UI half is rejected.

VERIFICATION. `pytest` 382 passed exit 0, `ruff` clean, `ascii_guard` exit 0,
all re-run after the last edit rather than taken from a report. Every load-bearing
subagent claim was independently re-probed: the bridge's 5 routes, the table
envelope shape, the absent `health.json`, the absent `package.json`, the
`ascii_guard` suffix list, `gear_score` 0 of 205 weapons, the 72-row
PhysicalPower tie, the 3,038-row corpus total, the 409/154 edge split, and 1,086
of 1,818 coefficients omitted. Two subagent claims were REFUTED
(`RM-DataRefresh`, and the observer lens's 2,038-row total) and one of my own
probes was refuted by the agent's.

## 003i - The slot round, the link corpus that was 146 not 119, and two gates probed (2026-08-01)

Commits `5609509` (slot flip and re-pin), `5665b1a` (link ingest opened),
`f50881e` (sweep completed and hook probe) and `bb59300` (the living docs and
this entry). **NO ROADMAP ITEM CLOSED** - all of this is the non-roadmap track, run
after ledger 003h closed the Bloodforge input spike earlier the same session.

State at close, one run each: `python -m pytest` **382 passed in 19.50s, exit
0**, `python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0.

WHAT SHIPPED.

1. **RM followed LW to N=3 and applied the three-repo re-pin.** LW flipped first
   and was carrying a red suite waiting on RC and RM. RC's bytes were copied
   VERBATIM from `moon_sync_inbox/slots.py.proposed-3repo` and re-hashed from
   RM's own disk rather than taken on either sibling's word: `5297f2d0...`, 7154
   bytes, LF only, zero non-ASCII, docstring-only diff. `AGREED_SHA256` moved in
   the SAME commit, because a pin that lags its file guards nothing.

2. **RM's own link ingest opened at `docs/research/LINK_INGEST.md`**, stages 1
   to 3 complete, using RC's stage structure as scaffolding and none of its
   judgements.

3. **The headless preflight passes**, and both recorded blockers were wrong.

4. **RM's PreToolUse gate probed headless** and a doctrine correction recorded.

THE FINDINGS.

**THE LINK CORPUS IS 146 ENTRIES, NOT 119, AND EVERY PRIOR PASS CALLED 119
COMPLETE.** The source's header, its score-ranked index and its score
distribution (`n=119`) all stop at CCR-119; full entries run to CCR-146. A later
batch was scored in place and never indexed or counted, and it includes GitHub
and Reddit sources rather than only marketplace MCP servers, so the header is
stale in two ways. **27 entries - 18% of the corpus - had never been triaged for
Red Moon at all.** Last session's "119/119 reviewed, zero above 5, nothing
adopted" was 119 of 146. A count read off a document's header is not a
measurement of the document, which is the same lesson the `ability_stats` pin
taught in the other direction hours earlier.

**RC'S FRAME HID RM'S SHARPEST NEED, AND THE OVERTURN IS A CLUSTER.** Scoring
against an RM rubric whose top weight is ROADMAP gap 7 - nothing can falsify a
computed TTK - moved six entries upward. The decisive pair is `CCR-35`
pyghidra-lite (8) and `CCR-89` x64dbg (7), binary reverse-engineering tooling
scored 2 for a League dashboard. **A coaching dashboard has no binary to
reverse; Red Moon's hardest problem class is nothing else** - 169 interop
assemblies scanned to prove `items.tier` had no source, a generic value reader
that hard-crashed the dedicated server twice with the diagnosis stopping at a
guess, and a `BACKLOG.md` item rejected on per-patch RE cost that these directly
reduce. Also raised: `CCR-50` schema-drift monitoring (7), and `CCR-75` (6)
change-watch on the build pin, which RM asserts across about 97 tracked sites
and currently learns has moved by noticing.

**A DRAFT OF THE CULL CARRIED A HISTOGRAM THAT DID NOT RECONCILE WITH ITS OWN
TABLE** - 24 survivors claimed against 21 enumerated, because the low bands were
grouped rather than counted. Withdrawn rather than quietly corrected, and the
withdrawal recorded in the document, since an unchecked count is the precise
defect the document exists to correct. Threshold 6+, **21 survivors, 125
culled**, every survivor named by id. Stage 4 has NOT run: every score so far is
against a one-line summary written by someone else for someone else.

**THE HEADLESS BLOCKER WAS A PATH-SEPARATOR MISMATCH, NOT AN UNACCEPTED
DIALOG.** `.claude.json` held TWO keys for one directory - `C:\RedMoon` True and
`C:/RedMoon` False - and headless reads the forward-slash form, so it discarded
all 13 `permissions.allow` entries. The workspace HAD been trusted. Fixed, RM's
key only, atomic, backed up. LW independently found the same bug with THREE keys
for one directory. RM's earlier "headless is NOT AUTHENTICATED" claim is
RETRACTED: there was no login error, and the second failure was `"model":
"rc-main"` set MACHINE-WIDE in the user-level settings. RM did not touch it -
it was RC's and machine-wide - and asked instead; RC deleted it on the finding
that the alias resolved for nobody.

**THE FIRST HOOK PROBE WAS INVALID AND ITS RESULT WAS A LIE.** Staged U+2014
under `_scratch/`, ran a headless commit, and it SUCCEEDED - which reads exactly
like "no gate fired". `_scratch` is on `ascii_guard.py`'s own skip list, so both
gates inspected the diff, found nothing they own and allowed it CORRECTLY.
Commit reset, HEAD restored. **A gate that stays silent because the probe gave
it nothing to catch is indistinguishable from a gate that is not wired** - the
mirror image of the two false NEGATIVES LW reported the same day. The fix that
made the retry trustworthy was to call `check_staged()` directly first and
confirm it returned a reason.

**AND THE VALID PROBE NEEDED A DISCRIMINATOR TO BE READABLE.** A plain
`git commit` was blocked, and that proved nothing: both the git hook and the
PreToolUse gate block, and the wording pointed at git, meaning the Bash tool had
run and git refused. `--no-verify` bypasses the git hook, so anything still
blocking must be the agent layer. It returned `precommit_gate.py`'s own
`"Commit blocked:"` string with HEAD unmoved. **RM's PreToolUse gate fires
headless under `bypassPermissions` on CLI 2.1.220 and covers `--no-verify`.**

DOCTRINE CORRECTED: RM has described the Claude-side gate as a backstop that
cannot fire under `--no-verify`. That is true of the `commit-msg` hook, which
strips the trailer through git, and FALSE of the PreToolUse ASCII gate, which
sits above git and is therefore the only cover for that channel. The two are
complementary, not redundant. Git hooks remain the floor because they survive a
human typing `git` in a terminal.

**RM DID NOT DUPLICATE LW'S PROBE.** The operator assigned the mechanism
question to LW; LW answered it (hooks DO fire on 2.1.220) and RC deliberately
abstained on the rule that one measurement gets one owner, because "two of us
agree" is not evidence. RM asked a different question about its own repo and
said so.

ALSO: a trailer audit across every surface came back clean - 0 of 106 commits on
`origin/master`, project `.claude/`, user-level commands and plugins, and there
is no `.github/` at all. And `RM-NEXT-SESSION.txt` now exists on the desktop,
matching the `LW-` and `RC-` convention it had been missing.

## 003h - Cycle 3 phases 2 and 3: the schema'd dump, and the boss health that is not on the prefab (2026-08-01)

Commits `863c16f` (the spike) and `a9d5428` (the living docs and this entry). **THE BLOODFORGE
INPUT SPIKE IS CLOSED** - phases 1, 2 and 3 all done, first roadmap movement in
six sessions.

State at close, one run each, re-run by the closing agent rather than taken from
a report: `python -m pytest` **382 passed in 19.86s, exit 0** (348 before),
`python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0,
`dotnet build -c Release -t:Rebuild` on the csproj **0 warnings, 0 errors**.

WHAT SHIPPED.

1. **`ability_stats`, new at schema_version 1, 1818 rows.** Keyed on the ability
   GROUP per ADR-007, selected by the marker component
   `AbilityGroupStartAbilitiesBuffer`. Carries cast time, post-cast time,
   cooldown, global cooldown, the damage coefficient, raw damage, damage type,
   the hit counts and the V Blood multiplier. Cast time resolves on 1815 rows,
   cooldown on 1818, and the full damage block on the 732 groups that reach a
   `_Hit` prefab. A group that deals no damage KEEPS its row with the
   coefficients omitted, never zeroed.

2. **`vbloods` to schema_version 2, `items` to 4.** Boss `physical_power`,
   `spell_power` and a four-key `resistances` map on all 65 rows;
   `ability_group_guids` on all 425 items, 563 links, `[]` where the item grants
   nothing.

3. **`/dump/statcontrol`, exploratory.** Emits every entity carrying a guid with
   ONE fixed list of typed reads, so a prefab and its live instance compare by
   VALUE. Phase 1 had proven a generic value reader impossible on this build
   twice over, so the readers here spell out their fields.

4. **An expected-count assertion on every table**, pinned to the build it was
   measured on. Cycle 2 earned this: four per-row gates passed 66 vblood rows
   over 65 distinct guids because every duplicate was byte-identical and the
   only symptom was the count. The pin stands DOWN loudly on any other build
   rather than silently, because a silent stand-down reads as a pass.

5. **ADR-007**, `docs/BLOODFORGE.md`'s input table rewritten from measurement,
   and ROADMAP gaps 1, 2 and 3 each closed or restated with evidence.

THE FINDINGS, each measured.

**A PREDICTED COUNT WOULD HAVE BEEN WRONG BY 344, AND NOTHING WOULD HAVE
NOTICED.** `ability_stats` was pinned at 1474 before the dump ran, on cycle 2's
figure, and MEASURED 1818. 1474 counted a NAME-selected population - prefabs
ending `_AbilityGroup` - and the shipped selector is the marker COMPONENT. 1476
of the 1818 carry that suffix; 341 use `_Group`, `_Abilitygroup`, `_UNUSED` and
others and are ability groups by component. A name-shaped selector would have
dropped all 341 silently. This is precisely why the spec demanded the count be
measured and pinned in the same commit. NOT RECONCILED and left visible: 1476 is
two above 1474.

**THE BOSS HEALTH POOL IS NOT ON THE PREFAB, AND THAT IS NOW MEASURED RATHER
THAN SUSPECTED.** `Health.MaxHealth` reads 0 on all 65 V Blood prefabs. The
phase 3 control settles what the zero means: on `CHAR_Vampire_Dracula_VBlood`,
**19 typed fields compared between the prefab (entity 29012) and the live
instance (322945), 17 IDENTICAL, 2 differing** - `Health.MaxHealth` and
`Health.Value`, both 0 against 8107. Every `UnitStats` field and
`UnitLevel.Level` agree exactly. So this is branch 3, confined to health, and it
is **NOT spawn scaling**: 0 to 8107 is not a ratio and there is no factor to
recover. `max_health` is DECLARED AND NEVER EMITTED, and a TTK denominator needs
a live world with the boss spawned. ROADMAP gap 1 is restated, not closed.

**A DEDUPE FIX TURNED A DUPLICATE INTO AN ORDER-DEPENDENT CHOICE.** A spawned
boss carries the SAME `PrefabGUID` as its prefab. Cycle 2 saw the pair as "66
vblood rows over 65 distinct" and fixed the COUNT by deduping on first write -
which silently made the row whichever of two DISAGREEING entities the world walk
reached first. The count looked right afterwards, which is why it survived a
cycle. The selector now requires the prefab marker.

**A GATE THAT HAD BEEN DEAD SINCE SCHEMA_VERSION 2.** `items.stats` became a
list when the first real dump showed a name-keyed map cannot carry
`ModificationType`. `core/table_deep.py` was not moved with it and kept routing
the field through the object-shaped mapping check, which returns early on a
list. So the one container whose schema description says the shallow gate cannot
see inside it was unvalidated by BOTH gates. Found while bumping the same table
to 4; fixed with negative tests that were proven red first.

**A COEFFICIENT THE SPEC DID NOT ASK FOR.**
`DealDamageParameters.MaterialModifiers` is 23 per-target-class multipliers, and
`VBlood` is one of them - MEASURED 0.33 to 1.0 over the 732 damage rows. It is
not in the spike spec's field list. It was found by reading the declared field
TYPES before writing the reader, and it is emitted because a boss-damage table
missing the boss multiplier would be wrong in exactly the direction nobody
checks. The other 22 are NOT ATTEMPTED.

**READ THE DECLARED TYPES, DO NOT ASSUME THEY ARE UNIFORM.** The four boss
resistances are NOT commensurable: `PhysicalResistance` and `SpellResistance`
are `ModifiableFloat`, `FireResistance` is a `ModifiableINT` RATING that only
becomes a reduction through the global `ResistanceData` block, and
`CorruptionDamageReduction` is already a reduction. Measured: physical and spell
are 0 on all 65, corruption is 0.5 on all 65, and only fire varies. No consumer
may average them. Also measured: `physical_power` EQUALS `spell_power` on every
row, 33 distinct values over 33 distinct levels, so both are level-derived
rather than per-boss authored.

**A NEGATIVE RESULT TAKEN TOO EARLY IS INDISTINGUISHABLE FROM A REAL ABSENCE.**
The first control run returned one entity, the prefab only, and looked like a
clean "there is no instance" finding. It was taken at about 5 s of server
uptime; at 20 s the instance was there with 151 components. The `Unload()`
lesson in a new place - poll for the SUBJECT, not just for `ready:true`.

COSTS AND RESIDUE, stated rather than buried.

- **The promoted `items` table lost its 425 `localization_guid` values.** The
  dump was taken on the dedicated server, where that join resolves 0 of 425 by
  cycle 2 measurement. Backed up to
  `_scratch\rmprobe\c3p2\items-client-v3-with-localization.json` and recoverable
  in one client dump. A host fact, not a regression, but it is owed back.
- `core/tables.py` is FROZEN and gained one line - `ability_stats` in
  `TABLE_NAMES`. The approved spec names that file as the shallow-gate home for
  the new table, so spec approval was read as covering it. Flagged rather than
  assumed.
- `test_item_stats_are_read_one_hop_off_the_item_prefab` banned the `BuffGuid`
  token file-wide. Phase 1 showed that ban too broad: `BuffGuid` is the ONLY
  route to the abilities an item grants and is wrong only for STATS. Narrowed to
  the stat reader by method rather than relaxed away.

WHAT THIS DOES NOT PROVE. All six acceptance criteria are about SOURCING INPUTS.
None asks whether the math over them is right, so all six can pass with a
confidently wrong time-to-kill. No TTK was published to any surface this
session. ROADMAP gap 7 must be settled before the combat-math spec opens.

## 003g - Three-project interop: the shared governor, port 8770, and a gate that read the wrong tree (2026-08-01)

Commits `b1b6b2d` (inbox out of the port scan), `6cfc614` (backlog plus memory
seed), `a3fa2f6` (phase 3 counts and ratios), `91b9ed2` (the gate fix),
`7d735da` (port 8770 and the shared governor), `370c019` (bucket held at 2) and
`9151d61` (this entry). **NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 still has not
started. All of this arrived from a cross-project handoff, not the roadmap.

State at close, one run: `python -m pytest` **348 passed in 20.15s, exit 0**
(335 before, plus 13 new), `python tools/ascii_guard.py` exit 0, `ruff` clean.

WHAT SHIPPED.

1. **The sibling inbox is out of the port scan.** RC opened a handoff channel at
   `moon_sync_inbox/` and asked for a `.gitignore` line. That was the LESSER
   HALF: the foreign-port guard walks the WORKING TREE via `rglob`, not tracked
   files, so gitignoring it changes nothing. RC's block is 8888-8895 and three of
   those are in `FORBIDDEN`, so the next note delivered as `.json` or `.ps1`
   rather than `.md` would have failed the suite on content Red Moon does not
   own. Latent, not live - `.md` is not a scanned suffix. Fixed in
   `SKIPPED_DIR_PARTS`, proven red by planting a real `.json` in the inbox.

2. **`tools/precommit_gate.py`, two defects, both found while probing something
   else.** Frozen file, changed under explicit operator approval.
   - It tested `"git commit" in command`, so any command merely QUOTING the
     phrase was gated against whatever happened to be staged. It denied this
     session's own headless probe for exactly that reason.
   - **The structural one: `main()` called `check_staged()` with no argument**,
     so it inspected the hardcoded main tree no matter where the command ran. A
     commit inside a WORKTREE was gated against MAIN's staging area while its own
     was never read. Every headless design on offer is worktree-based, which made
     the Claude-side gate decorative in precisely the runs it exists to guard.
   Five characterization tests red first, then verified END TO END against a live
   worktree - a phrase-mention returns nothing, and both a `cwd`-based and a
   `git -C` worktree commit return a deny naming the worktree's own file. Both
   would have passed before.

3. **Port 8770 for the headless control plane**, on the FLOOR of the block.
   `core/ports.py` is frozen; operator-approved. ADR-003 amended with the block
   reservation 8770-8789 and the split - infrastructure 8770-8776, game services
   8777 and up. `RmPorts.g.cs` verified unchanged: the generator emits only the
   two bridge ports.

4. **Red Moon joined the machine-wide slot governor.** `ops/loop/slots.py`
   vendored BYTE-IDENTICAL and pinned by a SHA256 file digest (not a commit
   hash) in `tests/test_slots.py`. Its project-neutrality was VERIFIED rather
   than trusted, and it passes RM's ruff
   and ASCII gates unmodified. `CLAUDE.md`'s standalone claim was FALSE the
   moment this landed and was corrected in the same commit rather than left to
   rot: RM now shares one file of code and one directory of data, and still
   shares no keys, no ports and no task namespace.

WHAT WAS MEASURED AND CAME BACK NEGATIVE.

**Phase 0 of the headless plan is INCONCLUSIVE, not passed.** The probe never
reached its question: `claude -p --permission-mode bypassPermissions` exits 1
because headless is NOT AUTHENTICATED on this box and `C:\RedMoon` is NOT A
TRUSTED WORKSPACE, which discards all 13 `permissions.allow` entries. RC's
measurement that PreToolUse hooks die headless is RC's, on RC's machine, and is
recorded as UNREPRODUCED here. The trust finding is the sharper one: a headless
worker would run under a DIFFERENT permission set than the interactive session
that wrote its prompt.

THE LESSONS, each paid for.

- **A void closure returns a verdict to neutral, not to good.** A 119-item
  MCP re-triage inherited from RC was re-scored for RM and adversarially
  challenged: 119/119 reviewed, **37 overturns, every one downward, nothing
  above 5**. The scoring agents correctly voided RC's closes that cited
  RC-only assets, then treated "RC's reason was wrong" as evidence the tool was
  right. Four falsifications killed most of it - `.claude/` is five files,
  `ops/runtime/` and `logs/` do not exist, `core` plus `tools` is 2,730 lines,
  and `precommit_gate.py` already fires PreToolUse.
- **The corpus addressed the wrong axis entirely.** All 119 entries are
  developer tooling; cycle 3 is blocked on measuring a game binary. Verdict:
  adopt nothing.
- **A fix can reintroduce the bug it fixes.** Tokenizing with
  `shlex.split(posix=True)` eats backslashes, so `git -C C:\RedMoon` resolves to
  a nonexistent `C:RedMoon` and falls back to the main tree - defect 2 restored
  through the fix for defect 1. Caught by a failing test, not by review.
- **Two of RM's own claims were wrong and a sibling caught both.** 8781/8782
  were "the free ones" - true only about the interior of the used region; the
  block floor 8770-8776 was never allocated at all. And RM proposed N=3 for the
  bucket, sound in general and wrong for this machine: LegionWallpaper is the
  only GPU-heavy participant and its GPU mutex was DECLARED BUT ACQUIRED BY
  NOTHING, so a third lane permitted unserialized CUDA. Withdrawn the same day.
- **A guard fired correctly twice mid-session**, which is the system working:
  the memory-seed mirror refused two unseeded entries, and ADR-003's consistency
  test refused an undocumented port.

RESIDUE, deliberately open. Phase 0's two preflight checks (assert
authenticated, assert workspace trusted) are unbuilt and are the next action on
that track. The shared `slots.py` docstring still says TWO repos; correcting it
needs a coordinated three-tree re-pin and RM will not move first. RC's copy of
the governor is still unhashed by RC - two of three digests confirmed.

## 003f - The orphaned-hook guard, and the fresh-clone ceiling (2026-07-26)

Commits `8f632b6` (the guard test), `9a624c3` (gc and the latent LFS risk) and
`b24ce0e` (this entry). **NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 has still
not started and the operator gate on the phase 1 component inventory is STILL
OPEN. Harness work, arriving from a cross-project handoff rather than the
roadmap.

State at close, one run: `python -m pytest` **335 passed in 18.73s, exit 0**
(334 before, plus 1 new), `python tools/ascii_guard.py` exit 0.

WHAT SHIPPED.

1. **`test_no_orphaned_hooks_left_behind_in_git_hooks`.** Setting
   `core.hooksPath` silently disables whatever `.git/hooks` already held. On the
   other project on this box that cost a Git LFS `pre-push`, so pushes looked
   clean while LFS content never reached the remote. It fails in the direction
   that loses data AND reports success, which is why it is asserted rather than
   noted. RM is clean today but PRE-ARMED for it: `filter.lfs.required=true` is
   configured, and `git lfs install` writes to `.git/hooks`, which
   `core.hooksPath` makes git ignore. The first LFS-tracked file added here
   arrives with an inert pre-push.
2. **The rewrite's backups were deleted and gc'd** with `--prune=now` after the
   history was confirmed good. This is what made the ledger SHA anchor a real
   check for the first time: the pre-rewrite objects no longer resolve, so
   `test_every_sha_the_ledger_cites_resolves` passing now proves the 26-citation
   remap complete rather than merely resolving off lingering objects.

VERIFICATION, AND THE TWO PROBES THAT MATTERED MORE THAN THE SUITE.

The guard test asserts a condition that WAS ALREADY TRUE, so it could not fail
first and could have shipped vacuously green - a typo'd path would look
identical. It was proven by injecting a fake `.git/hooks/pre-push`, watching it
go red naming that file, and removing it. A guard nobody has seen red is not a
guard.

`core.hooksPath` is LOCAL config and is NOT cloned, so a tracked hooks directory
is inert on arrival however correct it is. Verified by actually cloning: a fresh
`git clone` of this repo has `core.hooksPath` unset and zero active hooks. RM
covers it at `docs/OPERATIONS.md` ("Wire the commit gate, once per clone",
marked mandatory) and by two suite failures there, one printing the remediation
command. The orphaned-hook test correctly SKIPPED in that clone, exercising its
skip branch for real. THE RESIDUAL GAP IS UNCLOSEABLE: between clone and first
verification, nothing has told the operator. Git never clones hooks by design.
The ceiling is loud-on-first-verification, not safe-on-arrival.

## 003e - The co-author trailer policy, enforced and backfilled (2026-07-26)

Commits `0cb03a1` (hook plus tests), `bbc2a81` (CLAUDE.md hard rule), `f47acd3`
(citation remap) and `d49bc3f` (this entry), on top of a
history rewrite of 29 commits. **NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 has
still not started and the operator gate on the phase 1 component inventory is
STILL OPEN - four sessions running. Harness work that arrived from outside the
roadmap.

State at close, one run: `python -m pytest` **334 passed in 18.77s, exit 0**
(327 before, plus 7 new), `python tools/ascii_guard.py` exit 0.

WHAT SHIPPED.

1. **The gap.** Operator policy 2026-06-03 says never emit the Claude co-author
   trailer. Nothing enforced it. `core.hooksPath` selects `hooks/`, and `hooks/`
   held only the pre-commit pair - there was no commit-msg hook, tracked or
   active, and the string `Co-Authored-By` appeared nowhere in the repo. The
   agent harness instructs the model to append the trailer to every commit, so
   an unwritten policy lost to a default that fires constantly: 16 commits
   carried it, and the clean ones were clean by accident.
2. **`hooks/commit-msg` plus `hooks/commitmsg_hook.py`.** An sh shim mirroring
   `hooks/pre-commit`, and the rewrite behind it. It STRIPS AND WARNS to stderr
   rather than blocking, deliberately unlike the ASCII gate: a check that did
   not run did not pass, but a strip that did not run leaves one line the
   operator can still delete. Same reason a missing interpreter exits 0 here and
   1 there. A human co-author survives - the policy names the Claude trailer,
   not co-authorship. `ops/install_git_hooks.py` now requires both files, so
   `--check` fails on a clone that lacks them.
3. **The hard rule is written down.** `CLAUDE.md` states the policy AND states
   that the hook is a backstop, not a licence to emit the line. Behaviour living
   only in a hook is not a rule a reader can learn, and the harness default
   pushes the other way in every new session.
4. **The 16 commits were backfilled**, on explicit operator approval after the
   blast radius was measured: stripping 16 rewrites 29, because every descendant
   takes a new SHA, and all 29 were already pushed.

THE FALSE GREEN THIS ENTRY EXISTS TO RECORD. `test_every_sha_the_ledger_cites_resolves`
probes with `git cat-file -e`, which still resolves rewritten-away commits for
as long as the old objects sit in the object database, referenced by
`refs/original` and a backup branch. Immediately after the rewrite it went green
on all 36 cited SHAs while a third of them named commits no longer reachable
from master. THE TEST CANNOT SEE THIS CLASS OF DRIFT. The remap was verified
instead by grepping every tracked doc for every pre-rewrite SHA prefix, which
returns nothing. 26 citations moved across five files, and four of the five -
`ROADMAP.md`, `WAKEUP_NOTES.md`, `docs/OPERATIONS.md`, `docs/history_notes.md` -
are outside that test's scope entirely.

VERIFICATION THAT PROVED IT, not unit tests alone. The seven new tests call the
Python entry point directly, which cannot prove git for Windows runs the sh shim
through `core.hooksPath`. So the trailer was deliberately included in a real
`git commit -F` and the stored commit came back with an empty trailer field.

CROSS-CHECK AGAINST THE TWO TRAPS REPORTED FROM THE OTHER PROJECT ON THIS BOX.
Neither applies here, and both were re-probed live rather than reasoned about.
Trap 1, hooks installed into `.git/hooks` while `core.hooksPath` points
elsewhere: RM's `.git/hooks` holds nothing but `.sample` files, so there are no
inert duplicates to mislead. Trap 2, a pre-commit that invokes
`precommit_gate.py` with no arguments, where the gate reads a PreToolUse payload
from stdin, finds no `git commit` and self-gates to a silent no-op: the
one-liner DOES reproduce here, `python tools/precommit_gate.py < /dev/null`
exits 0, but RM never invokes that path. `hooks/precommit_hook.py` imports
`check_staged` directly. Settled end to end by staging an em-dash and running a
real `git commit`: `COMMIT BLOCKED by hooks/pre-commit`, `U+2014`, HEAD
unmoved. RM's gate is live.

## 003d - Two drift anchors, and six checks that already existed (2026-07-26)

Commits `d6bfdd9` (tests) and `ba8b5d9` (ledger, notes, handoff).
**NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 still has not
started and the operator gate on the phase 1 inventory is still open. This is
harness work that arrived from outside the roadmap.

WHAT SHIPPED. `tests/test_drift_anchors.py`, three tests, closing the only two
gaps a proposed eight-check drift guard actually had against this repo.

1. **Build-pin anchor.** The game build pin has about 97 tracked sites and
   nothing asserted they agree with the one CLAUDE.md declares, so a bump could
   land on some and silently miss others. The check reads the canonical pin out
   of CLAUDE.md rather than hardcoding it. The documented `v3` stale-trap pin is
   allowlisted BY VALUE, not by file, so it keeps its own identity instead of
   drifting onto the current pin. Historical records - `history_notes.md`, this
   ledger, `BRIDGE_SPIKES.md`, `WAKEUP_NOTES.md` and the dated
   `docs/superpowers/` specs - are excluded, because a superseded pin in a
   record of what was true is correct. Fixture pins are recognised BY SHAPE
   (majors 8 and 9, which V Rising cannot reach) rather than by exclusion of
   `tests/`, so a fixture asserting against the CURRENT build still has to move
   when the pin moves.
2. **Ledger SHA anchor.** Nothing verified the commit hashes this file cites by
   its own stated format. A hash written from a worktree slice does not survive
   cherry-pick, and the failure only surfaces when someone later tries to use
   the citation. Entry 003c needed exactly this backfill last session.

THE VERIFICATION THAT PROVED IT. Both anchors were confirmed to FAIL on injected
violations before being accepted, because a guard that cannot fail proves
nothing: a stale pin `1.1.12.0-r99000` appended to `docs/API.md` tripped the
first, and a fabricated eight-hex hash appended to this file tripped the second.
Each named the offending file, line and value. The working tree was restored and
`git status --porcelain` confirmed clean afterwards. Suite: **327 passed in
18.47s** (324 before, plus these 3), `python tools/ascii_guard.py` exit 0.

WHAT WAS DELIBERATELY NOT BUILT, AND WHY. The source proposed a standalone
`tools/drift_guard.py` carrying eight checks. Measured against this repo, six of
them already exist as tests: `test_claude_md_stays_under_the_size_budget`,
`test_live_memory_matches_the_committed_seed`, `test_memory_namespace_is_seeded`
(stricter than the proposal - an exact expected set, not a link parse),
`test_every_adr_file_is_listed_in_the_index`, `.claude/` being fully tracked,
and a counted-claim construct this repo does not have. Adding the script would
have duplicated them into a second place that runs only at wrap, where the tests
run on every `pytest`. The two real gaps became tests in the same suite instead.

THE LESSON, WHICH THE SOURCE DOC TAUGHT AND THEN EARNED. Its own headline advice
is to measure the shape before choosing a lever. Applied to itself, its central
premise - a 27-minute suite worth moving to CI - does not hold here: this suite
is 18.47s, there is no `.github/`, and overlapping doc-writing with a dispatched
CI run would have been pure overhead. Adopting the parts of an external process
doc that fit is only possible after measuring which parts those are.

## 003c - Cycle 3 phase 1: the component inventory (2026-07-26)

Commits `48a9215` (endpoint plus inventory) and `2fff79f` (ledger, notes,
ROADMAP). Exploratory only: no schema, no table, no ingest gate, no
combat math. Stops at the operator gate by design.

WHAT SHIPPED. `GET /dump/components` in `bridge/src/RedMoon.Bridge/`, taking
guid, or name as a prefix plus limit, plus `instanced=1`. It ENUMERATES an
entity's actual component types and prints all of them with declared fields,
nested value types expanded and enum members named. It never calls
`HasComponent` on a hoped-for name, waits on `GameDataInitialized`, and rides
the existing main-thread handoff rather than opening a second one. Plus the
inventory itself in `docs/BRIDGE_SPIKES.md`, all four subject classes at the
spec's minimum samples: three `CHAR_*_VBlood` prefabs at levels 16, 57 and 91
(150 components each), four ability groups across schools including a WEAPON
group, two weapon families, and a live instanced boss.

THE FINDING THAT COST THE MOST AND IS WORTH THE MOST. The endpoint reads NAMES
and not VALUES, and that is measured rather than convenient. Two generic value
readers were built and both failed. Managed reflection through
`EntityManagerDebug.GetComponentBoxed` gave correct field names and GARBAGE
values: every `Int32` read 539327184 and every `Single` read 1.402156E-19, the
same number everywhere. Raw il2cpp field offsets off that same boxed pointer
HARD CRASHED the dedicated server on the first request, twice, as did the raw
`il2cpp_class_get_fields` iterator. `GetComponentBoxed` is not backed by real
chunk memory on this build.

What caught the first failure was a control that cost nothing: every entity
carries `Stunlock.Core.PrefabGUID`, whose value the same response ALREADY states
from a typed read. The reader said 539327184 where the truth was -327335305.
Without it the numbers would have shipped and every line of the inventory would
have been fiction - `items.tier` again, caught before paper rather than after.

THE 14 FIELDS. `NOT ATTEMPTED` is EMPTY. T1 `ProjectM.Health.MaxHealth`. T2
`UnitStats.PhysicalResistance`, `.SpellResistance`, `.FireResistance`,
`.CorruptionDamageReduction`, and Holy, Silver and Garlic PROVEN ABSENT from the
unit across 150 enumerated components. A1 `AbilityCastTimeData.MaxCastTime`. A2
`AbilityCooldownData.Cooldown`. A3 `DealDamageParameters.MainFactor`. A4
`.MainType`. A5 proven absent as a field. A6 partial, a counting job. L1 closed
as a four-hop chain ending at `ReplaceAbilityOnSlotBuff.NewGroupId`.

TWO CYCLE 2 STATEMENTS CORRECTED by a live component list, the same way
`EquippableData` was. `ProjectM.AbilitySpellSchool` DOES exist, on the ability
group, carrying school guid and tier; three metadata scans missed it. And
`ProjectM.WeaponAbilityData` tells a weapon group from a spell group by
COMPONENT, which is what dissolves ROADMAP cycle 3 gap 3.

VERIFIED. `python -m pytest` **324 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` exit 0
with 0 warnings. The liveness assertion holds: instanced Dracula is entity 322916
with no `Unity.Entities.Prefab` against prefab entity 29012 with it.

## 003b - The precommit gate wired as a real git hook (2026-07-26)

Commit `64eb9e8`.

THE PROBLEM. `tools/precommit_gate.py` has held the ASCII and ruff checks since
cycle 1 and NOTHING CALLED IT. `.git/hooks` carried only `.sample` files and
`core.hooksPath` was unset. That is how a UTF-8 BOM reached `master` in `56be457`
while `python tools/ascii_guard.py` exited 1 in the same shell chain: Windows
PowerShell 5.1 has no `&&`, so a verification joined with `;` is a log line
rather than a gate.

WHAT SHIPPED, entirely OUTSIDE the two frozen files. `hooks/pre-commit`, a sh
shim at mode 100755 where a missing interpreter FAILS the commit rather than
passing quietly. `hooks/precommit_hook.py`, which calls the frozen
`check_staged()` and turns a non-empty reason list into a non-zero exit - the
only thing git reads. `precommit_gate.main()` speaks Claude Code's PreToolUse
JSON protocol and always exits 0, so git could never have learned a refusal from
it. `hooks/` is COMMITTED and selected by `core.hooksPath`, because `.git/hooks`
is not version controlled and a fresh clone would inherit nothing.
`ops/install_git_hooks.py` makes that one config command discoverable, and
`--check` is what the suite asserts.

VERIFIED AGAINST GIT, not only against the unit tests. Seven failing tests first
per TDD. Then a deliberate BOM file was staged in this repo and `git commit` was
REFUSED: `COMMIT BLOCKED by hooks/pre-commit`, `docs/bom_probe.md:1:1 non-ascii
U+FEFF`, exit 1, HEAD unchanged. A passing unit test is not evidence that git
rejects anything.

## 003a - Cycle 3 spike SPEC approved, no implementation (2026-07-26)

Docs only. No production code changed, by instruction: cycle 3 cannot open by
writing combat math while two of its declared inputs have no source.

WHAT SHIPPED. `docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md`,
342 lines, operator-approved section by section. `ROADMAP.md` cycle 3 now names
two specs where it carried one TBD: this spike, then the combat math opened only
against what the spike returns.

THE PROBLEM IT ANSWERS. `vbloods` rows carry `level`, `name` and `prefab_guid`
and no stat line; `abilities` rows carry identity, school and a partial damage
type and no coefficients. Time-to-kill is the engine's headline output and its
denominator is not on disk. A TTK against an assumed boss health would be the
`items.tier` fabrication with a larger blast radius.

THE FIVE DECISIONS. Scope is the spike alone with a declared consumer contract.
The boss stat line reads from the PREFAB with a live instance as a negative
control. Coefficients key on the ability GROUP across all 1474 groups in a new
`ability_stats` table, which DISSOLVES ROADMAP gap 3 because a weapon ability
needs no `<Weapon>SpellSchoolAsset` to have coefficients, only a
weapon-to-group link - ADR-007 will record that. A throwaway
`/dump/components` endpoint runs first, printing full component lists, with an
operator gate before any schema. The required-field contract includes the
level/power-difference term, because a TTK omitting it is wrong by a factor and
no test can see that.

THE CLOSURE RULE. All 14 required fields end as SOURCED with component and field
named, or PROVEN ABSENT in the `items.tier` pattern with the negative control
that makes the absence readable. NOT ATTEMPTED must be empty. No field may be
defaulted to `1.0`, `0` or a plausible guess.

FOUR CYCLE 2 LESSONS ENCODED AS STRUCTURE, not advice, because advice does not
survive a subagent and a numbered acceptance criterion does: full component
lists rather than a guessed `HasComponent`; minimum sample counts written into
the protocol, after the `blood_types` near miss came from sampling the two
unrepresentative first rows; an expected-count assertion on every table, after
`vbloods` 66 survived four per-row gates on byte-identical duplicates; and a
stub-proof liveness assertion, after `StateReader.cs` read the PlayerCharacter
template at 0 warnings and 284 green tests.

SELF-REVIEW FIXED TWO AMBIGUITIES before commit. `ability_stats` has no expected
count before the spike runs, so the measured count is PINNED as a constant in the
same commit that lands the table, making the assertion a drift detector rather
than a rubber stamp. And `/dump/components` is no longer described as "ungated"
while also being gated on `GameDataInitialized` - readiness precondition and
validation gate are now distinguished.

HOUSEKEEPING, on operator instruction. There was NO stray worktree;
`git worktree list` showed only `C:/RedMoon [master]`. The stale item was a
BRANCH, `cycle-2-bridge`, verified fully merged (`--is-ancestor` exit 0,
`master..cycle-2-bridge` empty) before deletion locally and on `origin`.
`Remus3/RedMoon` was made PUBLIC after scanning history: `API-Key-Claude.txt`
has never been committed on any ref and no key/secret/token/pem/credential/
password path was ever added. The stale repo description was refreshed.

VERIFICATION. `python -m pytest` 317 passed, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, all re-run after the last edit. No C#
changed so no `dotnet build` was run. Note: this repo's pytest config suppresses
the summary line, so the count was obtained by counting progress characters -
317 dots, 0 of `F/E/s/x`, exit 0 - rather than reported from memory.

STATUS. Cycle 3 is OPEN. The spec is approved and nothing is implemented.

Commits: `c95c47f` (spec plus `ROADMAP.md`), `56be457` (this entry, wakeup notes,
the history archive and the phase 1 bootstrap), `2830bfd` (a BOM fix - see below).

PROCESS FAILURE IN THIS SESSION, recorded because it nearly shipped silently.
Archiving the oldest wakeup session was done mechanically with PowerShell
`Set-Content -Encoding utf8`, which on PowerShell 5.1 writes a UTF-8 BOM. That
put a U+FEFF at byte 0 of `WAKEUP_NOTES.md` and `ascii_guard` exited 1 - the
exact class of defect the guard exists for, given this project's PowerShell
parse-failure history. The guard caught it. What did NOT catch it was the shell
chain: `guard; git add; git commit` uses `;`, so the commit ran on a FAILED gate
and `56be457` landed with the BOM in it. Fixed in `2830bfd`, guard back to exit 0.
The lesson is not "remember the BOM" - it is that a verification step chained
with `;` is not a gate, it is a log line. Chain gates with `if ($?)` or run them
as a separate call whose exit code is read before proceeding.

## 002g - Cycle 2 CLOSED (2026-07-26)

Docs only. No code changed.

WHAT CLOSED. Cycle 2's charter was live item and ability stat data on a local
port, and the data that cannot be read offline is now on disk: `items` 425,
`recipes` 663, `abilities` 54, `vbloods` 65, `blood_types` 13 - every table in
`core/tables.py`, promoted from a client dump in 103 ms. All six original spikes
S1 to S6 are closed, plus S3a and S7. `/state` returns live data and
`bridge_probe --motion-diff --expect-host client` PASSES. One assembly loads in
both hosts (ADR-004) and the port is a pure function of the detected host
(ADR-005).

WHAT THIS ENTRY ACTUALLY DID. `ROADMAP.md`'s cycle 2 section was a running log
appended to six times across six sessions, carrying superseded numbers inline
(most visibly `vbloods` 66 with its own correction note beside it). It is now a
settled record of what was measured, and cycle 3 is marked CURRENT.
`docs/ARCHITECTURE.md` had drifted a full cycle behind - it still read "Nothing
runs as a service in cycle 1" and listed `bridge/` as planned, with a module map
naming three files out of the sixteen that exist. It now describes the shipped
shape, the real live data path, and the host-specific localization join.

THE RESIDUE, and why it does not block cycle 3. Three items were weighed against
closing:

1. **4 unmapped recipes.** Confirmed to be recipe prefabs with an empty ITEM
   output buffer, consistent with the `RecipeOutputUnitBuffer` hypothesis but not
   proven to be it. They produce units, not items, and no cycle 3 consumer reads
   them. Closing this would buy a label, not data.
2. **`items.tier`.** There is nothing left to spend a session on. No per-item
   source exists on this build (67 `Tier`-shaped fields across 169 assemblies,
   zero per item; `Rarity` zero hits anywhere) and both derivations were rejected
   on evidence. DECLARED and OMITTED is already the correct final state. Absent
   means unsourced, never zero.
3. **Weapon abilities produce no `abilities` row.** This one has teeth, and it is
   the reason the close is not silent about it. Bloodforge computes weapon DPS
   and there is no `<Weapon>SpellSchoolAsset` to source the school from. It is
   carried into cycle 3 as a NAMED INPUT GAP in `ROADMAP.md` rather than a
   footnote, so no cycle 3 code scaffolds weapon damage on an assumed source.

TWO CYCLE 3 BLOCKERS FOUND AT CLOSE, by reading the promoted ROWS rather than
the schema. Both were about to become cycle 3 assumptions:

1. **There is no BOSS STAT LINE.** `vbloods` rows carry exactly `level`, `name`
   and `prefab_guid`. No health, no resistances, no damage. `docs/BLOODFORGE.md`
   named `tables/vbloods.json` as the source for "Boss stat line and
   resistances" - a claim written in cycle 1, never checked against real rows,
   and false. Time-to-kill is the engine's headline output and its denominator
   is not on disk.
2. **There are no ABILITY COEFFICIENTS.** `abilities` carries identity, school
   and (16 of 54) a damage type. No cast time, no cooldown, no damage scalar.

The player side is NOT a gap and was checked in the same pass: 203 of 205 weapon
items carry real `PhysicalPower` or `SpellPower` values over 29 distinct stat
types, each with an explicit `modification`. The missing half is the TARGET side
and the ABILITY side.

`docs/BLOODFORGE.md`'s input table is corrected to carry a per-input STATUS
column rather than a bare source, and `ROADMAP.md` cycle 3 now lists six named
gaps instead of four. CONSEQUENCE recorded in both: cycle 3 cannot open by
writing combat math. It opens by settling where those two inputs come from,
because a TTK against an assumed boss health is the `items.tier` fabrication
with a larger blast radius.

VERIFICATION: `python -m pytest` 317 passed, `python tools/ascii_guard.py` exit
0, `python -m ruff check .` clean. Commits `8bea7fe` (the close) and `6cf8f0a` (the
two blockers and the doc corrections).

THE LESSON CYCLE 2 LEAVES BEHIND, promoted out of the session notes because it
outlives them: a real measurement can answer the RIGHT question about the WRONG
SUBJECT. "0 of 425" was correct, reproducible and had a proper negative control,
and it described a headless host rather than the game. Before generalizing a
measurement, check what it was taken OF.

## 002f - Cycle 2 part 6: the client host, and a wrong number four gates could not see (2026-07-26)

Code and docs on `master`, commit `b4e360c`.

WHAT SHIPPED. The bridge now reads the localization join, inverts the station
link, and refuses to emit a row twice. Both hosts ran the SAME binary
CONCURRENTLY - dedicated server on 8780, live client on 8777 - which is what
makes every comparison below like-for-like rather than a comparison of builds.

| table | rows | schema_version | changed |
|---|---|---|---|
| `items` | 425 | 3 | all 425 now carry `localization_guid` |
| `recipes` | 663 | 2 | `station_guid` retired for `station_guids` (ADR-006) |
| `abilities` | 54 | 1 | was 56 rows over 54 guids |
| `vbloods` | **65** | 1 | **was recorded as 66; the 66th was a duplicate** |
| `blood_types` | 13 | 2 | unchanged |

Promoted from the CLIENT dump, 103 ms, by `tools/rmdata_ingest.py --accept`.

VERIFICATION, all four re-run by this session after the last edit rather than
taken from a report: `python -m pytest` 317 passed, `python -m ruff check .`
clean, `python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild`
exit 0 with 0 warnings. Plus the live evidence: two dumps taken minutes apart
from both hosts, diffed row by row.

THE FOUR MEASUREMENTS.

1. **Client item COMPONENT data is IDENTICAL to the server's.** The open
   question was never counts - two 425-row tables can disagree on every field -
   so both dumps were diffed row by row, keyed on `prefab_guid`, every field
   compared. ZERO differing rows across all five tables. Either host may serve
   the dump.

2. **`localization_guid` is WRITABLE on the CLIENT and not on the server.** Same
   binary, same call: `resolved=425` in the client, `resolved=0` in the
   dedicated server. All 425 client guids are real `strings.json` keys, resolving
   to real display names. The recorded ABSENCE was a true statement about a
   HEADLESS HOST that had been written down as a statement about the build. Every
   dump now carries its own `localization` counters and the ingest prints them,
   so a saved payload states which host produced it.

3. **`vbloods` is 65, not 66, and `abilities` was emitting 56 rows over 54
   guids.** More than one ENTITY can carry the same `PrefabGUID`, and the dumper
   wrote one row per entity, so `CHAR_Vampire_Dracula_VBlood` and two blood
   ability groups were counted twice. Every duplicate pair was BYTE-IDENTICAL,
   which is why the shallow gate, the deep gate, the schema and the census all
   passed it: each inspects one row at a time and each of those rows was
   individually perfect. The only symptom was the count - and that count was
   already in `ROADMAP.md` and in ledger 002e as a finding. Fixed at BOTH ends:
   the dumper dedupes on first write, and `duplicate_key_problems` in the ingest
   refuses the whole promotion.

4. **`recipes.station_guids` is ruled and writable (ADR-006).** 911 unique
   (recipe, station) pairs from 942 raw buffer references. 575 recipes reach at
   least one station, 88 reach none, and 19 sit at TWELVE stations each - which
   is exactly why a first-station-wins value was barred rather than merely
   discouraged.

5. **`Unload()` does NOT run on a normal exit, and that is CLOSED.** Two quits
   on the uninstrumented build produced no shutdown line, but since `Unload()`
   logged nothing at all that silence fit three hypotheses equally. It now also
   appends to `BepInEx\redmoon-unload.log` outside BepInEx's logging. On the
   instrumented build a normal in-game quit left the marker ABSENT, the log
   unchanged, and 8777 without a LISTEN. Two independent channels both silent
   eliminates "the pipeline was gone first", so BepInEx 6 IL2CPP does not invoke
   `BasePlugin.Unload()` at shutdown. The control that makes the silence
   readable: the observed run provably carried the instrumented build, because
   the dump it served included `station_guids`. Benign - R11 already measured the
   hard-kill path and a normal exit is identical to it.

STILL OPEN, and deliberately not claimed.
`abilities` covers spell-school abilities only - weapon abilities have no school
asset - and 38 of the 54 rows carry no `damage_type` because the projectile deals
the damage. 4 recipes remain unmapped on an empty item output buffer.

THE LESSON, one layer up from last session's. Last session recorded "a real
measurement can still answer the wrong question". This one adds: a real
measurement can answer the RIGHT question about the WRONG SUBJECT. The `0 of 425`
localization result was correct, reproducible, and carried a proper negative
control - and it described a host, not a game. Before generalizing a measurement,
check what it was actually taken OF.

---

## 002e - Cycle 2 part 5: all five tables populated, and two recorded findings corrected (2026-07-26)

Code and docs on `master`, commit `417060f`.

WHAT SHIPPED. `PrefabDumper.cs` now writes every table in `core/tables.py`. One
live `/dump/prefabs` against the standalone dedicated server, 714 ms, validated
and promoted by `tools/rmdata_ingest.py --accept`:

| table | rows | schema_version |
|---|---|---|
| `items` | 425 | 3 |
| `recipes` | 663 | 1 |
| `abilities` | 54 | 1 |
| `vbloods` | 66 | 1 |
| `blood_types` | 13 | 2 |

VERIFICATION, all four re-run by this session after the last edit rather than
taken from a report: `python -m pytest` 289 passed, `python -m ruff check .`
clean, `python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild`
exit 0 with 0 warnings.

HOW IT WAS MEASURED. Three runs of an extended `_scratch\rmprobe` in the
dedicated server, each behind the `GameDataInitialized` gate, printing FULL
component lists rather than probing for guessed component names. Every number is
in `docs/BRIDGE_SPIKES.md`, "The cycle 2 measurement pass".

THE TWO CORRECTIONS, both to findings this project had already recorded as
measured:

1. The ability school is NOT `DealDamageParameters.MainType`. That is the damage
   type. `abilities.school` comes from `SpellSchoolAbility.AbilityGroup` on the
   `<School>SpellSchoolAsset` prefab - 9 abilities in each of six schools.
2. The V Blood level is NOT `VBloodConsumeSource.Tier`, a five-valued
   `SpellSchoolProgressionTier`. It is `UnitLevel.Level`, measured 16 to 91.

THE SCHEMA AMENDMENT, ruled on evidence. `blood_types` goes to `schema_version`
2. The version 1 nested contract - a numeric `quality` threshold and a
name-to-number `stats` map - is wrong on both halves: no threshold field exists,
and every bonus magnitude reads 0 because it is scaled from blood quality at
runtime. `core/table_deep.py` now asserts slot, 1-based tier, `buff_guid`,
`buff_name` and a `stats` list of `{stat, modification}`, with tiers ascending
WITHIN a slot - a global ascent check would reject the real primary-1..5-then-
secondary-1..4 row, and there is a regression test on exactly that.

TWO NEGATIVES THAT ARE RESULTS. `recipes.station_guid` is reverse-only and
one-to-many (942 station references over 663 recipes), so the singular schema
field owes a decision. The runtime localization join is ABSENT on the server
host: 0 of 425 equippables resolve, with the without-logging overload as the
control. S7 had inferred both would work.

OPERATOR FIX, out of band: the flashing PowerShell consoles were the `statusLine`
command in the user-level `settings.json`, now running `-NonInteractive
-WindowStyle Hidden` with the original backed up beside it.

## 002d - Cycle 2 part 4: /state goes live, and two fabricated fields are retired (2026-07-26)

Code commit `9b1f58f` on `master`, docs commit `d0bc2b0` carrying this entry.
No merge hash: `cycle-2-bridge` was
fast-forwarded into `master` this session at `6acbc66` and work continued
directly on `master`, so the code commit IS the carrying hash. The
fast-forward was deliberate - a `merge:` commit would have recorded a cycle 2
completion that has not happened.

Shipped `bridge/src/RedMoon.Bridge/StateReader.cs` plus `tests/test_bridge_state.py`,
the `BridgeServer.cs` `/state` wiring, `data/schemas/items.schema.json` at
`schema_version` 3, the `PrefabDumper.cs` tier removal, and the
`.claude/settings.json` visual-tool permission grant.

Verified in the main session rather than taken from the build agent:
`python -m pytest` **284 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release` exit 0 with
0 warnings. The agent's claims were re-run independently before any were
believed.

Proven LIVE, which is the entire point of this entry. `bridge_probe
--motion-diff --expect-host client` **PASSES** with the operator moving:
position `-868.508972, -1788.14209` to `-862.950745, -1784.278076`. Vitals read
`health 231.899994` against `max_health 231.905533`, a fractional mismatch no
default constructor produces.

The finding worth carrying: **a green suite and a clean build proved nothing
here.** The first StateReader compiled at 0 warnings, passed all 284 tests, and
returned `state_reason: ok` with full vitals while reading the `PlayerCharacter`
PREFAB TEMPLATE on a server with nobody connected - position `0,0,0`, health
`125/125`. Only `--motion-diff` caught it, because two samples five seconds
apart were byte-identical. The fix skips `Unity.Entities.Prefab`, and the same
empty server then honestly returns `no_character` with `state: null`, which is a
real negative control rather than a passing assertion.

S1(b) CLOSED. `Client_0` fills `0 -> 7005 -> 16352 -> 30484` with
`GameDataInitialized` flipping as it settles; census `total=85591
withPrefabGUID=31953` in 95 ms. The client map is LARGER than the server's by
7975 entities. "The client can serve a dump" is now proven and writable. A
near-miss is recorded in `BRIDGE_SPIKES.md`: the client census line reads
`equip=2 recipe=2`, which looks like "no item data", but the SERVER line reads
the same and produced 425 items - those counters are capped deep-dump selectors,
evidence of nothing.

`items.tier` retired at `schema_version` 3 after an exhaustive scan of all 169
interop assemblies returned 67 `Tier`-shaped fields and ZERO per-item-prefab.
Both derivations rejected on evidence, including the tempting
`ArmorLevelSource.Level` which is exactly `10 x tier` on 117 of 425 rows.

**Data backfill DONE, not merely prevented.** The 425 rows already on disk
carried the fabricated `tier: 0`. The plugin was rebuilt, redeployed, the
standalone server relaunched, `/dump/prefabs` re-taken and promoted: live
`items.json` is now `schema_version` 3, 425 rows, **0 carrying `tier`**, with
counts identical to before (items 425, recipes 663, 899 stat entries) so it is a
true like-for-like recovery. Note `data/rmdata/` is gitignored
(`.gitignore:16`), so the backfill lives on disk and is reproducible from the
dump rather than committed.

Also closed: the localization join is MEASURED ABSENT offline (0 of 425 on
seven key forms), R17's reference set extends to `Unity.Transforms` by
measurement, and the false `PrefabLookupMap` localization claim in
`BRIDGE_SPIKES.md` is corrected.

STILL OPEN and deliberately not claimed: whether client item COMPONENT data
matches the server's (only the prefab maps were compared), `recipes.station_guid`,
the ability-group-to-`_Hit` join, `VBloodConsumeSource.Tier` value measurement,
and `Unload()`'s graceful path.

## 002c - Cycle 2 part 3: RedMoon.Bridge ships and the first real dump lands (2026-07-26)

Shipped `bridge/src/RedMoon.Bridge/` - `RedMoon.Bridge.csproj`, `HostDetect.cs`,
`Plugin.cs`, `BridgeServer.cs`, `PrefabDumper.cs` - plus `tests/test_bridge_project.py`.

Verified in the main session rather than taken from the build agent: `dotnet
build -c Release` exit 0 with 0 warnings, `python -m pytest` 272 passed, `ruff`
clean, `ascii_guard` exit 0, no port literal in any C# file, no `BuffGuid`
follow in `PrefabDumper.cs`.

Proven LIVE in the dedicated server, not just compiled. Banner
`RedMoon.Bridge v0.1.0 host=server port=8780` carries all three contract tokens.
`/health` reported `ready:false` at `prefab_count:3212` and `ready:true` at
23583, so the readiness gate was observed doing its job mid-load.
`/dump/prefabs` returned 425 items and 663 recipes in 276 ms with 4 unmapped.
`rmdata_ingest` without `--accept` produced the shape census, then `--accept`
promoted it: `items.json` 425 rows at `schema_version` 2, `recipes.json` 663.

Schema ruling, made on the census rather than in advance: `items.stats` becomes
an array because three modification kinds occur (Add 665, AddToBase 232,
MultiplyBaseAdd 2). The duplicate-StatType argument for the same change was
measured FALSE (0 of 425) and discarded.

Corrected four recorded findings: `items.stats` is one hop not two; the prefab
count is 23583 not 1189; the ability school is `DealDamageParameters.MainType`
on the `_Hit` entity; `vbloods` had the wrong marker component.

Commits `7a06e61`, `98d6a09`, `87d80c8`, `1f76090`, `7568323` on `cycle-2-bridge`.

Cycle 2 is NOT done. Open: the in-game client sample, the fabricated
`items.tier`, `items.name` being the prefab name, `StateReader.cs`, and
`recipes.station_guid`.

## 002b - Cycle 2 part 2: the probe plugin closes seven spikes (2026-07-26)

Cycle 2 is still NOT done and no bridge code exists yet. This is the spike-closure
entry. Entry 002 proper is appended when the plugin is live-proved.

**The artifact is a probe, not the bridge.** `_scratch\rmprobe\`, a minimal
enumerate-and-log BepInEx plugin, built and deployed into both hosts before any
bridge code, because S1(b), S1(c), S1(d), S2, S5 and S6 are not answerable from
static metadata. Scratch and deliberately not committed, the same rule as
`_scratch\typedump\`: regenerable, and it must not become a second plugin to
maintain per patch. It compiles the SAME generated `RmPorts.g.cs` the real plugin
will, so the no-port-literal rule holds even in scratch, and it reads ECS only
from `Update()` while its listener thread serves a constant, so it exercises both
halves of D7 without violating D7 or risk R4.

**R17 CLOSED, and the obvious diff was the wrong one.** The client was launched
and generated its own `BepInEx\interop\`: 172 files, 169 `.dll`, matching the
server exactly - which also explains the previously recorded "169 assemblies" as
the dll count, so no correction was owed. Assembly name sets are identical. All
169 SHA256 hashes differ, and that is NOT a divergence signal: Il2CppInterop
codegen is non-deterministic, so a hash diff reports total divergence between any
two generations and would have manufactured a blocking finding. The type-level
diff is the one that decides the `.csproj`: 97 client-only and 591 server-only
types, almost all of it per-build codegen noise
(`__JobReflectionRegistrationOutput__<hash>`, `__UnmanagedPostProcessorOutput__<hash>`,
closure and iterator types), with the real divergence confined to 499 server-only
netcode serializers, about 17 server-only send-priority types in `ProjectM`, and
client-only Rukhanka animation types. None is needed. `ProjectM.Shared`,
`Stunlock.Core`, `Unity.Entities` and `ProjectM.Gameplay.Systems` have zero real
divergence and every design-needed type was checked present in both sets by name.

**S4 fully closed and R2 retired.** The build succeeds with the entire reference
set added, not just the bare target framework. `Paths.BepInExVersion` returns a
`SemanticVersioning.Version`, which forces one non-obvious reference.

**S1(a)** is `World.All`. **S1(d)** is `BepInEx.Paths.ProcessName`, measured as
`VRising` and `VRisingServer`. **S1(c)**: the server's target world is named
`Server` with 710 systems, and selection must be BY NAME - `Default World` is also
a Simulation world, sits at index 0, and throws `ArgumentException` when asked for
the prefab map, while `LoadingWorld0` throws `InvalidOperationException`. Those
two exceptions are the natural `world_not_ready` path and a genuine negative
control that a stub cannot produce. **S2**: an Il2Cpp-injected `MonoBehaviour`
`Update` reaches main thread 1 in both hosts, so no Harmony patch is needed and
D7 is implementable as written. **S5 and R11**: `HttpListener` binds and serves in
both hosts concurrently, which is the ADR-005 payoff observed rather than argued,
and after `taskkill /F` the port holds no LISTEN while
`bridge_probe.py --expect-unreachable` passes. **S6 partial**: the prefab lookup
map reports `Count` 1189 in under a millisecond, so reading it needs no chunking;
the dump itself is still unmeasured. **S3 advanced**: `items` and `recipes` are
mapped, and the headline is that `EquippableData` carries NO stats, only a
`BuffGuid`, so `items.stats` is a two-hop read through the buff prefab's
`DynamicBuffer<ModifyUnitStatBuff_DOTS>`.

**One real defect, found by the probe rather than by a test.** The suite carried a
test whose comment read "nothing is listening on the bridge ports during the
suite" and which depended on it being true. The probe bound the client port, the
connection succeeded, and the test failed with no defect anywhere in the code
under test - the mirror image of cycle 1's gate that could not fail. Fixed by
pointing `RM_GAME_HOST` at `192.0.2.1`, RFC 5737 TEST-NET-1, so unreachability is
a property of the test rather than of the machine.

**Left open, honestly.** S1(b) has only the client MAIN MENU sample: two worlds,
no prefab-carrying world, so a client-side dump is UNPROVEN. The remainder of S3
is gated behind the same in-game sample. The operator chose to wrap rather than
load a character.

Verification, all observed in one run after the last edit: `python -m pytest` 245
passed, `python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0. The
245 was observed with the probe still bound to the client port and answering
`curl`, which is the exact condition that broke the old test.

Commits: `9a036d2`, `46ec231`, `003d027`, plus the docs sync.

## 002a - Cycle 2 part 1: ADR-005, the Python half, and the spike environment (2026-07-26)

Cycle 2 is NOT done. This is a partial entry for the part that shipped, written
so the next session does not re-derive it. Entry 002 proper is appended when the
plugin is live-proved.

**ADR-005 minted a fifth port and struck the arbitration.** The approved spec
answered the port-8777 collision between the two ADR-004 hosts with bind-time
first-come plus a procedural "start the dedicated server first". That was
procedure, not enforcement. Ruled instead: the client binds 8777, the dedicated
server binds 8780, and the choice is a pure function of the detected host via
`core.ports.bridge_port_for_host`, which is total over the two hosts and raises
otherwise. Struck as a consequence: the stand-down path, install step 6b,
acceptance criterion 5b and risk R15. Both hosts can now serve at once, which
first-come could not do and which cycle 3 and cycle 4 actually need. The client
kept 8777 because solo client is the dominant topology and the frozen
`tools/rm_facts.py` already probes that number. `core/ports.py` is frozen and
ADR-003 was Accepted; both edits were operator-approved before the change.

**Shipped:** `tools/gen_bridge_ports.py`, `core/bridge_client.py`,
`core/table_deep.py`, `tools/install_bepinex.py`, `tools/rmdata_ingest.py`,
`tools/bridge_probe.py`, `bridge/Directory.Build.props`, the generated
`RmPorts.g.cs`, ADR-005, and `docs/BRIDGE_SPIKES.md`.

**Verified, all observed in one run after the last edit rather than carried
forward from a subagent's report:** `python -m pytest` reports **241 passed**
(was 106); `python -m ruff check .` is clean; `python tools/ascii_guard.py`
exits 0.

**Verified live against the real install, not against a fixture:**

- Both v3 negative controls REFUSE with `v3-path-component` and write nothing.
- The client profile pointed at `VRising_Server` refuses with
  `client-target-is-server-dir`.
- HONEST CORRECTION to acceptance criterion 2: the fourth negative control,
  `--target server` pointed at the root, is UNREACHABLE rather than refused. The
  installer takes `--root` and derives the server target from it, so the
  mismatch cannot be expressed. Prevented by construction beats refused, but it
  is not the control the spec asked for and is not recorded as one.
- BepInEx 1.733.2 installed into both hosts, 233 files each, Thunderstore
  metadata correctly dropped, `v3\` untouched.
- The dedicated server launched once and generated 169 Il2CppInterop assemblies.

**Spikes closed by measurement:** S4 (a net6.0 library builds under SDK 10.0.301
with no targeting pack and no `global.json` - neither fallback is needed, R2
retired for the bare TFM) and S3a (`ProjectM.PrefabCollectionSystem` is REAL in
`ProjectM.Shared.dll` - the unverified roadmap label is CONFIRMED, not
corrected). S3 is partially resolved: the component types are located and named,
the field mapping is not done. S1, S2, S5 and S6 remain OPEN.

**Not done, and not claimed:** no plugin C# is written, nothing is built against
the interop set, and no leg of the D5 wiredness proof has run. Leg 4 structurally
requires the operator to load a character and move it.

**Process incident, recorded rather than buried.** `251803b` was committed while
a build subagent was still live, and it captured that agent's file mid-mutation
test: the v3 guard in `tools/bridge_probe.py` is committed as `if False:` in
that one commit. Verified directly with `git show 251803b:tools/bridge_probe.py`
rather than taken on the agent's report. The guard is CORRECT at `d614a09` and
at HEAD, the working tree is clean, and a fresh full run after the fact is 245
passed / ruff clean / ascii_guard 0. No history rewrite: the defect existed in
one intermediate commit and is fixed in the next, which is what a branch is for.

The lesson is the standing one and it was paid for again here: do not commit
while agents are live, and check `git show --stat` after every commit. A green
suite taken moments before a `git add -A` does not describe what `git add -A`
actually staged.

Worth carrying separately: that agent's own mutation testing found a real hole
in its tests. A mutation making the loader-log banner matcher accept any line
containing `RedMoon.Bridge` SURVIVED 25 tests, because the negative fixture
carried no banner token at all - cycle 1's exact failure mode, a gate that
cannot fail. Four parametrized tests were added and the mutation then failed.
This is the second time in two cycles that the bug was "the check never checked".

Consequence for the not-yet-written plugin: `Plugin.cs` MUST emit a banner
carrying all three tokens, version, host and port, in the shape
`RedMoon.Bridge v<semver> host=<client|server> port=<n>`. The matcher is
token-based and order-independent by design, but it requires all three.

Commits: `9fbce0c` (ADR-005), `251803b` (the Python half), branch
`cycle-2-bridge`.
Spec: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`
Spike findings: `docs/BRIDGE_SPIKES.md`

## 001 - Cycle 1: harness plus data floor (2026-07-26)

Shipped the Red Moon process harness and the offline data floor. ASCII guard,
port registry, doctrine documents, living docs, ADR-001 through ADR-003, the
data extractor, typed table schemas, four enforcement hooks, the verifier
subagent, three slash commands, the memory namespace seed, and RM-DataRefresh
registration.

Closed out by the whole-branch review fix wave: the precommit gate's hook
matcher was a permission-rule specifier, which never matches a tool name, so the
gate had never fired; the extractor now creates the `tables/` seam cycle 2 dumps
into; the port-literal rule is enforced for Red Moon's own ports across `.py`,
`.cs`, `.json` and `.ps1`; and the memory namespace has a committed seed under
`docs/memory_seed/` with a drift guard.

Verified: `python -m pytest` reports 106 passed; `python -m ruff check .` is
clean; `python tools/ascii_guard.py` exits 0; `python tools/rmdata_extract.py`
is idempotent and writes `data/rmdata/1.1.13.0-r99712/`; the commit gate blocks
a staged em-dash.

Merge: `2a493ea` (branch `cycle-1-harness`, 34 commits, merged into `master`)
Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`
Plan: `docs/superpowers/plans/2026-07-26-redmoon-cycle1-harness.md`
Execution record: `docs/history_notes.md`

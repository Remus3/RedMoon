# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-08-01 - Three projects, one machine: a shared governor, a gate that read the wrong tree, and a triage that adopted nothing

Branch `master`. Ledger 003g. Commits `b1b6b2d`, `6cfc614`, `a3fa2f6`,
`91b9ed2`, `7d735da`, `370c019`, plus the docs commit carrying this entry.
**NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 STILL has not started - five
sessions now. Every item this session arrived from a cross-project handoff.

State at close, one run: `python -m pytest` **348 passed in 20.15s, exit 0**
(335 before, plus 13 new), `python tools/ascii_guard.py` exit 0, `ruff` clean.

**THE SESSION WAS DRIVEN BY AN INBOX, NOT THE ROADMAP.** `moon_sync_inbox/` is a
sibling-to-sibling channel a sibling project opened in this repo. Three notes
arrived and three went out. If that directory has new files at session start,
read it before planning anything.

**THE .GITIGNORE ASK WAS THE LESSER HALF, AND SAYING YES TO IT ALONE WOULD HAVE
LEFT THE BUG.** RC asked for `moon_sync_inbox/` in `.gitignore`. The foreign-port
guard walks the WORKING TREE via `rglob`, not tracked files, so gitignoring
changes nothing about what it scans. RC's block is 8888-8895 and three of those
sit in `FORBIDDEN`, so the next note delivered as `.json` or `.ps1` instead of
`.md` fails the suite on content Red Moon does not own. Fixed in
`SKIPPED_DIR_PARTS`. **When a sibling proposes a fix, check whether it addresses
the mechanism or the symptom.**

**THE GATE READ THE WRONG TREE, AND THIS IS THE FINDING WITH THE LONGEST TAIL.**
`tools/precommit_gate.py` (frozen, changed with operator approval) called
`check_staged()` with NO ARGUMENT, so it inspected the hardcoded main tree
regardless of where the command ran. A commit inside a WORKTREE was gated against
MAIN's staging area while the worktree's own was never read. Every headless
design on offer is worktree-based. The git hook still fired correctly, so the
floor held - but the Claude-side gate was decorative in exactly the runs it
exists to guard. Second defect in the same file: it tested `"git commit" in
command`, so any command merely QUOTING the phrase was gated - it denied this
session's own probe that way. Both proven END TO END against a live worktree,
because presence of a gate is not proof it fires.

**A FIX CAN REINTRODUCE THE BUG IT FIXES.** The first tokenizer used
`shlex.split(posix=True)`, which eats backslashes, so `git -C C:\RedMoon`
resolved to a nonexistent `C:RedMoon` and fell back to the main tree - defect 2
restored through the fix for defect 1. A failing test caught it; review did not.

**PHASE 0 IS INCONCLUSIVE, NOT PASSED, AND THAT IS THE HONEST RESULT.**
`claude -p --permission-mode bypassPermissions` exits 1 here: **headless is NOT
AUTHENTICATED on this box, and `C:\RedMoon` is NOT A TRUSTED WORKSPACE**, which
discards all 13 `permissions.allow` entries. RC's measurement that PreToolUse
hooks die headless is RC's, on RC's machine, and is UNREPRODUCED here - do not
cite it as confirmed. The trust finding is sharper than the auth one: a headless
worker would run under a DIFFERENT permission set than the interactive session
that authored its prompt. Neither has a phase in RC's plan.

**JOINED THE MACHINE-WIDE GOVERNOR, AND CLAUDE.MD WAS FALSE UNTIL CORRECTED.**
`ops/loop/slots.py` is vendored BYTE-IDENTICAL, sha256 `95077a62`, pinned by
test. Neutrality was VERIFIED, not trusted. `CLAUDE.md` opened by claiming Red
Moon "shares no code, data, keys or scheduled-task namespace" - false the moment
this landed, and corrected in the same commit. **RM now shares exactly one file
of code and one directory of data; still no keys, ports or task namespace.**
DO NOT EDIT `slots.py`: the digest is the contract and re-syncing is a
three-repo act. Its own docstring still says TWO repos; correcting that needs a
coordinated re-pin and RM will not move first.

**TWO OF RM'S OWN CLAIMS WERE WRONG AND SIBLINGS CAUGHT BOTH.** RM told RC that
8781 and 8782 were "the free ones" - true about the INTERIOR of the used region,
blind to the block FLOOR 8770-8776 never being allocated at all. 8777 is merely
the lowest USED port. RM took 8770. Separately RM proposed bucket N=3, reasoning
that 2 blocks one of three participants permanently; LegionWallpaper replied the
same day with a measured blocker RM could not see - **LW is the only GPU-heavy
participant and its GPU mutex was DECLARED BUT ACQUIRED BY NOTHING**, so a third
lane permitted unserialized CUDA, whose failure mode is a half-written image
rather than a clean error. Withdrawn same day, held at 2.

**THE 119-ITEM MCP TRIAGE ADOPTED NOTHING, AND THE REASON GENERALIZES.**
Re-scored for RM then adversarially challenged: **119/119 reviewed, 37 overturns,
every one downward, zero entries above 5.** The scoring pass correctly voided
RC's closes that cited RC-only assets, then made a worse error - **treating "RC's
reason was wrong" as evidence the tool is right.** A void closure returns a
verdict to NEUTRAL, not to good. Four falsifications did most of the killing:
`.claude/` is five files, `ops/runtime/` and `logs/` do not exist, `core` plus
`tools` is 2,730 lines, and `precommit_gate.py` already fires PreToolUse. The
structural finding is bigger than any entry: **all 119 are developer tooling
while cycle 3 is blocked on measuring a game binary.** Do not re-run this triage
on a new link dump before cycle 5.

**AN ADVERSARIAL PASS IS ONLY AS GOOD AS ITS INPUT PLUMBING.** The first fan-out
truncated its challenge input at 12,000 chars, so 33 of 119 entries were scored
but never challenged - and every surviving 6+ entry was one the challenge never
saw. The survivors were artifacts of the bug, not merit. A gap-fill run knocked
all of them down. **Check coverage before reporting a fan-out's conclusions.**

**TWO GUARDS FIRED CORRECTLY MID-SESSION**, which is the system working rather
than a problem: the memory-seed mirror refused two unseeded memory entries, and
`test_adr_003_agrees_with_the_port_registry` refused an undocumented port.

**BACKLOG GAINED TWO REAL BLOODFORGE GAPS.** Cycle 3's six acceptance criteria
are ALL about sourcing inputs, so **all six can pass with a confidently wrong
TTK** - Red Moon has no ground-truth anchor for any computed number. And no
default subject vector is declared, so the first TTK silently ranks every build
for anyone who does not override. Neither blocks phase 2; the first must be
settled before the combat-math spec opens.

## 2026-07-26 - The co-author trailer: a policy nothing enforced, and a test that lied

Branch `master`. Ledger 003e. Commits `0cb03a1` (hook plus tests), `bbc2a81`
(CLAUDE.md), `f47acd3` (citation remap) and `d49bc3f` (this entry), on top of a
29-commit history rewrite that was FORCE-PUSHED to
`origin/master`. **NO ROADMAP ITEM CLOSED.** The operator gate on the cycle 3
phase 1 component inventory is STILL OPEN - four sessions now. That gate is the
real next action.

State at close, one run: `python -m pytest` **334 passed in 18.77s, exit 0**
(327 before, plus 7 new), `python tools/ascii_guard.py` exit 0.

**THE ASK WAS A VERIFICATION, AND IT CAME BACK NEGATIVE.** "Be sure the active
commit-msg hook enforces the policy and strips the trailer - the tracked one
doesn't." There was no commit-msg hook at all, tracked or active. `core.hooksPath`
selects `hooks/`, which held only the pre-commit pair; `.git/hooks` holds only
samples; the string `Co-Authored-By` appeared NOWHERE in the repo. The premise
that a weaker tracked hook existed was itself wrong, and 16 commits carried the
trailer including both of that day's earlier doc commits.

**WHY AN UNWRITTEN POLICY LOSES.** The agent harness instructs the model to
append the trailer to every commit message. A policy that lives only in the
operator's head is a coin flip against a default that fires every single time.
`CLAUDE.md` now carries it as a hard rule AND says the hook is a backstop, not a
licence to emit the line - the hook cannot fire on `--no-verify` or on a rebase
replaying old messages.

**STRIP, DO NOT BLOCK.** Deliberately unlike the ASCII gate. A check that did
not run did not pass, but a strip that did not run leaves one line the operator
can still delete by hand; refusing the commit would trade a cosmetic defect for
a blocked repo. Same reasoning makes a missing interpreter exit 0 in
`hooks/commit-msg` and 1 in `hooks/pre-commit`.

**THE TEST THAT WOULD HAVE LIED, AND THIS IS THE PART WORTH REMEMBERING.**
`test_every_sha_the_ledger_cites_resolves` probes with `git cat-file -e`. Old
objects survive a rewrite in the object database while `refs/original` and a
backup branch still reference them, so the test went GREEN on all 36 cited SHAs
at the exact moment a third of them named commits unreachable from master. It
would have failed days later, after gc, with no connection to its cause. The
remap was proven instead by grepping every tracked doc for every pre-rewrite SHA
prefix - empty. 26 citations across five files, four of which that test does not
even look at. **A resolving SHA is not a reachable SHA.**

**BLAST RADIUS WAS MEASURED BEFORE ASKING, NOT AFTER.** Stripping 16 commits
rewrites 29, because every descendant takes a new SHA, and all 29 were already
on GitHub. The approval was given against that number, not against "14 commits".

**THE OTHER PROJECT'S TWO TRAPS DO NOT APPLY HERE - RE-PROBED, NOT REASONED.**
Trap 1, hooks in `.git/hooks` while `core.hooksPath` points elsewhere: RM has no
non-sample files there. Trap 2, `precommit_gate.py` invoked with no args
self-gating to a silent no-op: the one-liner DOES reproduce
(`python tools/precommit_gate.py < /dev/null` exits 0) but RM never uses that
path - `hooks/precommit_hook.py` imports `check_staged` directly. Settled by
staging an em-dash and running a real commit: BLOCKED, `U+2014`, HEAD unmoved.

**BACKUP, NOW GONE.** Branch `backup-pre-trailer-rewrite` and
`refs/original/refs/heads/master` were deleted and gc'd with `--prune=now` after
the rewritten history was confirmed good. The pre-rewrite objects no longer
resolve, which is what makes the ledger SHA anchor a real check again - it
passes against a purged object database, so the 26-citation remap is proven
complete rather than merely resolving off lingering objects.

**ORPHANED-HOOK CLASS, CHECKED AND CLEAR - BUT RM IS PRE-ARMED FOR IT.**
`.git/hooks` holds only `.sample` files, there is no `.gitattributes`, and
`git lfs ls-files` is empty, so nothing was silently disabled when
`core.hooksPath` was set. LATENT RISK: `filter.lfs.required=true` IS configured.
`git lfs install` writes its hooks to `.git/hooks`, which `core.hooksPath`
makes git ignore. So the first LFS-tracked file added to this repo gets an inert
`pre-push`, pushes look clean, and the LFS content never reaches the remote.
If LFS is ever adopted here, port the LFS hooks into `hooks/` in the same
commit. GUARDED as of this session by
`test_no_orphaned_hooks_left_behind_in_git_hooks`. It asserts a condition that
was ALREADY TRUE, so it could not fail first and could have shipped vacuously
green - it was proven by injecting a fake `.git/hooks/pre-push`, watching it go
red naming that file, and removing it. A guard test that has never been seen red
is not a guard.

**FRESH-CLONE BOOTSTRAP, RAISED FROM THE OTHER PROJECT AND VERIFIED HERE BY
ACTUALLY CLONING.** `core.hooksPath` is LOCAL config and is NOT cloned, so a
tracked hooks directory is inert on arrival no matter how correct it is. Probed
rather than reasoned: `git clone C:/RedMoon <scratch>` came back with
`core.hooksPath` UNSET and zero active hooks. RM already covers it in two
places - `docs/OPERATIONS.md` has "Wire the commit gate, once per clone" marked
mandatory, and the suite fails there on
`test_core_hooks_path_selects_the_committed_hooks_dir` plus
`test_installer_reports_the_wiring_as_installed`, the latter printing the exact
remediation command. The new orphaned-hook test correctly SKIPPED in that
clone, so its skip branch is exercised for real rather than assumed.
THE RESIDUAL GAP CANNOT BE CLOSED BY ANYONE: between clone and the first
verification run, nothing has told the operator yet. Git never clones hooks by
design, because that would execute arbitrary code on clone. The ceiling is
"loud on first verification", not "safe on arrival". A local clone is cheap -
the repo is 685K - so this probe is worth repeating whenever the wiring changes.

# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-07-26 - An external /done doc, measured, and the two checks it was right about

Branch `master`. Ledger 003d. Commit `d6bfdd9` (tests) plus the docs commit that
carries this entry. **NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 still has not
started and the operator gate on the phase 1 component inventory is STILL OPEN -
three sessions running now. That gate is the real next action.

State at close, one run: `python -m pytest` **327 passed in 18.47s, exit 0**
(324 before, plus 3 new), `python tools/ascii_guard.py` exit 0.

**The input and the ask.** `C:\Users\Administrator\Desktop\DONE_RITUAL_OPTIMIZED.md`,
another portable process doc from the other project on this box, this one an optimized
`/done` ritual. Ask was "process it". It proposes two things: a speed rewrite
that moves a slow suite off-machine to CI, and a standalone `tools/drift_guard.py`
carrying eight cheap invariant checks.

**MOST OF IT DOES NOT APPLY, AND MEASURING IS THE ONLY WAY THAT WAS KNOWABLE.**
Its own headline lesson is to measure the shape before choosing a lever. Applied
to itself: its entire premise is a 27-minute local suite worth overlapping with a
17-minute CI run. This suite is **18.47s**, there is no `.github/` at all, and no
CI. Overlapping ~15 minutes of doc writing with a dispatched CI run would have
been pure overhead. Sections 1 and 2 are inapplicable in full.

**SIX OF THE EIGHT DRIFT CHECKS ALREADY EXIST HERE, AS TESTS.** Doc budget ->
`test_claude_md_stays_under_the_size_budget`. Mirror parity ->
`test_live_memory_matches_the_committed_seed`. Memory index ->
`test_memory_namespace_is_seeded`, which is STRICTER than the proposal, asserting
an exact expected set rather than parsing links. Orphan docs ->
`test_every_adr_file_is_listed_in_the_index`. Untracked authored files -> `.claude/`
is fully tracked, verified. Counted claims -> no such construct in this repo.
Building the script would have duplicated all six into a second place that runs
only at wrap, where the tests run on every `pytest`. It was not built.

**THE TWO REAL GAPS, SHIPPED AS `tests/test_drift_anchors.py`.**

1. **Build-pin anchor.** The pin has about 97 tracked sites and nothing asserted
   they agree with the one CLAUDE.md declares. The canonical value is READ from
   CLAUDE.md, not hardcoded. The `v3` stale-trap pin is allowlisted BY VALUE so
   it keeps its own identity. Historical records are excluded. Fixture pins are
   matched BY SHAPE - majors 8 and 9, which V Rising cannot reach - rather than
   by excluding `tests/`, so a fixture asserting against the CURRENT build still
   has to move when the pin moves. The first draft DID exclude nothing and caught
   ten real fixture pins, which is how the shape rule was arrived at.
2. **Ledger SHA anchor.** Nothing verified the hashes `docs/LEDGER.md` cites by
   its own stated format. Entry 003c needed exactly this backfill last session.

**Both were proven to FAIL before being accepted.** A guard that cannot fail
proves nothing. A stale pin `1.1.12.0-r99000` appended to `docs/API.md` tripped
the first with file, line and value; a fabricated eight-hex hash appended to the
ledger tripped the second. Tree restored, `git status --porcelain` clean after.

**Its section 5 needed reframing, and the scrub came back clean.** The doc says
to run a secret scrub BEFORE flipping a repo public. This repo is ALREADY public
(`Remus3/RedMoon`), so that ordering is moot - but the scrub was run anyway and
passes: `API-Key-Claude.txt` was never committed, no key-shaped blob exists
anywhere in history, and no email appears in any tracked file. The only exposure
is the git author email in commit metadata, inherent to a public repo.

Its section 4 lists three defects to fix in the ritual text. All three are N/A
here: this `done.md` has no commit trailer, no retired section, and sequential
numbering. Worth recording so the next reader does not re-check them.

**SCHEDULED TASKS: ASKED MID-SESSION, ANSWERED, NOTHING TO FIX.** The operator
asked to find `schtasks` entries that make a window and silence them. Enumerated
machine-wide: **no scheduled task on this box can show a window.** Only five run
a console binary at all - one activation shim plus four belonging to the other
project on this box - and every one runs under **S4U or ServiceAccount** logon,
which has no desktop and cannot draw a window whatever the binary does. Every
**Interactive**-logon task runs either a GUI binary or `pythonw.exe`, the
windowless Python host. Red Moon's own `RM-DataRefresh` is Interactive but runs
`pythonw.exe` on `tools/rmdata_extract.py` - correct by construction.
**The `Hidden` property is a red herring**: it controls visibility in the Task
Scheduler LIST, not whether a console window appears, so several tasks reading
`Hidden: False` are still windowless. This CORROBORATES the existing memory entry
`reference_flashing_consoles_are_mcp_launchers` - the flashing consoles are not
scheduled tasks, and this session ruled them out by direct enumeration rather
than by trusting the note.

# Red Moon History Notes


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

## 2026-07-26 - The same PS7 doc, re-validated after the operator updated it

Branch `master`. **NO ROADMAP ITEM CLOSED and no production code changed.** The
only repo change is docs: these notes, the archive move, the next-session prompt
and one memory seed. Cycle 3 phase 2 still has not started.

State at close, observed in one run: `python -m pytest` **324 passed in 18.40s,
exit 0**, `python tools/ascii_guard.py` exit 0. The summary line DID print, so
the dot-counting workaround the section below describes was not needed this time
- the line appears on some runs and not others, which is worth knowing before
anyone "fixes" the pytest config.

**The input and the ask.** The operator updated
`C:\Users\Administrator\Desktop\POWERSHELL_7_MIGRATION.md` - the same
another-project doc audited in the session below - and asked for it to be
re-ingested and validated again. It is now 8 sections; the update added a
detailed section 5 point 1 listing that project's live VBS and BAT shims that
name `powershell.exe` explicitly, and a section 8 migration log.

**Eleven claims re-measured and confirmed.** PS7 7.6.4 Core at
`C:\Program Files\PowerShell\7\pwsh.exe`, machine PATH carries
`C:\Program Files\PowerShell\7\`, the MSIX per-user alias
`%LOCALAPPDATA%\Microsoft\WindowsApps\pwsh.exe` does NOT exist, 5.1 is intact at
exactly `5.1.19041.6456` as its section 6 predicts, and 22 `RC-*` scheduled
tasks exist. Its section 5 parse measurement also reproduces here, which matters
because it is the doc's only claim that touches this repo's hard rules: a no-BOM
UTF-8 `.ps1` with U+2014 inside a double-quoted string, through
`[System.Management.Automation.Language.Parser]::ParseFile`, gives **2 errors
under 5.1 and 0 under 7.6.4**.

**TWO DEFECTS, AND BOTH SURVIVED THE UPDATE.**

1. **Section 4c is still wrong**, and it is the doc's most actionable claim.
   Measured again through the tool this session: `$PSVersionTable` is **7.6.4 /
   Core** and the process `MainModule.FileName` is
   **`C:\Program Files\PowerShell\7\pwsh.exe`**. Its PREMISE is correct and was
   verified - the global `C:\Users\Administrator\.claude\settings.json:6` does
   hold `CLAUDE_CODE_USE_POWERSHELL_TOOL: "1"` and there is indeed no key that
   selects the binary - but the conclusion drawn from that premise does not
   follow. An agent here gets pwsh, so `&&`, `||`, ternary, `??` and `?.` work
   directly and the `& pwsh -NoProfile -File` escape hatch is real but
   unnecessary. That the error persisted across a revision is itself the lesson:
   **a doc being updated is not evidence that any particular claim in it was
   re-checked.**
2. **The header hostname is wrong.** It says `DESKTOP-JKZECV9`; this machine is
   **`DESKTOP-LCA3EBI`**. Every other fact in the doc matches this box, so it is
   a mis-recorded name and not a different machine. Its `legion-rc` Tailscale
   label could not be checked at all - Tailscale is not installed and not on
   PATH here.

**Red Moon impact is still exactly zero, and the update gave a NEW way to
check.** Section 5 point 1 now says to grep your own project for
`powershell.exe` in `*.vbs`, `*.bat` and `*.cmd`, because a shim is easy to miss
when it is neither a scheduled task nor a `.ps1`. Run against this repo that
returns **no matches**, so Red Moon carries none of the live 5.1 `ParseFile`
exposure that list documents. Combined with last session's `*.py` and `*.json`
grep and `RM-DataRefresh` executing `pythonw.exe`, the migration surface here is
empty by measurement across every file type the doc names.

**The ASCII rule is unchanged.** 5.1 is installed and reachable, it is an
operator style rule independent of any parser, and `tools/ascii_guard.py` plus
the wired precommit gate enforce it mechanically. PS7 removes one failure mode,
not the rule.

**That doc was not edited.** It is another project's territory and correcting
its 4c and its header is the operator's call. The measurements above are the
evidence if it is corrected.

**No ledger entry, for the reason the section below states at length** -
`docs/LEDGER.md` scopes itself to completed roadmap items with an item number
and a commit hash, and this session closed none. `reference_powershell_editions_on_legion`
was extended with the hostname correction, the 2/0 parse numbers and the fact
that 4c survived a revision, and `docs/memory_seed/` was re-synced in the same
commit by copying the live file AFTER the memory system rewrote its `modified:`
timestamp, which is the ordering last session learned the hard way.

## 2026-07-26 - A PowerShell 7 migration doc, audited against this repo

Branch `master`. **NO ROADMAP ITEM CLOSED, no production code changed, and no
ledger entry was written** - see the note at the end of this section for why
that is deliberate rather than an omission. Cycle 3 phase 2 has not started.

State at close, observed in one run: `python -m pytest` exit 0 with **324 dots
and zero of `F/E/s/x`**, `python tools/ascii_guard.py` exit 0. The working tree
was clean at session start and stayed clean apart from these notes. The pytest
summary line still does not print in this repo (the cause is the pytest config,
not the invocation) so the count is from the progress block, as last session
also recorded.

**The input.** The operator pasted
`C:\Users\Administrator\Desktop\POWERSHELL_7_MIGRATION.md`, written by ANOTHER
PROJECT on this same machine. PowerShell 7.6.4 was installed there via the MSI
(deliberately not the MSIX, whose real path carries the version and whose
launcher is a per-user app-execution alias - both disqualifying for scheduled
tasks). 5.1 is untouched and still lives at `powershell.exe`; PS7 is
`C:\Program Files\PowerShell\7\pwsh.exe`. It is a side-by-side install and
nothing switched automatically.

**THE FINDING, and it is the whole session.** That doc's section 4c asserts that
Claude Code's PowerShell tool invokes `powershell.exe`, so an agent on this box
must keep writing 5.1-compatible PowerShell. **Measured in this session, it does
not.** `$PSVersionTable` through the tool returns **7.6.4, edition Core**, and
`(Get-Process -Id $PID).Path` returns
**`C:\Program Files\PowerShell\7\pwsh.exe`**. So `&&`, `||`, ternary, `??`,
`?.` and `ConvertFrom-Json -AsHashtable` all work directly in agent PowerShell
here, with no `& pwsh -File` escape hatch needed. The doc's stated workaround is
real but unnecessary. It was checked 2026-07-26 by that project and is wrong as
of the same date here, so it was either inferred rather than probed, or the tool
changed under it. Either way: **probe `$PSVersionTable` before planning around
which PowerShell an agent gets.**

**Red Moon has nothing to migrate. Section 4 of that doc is a no-op here, and
this was verified rather than assumed:**

- **Scheduled tasks (4a).** The only `RM-*` task is `RM-DataRefresh` and its
  `Execute` is `pythonw.exe`, not `powershell.exe`. Zero candidates.
- **Call sites (4b).** A case-insensitive grep for `powershell(\.exe)?` across
  `*.py` and `*.json` in the repo returns four hits and NONE is an invocation:
  `tests/test_hooks.py:131` asserts hook coverage of the tool NAME,
  `.claude/settings.json:24` and `:33` are a permission entry and a hook matcher
  string, and `tools/ascii_guard.py:4` is the docstring explaining the 5.1
  parser bug. Red Moon shells out to Python, never to PowerShell.
- **CI (4d).** Nothing to check.

**The ASCII rule stands, unchanged, and the doc agrees.** Its section 5 measured
that a no-BOM UTF-8 `.ps1` carrying an em-dash parses with 0 errors under 7.6.4,
and then correctly declined to relax the rule. The same holds here for three
reasons: `powershell.exe` 5.1 is still installed and still reachable, it is an
operator style rule independent of any parser, and it is mechanically enforced
by `tools/ascii_guard.py` plus the now-wired precommit gate. **PS7 removes one
FAILURE MODE, not the rule.** One nuance worth carrying: `CLAUDE.md`'s stated
*why* for the rule is now HISTORICAL rather than live, because the shell an
agent actually gets in this session cannot exhibit that parse failure. The
wording was left alone deliberately - it is accurate about 5.1, and 5.1 has not
gone anywhere.

**Nothing was changed in that other project's doc.** It is another project's
territory and correcting its section 4c is the operator's call, not something to
do unasked. If it is corrected, the measured output above is the evidence.

**Why there is no ledger entry.** `docs/LEDGER.md` states its own contract in
its header: one entry per COMPLETED ROADMAP ITEM, with an item number and a
commit hash. This session closed no roadmap item, so minting an item number for
it would make the ledger's numbering describe something the roadmap does not
contain. The `/done` ritual's steps 4 and 5 were therefore skipped on purpose
and the finding lives here instead. If a future session disagrees, the fix is to
change the ledger's stated format first, not to backfill a number.

**Two guards fired on this session's own notes, and both were right.**
`tests/test_root_docs.py::test_no_riot_commander_references_in_root_docs` failed
because the first draft of THIS section named the other project three times in a
root doc. ADR-001 rules that non-root docs may name it plainly while root docs
stay anonymous, so the notes were reworded and `docs/memory_seed/` was left
naming it. And `test_live_memory_matches_the_committed_seed` failed because the
memory system REWRITES the `modified:` timestamp in the live file after a write,
so a hand-authored timestamp in the seed can never match - copy the live value
into the seed after writing, not before.

The PS7 fact was also written to the live memory namespace as
`reference_powershell_editions_on_legion`, and seeded into `docs/memory_seed/`
in the same commit - the suite asserts that seeding, and last session's failure
was exactly a memory entry written live and never seeded.

## 2026-07-26 - The hook that was never wired, and the cycle 3 component inventory

Branch `master`. Ledger 003b and 003c. Commits `64eb9e8` (hooks) and `48a9215`
(phase 1). **Phase 1 is COMPLETE and STOPPED AT THE OPERATOR GATE.** No schema,
no table, no ingest gate, no combat math - the spec bars all four until the
inventory is reviewed.

State at close, observed in one run after the last edit: `python -m pytest`
**324 passed in 19.10s** (the summary line DID print this time, unlike last
session), `python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0,
`dotnet build -c Release -t:Rebuild` on the bridge csproj exit 0 with 0 warnings.

### Item 0: the gate that was a script nothing called

`tools/precommit_gate.py` has held the ASCII and ruff checks since cycle 1 and
had NO CALLER. `.git/hooks` held only `.sample` files, `core.hooksPath` was
unset. That is the whole explanation for last session's BOM in `56be457`.

The wiring lives entirely outside the two frozen files. `hooks/pre-commit` (sh,
mode 100755) plus `hooks/precommit_hook.py`, committed and selected by
`core.hooksPath`, with `ops/install_git_hooks.py --check` asserted by the suite.

**Why a wrapper rather than pointing git at the gate.** `precommit_gate.main()`
speaks Claude Code's PreToolUse protocol: it reads JSON on stdin and ALWAYS
returns 0, emitting a refusal as a JSON permission decision. git reads an exit
code and nothing else, so git could never have learned a refusal from it no
matter how it was invoked. The wrapper also does NOT swallow exceptions the way
the PreToolUse gate must - a crashing PreToolUse hook must not block unrelated
tooling, a crashing commit gate must block the commit.

**Proven against git, which is the only proof that counts.** Seven failing tests
first. Then a real BOM file staged in this repo and `git commit` REFUSED:
`COMMIT BLOCKED by hooks/pre-commit`, `U+FEFF` at 1:1, exit 1, HEAD unchanged.
Both later commits then passed through the live gate, so it blocks the bad and
admits the good.

### Phase 1: the inventory, and the value reader that had to be thrown away twice

`GET /dump/components` enumerates an entity's ACTUAL component types and prints
all of them with declared fields, nested types expanded and enum members named.
Subjects, at the spec's minimum samples: `CHAR_*_VBlood` at levels 16, 57 and 91
(150 components each), four ability groups across schools INCLUDING a weapon
group, two weapon families, and a LIVE INSTANCED boss.

**THE THING TO CARRY FORWARD. It reads names, not values, and that is measured.**
Two generic value readers were built and both failed:

1. Managed reflection via `EntityManagerDebug.GetComponentBoxed` - correct field
   names, GARBAGE values. Every `Int32` on every component of every entity read
   **539327184**, every `Single` read **1.402156E-19**. Not a plausible wrong
   number. The SAME number everywhere, which is the tell.
2. Raw il2cpp field offsets off that boxed pointer HARD CRASHED the dedicated
   server process on the first request. Twice. So did the raw
   `il2cpp_class_get_fields` iterator, reading metadata only.

`GetComponentBoxed` does not hand back an object backed by real chunk memory on
this build. **Do not spend another session on a generic value reader.** Values
are read the way cycle 2 reads them - typed, with the type spelled out - and the
inventory now says which type to spell.

**What caught failure 1 cost nothing and is the transferable part.** Every entity
carries `Stunlock.Core.PrefabGUID`, whose value the same response ALREADY states
from a typed read. The generic reader said 539327184 where the truth was
-327335305. A reader with no such control would have shipped and every line of
the inventory would have been fiction. When building any new reader, find the
quantity you already know and make the new path restate it.

### The 14 fields, and NOT ATTEMPTED is empty

T1 `ProjectM.Health.MaxHealth`. T3 `UnitLevel.Level`. T4 and P2 named as
candidates. A1 `AbilityCastTimeData.MaxCastTime`. A2
`AbilityCooldownData.Cooldown` plus `GlobalCooldown.Value`. A3
`DealDamageParameters.MainFactor`. A4 `.MainType`. L1 CLOSED as a four-hop chain:
item -> `EquippableData.BuffGuid` -> `EquipBuff_Weapon_<Family>_Base` ->
`DynamicBuffer<ReplaceAbilityOnSlotBuff>` -> `.NewGroupId`.

**T2 splits and the split is the finding.** `UnitStats` carries
`PhysicalResistance`, `SpellResistance`, `FireResistance` and
`CorruptionDamageReduction`. Holy, Silver and Garlic have NO unit-side field
anywhere in 150 enumerated components; `ResistanceData` holds only global
per-rating conversion rates. Those are the anti-vampire types, so the absence is
coherent rather than a miss - but it is a full enumeration, not a failed
`HasComponent`, which is what makes it readable at all.

A5 is PROVEN ABSENT as a field: no power-selector member on the `_Hit` entity's
51 components, and `MainType` is the only discriminator present. A6 is the one
PARTIAL and it is a counting job over buffer lengths, not a hunt.

### Two cycle 2 statements corrected, both by a live component list

- **`ProjectM.AbilitySpellSchool` DOES exist**, on the ability GROUP, carrying
  `SpellSchool` (guid) and `Tier`. Cycle 2 recorded "there is no `SpellSchool`
  component type" and joined through the `<School>SpellSchoolAsset` buffer
  instead. Those 54 rows are not wrong; the type was missed by metadata scans and
  a live list found it in one run. Exactly the `EquippableData` shape.
- **`ProjectM.WeaponAbilityData` tells a weapon group from a spell group by
  COMPONENT.** That is what dissolves ROADMAP cycle 3 gap 3 in data rather than
  by argument. `VBloodAbilityData.AbilitySchool` is a second school source and
  its enum carries `Shadow`, which the six-school join cannot produce.

### The liveness assertion, and a real subject for the phase 3 control

Instanced `CHAR_Vampire_Dracula_VBlood` is entity **322916** with NO
`Unity.Entities.Prefab`; the prefab is entity **29012** with it. 151 components
against 150. Instance-only: `AttachParentId`, `AttachedBuffer`,
`DisabledDueToNoPlayersInRange`, `Unity.Entities.Disabled`. **Every stat-bearing
component is on BOTH**, so phase 3's prefab-versus-instance control can be a
VALUE comparison rather than a presence check.

### Two operational traps that each cost a debug cycle

- **Two plugin copies under `plugins\`.** A stale flat
  `plugins\RedMoon.Bridge.dll` sat beside the fresh
  `plugins\RedMoon.Bridge\RedMoon.Bridge.dll`. BepInEx loaded both; one bound
  8780 and the other stood down, and the one answering was the STALE build. It
  served `/health` perfectly and returned `not_found` for the endpoint that had
  just been built. Check for a second copy before blaming the code.
- **The server sometimes dies on a relaunch immediately after `taskkill /F`.**
  Waiting a few seconds and launching again works every time. Not investigated.

`docs/OPERATIONS.md` named a bridge `.sln` that has never existed; corrected, and
it now records the two-copies trap.

## 2026-07-26 - Cycle 3 spike SPEC approved, and the repo went public

ARCHIVED to `docs/history_notes.md`. Summary only: ledger 003a, commit
`c95c47f`. The cycle 3 input-spike spec was approved with five operator
decisions, the load-bearing one being that coefficients key on the ability
GROUP rather than the ability or the school. No code was written. The repo
was also made public after a full-history secret scan.

## 2026-07-26 - CYCLE 2 CLOSED, cycle 3 opened

ARCHIVED to `docs/history_notes.md`. Summary only: cycle 2 closed on the
operator's call with three weighed residue items, and the session found the two
cycle 3 blockers - there is no boss stat line and there are no ability
coefficients in the promoted tables.

## 2026-07-26 - Cycle 2 part 1: ADR-005, the Python half, spikes S4 and S3a closed

Branch `cycle-2-bridge`, two commits (`9fbce0c`, `251803b`). Cycle 2 is NOT
done and is not claimed to be. Ledger entry 002a carries the detail.

The two things the last session said must be settled BEFORE code are settled:

1. Port arbitration. RULED: mint the fifth port. Client binds 8777, dedicated
   server binds 8780, chosen by `core.ports.bridge_port_for_host`. ADR-005
   amends ADR-003. The stand-down path, install step 6b, acceptance criterion 5b
   and risk R15 are STRUCK from the spec - do not implement them. Operator
   approved the frozen `core/ports.py` edit and the ADR amendment before it was
   made.
2. `PrefabCollectionSystem`. CONFIRMED, not corrected:
   `ProjectM.PrefabCollectionSystem` in `ProjectM.Shared.dll`, deriving from
   `Stunlock.Core.PrefabCollectionSystem_Base`. The label carried from
   `ROADMAP.md` survives contact with the build.

State at close, every number observed in one run after the last edit:
`python -m pytest` 241 passed (was 106), `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0.

Shipped: `gen_bridge_ports.py`, `core/bridge_client.py`, `core/table_deep.py`,
`install_bepinex.py`, `rmdata_ingest.py`, `bridge_probe.py`,
`Directory.Build.props`, ADR-005, `docs/BRIDGE_SPIKES.md`.

Environment, done and verified live: BepInEx 1.733.2 installed into BOTH hosts
(233 files each, Thunderstore metadata dropped, `v3\` untouched). The dedicated
server launched once and generated 169 Il2CppInterop assemblies. Both v3
negative controls refuse.

Spike status. S4 CLOSED by measurement: a net6.0 library builds under SDK
10.0.301 with NO targeting pack and NO `global.json` - neither fallback is
needed. S3a CLOSED. S3 PARTIAL - the component types are located and named
(`EquippableData`, `RecipeData`, `RecipeRequirementBuffer`, `SpellLevel`,
`BloodQualityBuff`), the field mapping is not done. S1, S2, S5, S6 OPEN.

One process incident, and the plugin contract that fell out of it. `251803b` was
committed while a build agent was still live and captured its file mid-mutation
test, so that ONE commit carries a disabled v3 guard in `bridge_probe.py`.
Correct at `d614a09` and at HEAD; verified with `git show`, not taken on the
agent's word; no history rewrite. Standing rule, re-paid: do not commit while
agents live, and read `git show --stat` afterwards.

That agent's mutation testing also found a hole worth knowing about: a mutation
letting the loader-log banner matcher accept ANY line containing
`RedMoon.Bridge` SURVIVED 25 tests, because the negative fixture had no banner
token at all. That is cycle 1's failure mode a second time - a gate that cannot
fail. It is now pinned. CONSEQUENCE: `Plugin.cs` must emit a banner carrying
version, host AND port, shaped `RedMoon.Bridge v<semver> host=<client|server>
port=<n>`. The probe requires all three tokens.

Three things the next session must not get wrong:

1. The CLIENT has BepInEx but has NOT been launched, so it has no `interop\`
   tree yet. The R17 interop diff cannot run and no `.csproj` reference set may
   be pinned until it does. Launching the game client was left to the operator
   deliberately rather than done unattended.
2. S1 parts b, c and d are NOT answerable from static metadata. `LogOutput.log`
   carries loader activity only and never names a world - that was checked, not
   assumed. Enumerating worlds needs a plugin in-process, so the correct next
   artifact is a MINIMAL enumerate-and-log plugin, not the full bridge.
3. Honest correction to acceptance criterion 2: the `--target server` pointed at
   the root negative control is UNREACHABLE, not refused, because the installer
   derives the server target from `--root`. Prevented by construction, but not
   the control the spec asked for. Do not tick it off as passed.

## 2026-07-26 - Cycle 2 spec APPROVED, no code yet

Spec written and approved: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`.
ADR-004 records the ruling. No C# exists yet. Suite still 106 passed,
`ascii_guard` exit 0, both observed this session rather than carried forward.

Ground truth probed live, all of it new:

- The install holds TWO full game copies. Root is `v1.1.13.0-r99712-b17`, the
  pinned build and the one Steam launches. `v3\` is a stale `v1.0.10.4-r91333`
  copy that must never receive BepInEx. The installer asserts VERSION first.
- IL2CPP, not Mono (`GameAssembly.dll`). Loader is BepInExPack V Rising
  `1.733.2`, wrapping BepInEx 6.0.0 bleeding-edge `be.733` on CoreCLR net6.
- `VRising_Server\VERSION` reads `VRisingServer: v1.1.13.0-r99712-b17
  (202605251709)`. Same semantic build as the client, DIFFERENT prefix and
  trailing timestamp, so the install assert compares the semantic build only.
- The game was launched once. `AppData\LocalLow\Stunlock Studios\VRising\` now
  exists with `Player.log`, `Settings\v4\ClientSettings.json`, `CloudSaves\` and
  `ConsoleProfile\`. No save directory, because no world was created.
- Only SDK present is .NET 10.0.301. The plugin targets net6.0. That path is an
  unresolved build risk, not a working config.

Operator rulings: the plugin targets BOTH hosts (client and dedicated server,
ADR-004, overriding the client-only recommendation); `/state` becomes an
envelope carrying `state: null` plus a build stamp and `docs/API.md` was amended
to match; generating `RmPorts.g.cs` into the `test_ports.py` allowlist is
approved; the C# test project is deferred past cycle 2; and downloading the
BepInEx pack is authorized for the next session only.

Two things the next session must settle BEFORE writing code:

1. Port 8777 arbitration when both hosts run at once has a chosen answer, not a
   clean one - bind-time first-come, loser stands down, plus a procedural
   "start the server first". That is procedure, not enforcement. Minting a fifth
   port instead needs an ADR-003 amendment and that call belongs before
   implementation.
2. `PrefabCollectionSystem` is an UNVERIFIED label carried from `ROADMAP.md`. It
   is not a confirmed type name. Six spikes (S1 to S6) remain open and block
   implementation.

## 2026-07-26 - Cycle 1 COMPLETE and merged

Cycle 1 shipped end to end. Branch `cycle-1-harness`, 34 commits, merged into
`master` as `2a493ea`. Ledger entry 001 carries the detail.

State at close, all verified live rather than reported:

- `python -m pytest` 106 passed, `python -m ruff check .` clean,
  `python tools/ascii_guard.py` exits 0.
- `python tools/rmdata_extract.py` writes `data/rmdata/1.1.13.0-r99712/` with
  8379 localization strings and 28 markup codes, byte-identical across runs, and
  seeds `tables/` with five empty validated envelopes for the cycle 2 bridge.
- Remote is `https://github.com/Remus3/RedMoon` (private). `master` pushed.
- `RM-DataRefresh` is installed and Ready, next run 05:30 daily.
- Memory namespace live at
  `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\`, restorable from
  the committed seed in `docs/memory_seed/`.

Two findings worth carrying forward, both caught by review rather than by
running code:

1. The precommit gate was wired with `"matcher": "Bash(git commit:*)"` -
   permission-rule syntax in a field matched against the tool name - so it never
   fired for the whole cycle despite being unit-tested and documented. Fixed to
   `Bash|PowerShell`, with a test that now rejects specifier syntax in any
   matcher. Worth remembering: a hook passing its unit tests says nothing about
   whether it is wired.
2. `docs/BLOODFORGE.md` named `data/rmdata/<build>/tables/*.json` as Bloodforge's
   inputs, but nothing created that directory and `empty_table()` had no
   production caller. Cycle 2 would have invented the path by accident. The
   extractor now produces the seam, never clobbering a populated table.

Parked items and every review ruling are archived in `docs/history_notes.md`.

## 2026-07-26 - Cycle 1 kickoff

Project created at `C:\RedMoon\`. Design spec and implementation plan written
and committed. Ground truth probed: V Rising build
`v1.1.13.0-r99712-b17 (202605251526)`, install at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`, game never launched (no
`AppData\LocalLow\Stunlock Studios`), dedicated server ships with the client.
Ports 8777, 8778, 8779 and 8783 confirmed free; the `RM-*` scheduled-task
namespace confirmed unused.

Key decision: item and ability stat data cannot be extracted offline. It arrives
in cycle 2 from the runtime bridge dump. Cycle 1 ships localization, difficulty
presets, settings schema, and empty typed tables.

Deep archive. Pruned `WAKEUP_NOTES.md` entries and closed context land here so
the working documents stay short.

(No entries yet.)

## Cycle 1 - subagent-driven execution record (2026-07-26)

Archived from the SDD workspace ledger before the scratch directory was deleted.
It records every review finding, ruling and parked item from the nine-task run.

# SDD ledger - plan: /c/RedMoon/docs/superpowers/plans/2026-07-26-redmoon-cycle1-harness.md

Branch: cycle-1-harness (no worktree: the plan hard-codes absolute C:\RedMoon paths in .claude/settings.json and the memory namespace test, which a relocated worktree would break).

Task 1: implemented (commit 5dbca7e, 6/6 tests pass, CLI exit 0)
Task 1: review - spec compliant; 2 Important findings, both plan-mandated (verbatim from plan code); 1 Minor deferred
Task 1: minor (deferred): is_authored exclusion branches not independently exercised - .git/COMMIT_EDITMSG and assets/icon.png are already rejected by the suffix check, so EXCLUDED_DIRS/EXCLUDED_PREFIXES have no proving case
Task 1: controller-resolved warning - reviewer could not verify is_authored callers pass relative paths. Checked plan Task 7: precommit_gate calls is_authored(Path(rel)) where rel comes from git diff --cached --name-only, which is repo-relative. Safe.
Task 1: fix round 1/5 (3 addressed, 0 open; commits 5dbca7e..528f948)
Task 1: complete (commits a8cf3dd..528f948, review clean; plan text realigned in d174326)
Task 2: complete (commits d174326..dc4be1b, review clean)
Task 2: minor (deferred): tests/test_ports.py read_text has no UnicodeDecodeError handling - a non-UTF-8 .py would raise instead of failing cleanly
Task 2: minor (deferred): port-guard exclusion set omits .venv/venv/site-packages/node_modules/build/dist - latent spurious-trip risk if a later task vendors deps under the repo root (third-party code commonly uses 8888)
Task 3: review - spec compliant (byte-exact transcription verified programmatically); 1 Important plan-mandated (commit message lacks a scope); 1 Minor
Task 3: controller-resolved minor - CLAUDE.md frozen-file list names precommit_gate.py / text_first_guard.py / pytest_guard.py which do not exist yet. Task 7 builds all three. Not a defect; will be true at end of cycle.
Task 3: ruling - human accepted the scopeless docs commit; plan Global Constraints relaxed (scope optional for repo-wide doc commits). No history rewrite.
Task 3: complete (commits dc4be1b..293a4ab, review clean)
Task 4: ruling - human chose to name Riot Commander plainly in ADR-001 (filename kept, prose updated); ADR-003 stays anonymous; root docs stay clean
Task 4: fix round 1/5 (1 addressed, 0 open; commits b1bef26..81ac017)
Task 4: complete (commits caa7bb7..81ac017, review clean; plan realigned in 9ab2ed4)
Task 4: minor (deferred): test_every_adr_file_is_listed_in_the_index uses a raw substring check against the whole README, not the INDEX_LINE regex - an ADR named only in prose would satisfy it
Task 4: minor (deferred): docs/adr/README.md describes Status as one of four sections, but every ADR renders it as a bold inline field first, not a trailing heading
Task 5: ruling - human chose to close both coverage gaps now via a test-only synthetic-install fixture
Task 5: fix round 1/5 (2 addressed, 0 open; commits 10773f6..1a15024)
Task 5: complete (commits 9ab2ed4..1a15024, review clean; plan amended in 0ecf364). Real run: 8379 strings, 28 codes, build 1.1.13.0-r99712, idempotent, data/ gitignored.
Task 5: minor (deferred): no try/finally around tmp.write_text, so a mid-write exception leaves a stray .tmp (self-heals next run)
Task 5: minor (deferred): pointer write duplicates the temp+replace pattern instead of reusing a shared primitive
Task 5: minor (deferred): extract() never removes stale files in build_dir before writing - matters only on a future schema change
Task 5: minor (deferred): main() success path untested; a deep extract() failure would print a raw traceback
Task 6: complete (commits 0ecf364..81a702c, review clean; 16/16 module, 57/57 suite)
Task 6: minor (deferred): core/tables.py validate_table uses a bare _TYPE_MAP[spec["type"]] lookup - an unknown type string in a hand-edited schema would raise KeyError instead of returning a problem string, breaking the function's own contract
Task 6: minor (deferred): test_validate_table_rejects_a_wrong_type also sets tier to "x" incidentally; only the prefab_guid problem is asserted
Task 7: implemented (commit 759d60b, 9/9 module, 66/66 suite). Implementer caught and correctly fixed a backslash-escaping defect in the plan's settings.json; review confirmed the fix correct on its merits.
Task 7: controller-verified live - hooks run from a foreign cwd (C:\Users) and exit 0; settings.json decodes to clean single-backslash paths; deny reason resolves ports.DASHBOARD to 8778; rm_facts reports real build 1.1.13.0-r99712 and all four ports free
Task 7: review - 4 Important, all plan-mandated: (1) reproduced AttributeError crash on valid-JSON-non-dict stdin in 3 of 4 hooks, violating the always-exit-0 contract; (2) 4 unbounded subprocess.run calls; (3) ruff branch of check_staged untested; (4) docstring claims net-new ruff findings but code blocks on any finding
Task 7: ruling - human chose to fix all four, plus the port-literal minor in tests/test_hooks.py
Task 7: plan defect corrected by controller - settings.json escaping was \\ in the plan (would parse to a double backslash); plan now uses \ throughout
Task 7: fix round 2/5 (1 addressed, 0 open; commits b6d0fdd..4730bfb) - settings.json PostToolUse budget 60->900, only that field changed
Task 7: complete (commits 81a702c..4730bfb, review clean)
Task 7: minor (deferred): tests/test_hooks.py hardcodes each script's internal subprocess timeout in a dict rather than parsing it from tools/*.py, so it catches settings.json-side drift but NOT a future script-side timeout increase above its harness budget
Task 8: implemented (commit 3b58bd6, 6/6 module, 87/87 suite)
Task 8: review - approved; 2 Important plan-mandated (memory assertion loop omits project_stats_require_bridge; memory tests are structure-only so a blank body would pass); 2 Minor
Task 8: minor (deferred): tests/test_claude_config.py hardcodes an absolute per-machine memory path, so the test is non-portable to another machine or CI
Task 9: review - NEEDS FIXES. Important: --show space-joins argv so the printed command would not run if pasted (the /tr value contains an inner space); no test exercises a path containing a space. Plan-mandated: ledger entry lacks the commit hash its own format requires; commit message not imperative.
Task 9: minor (deferred): build_create_command raises a bare KeyError while build_delete_command raises a labelled one - asymmetric error quality
Task 9: minor (deferred): --install/--remove always act on the whole TASKS dict with no per-task selection, which will matter when cycle 8 adds more tasks
Task 9: minor (deferred): /rl HIGHEST is hardcoded in the builder rather than sourced from the spec dict like every other schtasks parameter
Rulings (human): ledger hash is backfilled at merge and /done gains that step; imperative commit mood dropped from the plan constraint (CLAUDE.md never stated it); both Task 8 memory-test weaknesses fixed now
Task 9: fix round 1/5 (1 addressed, 1 open; commits 1dc5150..dd9015b) - --show now uses list2cmdline and matches real execution; the new quoting test was proven toothless (an `or` fallback let it pass under both the fix and the original unquoted bug, and it never exercised main())
Task 9: fix round 2/5 dispatched - replace with a CommandLineToArgvW round-trip test asserting the /tr value tokenizes back to exactly one argument, plus a capsys test on main() --show asserting it differs from a naive space-join; both must be proven to fail against deliberately reverted production code
Task 8: fix round 1/5 (3 addressed, 0 open; commits dd9015b..3f6b864) - entry set now derived from disk via set-equality, body-content floor of 100 non-whitespace chars asserted on the body after frontmatter, done.md gained the ledger-hash backfill step with correct renumbering. Deliberate truncation proof: frontmatter-only file failed with "assert 0 >= 100", restored file passes.
Task 8: complete (commits cb79d10..3f6b864, review clean)
Task 9: fix round 2/5 (1 addressed, 0 open; commits 3f6b864..661d542) - old weak test deleted; TEST A round-trips through CommandLineToArgvW asserting the /tr token by equality; TEST B drives main() --show via capsys asserting both equality with list2cmdline and inequality with the naive space-join; both proven to fail against deliberately reverted production code
Task 9: fix round 3/5 dispatched - unused `from ctypes import wintypes` leaves the repo failing `ruff check .` (controller-verified, 1 error), which the project's own precommit gate would block
Task 9: fix round 3/5 (1 addressed, 0 open; commits 661d542..adafce3)
Task 9: complete (commits 3b58bd6..adafce3, review clean)
ALL 9 TASKS COMPLETE. Controller-verified at branch head: ruff check clean, 95 tests pass, ascii_guard exit 0.
FINAL REVIEW (opus, whole branch ae4bb80..b860e15): 1 Critical, 5 Important, 8 Minor. Critical C1 - the precommit gate never fired: matcher "Bash(git commit:*)" is permission-rule syntax in a tool-name field, and the plan had also dropped the PowerShell entry that makes the equivalent work upstream.
FINAL FIX WAVE (7 commits b860e15..015143b): C1 matcher corrected to Bash|PowerShell with a test banning specifier syntax in matchers; ledger count corrected to the observed 106; ROADMAP cycle 1 retired; the tables/ seam now produced by extract() with no-clobber and stale-file sweep; port-literal rule enforced for RM's own ports across .py/.cs/.json/.ps1; memory namespace seed committed under docs/memory_seed/ with a drift guard; 8 minors closed.
FINAL RE-REVIEW: all findings addressed, no new Critical/Important breakage. Both implementer deviations judged sound.
PARKED (controller adjudication, none load-bearing, no second fix wave):
Parked: seed_tables uses `if path.exists()` not `is_file()`, so a directory occupying tables/<name>.json would silently skip seeding forever - ruling: cannot arise without manual mischief inside a gitignored generated directory; fix opportunistically in cycle 2.
Parked: stale-file deletion in tables/ is extension-agnostic by design and matches the instruction as written, with a covering test - ruling: intentional, not a defect.
Parked: test_live_memory_matches_the_committed_seed and test_memory_seed_is_ascii lack their own non-emptiness guard - ruling: the sibling test_memory_seed_covers_every_live_memory_file asserts is_dir() and set-equality, so the suite cannot pass with a missing or empty seed.
Deferred (doc-sync opportunity, not a blocker): docs/BLOODFORGE.md never gained a line acknowledging the new never-clobber-a-populated-table guarantee that cycle 2 and 3 will depend on.

## 2026-07-26 - Cycle 2 part 2: the probe plugin, and seven spikes closed by running it

Branch `cycle-2-bridge`, three commits on top of `5933cfe`. Cycle 2 is still NOT
done. Ledger entry 002b carries the detail.

State at close, every number observed in one run after the last edit:
`python -m pytest` 245 passed, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0.

The artifact is `_scratch\rmprobe\`, a MINIMAL enumerate-and-log BepInEx plugin
built and deployed to both hosts BEFORE any bridge code. It is scratch and not
committed, same rule as `_scratch\typedump\`. It compiles the same generated
`RmPorts.g.cs` the real plugin will, so the no-port-literal rule holds even in
scratch, and it reads ECS only from `Update()` while its listener thread serves a
constant, so it tests both halves of D7 without violating D7.

Closed by measurement, not by reading:

- **R17.** The client generated its own interop tree: 172 files, 169 dll,
  matching the server exactly. That also explains the earlier "169 assemblies" -
  it was the dll count, so no correction was needed. Assembly NAME sets are
  identical. All 169 hashes differ, which is NOT a divergence signal because
  Il2CppInterop codegen is non-deterministic; a hash diff would report 100
  percent divergence between any two generations. The type-level diff is the one
  that decides the `.csproj`, and `ProjectM.Shared`, `Stunlock.Core`,
  `Unity.Entities` and `ProjectM.Gameplay.Systems` have ZERO real divergence.
- **S4 fully, R2 retired.** The build works with the whole reference set, not
  just the bare target framework. One non-obvious reference:
  `Paths.BepInExVersion` returns a `SemanticVersioning.Version`.
- **S1(a)** `World.All`. **S1(d)** `BepInEx.Paths.ProcessName`, `VRising` vs
  `VRisingServer`.
- **S1(c)** the server's target world is named `Server`, 710 systems, and world
  selection MUST be by name: `Default World` is also a Simulation world, sits at
  index 0, and throws when asked for the prefab map.
- **S2** an Il2Cpp-injected `MonoBehaviour` `Update` reaches main thread 1 in
  both hosts. No Harmony patch needed.
- **S5 and R11** `HttpListener` binds and serves in both hosts CONCURRENTLY,
  which is the ADR-005 payoff observed rather than argued, and after
  `taskkill /F` the port holds no LISTEN and `--expect-unreachable` passes.
- **S6 partial** prefab map `Count` 1189 in under a millisecond.
- **S3** items and recipes are mapped. The headline: `EquippableData` carries NO
  stats, only a `BuffGuid`, so `items.stats` is a two-hop read through the buff
  prefab's `DynamicBuffer<ModifyUnitStatBuff_DOTS>`.

One finding that is a real defect rather than a spike result. The suite had a
test whose comment read "nothing is listening on the bridge ports during the
suite" and which relied on it. The probe bound the client port, the connection
succeeded, and the test failed with no defect in the code under test. That is the
mirror image of cycle 1's gate-that-cannot-fail: a gate that fails for reasons
unrelated to its assertion. Fixed by pointing `RM_GAME_HOST` at `192.0.2.1`
(RFC 5737 TEST-NET-1). Proof it is real: 245 passed with the probe still bound
and answering curl.

Three things the next session must not get wrong:

1. **A client-side dump is UNPROVEN.** At the main menu the client has TWO worlds
   and NO prefab-carrying world at all. S1(b) has only the menu sample. The
   in-game client world set needs a character loaded and was not measured - the
   operator chose to wrap instead. Do not write down that the client can serve a
   dump.
2. The rest of S3 - ability school, V Blood level, blood bonus tiers - is gated
   behind the SAME in-game sample, not behind more metadata reading. There is no
   `SpellSchool` component type; the school-shaped types found are
   `SpellSchoolAuthoring`, `SchoolDebuffData` and
   `SpellSchoolTierProgressionPoints`, none obviously the per-ability field.
3. `items.stats` as a flat name-to-number map is expected to need a schema
   amendment, because it cannot carry `ModificationType`. Decide that at the
   first-dump review, from the census, not before.

Operator request logged, not started: automated V Rising launch plus OBS capture.
Filed in `BACKLOG.md` and scoped to cycle 8 - it is an ops concern and was
deliberately kept out of the middle of the spike chain.

## 2026-07-26 - Cycle 2 part 4: /state goes live, two fabricated fields retired, S1(b) closed

Branch `master` (see the branch note below), commit `9b1f58f`. Ledger 002d.

State at close, every number observed in one run after the last edit:
`python -m pytest` **284 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release` exit 0 with 0
warnings. All four re-run by this session rather than taken from the build
agent's report.

**BRANCH NOTE, read this first.** The session opened checked out on `master` at
`42e5b39` while all 15 cycle 2 commits sat unmerged on `cycle-2-bridge` - which
is why `docs/BRIDGE_SPIKES.md` read as missing at bootstrap. `master` was
fast-forwarded to `6acbc66` and pushed, and work continued on `master`. The
fast-forward was deliberate: a `merge:` commit would have recorded a cycle 2
completion that has not happened. `cycle-2-bridge` still exists as a safety net.
There are NO worktrees - `git worktree list` shows only `C:/RedMoon`, confirming
last session's "worktree-isolated" agent really did write into the main tree.

**The headline: `bridge_probe --motion-diff --expect-host client` PASSES.**
`/state` returned `state: null` at session start and now returns live data:
position `-868.508972, -1788.14209` to `-862.950745, -1784.278076` across five
seconds with the operator moving.

**The finding to carry into every future session: a green suite and a clean
build proved nothing here.** The first `StateReader.cs` compiled at 0 warnings,
passed all 284 tests, and on a `batchMode` server with NOBODY connected returned
`state_reason: ok`, `position 0,0,0`, `health 125/125`. It was reading the
`PlayerCharacter` PREFAB TEMPLATE. Only `--motion-diff` caught it, because two
samples five seconds apart were byte-identical. The fix is one filter - skip
`Unity.Entities.Prefab` - after which the same empty server honestly returns
`no_character` with `state: null`. That is a real negative control; a stub
cannot tell the two cases apart. For a live-data reader, tests are necessary and
nowhere near sufficient.

Four things closed by measurement:

1. **S1(b) CLOSED. The client CAN serve a dump.** `Client_0` fills
   `0 -> 7005 -> 16352 -> 30484`, `GameDataInitialized` flips as it settles,
   census `total=85591 withPrefabGUID=31953` in 95 ms. The client map is LARGER
   than the server's by 7975 entities. NEAR-MISS worth keeping: the client
   census line reads `equip=2 recipe=2 spell=0 blood=0 vblood=0`, which looks
   exactly like "the client has no item data" - but the SERVER line reads
   `equip=2 recipe=2` too and produced 425 items. Those are capped deep-dump
   selectors, evidence of nothing. Comparing against the server log caught it.
2. **`items.tier` has NO SOURCE on this build.** 67 `Tier`-shaped fields across
   all 169 interop assemblies, ZERO per-item-prefab. `Rarity` zero hits
   anywhere. `ProjectM.ItemData` has none. Dropped from `required` at
   `schema_version` 3, kept declared, omitted by the dumper. The tempting
   rejection: `ArmorLevelSource.Level` is exactly `10 x tier` on 117 of 425
   rows, but that divisor comes from the barred `_T0x` token, the value is
   already `gear_score`, and 74 rows have no level component at all.
3. **The localization join does not exist offline.** All 8379 `strings.json`
   keys are dashed UUIDs; 0 of 425 rows join by name, decimal guid, or six hex
   forms. Best heuristic was 53/425. Runtime route is
   `GameDataSystem.ManagedDataRegistry`, NOT `PrefabLookupMap` - whose claim to
   serve the join was a false line in `BRIDGE_SPIKES.md` and is now corrected.
4. **R17 extends to `Unity.Transforms` by measurement.** 61 types both hosts, all
   4 diffs per-build codegen hashes, identical signature to `Unity.Entities`.

**The data backfill is DONE, not merely prevented.** The 425 rows on disk
carried the fabricated `tier: 0`. Plugin rebuilt, redeployed, server relaunched,
`/dump/prefabs` re-taken and promoted. Live `items.json` is `schema_version` 3,
425 rows, 0 carrying `tier`, counts identical (425 / 663 / 899 stat entries) so
it is a true like-for-like recovery. `data/rmdata/` is gitignored, so it lives
on disk and is reproducible rather than committed.

Still open, and deliberately NOT claimed: whether client item COMPONENT data
matches the server's - only the prefab MAPS were compared, and settling it needs
the real bridge run in the client and a diff of the two dumps. Plus all of item
5: `recipes.station_guid`, the ability-group-to-`_Hit` join,
`VBloodConsumeSource.Tier` value measurement, `Unload()`'s graceful path. The 4
unmapped recipes are confirmed `recipe prefab with an empty item output buffer`,
consistent with the `RecipeOutputUnitBuffer` hypothesis but not proven to be it.

Process note: `.claude/settings.json` now pre-approves computer-use and the
Windows-MCP VISUAL tools, but DENIES `Windows-MCP PowerShell/FileSystem/Registry/
MultiEdit` - the `precommit_gate.py` hook matches `Bash|PowerShell` only and
would never fire on `mcp__Windows-MCP__PowerShell`, so allowing it would have
opened an ungated commit path.

## 2026-07-26 - Cycle 2 part 3: the plugin ships, the first real dump lands, four recorded findings corrected

Branch `cycle-2-bridge`, five commits on top of `46e405f`. Ledger entry 002c.

State at close, every number observed in one run after the last edit:
`python -m pytest` **272 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release` on
`bridge/src/RedMoon.Bridge` exit 0 with 0 warnings. The build and the suite were
re-run by this session rather than taken from the build agent's report.

**The headline: `data/rmdata/1.1.13.0-r99712/tables/items.json` has 425 rows and
`recipes.json` has 663.** The plugin loaded in the dedicated server, bound 8780,
answered `/health` and `/dump/prefabs`, and `rmdata_ingest` validated and
promoted the result. That is the first item stat data ever to enter this repo.

Four things that were WRITTEN DOWN and turned out wrong. All four were corrected
by running something, and the corrections are the real value of the session:

1. **`items.stats` is a ONE-HOP read.** `ModifyUnitStatBuff_DOTS` is populated
   directly on the item prefab. The buff prefab named by `EquippableData.BuffGuid`
   has NO stat buffer at all. The two-hop path in `BRIDGE_SPIKES.md` was inferred
   from a field list and presented as measurement.
2. **The prefab count is 23583, not 1189.** The map fills over about 1.7 s and
   1189 was a mid-load sample. `GameDataInitialized` flips exactly as it settles,
   so it is a real readiness gate. A census taken at first non-zero count returns
   castle tiles and blueprints and looks complete while being wrong - that
   happened on the first run and is why the gate exists.
3. **The ability school is `DealDamageParameters.MainType`** on the `_Hit`
   entity, `ProjectM.MainDamageType`. Not on `_Cast`, `_AbilityGroup`, `_Buff` or
   `_Projectile`, all four checked against real component lists. Six samples were
   taken deliberately because one `Physical` reading cannot be told from a
   default; `MainType` and `MainFactor` both vary.
4. **`vbloods` was probed with the wrong marker.** `ShadowVBloodUnitTagComponent`
   is a runtime tag, so its zero was a true absence AND misleading. The real
   types are `VBloodUnit`, `VBloodConsumeSource`, `VBloodAbilityBuffEntry`,
   `VBloodUnlockTechBuffer`.

The schema amendment was ruled ON EVIDENCE and one of its own arguments was
discarded. `items.stats` went to an array at `schema_version` 2 because three
modification kinds occur in the real data (Add 665, AddToBase 232,
MultiplyBaseAdd 2). The "a map would collapse duplicate StatTypes" argument was
MEASURED FALSE - zero of 425 items repeat a StatType - and is not used to
justify the change. `blood_types.bonuses[].stats` is a different field and was
deliberately left alone.

Three things the next session must not get wrong:

1. **`items.tier` is fabricated as 0 on every one of the 425 rows.** The schema
   requires it, no per-item tier component exists on this build, and the dumper
   emits a placeholder. Do NOT let a cycle 3 consumer treat it as real, and do
   NOT close it by parsing the `_T0x` name token.
2. **Nothing has been run in the CLIENT.** The client half of S1(b) is still
   open: `Client_0` read `Count=0` at the load instant and was never re-measured.
   A Private Game spawns a child `VRisingServer.exe` that does not load BepInEx,
   so in that configuration neither host can serve a dump. The reason it does not
   load is a HYPOTHESIS, not a measurement.
3. `/state` returns `state: null` honestly - there is no `StateReader.cs` yet, so
   `bridge_probe --motion-diff` cannot pass and should not be expected to.

Process note worth keeping: the build agent wrote into the MAIN working tree
despite being launched with worktree isolation, and `git worktree list` never
showed a second tree. Nothing was lost, but the "never commit while agents live"
rule did real work here. It also read one instruction in its brief against
`docs/API.md` D3, followed the repo rule, and flagged the conflict instead of
silently choosing - which is the behaviour that should be reinforced.

## 2026-07-26 - Cycle 2 part 5: all five tables populated, two recorded answers corrected

Branch `master`. Ledger 002e.

State at close, every number observed in one run after the last edit:
`python -m pytest` **289 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` on
`bridge/src/RedMoon.Bridge` exit 0 with 0 warnings. All four re-run by this
session, not taken from a report.

**The headline: `abilities` 54, `vbloods` 66, `blood_types` 13 are on disk.**
Together with `items` 425 and `recipes` 663 that is every table in
`core/tables.py`, from one `/dump/prefabs` in 714 ms, validated and promoted by
`rmdata_ingest --accept`.

**Two things that were WRITTEN DOWN as findings and were wrong. Both were
recorded by this project as measured, and both are the same failure: a real
measurement answering a question nobody had checked was the right question.**

1. **The ability school is not `DealDamageParameters.MainType`.** That reading is
   correct and it is the DAMAGE type - `Physical`, `Spell`, `Fire`, `Holy`,
   `Silver`, `Garlic`, `Corruption`. `abilities.school` is declared as blood,
   chaos, frost, illusion, storm, unholy or weapon. The real join is
   `DynamicBuffer<ProjectM.SpellSchoolAbility>` on the `<School>SpellSchoolAsset`
   prefab, whose element carries `.AbilityGroup`. It yields exactly 9 abilities in
   each of the six schools, which is itself a liveness signal - six buffers read
   independently do not land on the same count by accident.
2. **The V Blood level is not `VBloodConsumeSource.Tier`.** That field is a
   `SpellSchoolProgressionTier` with five members, measured
   `Tier1:23 Tier2:19 Tier3:13 Tier4:6 Undefined:4`. Five buckets cannot be a
   boss level. It is `ProjectM.UnitLevel.Level`, measured 16 to 91 over 92
   prefabs.

**The ability-group join, which was the session's first task, is a REFERENCE
join and the numbers are why.** Name join over 1474 `_AbilityGroup` names reaches
`_Cast` 1291 but `_Hit` only **258**. The reference chain
`AbilityGroupStartAbilitiesBuffer -> _Cast -> AbilitySpawnPrefabOnCast` resolves
a cast for **1474 of 1474**. A second spawn hop adds exactly 0, so one hop is the
answer and the 912 groups that never reach damage genuinely do not.

**`blood_types` went to `schema_version` 2 on evidence.** The version 1 nested
contract - a numeric `quality` threshold plus a name-to-number `stats` map - is
wrong on BOTH halves: no threshold field exists on the prefab, and every stat
magnitude on the tier buff reads 0 with `SoftCapValue` 1, scaled from blood
quality at runtime. The table now carries slot, 1-based tier, `buff_guid`,
`buff_name` and stat NAMES. Tiers ascend WITHIN a slot, not across the list; the
real row is primary 1..5 then secondary 1..4 and a global ascent check would
reject it. There is a regression test on that specific trap.

**Two negatives that are results, not failures:**

- `recipes.station_guid` is reverse-only AND one-to-many. `RecipeLinkBuffer`
  looked like the forward link and is not - 5 of 667 recipes carry it and every
  link resolves to another RECIPE. The station side is 35 `WorkstationRecipesBuffer`
  plus 23 `RefinementstationRecipesBuffer` holding 942 references over 663
  recipes. The field stays omitted until the singular-vs-plural schema question
  is decided.
- The runtime localization join is ABSENT on the server host. Over all 425
  equippables, `TryGet<ManagedItemData>` returns false 425 times, and the
  `TryGetWithoutLogging` control agrees, so it is not a logging refusal.
  `ManagedAbilityGroupData` over 200 groups: 0 hits. S7 had this INFERRED as
  working; it does not on this host.

Near miss worth keeping: the first blood-type deep dump sampled the first two
types, which are `BloodType_VBlood` and `BloodType_GateBoss`, both pointing at
the single buff that has no stat buffer. It looked exactly like "blood bonuses
carry no stats at all". Naming two REAL types settled it. Same shape as last
session's `equip=2 recipe=2` near miss: an unrepresentative sample that reads as
a family-wide absence.

Process note: the flashing PowerShell consoles the operator saw were the
`statusLine` command in `C:\Users\Administrator\.claude\settings.json`, which
spawns `powershell.exe` on every status refresh. It now runs with
`-NonInteractive -WindowStyle Hidden`; a backup of the original sits beside it as
`settings.json.bak-statusline`. Three other scheduled tasks outside the `RM-*`
namespace also run `powershell.exe`, two with an Interactive logon, but they fire
daily and weekly at 03:00 and 04:15 and belong to another project on this
machine, so they were left alone.

## 2026-07-26 - Cycle 2 part 6: the client host, and a wrong number four gates could not see

Branch `master`. Ledger 002f.

State at close, every number observed in one run after the last edit:
`python -m pytest` **317 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` on
`bridge/src/RedMoon.Bridge` exit 0 with 0 warnings.

**BOTH HOSTS RAN THE SAME BINARY AT THE SAME TIME.** The dedicated server on
8780 and the operator's live client on 8777, concurrent, which is what made
every comparison below like-for-like rather than a comparison of two builds.

**1. The client item COMPONENT data is IDENTICAL to the server's.** Row-by-row
diff keyed on `prefab_guid`, every field on every row of all five tables: ZERO
differences. Matching counts would have proved nothing - two 425-row tables can
disagree on every field - so this was diffed rather than counted. The client
dump costs 103 ms against the server's 794.

**2. `localization_guid` is WRITABLE, on the CLIENT only. The recorded absence
was a HOST fact that had been read as a BUILD fact.** Same binary, same call,
same session:

```
dedicated server   attempted=425  resolved=0    missed=425  quiet_hits=0
client             attempted=425  resolved=425  missed=0    quiet_hits=0
```

All 425 client guids are real `strings.json` keys - `Item_Headgear_WolfTrophy01`
to "Wolf Head". 342 distinct guids over 425 rows, because skins share a name.
The offline heuristic that was rejected reached 53 of 425.

The lesson is the session's inherited one, one layer up. Last session's warning
was "a real measurement can still answer the wrong question". This one is: a
real measurement can answer the right question about the wrong SUBJECT. `0 of
425` was correct, reproducible, and had a proper negative control
(`TryGetWithoutLogging`) - and it was a statement about a headless host that got
written down as a statement about the game. Every dump now carries its own
`localization` counter block and `rmdata_ingest` prints it, so a saved payload
says for itself which host produced it.

**3. `vbloods` is 65, not 66. A wrong number that four gates could not see.**
Diffing by `prefab_guid` surfaced duplicate rows: `abilities` 56 rows over 54
distinct guids on BOTH hosts (`AB_Blood_BloodRite_AbilityGroup` and
`AB_Blood_Shadowbolt_AbilityGroup` twice each), and the server 66 vbloods over
65 (`CHAR_Vampire_Dracula_VBlood` twice). More than one ENTITY can carry the
same `PrefabGUID` and the dumper wrote one row per entity.

Why it survived: every duplicate pair was BYTE-IDENTICAL. The shallow gate, the
deep nested gate, the schema and the census all inspect one row at a time, and
each of those rows was individually perfect. The only symptom was the COUNT, and
66 had already been written into `ROADMAP.md` and ledger 002e as a finding.
Fixed in the dumper (dedupe on first write) AND gated at ingest
(`duplicate_key_problems`, a cross-ROW check) - the producer being fixed today is
not the same as the defect being detectable tomorrow.

A trap inside the fix, caught before it shipped: `&&` short-circuits left to
right, so `seenItems.Add(guid)` placed BEFORE the marker-component test would
claim the guid on behalf of every entity carrying it and then reject the real row
when it arrived. That turns a duplicate bug into a missing-row bug. There is a
test asserting the guard order.

**4. `recipes.station_guids`, ADR-006.** The singular field is retired at
`schema_version` 2 and the plural array is emitted. 911 unique (recipe, station)
pairs from 942 raw references; 575 recipes reach a station, 88 reach none, 19 sit
at TWELVE stations each. That histogram is why first-station-wins was barred: it
would have been arbitrary for 138 recipes. The 88 empty lists ship as `[]`, so
"reachable from no station" stays distinguishable from "the inversion did not
run".

**5. `Unload()` is still UNOBSERVED, and the reason is worth keeping.** Measured
twice on a normal in-game quit: `LogOutput.log` gains nothing after
`Chainloader startup complete`. But `Unload()` logged NOTHING, so that silence
was equally consistent with "ran fine", "never ran" and "the logging pipeline
was torn down first" - a zero three hypotheses predict is not evidence. It now
appends to `BepInEx\redmoon-unload.log` via `File.AppendAllText`, OUTSIDE the
logging pipeline, so the three outcomes are distinguishable.

**CLOSED on the instrumented build: `Unload()` does NOT run.** A normal in-game
quit left the marker ABSENT, the log unchanged, and 8777 with no LISTEN. The two
channels fail independently, which eliminates "the pipeline was gone first", so
BepInEx 6 IL2CPP does not invoke `BasePlugin.Unload()` at shutdown. The control
that makes the silence readable: the observed run PROVABLY carried the
instrumented build, because the dump it served included `station_guids`, which
exists only there. Benign - R11 already measured that a hard kill releases the
port, and a normal exit takes the identical path.

The promoted dump is the CLIENT one: `items` 425 (schema 3, all 425 carrying
`localization_guid`), `recipes` 663 (schema 2, with `station_guids`),
`abilities` 54, `vbloods` 65, `blood_types` 13, in 103 ms.

Process note, answering the operator's flashing-console report: a 120-second
`Win32_Process` trace named them, and NONE is Red Moon's. They are
`cmd.exe /d /s /c npx ...` MCP launchers, each spawning its own `conhost.exe` -
`pathmode-mcp`, `desktop-commander`, `chrome-devtools-mcp`, `playwright-mcp` -
fired in bursts by four concurrent `claude.exe` instances, plus another Claude
session running a different project's `pytest` hook through Git Bash. Red Moon's own
hooks all run under `pythonw.exe`, which is windowless and never appeared as a
console. Last session's `statusLine` fix held: it did not appear in the trace at
all. The remedy is disabling unused MCP plugins in the user `settings.json`,
which currently lists 15 enabled.

## 2026-07-26 - CYCLE 2 CLOSED, cycle 3 opened

Branch `master`. Ledger 002g. Docs plus one test constant and one seed file. No
production code changed.

State at close, observed in one run after the last edit: `python -m pytest`
**317 passed**, `python -m ruff check .` clean, `python tools/ascii_guard.py`
exit 0.

**The decision.** The operator was given the residue against closing and chose to
close. Cycle 2's charter was live item and ability stat data on a local port, and
all five tables are populated, host-diffed and gated. The three residue items
were weighed rather than waved past:

- **4 unmapped recipes** - empty ITEM output buffer, they produce units, no
  cycle 3 consumer reads them. Closing buys a label, not data.
- **`items.tier`** - nothing left to spend a session on. No source exists on this
  build and both derivations are rejected on evidence. DECLARED and OMITTED is
  already the correct final state.
- **Weapon abilities produce no `abilities` row** - the only one with teeth,
  because Bloodforge computes weapon DPS and there is no `<Weapon>SpellSchoolAsset`
  to source a school from. Carried into `ROADMAP.md` cycle 3 as a NAMED INPUT GAP
  so no cycle 3 code scaffolds weapon damage on an assumed source.

**Two docs had drifted and are now synced.** `ROADMAP.md`'s cycle 2 section was a
running log appended to across six sessions, still carrying superseded numbers
inline with their corrections beside them - `vbloods` 66 was readable as current
if you stopped at the wrong paragraph. It is now a settled record.
`docs/ARCHITECTURE.md` was a full cycle behind: it read "Nothing runs as a
service in cycle 1", listed `bridge/` as planned, and named three modules out of
sixteen.

**A real gap the suite caught, and it was not mine.** Three tests in
`tests/test_claude_config.py` failed at session start, before any edit. Last
session wrote the memory entry `reference_flashing_consoles_are_mcp_launchers`
into the LIVE namespace and never seeded it into `docs/memory_seed/`. The live
namespace is outside the repository and uncommitted, so until this was fixed that
entry had no path back if it were lost - which is exactly the failure the seed
exists to prevent. Fixed by seeding the file, refreshing the seeded `MEMORY.md`,
and adding the name to `EXPECTED_MEMORY_ENTRIES`.

Worth keeping: three independent guards fired on one missing file, and the
session that created it saw none of them because it never re-ran the suite after
writing memory. Writing a memory entry is a repo-affecting act here.

**TWO CYCLE 3 BLOCKERS FOUND AT THE VERY END, and they are the most valuable
thing in this session.** While writing the next-session prompt I read the
promoted ROWS rather than the schema, and two of Bloodforge's declared inputs do
not exist:

1. **There is no BOSS STAT LINE.** `vbloods` rows carry exactly `level`, `name`
   and `prefab_guid`. No health, no resistances, no damage. `docs/BLOODFORGE.md`
   has named `tables/vbloods.json` as the source for "Boss stat line and
   resistances" since cycle 1 - written as a design intention, never checked
   against a real row, and false. **Time-to-kill is the engine's headline output
   and its denominator is not on disk.**
2. **There are no ABILITY COEFFICIENTS.** `abilities` carries identity, school
   and (16 of 54) a damage type. No cast time, no cooldown, no damage scalar.

The player side is NOT a gap and was checked in the same pass: 203 of 205 weapon
items carry real `PhysicalPower` or `SpellPower` over 29 stat types, each with an
explicit `modification`. The missing half is the TARGET side and the ABILITY
side.

This is the cycle 2 lesson landing one more time, from the other direction. Every
number cycle 2 published is correct. What nobody had done was ask whether the
correct numbers were the ones cycle 3 needs - "all five tables are populated" is
true and was quietly read as "cycle 3 has its inputs". A schema being satisfied
says nothing about a consumer being served.

`docs/BLOODFORGE.md`'s input table now carries a per-input STATUS column instead
of a bare source, and `ROADMAP.md` cycle 3 lists six named gaps instead of four,
with the consequence stated in both: **cycle 3 cannot open by writing combat
math.** It opens by settling those two inputs, because a TTK against an assumed
boss health is the `items.tier` fabrication with a larger blast radius.

**Cycle 3 opens** with verified inputs on disk (`items` 425, `recipes` 663,
`abilities` 54, `vbloods` 65, `blood_types` 13), six named gaps, and a spec
session ahead of any code. Per `ROADMAP.md` line 3 that spec is its own session.

## 2026-07-26 - Cycle 3 spike SPEC approved, and the repo went public

Branch `master`. Ledger 003a. Commits `c95c47f` (spec plus ROADMAP) and the docs
commit backfilled into the ledger entry. **No production code changed and none
was meant to** - this session was the spec, by explicit instruction.

State at close, observed in one run after the last edit: `python -m pytest`
**317 passed** (see the counting note below), `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0. No C# changed, so no `dotnet build` was
run.

**A counting note worth keeping, because the ritual asks for exact numbers.**
This repo's pytest config suppresses the textual summary line - `pytest -q`
prints only the progress block, and neither a pipeline capture nor a `>`
redirect produced a "N passed" line. Rather than report 317 from memory or from
eyeballing four rows of dots, the progress characters were counted directly:
**317 dots, 0 of `F/E/s/x`, exit 0.** If a future session needs the summary line
back, the cause is in the pytest config, not in the invocation.

**What shipped: `docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md`,
342 lines.** Cycle 3's first spec, and it deliberately contains no combat math.
`ROADMAP.md` cycle 3 now names TWO specs where it said one TBD: this spike, then
the math opened only against what the spike returns.

**Five decisions the operator made, each of which changes what gets built.**

1. **Scope is the spike alone**, with a declared consumer contract. Not a full
   engine spec with the spike as phase 0.
2. **The boss stat line reads from the PREFAB, with a live instance as a negative
   control.** Not prefab-only, not instance-only. The prefab keeps the dump
   repeatable; the instance is what makes a template-reading stub fail.
3. **Coefficients key on the ability GROUP, all 1474**, in a new `ability_stats`
   table - not by extending the 54 `abilities` rows. This is the load-bearing
   one: it DISSOLVES ROADMAP gap 3, because a weapon ability needs no
   `<Weapon>SpellSchoolAsset` to have coefficients, only a weapon-to-group link.
   ADR-007 will record it.
4. **A throwaway `/dump/components` endpoint runs FIRST**, printing full
   component lists, with an operator gate before any schema is written.
5. **The required-field contract includes the level/power-difference term**, not
   just health and coefficients.

**The thing this spec does that a normal spec does not: it encodes four cycle 2
lessons as structure rather than as advice.** Advice in a doc does not survive a
subagent; a numbered acceptance criterion does.

- Full component lists, never a guessed `HasComponent` - a false return is
  evidence only if the type name was right.
- MINIMUM SAMPLE COUNTS, written into the protocol: three bosses spanning level
  16 to 91, three ability groups across schools, two weapon families. The
  `blood_types` near miss came from sampling the first two rows, which happened
  to be the two unrepresentative ones.
- An expected-count assertion on every table, because `vbloods` 66 survived four
  per-row gates when every duplicate pair was byte-identical and the count was
  the only symptom.
- A stub-proof liveness assertion: the source entity must NOT carry
  `Unity.Entities.Prefab` and its entity index must differ from the prefab's.
  `StateReader.cs` compiled at 0 warnings and passed 284 tests while reading the
  PlayerCharacter template.

**The closure rule is the spec's spine.** All 14 required fields end as SOURCED
with component and field named, or PROVEN ABSENT in the `items.tier` pattern with
the negative control that makes the absence readable. NOT ATTEMPTED must be
empty. No field may be defaulted to `1.0`, `0` or a plausible guess.

**Self-review caught two real ambiguities, both fixed before commit.** The gates
section demanded an expected-count assertion on every table, but `ability_stats`
has no known count until the spike runs - so the rule now says the measured count
is PINNED as a constant in the same commit that lands the table, which makes the
assertion a drift detector rather than a rubber stamp. And `/dump/components` was
called "ungated" in the deliverables while section 3 gates it on
`GameDataInitialized`; readiness precondition and validation gate are now
distinguished.

**Housekeeping, on operator instruction.**

- **There was no stray worktree.** `git worktree list` showed only
  `C:/RedMoon [master]`. What existed was a stale BRANCH, `cycle-2-bridge`.
  Verified fully merged first - `git merge-base --is-ancestor` exit 0 and
  `git log master..cycle-2-bridge` empty - then deleted locally and on `origin`.
  Nothing was lost, and the verification is why that can be said.
- **`Remus3/RedMoon` is now PUBLIC.** Before flipping it, history was scanned:
  `API-Key-Claude.txt` has never been committed on any ref, and no path matching
  key/secret/token/pem/credential/password was ever ADDED in full history. The
  repo description was also a cycle behind - it said "Cycle 1: harness plus
  offline data floor" - and now names cycle 2 done and cycle 3 in progress.

**Cycle 3 remains OPEN.** The spec is approved; nothing is implemented. Next
session is phase 1: the exploratory endpoint and the component inventory, then
the operator gate.

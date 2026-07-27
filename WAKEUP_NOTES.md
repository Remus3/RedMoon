# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

**BACKUP.** Branch `backup-pre-trailer-rewrite` at the pre-rewrite tip
`92ca7f1`, plus `refs/original/refs/heads/master`. Delete both once the
rewritten history has been confirmed good, and note that deleting them is what
finally makes stale citations fail the anchor test.

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


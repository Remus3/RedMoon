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

## 003g - Three-project interop: the shared governor, port 8770, and a gate that read the wrong tree (2026-08-01)

Commits `b1b6b2d` (inbox out of the port scan), `6cfc614` (backlog plus memory
seed), `a3fa2f6` (phase 3 counts and ratios), `91b9ed2` (the gate fix),
`7d735da` (port 8770 and the shared governor), `370c019` (bucket held at 2) and
`<docs>` (this entry). **NO ROADMAP ITEM CLOSED.** Cycle 3 phase 2 still has not
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

# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

Branch `master`. Ledger 003b and 003c. Commits `ca2d539` (hooks) and `68f6d57`
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
unset. That is the whole explanation for last session's BOM in `2f14c4c`.

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

Branch `master`. Ledger 003a. Commits `774d7d3` (spec plus ROADMAP) and the docs
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

## 2026-07-26 - CYCLE 2 CLOSED, cycle 3 opened

ARCHIVED to `docs/history_notes.md`. Summary only: cycle 2 closed on the
operator's call with three weighed residue items, and the session found the two
cycle 3 blockers - there is no boss stat line and there are no ability
coefficients in the promoted tables.


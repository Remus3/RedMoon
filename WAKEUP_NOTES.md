# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

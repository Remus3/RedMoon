# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 phase 2: the schema'd dump. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/BRIDGE_SPIKES.md (the "Cycle 3 phase 1" section is the
whole input to this session) and
docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md section 4,
then git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING - it is a
sibling-project channel and the last session was driven entirely by it.

THE SPEC IS APPROVED AND THE PHASE 1 GATE IS PASSED. Do not re-litigate either
and do not re-run the brainstorming skill. Do not write combat math: that is a
SECOND spec, opened only after this one lands.

CONTEXT, do not re-derive or re-verify:

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above rather than from a hash written here.
- Last verified, one run: pytest 348 passed in 20.15s exit 0, ruff clean,
  ascii_guard exit 0. dotnet build -c Release -t:Rebuild on
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj was last green at 335 tests
  and has NOT been re-run since; there is NO .sln - build the csproj.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. hooks/commit-msg strips it and warns, but it is a
  backstop, not a licence: it cannot fire under --no-verify or on a rebase
  replaying old messages. A human co-author is fine.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log, never from an old doc.
- Never write a port literal - import from core/ports.py. That file is FROZEN.
- data/rmdata/ is gitignored and regenerable: items 425 (schema 3), recipes 663
  (schema 2), abilities 54, vbloods 65, blood_types 13. Do not rebuild it.
- DO NOT run git lfs install. filter.lfs.required=true is set and core.hooksPath
  makes git ignore anything LFS writes to .git/hooks, so the first LFS-tracked
  file would arrive with an inert pre-push.

WHAT LANDED 2026-08-01 THAT CHANGES YOUR GROUND TRUTH.

- RED MOON IS NO LONGER FULLY STANDALONE. It shares exactly ONE file of code and
  ONE directory of data with two sibling projects: ops/loop/slots.py, the
  machine-wide slot governor, vendored BYTE-IDENTICAL and pinned by SHA256
  95077a62 in tests/test_slots.py. DO NOT EDIT IT. The digest is the contract
  and re-syncing is a three-repo act performed in one day. Rationale in
  ops/loop/__init__.py. Still no shared keys, ports or task namespace.
  MAX_CONCURRENT_SLOTS = 2, and all three projects must carry the SAME number.
  Nothing in RM calls the governor yet.
- PORT 8770 = CONTROL, the headless control plane, on the FLOOR of RM's block.
  RM reserves 8770-8789 and the block reads as two regions: 8770-8776
  infrastructure, 8777 and up game services. ADR-003 carries the reservation.
  Only 8777 and 8780 actually BIND today - never read a live port scan as
  evidence the others are free.
- tools/precommit_gate.py was FIXED and is frozen. It now matches only real git
  commit invocations (not the quoted phrase) and gates THE TREE THE COMMIT
  TARGETS rather than a hardcoded main tree. If you touch it, know that
  shlex.split(posix=True) eats backslashes and silently reintroduces the
  main-tree bug on any Windows path.
- moon_sync_inbox/ is gitignored AND excluded from the port scan. Siblings may
  quote their own ports there in any file type.

THE HEADLESS TRACK IS A SEPARATE, BLOCKED TRACK. Do not start it inside this
session and do not fold it into Bloodforge. A sibling delivered a 12-section
plan (moon_sync_inbox/2026-08-01-0815-from-RC-headless-plan.md). Its phase 0 is
INCONCLUSIVE, not passed: claude -p --permission-mode bypassPermissions exits 1
here because headless is NOT AUTHENTICATED and C:\RedMoon is NOT A TRUSTED
WORKSPACE, which discards all 13 permissions.allow entries. The claim that
PreToolUse hooks die headless is UNREPRODUCED on this machine - do not cite it
as confirmed. The next action on that track is two preflight checks, not code.

WHAT PHASE 1 ESTABLISHED, which is what you build against.

- T1 ProjectM.Health.MaxHealth (ModifiableFloat).
- T2 ProjectM.UnitStats.PhysicalResistance, .SpellResistance, .FireResistance,
  .CorruptionDamageReduction. Holy, Silver and Garlic have NO unit-side field
  across 150 enumerated components. ProjectM.ResistanceData is a GLOBAL
  per-rating coefficient block, NOT a per-boss vector.
- T3 ProjectM.UnitLevel.Level. T4 and P2 candidates: UnitLevel.Level,
  UnitStats.PhysicalPower / .SpellPower, WeaponLevelSource on the item,
  WeaponLevel on the equip buff.
- A1 ProjectM.AbilityCastTimeData.MaxCastTime and .PostCastTime, on _Cast.
- A2 ProjectM.AbilityCooldownData.Cooldown plus ProjectM.GlobalCooldown.Value.
- A3 ProjectM.DealDamageParameters.MainFactor, .RawDamageValue,
  .RawDamagePercent, on the _Hit entity's DealDamageOnGameplayEvent buffer.
- A4 .MainType. A5 PROVEN ABSENT as a field. A6 PARTIAL:
  DealDamageOnGameplayEvent.DamageModifierPerHit and
  .MultiplyMainFactorWithStacks exist; the multiplicity itself is buffer LENGTHS
  (HitTrigger, CreateGameplayEventsOnHit, AbilitySpawnPrefabOnCast) and COUNTING
  THEM IS A PHASE 2 JOB.
- L1 CLOSED: item -> ProjectM.EquippableData.BuffGuid ->
  EquipBuff_Weapon_<Family>_Base -> DynamicBuffer<ProjectM.ReplaceAbilityOnSlotBuff>
  -> element .NewGroupId is the ability GROUP and .Slot is the bar slot.
- L2: cycle 2's chain, AbilityGroupStartAbilitiesBuffer -> _Cast ->
  AbilitySpawnPrefabOnCast, 1474 of 1474, one hop only.
- ProjectM.WeaponAbilityData on a group means WEAPON ability;
  ProjectM.VBloodAbilityData and ProjectM.AbilitySpellSchool mean spell.

DO NOT BUILD A GENERIC VALUE READER. It was attempted twice and both attempts
are recorded as failures in docs/BRIDGE_SPIKES.md.
EntityManagerDebug.GetComponentBoxed returns an object NOT backed by real chunk
memory on this build: managed reflection read 539327184 for every Int32 and
1.402156E-19 for every Single, and raw il2cpp field offsets off that pointer HARD
CRASHED the dedicated server, as did the raw il2cpp_class_get_fields iterator.
Read values with TYPED accessors, the way PrefabDumper.cs already does. The
inventory tells you which type to spell.

CARRY THE CONTROL FORWARD. Every entity carries Stunlock.Core.PrefabGUID whose
value the response already states from a typed read. Any new reader must restate
a quantity that is already known, or its numbers are unfalsifiable. That control
is the only reason phase 1 did not publish fiction.

WHAT PHASE 2 IS, per spec section 4.

1. vbloods to schema_version 2: max health, a resistance map keyed by damage
   type, and the target-side diff-term field. New dataclass fields APPEND AT THE
   END with a default (CLAUDE.md Python convention).
2. ability_stats, new, schema_version 1, keyed on ability-GROUP guid: cast time,
   cooldown, coefficient, power stat, hits per cast, damage type. abilities stays
   the identity and school table and joins on prefab_guid.
3. items to schema_version 4: an ability_group_guids ARRAY, copying ADR-006's
   station_guids shape exactly - plural, and an empty list ships as [] so "grants
   no ability" stays distinguishable from "the join did not run".
4. Gates: shallow schema in core/tables.py, nested contract in
   core/table_deep.py, duplicate_key_problems on ability_stats, and AN EXPLICIT
   EXPECTED-COUNT ASSERTION ON EVERY TABLE. ability_stats has no known count
   until it runs, so PIN the measured count as a constant in the same commit that
   lands the table, together with the chain that produced it. A count that is
   merely whatever the dumper emitted is not an assertion.
5. ADR-007: the coefficient key space is the ability GROUP, not the ability and
   not the school.
6. Phase 3, in the same session if it fits: the prefab-versus-instance control.
   You have a real subject on both sides - instanced CHAR_Vampire_Dracula_VBlood
   is entity 322916 with no Unity.Entities.Prefab, the prefab is 29012 with it,
   and every stat-bearing component is on BOTH. So this is a VALUE comparison,
   not a presence check. Name which of the three branches happened, in writing:
   they agree, they differ by a factor (that factor is spawn scaling and must be
   sourced before any TTK is published), or the prefab carries nothing.

   COUNT, DO NOT JUST CLASSIFY. A branch name alone is a PRESENCE-shaped answer
   to a VALUE-shaped question and cannot be checked by the next reader. Report,
   per component: HOW MANY fields were compared, HOW MANY differ, and FOR EACH
   DIFFERING FIELD the ratio instance/prefab. "They differ" proves nothing.
   "9 of 14 fields differ, 8 of them by exactly 2.0x and MaxHealth by 3.5x"
   names spawn scaling and is falsifiable by anyone who re-runs it. If the
   branch is "they agree", say how many fields were compared to reach that.

ABSENT STAYS ABSENT. A proven-absent field is DECLARED and OMITTED, never zero.
Do not default anything to 1.0, 0 or a plausible guess. Holy, Silver and Garlic
resistance are absent from the unit - do not write zeroes for them.

NO BACKFILL PASS IS OWED. data/rmdata/ is gitignored and fully regenerable from
one dump, so re-promoting IS the recovery.

TDD per CLAUDE.md: failing characterization tests before the dumper changes,
including the guard-order regression - the dedupe Add must sit AFTER the marker
component test, because && short-circuits left to right and an Add placed first
claims the guid on behalf of every entity carrying it and then rejects the real
row when it arrives.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. There is no .sln.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. A stale
  flat plugins\RedMoon.Bridge.dll beside
  plugins\RedMoon.Bridge\RedMoon.Bridge.dll cost a debug cycle: BepInEx loaded
  both, the stale one bound the port, served /health perfectly and returned
  not_found for the endpoint that had just been built.
- Launch: VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver
  -saveName world1 -batchMode -nographics. Poll http://127.0.0.1:8780/health for
  "ready":true, about 15 s. If it dies immediately after a taskkill /F, wait a
  few seconds and launch again - that works every time and is not investigated.
- Never Stop-Process; taskkill /F through PowerShell.
- Your PowerShell tool is pwsh 7.6.4 Core, NOT 5.1, so &&, ||, ternary and ??
  work directly. This does NOT relax the 7-bit-ASCII rule.
- Output to _scratch\rmprobe as saved JSON, not committed. Never read a number
  off a screenshot.

ACCEPTANCE, spec section 5. The spike closes only when all six hold: every field
SOURCED or PROVEN ABSENT with NOT ATTEMPTED empty; the component inventories
recorded (DONE in phase 1); the prefab-versus-instance control run with one
branch named in writing AND a per-component count of fields compared, fields
differing, and the ratio for each differing field; tables promoted with counts
asserted (vbloods 65, items 425, ability_stats at its measured count together
with the chain that produced it); pytest, ruff, ascii_guard and dotnet build all
green and RE-RUN by the closing agent rather than taken from a report; ADR-007
written, docs/BLOODFORGE.md's input table rewritten from the measurement, and
ROADMAP cycle 3 gaps 1, 2 and 3 each closed or restated with evidence.

KNOW WHAT ACCEPTANCE DOES NOT COVER, so you do not mistake a green spike for a
correct engine. All six criteria are about SOURCING INPUTS. None asks whether
the math over those inputs is right, so all six can pass with a confidently
wrong time-to-kill. Red Moon has NO ground-truth anchor for computed DPS, EHP or
TTK - now ROADMAP cycle 3 gap 7 and a BACKLOG item. It does not block this
phase. It DOES have to be settled before the combat-math spec opens. Do not
publish a TTK to any surface in this session.

Launch build work via subagents per CLAUDE.md, but note that a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself. If you fan out,
CHECK THE FAN-OUT'S OWN COVERAGE before believing its conclusions: last session
a challenge pass silently truncated its input and left 33 of 119 items
unreviewed, and every apparent survivor was an artifact of that gap.

End with /done, and print the next-session prompt inline.
```

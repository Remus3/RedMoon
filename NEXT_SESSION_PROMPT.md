# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 phase 2: the schema'd dump. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/BRIDGE_SPIKES.md (the "Cycle 3 phase 1" section is the
whole input to this session) and
docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md section 4,
then git log --oneline -6.

THE SPEC IS APPROVED AND THE PHASE 1 GATE IS PASSED. Do not re-litigate either
and do not re-run the brainstorming skill. Do not write combat math: that is a
SECOND spec, opened only after this one lands.

CONTEXT, do not re-derive or re-verify:

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above rather than from a hash written here.
- Last verified: pytest 324 passed, ruff clean, ascii_guard exit 0, dotnet build
  -c Release -t:Rebuild on bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj exit 0
  with 0 warnings. There is NO .sln - build the csproj.
- The precommit gate is now WIRED: committed hooks/ plus core.hooksPath, proven
  to refuse a real BOM commit. A bad commit is blocked structurally now, not by
  a shell chain.
- data/rmdata/ is gitignored and regenerable: items 425 (schema 3), recipes 663
  (schema 2), abilities 54, vbloods 65, blood_types 13. Do not rebuild it.
- Never write a port literal - import from core/ports.py.

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

ABSENT STAYS ABSENT. A proven-absent field is DECLARED and OMITTED, never zero.
Do not default anything to 1.0, 0 or a plausible guess. Holy, Silver and Garlic
resistance are absent from the unit - do not write zeroes for them.

NO BACKFILL PASS IS OWED. data/rmdata/ is gitignored and fully regenerable from
one dump, so re-promoting IS the recovery. The spec records this exemption so it
is not mistaken for an oversight.

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
- Output to _scratch\rmprobe as saved JSON, not committed. Never read a number
  off a screenshot.

ACCEPTANCE, spec section 5. The spike closes only when all six hold: every field
SOURCED or PROVEN ABSENT with NOT ATTEMPTED empty; the component inventories
recorded (DONE in phase 1); the prefab-versus-instance control run with one
branch named in writing; tables promoted with counts asserted (vbloods 65, items
425, ability_stats at its measured count together with the chain that produced
it); pytest, ruff, ascii_guard and dotnet build all green and RE-RUN by the
closing agent rather than taken from a report; ADR-007 written,
docs/BLOODFORGE.md's input table rewritten from the measurement, and ROADMAP
cycle 3 gaps 1, 2 and 3 each closed or restated with evidence.

Launch build work via subagents per CLAUDE.md, but note that a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself.

End with /done, and print the next-session prompt inline.
```

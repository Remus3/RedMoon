# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3 phase 1: the Bloodforge input spike, exploratory pass only. Read
CLAUDE.md, MEMORY.md, ROADMAP.md, WAKEUP_NOTES.md,
docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md and
docs/BRIDGE_SPIKES.md, then git log --oneline -10.

THE SPEC IS APPROVED. Do not re-litigate it and do not re-run the brainstorming
skill. Implement phase 1 only, then STOP at the operator gate. Writing any
schema, any table or any combat math this session violates the spec.

CONTEXT (do not re-derive, do not re-verify):
- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree (C:/RedMoon),
  no stray branches. github.com/Remus3/RedMoon is PUBLIC as of 2026-07-26.
- Last verified: pytest 317 passed, ruff clean, ascii_guard exit 0. NOTE this
  repo's pytest config suppresses the "N passed" summary line - count progress
  characters instead of reporting a number you did not see.
- Cycle 2 is CLOSED. All five tables are on disk under
  data/rmdata/1.1.13.0-r99712/tables/: items 425 (schema 3), recipes 663
  (schema 2), abilities 54, vbloods 65, blood_types 13. data/rmdata/ is
  gitignored and regenerable. Do not rebuild it.
- Never write a port literal - import from core/ports.py.

WHAT PHASE 1 IS. One throwaway endpoint and one document. Nothing else.

1. GET /dump/components in bridge/src/RedMoon.Bridge/, taking either guid, or
   name as a prefix plus limit, plus instanced=1 to scan spawned entities rather
   than prefabs. For every matched entity print: entity index, prefab_guid,
   prefab name, the COMPLETE component-type list by full type name, and every
   readable field of each blittable component with its type and value.
   Exploratory: no schema, no ingest gates, never promoted. It DOES wait on the
   GameDataInitialized readiness gate. Instanced scans skip
   Unity.Entities.Prefab.
2. The component inventory for all four subject classes, written into
   docs/BRIDGE_SPIKES.md with every component and field NAMED.

THE ONE HARD RULE. Never call HasComponent on a name you hoped for. Enumerate
the entity's actual component types and print all of them. A HasComponent that
returns false is evidence only when the type name was right, and at this stage
you have no way to know that.

MINIMUM SAMPLES, fixed by the spec, not negotiable. Cycle 2's blood_types near
miss came from sampling the first two rows, which were BloodType_VBlood and
BloodType_GateBoss - both unrepresentative, and the result read as a family-wide
absence.
- at least three CHAR_*_VBlood prefabs spanning the level range: near 16, mid,
  and near 91
- at least three ability groups across different schools, plus at least one
  WEAPON ability group
- at least one LIVE INSTANCED boss entity
- at least two weapon items from different weapon families, for the L1 hop

WHAT YOU ARE HUNTING, the 14 required fields from spec section 2. Report each as
SOURCED with component and field named, PROVEN ABSENT, or NOT ATTEMPTED:
T1 boss max health, T2 boss resistance per damage type (Physical, Spell, Fire,
Holy, Silver, Garlic, Corruption), T3 boss unit level (HAVE - ProjectM.UnitLevel
.Level, 16 to 91), T4 target-side input to the level/power-difference term,
A1 cast time, A2 cooldown, A3 damage coefficient, A4 damage type (PARTIAL, 16 of
54), A5 which power stat the ability scales off, A6 hits per cast, P1
PhysicalPower/SpellPower (HAVE, 203 of 205), P2 player-side input to the diff
term, L1 weapon item to ability group, L2 ability group to coefficients.

THE L1 ASYMMETRY, stated so you do not trip over it. EquippableData.BuffGuid is
BARRED as a route to item STATS - items.stats is a one-hop read off the item
prefab and cycle 2 settled that. For ABILITIES the equip buff is the CORRECT
hop. The rule is field-specific, not blanket.

USEFUL CYCLE 2 MEASUREMENTS. The chain
AbilityGroupStartAbilitiesBuffer -> _Cast -> AbilitySpawnPrefabOnCast resolves a
cast for 1474 of 1474 ability groups; a second spawn hop adds exactly 0, so one
hop is the answer and the 912 groups that never reach damage genuinely do not.
The ability school is DynamicBuffer<ProjectM.SpellSchoolAbility> on the
<School>SpellSchoolAsset prefab, NOT DealDamageParameters.MainType, which is the
DAMAGE type. Client and server component data are IDENTICAL (zero differing
rows, five tables, diffed on prefab_guid), so either host may serve a dump.

OPERATIONS:
- Launch the dedicated server yourself: VRisingServer.exe -persistentDataPath
  C:\RedMoon\_scratch\vrserver -saveName world1 -batchMode -nographics. Bridge
  answers http://127.0.0.1:8780/health and /dump/prefabs; poll for "ready":true
  before dumping (about 9 s).
- Try world1 on the dedicated server for the LIVE INSTANCED boss first. Only if
  that produces no instanced boss, ASK the operator to launch the CLIENT (which
  binds 8777). Do not attempt to launch the client yourself.
- Never Stop-Process; taskkill /F via PowerShell (Git Bash mangles /F).
- Output goes to _scratch\rmprobe as saved JSON, not committed. Never read a
  number off a screenshot.

STOP AT THE GATE. When the component inventory is written, STOP and hand it to
the operator for review. Phase 2 - the vbloods schema 2 bump, ability_stats,
items schema 4, the ingest gates and ADR-007 - does not start until real type
and field names are on paper and approved. If a required field looks absent, say
which of the three states it is in and what negative control makes that
readable; do not default it to 1.0, 0 or a plausible guess.

Launch build work via subagents per CLAUDE.md, but note that a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself.

End with /done, and print the next-session prompt inline.
```

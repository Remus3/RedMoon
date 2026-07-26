# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Open Red Moon cycle 3, Bloodforge core. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/BLOODFORGE.md and docs/ARCHITECTURE.md, then
git log --oneline -10.

THIS SESSION WRITES THE SPEC, NOT CODE. Cycle 3 has two unsourced inputs (below)
and writing combat math before they are settled would fabricate the engine's
headline number. Start with the brainstorming skill, emit the spec to
docs/superpowers/specs/, and get operator approval before any implementation.

CONTEXT (do not re-derive, do not re-verify):
- Repo C:\RedMoon, branch master, clean and pushed, no worktrees.
- Last verified: pytest 317 passed, ruff clean, ascii_guard exit 0, and on
  bridge/src/RedMoon.Bridge dotnet build -c Release -t:Rebuild exit 0 / 0
  warnings.
- CYCLE 2 IS CLOSED (ledger 002g). The bridge ships, loads in BOTH hosts, and
  all five tables are populated on disk under
  data/rmdata/1.1.13.0-r99712/tables/:
    items 425 (schema 3), recipes 663 (schema 2), abilities 54 (schema 1),
    vbloods 65 (schema 1), blood_types 13 (schema 2).
  data/rmdata/ is gitignored and regenerable from a dump. Do not rebuild it.
- Cycle 3 targets: engine on port 8783, ENGINE_VERSION pinned to 1.1.13.0-r99712.
  Never write a port literal - import from core/ports.py.

THE TWO BLOCKERS, found at cycle 2 close by reading the promoted ROWS rather
than the schema. These are the session's real subject:

1. THERE IS NO BOSS STAT LINE. vbloods rows carry exactly level, name and
   prefab_guid. No health, no resistances, no damage. docs/BLOODFORGE.md had
   named tables/vbloods.json as the source for "Boss stat line and resistances"
   since cycle 1; that line was never checked against real rows and is false.
   It is now annotated. Time-to-kill is the engine's headline output and its
   denominator is not on disk.
2. THERE ARE NO ABILITY COEFFICIENTS. abilities rows carry name, prefab_guid,
   school and, for 16 of 54, damage_type. No cast time, no cooldown, no damage
   scalar. Spell DPS cannot be computed from this table as it stands.

Both almost certainly need another measured bridge pass. Treat that as a cycle 3
SPIKE with the same discipline cycle 2 used: print full component lists rather
than probing a guessed component name, because a HasComponent that returns false
is only evidence when the type name was right.

THE PLAYER SIDE IS FINE and is not a gap - checked in the same pass. 203 of 205
weapon items carry real PhysicalPower or SpellPower values, 29 distinct stat
types, an explicit modification (Add / AddToBase / MultiplyBaseAdd) on every
entry. Sample: Item_Weapon_Claws_T06_Iron_Reinforced, PhysicalPower 17.302807
AddToBase, ResourcePower 16 Add.

FOUR SMALLER GAPS, all named in ROADMAP.md cycle 3:
- Weapon abilities produce NO abilities row - there is no <Weapon>SpellSchoolAsset
  to source a school from. Weapon DPS cannot be scaffolded on that table.
- items.tier is ABSENT, not zero. No per-item source exists on this build (67
  Tier-shaped fields across 169 assemblies, zero per item; Rarity zero hits
  anywhere). Do not try to source it again and never parse the _T0x name token.
- items.gear_score is present on only 117 of 425 rows and is a Red Moon-COMPUTED
  quantity over three separate level systems, not a direct read.
- blood_types carries stat NAMES and no magnitudes; every value is scaled from
  blood quality at runtime.

CLOSED BY MEASUREMENT, do not re-open: all six spikes S1 to S6 plus S3a and S7;
R2, R11, R17 (including Unity.Transforms). Client and server component data are
IDENTICAL (zero differing rows, five tables, diffed on prefab_guid) so either
host may serve a dump. localization resolves 425/425 on the CLIENT and 0/425 on
the dedicated server - that is a HOST fact, not a build fact. station_guids per
ADR-006 (911 pairs, 19 recipes at 12 stations). vbloods is 65, not 66.
Unload() does NOT run - BepInEx 6 IL2CPP never calls it; the port is released by
process death. items.stats is a ONE-HOP read off the item prefab - never follow
EquippableData.BuffGuid for stats. GameDataInitialized is the readiness gate.
Skip Unity.Entities.Prefab when scanning for instanced entities.

OPERATIONS:
- Launch the dedicated server yourself: VRisingServer.exe -persistentDataPath
  C:\RedMoon\_scratch\vrserver -saveName world1 -batchMode -nographics. Bridge
  answers http://127.0.0.1:8780/health and /dump/prefabs; poll for "ready":true
  before dumping (about 9 s).
- The CLIENT needs the operator to launch it and load a world. Ask, do not
  attempt it yourself unless told to drive it. The client binds 8777.
- Never Stop-Process; taskkill /F via PowerShell (Git Bash mangles /F).
- _scratch\rmprobe, _scratch\typedump, _scratch\bridge-build are scratch,
  regenerable, NOT committed.

THE LESSONS CYCLE 2 PAID FOR, in the order they cost the most:
1. A real measurement can answer the RIGHT question about the WRONG SUBJECT.
   "0 of 425" was correct, reproducible and had a proper negative control, and it
   described a headless host rather than the game. Before generalizing, check
   what the measurement was taken OF.
2. A green suite and a clean build prove NOTHING for a live-data reader.
   StateReader.cs compiled at 0 warnings, passed 284 tests, and returned full
   vitals while reading the PlayerCharacter PREFAB TEMPLATE. Only a liveness
   probe a stub cannot pass caught it.
3. A zero that three hypotheses predict equally is not evidence. That shape
   appeared three times: items.tier, ShadowVBloodUnitTagComponent, and Unload().
4. Per-row gates cannot see a wrong COUNT. vbloods 66 survived four gates
   because every duplicate pair was byte-identical.
5. Writing a memory entry is a repo-affecting act here - it must be seeded into
   docs/memory_seed/ in the same commit or three tests fail.

Launch build work via subagents per CLAUDE.md, but note that a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself.

End with /done, and print the next-session prompt inline.
```

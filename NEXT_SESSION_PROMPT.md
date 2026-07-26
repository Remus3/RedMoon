# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Continue Red Moon cycle 2. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/ARCHITECTURE.md and docs/BRIDGE_SPIKES.md, then
git log --oneline -10.

CONTEXT (do not re-derive, do not re-verify):
- Repo C:\RedMoon. Work on master. Cycle 2 code is ON master - the branch
  cycle-2-bridge was fast-forwarded in at 6acbc66 and master now carries
  everything. cycle-2-bridge still exists as a safety net; do not work on it.
  There are NO worktrees. Ledger 002d carries this session's detail.
- Last verified state: python -m pytest 284 passed, ruff clean, ascii_guard
  exit 0, dotnet build -c Release exit 0 / 0 warnings.
- The plugin runs live in BOTH hosts. items.json has 425 rows at
  schema_version 3, recipes.json 663. Do not rebuild these.
- /state WORKS. bridge_probe --motion-diff --expect-host client PASSES.
- CLOSED by measurement, do not re-open: R17 (now including Unity.Transforms),
  R2, R11, S1 all parts including S1(b), S2, S3a, S4, S5, S6, S7. Prefab total
  is 23583 server / 30484 client. GameDataInitialized is the readiness gate.
  items.stats is ONE HOP - never follow EquippableData.BuffGuid for stats.
  Ability school is DealDamageParameters.MainType on the _Hit entity.
  items.tier has NO source on this build and is correctly omitted - do not
  try to source it again, and never parse the _T0x name token.

THE ONE LESSON FROM LAST SESSION, apply it to everything below:
A green suite and a clean build proved NOTHING. StateReader.cs compiled at 0
warnings, passed all 284 tests, and returned state_reason:ok with full vitals
while reading the PlayerCharacter PREFAB TEMPLATE - position 0,0,0, health
125/125, on a server with nobody connected. Only --motion-diff caught it,
because two samples five seconds apart were byte-identical. Every live-data
reader you write needs a liveness probe that a stub cannot pass. Skip
Unity.Entities.Prefab when scanning for instanced entities.

OPERATIONS:
- Launch the server yourself: VRisingServer.exe -persistentDataPath
  C:\RedMoon\_scratch\vrserver -saveName world1 -batchMode -nographics.
  Bridge answers http://127.0.0.1:8780/health and /dump/prefabs. Poll for
  "ready":true before dumping (about 9 s).
- The CLIENT plugins dir now holds the real bridge, NOT the probe (RmProbe.dll
  was removed; both bind 8777 and cannot coexist). The client needs the
  operator to launch it and load Solo Only - ask, do not attempt it yourself
  unless the operator says to drive it.
- Never Stop-Process; taskkill /F via PowerShell (Git Bash mangles /F).
- data/rmdata/ is gitignored. The tables are regenerable from a dump.
- _scratch\rmprobe, _scratch\typedump, _scratch\bridge-build are scratch,
  regenerable, NOT committed.

DO IN THIS ORDER:
1. abilities. The school is found but the ability-group-to-_Hit join is NOT
   traced, so no row can be assembled end to end. Trace it - it is a name or
   reference join question, not another school hunt. Census counts: AB_ 8308,
   split Cast 1551, AbilityGroup 1476, Buff 456, Hit 359, Projectile 289.
2. recipes.station_guid. OPEN because the station references the recipe, not
   the reverse. Find the reverse index or record that it must be inverted at
   ingest time.
3. localization_guid. The runtime route is verified in metadata but NOT run:
   GameDataSystem.ManagedDataRegistry -> TryGet<ManagedItemData>(PrefabGUID)
   -> .Name.Key.ToGuid().ToString(). Two things are INFERRED and must be
   measured: that ManagedItemData is registered for all 425 equippables, and
   that Localization is initialized on a server host.
4. blood_types. Buffer element fields of PrimaryUnitBloodTypeBuffs and
   SecondaryUnitBloodTypeBuffs are unread.
5. vbloods. VBloodConsumeSource.Tier is the level candidate, metadata-read
   only - measure its VALUES. Markers are VBloodUnit, VBloodConsumeSource,
   VBloodAbilityBuffEntry, VBloodUnlockTechBuffer.
6. Smaller: does client item COMPONENT data match the server's (only the
   prefab MAPS were compared - diff two real dumps); Unload()'s graceful path;
   the 4 unmapped recipes, confirmed "empty item output buffer" and consistent
   with RecipeOutputUnitBuffer but not proven to be it.

Launch build work via subagents, but note: a worktree-isolated agent wrote into
the MAIN tree twice now and git worktree list never showed a second tree. Do not
commit while an agent is live, and read git show --stat after. Re-run any agent's
claimed test counts and builds yourself before believing them.

End with /done, and print the next-session prompt inline.
```

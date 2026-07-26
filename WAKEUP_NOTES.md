# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-07-26 - Cycle 2 part 4: /state goes live, two fabricated fields retired, S1(b) closed

Branch `master` (see the branch note below), commit `2bc26d5`. Ledger 002d.

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

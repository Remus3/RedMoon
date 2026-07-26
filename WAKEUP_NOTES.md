# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-07-26 - Cycle 2 part 2: the probe plugin, and seven spikes closed by running it

Branch `cycle-2-bridge`, three commits on top of `5933cfe`. Cycle 2 is still NOT
done. Ledger entry 002b carries the detail.

State at close, every number observed in one run after the last edit:
`python -m pytest` 245 passed, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0.

The artifact is `_scratch\rmprobe\`, a MINIMAL enumerate-and-log BepInEx plugin
built and deployed to both hosts BEFORE any bridge code. It is scratch and not
committed, same rule as `_scratch\typedump\`. It compiles the same generated
`RmPorts.g.cs` the real plugin will, so the no-port-literal rule holds even in
scratch, and it reads ECS only from `Update()` while its listener thread serves a
constant, so it tests both halves of D7 without violating D7.

Closed by measurement, not by reading:

- **R17.** The client generated its own interop tree: 172 files, 169 dll,
  matching the server exactly. That also explains the earlier "169 assemblies" -
  it was the dll count, so no correction was needed. Assembly NAME sets are
  identical. All 169 hashes differ, which is NOT a divergence signal because
  Il2CppInterop codegen is non-deterministic; a hash diff would report 100
  percent divergence between any two generations. The type-level diff is the one
  that decides the `.csproj`, and `ProjectM.Shared`, `Stunlock.Core`,
  `Unity.Entities` and `ProjectM.Gameplay.Systems` have ZERO real divergence.
- **S4 fully, R2 retired.** The build works with the whole reference set, not
  just the bare target framework. One non-obvious reference:
  `Paths.BepInExVersion` returns a `SemanticVersioning.Version`.
- **S1(a)** `World.All`. **S1(d)** `BepInEx.Paths.ProcessName`, `VRising` vs
  `VRisingServer`.
- **S1(c)** the server's target world is named `Server`, 710 systems, and world
  selection MUST be by name: `Default World` is also a Simulation world, sits at
  index 0, and throws when asked for the prefab map.
- **S2** an Il2Cpp-injected `MonoBehaviour` `Update` reaches main thread 1 in
  both hosts. No Harmony patch needed.
- **S5 and R11** `HttpListener` binds and serves in both hosts CONCURRENTLY,
  which is the ADR-005 payoff observed rather than argued, and after
  `taskkill /F` the port holds no LISTEN and `--expect-unreachable` passes.
- **S6 partial** prefab map `Count` 1189 in under a millisecond.
- **S3** items and recipes are mapped. The headline: `EquippableData` carries NO
  stats, only a `BuffGuid`, so `items.stats` is a two-hop read through the buff
  prefab's `DynamicBuffer<ModifyUnitStatBuff_DOTS>`.

One finding that is a real defect rather than a spike result. The suite had a
test whose comment read "nothing is listening on the bridge ports during the
suite" and which relied on it. The probe bound the client port, the connection
succeeded, and the test failed with no defect in the code under test. That is the
mirror image of cycle 1's gate-that-cannot-fail: a gate that fails for reasons
unrelated to its assertion. Fixed by pointing `RM_GAME_HOST` at `192.0.2.1`
(RFC 5737 TEST-NET-1). Proof it is real: 245 passed with the probe still bound
and answering curl.

Three things the next session must not get wrong:

1. **A client-side dump is UNPROVEN.** At the main menu the client has TWO worlds
   and NO prefab-carrying world at all. S1(b) has only the menu sample. The
   in-game client world set needs a character loaded and was not measured - the
   operator chose to wrap instead. Do not write down that the client can serve a
   dump.
2. The rest of S3 - ability school, V Blood level, blood bonus tiers - is gated
   behind the SAME in-game sample, not behind more metadata reading. There is no
   `SpellSchool` component type; the school-shaped types found are
   `SpellSchoolAuthoring`, `SchoolDebuffData` and
   `SpellSchoolTierProgressionPoints`, none obviously the per-ability field.
3. `items.stats` as a flat name-to-number map is expected to need a schema
   amendment, because it cannot carry `ModificationType`. Decide that at the
   first-dump review, from the census, not before.

Operator request logged, not started: automated V Rising launch plus OBS capture.
Filed in `BACKLOG.md` and scoped to cycle 8 - it is an ops concern and was
deliberately kept out of the middle of the spike chain.

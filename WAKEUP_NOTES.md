# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

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

## 2026-07-26 - Cycle 2 part 1: ADR-005, the Python half, spikes S4 and S3a closed

Branch `cycle-2-bridge`, two commits (`9fbce0c`, `251803b`). Cycle 2 is NOT
done and is not claimed to be. Ledger entry 002a carries the detail.

The two things the last session said must be settled BEFORE code are settled:

1. Port arbitration. RULED: mint the fifth port. Client binds 8777, dedicated
   server binds 8780, chosen by `core.ports.bridge_port_for_host`. ADR-005
   amends ADR-003. The stand-down path, install step 6b, acceptance criterion 5b
   and risk R15 are STRUCK from the spec - do not implement them. Operator
   approved the frozen `core/ports.py` edit and the ADR amendment before it was
   made.
2. `PrefabCollectionSystem`. CONFIRMED, not corrected:
   `ProjectM.PrefabCollectionSystem` in `ProjectM.Shared.dll`, deriving from
   `Stunlock.Core.PrefabCollectionSystem_Base`. The label carried from
   `ROADMAP.md` survives contact with the build.

State at close, every number observed in one run after the last edit:
`python -m pytest` 241 passed (was 106), `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0.

Shipped: `gen_bridge_ports.py`, `core/bridge_client.py`, `core/table_deep.py`,
`install_bepinex.py`, `rmdata_ingest.py`, `bridge_probe.py`,
`Directory.Build.props`, ADR-005, `docs/BRIDGE_SPIKES.md`.

Environment, done and verified live: BepInEx 1.733.2 installed into BOTH hosts
(233 files each, Thunderstore metadata dropped, `v3\` untouched). The dedicated
server launched once and generated 169 Il2CppInterop assemblies. Both v3
negative controls refuse.

Spike status. S4 CLOSED by measurement: a net6.0 library builds under SDK
10.0.301 with NO targeting pack and NO `global.json` - neither fallback is
needed. S3a CLOSED. S3 PARTIAL - the component types are located and named
(`EquippableData`, `RecipeData`, `RecipeRequirementBuffer`, `SpellLevel`,
`BloodQualityBuff`), the field mapping is not done. S1, S2, S5, S6 OPEN.

One process incident, and the plugin contract that fell out of it. `251803b` was
committed while a build agent was still live and captured its file mid-mutation
test, so that ONE commit carries a disabled v3 guard in `bridge_probe.py`.
Correct at `d614a09` and at HEAD; verified with `git show`, not taken on the
agent's word; no history rewrite. Standing rule, re-paid: do not commit while
agents live, and read `git show --stat` afterwards.

That agent's mutation testing also found a hole worth knowing about: a mutation
letting the loader-log banner matcher accept ANY line containing
`RedMoon.Bridge` SURVIVED 25 tests, because the negative fixture had no banner
token at all. That is cycle 1's failure mode a second time - a gate that cannot
fail. It is now pinned. CONSEQUENCE: `Plugin.cs` must emit a banner carrying
version, host AND port, shaped `RedMoon.Bridge v<semver> host=<client|server>
port=<n>`. The probe requires all three tokens.

Three things the next session must not get wrong:

1. The CLIENT has BepInEx but has NOT been launched, so it has no `interop\`
   tree yet. The R17 interop diff cannot run and no `.csproj` reference set may
   be pinned until it does. Launching the game client was left to the operator
   deliberately rather than done unattended.
2. S1 parts b, c and d are NOT answerable from static metadata. `LogOutput.log`
   carries loader activity only and never names a world - that was checked, not
   assumed. Enumerating worlds needs a plugin in-process, so the correct next
   artifact is a MINIMAL enumerate-and-log plugin, not the full bridge.
3. Honest correction to acceptance criterion 2: the `--target server` pointed at
   the root negative control is UNREACHABLE, not refused, because the installer
   derives the server target from `--root`. Prevented by construction, but not
   the control the spec asked for. Do not tick it off as passed.

## 2026-07-26 - Cycle 2 spec APPROVED, no code yet

Spec written and approved: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`.
ADR-004 records the ruling. No C# exists yet. Suite still 106 passed,
`ascii_guard` exit 0, both observed this session rather than carried forward.

Ground truth probed live, all of it new:

- The install holds TWO full game copies. Root is `v1.1.13.0-r99712-b17`, the
  pinned build and the one Steam launches. `v3\` is a stale `v1.0.10.4-r91333`
  copy that must never receive BepInEx. The installer asserts VERSION first.
- IL2CPP, not Mono (`GameAssembly.dll`). Loader is BepInExPack V Rising
  `1.733.2`, wrapping BepInEx 6.0.0 bleeding-edge `be.733` on CoreCLR net6.
- `VRising_Server\VERSION` reads `VRisingServer: v1.1.13.0-r99712-b17
  (202605251709)`. Same semantic build as the client, DIFFERENT prefix and
  trailing timestamp, so the install assert compares the semantic build only.
- The game was launched once. `AppData\LocalLow\Stunlock Studios\VRising\` now
  exists with `Player.log`, `Settings\v4\ClientSettings.json`, `CloudSaves\` and
  `ConsoleProfile\`. No save directory, because no world was created.
- Only SDK present is .NET 10.0.301. The plugin targets net6.0. That path is an
  unresolved build risk, not a working config.

Operator rulings: the plugin targets BOTH hosts (client and dedicated server,
ADR-004, overriding the client-only recommendation); `/state` becomes an
envelope carrying `state: null` plus a build stamp and `docs/API.md` was amended
to match; generating `RmPorts.g.cs` into the `test_ports.py` allowlist is
approved; the C# test project is deferred past cycle 2; and downloading the
BepInEx pack is authorized for the next session only.

Two things the next session must settle BEFORE writing code:

1. Port 8777 arbitration when both hosts run at once has a chosen answer, not a
   clean one - bind-time first-come, loser stands down, plus a procedural
   "start the server first". That is procedure, not enforcement. Minting a fifth
   port instead needs an ADR-003 amendment and that call belongs before
   implementation.
2. `PrefabCollectionSystem` is an UNVERIFIED label carried from `ROADMAP.md`. It
   is not a confirmed type name. Six spikes (S1 to S6) remain open and block
   implementation.

## 2026-07-26 - Cycle 1 COMPLETE and merged

Cycle 1 shipped end to end. Branch `cycle-1-harness`, 34 commits, merged into
`master` as `2a493ea`. Ledger entry 001 carries the detail.

State at close, all verified live rather than reported:

- `python -m pytest` 106 passed, `python -m ruff check .` clean,
  `python tools/ascii_guard.py` exits 0.
- `python tools/rmdata_extract.py` writes `data/rmdata/1.1.13.0-r99712/` with
  8379 localization strings and 28 markup codes, byte-identical across runs, and
  seeds `tables/` with five empty validated envelopes for the cycle 2 bridge.
- Remote is `https://github.com/Remus3/RedMoon` (private). `master` pushed.
- `RM-DataRefresh` is installed and Ready, next run 05:30 daily.
- Memory namespace live at
  `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\`, restorable from
  the committed seed in `docs/memory_seed/`.

Two findings worth carrying forward, both caught by review rather than by
running code:

1. The precommit gate was wired with `"matcher": "Bash(git commit:*)"` -
   permission-rule syntax in a field matched against the tool name - so it never
   fired for the whole cycle despite being unit-tested and documented. Fixed to
   `Bash|PowerShell`, with a test that now rejects specifier syntax in any
   matcher. Worth remembering: a hook passing its unit tests says nothing about
   whether it is wired.
2. `docs/BLOODFORGE.md` named `data/rmdata/<build>/tables/*.json` as Bloodforge's
   inputs, but nothing created that directory and `empty_table()` had no
   production caller. Cycle 2 would have invented the path by accident. The
   extractor now produces the seam, never clobbering a populated table.

Parked items and every review ruling are archived in `docs/history_notes.md`.

## 2026-07-26 - Cycle 1 kickoff

Project created at `C:\RedMoon\`. Design spec and implementation plan written
and committed. Ground truth probed: V Rising build
`v1.1.13.0-r99712-b17 (202605251526)`, install at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`, game never launched (no
`AppData\LocalLow\Stunlock Studios`), dedicated server ships with the client.
Ports 8777, 8778, 8779 and 8783 confirmed free; the `RM-*` scheduled-task
namespace confirmed unused.

Key decision: item and ability stat data cannot be extracted offline. It arrives
in cycle 2 from the runtime bridge dump. Cycle 1 ships localization, difficulty
presets, settings schema, and empty typed tables.

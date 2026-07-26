# RedMoon.Bridge spike findings

Cycle 2 opened with six spikes (S1 to S6) that block the plugin. This file
records what has been MEASURED against build `1.1.13.0-r99712`, and what is
still open. Nothing here is recalled or inferred - every closed item names how
it was observed.

Rule for anyone extending this: a spike is closed by running something, not by
reading a wiki. If a line below says OPEN, no code may be scaffolded against a
guess at its answer (CLAUDE.md, Testing Discipline).

## Environment established 2026-07-26

BepInExPack V Rising 1.733.2 is installed into BOTH hosts, 233 files each:

- `<root>\` (client target)
- `<root>\VRising_Server\` (dedicated-server target)

SHA256 of the pack as downloaded:
`EABFB53D80BED427DDBD1ECF8AF4DCD6E82E152809D44AB3218D0A09984F491C`, 33503624
bytes. The archive nests its payload one directory deep under
`BepInExPack_V_Rising/` and carries `icon.png`, `manifest.json` and `README.md`
as Thunderstore metadata at the archive root; the installer strips the wrapper
and drops the three metadata files, which was verified on the real install.

The stale `<root>\v3\` copy (build `v1.0.10.4-r91333-b12`) received nothing and
has no `winhttp.dll`. Both installer negative controls refuse.

The dedicated server was launched once. It reports:

```
BepInEx 6.0.0-dev - VRisingServer
Running under Unity 2022.3.58f1
Runtime version: 6.0.7 (.NET 6.0.7)
IL2CPP Metadata version 31.1
```

That first launch generated **169 Il2CppInterop assemblies** into
`<root>\VRising_Server\BepInEx\interop\`. Those are the plugin's compile-time
references and did not exist before it.

## The probe plugin

Spikes S1(b), S1(c), S1(d), S2, S5 and S6 were closed by a MINIMAL
enumerate-and-log plugin, `_scratch\rmprobe\`, built before the real bridge
precisely because none of those questions is answerable from static metadata.
Like `_scratch\typedump\` it is scratch and deliberately NOT committed - it is
regenerable and must not become a second plugin to maintain per patch.

It compiles the SAME generated `RmPorts.g.cs` the real plugin will, so the
no-port-literal rule holds even in scratch. It reads ECS only from `Update()`
and its listener thread serves a constant, so it never violates D7 / R4 while
testing D7's two halves separately.

It was deployed to both hosts' `BepInEx\plugins\` and each host's OWN log was
read: `BepInEx\rmprobe-client.log` and
`VRising_Server\BepInEx\rmprobe-server.log`.

## R17 - do the two interop sets diverge: CLOSED, safe for the planned reference set

The client was launched and generated its own `BepInEx\interop\`: 172 files, 169
`.dll` plus 2 `.db` and 1 `.txt`. That matches the server exactly, and it also
explains the earlier "169 assemblies" figure - 169 is the DLL count, 172 the file
count. No correction needed.

Three measurements, in increasing usefulness:

1. **Assembly name sets: IDENTICAL.** Zero client-only and zero server-only file
   names.
2. **SHA256: all 169 DLLs differ.** This is NOT a divergence signal.
   Il2CppInterop codegen is non-deterministic, so a hash diff reports 100 percent
   divergence between any two generations and is useless here. 11 DLLs also
   differ in SIZE, which is a real signal:
   `ProjectM`, `ProjectM.Shared`, `ProjectM.GeneratedNetCode`, `ProjectM.HUD`,
   `Il2Cppmscorlib`, `Rukhanka.Hybrid`, `Rukhanka.Runtime`,
   `Unity.Entities.Graphics`, `Unity.Mathematics`,
   `Unity.RenderPipelines.Core.Runtime`, `UnityEngine.UnityWebRequestModule`.
3. **Type-level diff, which is the one that decides the `.csproj`.** 55085 types
   in the client set, 55579 in the server set: 97 client-only, 591 server-only.

Almost all of that count is codegen noise, not API divergence. Two generated
types per assembly, `__JobReflectionRegistrationOutput__<hash>` and
`__UnmanagedPostProcessorOutput__<hash>`, carry a per-build hash in their name
and so appear as a diff in BOTH directions for nearly every assembly. Compiler
closure and iterator types (`__c__DisplayClass*`, `_Start_d__*`, `__c`) and
system-nested helpers (`Enumerator`, `TypeHandle`, `ResolvedChunk`, `IFE_*`)
renumber the same way. None is referenceable by name from authored code.

The REAL divergence is in three places, and none is needed:

- `ProjectM.GeneratedNetCode`: 499 server-only types, the netcode serializer set.
- `ProjectM`: about 17 server-only types, all network send-priority machinery
  (`ProjectM.Network.PrioritizeSystemData`, `AddAlwaysSyncToUsersJob`,
  `UserPriorityRange` and siblings).
- `Rukhanka.Runtime` and `Rukhanka.Hybrid`: client-only animation types.

RULING for the `.csproj`: **`ProjectM.Shared`, `Stunlock.Core`, `Unity.Entities`
and `ProjectM.Gameplay.Systems` have ZERO real type divergence between the two
hosts**, and every type the design needs was checked present in BOTH sets by
name: `ProjectM.PrefabCollectionSystem`,
`Stunlock.Core.PrefabCollectionSystem_Base`, `Stunlock.Core.PrefabLookupMap`,
`ProjectM.EquippableData`, `ProjectM.RecipeData`,
`ProjectM.RecipeRequirementBuffer`, `ProjectM.SpellLevel`,
`ProjectM.SpellLevelSource`, `ProjectM.BloodQualityBuff`,
`ProjectM.ShadowVBloodUnitTagComponent`, `Unity.Entities.World`,
`Unity.Entities.WorldUnmanaged`, and all three of
`ProjectM.Gameplay.Systems.ArmorLevelSystem_Spawn`, `WeaponLevelSystem_Spawn`
and `SpellLevelSystem_Spawn`. The `.csproj` may reference either tree for these;
the probe references the CLIENT tree and loads correctly in both hosts, which is
the proof. R17 is retired for this reference set and must be re-run per patch.

## S4 - building net6.0 with a .NET 10 SDK: CLOSED, now including the references

MEASURED. A `net6.0` class library builds clean under SDK `10.0.301`, the only
SDK installed, with exit 0. No .NET 6 targeting pack is installed on this
machine and none was needed - NuGet restored the reference pack itself. No
`global.json` is needed.

Resolution: NEITHER fallback in the spec's resolution order applies. Risk R2 is
retired for the bare target framework.

The residual half is now closed too. The probe plugin builds clean, exit 0, zero
warnings, with the full reference set added: `BepInEx.Core`,
`BepInEx.Unity.Common`, `BepInEx.Unity.IL2CPP`, `Il2CppInterop.Runtime`,
`0Harmony`, `SemanticVersioning`, and the interop assemblies `Il2Cppmscorlib`,
`Il2CppSystem`, `Il2CppSystem.Core`, `UnityEngine.CoreModule`, `Unity.Entities`,
`Unity.Collections`, `Unity.Mathematics`, `Stunlock.Core`, `ProjectM`,
`ProjectM.Shared`, `ProjectM.Gameplay.Systems`.

One reference is non-obvious and cost a build: `BepInEx.Paths.BepInExVersion`
returns a `SemanticVersioning.Version`, so touching it forces a reference to
`BepInEx\core\SemanticVersioning.dll`. R2 is fully retired.

## S3a - the prefab collection type: CLOSED, CONFIRMED

`PrefabCollectionSystem` was carried into `ROADMAP.md` and the cycle 1 spec from
prior project notes as an UNVERIFIED label. It survives contact with the build.

```
ProjectM.Shared.dll    ProjectM.PrefabCollectionSystem
Stunlock.Core.dll      Stunlock.Core.PrefabCollectionSystem_Base
ProjectM.Shared.dll    ProjectM.PrefabCollectionSystem_ReactToGameDataInitialized
```

Confirmed, not corrected. The roadmap needs no fix on this point.

Its GUID-to-entity mapping, read from the type's own metadata:

- `_PrefabGuidToEntityMap`, whose element type is visible in the
  `RegisterPrefabs_Execute` signature as
  `NativeParallelHashMap<PrefabGUID, Entity>`.
- `_PrefabLookupMap`, reachable through the instance property
  `get_PrefabLookupMap` and through two STATIC overloads,
  `GetPrefabLookupMap(World)` and `GetPrefabLookupMap(WorldUnmanaged)`. The
  static-over-World overload is the most promising entry point for the dumper,
  because it needs a world handle and nothing else.
- `get_GameDataInitialized` returns a bool and is the natural readiness gate for
  the `world_not_ready` error code.
- `_SpawnableNameToPrefabGuidDictionary` is a `Dictionary<String, PrefabGUID>`
  and is a second, name-keyed route into the same data.

## S3 - which component types carry item stats: PARTIALLY RESOLVED

Real types located in the interop set. These are confirmed to EXIST with these
exact names and assemblies. Their FIELD LAYOUTS are not yet mapped onto the five
schemas, and that mapping is what remains of S3:

| Need | Confirmed type | Assembly |
|---|---|---|
| Equipment identity | `ProjectM.EquippableData` | `ProjectM.Shared` |
| Recipe definition | `ProjectM.RecipeData` | `ProjectM.Shared` |
| Recipe ingredients | `ProjectM.RecipeRequirementBuffer` | `ProjectM.Shared` |
| Spell level | `ProjectM.SpellLevel`, `ProjectM.SpellLevelSource` | `ProjectM.Shared` |
| Gear level systems | `ArmorLevelSystem_Spawn`, `WeaponLevelSystem_Spawn`, `SpellLevelSystem_Spawn` | `ProjectM.Gameplay.Systems` |
| Blood quality | `ProjectM.BloodQualityBuff` | `ProjectM` |
| V Blood tracking | `ProjectM.ShadowVBloodUnitTagComponent` | `ProjectM` |

Note the shape this implies for gear score: armor, weapon and spell levels are
carried by three SEPARATE systems and component families, not one gear_score
field. The `items.gear_score` schema field is a Red Moon-computed quantity, not
a direct read, and cycle 3 should treat it as such.

### S3 field layouts, read 2026-07-26

Real fields, read from each type's own metadata rather than recalled:

`ProjectM.EquippableData` (`ProjectM.Shared`):
`BuffGuid`, `EquipmentType`, `WeaponType`, `EquipmentSet`, `SCTBrokenText`,
`DurabilitySettings`.

**This is the S3 headline and it changes the dumper's shape.** `EquippableData`
carries NO stat values. There is no stat line on the equipment component at all.
It carries a `BuffGuid`, and the stats live on the BUFF prefab that guid points
at. So `items.stats` is a two-hop read, not a field copy:

```
item prefab entity
  -> EquippableData.BuffGuid
  -> PrefabLookupMap lookup on that guid
  -> buff prefab entity
  -> DynamicBuffer<ProjectM.ModifyUnitStatBuff_DOTS>
```

`ProjectM.ModifyUnitStatBuff_DOTS` (`ProjectM.Shared`) is the stat element:
`StatType`, `ModificationType`, `Value`, `SoftCapValue`, `Modifier`,
`IncreaseByStacks`, `ValueByStacks`, `Priority`, `AttributeCapType`, `Id`.

CONSEQUENCE for the schema: `items.stats` is documented as "stat modifier name to
numeric value", which is a FLATTENING of that element. A single stat entry
carries a modification type, a soft cap and a stacking rule, and none of those
survives a name-to-number map. Cycle 3 combat math needs `ModificationType` at
minimum, because an additive and a multiplicative modifier of the same `Value`
are not the same stat. This is a real schema question for the first-dump review,
not a dumper detail. Do NOT flatten silently.

`ProjectM.RecipeData` (`ProjectM.Shared`): `Entity`, `Guid`, `CraftDuration`,
`HudSortingOrder`, `AlwaysUnlocked`, `HideInStation`, `IgnoreServerSettings`.

`ProjectM.RecipeRequirementBuffer` (`ProjectM.Shared`): `Guid`, `Amount`, plus a
`ToInventoryBuffer` accessor. This maps cleanly onto
`recipes.ingredients[].{guid,amount}`.

Note `RecipeData` has no output-guid field. `recipes.output_guid` is required by
the schema, so where the output comes from is an open question for the first
dump - candidates are the recipe prefab's own guid and a separate output buffer.

STILL OPEN in S3: the ability school field, the V Blood level field, the blood
type bonus tiers, and the confirmed-or-corrected `/state` field set. The mapping
above is enough to start `PrefabDumper.cs` for items and recipes and no more.

## S1 - ECS world access and host detection

### S1(a) world acquisition: CLOSED

`Unity.Entities.World.All` is a public static property returning
`NoAllocReadOnlyCollection<World>`, read from the type's own metadata and then
exercised live. It is indexable and gives `Name`, `Flags`, `IsCreated`,
`SequenceNumber` and `Systems`. That is the whole world-acquisition code path;
nothing else is needed.

### S1(d) host detection: CLOSED

`BepInEx.Paths.ProcessName` is the mechanism. Measured live:

| Host | `Paths.ProcessName` | `Paths.GameRootPath` | port |
|---|---|---|---|
| client | `VRising` | `...\common\VRising` | 8777 |
| server | `VRisingServer` | `...\common\VRising\VRising_Server` | 8780 |

Both hosts also report `Paths.BepInExVersion`
`6.0.0-dev+3a12d1810bf4dd5ca1635352ccf5bff5d95f987f` and
`Environment.Version` `6.0.7`. `HostDetect.cs` is a one-liner over
`ProcessName`, and `Paths.GameRootPath` is what `/health` reports as
`game_root`.

### S1(c) server worlds: CLOSED

Server host, world set stable across 12 samples:

| # | Name | Flags | Systems | Prefab map |
|---|---|---|---|---|
| 0 | `Default World` | Simulation | 28 | throws |
| 1 | `LoadingWorld0` | Streaming | 0 | throws |
| 2 | **`Server`** | Simulation | 710 | **OK, Count 1189** |
| 3 | `LoadingWorld0` | Streaming | 0 | not reached |

The target world in the server host is named `Server`.

CONSEQUENCE, and it is the important one: world selection MUST be by name plus a
readiness check, never by index and never by taking the first Simulation world.
`Default World` is a Simulation world too, it appears at index 0, and asking it
for the prefab map throws `ArgumentException: The entity does not exist`.
`LoadingWorld0` throws `InvalidOperationException: System is from a different
world`. Those two exceptions are the natural `world_not_ready` error path and
they are a genuine negative control - a stub cannot produce them.

### S1(b) client worlds: PARTIAL, needs an in-game sample

Client host at the MAIN MENU, two worlds only:

| # | Name | Flags | Systems | Prefab map |
|---|---|---|---|---|
| 0 | `Default World` | Simulation | 56 | throws (entity does not exist) |
| 1 | `LoadingWorld0` | Streaming | 0 | throws (different world) |

So at the client main menu there is NO prefab-carrying world at all. This is a
finding, not a failure: `/state` and `/dump/prefabs` in the client host must
report `world_not_ready` until a world is loaded, and the client-host dump cannot
be taken from the menu.

What remains of S1(b) is the in-game client world set, which needs a character
loaded. Until that sample exists, the claim "the client can serve a dump" is
UNPROVEN and must not be written down as true. The old S1 question - whether a
server simulation world exists inside the client process when playing solo - is
answered by the same sample.

## S2 - scheduling onto the game's main thread: CLOSED

An Il2Cpp-injected `MonoBehaviour` is the mechanism, and it works in both hosts:

```
ClassInjector.RegisterTypeInIl2Cpp<Tick>();
var go = new GameObject("...");
go.hideFlags = HideFlags.HideAndDontSave;
UnityEngine.Object.DontDestroyOnLoad(go);
go.AddComponent<Tick>();
```

`Update()` was reached in both hosts on managed thread 1, about 2.4 s after
`Load()` in the server and 2.6 s in the client. Neither a Harmony patch nor an
Il2CppInterop hook is needed. D7 is implementable as specified: this tick is the
snapshot producer, the listener thread is the consumer.

Note the injected type needs the `public Tick(IntPtr ptr) : base(ptr) { }`
constructor or injection fails.

## S5 - HTTP listener viability in-process: CLOSED for bind, serve and hard-kill

`System.Net.HttpListener` is the choice. Measured in both hosts:

- Bind: `http://127.0.0.1:8780/` in the server and `http://127.0.0.1:8777/` in
  the client, both within about 12 ms of `Load()`, no elevation needed for a
  `127.0.0.1` prefix.
- Serve: a real `curl` against each host returned the probe body, and each host's
  own log recorded the request. Both hosts served concurrently, which is the
  ADR-005 payoff observed rather than argued.
- Release, risk R11: after `taskkill /F` on the server, port 8780 held no
  LISTEN - only a client-side `TIME_WAIT` on the ephemeral port - and
  `bridge_probe.py --expect-unreachable --expect-host server` PASSED. A hard kill
  is the worst case, so R11 is retired.

Still unobserved: the graceful path, `Unload()` running `_listener.Stop()` on a
normal game exit. `taskkill /F` skips `Unload()` by definition.

## S6 - dump cost: PARTIAL, and much cheaper than feared

Server host, `Server` world: `PrefabCollectionSystem.GetPrefabLookupMap(world)`
returned `IsCreated=True` with `Count()` of **1189**, in under 1 ms end to end
(`get_ms=0`, `total_ms=0`).

Reading the map is therefore free at frame scale and needs no chunking. What is
NOT yet measured is the cost of the actual dump: resolving 1189 entities, reading
their components, and serializing them. 1189 is also the count of prefabs
REGISTERED at that moment, not a proven total, so it is a floor rather than a
final number. `Stunlock.Core.PrefabLookupMap` exposes `Count`, `TryGetValue`,
`TryGetName`, `GetName` and `TryGetPrefabGuidWithName`, which is enough for the
dumper and for the localization join.

## Tooling note

The spike tool is `_scratch\typedump\`, a throwaway net8.0 console app that
reads the interop assemblies with `System.Reflection.Metadata` and reports type
names, fields and methods. It is deliberately NOT committed - it is scratch, it
is regenerable, and it must not become a second thing to maintain per patch.
Recreate it if another metadata question comes up.

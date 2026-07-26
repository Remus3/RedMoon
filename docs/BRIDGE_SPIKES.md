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

## S4 - building net6.0 with a .NET 10 SDK: CLOSED

MEASURED. A `net6.0` class library builds clean under SDK `10.0.301`, the only
SDK installed, with exit 0. No .NET 6 targeting pack is installed on this
machine and none was needed - NuGet restored the reference pack itself. No
`global.json` is needed.

Resolution: NEITHER fallback in the spec's resolution order applies. Risk R2 is
retired for the bare target framework. What remains unproven is the build with
the BepInEx and Il2CppInterop references added, which is a reference-resolution
question rather than a targeting-pack one.

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

STILL OPEN in S3: the field-by-field mapping table that `PrefabDumper.cs`
implements, and the confirmed-or-corrected `/state` field set. Do not write the
dumper before this is done.

## S1 - ECS world access and host detection: OPEN

Partially advanced, not closed. What is now known:

- The interop set for the SERVER host is enumerated: 169 assemblies, including
  `Unity.Entities`, `ProjectM`, `ProjectM.Shared`, `ProjectM.Gameplay.Systems`,
  `Stunlock.Core` and `Stunlock.Localization`.
- The CLIENT host's interop set has NOT been generated. The client has BepInEx
  installed but has not been launched. Until it is, the interop DIFF that risk
  R17 depends on cannot be run, and no reference set may be pinned in the
  `.csproj`.

What is still open and CANNOT be answered from static metadata: the world NAMES
visible in each host, and the host-detection mechanism. `BepInEx\LogOutput.log`
carries loader activity only and never names a world, which was checked rather
than assumed. Enumerating `World.All` requires a plugin actually running in the
process. S1(b), S1(c) and S1(d) are therefore blocked on a first plugin build,
which makes a minimal enumerate-and-log plugin the correct next artifact rather
than the full bridge.

## S2 - scheduling onto the game's main thread: OPEN

Not started. Decision D7 depends on it.

## S5 - HTTP listener viability in-process: OPEN

Not started. Note one input the environment now supplies: the loader runs on
CoreCLR .NET 6.0.7 under Unity 2022.3.58f1, so `HttpListener` is available in
principle. Whether it binds and shuts down cleanly inside the IL2CPP host
remains the actual question.

## S6 - dump cost: OPEN

Not started. Depends on the dumper existing.

## Tooling note

The spike tool is `_scratch\typedump\`, a throwaway net8.0 console app that
reads the interop assemblies with `System.Reflection.Metadata` and reports type
names, fields and methods. It is deliberately NOT committed - it is scratch, it
is regenerable, and it must not become a second thing to maintain per patch.
Recreate it if another metadata question comes up.

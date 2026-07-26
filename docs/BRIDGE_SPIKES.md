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

**CORRECTED 2026-07-26 by a live entity dump. The two-hop conclusion below was
WRONG.** `EquippableData` genuinely carries no stat values - that half stands -
but the inference that the stats therefore live on the buff prefab does not. They
are on the ITEM prefab itself, as a populated `DynamicBuffer`:

```
Item_Boots_T00_StartingRags  item stats.Length=1
  [0] StatType=MaxHealth ModificationType=Add Value=13 Priority=0 IncreaseByStacks=False
  EquippableData.BuffGuid=-1465458722 name=EquipBuff_Boots_Base
  buff: no ModifyUnitStatBuff_DOTS buffer
```

Three of three sampled items agree (`Boots` 13, `Legs` 16, `Chest` 17 MaxHealth
Add), and in every case the buff prefab named by `BuffGuid` has NO stat buffer at
all. So `items.stats` is a ONE-HOP read off the item prefab, and
`EquippableData.BuffGuid` names a behaviour buff, not a stat carrier.

How the error happened is worth keeping: the field list was read from type
metadata, saw no stat field on `EquippableData`, and reasoned to where the stats
"must" be. That is inference presented as measurement. The component list of a
real entity settled it in one run.

The schema consequence is UNCHANGED and now has real values behind it:
`ModificationType=Add` is a live enum on the element, so a flat name-to-number map
cannot carry it, and an additive and a multiplicative modifier of the same `Value`
are not the same stat.

The superseded two-hop path, kept so the correction is legible:

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

`RecipeData` has no output-guid field, and the answer is a second buffer:
`ProjectM.RecipeOutputBuffer` (`ProjectM.Shared`), fields `Guid` and `Amount`,
which maps onto `recipes.output_guid` and `recipes.output_amount`. There is also
a `ProjectM.RecipeOutputUnitBuffer` for recipes that produce a unit rather than
an item, which the dumper must not confuse with the item output.

So `recipes` is fully mapped except `station_guid`:

| Schema field | Source |
|---|---|
| `prefab_guid` | the recipe prefab's own PrefabGUID |
| `output_guid` | `RecipeOutputBuffer.Guid` |
| `output_amount` | `RecipeOutputBuffer.Amount` |
| `ingredients[].prefab_guid` | `RecipeRequirementBuffer.Guid` |
| `ingredients[].amount` | `RecipeRequirementBuffer.Amount` |
| `craft_duration` | `RecipeData.CraftDuration` |
| `station_guid` | OPEN - the station references the recipe, not the reverse |

STILL OPEN in S3, and deliberately left open rather than guessed: the ability
school field, the V Blood level field, the blood type bonus tiers, and the
confirmed-or-corrected `/state` field set. There is no `SpellSchool` component
type - the school-shaped types are `SpellSchoolAuthoring`,
`SchoolDebuffData` and `SpellSchoolTierProgressionPoints`, none of which is
obviously the per-ability field. That hunt wants a live entity sample and its
real component list, which needs the in-game world, so it is blocked behind the
same gate as S1(b) rather than behind more metadata reading.

### S3 live entity dump, 2026-07-26: what the component lists settled

Taken in the standalone dedicated server at a settled map (23583). The name table
makes every schema addressable: `AB_` 8308, `TM_` 4121, `Item_` 1107, `Recipe_`
667, `Buff_` 560, `CHAR_` 532, plus `BloodType_*` and `CHAR_*_VBlood` by name.

`recipes` is CONFIRMED writable, with values, not just field names:

```
Recipe_Headgear_T01_RazerHood  CraftDuration=10 AlwaysUnlocked=True HideInStation=False
  req[0] -237441421  x1 Item_Ingredient_Gem_Emerald_T01
  req[1] -700774739  x8 Item_Ingredient_Cloth
  out[0] -1797796642 x1 Item_Headgear_RazerHood
```

`blood_types` is now mappable and was not before. `BloodType_VBlood` has 12
components, two of which are the bonus tiers:
`ProjectM.Shared.PrimaryUnitBloodTypeBuffs` and
`ProjectM.Shared.SecondaryUnitBloodTypeBuffs`, both `DynamicBuffer`s.

`vbloods` has its LEVEL candidate, read from type metadata and NOT yet value-
measured, so it is a lead and not a closed question.
`ProjectM.VBloodConsumeSource` carries `Source`, `JournalCategory`,
`QuestFlavorTextOverride`, `TooltipGUID`, `SpellSchool`, `Tier`,
`SpellSchoolPoints` and `PassivePoints`. `Tier` is the V Blood level candidate.

Do NOT conflate the two school facts. `VBloodConsumeSource.SpellSchool` is a
FIELD naming the school a V Blood GRANTS on feeding, and it is why the earlier
"there is no SpellSchool component type" note was true but misleading - the name
exists as a field, not a type. The per-ability damage school is a different
thing entirely: `DealDamageParameters.MainType` on the `_Hit` entity, measured
above. One is progression, the other is combat math.

`vbloods` also has its marker CORRECTED. The census probed
`ShadowVBloodUnitTagComponent` and returned zero, which is a true absence and a
misleading one - that type is a runtime tag, not a prefab marker. The real
prefab-side types, read off `CHAR_Militia_HoundMaster_VBlood` and
`CHAR_Undead_BishopOfDeath_VBlood`, are `ProjectM.VBloodUnit`,
`ProjectM.VBloodConsumeSource`, `ProjectM.VBloodAbilityBuffEntry` (buffer) and
`ProjectM.VBloodUnlockTechBuffer` (buffer). The V Blood LEVEL field is not yet
pinned to one of them.

**The ability school is FOUND and MEASURED.** There is no `SpellSchool`
component, which is why three metadata scans missed it. The school is a field on
a buffer element on the ability's `_Hit` entity:

```
ability _Hit prefab
  -> DynamicBuffer<ProjectM.DealDamageOnGameplayEvent>
  -> element .Parameters            (ProjectM.DealDamageParameters)
  -> .MainType                      (ProjectM.MainDamageType)
```

`ProjectM.MainDamageType` (`ProjectM.Shared`) has ten members: `Physical`,
`Spell`, `Fire`, `Holy`, `Silver`, `Garlic`, `RadialHoly`, `RadialGarlic`,
`WeatherLightning`, `Corruption`. `DealDamageParameters` also carries
`MainFactor`, `RawDamageValue`, `RawDamagePercent`, `StaggerFactor`,
`ResourceModifier`, `MaterialModifiers` and `DealDamageFlags`.

Six live samples, and the point of taking six is that one would not have been
evidence - a single `Physical` reading cannot be told apart from a default:

| Prefab | MainType | MainFactor |
|---|---|---|
| `AB_EmeryGolem_GroundSlam_Hit` | Physical | 2.5 |
| `AB_IronGolem_GroundSlam_Hit` | Physical | 2.5 |
| `AB_Monster_GroundSlam_Hit` | Physical | 1.4 |
| `AB_Undead_Leader_AreaAttack_Hit` | **Spell** | 2.5 |
| `AB_Legion_NightMaiden_WhipTwirl_Hit` | Physical | 1.8 |
| `AB_Purifier_MeleeAttack_Right_Hit` | Physical | 1.3 |

Both fields vary across samples, so this is a real per-ability field.

Where it is NOT, all four checked against real component lists rather than
guessed: `_Cast` (40 components, e.g. `AB_Knight_2H_SideStep_Left_Cast`),
`_AbilityGroup` (16), `_Buff`, `_Projectile`. None carries anything
school-shaped. The `AB_` family splits by suffix - census counts `Cast` 1551,
`AbilityGroup` 1476, `Buff` 456, `Hit` 359, `Projectile` 289 - and only `_Hit`
carries the damage parameters.

What is still open for `abilities`: the join from an ability GROUP to its `_Hit`
entity is not yet traced, so a per-ability row cannot be assembled end to end
yet. That is a name or reference join question, not another school hunt.

`PrefabDumper.cs` may therefore write `items` and `recipes` now. `blood_types` is
close but its buffer element fields are unread. `abilities` and `vbloods` are not
writable.

The superseded summary line, kept for legibility: "enough to start
`PrefabDumper.cs` for `items` and `recipes` and no more."

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

### S1(b) client worlds: CLOSED for the world set, and the answer relocates the dump

Client host IN GAME, measured 2026-07-26 in a Private Game (Relaxed, Solo Only
ticked, world named `Solo Only`, no password). Six worlds, stable for the whole
session:

| # | Name | Flags | Systems | Prefab map |
|---|---|---|---|---|
| 0 | `Default World` | Simulation | 56 | throws (entity does not exist) |
| 1 | `LoadingWorld0` | Streaming | 0 | throws (different world) |
| 2 | **`Client_0`** | Simulation | 688 | IsCreated=True, **Count=0** |
| 3 | `LoadingWorld0` | Streaming | 0 | throws |
| 4 | `LoadingWorld1` | Streaming | 0 | throws |
| 5 | `LoadingWorld2` | Streaming | 0 | throws |

**No world named `Server` exists inside the client process.** The old S1 question -
whether a server simulation world lives in the client when playing solo - is
answered NO.

Where it actually lives, and this is the finding that matters: a Private Game
SPAWNS A CHILD PROCESS. Measured, `VRisingServer.exe` pid 17256 with
ParentProcessId 22512 (the client), started in the same second the client world
set changed, running from `VRising_Server\VRisingServer.exe` - the tree that HAS
BepInEx installed.

**BepInEx does not load into that child.** Three independent observations:

- port 8780 held no LISTEN while it ran;
- `VRising_Server\BepInEx\LogOutput.log` was untouched by it;
- its own `Player-server.log`, live and 139 KB, contains zero occurrences of
  `doorstop`, `bepinex` or `preloader`.

CONSEQUENCE. In the Private Game configuration neither host can currently serve a
prefab dump: the client's own map is empty and the process holding the real world
has no plugin. The dump route that IS proven is the STANDALONE dedicated server.
Why the child does not load BepInEx is NOT established - doorstop environment
inheritance from the parent is a hypothesis, not a measurement, and must not be
written down as the cause until someone tests it.

Still genuinely open: whether `Client_0`'s count stays 0 after a full load. It was
sampled 0 at the load instant, and the probe that took the sample only logged on
world-set change, so it could not re-measure. The count-change tracking that
closes this is now in the probe but has not yet been run in the client.

### S1(b) history: the main-menu sample

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

## S6 - dump cost: CLOSED, and the 1189 figure was a mid-load artifact

**The count is 23583, not 1189.** The earlier note called 1189 "a floor rather
than a final number" and that caution was right. Measured with per-sample count
tracking, the server's map fills in over about 1.7 s after the world appears:

```
Count 1189 -> 3212 -> 11760 -> 17400 -> 23583   GameDataInitialized False..False,True
```

`GameDataInitialized` flips False to True exactly as the count settles at 23583,
so it is a REAL readiness gate and not merely a plausible one. That is the flag
the bridge should use for `world_not_ready`, and it is now measured rather than
assumed.

CONSEQUENCE, and it is a trap worth naming: anything that samples the prefab map
on first non-zero count gets a castle-tile-and-blueprint subset. The first census
run did exactly that and reported zero items, zero recipes and zero abilities -
a confident, complete-looking, wrong answer. Gate on a settled count, or on
`GameDataInitialized`, or on both.

Dump cost, now measured end to end rather than deferred: **47573 entities in the
world, 23955 carrying `PrefabGUID`, full component enumeration and name
resolution for every one of them, in 57 ms** on the main thread. Reading the map
itself remains free (`get_ms=0`). No chunking is needed. `Stunlock.Core.PrefabLookupMap` exposes `Count`, `TryGetValue`,
`TryGetName`, `GetName` and `TryGetPrefabGuidWithName`, which is enough for the
dumper.

**CORRECTED 2026-07-26. The clause "and for the localization join" was WRONG**
and is struck. `PrefabLookupMap`'s full member list was read from its own
metadata - `GuidToEntityMap`, `AssetDataLookup`, `_ConversionStateLookup`,
`GameDataInitialized`, plus `Count`, `ContainsKey`, `TryGetValue`,
`GetValueOrDefault`, `GetName`, `TryGetName`, `GetFixedName`, `TryGetFixedName`,
`TryGetPrefabGuidWithName`, `NameMatches`, `IsConvertedOrConvertable`,
`CheckConvertableOnDemand`, `GetConversionState`, `SetConversionState` - and
NONE of them is localization-shaped. The name it returns is the PREFAB name, not
a display name. See the S7 section for where the join actually lives.

## S1(b) client dump: CLOSED 2026-07-26, the client CAN serve a dump

The last open half of S1(b) is measured. The operator loaded the Solo Only world
with the count-tracking probe deployed, and `BepInEx\rmprobe-client.log` records
`Client_0` filling and settling:

```
Count 0 -> 7005 -> 16352 -> 30484   GameDataInitialized False..False,True
census gate open: Count=30484 held for 5 samples, GameDataInitialized=True
census: total=85591 withPrefabGUID=31953 listed=31953 complete elapsed_ms=95
```

`GameDataInitialized` flips exactly as the count settles, the same readiness
signature the server showed. Side by side:

| | client | server |
|---|---|---|
| total entities | 85591 | 47631 |
| carrying `PrefabGUID` | 31953 | 23978 |
| dump cost | 95 ms | 54 ms |

The client map is LARGER than the server's by 7975 entities and 95 ms is still
free. "The client can serve a dump" is now PROVEN and may be written down.

A trap worth recording, because it nearly produced a wrong entry here. The
client census line reads `equip=2 recipe=2 spell=0 blood=0 vblood=0`, which
looks exactly like "the client carries no item data". It is not. The SERVER line
reads `equip=2 recipe=2` too, and the server produced 425 items and 663 recipes.
Those counters are capped deep-dump target selectors (`_scratch\rmprobe\Probe.cs`
lines 441 to 445), not census totals. They are evidence of nothing in either
direction. The comparison against the server log is what caught it.

STILL OPEN, and deliberately not claimed: whether the client's item and recipe
COMPONENT data matches the server's. Only the prefab map was compared. Settling
it needs the real bridge run in the client host and a diff of the two dumps.

## S7 - the prefab to localization join: MEASURED ABSENT offline

`items.name` is the raw prefab name and `localization_guid` was omitted. The
question was whether a join exists in the data already on disk. It does not.

`strings.json` is a flat map of localization GUID to English text, keyed from
`entry["Guid"]` of `StreamingAssets/Localization/English.json` Nodes
(`tools/rmdata_extract.py` lines 77 to 81, written at line 143). MEASURED: all
8379 keys are dashed UUIDs, zero are integers, and every Node carries exactly
`(Guid, Text)` - there is no prefab name or prefab hash anywhere in the file.

Join attempts against all 425 item rows, every one measured rather than reasoned:

| Key tried | Hit rate |
|---|---|
| prefab name as a `strings.json` key | 0 / 425 |
| `prefab_guid` decimal | 0 / 425 |
| `prefab_guid` in six hex, 0x, 8-digit and unsigned-32 forms | 0 / 425 |
| prefab name as a `strings.json` VALUE | 0 / 425 |
| casefold-alnum tail of prefab name vs value | 0 / 425 |
| token-set equality, camelCase split | 53 / 425 |

12.5 percent on a name heuristic is not a join. `BuiltVariants.json` is a shader
variant list and contains 0 of 425 prefab names and 0 of 500 loc guids.
Excluding the opaque DOTS blobs under `ContentArchives/` and `EntityScenes/`,
StreamingAssets ships no prefab-to-localization table.

The runtime route, every member verified against the interop metadata:

```
ProjectM.GameDataSystem            (ProjectM.Shared, base SystemBase)
  -> get_ManagedDataRegistry()     -> Stunlock.Core.ManagedDataRegistry
  -> TryGet<ProjectM.ManagedItemData>(PrefabGUID, out T)
  -> .Name                         (Stunlock.Localization.LocalizationKey)
  -> .Key.ToGuid().ToString()      -> the dashed lowercase strings.json key
```

NOT `PrefabLookupMap`, which carries no localization member - see the correction
in S6. `localization_guid` stays declared and optional in the schema and is
omitted until the dumper performs this read. INFERRED and not measured: that
`ManagedItemData` is registered for all 425 equippables, and that `Localization`
is initialized on a server host.

## items.tier - NO SOURCE EXISTS on this build, schema_version 3

`items.tier` was FABRICATED as 0 on all 425 rows of the first dump. The schema
required it, so the dumper emitted a placeholder. It is now dropped from
`required` at `schema_version` 3, kept DECLARED so `validate_table` still
type-checks it and existing fixtures still pass, and OMITTED by the dumper.

The negative is credible because of what was checked and not found. MEASURED
across all 169 client interop assemblies: an exhaustive field-name scan for
`Tier` returns 67 fields and ZERO on a per-item-prefab component - every one is
spell-school progression, blood, jewel or spellmod roll data, legendary instance
state, castle heart, a hash-map key, a HUD view-model, an authoring type or
Unity graphics. `Rarity` returns zero hits anywhere in ProjectM. `Rank` hits
only the EOS SDK. `ProjectM.ItemData`, the real item-definition component
(`SilverValue`, `ItemTypeGUID`, `MaxAmount`, `ItemType`, `ItemCategory`,
`RemoveOnConsume`, `SortOrder`), has no tier field; `ItemType` and `ItemCategory`
are flag enums, not ordinal tiers. `ProjectM.TechData` has no tier either.

TWO derivations were REJECTED on evidence rather than left untried:

1. The `_T0x` prefab-name token. Name-convention guessing already produced one
   wrong answer this cycle and is barred.
2. `ArmorLevelSource.Level`. MEASURED exactly `10 x tier` on 117 of 425 rows -
   genuinely tempting - but that divisor is calibrated against the same
   forbidden token, the value is ALREADY published as `gear_score`, and
   headgear (34), cloaks (34) and bags (6) carry no level component at all,
   leaving 74 rows unsourced.

`ProjectM.ItemConstants` exposes a static `MAX_TIER` and no backing per-item
field, which is the tell: the concept exists in Stunlock's code and nothing
stores it per item. Absent now means unsourced, NOT zero.

## R17 extension: `Unity.Transforms` is inside the measured set

`StateReader.cs` needed `Unity.Transforms.LocalToWorld` as a position fallback,
which is outside R17's original four-assembly ruling. Rather than assume, the
divergence was measured from the existing `_scratch\types_client.txt` and
`types_server.txt`:

| Assembly | client types | server types | client-only | server-only |
|---|---|---|---|---|
| `Unity.Transforms` | 61 | 61 | 4 | 4 |
| `Unity.Entities` | 3441 | 3441 | 6 | 6 |

All 4 `Unity.Transforms` differences are `__JobReflectionRegistrationOutput__`
and `__UnmanagedPostProcessorOutput__` per-build hash types, which R17 already
established are codegen noise and not referenceable by name from authored code.
That is the identical signature to `Unity.Entities`, which was already inside
the set. ZERO real divergence, so the reference is safe. Re-run per patch.

## StateReader and the prefab-template trap: a passing test suite proved nothing

`/state` used to return `state: null`. `StateReader.cs` now returns real data and
`bridge_probe --motion-diff` PASSES against the live client. The route is worth
recording because the first version was WRONG in a way that looked right.

The first implementation compiled clean at 0 warnings, passed 284 tests, and on
a `batchMode` server with NOBODY CONNECTED returned:

```
state_reason: ok
position: {x: 0, y: 0, z: 0}
vitals:   health 125/125, blood 75/100
```

Confident, complete-looking, and false. The prefab map holds a `PlayerCharacter`
TEMPLATE entity, and an unfiltered `GetAllEntities` scan finds it. Only
`--motion-diff` caught it: two samples five seconds apart were byte-identical,
because a template never moves. The probe's own failure text names the class
exactly - a stub, a cached snapshot and a default-constructed component all look
like this.

The fix is one filter: skip entities carrying `Unity.Entities.Prefab`, which is
component `[109]` on the real component list in the census log, not a guess.
After it, the same no-player server honestly returns `state_reason=no_character`
with `state: null` - a real negative control, since a stub cannot tell the two
cases apart.

Verified live in the client, operator moving:

```
sample 1  position {x: -868.508972, y: 4e-06, z: -1788.14209}
sample 2  position {x: -862.950745, y: 4e-06, z: -1784.278076}
PASS motion-diff: the game is live
```

Vitals read `health 231.899994` against `max_health 231.905533` - a fractional
mismatch no default constructor produces. The lesson to carry: for a live-data
reader, a green suite and a clean build are necessary and nowhere near
sufficient. Only the liveness probe distinguished real from plausible.

## The cycle 2 measurement pass, 2026-07-26: all five tables become writable

Six open questions were carried into this pass. All six are now measured, three
runs of an extended `_scratch\rmprobe` in the standalone dedicated server, each
behind the same `GameDataInitialized` gate the census uses. The probe printed
FULL component lists rather than probing for a guessed component name, because a
`HasComponent` that returns false is only evidence when the type name was right.

### A - the ability-group join: CLOSED, and it is a REFERENCE join

The name join is not viable and the number says why. Over 1474 `_AbilityGroup`
names: `_Cast` 1291, **`_Hit` 258**, `_Projectile` 177, `_Buff` 247. A join that
reaches 17 percent of the family is not a join.

The reference chain, read off the group's own component list:

```
_AbilityGroup
  -> DynamicBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>  .PrefabGUID
  -> the _Cast entity
  -> DynamicBuffer<ProjectM.AbilitySpawnPrefabOnCast>          .SpawnPrefab
  -> the entity carrying DealDamageOnGameplayEvent
  -> .Parameters.MainType
```

MEASURED over all 1474 groups: `withStartBuffer=1474`, `startElements=1664`,
`castResolved=1474`, `castWithSpawnBuffer=1371`, `spawnElements=1868`,
`reachedDealDamage=562`. A SECOND spawn hop adds exactly **0** more, so one hop
is the whole answer and the remaining 912 groups genuinely never deal damage
through this path.

### A2 - the school is NOT the damage type, and the schema meant the school

This is the correction that matters most in this section. `BRIDGE_SPIKES.md`
recorded "the ability school is `DealDamageParameters.MainType`". `MainType`'s
members are `Physical`, `Spell`, `Fire`, `Holy`, `Silver`, `Garlic`,
`RadialHoly`, `RadialGarlic`, `WeatherLightning`, `Corruption` - a DAMAGE type.
`abilities.school` is declared as blood, chaos, frost, illusion, storm, unholy or
weapon. They are different fields, and writing one into the other would have been
the fabricated `items.tier` mistake with a new name.

The real school join is on the SCHOOL asset, not the ability:

```
<School>SpellSchoolAsset prefab entity
  -> DynamicBuffer<ProjectM.SpellSchoolAbility>
  -> element .AbilityGroup   (PrefabGUID), plus .Tier and .MinDropLevel
```

`BloodSpellSchoolAsset`'s component list carries `ProjectM.SpellSchoolAbility`,
`ProjectM.SpellSchoolPassive` and `ProjectM.SpellPointPassiveProgression`, all
present on the SERVER host. The dump that followed emits **54 ability rows, 9 in
each of the six schools** - blood, chaos, frost, illusion, storm, unholy. An
even 9 across six independently-read buffers is itself a liveness signal.

What this does NOT cover, stated rather than hidden: weapon abilities have no
school asset and so produce no row, and only 16 of the 54 rows carry a
`damage_type`, because a spell whose projectile deals the damage is not reached
by the one measured hop. `damage_type` is OMITTED when unknown, never defaulted
to `Physical`, which is also the enum's zero value and therefore unreadable as
evidence.

### B - the V Blood level: `UnitLevel.Level`, and `Tier` was the wrong candidate

`ProjectM.VBloodConsumeSource.Tier` was the recorded level candidate. It is a
`ProjectM.SpellSchoolProgressionTier`, whose only members are `Undefined` and
`Tier1` to `Tier4`, and its measured distribution over the 65 V Bloods carrying
the component is `Tier1:23 Tier2:19 Tier3:13 Tier4:6 Undefined:4`. Five buckets
cannot be a boss level. It is the spell-school progression tier the boss grants.

The level is `ProjectM.UnitLevel.Level`, a `ModifiableInt`, read off the real
component list of `CHAR_Militia_HoundMaster_VBlood`. MEASURED: all 92
`VBloodUnit` prefabs carry it, range **16 to 91**, 33 distinct values.

The marker matters too. 92 prefabs carry `VBloodUnit` and only 65 carry
`VBloodConsumeSource`; the other 27 are templates such as
`GateBossComponentsTemplate_Major` (UnitLevel 85) that would have passed for
bosses. The dumper requires BOTH and emits 66 rows.

### C - blood type bonuses: shape MEASURED, magnitudes ABSENT

13 blood types. `PrimaryUnitBloodTypeBuffs` and `SecondaryUnitBloodTypeBuffs`
each carry ONE field, `BuffType` (a `PrefabGUID`), so the tier ORDER is the
buffer index and there is no quality-threshold field anywhere on the prefab. The
ordinary types carry 5 primary and 4 secondary entries; `BloodType_None` carries
0 and `BloodType_VBlood` and `BloodType_GateBoss` carry a single shared
`AB_BloodBuff_VBlood_0`.

Following `BuffType` one hop reaches a real `ModifyUnitStatBuff_DOTS` buffer with
real `StatType`s - `PhysicalCriticalStrikeChance`, `BonusMovementSpeed`,
`PhysicalLifeLeech` and so on - and **every `Value` on it measures 0** with
`SoftCapValue` 1. The magnitudes are scaled from blood quality at runtime and are
not on the prefab. So `blood_types` is writable as slot, tier, buff and stat
NAMES, and emitting those zeroes would have been a fabricated field.

A near miss worth recording: the first pass deep-dumped the first two blood
types, which are `BloodType_VBlood` and `BloodType_GateBoss`, both pointing at
the one buff that has NO stat buffer at all. That looked exactly like "blood
bonuses carry no stats". Naming two REAL types settled it.

CONSEQUENCE: `blood_types` goes to **`schema_version` 2**. The version 1 nested
contract in `core/table_deep.py` - a numeric `quality` threshold and a
name-to-number `stats` mapping, ascending by quality - was measured wrong on
both halves. The new contract is slot, 1-based tier, `buff_guid`, `buff_name`, a
`stats` list of `{stat, modification}` and a `value_source`, with tiers ascending
WITHIN a slot. A single global ascent check would reject the real row, which runs
primary 1..5 then secondary 1..4, and there is a regression test for exactly that.

### D - `recipes.station_guid`: CONFIRMED reverse-only, and one-to-many

`ProjectM.RecipeLinkBuffer` looked like the forward link and is NOT it. MEASURED:
5 of 667 recipes carry it, 56 links total, and every link resolves to ANOTHER
RECIPE - `Recipe_Ingredient_FakeGemDust` links 24 gem recipes. It is a
recipe-group alias, not a station reference.

The station side, measured over the whole world: **35 prefabs carry
`WorkstationRecipesBuffer` with 693 recipe references, and 23 carry
`RefinementstationRecipesBuffer` with 249**. 942 references over 663 recipes.

Two consequences, and the second is a schema question rather than a dumper one:

1. `station_guid` must be INVERTED at ingest time. Nothing on the recipe entity
   names a station.
2. It cannot be a single guid. A recipe appears at several stations -
   `TM_SpecialStation_PrisonCell` and `TM_SpecialStation_PrisonCell_StrongbladeDLC`
   share all 14 - and the crafting `User` prefab itself carries 29. The field
   stays OMITTED until that is settled; a first-station-wins value would be
   indistinguishable from a real one.

### E - the runtime localization join: MEASURED ABSENT on the server host

S7 recorded the runtime route as verified in metadata and INFERRED for two
things: that `ManagedItemData` is registered for all 425 equippables, and that
localization is initialized on a server host. Both are now measured, and the
answer is no.

Over all 425 equippables on the dedicated server:
`resolvedNonEmptyKey=0 resolvedEmptyKey=0 tryGetMissed=425 tryGetNullData=0
withoutLoggingHits=0`. `GameDataSystem` is present and non-null,
`ManagedDataRegistry` is present and non-null, and `TryGet<ManagedItemData>`
returns false for every one. The `TryGetWithoutLogging` overload was run as the
control and agrees, so this is not a logging-path refusal. `ManagedAbilityGroupData`
over 200 ability groups: 0 hits.

CONCLUSION: managed presentation data is not loaded in the dedicated server host.
`localization_guid` stays omitted from every table. Whether the CLIENT host
registers it is UNTESTED and is the natural next client-side measurement - it is
the same host question as the item COMPONENT diff.

### The dump that followed

Server host, `/dump/prefabs`, 714 ms, promoted by `rmdata_ingest --accept`:

| table | rows | schema_version |
|---|---|---|
| `items` | 425 | 3 |
| `recipes` | 663 | 1 |
| `abilities` | 54 | 1 |
| `vbloods` | 66 | 1 |
| `blood_types` | 13 | 2 |

`unmapped` is still the same 4 recipes with an empty item output buffer.

## Cycle 3 phase 1, 2026-07-26: the component inventory

Taken on the standalone dedicated server, build `1.1.13.0-r99712`, through the
new exploratory `GET /dump/components`. Payloads under `_scratch\rmprobe\c3\`,
not committed. Nothing below is recalled: every component and field name is read
off an enumerated type list of a real entity.

### What the endpoint reads, and the one thing it does NOT

It reads NAMES: the entity's complete component-type list, and for every
component the declared field list with types, nested value types expanded and
enum member names printed.

It does NOT read field VALUES, and that is a measured result rather than a
shortcut. Two generic value readers were built and both failed:

1. **Managed reflection** (`EntityManagerDebug.GetComponentBoxed`, then
   `Il2CppSystem.Type.GetFields` and `FieldInfo.GetValue`). Correct field names,
   GARBAGE VALUES: every `System.Int32` on every component of every entity read
   **539327184** and every `System.Single` read **1.402156E-19**. Not a
   plausible wrong number, the SAME number everywhere, which is the tell that
   the read hit a fixed location rather than the field.
2. **Raw il2cpp field offsets** off that same boxed pointer. It HARD CRASHED the
   dedicated server process on the first request, twice, which is the stronger
   form of the same finding: `GetComponentBoxed` does not hand back an object
   backed by the component's real chunk memory on this build, so there is
   nothing valid to point at. The raw `il2cpp_class_get_fields` iterator crashed
   the process as well, even reading metadata only.

**What caught failure 1 is a control that cost nothing.** Every entity carries
`Stunlock.Core.PrefabGUID`, whose value the same response ALREADY states from a
typed read. The generic reader said 539327184 where the truth was -327335305. A
value reader with no such control would have shipped, and every number in this
document would have been fiction. This is the `items.tier` failure mode caught
before it reached paper rather than after.

The consequence is scoped. Phase 1's gate asks for the inventory BY NAME, which
is what this is, and cycle 2 already proved that TYPED reads off a named
component work perfectly - that is how all five tables are populated. Values are
read the way they are read everywhere else here: with the type spelled out, now
that the inventory says which type to spell.

`ProjectM.ModifiableInt` and `ProjectM.ModifiableFloat` expand to `{}` under
`GetFields()`, so `_Value` is a PROPERTY rather than a field. Cycle 2 already
reads `UnitLevel.Level._Value` in `PrefabDumper.cs`, so this is a limit of the
reflection walk, not an absence.

### Subject 1: `CHAR_*_VBlood` prefabs, three across the level range

`CHAR_Forest_Wolf_VBlood` (level 16), `CHAR_Vampire_HighLord_VBlood` (57) and
`CHAR_Vampire_Dracula_VBlood` (91). **150 components each**, and the stat-bearing
ones are identical across all three, which is what makes one sample readable.

| Need | Component | Fields |
|---|---|---|
| max health | `ProjectM.Health` | `MaxHealth` (`ModifiableFloat`), `Value`, `MaxRecoveryHealth`, `TimeOfDeath`, `IsDead` |
| health rules | `ProjectM.HealthConstants` | `LowHealthFactor`, `DestroyOnDeath`, `DestroyAfterDuration`, `DisableDamageSCT` |
| level | `ProjectM.UnitLevel` | `Level` (`ModifiableInt`), `HideLevel` |
| the stat line | `ProjectM.UnitStats` | `PhysicalPower`, `SpellPower`, `ResourcePower`, `SiegePower`, `PhysicalResistance`, `SpellResistance`, `FireResistance`, `PassiveHealthRegen`, `CCReduction`, `HealthRecovery`, `DamageReduction`, `HealingReceived`, `ReducedBloodDrain`, `BloodDrainMultiplier`, `CorruptionDamageReduction` |
| resistance TUNING | `ProjectM.ResistanceData` | `SunResistance_IncreasedSunPiercingDuration`, `GarlicResistance_DamageReductionPerRating`, `GarlicResistance_IncreasedExposureFactorPerRating`, `GarlicResistance_ReduceMaxStacksPerRating`, `FireResistance_DamageReductionPerRating`, `FireResistance_RedcuedIgiteChancePerRating`, `SilverResistance_DamageReductionPerRating`, `SilverResistance_CarryValueAbsorbedPerRating`, `HolyResistance_DamageReductionPerRating`, `HolyResistance_DamageAbsorbPerRating`, `PvPResilience_DamageReductionPerRating` |
| V Blood identity | `ProjectM.VBloodUnit`, `ProjectM.VBloodConsumeSource`, `ProjectM.VBloodUnlockTechBuffer` (buffer) | as cycle 2 |

`ProjectM.ResistanceData` is a COEFFICIENT block, not a per-boss resistance
vector: every field is a "per rating" conversion rate. The per-unit resistance
values are on `UnitStats`.

**The four anti-vampire damage types have no unit-side resistance field.** Across
all 150 enumerated components on all three bosses there is no Holy, Silver,
Garlic or Sun resistance member outside `ResistanceData`'s per-rating rates.
Physical, Spell, Fire and Corruption each have one on `UnitStats`. That is a full
enumeration rather than a failed `HasComponent`, so the absence is readable.

### Subject 2: ability groups, four across schools plus a weapon group

`AB_Blood_BloodRite_AbilityGroup` (34 components), `AB_Frost_CrystalLance_AbilityGroup`,
`AB_Storm_LightningWall_AbilityGroup`, and the WEAPON group
`AB_Spear_AThousandSpears_Stab_AbilityGroup` (32 components).

**The weapon and spell groups are told apart by a component, not by a name.**

| Component | On | Fields |
|---|---|---|
| `ProjectM.WeaponAbilityData` | weapon groups only | `AbilityType` (enum `Primary,Secondary,Travel,Dash,Power,Offensive,SpellSlot1,Defensive,SpellSlot2,Ultimate,None`) |
| `ProjectM.VBloodAbilityData` | spell groups | `AbilityType`, `AbilitySchool` (enum `Blood,Unholy,Illusion,Frost,Chaos,Storm,Shadow`), `AbilityTooltipType` |
| `ProjectM.AbilitySpellSchool` | spell groups | `SpellSchool` (`PrefabGUID`), `Tier` (`SpellSchoolProgressionTier`) |
| `ProjectM.AbilityGroupInfo` | both | `MinRange`, `MaxRange`, `BehaviorType`, `InputType`, `Target`, `ReleaseCastQueueTime`, `CastCondition`, `HoverCondition` |
| `ProjectM.AbilityGroupStartAbilitiesBuffer` | both, buffer | the cycle 2 chain head |

**`ProjectM.AbilitySpellSchool` CORRECTS a cycle 2 statement.** Cycle 2 recorded
"there is no `SpellSchool` component type" and joined the school through the
`<School>SpellSchoolAsset` prefab's `SpellSchoolAbility` buffer instead. The
component does exist, sitting on the ability GROUP, and it carries both the
school guid and the progression tier. The cycle 2 join is not wrong and its 54
rows stand; it was reached by metadata scans that missed this type, and a live
component list found it in one run. Same shape as the `EquippableData` correction.

`ProjectM.VBloodAbilityData.AbilitySchool` is a second, independent school source
and its enum carries `Shadow`, which the six-school join cannot produce.

### Subject 3: the `_Cast` and `_Hit` entities, where the coefficients live

`AB_Spear_AThousandSpears_Stab_Cast`, 36 components:

| Need | Component | Fields |
|---|---|---|
| cast time | `ProjectM.AbilityCastTimeData` | `MaxCastTime` (`ModifiableFloat`), `PostCastTime`, `HideCastBar` |
| cooldown | `ProjectM.AbilityCooldownData` | `Cooldown` (`ModifiableFloat`), `IgnoreCooldownModifier`, `ShowInteractCooldownHUD` |
| global cooldown | `ProjectM.GlobalCooldown` | `Value` (`Single`) |
| the next hop | `ProjectM.AbilitySpawnPrefabOnCast` (buffer) | the cycle 2 chain |

`AB_Spear_AThousandSpears_Stab_Hit`, 51 components:

| Need | Component | Fields |
|---|---|---|
| coefficient and type | `ProjectM.DealDamageOnGameplayEvent` (buffer) | `Parameters` (`DealDamageParameters`), `DamageModifierPerHit`, `MultiplyMainFactorWithStacks` |
| inside `Parameters` | `ProjectM.DealDamageParameters` | `MainFactor`, `RawDamageValue`, `RawDamagePercent`, `MainType`, `StaggerFactor`, `ResourceModifier`, `MaterialModifiers`, `DealDamageFlags` |
| hit multiplicity | `ProjectM.HitTrigger`, `ProjectM.CreateGameplayEventsOnHit`, `ProjectM.HitColliderCast`, `ProjectM.TriggerHitConsume` (all buffers) | lengths not counted this phase |

### Subject 4: weapon items, two families, and the L1 hop CLOSED

`Item_Weapon_GreatSword_T06_Iron_Reinforced` and
`Item_Weapon_Spear_T06_Iron_Reinforced`, 30 components each. The item itself
carries NO ability reference. The chain, every hop read off an enumerated
component list:

```
weapon item prefab
  -> ProjectM.EquippableData.BuffGuid          (PrefabGUID)
  -> EquipBuff_Weapon_<Family>_Base            (26 components)
  -> DynamicBuffer<ProjectM.ReplaceAbilityOnSlotBuff>
  -> element .NewGroupId                       (PrefabGUID) = the ability GROUP
     element .Slot                             (Int32)      = the ability bar slot
```

`ProjectM.ReplaceAbilityOnSlotBuff` also carries `Target`, `ReplaceGroupId`,
`Priority`, `Condition`, `CastBlockType` and `CopyCooldown`. The equip buff
additionally carries `ProjectM.WeaponLevel` and the item carries
`ProjectM.WeaponLevelSource`, which are the P2 candidates.

This is the L1 asymmetry the spec warned about, holding up exactly as stated:
`EquippableData.BuffGuid` is barred as a route to item STATS, because
`ModifyUnitStatBuff_DOTS` sits on the item prefab itself and cycle 2 settled
that. For ABILITIES the equip buff is the only route, and it is the right one.

### Subject 5: the LIVE INSTANCED boss, and the liveness assertion

`CHAR_Vampire_Dracula_VBlood` exists as a spawned entity in `world1` on the
dedicated server. The stub-proof assertion the spec asks for HOLDS:

| | prefab | live instance |
|---|---|---|
| entity index | 29012 | **322916** |
| `Unity.Entities.Prefab` | present | **absent** |
| components | 150 | 151 |

Instance-only: `ProjectM.AttachParentId`, `ProjectM.AttachedBuffer`,
`ProjectM.DisabledDueToNoPlayersInRange`, `Unity.Entities.Disabled`.
Prefab-only: `Unity.Entities.Prefab`, `Unity.Entities.SpawnTag`,
`ProjectM.Pathfinding.PathRequestSolveDebugBuffer`.

**Every stat-bearing component is on BOTH.** `Health`, `UnitLevel`, `UnitStats`
and `ResistanceData` are present on the instance and on the prefab, so the
prefab-versus-instance control of phase 3 has a real subject on both sides and
can be a value comparison rather than a presence check. The two entities differ
only in spawn, attachment and disabled-state machinery, which is what an
unvisited boss should look like.

### The 14 required fields, phase 1 verdict

Named per the spec's closure rule. SOURCED means the component and field are
named here; VALUES are phase 2 and are read with typed accessors.

| id | field | state | source |
|---|---|---|---|
| T1 | boss max health | SOURCED | `ProjectM.Health.MaxHealth` |
| T2 | resistance per damage type | SOURCED for 4 of 7, PROVEN ABSENT for 3 | `UnitStats.PhysicalResistance` / `.SpellResistance` / `.FireResistance` / `.CorruptionDamageReduction`; Holy, Silver and Garlic have no unit-side field across 150 enumerated components |
| T3 | boss unit level | SOURCED | `ProjectM.UnitLevel.Level` |
| T4 | target-side diff input | SOURCED as candidates | `UnitLevel.Level`, `UnitStats.PhysicalPower` / `.SpellPower` |
| A1 | cast time | SOURCED | `AbilityCastTimeData.MaxCastTime`, `.PostCastTime` |
| A2 | cooldown | SOURCED | `AbilityCooldownData.Cooldown`, `GlobalCooldown.Value` |
| A3 | damage coefficient | SOURCED | `DealDamageParameters.MainFactor`, `.RawDamageValue`, `.RawDamagePercent` |
| A4 | damage type | SOURCED | `DealDamageParameters.MainType` |
| A5 | which power stat | PROVEN ABSENT as a field | no power-selector member on the `_Hit` entity's 51 components; `MainType` is the only discriminator present |
| A6 | hits per cast | PARTIAL | `DealDamageOnGameplayEvent.DamageModifierPerHit`, `.MultiplyMainFactorWithStacks`; multiplicity is buffer LENGTHS, not yet counted |
| P1 | weapon power | SOURCED, cycle 2 | `DynamicBuffer<ModifyUnitStatBuff_DOTS>` on the item prefab |
| P2 | player-side diff input | SOURCED as candidates | `WeaponLevelSource` on the item, `WeaponLevel` on the equip buff, `UnitStats` on the character |
| L1 | weapon to ability group | SOURCED | the four-hop chain above, ending at `ReplaceAbilityOnSlotBuff.NewGroupId` |
| L2 | group to coefficients | SOURCED | cycle 2's chain, with the payload fields now named under subject 3 |

NOT ATTEMPTED is EMPTY. A6 is the only partial and it is a counting job, not a
hunt.

## Tooling note

The spike tool is `_scratch\typedump\`, a throwaway net8.0 console app that
reads the interop assemblies with `System.Reflection.Metadata` and reports type
names, fields and methods. It is deliberately NOT committed - it is scratch, it
is regenerable, and it must not become a second thing to maintain per patch.
Recreate it if another metadata question comes up.

## The client-host pass, 2026-07-26: the join that only exists on one host

Everything below was measured in ONE session with both hosts live at once - the
standalone dedicated server on 8780 and the operator's client on 8777 - running
the SAME plugin binary. That concurrency is the ADR-005 payoff used rather than
argued, and it is what makes the comparisons like-for-like.

### The client item COMPONENT diff: CLOSED, they are IDENTICAL

The open question was whether client item component data matches the server's.
Only the prefab MAPS had ever been compared, and matching COUNTS are not an
answer - two 425-row tables can disagree on every field.

Both dumps were taken minutes apart from the same binary and diffed ROW BY ROW,
keyed on `prefab_guid`, every field compared:

| table | server | client | shared rows differing |
|---|---|---|---|
| `items` | 425 | 425 | **0** |
| `recipes` | 663 | 663 | **0** |
| `abilities` | 54 | 54 | **0** |
| `vbloods` | 65 | 65 | **0** |
| `blood_types` | 13 | 13 | **0** |

Zero differing rows across all five tables, on every field except
`localization_guid`, which was held out because it is the one field the two hosts
were expected to disagree on. The client dump costs 103 ms against the server's
794. Either host may serve the table dump and cycle 3 need not care which did.

### S7 and section E OVERTURNED on the client: the join resolves 425 of 425

The runtime localization join was recorded as MEASURED ABSENT. That measurement
was correct and it was HOST-SPECIFIC, which nobody had checked:

| host | registry | attempted | resolved | missed | quiet_hits |
|---|---|---|---|---|---|
| dedicated server | present | 425 | **0** | 425 | 0 |
| client | present | 425 | **425** | 0 | 0 |

`GameDataSystem.ManagedDataRegistry.TryGet<ManagedItemData>` returns false for
every equippable in the headless host and true for every one in the client. The
route is exactly the one S7 read out of the interop metadata, unchanged:

```
GameDataSystem -> ManagedDataRegistry -> TryGet<ManagedItemData>(PrefabGUID)
  -> .Name (Stunlock.Localization.LocalizationKey) -> .Key.ToGuid().ToString()
```

And the guids are not merely present, they JOIN: **425 of 425 client
`localization_guid` values are keys in `strings.json`**, resolving to real
display names - `Item_Headgear_WolfTrophy01` to "Wolf Head",
`Item_Headgear_PopeMitre` to "Mitre". 342 distinct guids over 425 rows, because
skins share a display name. Compare the best offline heuristic, 53 of 425.

CONSEQUENCE: `localization_guid` is WRITABLE, on the client host only. The
counters now ride inside every dump as its `localization` block and
`tools/rmdata_ingest.py` prints them, so a saved payload states for itself which
host produced it and whether the field was writable there. The earlier absence
stands as a true statement about the dedicated server and was never a statement
about the build.

### The duplicate rows: a wrong number that four gates could not see

Diffing by `prefab_guid` surfaced a defect nothing else had. MEASURED on BOTH
hosts: `abilities` emitted **56 rows over 54 distinct guids** -
`AB_Blood_BloodRite_AbilityGroup` and `AB_Blood_Shadowbolt_AbilityGroup` twice
each - and the SERVER emitted **66 vblood rows over 65 distinct**, with
`CHAR_Vampire_Dracula_VBlood` twice.

More than one entity can carry the same `PrefabGUID`, so a straight pass over
`GetAllEntities` writes the row once per entity. Every duplicate pair was
BYTE-IDENTICAL, which is why it survived: the shallow gate, the deep nested gate,
the schema and the census all inspect rows one at a time, and each of those rows
was individually perfect. The only symptom was the COUNT.

**`vbloods` is 65, not 66.** The 66 recorded in `ROADMAP.md` and ledger 002e was
65 real V Bloods plus a duplicated Dracula. It is corrected there.

Two fixes, because the defect has two homes. `PrefabDumper.cs` dedupes every
table on first write - with the marker component tested BEFORE the set insert,
since `&&` short-circuits and an insert placed first would claim the guid on
behalf of entities that are not rows of that table at all. And
`tools/rmdata_ingest.py` gained `duplicate_key_problems`, a cross-ROW gate that
refuses the whole ingest, because the producer being fixed today is not the same
as the defect being detectable tomorrow.

Verified after the fix, both hosts: 425 / 663 / 54 / 65 / 13, zero duplicates.

### `recipes.station_guids`: RULED and WRITABLE, ADR-006

The singular `station_guid` was measured unrepresentable and is replaced by a
plural array at `recipes` `schema_version` 2. The full reasoning is ADR-006; the
numbers are the reverse-only, one-to-many result already recorded in section D.

The inversion runs in the DUMPER, which already walks the whole world for the
school index. MEASURED live over both hosts, identically:

```
663 recipes, 575 reachable from at least one station, 88 from none
911 unique (recipe, station) pairs emitted from 942 raw buffer references
stations per recipe: 0->88  1->437  2->113  3->4  4->2  12->19
```

That histogram is the ruling's whole justification standing up in the data: a
first-station-wins value would have been arbitrary for **138 recipes**, and
wrong-by-a-factor-of-twelve for 19 of them. The 88 empty lists are emitted as
`[]` rather than omitted, so "reachable from no station" stays distinguishable
from "the inversion did not run".

### `Unload()`: the graceful path is still UNOBSERVED, and now it is observABLE

MEASURED, twice, on a normal in-game quit of the client: `BepInEx\LogOutput.log`
gains NOTHING after `Chainloader startup complete`. No shutdown line from the
plugin and none from BepInEx itself.

That is not yet an answer, and the reason is the point. `Unload()` logged nothing
at all, so a silent log was consistent with "Unload ran fine" and with "Unload
never ran" and with "the logging pipeline was torn down first". A zero that three
hypotheses predict equally is not evidence - the same shape as the `items.tier`
zero and the `ShadowVBloodUnitTagComponent` zero.

`Unload()` now does two things: it logs, and it appends a timestamped line to
`BepInEx\redmoon-unload.log` through `File.AppendAllText`, OUTSIDE BepInEx's
logging pipeline. The file is the observation that does not depend on the thing
being observed. If the marker appears, Unload ran; if only the marker appears and
not the log line, the pipeline was already gone; if neither appears, Unload does
not run on a normal exit. Three hypotheses, three distinguishable outcomes.

### `Unload()`: CLOSED. It does NOT run on a normal exit.

The instrumented build was loaded and the operator quit through the in-game
menu. Result:

```
BepInEx\redmoon-unload.log   ABSENT
LogOutput.log                unchanged after "Chainloader startup complete"
port 8777                    no LISTEN
```

The control that makes this silence readable: the observed client run is
PROVABLY the instrumented one, because the dump it served carried
`station_guids`, a field that exists only in that build. This is not a stale
binary reporting nothing.

Both channels are silent and they fail INDEPENDENTLY - one goes through
BepInEx's logger, the other through `File.AppendAllText` - which eliminates "the
logging pipeline was torn down first". **BepInEx 6 IL2CPP does not invoke
`BasePlugin.Unload()` on process shutdown on this build.** The listener socket is
released by process termination instead.

CONSEQUENCE, and it is benign: the graceful path does not exist here and nothing
depends on it. R11 already measured the hard-kill case - after `taskkill /F`,
port 8780 held no LISTEN and `bridge_probe --expect-unreachable` PASSED - and a
normal exit is now measured to take that identical path. `Unload()` stays
implemented and instrumented, so a future BepInEx that does call it will be
observed rather than assumed.

### `abilities` coverage, stated rather than left implied

54 rows, 9 in each of the six spell schools, and the shape of what is missing is
known rather than suspected:

- **Weapon abilities produce no row at all.** The school comes from the
  `<School>SpellSchoolAsset` prefab's `SpellSchoolAbility` buffer, and there is
  no weapon school asset. `abilities.school` declares `weapon` as a legal value
  and nothing on this build can source it.
- **38 of 54 rows carry no `damage_type`.** The one measured hop reaches
  `DealDamageOnGameplayEvent` for 562 of 1474 ability groups; a spell whose
  PROJECTILE deals the damage is not reached, and a second spawn hop was measured
  to add exactly 0. `damage_type` is OMITTED for those 38, never defaulted to
  `Physical` - which is also the enum's zero value and therefore unreadable as
  evidence.

Neither is a defect to fix by widening the join. Both are the honest edge of a
measured chain, and cycle 3 must treat `abilities` as covering spell-school
abilities only.

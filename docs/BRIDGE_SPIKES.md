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
dumper and for the localization join.

## Tooling note

The spike tool is `_scratch\typedump\`, a throwaway net8.0 console app that
reads the interop assemblies with `System.Reflection.Metadata` and reports type
names, fields and methods. It is deliberately NOT committed - it is scratch, it
is regenerable, and it must not become a second thing to maintain per patch.
Recreate it if another metadata question comes up.

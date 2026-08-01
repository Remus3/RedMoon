// Prefab collection -> table rows. MAIN THREAD ONLY (spec decision D7).
//
// Everything here reads ECS, so every entry point is called from the injected
// MonoBehaviour tick in Plugin.cs and never from the listener thread.
//
// What this file may emit is bounded by what was MEASURED against build
// 1.1.13.0-r99712 (docs/BRIDGE_SPIKES.md). All five schemas are now writable:
// the ability school is SpellSchoolAbility.AbilityGroup on the
// <School>SpellSchoolAsset prefab (NOT DealDamageParameters.MainType, which is
// the damage type), the V Blood level is UnitLevel.Level (NOT
// VBloodConsumeSource.Tier, which has five members and cannot be a level), and
// the blood bonus tiers are the two UnitBloodTypeBuffs buffers. Fields with no
// measured source - items.tier, and localization_guid on a host whose registry
// does not resolve - are OMITTED, never defaulted.
//
// Three measured traps are encoded here rather than commented around:
//
//  1. READINESS. The prefab map fills in over about 1.7 s, climbing
//     1189 -> 3212 -> 11760 -> 17400 -> 23583, and GameDataInitialized flips
//     False to True exactly as it settles. A dump taken on first non-zero count
//     returns a castle-asset subset and LOOKS complete. Every dump is gated on
//     GameDataInitialized.
//  2. WORLD SELECTION IS BY NAME. "Default World" is a Simulation world sitting
//     at index 0 in both hosts and it THROWS when asked for the prefab map, so
//     "first Simulation world" is a wrong rule that happens to be plausible.
//  3. PREFAB GUIDS REPEAT ACROSS ENTITIES. More than one entity can carry the
//     same PrefabGUID, so a straight pass over GetAllEntities emits the same
//     row twice. MEASURED on both hosts: 56 ability rows over 54 guids, and 66
//     vblood rows over 65 on the server. The duplicate rows were IDENTICAL, so
//     the only symptom was a wrong count - and that count had already been
//     written down as a finding. Every table dedupes on first write.
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text;
using Unity.Collections;
using Unity.Entities;

namespace RedMoon.Bridge
{
    /// <summary>What the dumper can see right now. Produced on the main thread.</summary>
    internal sealed class WorldStatus
    {
        internal string[] WorldNames = new string[0];
        internal string TargetName = "";
        internal bool Ready;
        internal int PrefabCount = -1;
    }

    internal static class PrefabDumper
    {
        /// <summary>
        /// The prefab-carrying world in each host, BY NAME. MEASURED: the server
        /// host has "Server" and the in-game client host has "Client_0". Neither
        /// index nor world flags identify it - see the header note.
        /// </summary>
        internal static readonly string[] TargetWorldNames = { "Server", "Client_0" };

        /// <summary>The tables mapped against this build.</summary>
        internal static readonly string[] WritableTables =
        {
            "items", "recipes", "abilities", "vbloods", "blood_types", "ability_stats"
        };

        /// <summary>
        /// The suffix every spell school asset prefab carries. MEASURED: 11
        /// prefab names contain "SpellSchool" and the school assets are exactly
        /// "&lt;School&gt;SpellSchoolAsset". This is an ASSET IDENTIFIER, not a
        /// semantic parsed out of a name token - the join itself is the
        /// SpellSchoolAbility buffer on that asset's own entity.
        /// </summary>
        private const string SchoolAssetSuffix = "SpellSchoolAsset";

        internal const string ErrorWorldNotReady = "world_not_ready";

        internal const string NotReadyMessage =
            "game world is not loaded yet, retrying";

        internal static bool IsWritable(string table)
        {
            for (int i = 0; i < WritableTables.Length; i++)
            {
                if (WritableTables[i] == table)
                {
                    return true;
                }
            }

            return false;
        }

        // -------------------------------------------------------------------
        // world selection and readiness
        // -------------------------------------------------------------------
        internal static WorldStatus Status()
        {
            var status = new WorldStatus();
            var all = World.All;

            var names = new string[all.Count];
            for (int i = 0; i < all.Count; i++)
            {
                names[i] = all[i].Name;
            }

            status.WorldNames = names;

            World target = FindTarget();
            if (target == null)
            {
                return status;
            }

            status.TargetName = target.Name;

            Stunlock.Core.PrefabLookupMap map;
            if (!TryGetMap(target, out map))
            {
                return status;
            }

            try
            {
                status.PrefabCount = map.Count();
            }
            catch (Exception)
            {
                status.PrefabCount = -1;
            }

            status.Ready = IsReady(map);
            return status;
        }

        private static World FindTarget()
        {
            var all = World.All;
            for (int t = 0; t < TargetWorldNames.Length; t++)
            {
                for (int i = 0; i < all.Count; i++)
                {
                    World world = all[i];
                    if (world != null && world.IsCreated && world.Name == TargetWorldNames[t])
                    {
                        return world;
                    }
                }
            }

            return null;
        }

        private static bool TryGetMap(World world, out Stunlock.Core.PrefabLookupMap map)
        {
            try
            {
                map = ProjectM.PrefabCollectionSystem.GetPrefabLookupMap(world);
                return map.IsCreated;
            }
            catch (Exception)
            {
                // "Default World" throws ArgumentException here and a streaming
                // world throws InvalidOperationException. Both mean "not the
                // prefab world", which is a routine answer, not a fault.
                map = default(Stunlock.Core.PrefabLookupMap);
                return false;
            }
        }

        /// <summary>
        /// World selection, shared with the exploratory ComponentDumper so the
        /// two cannot drift apart on the by-name rule. See trap 2 in the header:
        /// "first Simulation world" is a wrong rule that happens to be plausible.
        /// </summary>
        internal static World FindTargetWorld()
        {
            return FindTarget();
        }

        /// <summary>
        /// The prefab map, but only once GameDataInitialized has flipped. One
        /// entry point rather than two so no caller can accidentally skip the
        /// readiness gate and take a castle-asset subset (trap 1).
        /// </summary>
        internal static bool TryGetReadyMap(World world, out Stunlock.Core.PrefabLookupMap map)
        {
            return TryGetMap(world, out map) && IsReady(map);
        }

        private static bool IsReady(Stunlock.Core.PrefabLookupMap map)
        {
            try
            {
                return map.GameDataInitialized.Value;
            }
            catch (Exception)
            {
                return false;
            }
        }

        // -------------------------------------------------------------------
        // the dump
        // -------------------------------------------------------------------
        /// <summary>
        /// Build the /dump/prefabs body. Returns null when the world is not
        /// ready, and the caller answers with the world_not_ready envelope.
        /// `table` narrows to one table; null or empty means every writable one.
        /// </summary>
        internal static string Dump(string build, string plugin, string table)
        {
            World target = FindTarget();
            if (target == null)
            {
                return null;
            }

            Stunlock.Core.PrefabLookupMap map;
            if (!TryGetMap(target, out map) || !IsReady(map))
            {
                return null;
            }

            bool wantItems = string.IsNullOrEmpty(table) || table == "items";
            bool wantRecipes = string.IsNullOrEmpty(table) || table == "recipes";
            bool wantAbilities = string.IsNullOrEmpty(table) || table == "abilities";
            bool wantVbloods = string.IsNullOrEmpty(table) || table == "vbloods";
            bool wantBloodTypes = string.IsNullOrEmpty(table) || table == "blood_types";
            bool wantAbilityStats = string.IsNullOrEmpty(table) || table == "ability_stats";

            var watch = Stopwatch.StartNew();
            var items = new StringBuilder();
            var recipes = new StringBuilder();
            var abilities = new StringBuilder();
            var vbloods = new StringBuilder();
            var bloodTypes = new StringBuilder();
            var abilityStats = new StringBuilder();
            var unmapped = new StringBuilder();
            int itemCount = 0;
            int recipeCount = 0;
            int abilityCount = 0;
            int vbloodCount = 0;
            int bloodTypeCount = 0;
            int abilityStatCount = 0;
            int unmappedCount = 0;

            // prefab_guid is the join key, and the world can hold MORE THAN ONE
            // entity carrying the same one. MEASURED 2026-07-26 on both hosts:
            // AB_Blood_BloodRite_AbilityGroup and AB_Blood_Shadowbolt_AbilityGroup
            // each appeared twice (56 rows over 54 guids), and the SERVER also
            // held CHAR_Vampire_Dracula_VBlood twice (66 rows over 65). Every
            // duplicate pair was byte-identical, so no per-row gate could see it
            // and the only symptom was a wrong COUNT - one that had already been
            // written into ROADMAP.md as the V Blood total.
            //
            // First write wins. The rows were identical, so which one wins does
            // not matter; that they are counted once does.
            //
            // ORDER MATTERS in the guards below: the marker component is tested
            // BEFORE Add, never after. && short-circuits left to right, so an
            // Add placed first would claim the guid on behalf of every entity
            // carrying it - including ones that are not rows of that table at
            // all - and then reject the real row when it came along later.
            var seenItems = new HashSet<int>();
            var seenRecipes = new HashSet<int>();
            var seenAbilities = new HashSet<int>();
            var seenVbloods = new HashSet<int>();
            var seenBloodTypes = new HashSet<int>();
            var seenAbilityStats = new HashSet<int>();

            // Opened once per dump, never per row: the registry handle is the
            // expensive part and the counters must accumulate across the pass.
            LocalizationJoin localization = LocalizationJoin.Open(target);

            EntityManager em = target.EntityManager;
            NativeArray<Entity> all = em.GetAllEntities(Allocator.Temp);

            // The school index must exist before the first ability row, so it
            // gets its own pass. A second full pass is affordable: the whole
            // dump measures 57 ms for 47573 entities.
            var schools = wantAbilities
                ? BuildSchoolIndex(em, map, all)
                : new Dictionary<int, string>();

            // ADR-006. Same shape of work as the school index and for the same
            // reason: the link runs from the STATION to the recipe, so a recipe
            // row cannot be written until the whole world has been walked once.
            var stations = wantRecipes
                ? BuildStationIndex(em, all)
                : new Dictionary<int, List<int>>();

            for (int i = 0; i < all.Length; i++)
            {
                Entity e = all[i];

                Stunlock.Core.PrefabGUID guid;
                try
                {
                    if (!em.HasComponent<Stunlock.Core.PrefabGUID>(e))
                    {
                        continue;
                    }

                    guid = em.GetComponentData<Stunlock.Core.PrefabGUID>(e);
                }
                catch (Exception)
                {
                    continue;
                }

                if (wantItems && Has<ProjectM.EquippableData>(em, e)
                    && seenItems.Add(guid.GuidHash))
                {
                    if (TryWriteItem(items, itemCount, em, map, e, guid, localization))
                    {
                        itemCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid,
                                      "equippable prefab whose components could not be read");
                        unmappedCount++;
                    }
                }

                if (wantRecipes && Has<ProjectM.RecipeData>(em, e)
                    && seenRecipes.Add(guid.GuidHash))
                {
                    string reason;
                    if (TryWriteRecipe(recipes, recipeCount, em, e, guid, stations, out reason))
                    {
                        recipeCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid, reason);
                        unmappedCount++;
                    }
                }

                // An ability row needs a school, which the schema requires. A
                // group the school index does not name is not a defective row,
                // it is a weapon or creature ability outside the six schools, so
                // it is skipped rather than reported as unmapped.
                if (wantAbilities && schools.ContainsKey(guid.GuidHash)
                    && seenAbilities.Add(guid.GuidHash))
                {
                    if (TryWriteAbility(abilities, abilityCount, em, map, e, guid,
                                        schools[guid.GuidHash]))
                    {
                        abilityCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid,
                                      "spell school ability whose components could not be read");
                        unmappedCount++;
                    }
                }

                // MEASURED: 92 prefabs carry VBloodUnit and only 65 carry
                // VBloodConsumeSource. The other 27 are templates such as
                // GateBossComponentsTemplate_Major, which have a UnitLevel and
                // would look exactly like a boss row.
                // THE PREFAB MARKER IS PART OF THE SELECTOR, cycle 3 phase 3.
                // A spawned boss carries the SAME PrefabGUID as its prefab, so
                // without this test the row was whichever of the two the world
                // walk reached first - and the two do NOT agree. MEASURED on
                // CHAR_Vampire_Dracula_VBlood: 19 fields compared, 17 identical,
                // and Health.MaxHealth reading 0 on the prefab against 8107 on
                // the live instance. Cycle 2 saw the same pair as "66 vblood
                // rows over 65 distinct" and fixed the COUNT by deduping, which
                // silently made the choice order-dependent instead.
                //
                // The PREFAB is the deliberate pick: it exists whether or not a
                // boss has spawned, so the dump stays repeatable and
                // host-independent. The price is max_health, which is
                // instance-only and is therefore OMITTED rather than written as
                // the prefab's 0.
                if (wantVbloods && Has<ProjectM.VBloodUnit>(em, e)
                    && Has<ProjectM.VBloodConsumeSource>(em, e)
                    && ComponentDumper.CarriesPrefabMarker(em, e)
                    && seenVbloods.Add(guid.GuidHash))
                {
                    string reason;
                    if (TryWriteVBlood(vbloods, vbloodCount, em, map, e, guid, out reason))
                    {
                        vbloodCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid, reason);
                        unmappedCount++;
                    }
                }

                // Selected by marker component, never by the BloodType_ name
                // prefix: HasBuffer is a fact, a prefix is a guess about
                // Stunlock's conventions.
                if (wantBloodTypes && HasBuffer<ProjectM.Shared.PrimaryUnitBloodTypeBuffs>(em, e)
                    && seenBloodTypes.Add(guid.GuidHash))
                {
                    if (TryWriteBloodType(bloodTypes, bloodTypeCount, em, map, e, guid))
                    {
                        bloodTypeCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid,
                                      "blood type prefab whose bonus buffers could not be read");
                        unmappedCount++;
                    }
                }

                // ADR-007: the coefficient key space is the ability GROUP. The
                // marker is AbilityGroupStartAbilitiesBuffer, which is what
                // MAKES an entity a group - cycle 2 measured it resolving a cast
                // for 1474 of 1474 groups. Deliberately NOT the school index the
                // abilities table uses: that index covers spell-school groups
                // only, and a weapon group has no school asset to be named by.
                // Selecting on the school here would reproduce ROADMAP cycle 3
                // gap 3 inside the table built to dissolve it.
                if (wantAbilityStats && HasBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>(em, e)
                    && seenAbilityStats.Add(guid.GuidHash))
                {
                    if (TryWriteAbilityStats(abilityStats, abilityStatCount, em, map, e, guid))
                    {
                        abilityStatCount++;
                    }
                    else
                    {
                        WriteUnmapped(unmapped, unmappedCount, guid,
                                      "ability group whose name could not be read");
                        unmappedCount++;
                    }
                }
            }

            watch.Stop();

            var body = new StringBuilder(items.Length + recipes.Length + 512);
            body.Append("{\"ok\":true,\"build\":").Append(Json.Str(build));
            body.Append(",\"plugin\":").Append(Json.Str(plugin));
            body.Append(",\"captured_at\":").Append(Json.Str(Json.UtcNow()));
            body.Append(",\"elapsed_ms\":").Append(watch.ElapsedMilliseconds);
            body.Append(",\"counts\":{");
            body.Append("\"items\":").Append(itemCount);
            body.Append(",\"recipes\":").Append(recipeCount);
            body.Append(",\"abilities\":").Append(abilityCount);
            body.Append(",\"vbloods\":").Append(vbloodCount);
            body.Append(",\"blood_types\":").Append(bloodTypeCount);
            body.Append(",\"ability_stats\":").Append(abilityStatCount);
            body.Append("},\"tables\":{");
            body.Append("\"items\":[").Append(items).Append(']');
            body.Append(",\"recipes\":[").Append(recipes).Append(']');
            body.Append(",\"abilities\":[").Append(abilities).Append(']');
            body.Append(",\"vbloods\":[").Append(vbloods).Append(']');
            body.Append(",\"blood_types\":[").Append(bloodTypes).Append(']');
            body.Append(",\"ability_stats\":[").Append(abilityStats).Append(']');
            body.Append("},\"unmapped\":[").Append(unmapped).Append(']');

            // Emitted on EVERY dump, including one that resolved nothing. A
            // measured zero is a result; a MISSING block is a dumper that owes
            // the measurement, and tools/rmdata_ingest.py reports the two
            // differently on purpose.
            body.Append(",\"localization\":");
            localization.Write(body);
            body.Append('}');
            return body.ToString();
        }

        private static bool Has<T>(EntityManager em, Entity e)
        {
            try
            {
                return em.HasComponent<T>(e);
            }
            catch (Exception)
            {
                return false;
            }
        }

        private static bool HasBuffer<T>(EntityManager em, Entity e) where T : unmanaged
        {
            try
            {
                return em.HasBuffer<T>(e);
            }
            catch (Exception)
            {
                return false;
            }
        }

        // -------------------------------------------------------------------
        // the station index
        // -------------------------------------------------------------------
        /// <summary>
        /// Recipe PrefabGUID hash to the sorted, deduplicated list of station
        /// PrefabGUID hashes that can run it. ADR-006.
        ///
        /// This index exists because the reference runs the WRONG WAY for a
        /// per-recipe read. Nothing on a recipe entity names a station, and the
        /// forward-looking candidate was checked and rejected: MEASURED, only 5
        /// of 667 recipes carry ProjectM.RecipeLinkBuffer, its 56 links every one
        /// resolve to another RECIPE rather than a station, and
        /// Recipe_Ingredient_FakeGemDust alone links 24 gem recipes. It is a
        /// recipe-group alias.
        ///
        /// The real links are the two station-side buffers. MEASURED over the
        /// whole world: 35 prefabs carry WorkstationRecipesBuffer with 693 recipe
        /// references and 23 carry RefinementstationRecipesBuffer with 249, which
        /// is 942 references over 663 recipes - so the relation is ONE-TO-MANY
        /// and the schema's old singular station_guid could not hold it.
        ///
        /// The two buffer types feed one list undifferentiated, per ADR-006
        /// decision 4.
        /// </summary>
        private static Dictionary<int, List<int>> BuildStationIndex(
            EntityManager em, NativeArray<Entity> all)
        {
            var index = new Dictionary<int, List<int>>();

            for (int i = 0; i < all.Length; i++)
            {
                Entity e = all[i];

                Stunlock.Core.PrefabGUID station;
                try
                {
                    if (!em.HasComponent<Stunlock.Core.PrefabGUID>(e))
                    {
                        continue;
                    }

                    station = em.GetComponentData<Stunlock.Core.PrefabGUID>(e);
                }
                catch (Exception)
                {
                    continue;
                }

                AddWorkstation(em, e, station.GuidHash, index);
                AddRefinementstation(em, e, station.GuidHash, index);
            }

            // Sorted and deduplicated, because core/table_deep.py asserts both.
            // Order is what makes two dumps of the same world comparable, and a
            // repeat would mean this inversion is broken rather than that the
            // game lists a station twice.
            foreach (var pair in index)
            {
                pair.Value.Sort();
                for (int i = pair.Value.Count - 1; i > 0; i--)
                {
                    if (pair.Value[i] == pair.Value[i - 1])
                    {
                        pair.Value.RemoveAt(i);
                    }
                }
            }

            return index;
        }

        /// <summary>
        /// The two buffers get one concrete reader each rather than a shared
        /// generic. A generic constrained to `unmanaged` cannot touch a field, so
        /// the only way to read the element is by name - and writing the name
        /// once for a type whose layout was never measured would be a guess. Two
        /// methods make the COMPILER check each field against the real type.
        /// `.RecipeGuid` on WorkstationRecipesBuffer is measured, read live by
        /// the spike probe.
        /// </summary>
        private static void AddWorkstation(EntityManager em, Entity e, int stationHash,
                                           Dictionary<int, List<int>> index)
        {
            try
            {
                if (!em.HasBuffer<ProjectM.WorkstationRecipesBuffer>(e))
                {
                    return;
                }

                var buffer = em.GetBuffer<ProjectM.WorkstationRecipesBuffer>(e, true);
                for (int k = 0; k < buffer.Length; k++)
                {
                    Record(index, buffer[k].RecipeGuid.GuidHash, stationHash);
                }
            }
            catch (Exception)
            {
                // A station whose buffer cannot be read contributes nothing,
                // which UNDERSTATES the list rather than inventing an entry.
            }
        }

        private static void AddRefinementstation(EntityManager em, Entity e, int stationHash,
                                                 Dictionary<int, List<int>> index)
        {
            try
            {
                if (!em.HasBuffer<ProjectM.RefinementstationRecipesBuffer>(e))
                {
                    return;
                }

                var buffer = em.GetBuffer<ProjectM.RefinementstationRecipesBuffer>(e, true);
                for (int k = 0; k < buffer.Length; k++)
                {
                    Record(index, buffer[k].RecipeGuid.GuidHash, stationHash);
                }
            }
            catch (Exception)
            {
            }
        }

        private static void Record(Dictionary<int, List<int>> index, int recipeHash,
                                   int stationHash)
        {
            List<int> list;
            if (!index.TryGetValue(recipeHash, out list))
            {
                list = new List<int>();
                index[recipeHash] = list;
            }

            list.Add(stationHash);
        }

        // -------------------------------------------------------------------
        // the school index
        // -------------------------------------------------------------------
        /// <summary>
        /// Ability group PrefabGUID hash to school name, built from the spell
        /// school ASSET prefabs.
        ///
        /// MEASURED, and the measurement is the reason this exists rather than a
        /// name join: the `_AbilityGroup` to `_Hit` name join reaches only 258 of
        /// 1474 groups, while the reference chain
        /// `AbilityGroupStartAbilitiesBuffer -> _Cast -> AbilitySpawnPrefabOnCast`
        /// resolves a cast for 1474 of 1474. The SCHOOL is a separate join
        /// again: `ProjectM.SpellSchoolAbility` is a buffer on the
        /// `*SpellSchoolAsset` prefab entity and names the ability group.
        /// </summary>
        private static System.Collections.Generic.Dictionary<int, string> BuildSchoolIndex(
            EntityManager em, Stunlock.Core.PrefabLookupMap map, NativeArray<Entity> all)
        {
            var index = new System.Collections.Generic.Dictionary<int, string>();

            for (int i = 0; i < all.Length; i++)
            {
                Entity e = all[i];
                Stunlock.Core.PrefabGUID guid;
                try
                {
                    if (!em.HasComponent<Stunlock.Core.PrefabGUID>(e))
                    {
                        continue;
                    }

                    guid = em.GetComponentData<Stunlock.Core.PrefabGUID>(e);
                }
                catch (Exception)
                {
                    continue;
                }

                if (!HasBuffer<ProjectM.SpellSchoolAbility>(em, e))
                {
                    continue;
                }

                string name;
                try
                {
                    name = map.GetName(guid);
                }
                catch (Exception)
                {
                    continue;
                }

                if (name == null || !name.EndsWith(SchoolAssetSuffix, StringComparison.Ordinal))
                {
                    continue;
                }

                string school = name
                    .Substring(0, name.Length - SchoolAssetSuffix.Length)
                    .ToLowerInvariant();

                try
                {
                    var buffer = em.GetBuffer<ProjectM.SpellSchoolAbility>(e, true);
                    for (int k = 0; k < buffer.Length; k++)
                    {
                        index[buffer[k].AbilityGroup.GuidHash] = school;
                    }
                }
                catch (Exception)
                {
                    // A school whose buffer cannot be read contributes nothing.
                    // Its abilities then have no school and are skipped, which
                    // is the honest outcome, not a zero-filled row.
                }
            }

            return index;
        }

        // -------------------------------------------------------------------
        // abilities
        // -------------------------------------------------------------------
        private static bool TryWriteAbility(StringBuilder sb, int index, EntityManager em,
                                            Stunlock.Core.PrefabLookupMap map, Entity e,
                                            Stunlock.Core.PrefabGUID guid, string school)
        {
            string name;
            try
            {
                name = map.GetName(guid);
            }
            catch (Exception)
            {
                return false;
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"name\":").Append(Json.Str(name));
            sb.Append(",\"school\":").Append(Json.Str(school));

            // damage_type is DealDamageParameters.MainType, reached through the
            // cast. It is NOT the school - MainType's members are Physical,
            // Spell, Fire, Holy, Silver, Garlic, RadialHoly, RadialGarlic,
            // WeatherLightning and Corruption, and the schema's school is one of
            // blood, chaos, frost, illusion, storm, unholy or weapon. Writing
            // one into the other would repeat the fabricated-tier mistake.
            string damage = DamageType(em, map, e);
            if (damage.Length > 0)
            {
                sb.Append(",\"damage_type\":").Append(Json.Str(damage));
            }

            // localization_guid is OMITTED on this host. MEASURED: the runtime
            // route resolves 0 of 425 equippables on the dedicated server -
            // ManagedDataRegistry.TryGet returns false for every one, and the
            // without-logging overload agrees.
            sb.Append('}');
            return true;
        }

        /// <summary>
        /// The measured chain, one hop at a time and never a name join:
        /// group -&gt; AbilityGroupStartAbilitiesBuffer.PrefabGUID -&gt; cast entity
        /// -&gt; AbilitySpawnPrefabOnCast.SpawnPrefab -&gt; the entity carrying
        /// DealDamageOnGameplayEvent -&gt; .Parameters.MainType.
        ///
        /// MEASURED coverage: 562 of 1474 groups reach damage this way, and a
        /// second spawn hop adds exactly ZERO more, so one hop is the whole
        /// answer. An ability that never deals damage returns "" and the field
        /// is omitted rather than defaulted to Physical, which is also the
        /// enum's zero value and so unreadable as evidence.
        /// </summary>
        private static string DamageType(EntityManager em, Stunlock.Core.PrefabLookupMap map,
                                         Entity group)
        {
            try
            {
                if (!em.HasBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>(group))
                {
                    return "";
                }

                var starts = em.GetBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>(group, true);
                for (int s = 0; s < starts.Length; s++)
                {
                    Entity cast;
                    if (!map.TryGetValue(starts[s].PrefabGUID, out cast))
                    {
                        continue;
                    }

                    if (!em.HasBuffer<ProjectM.AbilitySpawnPrefabOnCast>(cast))
                    {
                        continue;
                    }

                    var spawns = em.GetBuffer<ProjectM.AbilitySpawnPrefabOnCast>(cast, true);
                    for (int k = 0; k < spawns.Length; k++)
                    {
                        Entity spawned;
                        if (!map.TryGetValue(spawns[k].SpawnPrefab, out spawned))
                        {
                            continue;
                        }

                        if (!em.HasBuffer<ProjectM.DealDamageOnGameplayEvent>(spawned))
                        {
                            continue;
                        }

                        var hits = em.GetBuffer<ProjectM.DealDamageOnGameplayEvent>(spawned, true);
                        if (hits.Length > 0)
                        {
                            return Lower(hits[0].Parameters.MainType.ToString());
                        }
                    }
                }
            }
            catch (Exception)
            {
            }

            return "";
        }

        // -------------------------------------------------------------------
        // ability_stats - ADR-007
        // -------------------------------------------------------------------
        /// <summary>
        /// One row per ability GROUP, carrying the combat coefficients.
        ///
        /// ADR-007: the key space is the GROUP, not the ability and not the
        /// school. A weapon group has no &lt;Weapon&gt;SpellSchoolAsset and so cannot
        /// be keyed by school at all, which is ROADMAP cycle 3 gap 3; keying on
        /// the group dissolves it, because phase 1 measured that
        /// ProjectM.WeaponAbilityData tells a weapon group from a spell group by
        /// COMPONENT.
        ///
        /// EVERY COEFFICIENT FIELD IS OMITTED WHEN THE CHAIN DOES NOT REACH IT.
        /// Cycle 2 measured 912 of 1474 groups reaching no damage prefab and a
        /// second spawn hop adding exactly zero, so those groups genuinely do
        /// not deal damage. They still get a ROW - they are real abilities with
        /// real cast times - and ship with the damage fields absent rather than
        /// zeroed. A zero MainFactor is indistinguishable from a real one.
        /// </summary>
        private static bool TryWriteAbilityStats(StringBuilder sb, int index, EntityManager em,
                                                 Stunlock.Core.PrefabLookupMap map, Entity e,
                                                 Stunlock.Core.PrefabGUID guid)
        {
            string name;
            try
            {
                name = map.GetName(guid);
            }
            catch (Exception)
            {
                return false;
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"name\":").Append(Json.Str(name));

            // The weapon-versus-spell discriminator is a COMPONENT, which is why
            // this is a fact rather than a name-prefix guess.
            bool isWeapon = Has<ProjectM.WeaponAbilityData>(em, e);
            sb.Append(",\"is_weapon_ability\":").Append(isWeapon ? "true" : "false");

            try
            {
                if (isWeapon)
                {
                    var weapon = em.GetComponentData<ProjectM.WeaponAbilityData>(e);
                    sb.Append(",\"ability_type\":").Append(Json.Str(weapon.AbilityType.ToString()));
                }
                else if (em.HasComponent<ProjectM.VBloodAbilityData>(e))
                {
                    var spell = em.GetComponentData<ProjectM.VBloodAbilityData>(e);
                    sb.Append(",\"ability_type\":").Append(Json.Str(spell.AbilityType.ToString()));

                    // A SECOND and independent school source to the
                    // <School>SpellSchoolAsset join that fills abilities.school,
                    // and its enum carries Shadow, which the six-school join
                    // cannot produce. Emitted alongside rather than instead:
                    // two sources that can be compared beat one that cannot.
                    sb.Append(",\"spell_school\":")
                      .Append(Json.Str(Lower(spell.AbilitySchool.ToString())));
                }
            }
            catch (Exception)
            {
            }

            WriteCastAndDamage(sb, em, map, e);

            // power_stat is DECLARED IN THE SCHEMA AND NEVER EMITTED. PROVEN
            // ABSENT in phase 1: no power-selector member exists across all 51
            // components enumerated on the _Hit entity, and MainType is the only
            // discriminator present. Absent means unsourced, not Physical.
            sb.Append('}');
            return true;
        }

        /// <summary>
        /// The cast entity and, through it, the hit entity. The measured chain,
        /// one hop at a time and never a name join - the _AbilityGroup to _Hit
        /// NAME join reaches only 258 of 1474 groups while this reference chain
        /// resolves a cast for 1474 of 1474.
        ///
        ///   group -&gt; AbilityGroupStartAbilitiesBuffer.PrefabGUID -&gt; _Cast
        ///   _Cast -&gt; AbilitySpawnPrefabOnCast.SpawnPrefab         -&gt; _Hit
        ///
        /// FIRST-WINS on both hops, matching the DamageType reader cycle 2
        /// shipped, so ability_stats and abilities.damage_type cannot disagree
        /// about which hit prefab they read. An ability whose buffer holds more
        /// than one start or more than one spawn has that multiplicity reported
        /// as a COUNT (spawn_prefabs_on_cast) rather than silently averaged.
        /// </summary>
        private static void WriteCastAndDamage(StringBuilder sb, EntityManager em,
                                               Stunlock.Core.PrefabLookupMap map, Entity group)
        {
            try
            {
                if (!em.HasBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>(group))
                {
                    return;
                }

                var starts = em.GetBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>(group, true);
                for (int s = 0; s < starts.Length; s++)
                {
                    Entity cast;
                    if (!map.TryGetValue(starts[s].PrefabGUID, out cast))
                    {
                        continue;
                    }

                    WriteCastTiming(sb, em, cast);

                    if (!em.HasBuffer<ProjectM.AbilitySpawnPrefabOnCast>(cast))
                    {
                        return;
                    }

                    var spawns = em.GetBuffer<ProjectM.AbilitySpawnPrefabOnCast>(cast, true);
                    sb.Append(",\"spawn_prefabs_on_cast\":").Append(spawns.Length);

                    for (int k = 0; k < spawns.Length; k++)
                    {
                        Entity hit;
                        if (!map.TryGetValue(spawns[k].SpawnPrefab, out hit))
                        {
                            continue;
                        }

                        if (!em.HasBuffer<ProjectM.DealDamageOnGameplayEvent>(hit))
                        {
                            continue;
                        }

                        var events = em.GetBuffer<ProjectM.DealDamageOnGameplayEvent>(hit, true);
                        if (events.Length == 0)
                        {
                            continue;
                        }

                        WriteDamage(sb, em, hit, events);
                        return;
                    }

                    return;
                }
            }
            catch (Exception)
            {
                // A partially written row is still valid JSON here: every field
                // this method appends is optional by schema, so an abort mid-way
                // omits the rest rather than corrupting the object.
            }
        }

        private static void WriteCastTiming(StringBuilder sb, EntityManager em, Entity cast)
        {
            try
            {
                if (em.HasComponent<ProjectM.AbilityCastTimeData>(cast))
                {
                    var timing = em.GetComponentData<ProjectM.AbilityCastTimeData>(cast);
                    sb.Append(",\"cast_time\":").Append(Json.Num(timing.MaxCastTime._Value));
                    sb.Append(",\"post_cast_time\":")
                      .Append(Json.Num(timing.PostCastTime._Value));
                }

                if (em.HasComponent<ProjectM.AbilityCooldownData>(cast))
                {
                    var cooldown = em.GetComponentData<ProjectM.AbilityCooldownData>(cast);
                    sb.Append(",\"cooldown\":").Append(Json.Num(cooldown.Cooldown._Value));
                }

                // GlobalCooldown.Value is a plain Single, NOT a ModifiableFloat.
                // Read off the declared field type rather than assumed uniform.
                if (em.HasComponent<ProjectM.GlobalCooldown>(cast))
                {
                    var global = em.GetComponentData<ProjectM.GlobalCooldown>(cast);
                    sb.Append(",\"global_cooldown\":").Append(Json.Num(global.Value));
                }
            }
            catch (Exception)
            {
            }
        }

        private static void WriteDamage(StringBuilder sb, EntityManager em, Entity hit,
                                        DynamicBuffer<ProjectM.DealDamageOnGameplayEvent> events)
        {
            var first = events[0];
            var parameters = first.Parameters;

            sb.Append(",\"coefficient\":").Append(Json.Num(parameters.MainFactor));
            sb.Append(",\"raw_damage_value\":").Append(Json.Num(parameters.RawDamageValue));
            sb.Append(",\"raw_damage_percent\":").Append(Json.Num(parameters.RawDamagePercent));
            sb.Append(",\"damage_type\":").Append(Json.Str(Lower(parameters.MainType.ToString())));

            // MaterialModifiers is a ProjectM.EntityTypeModifiers carrying 23
            // per-target-CLASS multipliers. VBlood is the one a boss
            // time-to-kill multiplies by, and it is emitted for that reason
            // alone; the other 22 are readable by this same hop and are NOT
            // ATTEMPTED because no cycle 3 consumer reads them.
            sb.Append(",\"vblood_damage_modifier\":")
              .Append(Json.Num(parameters.MaterialModifiers.VBlood));

            sb.Append(",\"damage_modifier_per_hit\":")
              .Append(Json.Num(first.DamageModifierPerHit));
            sb.Append(",\"multiply_main_factor_with_stacks\":")
              .Append(first.MultiplyMainFactorWithStacks ? "true" : "false");

            // A6. The multiplicity is BUFFER LENGTHS, and these are counted
            // rather than folded into a single hits-per-cast, because turning
            // three counts into one effective number is a MODEL and belongs to
            // the combat-math spec. Counting is measurement; the fold is not.
            sb.Append(",\"hits_per_cast\":").Append(events.Length);
            sb.Append(",\"hit_triggers\":").Append(BufferLength<ProjectM.HitTrigger>(em, hit));
            sb.Append(",\"gameplay_events_on_hit\":")
              .Append(BufferLength<ProjectM.CreateGameplayEventsOnHit>(em, hit));
        }

        private static int BufferLength<T>(EntityManager em, Entity e) where T : unmanaged
        {
            try
            {
                return em.HasBuffer<T>(e) ? em.GetBuffer<T>(e, true).Length : 0;
            }
            catch (Exception)
            {
                return 0;
            }
        }

        // -------------------------------------------------------------------
        // vbloods
        // -------------------------------------------------------------------
        private static bool TryWriteVBlood(StringBuilder sb, int index, EntityManager em,
                                           Stunlock.Core.PrefabLookupMap map, Entity e,
                                           Stunlock.Core.PrefabGUID guid, out string reason)
        {
            reason = "";

            int level;
            try
            {
                // MEASURED: UnitLevel.Level ranges 16..91 over the 92 VBloodUnit
                // prefabs. VBloodConsumeSource.Tier was the recorded candidate
                // and is NOT the level - it is a SpellSchoolProgressionTier with
                // values Undefined and Tier1..Tier4, measured 23/19/13/6/4.
                level = em.GetComponentData<ProjectM.UnitLevel>(e).Level._Value;
            }
            catch (Exception)
            {
                reason = "V Blood prefab with no readable UnitLevel";
                return false;
            }

            string name;
            try
            {
                name = map.GetName(guid);
            }
            catch (Exception)
            {
                name = "";
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"name\":").Append(Json.Str(name));
            sb.Append(",\"level\":").Append(level);

            // THE BOSS STAT LINE, schema_version 2. ROADMAP cycle 3 gap 1: these
            // rows carried level, name and guid only, so time-to-kill had no
            // denominator. Phase 1 enumerated all 150 components on three bosses
            // spanning levels 16, 57 and 91 and named the source of every field;
            // this reads them with TYPED accessors, which is the only thing that
            // works on this build - a generic value reader was built twice and
            // failed twice, once returning 539327184 for every Int32 and once
            // hard-crashing the process.
            // max_health IS NOT EMITTED, and this is a MEASUREMENT rather than a
            // gap. ProjectM.Health.MaxHealth reads 0 on all 65 V Blood PREFABS.
            // The phase 3 control settles what that zero means: on
            // CHAR_Vampire_Dracula_VBlood, 19 typed fields were compared between
            // the prefab (entity 29012) and the live instance (322945) and 17
            // are IDENTICAL - every UnitStats field and UnitLevel.Level. The two
            // that differ are Health.MaxHealth and Health.Value, both 0 on the
            // prefab and 8107 on the instance.
            //
            // So there is NO spawn-scaling factor to recover: 17 of 19 agree
            // exactly, and 0 -> 8107 is not a ratio. The health pool simply is
            // not authored on the prefab. Writing the 0 would be the fabricated
            // items.tier mistake with the denominator of every time-to-kill.
            //
            // CONSEQUENCE, carried into ROADMAP cycle 3 gap 1 rather than
            // buried here: the boss stat line IS on the prefab except for the
            // health pool, and a TTK denominator needs a live world with the
            // boss actually spawned.
            WriteUnitStats(sb, em, e);

            // blood_type, unlocks and region stay OMITTED and are NOT ATTEMPTED
            // this phase, which is a different statement from measured-absent.
            sb.Append('}');
            return true;
        }

        /// <summary>
        /// physical_power, spell_power and the resistance map, all from
        /// ProjectM.UnitStats.
        ///
        /// THE FOUR RESISTANCES ARE NOT COMMENSURABLE, and this is the finding
        /// that matters most about this block. Read off the declared field
        /// types rather than assumed:
        ///
        ///   PhysicalResistance          ModifiableFloat
        ///   SpellResistance             ModifiableFloat
        ///   FireResistance              ModifiableINT   - a RATING, not a fraction
        ///   CorruptionDamageReduction   ModifiableFloat - already a REDUCTION
        ///
        /// Fire is an integer RATING that only becomes a damage reduction
        /// through ProjectM.ResistanceData.FireResistance_DamageReductionPerRating,
        /// which is a GLOBAL per-rating coefficient block and not a per-boss
        /// vector. Corruption is named DamageReduction rather than Resistance
        /// and is already the reduced fraction. So a consumer must NOT average
        /// these four or feed them to one formula: they are four differently
        /// shaped quantities sharing a JSON object because they share a source
        /// component.
        ///
        /// Holy, Silver, Garlic and Sun are PROVEN ABSENT on the unit across
        /// that same full enumeration and are OMITTED. A zero would be
        /// indistinguishable from a real zero, which is the items.tier mistake.
        /// </summary>
        private static void WriteUnitStats(StringBuilder sb, EntityManager em, Entity e)
        {
            ProjectM.UnitStats stats;
            try
            {
                stats = em.GetComponentData<ProjectM.UnitStats>(e);
            }
            catch (Exception)
            {
                // The whole field is omitted, which says "UnitStats could not be
                // read at all" - a different claim from an empty resistance map.
                return;
            }

            sb.Append(",\"physical_power\":").Append(Json.Num(stats.PhysicalPower._Value));
            sb.Append(",\"spell_power\":").Append(Json.Num(stats.SpellPower._Value));

            sb.Append(",\"resistances\":{");
            sb.Append("\"physical\":").Append(Json.Num(stats.PhysicalResistance._Value));
            sb.Append(",\"spell\":").Append(Json.Num(stats.SpellResistance._Value));
            sb.Append(",\"fire\":").Append(stats.FireResistance._Value);
            sb.Append(",\"corruption\":")
              .Append(Json.Num(stats.CorruptionDamageReduction._Value));
            sb.Append('}');
        }

        // -------------------------------------------------------------------
        // blood_types
        // -------------------------------------------------------------------
        /// <summary>
        /// MEASURED: 13 blood types, each with a primary buffer of up to 5 tier
        /// buffs and a secondary buffer of up to 4. The buffer element carries
        /// ONE field, a PrefabGUID naming the tier's buff prefab, so the tier
        /// ORDER is the buffer index and there is no threshold field to read.
        ///
        /// The bonus VALUES are deliberately not emitted. Following the buff
        /// guid one hop reaches a real ModifyUnitStatBuff_DOTS buffer with real
        /// StatTypes, but every Value on it measures 0 with SoftCapValue 1 -
        /// the magnitudes are scaled from blood quality at runtime and are not
        /// on the prefab. Emitting those zeroes would be the fabricated
        /// items.tier mistake with a different field name.
        /// </summary>
        private static bool TryWriteBloodType(StringBuilder sb, int index, EntityManager em,
                                              Stunlock.Core.PrefabLookupMap map, Entity e,
                                              Stunlock.Core.PrefabGUID guid)
        {
            string name;
            try
            {
                name = map.GetName(guid);
            }
            catch (Exception)
            {
                return false;
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"name\":").Append(Json.Str(name));
            sb.Append(",\"bonuses\":[");

            int written = 0;
            try
            {
                var primary = em.GetBuffer<ProjectM.Shared.PrimaryUnitBloodTypeBuffs>(e, true);
                for (int i = 0; i < primary.Length; i++)
                {
                    WriteBonus(sb, written, em, map, "primary", i + 1, primary[i].BuffType);
                    written++;
                }

                if (em.HasBuffer<ProjectM.Shared.SecondaryUnitBloodTypeBuffs>(e))
                {
                    var secondary =
                        em.GetBuffer<ProjectM.Shared.SecondaryUnitBloodTypeBuffs>(e, true);
                    for (int i = 0; i < secondary.Length; i++)
                    {
                        WriteBonus(sb, written, em, map, "secondary", i + 1,
                                   secondary[i].BuffType);
                        written++;
                    }
                }
            }
            catch (Exception)
            {
                // A partially written array would be invalid JSON, so the close
                // below is the only safe recovery.
            }

            sb.Append("]}");
            return true;
        }

        private static void WriteBonus(StringBuilder sb, int written, EntityManager em,
                                       Stunlock.Core.PrefabLookupMap map, string slot, int tier,
                                       Stunlock.Core.PrefabGUID buffGuid)
        {
            if (written > 0)
            {
                sb.Append(',');
            }

            string buffName;
            try
            {
                buffName = map.GetName(buffGuid);
            }
            catch (Exception)
            {
                buffName = "";
            }

            sb.Append("{\"slot\":").Append(Json.Str(slot));
            sb.Append(",\"tier\":").Append(tier);
            sb.Append(",\"buff_guid\":").Append(buffGuid.GuidHash);
            sb.Append(",\"buff_name\":").Append(Json.Str(buffName));
            sb.Append(",\"stats\":[");

            int stats = 0;
            try
            {
                Entity buffEntity;
                if (map.TryGetValue(buffGuid, out buffEntity)
                    && em.HasBuffer<ProjectM.ModifyUnitStatBuff_DOTS>(buffEntity))
                {
                    var buffer = em.GetBuffer<ProjectM.ModifyUnitStatBuff_DOTS>(buffEntity, true);
                    for (int i = 0; i < buffer.Length; i++)
                    {
                        if (stats > 0)
                        {
                            sb.Append(',');
                        }

                        sb.Append("{\"stat\":").Append(Json.Str(buffer[i].StatType.ToString()));
                        sb.Append(",\"modification\":")
                          .Append(Json.Str(buffer[i].ModificationType.ToString()));
                        sb.Append('}');
                        stats++;
                    }
                }
            }
            catch (Exception)
            {
            }

            // value_source is a fact about the data, not a value: the prefab
            // carries the stat NAMES and zero magnitudes.
            sb.Append("],\"value_source\":\"blood_quality_scaled_at_runtime\"}");
        }

        private static void WriteUnmapped(StringBuilder sb, int index,
                                          Stunlock.Core.PrefabGUID guid, string reason)
        {
            // MANDATORY and deliberately NARROW. `unmapped` reports a prefab the
            // dumper TRIED to classify and could not - it is not a list of every
            // prefab outside the two writable tables, which on this build would be
            // about 22000 rows of noise drowning the signal it exists to carry.
            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"reason\":").Append(Json.Str(reason)).Append('}');
        }

        // -------------------------------------------------------------------
        // items
        // -------------------------------------------------------------------
        private static bool TryWriteItem(StringBuilder sb, int index, EntityManager em,
                                         Stunlock.Core.PrefabLookupMap map, Entity e,
                                         Stunlock.Core.PrefabGUID guid,
                                         LocalizationJoin localization)
        {
            string category;
            string weaponType;
            try
            {
                var equippable = em.GetComponentData<ProjectM.EquippableData>(e);
                category = Lower(equippable.EquipmentType.ToString());
                weaponType = category == "weapon" ? equippable.WeaponType.ToString() : "";
            }
            catch (Exception)
            {
                return false;
            }

            string name;
            try
            {
                name = map.GetName(guid);
            }
            catch (Exception)
            {
                name = "";
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"name\":").Append(Json.Str(name));
            sb.Append(",\"category\":").Append(Json.Str(category));

            // tier is OMITTED, not faked. It was emitted as a hardcoded 0 on all
            // 425 rows of the first dump; schema_version 3 dropped it from
            // required once an exhaustive scan of all 169 interop assemblies
            // returned 67 Tier-shaped fields and ZERO on a per-item-prefab
            // component. Rarity returns zero hits anywhere in ProjectM, and
            // ProjectM.ItemData, the real item-definition component, has no tier.
            // Two derivations were rejected on evidence rather than left untried:
            // the _T0x prefab-name token (name-convention guessing, which has
            // already produced one wrong answer this cycle) and
            // ArmorLevelSource.Level / 10 (exact on 117 of 425 rows, but that
            // divisor is calibrated against the same forbidden token, the value
            // is already published as gear_score, and headgear, cloaks and bags
            // carry no level component at all).

            // localization_guid is ATTEMPTED per host and OMITTED when the join
            // does not resolve. It is never faked: the offline join does not
            // exist at all (all 8379 strings.json keys are dashed UUIDs, and 0
            // of 425 rows join by name, decimal guid or six hex forms), and the
            // runtime route is GameDataSystem.ManagedDataRegistry, NOT
            // PrefabLookupMap, which carries no localization member.
            //
            // MEASURED absent on the dedicated server, 0 of 425 with the
            // without-logging control agreeing. The CLIENT host is a separate
            // measurement, which is why this reads rather than assumes. The
            // per-dump counters ride in the envelope's localization block.
            string loc = localization.GuidFor(guid);
            if (loc.Length > 0)
            {
                sb.Append(",\"localization_guid\":").Append(Json.Str(loc));
            }

            // gear_score is emitted only when ArmorLevelSource is actually present.
            try
            {
                if (em.HasComponent<ProjectM.ArmorLevelSource>(e))
                {
                    var armor = em.GetComponentData<ProjectM.ArmorLevelSource>(e);
                    sb.Append(",\"gear_score\":").Append(Json.Num(armor.Level));
                }
            }
            catch (Exception)
            {
                // Absent or unreadable: omit rather than report a zero that
                // cannot be told apart from a real zero.
            }

            sb.Append(",\"weapon_type\":").Append(Json.Str(weaponType));

            // ability_group_guids, schema_version 4, the L1 link. EquippableData
            // was read successfully above or this method already returned false,
            // so the chain HAS run by the time this emits - which is what makes
            // an empty list mean "grants no ability" rather than "not measured",
            // exactly as ADR-006 rules for station_guids.
            sb.Append(",\"ability_group_guids\":[");
            WriteAbilityGroups(sb, em, map, e);
            sb.Append(']');

            sb.Append(",\"stats\":");
            WriteStats(sb, em, e);
            sb.Append('}');
            return true;
        }

        /// <summary>
        /// The L1 chain, every hop read off an enumerated component list in
        /// phase 1 rather than guessed:
        ///
        ///   item prefab
        ///     -&gt; ProjectM.EquippableData.BuffGuid        (PrefabGUID)
        ///     -&gt; EquipBuff_Weapon_&lt;Family&gt;_Base
        ///     -&gt; DynamicBuffer&lt;ProjectM.ReplaceAbilityOnSlotBuff&gt;
        ///     -&gt; element .NewGroupId                     = the ability GROUP
        ///
        /// The item prefab itself carries NO ability reference, so the equip
        /// buff is the only route. Note the ASYMMETRY, which is not a
        /// contradiction: BuffGuid is BARRED as a route to item STATS, because
        /// ModifyUnitStatBuff_DOTS sits on the item prefab itself and cycle 2
        /// settled that. Different question, different answer.
        ///
        /// Sorted and deduplicated before emit, because core/table_deep.py
        /// asserts both and for the same reasons it does on station_guids: a
        /// repeat would mean this walk is broken rather than that the game lists
        /// a group twice, and order is what makes two dumps comparable.
        ///
        /// element .Slot is READ AND DISCARDED. It is the ability bar slot, it is
        /// real, and no cycle 3 consumer has a use for it yet; recording that it
        /// was seen and dropped is cheaper than a future session re-deriving
        /// whether the chain could carry it.
        /// </summary>
        private static void WriteAbilityGroups(StringBuilder sb, EntityManager em,
                                               Stunlock.Core.PrefabLookupMap map, Entity e)
        {
            var groups = new List<int>();
            try
            {
                var equippable = em.GetComponentData<ProjectM.EquippableData>(e);

                Entity buff;
                if (map.TryGetValue(equippable.BuffGuid, out buff)
                    && em.HasBuffer<ProjectM.ReplaceAbilityOnSlotBuff>(buff))
                {
                    var replacements = em.GetBuffer<ProjectM.ReplaceAbilityOnSlotBuff>(buff, true);
                    for (int i = 0; i < replacements.Length; i++)
                    {
                        int group = replacements[i].NewGroupId.GuidHash;

                        // 0 is the empty PrefabGUID and means "this slot clears
                        // the ability" rather than "this slot grants group 0".
                        // Emitting it would invent a join target.
                        if (group != 0 && !groups.Contains(group))
                        {
                            groups.Add(group);
                        }
                    }
                }
            }
            catch (Exception)
            {
                // Understates the list rather than inventing an entry. The
                // resulting [] is honest about the walk having run.
            }

            groups.Sort();
            for (int i = 0; i < groups.Count; i++)
            {
                if (i > 0)
                {
                    sb.Append(',');
                }

                sb.Append(groups[i]);
            }
        }

        /// <summary>
        /// The stat block, read ONE HOP off the item prefab itself.
        ///
        /// HONEST SHAPE, deliberately not the schema's flat name-to-number map:
        /// an array of {stat, modification, value}. A measured element carries
        /// ModificationType alongside Value, an additive and a multiplicative
        /// modifier of the same Value are not the same stat, and one item can
        /// carry two modifiers of the SAME StatType, which a map would silently
        /// collapse. Flattening to satisfy the schema would destroy all three
        /// facts. The mismatch is meant to surface in the rmdata_ingest census.
        /// </summary>
        private static void WriteStats(StringBuilder sb, EntityManager em, Entity e)
        {
            sb.Append('[');
            try
            {
                if (!em.HasBuffer<ProjectM.ModifyUnitStatBuff_DOTS>(e))
                {
                    sb.Append(']');
                    return;
                }

                var buffer = em.GetBuffer<ProjectM.ModifyUnitStatBuff_DOTS>(e, true);
                for (int i = 0; i < buffer.Length; i++)
                {
                    var entry = buffer[i];
                    if (i > 0)
                    {
                        sb.Append(',');
                    }

                    sb.Append("{\"stat\":").Append(Json.Str(entry.StatType.ToString()));
                    sb.Append(",\"modification\":")
                      .Append(Json.Str(entry.ModificationType.ToString()));
                    sb.Append(",\"value\":").Append(Json.Num(entry.Value)).Append('}');
                }
            }
            catch (Exception)
            {
                // A partially written array would be invalid JSON, so the
                // opening bracket plus this close is the only safe recovery.
            }

            sb.Append(']');
        }

        // -------------------------------------------------------------------
        // recipes
        // -------------------------------------------------------------------
        private static bool TryWriteRecipe(StringBuilder sb, int index, EntityManager em,
                                           Entity e, Stunlock.Core.PrefabGUID guid,
                                           Dictionary<int, List<int>> stations,
                                           out string reason)
        {
            reason = "";

            float duration;
            try
            {
                duration = em.GetComponentData<ProjectM.RecipeData>(e).CraftDuration;
            }
            catch (Exception)
            {
                reason = "recipe prefab whose RecipeData could not be read";
                return false;
            }

            // output_guid is REQUIRED by the schema and the recipe's own
            // component carries no output field - the answer is a second buffer.
            // A recipe that produces a unit rather than an item has no entry
            // here, and that is reported rather than defaulted to zero.
            int outputGuid;
            int outputAmount;
            try
            {
                if (!em.HasBuffer<ProjectM.RecipeOutputBuffer>(e))
                {
                    reason = "recipe prefab with no item output buffer";
                    return false;
                }

                var outputs = em.GetBuffer<ProjectM.RecipeOutputBuffer>(e, true);
                if (outputs.Length == 0)
                {
                    reason = "recipe prefab with an empty item output buffer";
                    return false;
                }

                outputGuid = outputs[0].Guid.GuidHash;
                outputAmount = (int)outputs[0].Amount;
            }
            catch (Exception)
            {
                reason = "recipe prefab whose output buffer could not be read";
                return false;
            }

            if (index > 0)
            {
                sb.Append(',');
            }

            sb.Append("{\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"output_guid\":").Append(outputGuid);
            sb.Append(",\"output_amount\":").Append(outputAmount);
            sb.Append(",\"craft_duration\":").Append(Json.Num(duration));

            // station_guids, ADR-006. Nothing on THIS entity names a station -
            // the reference runs the other way - so the value comes from the
            // inverted index built in Dump(). Emitted even when empty, because
            // "reachable from no station" is a real answer for an AlwaysUnlocked
            // player-crafted recipe and must stay distinguishable from "the
            // inversion did not run".
            sb.Append(",\"station_guids\":[");
            List<int> stationList;
            if (stations.TryGetValue(guid.GuidHash, out stationList))
            {
                for (int i = 0; i < stationList.Count; i++)
                {
                    if (i > 0)
                    {
                        sb.Append(',');
                    }

                    sb.Append(stationList[i]);
                }
            }

            sb.Append(']');

            sb.Append(",\"ingredients\":[");
            try
            {
                if (em.HasBuffer<ProjectM.RecipeRequirementBuffer>(e))
                {
                    var requirements = em.GetBuffer<ProjectM.RecipeRequirementBuffer>(e, true);
                    for (int i = 0; i < requirements.Length; i++)
                    {
                        var requirement = requirements[i];
                        if (i > 0)
                        {
                            sb.Append(',');
                        }

                        sb.Append("{\"prefab_guid\":").Append(requirement.Guid.GuidHash);
                        sb.Append(",\"amount\":").Append((int)requirement.Amount).Append('}');
                    }
                }
            }
            catch (Exception)
            {
            }

            sb.Append("]}");
            return true;
        }

        private static string Lower(string value)
        {
            return value == null ? "" : value.ToLowerInvariant();
        }
    }
}

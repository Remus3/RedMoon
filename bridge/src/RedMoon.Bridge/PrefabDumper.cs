// Prefab collection -> table rows. MAIN THREAD ONLY (spec decision D7).
//
// Everything here reads ECS, so every entry point is called from the injected
// MonoBehaviour tick in Plugin.cs and never from the listener thread.
//
// What this file may emit is bounded by what was MEASURED against build
// 1.1.13.0-r99712 (docs/BRIDGE_SPIKES.md, S3 live entity dump): items and
// recipes only. The other three schemas are NOT writable yet - the ability
// school is not on the _Cast entity, the V Blood level field is unpinned, and
// the blood bonus buffer element fields are unread - so this file does not
// pretend to fill them. tests/test_bridge_project.py fails if it starts to.
//
// Two measured traps are encoded here rather than commented around:
//
//  1. READINESS. The prefab map fills in over about 1.7 s, climbing
//     1189 -> 3212 -> 11760 -> 17400 -> 23583, and GameDataInitialized flips
//     False to True exactly as it settles. A dump taken on first non-zero count
//     returns a castle-asset subset and LOOKS complete. Every dump is gated on
//     GameDataInitialized.
//  2. WORLD SELECTION IS BY NAME. "Default World" is a Simulation world sitting
//     at index 0 in both hosts and it THROWS when asked for the prefab map, so
//     "first Simulation world" is a wrong rule that happens to be plausible.
using System;
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
            "items", "recipes", "abilities", "vbloods", "blood_types"
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

            var watch = Stopwatch.StartNew();
            var items = new StringBuilder();
            var recipes = new StringBuilder();
            var abilities = new StringBuilder();
            var vbloods = new StringBuilder();
            var bloodTypes = new StringBuilder();
            var unmapped = new StringBuilder();
            int itemCount = 0;
            int recipeCount = 0;
            int abilityCount = 0;
            int vbloodCount = 0;
            int bloodTypeCount = 0;
            int unmappedCount = 0;

            EntityManager em = target.EntityManager;
            NativeArray<Entity> all = em.GetAllEntities(Allocator.Temp);

            // The school index must exist before the first ability row, so it
            // gets its own pass. A second full pass is affordable: the whole
            // dump measures 57 ms for 47573 entities.
            var schools = wantAbilities
                ? BuildSchoolIndex(em, map, all)
                : new System.Collections.Generic.Dictionary<int, string>();

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

                if (wantItems && Has<ProjectM.EquippableData>(em, e))
                {
                    if (TryWriteItem(items, itemCount, em, map, e, guid))
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

                if (wantRecipes && Has<ProjectM.RecipeData>(em, e))
                {
                    string reason;
                    if (TryWriteRecipe(recipes, recipeCount, em, e, guid, out reason))
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
                if (wantAbilities && schools.ContainsKey(guid.GuidHash))
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
                if (wantVbloods && Has<ProjectM.VBloodUnit>(em, e)
                    && Has<ProjectM.VBloodConsumeSource>(em, e))
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
                if (wantBloodTypes && HasBuffer<ProjectM.Shared.PrimaryUnitBloodTypeBuffs>(em, e))
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
            body.Append("},\"tables\":{");
            body.Append("\"items\":[").Append(items).Append(']');
            body.Append(",\"recipes\":[").Append(recipes).Append(']');
            body.Append(",\"abilities\":[").Append(abilities).Append(']');
            body.Append(",\"vbloods\":[").Append(vbloods).Append(']');
            body.Append(",\"blood_types\":[").Append(bloodTypes).Append(']');
            body.Append("},\"unmapped\":[").Append(unmapped).Append("]}");
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

            // max_health, physical_power, spell_power, resistances, blood_type,
            // unlocks and region are all OMITTED: none has been measured on this
            // build, and a zero here is indistinguishable from a real zero.
            sb.Append('}');
            return true;
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
                                         Stunlock.Core.PrefabGUID guid)
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

            // localization_guid is OMITTED, not faked: MEASURED, the join does
            // not exist offline - all 8379 strings.json keys are dashed UUIDs and
            // zero of 425 rows join by name, by decimal guid or by six hex forms.
            // The runtime route is GameDataSystem.ManagedDataRegistry, NOT
            // PrefabLookupMap, which carries no localization member.
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
            sb.Append(",\"stats\":");
            WriteStats(sb, em, e);
            sb.Append('}');
            return true;
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

            // station_guid is OMITTED. It is OPEN in S3: the station references
            // the recipe, not the reverse, so there is nothing on this entity to
            // read and a guessed zero would be indistinguishable from a real one.
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

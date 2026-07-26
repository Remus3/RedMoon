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

        /// <summary>The only tables mapped against this build.</summary>
        internal static readonly string[] WritableTables = { "items", "recipes" };

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

            var watch = Stopwatch.StartNew();
            var items = new StringBuilder();
            var recipes = new StringBuilder();
            var unmapped = new StringBuilder();
            int itemCount = 0;
            int recipeCount = 0;
            int unmappedCount = 0;

            EntityManager em = target.EntityManager;
            NativeArray<Entity> all = em.GetAllEntities(Allocator.Temp);

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
            body.Append("},\"tables\":{");
            body.Append("\"items\":[").Append(items).Append(']');
            body.Append(",\"recipes\":[").Append(recipes).Append(']');
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

            // tier: REQUIRED by data/schemas/items.schema.json and UNSOURCED on
            // this build. No per-item tier component exists - a type scan for
            // Tier-shaped types returns spell schools, jewels and castle hearts
            // and nothing per item. The only other candidate is the _T0x token in
            // the prefab NAME, which is a guess about Stunlock's conventions and
            // exactly the kind of inference BRIDGE_SPIKES.md records as having
            // produced a wrong answer once already. 0 is emitted, every row will
            // read 0, and the first-dump review owes this field a real source.
            sb.Append(",\"tier\":0");

            // localization_guid is OMITTED, not faked: nothing measured joins a
            // prefab to a localization key yet. gear_score is emitted only when
            // ArmorLevelSource is actually present.
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

// EXPLORATORY. Cycle 3 phase 1 of the Bloodforge input spike.
//
// This file carries NO SCHEMA, feeds NO ingest gate, and is never promoted to a
// table. It exists to answer one question that cannot be answered from static
// metadata alone: which components does a REAL ENTITY actually carry, and what
// fields do those components declare. See docs/superpowers/specs/
// 2026-07-26-bloodforge-input-spike-design.md section 3.
//
// THE ONE HARD RULE OF THIS FILE. It never calls HasComponent on a name anyone
// hoped for. It ENUMERATES the entity's actual component types and prints all of
// them. A HasComponent that returns false is evidence only when the type name
// was right, and at this stage nothing establishes that. Cycle 2 paid for this
// lesson three times: ShadowVBloodUnitTagComponent returned a true and
// misleading zero, "there is no SpellSchool component type" was true but
// useless, and items.tier was fabricated as 0 on 425 rows.
//
// MAIN THREAD ONLY (spec decision D7), same as PrefabDumper. Readiness is gated
// on GameDataInitialized, which is a precondition for reading anything at all
// rather than a validation of what was read.
//
// WHAT THIS READS, AND WHAT IT DELIBERATELY DOES NOT.
//
// It reads NAMES: the entity's complete component-type list, and for every
// component the full declared field list - field name, field type, byte offset,
// and nested value types expanded - taken from il2cpp CLASS METADATA.
//
// It does NOT read field VALUES, and that is a measured decision rather than an
// omission. Two generic value readers were built and both failed:
//
//  1. Managed reflection - EntityManagerDebug.GetComponentBoxed, then
//     Il2CppSystem.Type.GetFields and FieldInfo.GetValue. It produced correct
//     field names and GARBAGE VALUES: every System.Int32 on every component of
//     every entity read 539327184 and every System.Single read 1.402156E-19.
//     Not a plausible wrong number - the SAME number everywhere, which is the
//     tell that the read hit a fixed location rather than the field.
//  2. Raw il2cpp field offsets read off that same boxed pointer. It HARD
//     CRASHED the dedicated server process on the first request, which is the
//     stronger version of the same finding: GetComponentBoxed does not hand
//     back an object backed by the component's real chunk memory on this
//     build, so there is nothing valid to point at.
//
// What caught (1) is a control that cost nothing and is worth copying: every
// entity carries Stunlock.Core.PrefabGUID, whose value the same response ALREADY
// states from a typed read. The generic reader said 539327184 where the truth
// was -327335305. A value reader with no such control would have shipped.
//
// The consequence is scoped, not fatal. Phase 1's gate asks for the component
// and field inventory BY NAME, which is exactly what this produces, and cycle 2
// already proved that TYPED reads off a named component work perfectly - that is
// how all five tables are populated. So values are read the way they are read
// everywhere else in this project: with the type spelled out, once the inventory
// below has told us which type to spell.
using System;
using System.Text;
using Unity.Collections;
using Unity.Entities;

namespace RedMoon.Bridge
{
    internal static class ComponentDumper
    {
        /// <summary>Default and ceiling on matched entities per request.</summary>
        internal const int DefaultLimit = 3;
        internal const int MaxLimit = 12;

        /// <summary>
        /// How deep a nested value type is expanded. 3 reaches
        /// UnitLevel.Level._Value and UnitStats.PhysicalPower._Value, which are
        /// the shapes this spike is hunting; deeper is noise.
        /// </summary>
        private const int MaxDepth = 3;

        /// <summary>
        /// The marker that separates a spawned entity from its prefab template.
        /// MEASURED in cycle 2 as component [109] on a real component list, and
        /// it is the filter that caught StateReader.cs reading the
        /// PlayerCharacter TEMPLATE while passing 284 tests.
        /// </summary>
        private const string PrefabMarker = "Unity.Entities.Prefab";

        /// <summary>
        /// Build the /dump/components body. Returns null when the world is not
        /// ready, and the caller answers with the world_not_ready envelope.
        /// </summary>
        internal static string Dump(string build, string plugin, int guidFilter,
                                    string namePrefix, int limit, bool instanced)
        {
            World target = PrefabDumper.FindTargetWorld();
            if (target == null)
            {
                return null;
            }

            Stunlock.Core.PrefabLookupMap map;
            if (!PrefabDumper.TryGetReadyMap(target, out map))
            {
                return null;
            }

            if (limit <= 0)
            {
                limit = DefaultLimit;
            }

            if (limit > MaxLimit)
            {
                limit = MaxLimit;
            }

            var body = new StringBuilder(1 << 16);
            body.Append("{\"ok\":true,\"exploratory\":true");
            body.Append(",\"build\":").Append(Json.Str(build));
            body.Append(",\"plugin\":").Append(Json.Str(plugin));
            body.Append(",\"captured_at\":").Append(Json.Str(Json.UtcNow()));
            body.Append(",\"field_values\":\"not_read_see_ComponentDumper_header\"");
            body.Append(",\"query\":{\"guid\":").Append(guidFilter);
            body.Append(",\"name\":").Append(Json.Str(namePrefix == null ? "" : namePrefix));
            body.Append(",\"limit\":").Append(limit);
            body.Append(",\"instanced\":").Append(instanced ? "true" : "false");
            body.Append("},\"entities\":[");

            EntityManager em = target.EntityManager;
            NativeArray<Entity> all = em.GetAllEntities(Allocator.Temp);

            int written = 0;
            int scanned = 0;
            int matched = 0;

            for (int i = 0; i < all.Length && written < limit; i++)
            {
                Entity e = all[i];
                scanned++;

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

                if (guidFilter != 0 && guid.GuidHash != guidFilter)
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
                    name = "";
                }

                if (!string.IsNullOrEmpty(namePrefix)
                    && (name == null
                        || !name.StartsWith(namePrefix, StringComparison.OrdinalIgnoreCase)))
                {
                    continue;
                }

                // The prefab / instance split is decided from the ENUMERATED
                // type list, not from a HasComponent on a hoped-for name, so the
                // same pass that classifies the entity also proves the marker's
                // presence or absence in the printed output.
                bool isPrefab = CarriesPrefabMarker(em, e);
                if (instanced == isPrefab)
                {
                    continue;
                }

                matched++;

                if (written > 0)
                {
                    body.Append(',');
                }

                WriteEntity(body, em, e, guid, name, isPrefab);
                written++;
            }

            body.Append("],\"scanned\":").Append(scanned);
            body.Append(",\"matched\":").Append(matched);
            body.Append(",\"written\":").Append(written);
            return body.Append('}').ToString();
        }

        /// <summary>
        /// True when the entity carries Unity.Entities.Prefab. Decided by walking
        /// the real type list rather than by HasComponent, which keeps this file
        /// honest to its own rule even for the one type name cycle 2 measured.
        /// </summary>
        private static bool CarriesPrefabMarker(EntityManager em, Entity e)
        {
            try
            {
                var types = em.GetComponentTypes(e, Allocator.Temp);
                for (int i = 0; i < types.Length; i++)
                {
                    if (TypeName(types[i]) == PrefabMarker)
                    {
                        return true;
                    }
                }
            }
            catch (Exception)
            {
            }

            return false;
        }

        private static string TypeName(ComponentType ct)
        {
            try
            {
                var managed = ct.GetManagedType();
                if (managed != null && managed.FullName != null)
                {
                    return managed.FullName;
                }
            }
            catch (Exception)
            {
            }

            try
            {
                return ct.ToString();
            }
            catch (Exception)
            {
                return "";
            }
        }

        private static void WriteEntity(StringBuilder sb, EntityManager em, Entity e,
                                        Stunlock.Core.PrefabGUID guid, string name,
                                        bool isPrefab)
        {
            sb.Append("{\"entity_index\":").Append(e.Index);
            sb.Append(",\"entity_version\":").Append(e.Version);
            sb.Append(",\"prefab_guid\":").Append(guid.GuidHash);
            sb.Append(",\"prefab_name\":").Append(Json.Str(name));

            // The liveness assertion the spec calls stub-proof, emitted as data
            // rather than asserted in code: a template read and a live read are
            // told apart by this flag plus the entity index above.
            sb.Append(",\"carries_prefab_marker\":").Append(isPrefab ? "true" : "false");
            sb.Append(",\"components\":[");

            try
            {
                var types = em.GetComponentTypes(e, Allocator.Temp);
                for (int i = 0; i < types.Length; i++)
                {
                    if (i > 0)
                    {
                        sb.Append(',');
                    }

                    WriteComponent(sb, types[i]);
                }

                sb.Append("],\"component_count\":").Append(types.Length);
            }
            catch (Exception ex)
            {
                // Reported, never swallowed: an unreadable type list is a
                // finding about this entity, and a silently short list would
                // read as a complete one.
                sb.Append("],\"component_count\":-1,\"component_error\":")
                  .Append(Json.Str(ex.GetType().Name + ": " + ex.Message));
            }

            sb.Append('}');
        }

        private static void WriteComponent(StringBuilder sb, ComponentType ct)
        {
            sb.Append("{\"type\":").Append(Json.Str(TypeName(ct)));

            bool isBuffer = false;
            bool isZeroSized = false;
            try
            {
                isBuffer = ct.IsBuffer;
                isZeroSized = ct.IsZeroSized;
            }
            catch (Exception)
            {
            }

            sb.Append(",\"buffer\":").Append(isBuffer ? "true" : "false");
            sb.Append(",\"zero_sized\":").Append(isZeroSized ? "true" : "false");

            if (isZeroSized)
            {
                // A tag component declares nothing. Saying so explicitly is the
                // difference between "no fields" and "fields not attempted".
                sb.Append(",\"fields\":\"tag_component_no_fields\"}");
                return;
            }

            Il2CppSystem.Type managed;
            try
            {
                managed = ct.GetManagedType();
            }
            catch (Exception)
            {
                managed = null;
            }

            if (managed == null)
            {
                sb.Append(",\"fields\":\"managed_type_unavailable\"}");
                return;
            }

            // A DynamicBuffer's ELEMENT type is the interesting one, and it is
            // exactly what ComponentType names for a buffer component, so the
            // same walk serves both cases.
            sb.Append(",\"fields\":");
            WriteFields(sb, managed, 0);
            sb.Append('}');
        }

        /// <summary>
        /// Every declared instance field of a component type, by name and
        /// declared type, with nested value types expanded to MaxDepth.
        ///
        /// This walks the TYPE and never an instance, which is what makes it
        /// incapable of both failures in the file header: there is no value to
        /// get wrong and no component memory to point at. The managed
        /// reflection surface is used rather than the raw il2cpp_class_get_fields
        /// iterator, and that too is a measured choice - the raw iterator hard
        /// crashed the dedicated server on the first request, twice, while this
        /// walk has produced correct field names on every run.
        /// </summary>
        private static void WriteFields(StringBuilder sb, Il2CppSystem.Type type, int depth)
        {
            sb.Append('{');
            int written = 0;

            try
            {
                var fields = type.GetFields();
                for (int i = 0; i < fields.Length; i++)
                {
                    var field = fields[i];
                    if (field == null || field.IsStatic)
                    {
                        continue;
                    }

                    Il2CppSystem.Type declared;
                    string declaredName;
                    try
                    {
                        declared = field.FieldType;
                        declaredName = declared == null ? "" : declared.FullName;
                    }
                    catch (Exception)
                    {
                        continue;
                    }

                    if (written > 0)
                    {
                        sb.Append(',');
                    }

                    written++;
                    sb.Append(Json.Str(field.Name)).Append(":{\"type\":")
                      .Append(Json.Str(declaredName));

                    WriteShape(sb, declared, depth);
                    sb.Append('}');
                }
            }
            catch (Exception ex)
            {
                if (written > 0)
                {
                    sb.Append(',');
                }

                sb.Append("\"_field_enumeration_error\":")
                  .Append(Json.Str(ex.GetType().Name + ": " + ex.Message));
            }

            sb.Append('}');
        }

        /// <summary>
        /// For an enum, its MEMBER NAMES; for a nested struct, its own fields.
        /// Member names are why the enum branch exists: a damage type or a stat
        /// type reads as evidence and its ordinal does not, and cycle 2's whole
        /// MainType-versus-school correction turned on seeing the member list.
        /// </summary>
        private static void WriteShape(StringBuilder sb, Il2CppSystem.Type declared, int depth)
        {
            if (declared == null || depth + 1 >= MaxDepth)
            {
                return;
            }

            try
            {
                if (declared.IsEnum)
                {
                    var names = declared.GetEnumNames();
                    sb.Append(",\"enum_members\":[");
                    for (int i = 0; i < names.Length; i++)
                    {
                        if (i > 0)
                        {
                            sb.Append(',');
                        }

                        sb.Append(Json.Str(names[i]));
                    }

                    sb.Append(']');
                    return;
                }

                if (declared.IsPrimitive || !declared.IsValueType)
                {
                    return;
                }
            }
            catch (Exception)
            {
                return;
            }

            sb.Append(",\"nested\":");
            WriteFields(sb, declared, depth + 1);
        }
    }
}

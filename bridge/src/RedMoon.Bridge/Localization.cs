using System;
using System.Text;

using Unity.Entities;

namespace RedMoon.Bridge
{
    /// <summary>
    /// The prefab-to-localization join, and its own negative control.
    ///
    /// MEASURED offline (BRIDGE_SPIKES.md S7): no join exists in the extracted
    /// data at all. All 8379 strings.json keys are dashed UUIDs, and zero of 425
    /// item rows join by prefab name, by decimal guid or by any of six hex forms.
    /// The best name heuristic reached 53 of 425, which is not a join.
    ///
    /// MEASURED at runtime on the DEDICATED SERVER host (BRIDGE_SPIKES.md,
    /// section E): GameDataSystem is present, ManagedDataRegistry is present, and
    /// TryGet&lt;ManagedItemData&gt; returns false for every one of the 425
    /// equippables. The TryGetWithoutLogging overload was run as the control and
    /// agrees, so it is not a logging-path refusal - the managed presentation
    /// data simply is not loaded in a headless host.
    ///
    /// Whether the CLIENT host registers it is a DIFFERENT question with a
    /// possibly different answer, which is the whole reason this class counts
    /// rather than assumes. The counters travel inside the dump so a saved
    /// payload states which host produced it and whether the field was writable
    /// there. Reading a plugin log to find that out is not a contract.
    /// </summary>
    internal sealed class LocalizationJoin
    {
        /// <summary>present, absent, or the exception type that denied it.</summary>
        internal string Registry { get; private set; }

        internal int Attempted { get; private set; }
        internal int Resolved { get; private set; }
        internal int EmptyKey { get; private set; }
        internal int Missed { get; private set; }
        internal int QuietHits { get; private set; }

        private readonly Stunlock.Core.ManagedDataRegistry _registry;

        private LocalizationJoin(Stunlock.Core.ManagedDataRegistry registry, string state)
        {
            _registry = registry;
            Registry = state;
        }

        /// <summary>
        /// Acquire the registry, or record why not. Never throws: a host that
        /// denies the registry must still serve a dump, because the four tables
        /// that do not need localization are the ones cycle 3 actually consumes.
        /// </summary>
        internal static LocalizationJoin Open(World world)
        {
            if (world == null)
            {
                return new LocalizationJoin(null, "absent");
            }

            try
            {
                var system = world.GetExistingSystemManaged<ProjectM.GameDataSystem>();
                if (system == null)
                {
                    return new LocalizationJoin(null, "absent");
                }

                var registry = system.ManagedDataRegistry;
                if (registry == null)
                {
                    return new LocalizationJoin(null, "absent");
                }

                return new LocalizationJoin(registry, "present");
            }
            catch (Exception ex)
            {
                // The exception TYPE is the diagnosis and is carried through to
                // the operator rather than flattened into "absent".
                return new LocalizationJoin(null, "error:" + ex.GetType().Name);
            }
        }

        /// <summary>
        /// The dashed lowercase strings.json key for one prefab, or "" when the
        /// join does not resolve. "" is always OMITTED by the caller, never
        /// written as an empty field: an empty localization_guid and a missing
        /// one are different claims, and only one of them is true here.
        /// </summary>
        internal string GuidFor(Stunlock.Core.PrefabGUID guid)
        {
            if (_registry == null)
            {
                return "";
            }

            Attempted++;
            try
            {
                ProjectM.ManagedItemData data;
                if (!_registry.TryGet<ProjectM.ManagedItemData>(guid, out data))
                {
                    Missed++;

                    // The control that separates "not registered" from
                    // "registered and the logging path refused it". Without it a
                    // zero is unreadable, which is the mistake that produced the
                    // fabricated items.tier.
                    ProjectM.ManagedItemData quiet;
                    if (_registry.TryGetWithoutLogging<ProjectM.ManagedItemData>(guid, out quiet)
                        && quiet != null)
                    {
                        QuietHits++;
                    }

                    return "";
                }

                if (data == null)
                {
                    Missed++;
                    return "";
                }

                var key = data.Name;
                if (key.IsEmpty)
                {
                    EmptyKey++;
                    return "";
                }

                string dashed = key.Key.ToGuid().ToString();
                if (string.IsNullOrEmpty(dashed))
                {
                    EmptyKey++;
                    return "";
                }

                Resolved++;
                return dashed;
            }
            catch (Exception)
            {
                Missed++;
                return "";
            }
        }

        /// <summary>
        /// The counters, as the dump's own "localization" block. Emitted on EVERY
        /// dump including one that resolved nothing, because a measured zero is a
        /// result and a missing block is a dumper that owes the measurement.
        /// tools/rmdata_ingest.py reads exactly these key names.
        /// </summary>
        internal void Write(StringBuilder sb)
        {
            sb.Append("{\"registry\":").Append(Json.Str(Registry));
            sb.Append(",\"attempted\":").Append(Attempted);
            sb.Append(",\"resolved\":").Append(Resolved);
            sb.Append(",\"empty_key\":").Append(EmptyKey);
            sb.Append(",\"missed\":").Append(Missed);
            sb.Append(",\"quiet_hits\":").Append(QuietHits);
            sb.Append('}');
        }
    }
}

// The live /state producer. MAIN THREAD ONLY (spec decision D7).
//
// Everything here reads ECS, so Capture() is called from BridgeServer's
// MainThreadTick, which the injected MonoBehaviour in Plugin.cs drives from
// Update(). The listener thread only ever serves the string this produced.
//
// WHAT THIS FILE IS FOR. tools/bridge_probe.py --motion-diff takes two /state
// samples with operator movement in between and fails unless the `position` or
// `vitals` member CHANGED. A stub, a mock, a cached snapshot and a
// default-constructed component all fail that leg, which is the point of it.
// So the only useful thing this file can do is read real components off a real
// entity, and every component it reads is named below with the assembly it was
// read out of.
//
// COMPONENT TYPES, read from the interop metadata at
// <install>\BepInEx\interop\ on build 1.1.13.0-r99712. Existence and field
// names are MEASURED. What is NOT measured is that a live player character
// entity carries them, because that needs the game running:
//
//   ProjectM.Shared    ProjectM.PlayerCharacter         Name, SmartClanName, UserEntity
//   ProjectM.Shared    ProjectM.Health                  Value, MaxHealth, MaxRecoveryHealth, IsDead
//   ProjectM.Shared    ProjectM.Blood                   Value, MaxBlood, Quality, BloodType
//   ProjectM.Shared    ProjectM.Network.LocalCharacter  tag, no fields
//   Unity.Entities     Unity.Transforms.Translation     Value (float3 x, y, z)
//   Unity.Transforms   Unity.Transforms.LocalToWorld    Value, Position
//   Stunlock.Core      Stunlock.Core.PrefabGUID         GuidHash
//
// Two traps are encoded here rather than commented around:
//
//  1. WORLD SELECTION IS BY NAME, and the name list is not spelled twice - it
//     is PrefabDumper.TargetWorldNames. "Default World" is a Simulation world
//     sitting at index 0 in both hosts and it throws when asked for the prefab
//     map, so "first Simulation world" is a wrong rule that looks plausible.
//  2. A FULL ENTITY SCAN IS NOT FREE. MEASURED 95 ms in the client world. The
//     tick runs about four times a second, so scanning every tick would burn a
//     third of a core for a value that changes when a character loads. The
//     resolved entity is cached and re-validated in O(1); a rescan only happens
//     when the cache is empty and only every RescanEveryCaptures ticks.
using System;
using System.Text;
using Unity.Collections;
using Unity.Entities;

namespace RedMoon.Bridge
{
    /// <summary>
    /// One main-thread state read. `Json` is the /state envelope's `state`
    /// MEMBER, already serialized, or null when there is nothing to report;
    /// `Reason` says which, and is never a raw exception string.
    /// </summary>
    internal sealed class StateCapture
    {
        internal StateCapture(string json, string reason)
        {
            Json = json;
            Reason = reason;
        }

        internal readonly string Json;
        internal readonly string Reason;
    }

    internal static class StateReader
    {
        internal const string ReasonOk = "ok";
        internal const string ReasonNoWorld = "no_world";
        internal const string ReasonNotReady = PrefabDumper.ErrorWorldNotReady;
        internal const string ReasonNoCharacter = "no_character";
        internal const string ReasonAmbiguous = "ambiguous_character";
        internal const string ReasonReadFailed = "read_failed";

        /// <summary>
        /// Ticks between full entity scans while no character is cached. The
        /// tick fires about four times a second, so this is a rescan every five
        /// seconds or so - fast enough that loading a character shows up
        /// promptly, cheap enough that an empty world costs nothing.
        /// </summary>
        internal const int RescanEveryCaptures = 20;

        private static Entity _character;
        private static bool _haveCharacter;
        private static int _sinceScan = RescanEveryCaptures;

        /// <summary>
        /// Read the world once. `status` is what PrefabDumper.Status() already
        /// computed this tick, so the readiness gate is the SAME measured flag
        /// the dump uses and is not evaluated twice.
        /// </summary>
        internal static StateCapture Capture(WorldStatus status)
        {
            if (status == null || !status.Ready)
            {
                // GameDataInitialized was MEASURED to flip exactly as the prefab
                // map settles, so before it flips there is no world worth
                // reading and the honest answer is the spec error code.
                Forget();
                return new StateCapture(null, ReasonNotReady);
            }

            World target = FindTarget();
            if (target == null)
            {
                Forget();
                return new StateCapture(null, ReasonNoWorld);
            }

            EntityManager em;
            try
            {
                em = target.EntityManager;
            }
            catch (Exception)
            {
                Forget();
                return new StateCapture(null, ReasonNoWorld);
            }

            Entity character;
            string reason;
            if (!TryResolveCharacter(em, out character, out reason))
            {
                return new StateCapture(null, reason);
            }

            string json = BuildState(em, target, character);
            if (json == null)
            {
                return new StateCapture(null, ReasonReadFailed);
            }

            return new StateCapture(json, ReasonOk);
        }

        // -------------------------------------------------------------------
        // world selection - BY NAME, reusing the one measured list
        // -------------------------------------------------------------------
        private static World FindTarget()
        {
            var all = World.All;
            for (int t = 0; t < PrefabDumper.TargetWorldNames.Length; t++)
            {
                for (int i = 0; i < all.Count; i++)
                {
                    World world = all[i];
                    if (world != null && world.IsCreated
                        && world.Name == PrefabDumper.TargetWorldNames[t])
                    {
                        return world;
                    }
                }
            }

            return null;
        }

        // -------------------------------------------------------------------
        // which entity is the operator
        // -------------------------------------------------------------------
        private static void Forget()
        {
            _haveCharacter = false;
            _sinceScan = RescanEveryCaptures;
        }

        private static bool TryResolveCharacter(EntityManager em, out Entity found,
                                                out string reason)
        {
            if (_haveCharacter && IsStillCharacter(em, _character))
            {
                found = _character;
                reason = ReasonOk;
                return true;
            }

            _haveCharacter = false;
            found = default(Entity);

            if (_sinceScan < RescanEveryCaptures)
            {
                _sinceScan++;
                reason = ReasonNoCharacter;
                return false;
            }

            _sinceScan = 0;

            Entity local = default(Entity);
            Entity first = default(Entity);
            bool haveLocal = false;
            int players = 0;

            try
            {
                NativeArray<Entity> all = em.GetAllEntities(Allocator.Temp);
                for (int i = 0; i < all.Length; i++)
                {
                    Entity e = all[i];
                    if (!Has<ProjectM.PlayerCharacter>(em, e))
                    {
                        continue;
                    }

                    // MEASURED 2026-07-26, and this filter is the whole reason
                    // /state was lying. The prefab map holds a PlayerCharacter
                    // TEMPLATE entity, so an unfiltered scan finds it on a
                    // batchMode server with nobody connected and reports
                    // state_reason=ok with position 0,0,0 and default vitals.
                    // bridge_probe --motion-diff caught it: two samples five
                    // seconds apart were byte-identical, because a template
                    // never moves. Unity.Entities.Prefab is the tag that tells
                    // a template from an instance - it is component [109] on
                    // the real component list in the census log, not a guess.
                    // Without this, "ok" is indistinguishable from a stub.
                    if (Has<Unity.Entities.Prefab>(em, e))
                    {
                        continue;
                    }

                    if (players == 0)
                    {
                        first = e;
                    }

                    players++;

                    // The client host tags the entity the operator is driving.
                    // The server host has no local anything, and in a solo game
                    // there is one player character, which is the fallback.
                    if (!haveLocal && Has<ProjectM.Network.LocalCharacter>(em, e))
                    {
                        local = e;
                        haveLocal = true;
                    }
                }
            }
            catch (Exception)
            {
                reason = ReasonReadFailed;
                return false;
            }

            if (haveLocal)
            {
                found = local;
            }
            else if (players == 1)
            {
                found = first;
            }
            else if (players == 0)
            {
                reason = ReasonNoCharacter;
                return false;
            }
            else
            {
                // Several player characters and none tagged local. Guessing
                // would report a stranger's position as the operator's, which
                // is worse than reporting nothing.
                reason = ReasonAmbiguous;
                return false;
            }

            _character = found;
            _haveCharacter = true;
            reason = ReasonOk;
            return true;
        }

        private static bool IsStillCharacter(EntityManager em, Entity e)
        {
            try
            {
                return em.Exists(e) && em.HasComponent<ProjectM.PlayerCharacter>(e);
            }
            catch (Exception)
            {
                return false;
            }
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

        // -------------------------------------------------------------------
        // the state member
        // -------------------------------------------------------------------
        private static string BuildState(EntityManager em, World world, Entity character)
        {
            try
            {
                var sb = new StringBuilder(320);
                sb.Append("{\"world\":").Append(Json.Str(world.Name));
                sb.Append(",\"character\":");
                WriteCharacter(sb, em, character);
                WritePosition(sb, em, character);
                sb.Append(",\"vitals\":");
                WriteVitals(sb, em, character);
                return sb.Append('}').ToString();
            }
            catch (Exception)
            {
                // A partially written object would be invalid JSON, so the whole
                // capture is discarded rather than half-published.
                return null;
            }
        }

        private static void WriteCharacter(StringBuilder sb, EntityManager em, Entity e)
        {
            sb.Append('{');
            try
            {
                if (em.HasComponent<Stunlock.Core.PrefabGUID>(e))
                {
                    var guid = em.GetComponentData<Stunlock.Core.PrefabGUID>(e);
                    sb.Append("\"prefab_guid\":").Append(guid.GuidHash);
                }
            }
            catch (Exception)
            {
                // Omitted rather than faked. A zero guid cannot be told apart
                // from a real one.
            }

            sb.Append('}');
        }

        /// <summary>
        /// The motion signal --motion-diff leans on hardest.
        ///
        /// Translation is read first: it lives in the ALREADY referenced
        /// Unity.Entities assembly, which R17 measured as free of cross-host
        /// divergence, and ProjectM carries a whole family of systems named for
        /// it (UserTranslationCopySystem, GetTranslationOnSpawn,
        /// EntityTranslationSorter). LocalToWorld is the fallback for the case
        /// where a player character turns out not to carry Translation - both
        /// types are confirmed present in the interop set, neither is confirmed
        /// present on a live character entity, and the fallback costs one
        /// HasComponent call in the case that never happens.
        ///
        /// Emitted only when one of them is readable: an omitted key is honest,
        /// and a zeroed one would diff as "no motion" forever.
        /// </summary>
        private static void WritePosition(StringBuilder sb, EntityManager em, Entity e)
        {
            float x;
            float y;
            float z;

            try
            {
                if (em.HasComponent<Unity.Transforms.Translation>(e))
                {
                    Unity.Mathematics.float3 value =
                        em.GetComponentData<Unity.Transforms.Translation>(e).Value;
                    x = value.x;
                    y = value.y;
                    z = value.z;
                }
                else if (em.HasComponent<Unity.Transforms.LocalToWorld>(e))
                {
                    Unity.Mathematics.float3 value =
                        em.GetComponentData<Unity.Transforms.LocalToWorld>(e).Position;
                    x = value.x;
                    y = value.y;
                    z = value.z;
                }
                else
                {
                    return;
                }
            }
            catch (Exception)
            {
                return;
            }

            sb.Append(",\"position\":{\"x\":").Append(Json.Num(x));
            sb.Append(",\"y\":").Append(Json.Num(y));
            sb.Append(",\"z\":").Append(Json.Num(z));
            sb.Append('}');
        }

        /// <summary>
        /// The second motion signal, and the more interesting one for cycle 3:
        /// blood drains continuously in V Rising, so vitals moves even when the
        /// operator does not. Each group is emitted only when its component is
        /// actually present.
        /// </summary>
        private static void WriteVitals(StringBuilder sb, EntityManager em, Entity e)
        {
            sb.Append('{');
            int written = 0;

            try
            {
                if (em.HasComponent<ProjectM.Health>(e))
                {
                    var health = em.GetComponentData<ProjectM.Health>(e);
                    // MEASURED field types, read by making the compiler name
                    // them: Value and MaxRecoveryHealth are float, MaxHealth is
                    // a ProjectM.ModifiableFloat. `.Value` is spelled out rather
                    // than leaning on its implicit conversion, so the number
                    // emitted is visibly the modified one.
                    sb.Append("\"health\":").Append(Json.Num(health.Value));
                    sb.Append(",\"max_health\":").Append(Json.Num(health.MaxHealth.Value));
                    sb.Append(",\"max_recovery_health\":")
                      .Append(Json.Num(health.MaxRecoveryHealth));
                    sb.Append(",\"is_dead\":").Append(health.IsDead ? "true" : "false");
                    written++;
                }
            }
            catch (Exception)
            {
                // Absent or unreadable: omitted, never zeroed.
            }

            try
            {
                if (em.HasComponent<ProjectM.Blood>(e))
                {
                    var blood = em.GetComponentData<ProjectM.Blood>(e);
                    if (written > 0)
                    {
                        sb.Append(',');
                    }

                    // Value and Quality are float; MaxBlood is a ModifiableFloat
                    // and BloodType is a Stunlock.Core.PrefabGUID.
                    sb.Append("\"blood\":").Append(Json.Num(blood.Value));
                    sb.Append(",\"max_blood\":").Append(Json.Num(blood.MaxBlood.Value));
                    sb.Append(",\"blood_quality\":").Append(Json.Num(blood.Quality));
                    sb.Append(",\"blood_type\":").Append(blood.BloodType.GuidHash);
                }
            }
            catch (Exception)
            {
            }

            sb.Append('}');
        }
    }
}

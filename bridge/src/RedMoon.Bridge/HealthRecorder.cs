// The boss/target health recorder - falsification spec section A.4.
//
// WHAT THIS IS FOR. Nothing in this project can currently falsify a computed
// time-to-kill. This file is the thing that can: it records a boss's
// ProjectM.Health.Value at the tick rate, with the controls that make the series
// discardable when it is wrong, so a Bloodforge TTK has something real to be
// wrong against.
//
// WHY NOT /dump/statcontrol. That endpoint walks every entity in the world per
// request (ComponentDumper.cs:504) against a MEASURED 95 ms full-scan cost
// (StateReader.cs:34-38), under a one-at-a-time gate (BridgeServer.cs:444-453).
// Polling it four times a second would burn a third of a core and contend with
// itself for the whole fight. So the subject is resolved ONCE by full scan and
// re-validated in O(1) thereafter; a rescan happens only when the handle goes
// stale, and then at most every StateReader.RescanEveryCaptures ticks, so a
// despawned subject cannot make the tick pay 95 ms four times a second.
//
// THREADING, spec decision D7. Everything here that touches ECS runs on the
// MAIN THREAD, from BridgeServer.MainThreadTick. Arm and stop ride the existing
// DumpRequest hand-off for exactly that reason. Status is the one thing served
// from the listener thread, and it reads published scalars only - it never
// scans and never touches ECS.
//
// VALUE READS ARE TYPED ACCESSORS ONLY, and that is a measured result rather
// than a preference. A generic value reader was built twice on this build and
// failed twice: managed reflection through EntityManagerDebug.GetComponentBoxed
// returned 539327184 for every Int32, and raw il2cpp field offsets off the same
// pointer HARD CRASHED the dedicated server. This file therefore copies the
// exact idiom of ComponentDumper.WriteStatValues - a fixed, spelled-out list of
// fields with their types - and wraps each component group in its own try/catch
// that OMITS the group on failure rather than zeroing it. A zero and an
// unreadable field are different claims and only one of them is ever true.
//
// ERROR HANDLING, CLAUDE.md: no raw exception string reaches a caller. The
// detail goes to the BepInEx log; the response carries a code and a friendly
// message built by BridgeServer.Error.
using System;
using System.Text;
using BepInEx.Logging;
using Unity.Collections;
using Unity.Entities;

namespace RedMoon.Bridge
{
    internal static class HealthRecorder
    {
        /// <summary>
        /// Hard capacity, about 17 minutes at 4 Hz.
        ///
        /// IT IS STOP-AT-CAP, NOT AN OVERWRITING WRAP-AROUND BUFFER, and the
        /// difference is load-bearing. Falsification check A.5.3 requires the
        /// FIRST sample to equal max health, because a run that did not start
        /// from full is excluded from the TTK gate. A wrap-around buffer
        /// silently discards the START of the fight, so an overlong recording
        /// would arrive looking like a perfectly clean short one. A true prefix
        /// plus a nonzero dropped count cannot be misread that way: the series
        /// is honest about where it stops and the count says how much is gone.
        /// </summary>
        internal const int MaxSamples = 4096;

        internal const string KindStart = "record_start";
        internal const string KindStatus = "record_status";
        internal const string KindStop = "record_stop";

        internal const string ErrorBadRequest = "bad_request";
        internal const string ErrorAlreadyRecording = "already_recording";
        internal const string ErrorNotRecording = "not_recording";

        /// <summary>
        /// The phase 3 timing trap, encoded as a PRECONDITION rather than
        /// commented around. The prefab and the live instance carry the SAME
        /// PrefabGUID, the prefab reads Health.Value 0, and the first phase 3
        /// control found only the prefab at about 5 s of server uptime and the
        /// instance by 20 s. A recorder latched onto the prefab therefore
        /// records a flat zero series that a naive reading turns into an
        /// instantaneous kill. Poll for the SUBJECT, never for ready:true.
        /// </summary>
        internal const string ErrorSubjectNotSpawned = "subject_not_spawned";

        private const string MessageAlreadyRecording =
            "a recording is already armed, stop it before starting another";

        private const string MessageNotRecording =
            "nothing has been recorded, arm the recorder first";

        private const string MessageSubjectNotSpawned =
            "that prefab exists but nothing is spawned from it yet, spawn the "
            + "subject and try again";

        private const string MessageBadGuid =
            "pass a nonzero guid so the recorder has a subject";

        private const string MessageArmFailed =
            "the recorder could not read the subject, see the plugin log";

        // -------------------------------------------------------------------
        // published state
        //
        // Written on the main thread only, read by the listener thread for
        // /record/status. Volatile scalars, so the status endpoint never has to
        // take a lock on the path a boss fight is running down.
        // -------------------------------------------------------------------
        private static volatile bool _armed;
        private static volatile int _guid;
        private static volatile int _sampleCount;
        private static volatile int _dropped;
        private static volatile string _startedAt = "";

        // Main-thread only below this line.
        private static string _runJson;
        private static StringBuilder _samples;

        private static Entity _subject;
        private static bool _haveSubject;
        private static int _sinceScan;

        private static Entity _character;
        private static bool _haveCharacter;
        private static int _sinceCharacterScan;

        // -------------------------------------------------------------------
        // listener thread
        // -------------------------------------------------------------------
        /// <summary>
        /// The one endpoint served without the main-thread hand-off. It reads
        /// published scalars and never scans, so polling it during a fight costs
        /// nothing measurable.
        /// </summary>
        internal static string Status()
        {
            var sb = new StringBuilder(160);
            sb.Append("{\"ok\":true");
            sb.Append(",\"armed\":").Append(_armed ? "true" : "false");
            sb.Append(",\"guid\":").Append(_guid);
            sb.Append(",\"sample_count\":").Append(_sampleCount);
            sb.Append(",\"dropped\":").Append(_dropped);
            sb.Append(",\"started_at\":").Append(Json.Str(_startedAt));
            return sb.Append('}').ToString();
        }

        // -------------------------------------------------------------------
        // main thread - the ONLY place ECS is touched
        // -------------------------------------------------------------------
        /// <summary>
        /// Service one armed request. Returns the body, or null to mean "the
        /// world was not ready", which the caller answers with the existing
        /// world_not_ready envelope. `request.Status` carries the HTTP status
        /// for the cases that are not 200.
        /// </summary>
        internal static string Handle(ManualLogSource log, DumpRequest request,
                                      string build, string plugin, string host)
        {
            if (request.RecordKind == KindStop)
            {
                return Stop(log, request, build, plugin, host);
            }

            return Start(log, request, build, plugin, host);
        }

        /// <summary>
        /// One sample per tick, which is 4 Hz.
        ///
        /// THE SAMPLE RATE IS A CEILING, NOT A KNOB. It is set by
        /// SampleEveryFrames = 15 in Plugin.cs and the falsification spec
        /// section C tolerances were computed against it, so there is
        /// deliberately no rate parameter anywhere in this file.
        /// </summary>
        internal static void Sample(ManualLogSource log)
        {
            if (!_armed)
            {
                return;
            }

            if (_sampleCount >= MaxSamples)
            {
                // Stop-at-cap. The series already held is a true prefix and the
                // dropped count says how much of the fight is missing.
                _dropped = _dropped + 1;
                return;
            }

            World target = PrefabDumper.FindTargetWorld();
            if (target == null)
            {
                _dropped = _dropped + 1;
                return;
            }

            EntityManager em;
            try
            {
                em = target.EntityManager;
            }
            catch (Exception)
            {
                _dropped = _dropped + 1;
                return;
            }

            Entity subject;
            if (!TryResolveSubject(em, out subject))
            {
                // The subject may have been destroyed - HealthConstants
                // DestroyOnDeath and DestroyAfterDuration both exist, so a
                // vanished boss is a terminal event, not a fault. Either way
                // nothing is recorded for this tick and the tick is counted.
                _dropped = _dropped + 1;
                return;
            }

            string sample = BuildSample(em, subject);
            if (sample == null)
            {
                _dropped = _dropped + 1;
                return;
            }

            if (_samples == null)
            {
                _samples = new StringBuilder(1 << 16);
            }

            if (_sampleCount > 0)
            {
                _samples.Append(',');
            }

            _samples.Append(sample);
            _sampleCount = _sampleCount + 1;
        }

        // -------------------------------------------------------------------
        // arm
        // -------------------------------------------------------------------
        private static string Start(ManualLogSource log, DumpRequest request,
                                    string build, string plugin, string host)
        {
            if (_armed)
            {
                request.Status = 409;
                return BridgeServer.Error(ErrorAlreadyRecording, MessageAlreadyRecording);
            }

            World target = PrefabDumper.FindTargetWorld();
            if (target == null)
            {
                return null; // world_not_ready
            }

            Stunlock.Core.PrefabLookupMap map;
            if (!PrefabDumper.TryGetReadyMap(target, out map))
            {
                return null; // world_not_ready
            }

            EntityManager em;
            try
            {
                em = target.EntityManager;
            }
            catch (Exception ex)
            {
                log.LogWarning("recorder could not take the entity manager: "
                               + ex.GetType().Name + ": " + ex.Message);
                return null;
            }

            // The ONE full scan this recorder is allowed. Everything after it is
            // an O(1) re-validation.
            Entity live;
            bool sawPrefabOnly;
            if (!TryScanForSubject(log, em, request.Guid, out live, out sawPrefabOnly))
            {
                request.Status = 404;
                log.LogWarning("recorder found no live entity for guid " + request.Guid
                               + " (prefab seen: " + sawPrefabOnly + ")");
                return BridgeServer.Error(ErrorSubjectNotSpawned, MessageSubjectNotSpawned);
            }

            string name;
            try
            {
                name = map.GetName(em.GetComponentData<Stunlock.Core.PrefabGUID>(live));
            }
            catch (Exception)
            {
                name = "";
            }

            string run = BuildRun(em, live, request.Guid, name, request.Note);
            if (run == null)
            {
                request.Status = 500;
                log.LogError("recorder could not build the run manifest for guid "
                             + request.Guid);
                return BridgeServer.Error("internal", MessageArmFailed);
            }

            _subject = live;
            _haveSubject = true;
            _sinceScan = 0;
            _guid = request.Guid;
            _samples = new StringBuilder(1 << 16);
            _sampleCount = 0;
            _dropped = 0;
            _startedAt = Json.UtcNow();
            _runJson = run;
            _armed = true;

            log.LogInfo("recorder armed on guid " + request.Guid + " entity " + live.Index);

            var sb = new StringBuilder(2048);
            sb.Append("{\"ok\":true,\"armed\":true");
            sb.Append(",\"build\":").Append(Json.Str(build));
            sb.Append(",\"plugin\":").Append(Json.Str(plugin));
            sb.Append(",\"host\":").Append(Json.Str(host));
            sb.Append(",\"captured_at\":").Append(Json.Str(_startedAt));
            sb.Append(",\"run\":").Append(run);
            return sb.Append('}').ToString();
        }

        /// <summary>
        /// The full scan, and the precondition that makes the series readable.
        ///
        /// It REQUIRES a match whose carries_prefab_marker is false. A prefab
        /// match alone is reported as subject_not_spawned, never latched onto.
        /// `sawPrefabOnly` says which of the two failures happened, for the log.
        /// </summary>
        private static bool TryScanForSubject(ManualLogSource log, EntityManager em,
                                              int guidFilter, out Entity found,
                                              out bool sawPrefabOnly)
        {
            found = default(Entity);
            sawPrefabOnly = false;

            try
            {
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

                    if (guid.GuidHash != guidFilter)
                    {
                        continue;
                    }

                    if (ComponentDumper.CarriesPrefabMarker(em, e))
                    {
                        sawPrefabOnly = true;
                        continue;
                    }

                    found = e;
                    return true;
                }
            }
            catch (Exception ex)
            {
                // `log` is null on the per-tick rescan path: a scan that fails
                // four times a second would flood the BepInEx log, and the
                // dropped counter already carries the same fact in a form the
                // Python side can read.
                if (log != null)
                {
                    log.LogWarning("recorder scan failed: "
                                   + ex.GetType().Name + ": " + ex.Message);
                }

                return false;
            }

            return false;
        }

        // -------------------------------------------------------------------
        // stop
        // -------------------------------------------------------------------
        private static string Stop(ManualLogSource log, DumpRequest request,
                                   string build, string plugin, string host)
        {
            if (!_armed && _runJson == null)
            {
                request.Status = 409;
                return BridgeServer.Error(ErrorNotRecording, MessageNotRecording);
            }

            var sb = new StringBuilder(1 << 16);
            sb.Append("{\"ok\":true,\"armed\":false");
            sb.Append(",\"build\":").Append(Json.Str(build));
            sb.Append(",\"plugin\":").Append(Json.Str(plugin));
            sb.Append(",\"host\":").Append(Json.Str(host));
            sb.Append(",\"captured_at\":").Append(Json.Str(Json.UtcNow()));
            sb.Append(",\"started_at\":").Append(Json.Str(_startedAt));
            sb.Append(",\"run\":").Append(_runJson == null ? "null" : _runJson);
            sb.Append(",\"sample_count\":").Append(_sampleCount);
            sb.Append(",\"dropped\":").Append(_dropped);
            sb.Append(",\"samples\":[");
            if (_samples != null)
            {
                sb.Append(_samples.ToString());
            }

            sb.Append("]}");

            log.LogInfo("recorder stopped on guid " + _guid + " with " + _sampleCount
                        + " samples and " + _dropped + " dropped ticks");

            Clear();
            return sb.ToString();
        }

        private static void Clear()
        {
            _armed = false;
            _guid = 0;
            _sampleCount = 0;
            _dropped = 0;
            _startedAt = "";
            _runJson = null;
            _samples = null;
            _haveSubject = false;
            _sinceScan = 0;
            _haveCharacter = false;
            _sinceCharacterScan = 0;
        }

        // -------------------------------------------------------------------
        // the subject handle
        // -------------------------------------------------------------------
        /// <summary>
        /// O(1) re-validation: the handle still exists AND still carries the
        /// guid that was armed. A rescan happens only when that fails, and then
        /// only every StateReader.RescanEveryCaptures ticks, which is the same
        /// throttle /state uses for the same measured reason.
        /// </summary>
        private static bool TryResolveSubject(EntityManager em, out Entity found)
        {
            if (_haveSubject && StillTheSubject(em, _subject))
            {
                found = _subject;
                return true;
            }

            _haveSubject = false;
            found = default(Entity);

            if (_sinceScan < StateReader.RescanEveryCaptures)
            {
                _sinceScan++;
                return false;
            }

            _sinceScan = 0;

            Entity live;
            bool sawPrefabOnly;
            if (!TryScanForSubject(null, em, _guid, out live, out sawPrefabOnly))
            {
                return false;
            }

            _subject = live;
            _haveSubject = true;
            found = live;
            return true;
        }

        private static bool StillTheSubject(EntityManager em, Entity e)
        {
            try
            {
                if (!em.Exists(e) || !em.HasComponent<Stunlock.Core.PrefabGUID>(e))
                {
                    return false;
                }

                return em.GetComponentData<Stunlock.Core.PrefabGUID>(e).GuidHash == _guid;
            }
            catch (Exception)
            {
                return false;
            }
        }

        /// <summary>
        /// The player character, resolved by the same rules StateReader uses:
        /// ProjectM.PlayerCharacter, NOT carrying Unity.Entities.Prefab (the
        /// prefab map holds a PlayerCharacter TEMPLATE and an unfiltered scan
        /// finds it with nobody connected), preferring the LocalCharacter tag
        /// and falling back to the single player in a solo game. Resolved
        /// separately here rather than reaching into StateReader's cache,
        /// because that cache is private and this file is not allowed to edit
        /// it - the duplication is deliberate and both sides are throttled the
        /// same way.
        /// </summary>
        /// <summary>
        /// Resolve the player character, honouring the rescan throttle unless
        /// `force` says otherwise.
        ///
        /// WHY `force` EXISTS, and it is a bug fix rather than an option.
        /// MEASURED 2026-08-01 against a live dedicated server: the arm returned
        /// player_resolved false while the SAMPLES it went on to take carried a
        /// full player block from index 19 onward. The cause is that the arm
        /// path reset _sinceCharacterScan and then immediately consulted the
        /// throttle it had just reset, so it declined to scan and reported the
        /// decline as an absence. Those two states are not the same and the
        /// caller cannot tell them apart, which is the same shape as the phase 1
        /// generic reader: a silent gate is indistinguishable from an unwired one.
        ///
        /// It matters more than a cosmetic flag. player_unit_stats at t0 is what
        /// falsification spec B.1 requires and it is the ENTIRE comparison basis
        /// of the power-stat experiment - the prediction is literally that the
        /// observed health delta equals PhysicalPower or SpellPower - so an arm
        /// that silently omits it produces a run that cannot decide anything.
        /// The arm is a one-shot that already pays one full scan for the boss;
        /// paying a second is the cheapest possible fix.
        /// </summary>
        private static bool TryResolveCharacter(EntityManager em, bool force, out Entity found)
        {
            if (_haveCharacter && StillCharacter(em, _character))
            {
                found = _character;
                return true;
            }

            _haveCharacter = false;
            found = default(Entity);

            if (!force && _sinceCharacterScan < StateReader.RescanEveryCaptures)
            {
                _sinceCharacterScan++;
                return false;
            }

            _sinceCharacterScan = 0;

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

                    if (Has<Unity.Entities.Prefab>(em, e))
                    {
                        continue;
                    }

                    if (players == 0)
                    {
                        first = e;
                    }

                    players++;

                    if (!haveLocal && Has<ProjectM.Network.LocalCharacter>(em, e))
                    {
                        local = e;
                        haveLocal = true;
                    }
                }
            }
            catch (Exception)
            {
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
            else
            {
                // Zero players, or several with none tagged local. Guessing
                // would put a stranger's health in the operator's series.
                return false;
            }

            _character = found;
            _haveCharacter = true;
            return true;
        }

        private static bool StillCharacter(EntityManager em, Entity e)
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
        // the run manifest, written once at arm
        // -------------------------------------------------------------------
        /// <summary>
        /// The t0 block section B.1 requires. player_unit_stats is what the
        /// power-stat experiment reads: the whole experiment is "does the
        /// observed health delta equal PhysicalPower or SpellPower", and that
        /// question needs the powers as they stood when the fight started.
        ///
        /// Every player_* key is OMITTED ENTIRELY when the character could not
        /// be resolved on this tick. Never zeroed and never null: a zero
        /// PhysicalPower is a real and different statement.
        /// </summary>
        private static string BuildRun(EntityManager em, Entity subject, int guid,
                                       string name, string note)
        {
            try
            {
                var sb = new StringBuilder(2048);
                sb.Append("{\"boss_prefab_guid\":").Append(guid);
                sb.Append(",\"boss_prefab_name\":").Append(Json.Str(name));
                sb.Append(",\"boss_entity_index\":").Append(subject.Index);

                // Restated from the scan that just required it to be false. It
                // is written out rather than assumed so the arm body and the
                // samples carry the same control in the same spelling.
                sb.Append(",\"carries_prefab_marker\":")
                  .Append(ComponentDumper.CarriesPrefabMarker(em, subject) ? "true" : "false");

                try
                {
                    if (em.HasComponent<ProjectM.Health>(subject))
                    {
                        var health = em.GetComponentData<ProjectM.Health>(subject);
                        sb.Append(",\"boss_max_health_observed\":")
                          .Append(Json.Num(health.MaxHealth._Value));
                        sb.Append(",\"boss_health_value_at_arm\":")
                          .Append(Json.Num(health.Value));
                    }
                }
                catch (Exception)
                {
                    // Omitted, never zeroed: 0 is what the PREFAB reads, and
                    // that is exactly the value this recorder exists to refuse.
                }

                try
                {
                    if (em.HasComponent<ProjectM.UnitStats>(subject))
                    {
                        var s = em.GetComponentData<ProjectM.UnitStats>(subject);
                        sb.Append(",\"boss_resistances_observed\":{");
                        sb.Append("\"physical\":").Append(Json.Num(s.PhysicalResistance._Value));
                        sb.Append(",\"spell\":").Append(Json.Num(s.SpellResistance._Value));
                        sb.Append(",\"fire\":").Append(Json.Num(s.FireResistance._Value));
                        // CorruptionDamageReduction is the only corruption-side
                        // field in the typed list phase 3 proved readable on
                        // this build. There is no CorruptionResistance member to
                        // read, so the key is named for the concept and the
                        // source field is named here rather than guessed at.
                        sb.Append(",\"corruption\":")
                          .Append(Json.Num(s.CorruptionDamageReduction._Value));
                        sb.Append('}');
                    }
                }
                catch (Exception)
                {
                }

                try
                {
                    if (em.HasComponent<ProjectM.UnitLevel>(subject))
                    {
                        var level = em.GetComponentData<ProjectM.UnitLevel>(subject);
                        sb.Append(",\"boss_unit_level\":").Append(Json.Num(level.Level._Value));
                    }
                }
                catch (Exception)
                {
                }

                Entity character;
                bool resolved = TryResolveCharacter(em, true, out character);
                sb.Append(",\"player_resolved\":").Append(resolved ? "true" : "false");
                if (resolved)
                {
                    WritePlayerBlock(sb, em, character);
                }

                sb.Append(",\"operator_note\":").Append(Json.Str(note == null ? "" : note));
                return sb.Append('}').ToString();
            }
            catch (Exception)
            {
                // A half-written object is invalid JSON, so the whole manifest
                // is discarded rather than published broken.
                return null;
            }
        }

        private static void WritePlayerBlock(StringBuilder sb, EntityManager em, Entity e)
        {
            try
            {
                if (em.HasComponent<ProjectM.UnitLevel>(e))
                {
                    var level = em.GetComponentData<ProjectM.UnitLevel>(e);
                    sb.Append(",\"player_unit_level\":").Append(Json.Num(level.Level._Value));
                }
            }
            catch (Exception)
            {
            }

            try
            {
                if (em.HasComponent<ProjectM.Health>(e))
                {
                    var health = em.GetComponentData<ProjectM.Health>(e);
                    sb.Append(",\"player_max_health\":")
                      .Append(Json.Num(health.MaxHealth._Value));
                }
            }
            catch (Exception)
            {
            }

            try
            {
                if (em.HasComponent<ProjectM.UnitStats>(e))
                {
                    var s = em.GetComponentData<ProjectM.UnitStats>(e);
                    int written = 0;
                    sb.Append(",\"player_unit_stats\":{");

                    // THE SAME FIXED LIST, IN THE SAME KEY SPELLING, as
                    // ComponentDumper.WriteStatValues. Sharing the spelling is
                    // what lets a t0 block and a /dump/statcontrol row be
                    // compared field by field without a translation table.
                    Stat(sb, ref written, "UnitStats.PhysicalPower", s.PhysicalPower._Value);
                    Stat(sb, ref written, "UnitStats.SpellPower", s.SpellPower._Value);
                    Stat(sb, ref written, "UnitStats.ResourcePower", s.ResourcePower._Value);
                    Stat(sb, ref written, "UnitStats.SiegePower", s.SiegePower._Value);
                    Stat(sb, ref written, "UnitStats.PhysicalResistance",
                         s.PhysicalResistance._Value);
                    Stat(sb, ref written, "UnitStats.SpellResistance", s.SpellResistance._Value);
                    Stat(sb, ref written, "UnitStats.FireResistance", s.FireResistance._Value);
                    Stat(sb, ref written, "UnitStats.PassiveHealthRegen",
                         s.PassiveHealthRegen._Value);
                    Stat(sb, ref written, "UnitStats.CCReduction", s.CCReduction._Value);
                    Stat(sb, ref written, "UnitStats.HealthRecovery", s.HealthRecovery._Value);
                    Stat(sb, ref written, "UnitStats.DamageReduction", s.DamageReduction._Value);
                    Stat(sb, ref written, "UnitStats.HealingReceived", s.HealingReceived._Value);
                    Stat(sb, ref written, "UnitStats.ReducedBloodDrain",
                         s.ReducedBloodDrain._Value);
                    Stat(sb, ref written, "UnitStats.BloodDrainMultiplier",
                         s.BloodDrainMultiplier._Value);
                    Stat(sb, ref written, "UnitStats.CorruptionDamageReduction",
                         s.CorruptionDamageReduction._Value);
                    sb.Append('}');
                }
            }
            catch (Exception)
            {
            }
        }

        private static void Stat(StringBuilder sb, ref int written, string key, float value)
        {
            if (written > 0)
            {
                sb.Append(',');
            }

            sb.Append(Json.Str(key)).Append(':').Append(Json.Num(value));
            written++;
        }

        // -------------------------------------------------------------------
        // one sample
        // -------------------------------------------------------------------
        /// <summary>
        /// Returns null when the boss health group could not be read, which the
        /// caller counts as a dropped tick. A sample without health is not a
        /// sample - it would satisfy the schema's required list only by being
        /// zeroed, and a zeroed health series is precisely the failure mode this
        /// whole file is built to make impossible.
        ///
        /// EVERY sample RESTATES prefab_guid and carries_prefab_marker. That
        /// restatement is the control that caught the phase 1 generic reader: a
        /// sample restating a guid other than the armed one means the recorder
        /// followed a stale entity handle, and the run is discarded rather than
        /// smoothed.
        /// </summary>
        private static string BuildSample(EntityManager em, Entity subject)
        {
            try
            {
                if (!em.HasComponent<ProjectM.Health>(subject))
                {
                    return null;
                }

                var health = em.GetComponentData<ProjectM.Health>(subject);

                int guid = _guid;
                try
                {
                    if (em.HasComponent<Stunlock.Core.PrefabGUID>(subject))
                    {
                        guid = em.GetComponentData<Stunlock.Core.PrefabGUID>(subject).GuidHash;
                    }
                }
                catch (Exception)
                {
                }

                var sb = new StringBuilder(320);
                sb.Append("{\"index\":").Append(_sampleCount);
                // MILLISECOND resolution deliberately, and not the envelope's
                // whole-second stamp: at 4 Hz a whole second gives four samples
                // the same instant, and every timing the falsification spec
                // derives from the series - the 750 ms gap discard, the 2.0 s
                // idle window, the bracketing of an isolated delta - would be
                // computed against a clock too coarse to express them.
                sb.Append(",\"captured_at\":").Append(Json.Str(Json.UtcNowMillis()));
                sb.Append(",\"prefab_guid\":").Append(guid);
                sb.Append(",\"carries_prefab_marker\":")
                  .Append(ComponentDumper.CarriesPrefabMarker(em, subject) ? "true" : "false");
                sb.Append(",\"health_value\":").Append(Json.Num(health.Value));
                sb.Append(",\"health_max\":").Append(Json.Num(health.MaxHealth._Value));
                sb.Append(",\"is_dead\":").Append(health.IsDead ? "true" : "false");

                Entity character;
                if (TryResolveCharacter(em, false, out character))
                {
                    WriteCharacterSample(sb, em, character);
                }

                return sb.Append('}').ToString();
            }
            catch (Exception)
            {
                return null;
            }
        }

        /// <summary>
        /// The player half of a sample. Both pairs are omitted rather than
        /// zeroed when their component is unreadable, per the anchor schema.
        /// blood_type_guid is the RAW int: the Python writer joins it to
        /// tables/blood_types.json for the name, so no lookup is attempted here.
        /// </summary>
        private static void WriteCharacterSample(StringBuilder sb, EntityManager em, Entity e)
        {
            try
            {
                if (em.HasComponent<ProjectM.Health>(e))
                {
                    var health = em.GetComponentData<ProjectM.Health>(e);
                    sb.Append(",\"player_health_value\":").Append(Json.Num(health.Value));
                    sb.Append(",\"player_health_max\":")
                      .Append(Json.Num(health.MaxHealth._Value));
                }
            }
            catch (Exception)
            {
            }

            try
            {
                if (em.HasComponent<ProjectM.Blood>(e))
                {
                    var blood = em.GetComponentData<ProjectM.Blood>(e);
                    sb.Append(",\"blood_quality\":").Append(Json.Num(blood.Quality));
                    sb.Append(",\"blood_type_guid\":").Append(blood.BloodType.GuidHash);
                }
            }
            catch (Exception)
            {
            }
        }
    }
}

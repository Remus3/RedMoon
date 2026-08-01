// The loopback HTTP surface: /health, /state and /dump/prefabs.
//
// THREADING, spec decision D7 and the one rule this file exists to keep. ECS is
// read ONLY on the game's main thread, from MainThreadTick(), which the injected
// MonoBehaviour in Plugin.cs calls from Update(). The listener thread never
// touches ECS. It serves a snapshot the tick already produced, and for the one
// endpoint that cannot be served from a snapshot - the prefab dump, which is a
// one-shot and expensive - it hands a request to the tick and waits on an event
// with a timeout, so a wedged main thread degrades into an error code instead of
// hanging the listener forever.
//
// ERROR HANDLING, CLAUDE.md: no raw exception string ever reaches a caller. The
// raw detail goes to the BepInEx log; the response carries a code and a friendly
// message.
using System;
using System.Globalization;
using System.Net;
using System.Text;
using System.Threading;
using BepInEx.Logging;

namespace RedMoon.Bridge
{
    /// <summary>Just enough JSON to emit the documented bodies, ASCII-safe.</summary>
    internal static class Json
    {
        internal static string Str(string value)
        {
            if (value == null)
            {
                return "null";
            }

            var sb = new StringBuilder(value.Length + 2);
            sb.Append('"');
            for (int i = 0; i < value.Length; i++)
            {
                char c = value[i];
                if (c == '"' || c == '\\')
                {
                    sb.Append('\\').Append(c);
                }
                else if (c == '\n')
                {
                    sb.Append("\\n");
                }
                else if (c == '\r')
                {
                    sb.Append("\\r");
                }
                else if (c == '\t')
                {
                    sb.Append("\\t");
                }
                else if (c < 0x20 || c > 0x7E)
                {
                    // Escaped rather than emitted raw: the payload is written as
                    // ASCII bytes, and a prefab name is not guaranteed to be.
                    sb.Append("\\u").Append(((int)c).ToString("x4", CultureInfo.InvariantCulture));
                }
                else
                {
                    sb.Append(c);
                }
            }

            return sb.Append('"').ToString();
        }

        /// <summary>Invariant, and never NaN or Infinity - neither is legal JSON.</summary>
        internal static string Num(double value)
        {
            if (double.IsNaN(value) || double.IsInfinity(value))
            {
                return "0";
            }

            return value.ToString("0.######", CultureInfo.InvariantCulture);
        }

        internal static string UtcNow()
        {
            return DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
        }

        /// <summary>
        /// The same instant at MILLISECOND resolution, for the anchor recorder
        /// and nothing else.
        ///
        /// WHY A SECOND FUNCTION RATHER THAN WIDENING THE FIRST. The envelope
        /// stamp above serves /health, /state and the dumps, where the interesting
        /// quantity changes on the order of seconds. The recorder samples at 4 Hz
        /// (Plugin.cs:41, SampleEveryFrames = 15), so a whole-second stamp gives
        /// FOUR samples the same captured_at and silently destroys every timing
        /// the falsification spec computes from the series: the A.5 discard on a
        /// sample gap over 750 ms cannot see a 750 ms gap at 1 s resolution, the
        /// C.2 idle window is 2.0 s, and an isolated delta is defined by its
        /// bracketing samples. The sample index stays the ordering; this is the
        /// clock.
        /// </summary>
        internal static string UtcNowMillis()
        {
            return DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ",
                                            CultureInfo.InvariantCulture);
        }
    }

    /// <summary>What the last main-thread tick saw. Immutable once published.</summary>
    internal sealed class BridgeSnapshot
    {
        internal BridgeSnapshot(WorldStatus status, StateCapture capture)
        {
            WorldName = status.TargetName;
            WorldNames = status.WorldNames;
            Ready = status.Ready;
            PrefabCount = status.PrefabCount;
            StateJson = capture == null ? null : capture.Json;
            StateReason = capture == null ? StateReader.ReasonReadFailed : capture.Reason;
            CapturedAt = DateTime.UtcNow;
        }

        internal readonly string WorldName;
        internal readonly string[] WorldNames;
        internal readonly bool Ready;
        internal readonly int PrefabCount;

        /// <summary>
        /// The /state envelope's `state` MEMBER, already serialized by the main
        /// thread, or null when there was nothing to report. The listener thread
        /// appends this string and never parses or rebuilds it.
        /// </summary>
        internal readonly string StateJson;

        /// <summary>Why StateJson is null, as a fixed code, never a raw error.</summary>
        internal readonly string StateReason;

        internal readonly DateTime CapturedAt;
    }

    /// <summary>A dump the listener thread asked the main thread to produce.</summary>
    internal sealed class DumpRequest
    {
        internal DumpRequest(string table)
        {
            Table = table;
        }

        /// <summary>
        /// The EXPLORATORY component dump (cycle 3 phase 1). It rides the same
        /// main-thread handoff as the table dump rather than getting a second
        /// one, because D7's whole point is that there is exactly one place ECS
        /// is read from.
        /// </summary>
        internal DumpRequest(int guid, string namePrefix, int limit, bool instanced)
        {
            Components = true;
            Guid = guid;
            NamePrefix = namePrefix;
            Limit = limit;
            Instanced = instanced;
        }

        /// <summary>
        /// The EXPLORATORY prefab-versus-instance VALUE control (cycle 3 phase
        /// 3). Separate from the component dump because that one reads NAMES
        /// only, by measured necessity: a generic value reader was built twice
        /// on this build and failed twice. This one reads a FIXED, spelled-out
        /// list of typed fields, which is the only thing that works here.
        /// </summary>
        internal DumpRequest(int guid, bool statValues)
        {
            StatValues = statValues;
            Guid = guid;
        }

        /// <summary>
        /// The HEALTH RECORDER hand-off (falsification spec A.4). Arming and
        /// stopping the recorder both touch ECS and both mutate main-thread-only
        /// state, so they ride this same hand-off rather than getting a second
        /// one - D7's whole point is that there is exactly one place ECS is read
        /// from. /record/status does NOT come through here: it reads published
        /// scalars off the listener thread and never scans.
        /// </summary>
        internal DumpRequest(string recordKind, int guid, string note)
        {
            RecordKind = recordKind;
            Guid = guid;
            Note = note;
        }

        internal readonly string Table;
        internal readonly bool Components;
        internal readonly bool StatValues;
        internal readonly string RecordKind;
        internal readonly string Note;
        internal readonly int Guid;
        internal readonly string NamePrefix;
        internal readonly int Limit;
        internal readonly bool Instanced;
        internal readonly ManualResetEventSlim Done = new ManualResetEventSlim(false);
        internal string Body;

        /// <summary>
        /// The HTTP status for a body that is not a 200. Zero means "the default
        /// for this outcome", which keeps every pre-existing request kind on
        /// exactly the behaviour it had before the recorder existed.
        /// </summary>
        internal int Status;
    }

    internal sealed class BridgeServer
    {
        internal const string Bound = "127.0.0.1";

        /// <summary>
        /// How long a caller waits for the main thread to produce a dump. The
        /// measured cost is 57 ms for 47573 entities, so anything near this
        /// ceiling means the tick is not running, not that the dump is slow.
        /// </summary>
        internal const int DumpTimeoutMs = 30000;

        private readonly ManualLogSource _log;
        private readonly string _host;
        private readonly string _build;
        private readonly string _plugin;
        private readonly string _gameRoot;
        private readonly int _port;
        private readonly DateTime _startedAt = DateTime.UtcNow;
        private readonly object _dumpGate = new object();

        private HttpListener _listener;
        private Thread _thread;
        private volatile bool _stopping;
        private volatile BridgeSnapshot _snapshot;
        private volatile DumpRequest _pending;

        internal BridgeServer(ManualLogSource log, string host, int port,
                              string build, string plugin, string gameRoot)
        {
            _log = log;
            _host = host;
            _port = port;
            _build = build;
            _plugin = plugin;
            _gameRoot = gameRoot;
        }

        // -------------------------------------------------------------------
        // lifecycle
        // -------------------------------------------------------------------
        internal bool Start()
        {
            string prefix = "http://" + Bound + ":" + _port + "/";
            try
            {
                _listener = new HttpListener();
                _listener.Prefixes.Add(prefix);
                _listener.Start();
            }
            catch (Exception ex)
            {
                // A lost bind is a stand-down, not a crash: the operator's game
                // must not be taken down by a bridge that cannot listen.
                _log.LogError("bridge could not bind " + prefix + ": "
                              + ex.GetType().Name + ": " + ex.Message);
                _listener = null;
                return false;
            }

            _thread = new Thread(Serve) { IsBackground = true, Name = "RedMoonBridge" };
            _thread.Start();
            _log.LogInfo("bridge listening on " + prefix);
            return true;
        }

        internal void Stop()
        {
            _stopping = true;

            // Release anyone blocked on a dump the tick will now never run.
            DumpRequest pending = _pending;
            if (pending != null)
            {
                _pending = null;
                pending.Done.Set();
            }

            try
            {
                if (_listener != null)
                {
                    _listener.Stop();
                    _listener.Close();
                    _listener = null;
                    _log.LogInfo("bridge listener stopped and closed");
                }
            }
            catch (Exception ex)
            {
                _log.LogWarning("bridge listener close failed: "
                                + ex.GetType().Name + ": " + ex.Message);
            }
        }

        // -------------------------------------------------------------------
        // main thread - the ONLY place ECS is touched
        // -------------------------------------------------------------------
        internal void MainThreadTick()
        {
            try
            {
                // One world lookup feeds both: StateReader takes the readiness
                // the dumper already computed rather than evaluating the gate a
                // second time, so /health and /state can never disagree about
                // whether the world is ready.
                WorldStatus status = PrefabDumper.Status();
                _snapshot = new BridgeSnapshot(status, StateReader.Capture(status));
            }
            catch (Exception ex)
            {
                _log.LogWarning("world snapshot failed: " + ex.GetType().Name + ": " + ex.Message);
            }

            // The recorder samples HERE: after the snapshot is published, before
            // the pending dump is serviced. One sample per tick, so 4 Hz, which
            // is a ceiling set by SampleEveryFrames = 15 in Plugin.cs and not a
            // knob - the falsification spec's tolerances were computed against
            // it. It runs before the dump so a caller arming a recording cannot
            // have its own arm tick counted as a sample.
            try
            {
                HealthRecorder.Sample(_log);
            }
            catch (Exception ex)
            {
                _log.LogWarning("health recorder sample failed: "
                                + ex.GetType().Name + ": " + ex.Message);
            }

            DumpRequest request = _pending;
            if (request == null)
            {
                return;
            }

            try
            {
                if (request.RecordKind != null)
                {
                    request.Body = HealthRecorder.Handle(_log, request, _build, _plugin, _host);
                }
                else if (request.StatValues)
                {
                    request.Body = ComponentDumper.StatControl(_build, _plugin, request.Guid);
                }
                else
                {
                    request.Body = request.Components
                        ? ComponentDumper.Dump(_build, _plugin, request.Guid, request.NamePrefix,
                                               request.Limit, request.Instanced)
                        : PrefabDumper.Dump(_build, _plugin, request.Table);
                }
            }
            catch (Exception ex)
            {
                request.Body = null;
                _log.LogError("prefab dump failed: " + ex.GetType().Name + ": " + ex.Message);
            }
            finally
            {
                _pending = null;
                request.Done.Set();
            }
        }

        // -------------------------------------------------------------------
        // listener thread
        // -------------------------------------------------------------------
        private void Serve()
        {
            while (!_stopping)
            {
                HttpListenerContext context;
                try
                {
                    context = _listener.GetContext();
                }
                catch (Exception)
                {
                    return; // Stop() disposed the listener out from under us.
                }

                try
                {
                    Route(context);
                }
                catch (Exception ex)
                {
                    _log.LogError("request handling failed: "
                                  + ex.GetType().Name + ": " + ex.Message);
                    TryRespond(context, 500, Error("internal", "the bridge hit an "
                                                   + "internal problem, see the plugin log"));
                }
            }
        }

        private void Route(HttpListenerContext context)
        {
            string path = context.Request.Url.AbsolutePath;

            if (path == "/health")
            {
                TryRespond(context, 200, Health());
                return;
            }

            if (path == "/state")
            {
                TryRespond(context, 200, State());
                return;
            }

            if (path == "/dump/prefabs")
            {
                string table = context.Request.QueryString["table"];
                if (!string.IsNullOrEmpty(table) && !PrefabDumper.IsWritable(table))
                {
                    TryRespond(context, 404, Error("not_found", "that table is not "
                                                   + "mapped against this game build yet"));
                    return;
                }

                int status;
                string body = RequestDump(new DumpRequest(table), out status);
                TryRespond(context, status, body);
                return;
            }

            // EXPLORATORY, cycle 3 phase 1. No schema, no ingest gate, never
            // promoted, and deliberately absent from /dump/prefabs so nothing
            // downstream can start depending on its shape. It DOES wait on the
            // same GameDataInitialized readiness gate, which is a precondition
            // for reading anything at all rather than a validation of what was
            // read.
            if (path == "/dump/components")
            {
                int guid = QueryInt(context, "guid", 0);
                string namePrefix = context.Request.QueryString["name"];
                int limit = QueryInt(context, "limit", ComponentDumper.DefaultLimit);
                bool instanced = QueryInt(context, "instanced", 0) != 0;

                if (guid == 0 && string.IsNullOrEmpty(namePrefix))
                {
                    TryRespond(context, 400, Error("bad_request", "pass guid, or name as a "
                                                   + "prefix, so the scan has a subject"));
                    return;
                }

                int status;
                string body = RequestDump(
                    new DumpRequest(guid, namePrefix, limit, instanced), out status);
                TryRespond(context, status, body);
                return;
            }

            // EXPLORATORY, cycle 3 phase 3: the prefab-versus-instance VALUE
            // control. Emits EVERY entity carrying the guid, prefab and instance
            // alike, with one fixed list of typed reads, so the two can be
            // compared field by field rather than by presence.
            if (path == "/dump/statcontrol")
            {
                int guid = QueryInt(context, "guid", 0);
                if (guid == 0)
                {
                    TryRespond(context, 400, Error("bad_request",
                                                   "pass guid so the control has a subject"));
                    return;
                }

                int status;
                string body = RequestDump(new DumpRequest(guid, true), out status);
                TryRespond(context, status, body);
                return;
            }

            // The BOSS HEALTH RECORDER, falsification spec A.4. Routed on the
            // PATH ONLY and answering both GET and POST: the spec writes POST,
            // a curl probe is a GET, and a method mismatch that reads as "no
            // such endpoint" is the least debuggable failure this surface could
            // offer.
            if (path == "/record/start")
            {
                int guid = QueryInt(context, "guid", 0);
                if (guid == 0)
                {
                    TryRespond(context, 400, Error("bad_request", "pass a nonzero guid so "
                                                   + "the recorder has a subject"));
                    return;
                }

                string note = context.Request.QueryString["note"];
                int status;
                string body = RequestDump(
                    new DumpRequest(HealthRecorder.KindStart, guid, note), out status);
                TryRespond(context, status, body);
                return;
            }

            // Served straight off published scalars. It never scans and never
            // waits on the tick, so it stays answerable even while a fight is
            // running the main thread hard.
            if (path == "/record/status")
            {
                TryRespond(context, 200, HealthRecorder.Status());
                return;
            }

            if (path == "/record/stop")
            {
                int status;
                string body = RequestDump(
                    new DumpRequest(HealthRecorder.KindStop, 0, null), out status);
                TryRespond(context, status, body);
                return;
            }

            TryRespond(context, 404, Error("not_found", "no such endpoint"));
        }

        /// <summary>
        /// A query parameter as an int, falling back rather than throwing. A
        /// malformed value takes the default, which keeps a typo in a probe URL
        /// from reaching the main thread as an exception.
        /// </summary>
        private static int QueryInt(HttpListenerContext context, string key, int fallback)
        {
            string raw = context.Request.QueryString[key];
            int value;
            if (string.IsNullOrEmpty(raw)
                || !int.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture,
                                 out value))
            {
                return fallback;
            }

            return value;
        }

        /// <summary>Hand the dump to the main thread and wait for it (D7).</summary>
        private string RequestDump(DumpRequest request, out int status)
        {
            // One dump at a time. The tick services a single pending request, so
            // concurrent callers queue here rather than overwriting each other.
            lock (_dumpGate)
            {
                _pending = request;
                if (!request.Done.Wait(DumpTimeoutMs))
                {
                    _pending = null;
                    _log.LogWarning("prefab dump timed out after "
                                    + DumpTimeoutMs + " ms - is the game ticking?");
                    status = 504;
                    return Error("dump_timeout", "the game did not produce a dump in time");
                }
            }

            if (request.Body == null)
            {
                status = 503;
                return Error(PrefabDumper.ErrorWorldNotReady, PrefabDumper.NotReadyMessage);
            }

            // A request that set its own status keeps it; everything else is a
            // 200, which is exactly what every pre-recorder caller already got.
            status = request.Status == 0 ? 200 : request.Status;
            return request.Body;
        }

        // -------------------------------------------------------------------
        // bodies
        // -------------------------------------------------------------------
        /// <summary>
        /// The one error-body shape. Internal rather than private so
        /// HealthRecorder builds its refusals through the same helper instead of
        /// growing a second spelling of the envelope.
        /// </summary>
        internal static string Error(string code, string message)
        {
            return "{\"ok\":false,\"error\":" + Json.Str(code)
                   + ",\"message\":" + Json.Str(message) + "}";
        }

        private string Health()
        {
            BridgeSnapshot snapshot = _snapshot;
            var sb = new StringBuilder(384);
            sb.Append("{\"ok\":true");
            sb.Append(",\"build\":").Append(Json.Str(_build));
            sb.Append(",\"plugin\":").Append(Json.Str(_plugin));
            sb.Append(",\"host\":").Append(Json.Str(_host));
            sb.Append(",\"port\":").Append(_port);
            sb.Append(",\"game_root\":").Append(Json.Str(_gameRoot));
            sb.Append(",\"bound\":").Append(Json.Str(Bound));
            sb.Append(",\"world\":")
              .Append(Json.Str(snapshot == null ? "" : snapshot.WorldName));
            sb.Append(",\"worlds\":[");
            if (snapshot != null && snapshot.WorldNames != null)
            {
                for (int i = 0; i < snapshot.WorldNames.Length; i++)
                {
                    if (i > 0)
                    {
                        sb.Append(',');
                    }

                    sb.Append(Json.Str(snapshot.WorldNames[i]));
                }
            }

            sb.Append(']');
            sb.Append(",\"ready\":").Append(snapshot != null && snapshot.Ready ? "true" : "false");
            sb.Append(",\"prefab_count\":").Append(snapshot == null ? -1 : snapshot.PrefabCount);
            sb.Append(",\"snapshot_age_s\":").Append(Json.Num(SnapshotAge(snapshot)));
            sb.Append(",\"uptime_s\":")
              .Append(Json.Num((DateTime.UtcNow - _startedAt).TotalSeconds));
            return sb.Append('}').ToString();
        }

        /// <summary>
        /// The D6 envelope. The null belongs to the `state` MEMBER, never to the
        /// body: a bare null carries no build stamp and cannot be told apart from
        /// a broken bridge.
        ///
        /// The member is whatever the LAST MAIN-THREAD TICK published (D7). This
        /// method does not touch ECS - it appends a string StateReader already
        /// built - and it still emits a null member honestly whenever the tick
        /// had nothing to report. `state_reason` is an additive field carrying
        /// WHY, as a fixed code, so a null member can be debugged without
        /// reading the plugin log.
        /// </summary>
        private string State()
        {
            BridgeSnapshot snapshot = _snapshot;
            string member = snapshot == null ? null : snapshot.StateJson;
            var sb = new StringBuilder(384);
            sb.Append("{\"ok\":true");
            sb.Append(",\"build\":").Append(Json.Str(_build));
            sb.Append(",\"plugin\":").Append(Json.Str(_plugin));
            sb.Append(",\"captured_at\":").Append(Json.Str(Json.UtcNow()));
            sb.Append(",\"snapshot_age_s\":").Append(Json.Num(SnapshotAge(snapshot)));
            sb.Append(",\"state_reason\":")
              .Append(Json.Str(snapshot == null ? StateReader.ReasonNoWorld
                                                : snapshot.StateReason));
            sb.Append(",\"state\":").Append(member == null ? "null" : member);
            return sb.Append('}').ToString();
        }

        private static double SnapshotAge(BridgeSnapshot snapshot)
        {
            return snapshot == null ? -1.0 : (DateTime.UtcNow - snapshot.CapturedAt).TotalSeconds;
        }

        private void TryRespond(HttpListenerContext context, int status, string body)
        {
            try
            {
                byte[] bytes = Encoding.ASCII.GetBytes(body);
                context.Response.StatusCode = status;
                context.Response.ContentType = "application/json";
                context.Response.ContentLength64 = bytes.Length;
                context.Response.OutputStream.Write(bytes, 0, bytes.Length);
                context.Response.OutputStream.Close();
            }
            catch (Exception ex)
            {
                _log.LogWarning("response write failed: "
                                + ex.GetType().Name + ": " + ex.Message);
            }
        }
    }
}

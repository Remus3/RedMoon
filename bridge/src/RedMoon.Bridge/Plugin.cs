// BepInEx entry point for RedMoon.Bridge.
//
// One assembly loads into both V Rising hosts (ADR-004) and the port it binds is
// a pure function of the host it detects (ADR-005), so nothing here races and no
// start order has to be remembered.
//
// The banner below is a HARD CONTRACT, not a log line. tools/bridge_probe.py
// --loader-log is the only proof that the loader actually loaded this assembly,
// and it matches on three independent tokens - version, host and port - because
// a matcher that accepted any line containing the plugin name survived mutation
// testing in cycle 1 while the thing it was watching was broken for a whole
// cycle. tests/test_bridge_project.py renders BannerFormat through that exact
// matcher, so the two cannot drift apart.
using System;
using System.Globalization;
using System.IO;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Unity.IL2CPP;
using Il2CppInterop.Runtime.Injection;
using RedMoon.Bridge.Generated;
using UnityEngine;

namespace RedMoon.Bridge
{
    /// <summary>
    /// The main-thread hook (spike S2, MEASURED reached in both hosts about 2.5 s
    /// after Load). Every ECS read in this plugin happens under this Update, and
    /// the listener thread only ever sees what it published (decision D7).
    /// </summary>
    public sealed class BridgeTick : MonoBehaviour
    {
        // Il2Cpp injection fails without this constructor.
        public BridgeTick(IntPtr ptr) : base(ptr) { }

        /// <summary>
        /// Frames between world samples. Every frame would re-allocate the world
        /// name array sixty times a second for a value that changes on the order
        /// of minutes; a quarter second keeps snapshot_age_s small anyway.
        /// </summary>
        private const int SampleEveryFrames = 15;

        private int _frames;

        private void Update()
        {
            BridgeServer server = BridgePlugin.Server;
            if (server == null)
            {
                return;
            }

            _frames++;
            if (_frames % SampleEveryFrames != 0)
            {
                return;
            }

            server.MainThreadTick();
        }
    }

    [BepInPlugin(PluginGuid, PluginName, PluginVersion)]
    public sealed class BridgePlugin : BasePlugin
    {
        internal const string PluginGuid = "redmoon.bridge";
        internal const string PluginName = "RedMoon.Bridge";

        // The ONLY place the plugin version is spelled. The banner and /health
        // read it back off the attribute at runtime rather than repeating it.
        private const string PluginVersion = "0.1.0";

        internal const string BannerFormat = "RedMoon.Bridge v{0} host={1} port={2}";

        /// <summary>Mirrors tools/rmdata_extract.parse_build_id.</summary>
        private static readonly Regex BuildPattern =
            new Regex(@"v(?<build>\d+\.\d+\.\d+\.\d+-r\d+)", RegexOptions.CultureInvariant);

        internal const string UnknownBuild = "unknown";

        /// <summary>
        /// The running server, for the injected tick. Unity constructs a
        /// MonoBehaviour itself, so it cannot be handed a reference any other way.
        /// </summary>
        internal static BridgeServer Server;

        public override void Load()
        {
            string host = HostDetect.Detect();
            int port = RmPorts.ForHost(host);
            string version = Version();
            string gameRoot = Paths.GameRootPath;
            string build = ReadBuild(gameRoot);

            Log.LogInfo(string.Format(CultureInfo.InvariantCulture,
                                      BannerFormat, version, host, port));
            Log.LogInfo("game_root=" + gameRoot + " build=" + build);

            var server = new BridgeServer(Log, host, port, build, version, gameRoot);
            if (!server.Start())
            {
                // Stand down rather than take the operator's game with us.
                Log.LogWarning("bridge stood down: nothing is listening, but the game is fine");
                return;
            }

            Server = server;

            try
            {
                ClassInjector.RegisterTypeInIl2Cpp<BridgeTick>();
                var carrier = new GameObject(PluginName);
                carrier.hideFlags = HideFlags.HideAndDontSave;
                UnityEngine.Object.DontDestroyOnLoad(carrier);
                carrier.AddComponent<BridgeTick>();
            }
            catch (Exception ex)
            {
                // Without the tick nothing reads ECS, so /health reports an
                // unready world forever. Loud, and still not fatal to the game.
                Log.LogError("main-thread tick injection failed, no ECS will be read: "
                             + ex.GetType().Name + ": " + ex.Message);
            }
        }

        /// <summary>
        /// The graceful shutdown path. `taskkill /F` skips it by definition, and
        /// spike R11 already retired the hard-kill case: after a forced kill the
        /// port held no LISTEN and bridge_probe --expect-unreachable PASSED.
        ///
        /// MEASURED 2026-07-26 and the reason for the marker file below: after a
        /// NORMAL in-game quit the client's BepInEx LogOutput.log contained no
        /// shutdown line of any kind - not from this plugin, which logged
        /// nothing here, and not from BepInEx itself. A Log.LogInfo alone cannot
        /// settle the question, because the logging pipeline may already be torn
        /// down when Unload runs, and a missing line would then be unreadable in
        /// exactly the same way the fabricated items.tier zero was.
        ///
        /// So the observation is a FILE, written outside BepInEx's logging: if
        /// redmoon-unload.log gains a line, Unload ran. If it does not, Unload
        /// did not run, or could not write. The two are then distinguishable by
        /// whether the log line appears as well.
        /// </summary>
        public override bool Unload()
        {
            BridgeServer server = Server;
            Server = null;
            if (server != null)
            {
                server.Stop();
            }

            try
            {
                Log.LogInfo("Unload: listener stopped, port released");
            }
            catch (Exception)
            {
                // The logging pipeline may already be gone. The marker below is
                // the observation that does not depend on it.
            }

            MarkUnloaded(server != null);
            return true;
        }

        /// <summary>
        /// Append one line to BepInEx\redmoon-unload.log. Appended rather than
        /// replaced so consecutive sessions accumulate instead of the last one
        /// erasing the evidence of the one before it.
        /// </summary>
        private static void MarkUnloaded(bool hadServer)
        {
            try
            {
                string path = Path.Combine(Paths.BepInExRootPath, "redmoon-unload.log");
                string line = string.Format(CultureInfo.InvariantCulture,
                                            "{0} host={1} listener_stopped={2}{3}",
                                            DateTime.UtcNow.ToString("o", CultureInfo.InvariantCulture),
                                            HostDetect.Detect(), hadServer, Environment.NewLine);
                File.AppendAllText(path, line);
            }
            catch (Exception)
            {
                // A plugin that throws on the way out is worse than one that
                // cannot record that it left.
            }
        }

        /// <summary>The version off this plugin's own BepInPlugin attribute.</summary>
        private string Version()
        {
            try
            {
                BepInPlugin metadata = MetadataHelper.GetMetadata(this);
                if (metadata != null && metadata.Version != null)
                {
                    return metadata.Version.ToString();
                }
            }
            catch (Exception ex)
            {
                Log.LogWarning("could not read plugin metadata: "
                               + ex.GetType().Name + ": " + ex.Message);
            }

            return PluginVersion;
        }

        /// <summary>
        /// The game build, read at RUNTIME from the answering host's own VERSION
        /// file. Both hosts carry one under their own GameRootPath and both parse
        /// to the same build id, which is what makes the wiredness probe's
        /// identity leg meaningful: a hardcoded constant could not pass it.
        /// </summary>
        private string ReadBuild(string gameRoot)
        {
            try
            {
                string path = Path.Combine(gameRoot, "VERSION");
                if (!File.Exists(path))
                {
                    Log.LogWarning("no VERSION file at " + path);
                    return UnknownBuild;
                }

                Match match = BuildPattern.Match(File.ReadAllText(path));
                if (!match.Success)
                {
                    Log.LogWarning("unparseable VERSION file at " + path);
                    return UnknownBuild;
                }

                return match.Groups["build"].Value;
            }
            catch (Exception ex)
            {
                Log.LogWarning("could not read the game build: "
                               + ex.GetType().Name + ": " + ex.Message);
                return UnknownBuild;
            }
        }
    }
}

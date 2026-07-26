// Which V Rising host is this assembly loaded into (spec decision D1).
//
// MEASURED 2026-07-26 in both hosts (docs/BRIDGE_SPIKES.md, S1(d)):
//
//   host    Paths.ProcessName    Paths.GameRootPath
//   client  VRising              ...\common\VRising
//   server  VRisingServer        ...\common\VRising\VRising_Server
//
// One assembly loads into both (ADR-004) and the port is a pure function of the
// answer (ADR-005), so this is the only thing standing between the two hosts and
// a contended port. It is deliberately a one-liner over a value BepInEx has
// already resolved rather than a process-tree or path heuristic.
using System;
using BepInEx;

namespace RedMoon.Bridge
{
    internal static class HostDetect
    {
        internal const string Client = "client";
        internal const string Server = "server";

        /// <summary>The detected host name, matching core.ports.BRIDGE_HOSTS.</summary>
        internal static string Detect()
        {
            string process = Paths.ProcessName ?? "";
            return process.IndexOf("Server", StringComparison.OrdinalIgnoreCase) >= 0
                ? Server
                : Client;
        }
    }
}

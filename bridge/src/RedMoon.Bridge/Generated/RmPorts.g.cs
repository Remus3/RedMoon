// GENERATED FILE - do not edit by hand.
// Producer: tools/gen_bridge_ports.py
// Source of truth: core/ports.py (ADR-003, amended by ADR-005).
//
// Regenerate with:
//     python tools/gen_bridge_ports.py
//
// tests/test_bridge_ports.py asserts this file is byte-identical to a fresh
// render, so editing core/ports.py without regenerating fails the suite, and so
// does hand-editing this file.

namespace RedMoon.Bridge.Generated
{
    internal static class RmPorts
    {
        /// <summary>Bridge port bound inside the V Rising CLIENT process.</summary>
        internal const int Bridge = 8777;

        /// <summary>Bridge port bound inside the DEDICATED SERVER process.</summary>
        internal const int BridgeServer = 8780;

        /// <summary>
        /// Port for a detected host. Total over the known hosts and throws
        /// otherwise, mirroring core.ports.bridge_port_for_host. An unknown
        /// host must fail loudly rather than default onto the client's port.
        /// </summary>
        internal static int ForHost(string host)
        {
            return host switch
            {
            "client" => 8777,
            "server" => 8780,
                _ => throw new System.ArgumentOutOfRangeException(
                    nameof(host), host, "unknown bridge host"),
            };
        }
    }
}

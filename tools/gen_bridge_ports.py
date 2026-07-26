#!/usr/bin/env python3
"""Generate the C# port constants from core/ports.py.

The bridge plugin is C# and cannot import the Python port registry, but
CLAUDE.md forbids writing a port literal anywhere outside that registry and
tests/test_ports.py enforces it over .cs files. The resolution (spec D2) is one
machine-written file, allowlisted by path, regenerated from the single source of
truth and guarded against drift by tests/test_bridge_ports.py.

The host-to-port mapping of ADR-005 is carried across rather than restated: the
generated ForHost matches core.ports.bridge_port_for_host, including the throw
on an unrecognised host, so the two sides cannot disagree about what happens
when host detection returns something unexpected.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Run as a script, sys.path[0] is tools/, not the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import ports  # noqa: E402

OUTPUT_REL = "bridge/src/RedMoon.Bridge/Generated/RmPorts.g.cs"
"""Repo-relative path of the generated file.

This exact string is in OWN_PORT_ALLOWLIST in tests/test_ports.py. Changing it
here without changing it there re-arms the port-literal guard against the
generator's own output, which is the correct failure.
"""

PRODUCER = "tools/gen_bridge_ports.py"


def _host_case_arms() -> str:
    arms = []
    for host in ports.BRIDGE_HOSTS:
        arms.append(f'            "{host}" => {ports.bridge_port_for_host(host)},')
    return "\n".join(arms)


def render() -> str:
    """Return the full text of the generated file. Pure and deterministic."""
    return f"""// GENERATED FILE - do not edit by hand.
// Producer: {PRODUCER}
// Source of truth: core/ports.py (ADR-003, amended by ADR-005).
//
// Regenerate with:
//     python {PRODUCER}
//
// tests/test_bridge_ports.py asserts this file is byte-identical to a fresh
// render, so editing core/ports.py without regenerating fails the suite, and so
// does hand-editing this file.

namespace RedMoon.Bridge.Generated
{{
    internal static class RmPorts
    {{
        /// <summary>Bridge port bound inside the V Rising CLIENT process.</summary>
        internal const int Bridge = {ports.BRIDGE};

        /// <summary>Bridge port bound inside the DEDICATED SERVER process.</summary>
        internal const int BridgeServer = {ports.BRIDGE_SERVER};

        /// <summary>
        /// Port for a detected host. Total over the known hosts and throws
        /// otherwise, mirroring core.ports.bridge_port_for_host. An unknown
        /// host must fail loudly rather than default onto the client's port.
        /// </summary>
        internal static int ForHost(string host)
        {{
            return host switch
            {{
{_host_case_arms()}
                _ => throw new System.ArgumentOutOfRangeException(
                    nameof(host), host, "unknown bridge host"),
            }};
        }}
    }}
}}
"""


def write(repo_root: Path) -> Path:
    """Write the generated file. Returns the path written."""
    path = repo_root / OUTPUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render()
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="ascii", newline="\n")
    tmp.replace(path)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if the file on disk differs from a fresh render",
    )
    args = parser.parse_args()

    path = args.repo / OUTPUT_REL
    if args.check:
        if not path.is_file():
            print(f"missing: {path}", file=sys.stderr)
            return 1
        if path.read_text(encoding="utf-8") != render():
            print(f"stale: {path} differs from core/ports.py", file=sys.stderr)
            return 1
        print(f"up to date: {OUTPUT_REL}")
        return 0

    written = write(args.repo)
    print(f"wrote {written}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

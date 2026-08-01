"""Red Moon port registry (ADR-003).

Deliberately disjoint from the other project running concurrently on this
machine. Import these constants; never write a port literal anywhere else - a
guard test greps the source for foreign port numbers, so naming them here (even
in a comment) would trip it. The full rationale lives in ADR-003.
"""
from __future__ import annotations

CONTROL = 8770
"""Headless control plane, on the floor of Red Moon's reserved block.

Infrastructure rather than a game service, and deliberately placed below the
game ports so the block reads as two regions: 8770-8776 for infrastructure,
8777 and up for services that talk to V Rising. Operator decision 2026-08-01,
adopting a structural split proposed by a sibling project on this machine.

Red Moon reserves 8770-8789. The floor was free the whole time - 8777 is the
lowest USED port, not the bottom of the block - and this constant is the first
allocation to sit below the bridge.

Nothing binds this yet. The headless orchestrator it serves is unbuilt, and a
reserved-but-unbound port must never be read off a live port scan as free.
"""

BRIDGE = 8777
"""RedMoon.Bridge in the V Rising CLIENT process, local live game JSON (cycle 2).

The client keeps the original bridge port because the solo client is the
dominant topology and tools/rm_facts.py already probes this number.
"""

BRIDGE_SERVER = 8780
"""RedMoon.Bridge in the DEDICATED SERVER process (ADR-005).

One plugin assembly loads in both hosts (ADR-004), and both hosts can run at
once on this machine. Rather than race for a single port and have the loser
stand down, each host binds the port its own detected host type selects. See
bridge_port_for_host.
"""

DASHBOARD = 8778
"""Dashboard, HTTPS (cycle 4)."""

VISION = 8779
"""Vision server (cycle 8, if it earns its place)."""

ENGINE = 8783
"""Bloodforge combat math server (cycle 3)."""

ALL = frozenset({CONTROL, BRIDGE, BRIDGE_SERVER, DASHBOARD, VISION, ENGINE})

BRIDGE_HOSTS = ("client", "server")
"""The two V Rising hosts the bridge assembly can load into (ADR-004)."""

_BRIDGE_PORT_BY_HOST = {"client": BRIDGE, "server": BRIDGE_SERVER}


def bridge_port_for_host(host: str) -> int:
    """Return the bridge port a host binds. Total over BRIDGE_HOSTS, else raises.

    This is the whole of the ADR-005 arbitration rule: the port is a pure
    function of the detected host, so two hosts running at once never contend
    and no start order has to be remembered.
    """
    try:
        return _BRIDGE_PORT_BY_HOST[host]
    except KeyError:
        raise ValueError(
            f"unknown bridge host {host!r}, expected one of {BRIDGE_HOSTS}"
        ) from None

GAME_HOST_ENV = "RM_GAME_HOST"
"""Environment variable naming the host every live reader talks to.

Defaults to 127.0.0.1. The game host is config, not code, so moving the game or
a dedicated server to another box never requires a code change.
"""

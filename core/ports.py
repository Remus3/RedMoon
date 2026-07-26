"""Red Moon port registry (ADR-003).

Deliberately disjoint from the other project running concurrently on this
machine. Import these constants; never write a port literal anywhere else - a
guard test greps the source for foreign port numbers, so naming them here (even
in a comment) would trip it. The full rationale lives in ADR-003.
"""
from __future__ import annotations

BRIDGE = 8777
"""RedMoon.Bridge BepInEx plugin, local live game JSON (cycle 2)."""

DASHBOARD = 8778
"""Dashboard, HTTPS (cycle 4)."""

VISION = 8779
"""Vision server (cycle 8, if it earns its place)."""

ENGINE = 8783
"""Bloodforge combat math server (cycle 3)."""

ALL = frozenset({BRIDGE, DASHBOARD, VISION, ENGINE})

GAME_HOST_ENV = "RM_GAME_HOST"
"""Environment variable naming the host every live reader talks to.

Defaults to 127.0.0.1. The game host is config, not code, so moving the game or
a dedicated server to another box never requires a code change.
"""

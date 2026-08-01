#!/usr/bin/env python3
"""List the units SPAWNED in the world, so an anchor run has a subject.

`docs/ANCHOR_RUNS.md` said "find the target's prefab guid" without saying how,
which is a hole in a procedure whose whole point is that it can be followed at
11pm. This is how.

`/dump/components` takes a `name` PREFIX and an `instanced` flag
(`bridge/src/RedMoon.Bridge/BridgeServer.cs:445-463`). `instanced=1` returns
only entities spawned in the world rather than the prefabs they came from, which
is the distinction that matters most here: a spawned unit carries the SAME
PrefabGUID as its prefab, the prefab reads `Health.Value` 0, and a recorder
latched onto the prefab produces a flat series that looks exactly like a
recorder reading nothing.

TWO THINGS THIS TOOL WILL NOT DO. It does not pick the target - the run needs a
unit that SURVIVES the hit, and nothing readable here says how much health a
unit will have. And it does not filter V Bloods out, it MARKS them, because a
tool that silently drops rows teaches the operator that the list is complete.

The endpoint enumerates every component of every match, about 60 KB per entity,
so the default limit is deliberately small.
"""
from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path

# Launched by absolute path, so sys.path[0] is tools/, not the repo root. Same
# idiom tools/anchor_record.py and tools/bridge_probe.py already use.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.bridge_client import BridgeUnreachable, get_json  # noqa: E402
from core.ports import BRIDGE_HOSTS  # noqa: E402

DUMP_PATH = "/dump/components"

DEFAULT_PREFIX = "CHAR_"
"""Every unit prefab on this build is named CHAR_<something>."""

DEFAULT_LIMIT = 24

VBLOOD_TOKEN = "VBlood"
"""How a V Blood boss is spelled in its prefab name, on all 65 rows."""

HEADER = f"{'entity':<10} {'prefab_guid':<14} {'marker':<7} prefab_name"


def format_rows(entities: Iterable[Mapping]) -> list[str]:
    """One line per spawned entity, V Bloods MARKED rather than dropped.

    `carries_prefab_marker` is carried through untouched. It must be false on
    the subject: true means the entity is the PREFAB, and the recorder refuses
    to arm against it (`HealthRecorder.cs`) for the reason in the module
    docstring.
    """
    lines = [HEADER]
    for entity in entities:
        name = str(entity.get("prefab_name", ""))
        note = ""
        if VBLOOD_TOKEN in name:
            note = "   <-- V BLOOD, not a run-1 target"
        elif entity.get("carries_prefab_marker"):
            note = "   <-- PREFAB, not spawned, the recorder will refuse it"
        lines.append(
            f"{entity.get('entity_index')!s:<10} "
            f"{entity.get('prefab_guid')!s:<14} "
            f"{entity.get('carries_prefab_marker')!s:<7} "
            f"{name}{note}"
        )
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List spawned units, so an anchor run has a subject."
    )
    parser.add_argument(
        "--host",
        choices=BRIDGE_HOSTS,
        default=BRIDGE_HOSTS[0],
        help="which V Rising host the bridge is loaded into (default: %(default)s)",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_PREFIX,
        help="prefab NAME PREFIX to scan for (default: %(default)s)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="how many matches to return; the payload is about 60 KB each "
        "(default: %(default)s)",
    )
    args = parser.parse_args(argv)

    query = {"name": args.name, "instanced": "1", "limit": str(args.limit)}
    try:
        payload = get_json(args.host, DUMP_PATH, query)
    except BridgeUnreachable as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    if payload.get("ok") is False:
        print(
            f"refused: the bridge returned {payload.get('error', 'an error')} "
            f"({payload.get('message', 'no message')})",
            file=sys.stderr,
        )
        return 2

    entities = payload.get("entities") or []
    print(f"host {args.host}  name {args.name!r}  spawned matches {len(entities)}")
    for line in format_rows(entities):
        print(line)
    if not entities:
        print(
            "\nNothing spawned matches that prefix. That is not the same as the "
            "unit not existing - poll for the SUBJECT, never for ready:true.",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

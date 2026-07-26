#!/usr/bin/env python3
"""PreToolUse text-first backstop (CLAUDE.md R1 to R3).

Denies the pure screen-text and clipboard readers, which always have a text
alternative: file content goes through Read and Grep, runtime state through the
dashboard API or ops/runtime/health.json.

Scope is deliberately narrow so a sanctioned visual ritual is never wedged.
Pixel screenshots, live game capture, DOM checks, clicks and typing are all
allowed. The escape hatch ops/runtime/allow_visual.flag allows everything.

The guard never raises. A crashing guard must not block tools.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import ports  # noqa: E402

DENY = frozenset(
    {
        "mcp__Windows-MCP__Scrape",
        "mcp__computer-use__read_clipboard",
    }
)

FLAG = Path(__file__).resolve().parents[1] / "ops" / "runtime" / "allow_visual.flag"

REASON = (
    "Text-first (CLAUDE.md R1-R2): do not read text or state off the screen. "
    "File content -> Read or Grep. Runtime state -> "
    f"curl -k https://127.0.0.1:{ports.DASHBOARD}/api/state or Read "
    "ops/runtime/health.json. Override only when no text path exists: create "
    "ops/runtime/allow_visual.flag."
)


def decide(payload: dict) -> dict | None:
    """Return the PreToolUse deny document, or None to allow."""
    if payload.get("tool_name", "") not in DENY:
        return None
    if FLAG.exists():
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    }


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        if not isinstance(payload, dict):
            # A syntactically valid but non-object top-level JSON value (null,
            # a number, a list, a bare string) must not reach decide() as-is -
            # treat it as an empty payload rather than relying on the except
            # below to catch the AttributeError from payload.get(...).
            payload = {}
        decision = decide(payload)
        if decision is not None:
            sys.stdout.write(json.dumps(decision))
    except (ValueError, TypeError, OSError, AttributeError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

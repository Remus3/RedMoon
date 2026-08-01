#!/usr/bin/env python3
"""SessionStart facts probe.

Prints live Red Moon state so a session bootstraps from ground truth rather than
from a stale document: game install and build, extracted data build, port
occupancy, and RM-* scheduled tasks.

Never raises. A failing probe must not break session start.
"""
from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import ports  # noqa: E402
from tools.rmdata_extract import DEFAULT_INSTALL, parse_build_id  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
"""Suppress the console a spawned CONSOLE exe would otherwise allocate.

This hook is launched with `pythonw.exe`, which has no console. That makes the
hook itself windowless and does NOT make its children windowless: on Windows a
console-subsystem executable started from a process with no console gets a BRAND
NEW one, which the operator sees as a window flashing open and shut. `schtasks`
below is such an executable.

`getattr` with a 0 default because CREATE_NO_WINDOW does not exist off Windows
and 0 is a valid `creationflags`, so this stays importable everywhere.

MEASURED before adopting: the flag does NOT affect `capture_output`. The same
`schtasks` and `git` calls return the same returncode and the same captured
output with and without it under a `pythonw.exe` parent. (Not byte-identical for
`schtasks` - its output carries a volatile Next Run Time - so the claim is that
capture WORKS, not that the bytes match.) That mattered because a flag which
detached the child instead of only hiding its window would leave every gate here
reading nothing while still exiting 0 - a gate that looks exactly like a working
one. Pinned by `tests/test_hook_consoles.py`."""

PORT_LABELS = {
    ports.BRIDGE: "bridge",
    ports.DASHBOARD: "dashboard",
    ports.VISION: "vision",
    ports.ENGINE: "engine",
}


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


NOT_INSTALLED = "not installed"
UNPARSEABLE = "unparseable"
NONE_EXTRACTED = "none extracted"

BUILD_SENTINELS = frozenset({NOT_INSTALLED, UNPARSEABLE, NONE_EXTRACTED})
"""What the two build accessors return INSTEAD of raising.

This probe never raises, so every failure has to come back as a value. That
makes the sentinels load-bearing rather than cosmetic: two of them compared to
each other are EQUAL, and a naive agreement check would report a machine with no
game installed as a perfect match. build_agreement excludes them first.

Named rather than repeated as literals at each return, so a rename cannot leave
the set behind. tests/test_build_pin_crosscheck.py imports this set rather than
restating it, for the same reason."""


def game_build() -> str:
    version = DEFAULT_INSTALL / "VERSION"
    if not version.is_file():
        return NOT_INSTALLED
    try:
        return parse_build_id(version.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return UNPARSEABLE


def data_build() -> str:
    pointer = REPO / "data" / "rmdata" / "current.txt"
    if not pointer.is_file():
        return NONE_EXTRACTED
    return pointer.read_text(encoding="utf-8").strip()


def build_agreement(installed: str, extracted: str) -> str:
    """Say whether the two build lines above agree, in one line.

    Added 2026-08-01 with explicit operator approval (this file is FROZEN).
    Both numbers have been printed at every session start since cycle 1 and
    nothing ever compared them, so a session could bootstrap from combat data
    extracted from a build the machine is no longer running and the banner would
    look entirely normal - two correct lines, side by side, disagreeing.

    A sentinel on either side is an UNAVAILABLE SOURCE and not a disagreement.
    Reporting a mismatch on a machine with no game installed would be a false
    alarm at every session start, which is the fastest way to teach an operator
    to stop reading the line.
    """
    unavailable = [
        f"{label} build is {value!r}"
        for label, value in (("game", installed), ("extracted data", extracted))
        if value in BUILD_SENTINELS
    ]
    if unavailable:
        return "NOT CHECKED - " + ", ".join(unavailable)
    if installed == extracted:
        return "MATCH"
    return (
        f"MISMATCH - the game on disk is {installed} but data/rmdata/ was "
        f"extracted from {extracted}. Re-run tools/rmdata_extract.py."
    )


def scheduled_tasks() -> list[str]:
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=5,  # comfortably under the 10s SessionStart hook timeout
            creationflags=NO_WINDOW,
        )
    except subprocess.TimeoutExpired:
        return []
    names = []
    for line in result.stdout.splitlines():
        name = line.split(",")[0].strip('"').lstrip("\\")
        if name.startswith("RM-") and name not in names:
            names.append(name)
    return names


def main() -> int:
    try:
        lines = ["# Red Moon live state (rm_facts.py)", ""]
        installed, extracted = game_build(), data_build()
        lines.append(f"- Game build: {installed}")
        lines.append(f"- Extracted data build: {extracted}")
        lines.append(f"- Build agreement: {build_agreement(installed, extracted)}")
        states = ", ".join(
            f"{label} {port} {'BUSY' if port_busy(port) else 'free'}"
            for port, label in sorted(PORT_LABELS.items())
        )
        lines.append(f"- Ports: {states}")
        tasks = scheduled_tasks()
        lines.append(f"- RM-* scheduled tasks: {', '.join(tasks) if tasks else 'none'}")
        sys.stdout.write("\n".join(lines) + "\n")
    except (OSError, ValueError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

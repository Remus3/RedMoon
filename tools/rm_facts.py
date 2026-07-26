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


def game_build() -> str:
    version = DEFAULT_INSTALL / "VERSION"
    if not version.is_file():
        return "not installed"
    try:
        return parse_build_id(version.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return "unparseable"


def data_build() -> str:
    pointer = REPO / "data" / "rmdata" / "current.txt"
    if not pointer.is_file():
        return "none extracted"
    return pointer.read_text(encoding="utf-8").strip()


def scheduled_tasks() -> list[str]:
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "csv", "/nh"],
            capture_output=True,
            text=True,
            timeout=5,  # comfortably under the 10s SessionStart hook timeout
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
        lines.append(f"- Game build: {game_build()}")
        lines.append(f"- Extracted data build: {data_build()}")
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

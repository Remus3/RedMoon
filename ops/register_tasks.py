#!/usr/bin/env python3
"""Register and remove Red Moon scheduled tasks.

All task names use the RM- prefix. That namespace is exclusive to this project;
never create or remove a task under any other prefix from here.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYTHONW = Path(
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\pythonw.exe"
)

TASKS: dict[str, dict] = {
    "RM-DataRefresh": {
        "script": str(REPO / "tools" / "rmdata_extract.py"),
        "schedule": "DAILY",
        "start_time": "05:30",
        "description": "Re-extract the V Rising data floor. No-op unless the build changed.",
    },
}


def build_create_command(name: str) -> list[str]:
    """schtasks argv that creates the named task."""
    spec = TASKS[name]
    action = f'"{PYTHONW}" "{spec["script"]}"'
    return [
        "schtasks",
        "/create",
        "/tn",
        name,
        "/tr",
        action,
        "/sc",
        spec["schedule"],
        "/st",
        spec["start_time"],
        "/rl",
        "HIGHEST",
        "/f",
    ]


def build_delete_command(name: str) -> list[str]:
    """schtasks argv that removes the named task."""
    if name not in TASKS:
        raise KeyError(f"unknown task {name!r}")
    return ["schtasks", "/delete", "/tn", name, "/f"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage RM-* scheduled tasks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true")
    group.add_argument("--remove", action="store_true")
    group.add_argument("--show", action="store_true")
    args = parser.parse_args()

    for name in TASKS:
        if args.show:
            print(f"{name}: {' '.join(build_create_command(name))}")
            continue
        argv = build_create_command(name) if args.install else build_delete_command(name)
        result = subprocess.run(argv, capture_output=True, text=True)
        print(f"{name}: exit {result.returncode} {result.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""PostToolUse edit guard.

py_compile only by default, because a syntax error crashes silently under
pythonw.exe. Set RM_FULL_SUITE=1 to run the whole suite after every edit during
a tier 2 batch (CLAUDE.md R5).

Never raises and never blocks. It reports to stdout only.
"""
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        path_text = str(payload.get("tool_input", {}).get("file_path", ""))
        if path_text.endswith(".py") and Path(path_text).is_file():
            try:
                py_compile.compile(path_text, doraise=True)
            except py_compile.PyCompileError as exc:
                sys.stdout.write(f"py_compile FAILED: {exc}\n")
                return 0

        if os.environ.get("RM_FULL_SUITE") == "1":
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=str(REPO),
                capture_output=True,
                text=True,
            )
            sys.stdout.write(result.stdout[-2000:])
    except (ValueError, TypeError, OSError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

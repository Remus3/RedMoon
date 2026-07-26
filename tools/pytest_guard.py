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
        if not isinstance(payload, dict):
            # A syntactically valid but non-object top-level JSON value (null,
            # a number, a list, a bare string) must not reach .get(...) as-is -
            # treat it as an empty payload rather than relying on the except
            # below to catch the AttributeError.
            payload = {}
        path_text = str(payload.get("tool_input", {}).get("file_path", ""))
        if path_text.endswith(".py") and Path(path_text).is_file():
            try:
                py_compile.compile(path_text, doraise=True)
            except py_compile.PyCompileError as exc:
                sys.stdout.write(f"py_compile FAILED: {exc}\n")
                return 0

        if os.environ.get("RM_FULL_SUITE") == "1":
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q"],
                    cwd=str(REPO),
                    capture_output=True,
                    text=True,
                    # Deliberately set BELOW this hook's 900s PostToolUse
                    # timeout in .claude/settings.json, so this script's own
                    # except below fires first and kills the child pytest
                    # process cleanly. If this bound were >= the harness
                    # timeout, the harness would kill the parent hook process
                    # first, bypassing this except entirely, and the child
                    # pytest run could be orphaned and keep running.
                    timeout=600,
                )
                sys.stdout.write(result.stdout[-2000:])
            except subprocess.TimeoutExpired:
                sys.stdout.write("pytest_guard: RM_FULL_SUITE run timed out after 600s\n")
    except (ValueError, TypeError, OSError, AttributeError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

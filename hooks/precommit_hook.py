#!/usr/bin/env python3
"""git pre-commit entry point for the Red Moon commit gate.

`tools/precommit_gate.py` holds the checks and is frozen. It is shaped for
Claude Code's PreToolUse protocol: it reads JSON on stdin and `main()` always
returns 0, emitting a refusal as a JSON permission decision. git reads neither
stdin JSON nor stdout - it reads an exit code and nothing else. So this wrapper
calls the same `check_staged()` and turns a non-empty reason list into a
non-zero exit.

It deliberately does NOT swallow exceptions the way the PreToolUse gate does. A
crashing PreToolUse hook must not block unrelated tooling; a crashing commit
gate must block the commit, because a check that did not run did not pass.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is hooks/, not the repo
# root. Bootstrap the root before importing anything from tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.precommit_gate import check_staged  # noqa: E402

MAX_REPORTED = 20


def repo_root() -> Path:
    """The repository being committed to, not the one this file lives in.

    Those differ whenever the hooks directory is shared, which is the case the
    tests exercise: the hook is invoked from a scratch repo while its own
    imports resolve out of C:\\RedMoon.
    """
    fallback = Path(__file__).resolve().parents[1]
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return fallback
    if result.returncode != 0 or not result.stdout.strip():
        return fallback
    return Path(result.stdout.strip())


def main() -> int:
    reasons = check_staged(repo_root())
    if not reasons:
        return 0
    sys.stderr.write("COMMIT BLOCKED by hooks/pre-commit\n")
    for reason in reasons[:MAX_REPORTED]:
        sys.stderr.write(f"  {reason}\n")
    if len(reasons) > MAX_REPORTED:
        sys.stderr.write(f"  ... and {len(reasons) - MAX_REPORTED} more\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())

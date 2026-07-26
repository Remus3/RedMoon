#!/usr/bin/env python3
"""Point git at the committed hooks/ directory.

`.git/hooks` is not version controlled, so a fresh clone inherits only sample
files and the commit gate would be a script nothing calls. One `git config`
selects the tracked `hooks/` directory instead. This script exists so that one
command is discoverable and verifiable rather than tribal knowledge.

Idempotent. `--check` verifies without writing and is what the test suite runs.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS_VALUE = "hooks"
REQUIRED_FILES = ("pre-commit", "precommit_hook.py")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=30,
    )


def current_hooks_path() -> str | None:
    result = _git("config", "core.hooksPath")
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def missing_hook_files() -> list[str]:
    return [name for name in REQUIRED_FILES if not (REPO / HOOKS_VALUE / name).is_file()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the wiring and exit non-zero if it is absent, writing nothing",
    )
    args = parser.parse_args(argv)

    missing = missing_hook_files()
    if missing:
        print(f"hooks/ is incomplete, missing: {', '.join(missing)}")
        return 1

    configured = current_hooks_path()

    if args.check:
        if configured != HOOKS_VALUE:
            print(f"core.hooksPath is {configured!r}, expected {HOOKS_VALUE!r}")
            print("run: python ops/install_git_hooks.py")
            return 1
        print(f"core.hooksPath={configured} - the commit gate is wired")
        return 0

    if configured == HOOKS_VALUE:
        print(f"core.hooksPath is already {HOOKS_VALUE} - nothing to do")
        return 0

    result = _git("config", "core.hooksPath", HOOKS_VALUE)
    if result.returncode != 0:
        print(f"git config failed: {result.stderr.strip()}")
        return 1
    print(f"core.hooksPath set to {HOOKS_VALUE}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""PreToolUse commit gate.

Blocks a commit whose staged authored files contain non-ASCII codepoints, or
whose staged Python files have any ruff finding. Ruff runs over the full
current content of each staged .py file and blocks on any finding, including
pre-existing lint debt on lines the commit never touched - this is not a
net-new-only check. See CLAUDE.md hard rules.

Never raises: a crashing gate must not block tooling.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.ascii_guard import is_authored, scan_text  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def staged_files(repo: Path | None = None) -> list[str]:
    """Repo-relative POSIX paths of files staged for commit."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            cwd=str(repo or REPO),
            capture_output=True,
            text=True,
            timeout=10,  # comfortably under the 60s PreToolUse hook timeout
        )
    except subprocess.TimeoutExpired:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_staged(repo: Path | None = None) -> list[str]:
    """Return blocking reasons. An empty list means the commit may proceed."""
    root = Path(repo or REPO)
    reasons: list[str] = []
    python_files: list[str] = []

    for rel in staged_files(root):
        path = root / rel
        if not path.is_file():
            continue
        if not is_authored(Path(rel)):
            continue
        if path.suffix == ".py":
            python_files.append(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, col_no, char in scan_text(text):
            reasons.append(
                f"{rel}:{line_no}:{col_no} non-ascii U+{ord(char):04X} - "
                "authored content must be 7-bit ASCII (CLAUDE.md hard rule)"
            )

    if python_files:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "ruff", "check", *python_files],
                cwd=str(root),
                capture_output=True,
                text=True,
                timeout=30,  # comfortably under the 60s PreToolUse hook timeout
            )
        except subprocess.TimeoutExpired:
            return reasons
        if result.returncode not in (0, 1):
            return reasons
        if result.returncode == 1:
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("Found "):
                    reasons.append(f"ruff: {line.strip()}")

    return reasons


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
        command = str(payload.get("tool_input", {}).get("command", ""))
        if "git commit" not in command:
            return 0
        reasons = check_staged()
        if reasons:
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Commit blocked:\n" + "\n".join(reasons[:20]),
                }
            }
            sys.stdout.write(json.dumps(out))
    except (ValueError, TypeError, OSError, AttributeError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())

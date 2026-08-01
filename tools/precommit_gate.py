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
import re
import shlex
import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.ascii_guard import is_authored, scan_text  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


# Shell operators that end one command and begin another. A commit hiding after
# any of these still has to be caught.
_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;&|\n]")

# git's own options that take a value, so the subcommand scan can step over them
# rather than mistaking the value for the subcommand.
_GIT_VALUE_OPTS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}


def _tokenize(segment: str) -> list[str]:
    """Split a shell segment WITHOUT treating backslash as an escape.

    posix=True would eat the separators in a Windows path, so `git -C C:\\RedMoon`
    would resolve to a nonexistent `C:RedMoon` and the gate would silently fall
    back to the main tree - reintroducing the very bug this function exists to
    fix. posix=False keeps backslashes and leaves quotes attached, so strip the
    surrounding pair afterwards.
    """
    tokens = []
    for tok in shlex.split(segment, posix=False):
        if len(tok) >= 2 and tok[0] == tok[-1] and tok[0] in "\"'":
            tok = tok[1:-1]
        tokens.append(tok)
    return tokens


def _git_subcommand(tokens: list[str]) -> tuple[str | None, str | None]:
    """Return (subcommand, -C path) for a token list whose first token is git."""
    i = 1
    cpath = None
    while i < len(tokens):
        tok = tokens[i]
        if tok in _GIT_VALUE_OPTS:
            if tok == "-C" and i + 1 < len(tokens):
                cpath = tokens[i + 1]
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok, cpath
    return None, cpath


def is_commit_command(command: str) -> bool:
    """True when the command actually INVOKES a commit.

    The gate used to test `"git commit" in command`, which fired on any command
    that merely QUOTED the phrase - a prompt argument, an echo, a grep pattern -
    and gated it against whatever happened to be staged at the time.

    A false negative here is far worse than a false positive, so an unparseable
    command falls back to the old substring test rather than being waved
    through.
    """
    if "commit" not in command:
        return False
    for segment in _SEGMENT_SPLIT.split(command):
        segment = segment.strip()
        if not segment:
            continue
        try:
            tokens = _tokenize(segment)
        except ValueError:
            # Unbalanced quotes. Fail safe: over-block rather than let a commit
            # through on a quoting error.
            return "git commit" in command
        if not tokens:
            continue
        if Path(tokens[0]).name.lower() in ("git", "git.exe"):
            sub, _ = _git_subcommand(tokens)
            if sub == "commit":
                return True
    return False


def _repo_root(path: Path) -> Path | None:
    """Resolve path to the top of its working tree, or None if it is not one."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(path),
            capture_output=True,
            text=True,
            timeout=10,  # comfortably under the 60s PreToolUse hook timeout
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root) if root else None


def target_repo(payload: dict) -> Path:
    """The working tree the commit will actually land in.

    main() used to inspect the hardcoded main tree no matter where the command
    ran, so a commit inside a WORKTREE was gated against main's staging area and
    its own was never read. Every headless design RM has been offered is
    worktree-based, which made the gate blind to exactly those runs.

    Falls back to the main tree whenever the target cannot be resolved - an
    unresolvable path must not silently disable the gate.
    """
    command = str(payload.get("tool_input", {}).get("command", ""))
    candidates = []
    try:
        for segment in _SEGMENT_SPLIT.split(command):
            tokens = _tokenize(segment.strip())
            if tokens and Path(tokens[0]).name.lower() in ("git", "git.exe"):
                sub, cpath = _git_subcommand(tokens)
                if sub == "commit" and cpath:
                    candidates.append(cpath)
    except ValueError:
        pass
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        candidates.append(cwd)
    for cand in candidates:
        try:
            path = Path(cand)
            if not path.is_dir():
                continue
        except (OSError, ValueError):
            continue
        root = _repo_root(path)
        if root is not None:
            return root
    return REPO


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
        if not is_commit_command(command):
            return 0
        reasons = check_staged(target_repo(payload))
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

"""The commit gate must be reachable from git, not merely present on disk.

`tools/precommit_gate.py` is shaped for Claude Code's PreToolUse protocol: it
reads JSON on stdin and `main()` always returns 0, so git can never learn a
refusal from it. It is also frozen. The wiring therefore lives outside it, in a
committed `hooks/` directory selected by `core.hooksPath`, because `.git/hooks`
is not version controlled and a fresh clone would inherit nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOKS_DIR = REPO / "hooks"


def _git(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd or REPO),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_core_hooks_path_selects_the_committed_hooks_dir():
    result = _git("config", "core.hooksPath")
    assert result.returncode == 0, (
        "core.hooksPath is unset, so git reads .git/hooks and the gate is a "
        "script nothing calls"
    )
    assert result.stdout.strip() == "hooks"


def test_pre_commit_hook_is_tracked_so_a_fresh_clone_inherits_it():
    assert (HOOKS_DIR / "pre-commit").is_file()
    assert (HOOKS_DIR / "precommit_hook.py").is_file()
    tracked = _git("ls-files", "--error-unmatch", "hooks/pre-commit", "hooks/precommit_hook.py")
    assert tracked.returncode == 0, ".git/hooks is not version controlled; hooks/ must be"


def test_pre_commit_shim_dispatches_to_the_python_entry_point():
    text = (HOOKS_DIR / "pre-commit").read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh"), "git for Windows runs hooks through sh"
    assert "precommit_hook.py" in text


def test_entry_point_calls_the_frozen_gate_rather_than_reimplementing_it():
    text = (HOOKS_DIR / "precommit_hook.py").read_text(encoding="utf-8")
    assert "from tools.precommit_gate import check_staged" in text


def test_entry_point_exits_zero_when_nothing_is_staged(tmp_path):
    """A real execution of the hook, against a clean scratch repo."""
    _git("init", "-q", str(tmp_path), cwd=REPO)
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "precommit_hook.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_entry_point_exits_nonzero_on_a_staged_bom(tmp_path):
    """The exact defect that reached master in commit 2f14c4c.

    A UTF-8 BOM decodes to U+FEFF at line 1 column 1, which is above 127 and so
    is a non-ASCII finding like any other. Asserted end to end through the hook
    process, because an exit code is the only thing git reads.
    """
    _git("init", "-q", str(tmp_path), cwd=REPO)
    bad = tmp_path / "notes.md"
    bad.write_bytes(b"\xef\xbb\xbf# Notes\n")
    _git("add", "notes.md", cwd=tmp_path)

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "precommit_hook.py")],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode != 0, "a staged BOM must block the commit"
    assert "U+FEFF" in result.stderr


def test_installer_reports_the_wiring_as_installed():
    result = subprocess.run(
        [sys.executable, str(REPO / "ops" / "install_git_hooks.py"), "--check"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

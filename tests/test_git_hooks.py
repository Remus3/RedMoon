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

import pytest

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


def _default_hooks_dir() -> Path:
    """`.git/hooks`, resolved through git so a worktree does not fool it."""
    result = _git("rev-parse", "--git-common-dir")
    common = Path(result.stdout.strip())
    if not common.is_absolute():
        common = REPO / common
    return common / "hooks"


def test_no_orphaned_hooks_left_behind_in_git_hooks():
    """Setting core.hooksPath silently disables whatever `.git/hooks` holds.

    This is not hypothetical - it cost the other project on this box its Git LFS
    pre-push hook, so pushes looked clean while LFS content never reached the
    remote. It fails in the direction that loses data and reports success, which
    is why it is asserted rather than left as a note.

    RM is pre-armed for exactly that: `filter.lfs.required=true` is configured,
    and `git lfs install` writes its hooks to `.git/hooks`, where core.hooksPath
    makes git ignore them. The first LFS-tracked file added here would arrive
    with an inert pre-push unless the hooks are ported into `hooks/` too.
    """
    configured = _git("config", "core.hooksPath").stdout.strip()
    default_dir = _default_hooks_dir()
    if not configured or (REPO / configured).resolve() == default_dir.resolve():
        # `.git/hooks` IS the active directory, so nothing there is orphaned.
        # That core.hooksPath must be set at all is a separate assertion, in
        # test_core_hooks_path_selects_the_committed_hooks_dir.
        pytest.skip("core.hooksPath is unset, so .git/hooks is not bypassed")

    if not default_dir.is_dir():
        return

    orphans = sorted(
        entry.name
        for entry in default_dir.iterdir()
        if entry.is_file() and not entry.name.endswith(".sample")
    )
    assert not orphans, (
        f"core.hooksPath={configured!r}, so git ignores {default_dir}, but it "
        f"holds {orphans} - these hooks look installed and never run. Port them "
        f"into hooks/ or delete them; do not leave them to be believed in."
    )


def _run_commit_msg(tmp_path: Path, message: str) -> tuple[subprocess.CompletedProcess, str]:
    """Run the commit-msg entry point over a message file, return it and the rewrite."""
    target = tmp_path / "COMMIT_EDITMSG"
    target.write_text(message, encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "commitmsg_hook.py"), str(target)],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return result, target.read_text(encoding="utf-8")


def test_commit_msg_hook_is_tracked_so_a_fresh_clone_inherits_it():
    assert (HOOKS_DIR / "commit-msg").is_file()
    assert (HOOKS_DIR / "commitmsg_hook.py").is_file()
    tracked = _git("ls-files", "--error-unmatch", "hooks/commit-msg", "hooks/commitmsg_hook.py")
    assert tracked.returncode == 0, ".git/hooks is not version controlled; hooks/ must be"


def test_commit_msg_shim_dispatches_to_the_python_entry_point():
    text = (HOOKS_DIR / "commit-msg").read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh"), "git for Windows runs hooks through sh"
    assert "commitmsg_hook.py" in text


def test_claude_coauthor_trailer_is_stripped_and_warned(tmp_path):
    """Operator policy 2026-06-03: never emit the Claude co-author trailer.

    Fourteen of the last thirty commits carried it because nothing enforced the
    policy. The harness default appends it, so the repo must remove it.
    """
    result, rewritten = _run_commit_msg(
        tmp_path,
        "docs(session): a subject line\n"
        "\n"
        "A body paragraph.\n"
        "\n"
        "Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n",
    )
    assert result.returncode == 0, "the hook strips rather than blocks"
    assert "Co-Authored-By" not in rewritten
    assert "noreply@anthropic.com" not in rewritten
    assert rewritten == "docs(session): a subject line\n\nA body paragraph.\n"
    assert "2026-06-03" in result.stderr, "a silent strip is an invisible strip"


def test_trailer_is_matched_regardless_of_case(tmp_path):
    _, rewritten = _run_commit_msg(
        tmp_path,
        "fix: something\n\nco-authored-by: Claude <noreply@anthropic.com>\n",
    )
    assert "anthropic" not in rewritten.lower()


def test_a_human_coauthor_survives(tmp_path):
    """The policy names the Claude trailer, not co-authorship as such."""
    _, rewritten = _run_commit_msg(
        tmp_path,
        "feat: paired work\n\nCo-Authored-By: Moonbeam <close.benham@gmail.com>\n",
    )
    assert "Moonbeam" in rewritten


def test_a_message_without_the_trailer_is_left_byte_identical(tmp_path):
    original = "docs(ledger): backfill a hash\n\n# Please enter the commit message.\n"
    result, rewritten = _run_commit_msg(tmp_path, original)
    assert rewritten == original
    assert result.returncode == 0
    assert result.stderr == ""


def test_installer_requires_the_commit_msg_hook_too():
    text = (REPO / "ops" / "install_git_hooks.py").read_text(encoding="utf-8")
    assert "commit-msg" in text, "an uninstalled hook is a policy nothing enforces"
    assert "commitmsg_hook.py" in text


def test_installer_reports_the_wiring_as_installed():
    result = subprocess.run(
        [sys.executable, str(REPO / "ops" / "install_git_hooks.py"), "--check"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from core import ports
from tools import precommit_gate, text_first_guard

REPO = Path(__file__).resolve().parents[1]
SETTINGS = REPO / ".claude" / "settings.json"


def run_hook(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "tools" / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def test_text_first_guard_denies_a_screen_text_reader():
    decision = text_first_guard.decide({"tool_name": "mcp__Windows-MCP__Scrape"})
    assert decision is not None
    inner = decision["hookSpecificOutput"]
    assert inner["hookEventName"] == "PreToolUse"
    assert inner["permissionDecision"] == "deny"
    assert str(ports.DASHBOARD) in inner["permissionDecisionReason"]


def test_text_first_guard_allows_screenshots_and_ordinary_tools():
    assert text_first_guard.decide({"tool_name": "mcp__computer-use__screenshot"}) is None
    assert text_first_guard.decide({"tool_name": "Read"}) is None
    assert text_first_guard.decide({}) is None


def test_text_first_guard_honours_the_escape_hatch(tmp_path, monkeypatch):
    flag = tmp_path / "allow_visual.flag"
    flag.write_text("", encoding="utf-8")
    monkeypatch.setattr(text_first_guard, "FLAG", flag)
    assert text_first_guard.decide({"tool_name": "mcp__Windows-MCP__Scrape"}) is None


def test_text_first_guard_exits_zero_on_malformed_stdin():
    result = run_hook("text_first_guard.py", {})
    assert result.returncode == 0


def test_precommit_gate_blocks_a_non_ascii_staged_file(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    bad = tmp_path / "note.md"
    bad.write_text("a \u2014 dash\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.md"], cwd=tmp_path, check=True)
    reasons = precommit_gate.check_staged(tmp_path)
    assert reasons
    assert "note.md" in reasons[0]
    assert "U+2014" in reasons[0]


def test_precommit_gate_passes_a_clean_staged_file(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    good = tmp_path / "note.md"
    good.write_text("a - dash\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.md"], cwd=tmp_path, check=True)
    assert precommit_gate.check_staged(tmp_path) == []


def test_gate_ignores_a_commit_phrase_inside_a_quoted_argument():
    """Mentioning a commit is not performing one.

    The gate matched the bare substring "git commit" anywhere in the command,
    so a command that merely QUOTED the phrase was gated against whatever
    happened to be staged. Measured 2026-08-01: a headless probe was denied
    because the phrase sat inside a prompt argument, and the command was not a
    commit at all.
    """
    assert not precommit_gate.is_commit_command(
        'claude -p "run this: git commit -m x" --print'
    )
    assert not precommit_gate.is_commit_command('echo "remember to git commit"')
    assert not precommit_gate.is_commit_command("grep -rn 'git commit' docs/")


def test_gate_still_fires_on_every_real_commit_shape():
    """False negatives are far worse than false positives here."""
    assert precommit_gate.is_commit_command('git commit -m "x"')
    assert precommit_gate.is_commit_command("git commit")
    assert precommit_gate.is_commit_command("git -C C:/RedMoon commit -m x")
    assert precommit_gate.is_commit_command("cd foo && git commit -m x")
    assert precommit_gate.is_commit_command("git add . ; git commit -F msg.txt")
    assert precommit_gate.is_commit_command("git --no-pager commit --amend")


def test_gate_fails_safe_on_an_unparseable_command():
    """An unlexable command containing the phrase must still gate.

    A quoting error must not become a hole. If the command cannot be tokenized
    the gate falls back to the old substring behaviour, which over-blocks.
    """
    assert precommit_gate.is_commit_command('git commit -m "unclosed')


def test_gate_inspects_the_tree_the_commit_actually_targets(tmp_path):
    """A worktree commit must be gated against the WORKTREE, not the main tree.

    main() called check_staged() with no argument, so it always inspected the
    hardcoded main tree no matter where the command ran. Every headless design
    RM has been offered is worktree-based, which made the gate structurally
    blind to exactly the runs it is there to guard.
    """
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    bad = tmp_path / "note.md"
    bad.write_text("a \u2014 dash\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.md"], cwd=tmp_path, check=True)

    # -C names the target tree explicitly.
    assert precommit_gate.target_repo(
        {"tool_input": {"command": f"git -C {tmp_path} commit -m x"}}
    ) == tmp_path
    # Otherwise the session cwd names it.
    assert precommit_gate.target_repo(
        {"cwd": str(tmp_path), "tool_input": {"command": "git commit -m x"}}
    ) == tmp_path
    # With neither, the main tree remains the answer.
    assert precommit_gate.target_repo({"tool_input": {"command": "git commit"}}) == REPO


def test_gate_falls_back_to_the_main_tree_for_a_non_repo_path(tmp_path):
    """A cwd that is not a git repo must not silently disable the gate."""
    plain = tmp_path / "not_a_repo"
    plain.mkdir()
    assert precommit_gate.target_repo(
        {"cwd": str(plain), "tool_input": {"command": "git commit -m x"}}
    ) == REPO


def test_settings_json_is_valid_and_wires_every_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    wired = json.dumps(settings["hooks"])
    for script in ("precommit_gate.py", "text_first_guard.py", "pytest_guard.py", "rm_facts.py"):
        assert script in wired, f"{script} is not wired into settings.json"
    assert "C:\\\\RedMoon" in wired or "C:\\RedMoon" in wired


# A bare tool name, or a pipe-separated alternation of them. The hyphen is
# allowed because real MCP tool names carry one (mcp__computer-use__screenshot);
# nothing else beyond word characters is.
MATCHER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*(\|[A-Za-z_][A-Za-z0-9_-]*)*$")


def test_every_matcher_is_a_plain_tool_name_alternation():
    """A hook matcher is evaluated against the TOOL NAME only.

    Permission-rule specifier syntax - the Bash(git commit:*) form that is
    valid in permissions.allow - is NOT understood in a matcher field. It does
    not error; it simply never matches any tool name, so the hook silently
    never fires. That is exactly how the precommit gate sat wired but dead:
    its matcher was Bash(git commit:*), which no tool name can ever equal.

    Every matcher must therefore be a bare tool name or a pipe-separated
    alternation of bare tool names, with no parentheses, colons or globs. Any
    command-scoping a hook needs belongs inside the hook script, which is where
    tools/precommit_gate.py already does it by returning early unless
    "git commit" appears in the command.
    """
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    seen = 0
    for event, entries in settings["hooks"].items():
        for entry in entries:
            if "matcher" not in entry:
                continue
            matcher = entry["matcher"]
            seen += 1
            for banned in ("(", ")", ":", "*"):
                assert banned not in matcher, (
                    f"{event} matcher {matcher!r} contains {banned!r} - that is "
                    "permission-rule specifier syntax, which never matches a tool name"
                )
            assert MATCHER_RE.match(matcher), (
                f"{event} matcher {matcher!r} is not a plain tool-name alternation"
            )
    assert seen > 0, "no matcher fields found - the scan would pass vacuously"


def test_precommit_gate_matcher_covers_the_shell_tools():
    """The commit gate must be reachable from every tool that can run git commit."""
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    matchers = [
        entry["matcher"]
        for entry in settings["hooks"]["PreToolUse"]
        if any("precommit_gate.py" in h.get("command", "") for h in entry.get("hooks", []))
    ]
    assert matchers, "precommit_gate.py is not wired into any PreToolUse entry"
    covered = {name for matcher in matchers for name in matcher.split("|")}
    assert {"Bash", "PowerShell"} <= covered, (
        f"precommit gate matchers {matchers} do not cover both shell tools"
    )


def test_settings_json_references_no_other_project():
    text = SETTINGS.read_text(encoding="utf-8")
    assert "Riot" not in text
    assert all(ord(c) <= 127 for c in text)


def test_rm_facts_runs_and_reports_ports():
    result = run_hook("rm_facts.py", {"hook_event_name": "SessionStart"})
    assert result.returncode == 0
    assert str(ports.BRIDGE) in result.stdout
    assert "1.1.13.0-r99712" in result.stdout or "not installed" in result.stdout


NON_OBJECT_JSON_PAYLOADS = ["null", "42", "[1, 2]", '"just a string"']


@pytest.mark.parametrize("script", ["text_first_guard.py", "precommit_gate.py", "pytest_guard.py"])
@pytest.mark.parametrize("bad_stdin", NON_OBJECT_JSON_PAYLOADS)
def test_hooks_exit_zero_on_non_object_json_stdin(script, bad_stdin):
    """A syntactically valid but non-object top-level JSON value on stdin

    (null, a bare number, a list, a bare string) must never crash a hook -
    payload.get(...) on a non-dict raises AttributeError, and a crashing
    PreToolUse hook would block every tool call for the whole session.
    """
    result = subprocess.run(
        [sys.executable, str(REPO / "tools" / script)],
        input=bad_stdin,
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert result.returncode == 0, (
        f"{script} with stdin {bad_stdin!r} exited {result.returncode}: {result.stderr}"
    )


def _init_repo_with_ruff_toml(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    shutil.copy(REPO / "ruff.toml", tmp_path / "ruff.toml")


def test_precommit_gate_blocks_a_staged_python_file_with_a_ruff_finding(tmp_path):
    _init_repo_with_ruff_toml(tmp_path)
    bad = tmp_path / "bad.py"
    bad.write_text("import os\n\n\ndef unused():\n    pass\n", encoding="utf-8")
    subprocess.run(["git", "add", "bad.py", "ruff.toml"], cwd=tmp_path, check=True)
    reasons = precommit_gate.check_staged(tmp_path)
    assert any("ruff" in reason for reason in reasons)


def test_precommit_gate_passes_a_clean_staged_python_file(tmp_path):
    _init_repo_with_ruff_toml(tmp_path)
    good = tmp_path / "good.py"
    good.write_text(
        '"""A clean module."""\n\n\ndef greet() -> str:\n    return "hi"\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "good.py", "ruff.toml"], cwd=tmp_path, check=True)
    assert precommit_gate.check_staged(tmp_path) == []


def test_harness_timeouts_exceed_internal_subprocess_timeouts():
    """The .claude/settings.json harness timeout for each hook must exceed the
    largest internal subprocess timeout that hook's script can hit.

    If the harness timeout is <= a script's own internal bound, the harness
    kills the parent hook process before the script's own
    except subprocess.TimeoutExpired handler can fire and terminate its
    child cleanly - orphaning a hung child that keeps running after the hook
    itself is gone. Keeping this machine-checked means a future change to
    either number without the other fails this test instead of silently
    reopening that gap.
    """
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))

    # Largest single internal subprocess timeout (seconds) each script uses,
    # per tools/<script>.py.
    script_internal_timeout = {
        "rm_facts.py": 5,
        "precommit_gate.py": 30,
        "pytest_guard.py": 600,
    }
    # text_first_guard.py makes no subprocess calls, so it has no entry and
    # is not checked here.

    # precommit_gate.py can make BOTH of its bounded calls (git diff, then
    # ruff check) in a single invocation - check against their sum, not just
    # the larger of the two, since both can occur one after the other.
    precommit_gate_call_sum = 10 + 30

    checked: set[str] = set()
    for hook_entries in settings["hooks"].values():
        for entry in hook_entries:
            for hook in entry.get("hooks", []):
                command = hook.get("command", "")
                declared_timeout = hook.get("timeout")
                if declared_timeout is None:
                    continue
                for script, internal_timeout in script_internal_timeout.items():
                    if script not in command:
                        continue
                    checked.add(script)
                    assert declared_timeout > internal_timeout, (
                        f"{script}: harness timeout {declared_timeout}s does not "
                        f"exceed its internal subprocess timeout {internal_timeout}s"
                    )
                    if script == "precommit_gate.py":
                        assert declared_timeout > precommit_gate_call_sum, (
                            f"precommit_gate.py: harness timeout {declared_timeout}s "
                            f"does not exceed its two-call sum {precommit_gate_call_sum}s"
                        )

    assert checked == set(script_internal_timeout), (
        f"expected to check {set(script_internal_timeout)}, only checked {checked}"
    )

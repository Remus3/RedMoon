import json
import subprocess
import sys
from pathlib import Path

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
    assert "8778" in inner["permissionDecisionReason"]


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


def test_settings_json_is_valid_and_wires_every_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    wired = json.dumps(settings["hooks"])
    for script in ("precommit_gate.py", "text_first_guard.py", "pytest_guard.py", "rm_facts.py"):
        assert script in wired, f"{script} is not wired into settings.json"
    assert "C:\\\\RedMoon" in wired or "C:\\RedMoon" in wired


def test_settings_json_references_no_other_project():
    text = SETTINGS.read_text(encoding="utf-8")
    assert "Riot" not in text
    assert all(ord(c) <= 127 for c in text)


def test_rm_facts_runs_and_reports_ports():
    result = run_hook("rm_facts.py", {"hook_event_name": "SessionStart"})
    assert result.returncode == 0
    assert "8777" in result.stdout
    assert "1.1.13.0-r99712" in result.stdout or "not installed" in result.stdout

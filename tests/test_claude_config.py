from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLAUDE_DIR = REPO / ".claude"
MEMORY = Path(r"C:\Users\Administrator\.claude\projects\C--RedMoon\memory")

REQUIRED_COMMANDS = ["done.md", "root-cause-fix.md", "sync-docs.md"]


def test_verifier_agent_exists_with_frontmatter():
    text = (CLAUDE_DIR / "agents" / "verifier.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: verifier" in text
    assert "description:" in text


def test_every_required_command_exists_and_is_non_empty():
    for name in REQUIRED_COMMANDS:
        path = CLAUDE_DIR / "commands" / name
        assert path.is_file(), f"missing command {name}"
        assert path.read_text(encoding="utf-8").strip()


def test_commands_reference_the_ledger_not_claude_md():
    text = (CLAUDE_DIR / "commands" / "done.md").read_text(encoding="utf-8")
    assert "docs/LEDGER.md" in text


def test_claude_dir_is_ascii():
    for path in CLAUDE_DIR.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert all(ord(c) <= 127 for c in text), f"{path} is not ascii"


def test_memory_namespace_is_seeded():
    index = MEMORY / "MEMORY.md"
    assert index.is_file(), "memory index not seeded"
    text = index.read_text(encoding="utf-8")
    for entry in ("project_redmoon_ports", "project_vrising_build_pin", "user_operator_profile"):
        assert entry in text, f"{entry} not listed in MEMORY.md"
        assert (MEMORY / f"{entry}.md").is_file(), f"{entry}.md missing"


def test_memory_entries_have_frontmatter():
    for path in MEMORY.glob("*.md"):
        if path.name == "MEMORY.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{path.name} has no frontmatter"
        assert "name:" in text and "description:" in text and "type:" in text

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLAUDE_DIR = REPO / ".claude"
MEMORY = Path(r"C:\Users\Administrator\.claude\projects\C--RedMoon\memory")
MEMORY_SEED = REPO / "docs" / "memory_seed"

REQUIRED_COMMANDS = ["done.md", "root-cause-fix.md", "sync-docs.md"]

EXPECTED_MEMORY_ENTRIES = {
    "project_redmoon_ports",
    "project_vrising_build_pin",
    "project_stats_require_bridge",
    "user_operator_profile",
}


def _frontmatter_body(text):
    lines = text.splitlines()
    assert lines and lines[0].strip() == "---", "missing opening frontmatter marker"
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break
    assert end_idx is not None, "frontmatter block never closes"
    return "\n".join(lines[end_idx + 1 :])


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
    index_text = index.read_text(encoding="utf-8")

    entry_files = {p.stem for p in MEMORY.glob("*.md") if p.name != "MEMORY.md"}
    assert entry_files == EXPECTED_MEMORY_ENTRIES, (
        f"memory directory entries {entry_files} do not match "
        f"expected {EXPECTED_MEMORY_ENTRIES} - index and directory must agree"
    )

    for entry in EXPECTED_MEMORY_ENTRIES:
        assert entry in index_text, f"{entry} not listed in MEMORY.md"
        assert (MEMORY / f"{entry}.md").is_file(), f"{entry}.md missing"


def test_memory_seed_covers_every_live_memory_file():
    """The live memory namespace is outside the repository and uncommitted, so
    without a committed seed there is no way to recreate it if it is lost - and
    four tests here would fail with no path back. docs/memory_seed/ is that
    path. See docs/OPERATIONS.md for the restore procedure.
    """
    assert MEMORY_SEED.is_dir(), "docs/memory_seed/ is missing"
    seeded = {p.name for p in MEMORY_SEED.glob("*.md")}
    live = {p.name for p in MEMORY.glob("*.md")}
    assert seeded == live, (
        f"seed {sorted(seeded)} does not cover live {sorted(live)} - "
        "a new memory entry must be seeded in the same commit"
    )
    assert "MEMORY.md" in seeded
    for entry in EXPECTED_MEMORY_ENTRIES:
        assert f"{entry}.md" in seeded


def test_live_memory_matches_the_committed_seed():
    """Content, so the seed cannot drift silently into being un-restorable.

    Newlines are normalized because the seed's line endings are whatever git
    checked out; drift in the actual text is what this guards.
    """
    for seed_path in sorted(MEMORY_SEED.glob("*.md")):
        live_path = MEMORY / seed_path.name
        assert live_path.is_file(), f"{seed_path.name} is seeded but not live"
        seed_text = seed_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        live_text = live_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        assert live_text == seed_text, (
            f"{seed_path.name} has drifted from docs/memory_seed/ - update the "
            "seed in the same commit as the memory entry"
        )


def test_memory_seed_is_ascii():
    for path in MEMORY_SEED.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert all(ord(c) <= 127 for c in text), f"{path} is not ascii"


def test_memory_entries_have_frontmatter():
    for path in MEMORY.glob("*.md"):
        if path.name == "MEMORY.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{path.name} has no frontmatter"
        assert "name:" in text and "description:" in text and "type:" in text


def test_memory_entries_have_substantive_body():
    for path in MEMORY.glob("*.md"):
        if path.name == "MEMORY.md":
            continue
        text = path.read_text(encoding="utf-8")
        body = _frontmatter_body(text)
        non_whitespace = "".join(ch for ch in body if not ch.isspace())
        assert len(non_whitespace) >= 100, (
            f"{path.name} body has only {len(non_whitespace)} non-whitespace "
            "characters after the frontmatter block - a closed empty "
            "frontmatter block must not pass"
        )

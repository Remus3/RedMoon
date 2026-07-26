from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REQUIRED = [
    "CLAUDE.md",
    "README.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "WAKEUP_NOTES.md",
    "NEXT_SESSION_PROMPT.md",
]

REQUIRED_CLAUDE_SECTIONS = [
    "## Topology",
    "## Paths",
    "## Hard rules",
    "## Session workflow",
    "## Session-End Ritual",
    "## Output Constraints",
    "## Testing Discipline",
    "## Verification",
    "## Error Handling",
    "## Active priorities",
]


def test_every_root_doc_exists_and_is_non_empty():
    for name in REQUIRED:
        path = REPO / name
        assert path.is_file(), f"missing {name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty {name}"


def test_claude_md_has_every_required_section():
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    for heading in REQUIRED_CLAUDE_SECTIONS:
        assert heading in text, f"CLAUDE.md missing section {heading}"


def test_claude_md_stays_under_the_size_budget():
    size = (REPO / "CLAUDE.md").stat().st_size
    assert size < 60_000, f"CLAUDE.md is {size} bytes, budget is 60000"


def test_claude_md_names_the_ledger_as_the_entry_sink():
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/LEDGER.md" in text


def test_no_riot_commander_references_in_root_docs():
    for name in REQUIRED:
        text = (REPO / name).read_text(encoding="utf-8")
        assert "Riot Commander" not in text, f"{name} references Riot Commander"
        assert "C:\\Riot" not in text, f"{name} references the RC path"

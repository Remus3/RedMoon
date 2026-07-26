import re
from pathlib import Path

from core import ports

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
ADR = DOCS / "adr"

REQUIRED_DOCS = [
    "ARCHITECTURE.md",
    "OPERATIONS.md",
    "API.md",
    "BLOODFORGE.md",
    "LEDGER.md",
    "history_notes.md",
]

INDEX_LINE = re.compile(r"^- \[(ADR-\d{3})\]\((ADR-\d{3}-[a-z0-9-]+\.md)\) - .+$")


def test_required_living_docs_exist_and_are_non_empty():
    for name in REQUIRED_DOCS:
        path = DOCS / name
        assert path.is_file(), f"missing docs/{name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty docs/{name}"


def test_adr_index_links_all_resolve():
    index = (ADR / "README.md").read_text(encoding="utf-8")
    linked = [m.group(2) for line in index.splitlines() if (m := INDEX_LINE.match(line))]
    assert linked, "ADR index lists no ADRs"
    for filename in linked:
        assert (ADR / filename).is_file(), f"index links missing {filename}"


def test_every_adr_file_is_listed_in_the_index():
    index = (ADR / "README.md").read_text(encoding="utf-8")
    on_disk = sorted(p.name for p in ADR.glob("ADR-*.md"))
    for filename in on_disk:
        assert filename in index, f"{filename} exists but is not in the index"


def test_adr_003_agrees_with_the_port_registry():
    text = (ADR / "ADR-003-port-map.md").read_text(encoding="utf-8")
    for port in sorted(ports.ALL):
        assert str(port) in text, f"ADR-003 does not document port {port}"


def test_ledger_is_newest_first_and_documents_its_own_rule():
    text = (DOCS / "LEDGER.md").read_text(encoding="utf-8")
    assert "newest first" in text.lower()
    assert "CLAUDE.md" in text

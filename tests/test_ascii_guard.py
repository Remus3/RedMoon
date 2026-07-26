from pathlib import Path

from tools.ascii_guard import is_authored, scan_repo, scan_text

REPO = Path(__file__).resolve().parents[1]


def test_scan_text_clean_returns_empty():
    assert scan_text("plain ascii - fine") == []


def test_scan_text_flags_em_dash_with_position():
    findings = scan_text("line one\nbad \u2014 dash")
    assert findings == [(2, 5, "\u2014")]


def test_scan_text_flags_smart_quotes_and_en_dash():
    chars = [f[2] for f in scan_text("\u2018a\u2019 \u201cb\u201d \u2013")]
    assert chars == ["\u2018", "\u2019", "\u201c", "\u201d", "\u2013"]


def test_is_authored_accepts_source_and_docs():
    assert is_authored(Path("tools/ascii_guard.py"))
    assert is_authored(Path("docs/ARCHITECTURE.md"))
    assert is_authored(Path(".claude/settings.json"))


def test_is_authored_rejects_binary_and_excluded_trees():
    assert not is_authored(Path("data/rmdata/1.1.13.0-r99712/strings.json"))
    assert not is_authored(Path("logs/2026-07-26.log"))
    assert not is_authored(Path(".git/COMMIT_EDITMSG"))
    assert not is_authored(Path("assets/icon.png"))


def test_repo_is_ascii_clean():
    findings = scan_repo(REPO)
    assert findings == {}, f"non-ascii in authored files: {findings}"

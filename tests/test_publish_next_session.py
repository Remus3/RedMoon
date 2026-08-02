"""The Desktop hand-off writer, and the four ways it can destroy something.

`Desktop/RM-NEXT-SESSION.txt` is what the operator actually pastes into a
cleared session. Until now nothing wrote it: the copy on disk was 13,918 bytes
dated 11:18 while the repo's prompt had moved on twice, and a stale hand-off is
worse than an absent one because it READS as current.

The guards exist because this is the one writer in the project that leaves the
repository:

1. THE DESKTOP IS SHARED. LW-NEXT-SESSION.txt and RC-NEXT-SESSION.txt sit beside
   ours and belong to other projects. A path bug here silently destroys another
   project's hand-off, so the target basename is a constant and the tests assert
   the siblings are untouched byte for byte.
2. A TRUNCATED PROMPT IS WORSE THAN A STALE ONE. Both look like a hand-off; only
   one has the context. A short block is refused rather than written.
3. NON-ASCII WOULD LAND IN NOTEPAD. The CLAUDE.md hard rule applies hardest at
   the one place the text leaves the toolchain.
4. THE SOURCE IS THE REPO FILE, NEVER A RETYPED COPY, so the Desktop and
   NEXT_SESSION_PROMPT.md cannot disagree.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tools import publish_next_session as pub

REPO = Path(__file__).resolve().parents[1]

BODY = "PROMPT BODY LINE\n" * 200  # comfortably over the minimum


def _source(block: str = BODY, fences: int = 1) -> str:
    head = "# Next Session Prompt\n\nPaste the fenced block below.\n\n---\n\n"
    return head + "".join(f"```\n{block}```\n\n" for _ in range(fences))


def _desktop(tmp_path: Path) -> Path:
    desktop = tmp_path / "Desktop"
    desktop.mkdir()
    (desktop / "LW-NEXT-SESSION.txt").write_text("LW handoff\n", encoding="ascii")
    (desktop / "RC-NEXT-SESSION.txt").write_text("RC handoff\n", encoding="ascii")
    return desktop


def test_it_extracts_the_single_fenced_block():
    assert pub.extract_prompt(_source()) == BODY


def test_it_refuses_a_source_with_no_fenced_block():
    with pytest.raises(pub.Refusal) as excinfo:
        pub.extract_prompt("# Next Session Prompt\n\nnothing fenced here\n")
    assert excinfo.value.reason == "no_prompt_block"


def test_it_refuses_a_source_with_more_than_one_fenced_block():
    with pytest.raises(pub.Refusal) as excinfo:
        pub.extract_prompt(_source(fences=2))
    assert excinfo.value.reason == "multiple_prompt_blocks"


def test_it_refuses_a_prompt_short_enough_to_be_a_truncation():
    with pytest.raises(pub.Refusal) as excinfo:
        pub.extract_prompt(_source(block="too short\n"))
    assert excinfo.value.reason == "prompt_too_short"


def test_it_refuses_a_prompt_carrying_non_ascii():
    # Built with chr() rather than written literally: this file is authored
    # content, so tools/ascii_guard.py refuses an em dash here too - which it
    # duly did on the first run of this test.
    with pytest.raises(pub.Refusal) as excinfo:
        pub.extract_prompt(_source(block=BODY + f"an em dash {chr(0x2014)} here\n"))
    assert excinfo.value.reason == "non_ascii"


def test_it_refuses_when_the_desktop_directory_is_absent(tmp_path):
    with pytest.raises(pub.Refusal) as excinfo:
        pub.publish(_source(), tmp_path / "no-such-desktop")
    assert excinfo.value.reason == "no_desktop"


def test_it_writes_the_block_verbatim(tmp_path):
    desktop = _desktop(tmp_path)
    result = pub.publish(_source(), desktop)
    written = (desktop / pub.TARGET_NAME).read_text(encoding="ascii")
    assert written == BODY
    assert result["bytes"] == len(BODY.encode("ascii"))


def test_it_never_touches_the_sibling_projects_handoffs(tmp_path):
    desktop = _desktop(tmp_path)
    pub.publish(_source(), desktop)
    assert (desktop / "LW-NEXT-SESSION.txt").read_text(encoding="ascii") == "LW handoff\n"
    assert (desktop / "RC-NEXT-SESSION.txt").read_text(encoding="ascii") == "RC handoff\n"
    assert pub.TARGET_NAME == "RM-NEXT-SESSION.txt"


def test_a_refused_publish_leaves_the_previous_handoff_and_no_debris(tmp_path):
    desktop = _desktop(tmp_path)
    pub.publish(_source(), desktop)
    with pytest.raises(pub.Refusal):
        pub.publish(_source(block="too short\n"), desktop)
    assert (desktop / pub.TARGET_NAME).read_text(encoding="ascii") == BODY
    assert sorted(p.name for p in desktop.iterdir()) == [
        "LW-NEXT-SESSION.txt",
        "RC-NEXT-SESSION.txt",
        pub.TARGET_NAME,
    ]


def test_check_mode_reports_drift_without_writing(tmp_path):
    desktop = _desktop(tmp_path)
    pub.publish(_source(), desktop)
    assert pub.check(_source(), desktop)["in_sync"] is True

    moved = BODY + "one more line\n"
    report = pub.check(_source(block=moved), desktop)
    assert report["in_sync"] is False
    assert (desktop / pub.TARGET_NAME).read_text(encoding="ascii") == BODY


def test_the_real_prompt_file_yields_a_publishable_block():
    # Catches a malformed NEXT_SESSION_PROMPT.md at test time rather than at
    # the end of a session, when the operator is waiting for the hand-off.
    block = pub.extract_prompt(pub.SOURCE.read_text(encoding="utf-8"))
    assert "CONTEXT, do not re-derive." in block


def test_the_cli_check_mode_exits_nonzero_on_drift(tmp_path):
    desktop = _desktop(tmp_path)
    proc = subprocess.run(
        [sys.executable, "tools/publish_next_session.py", "--check", "--desktop", str(desktop)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, proc.stdout
    assert "in_sync" in proc.stdout

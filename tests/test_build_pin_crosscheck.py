"""The build pin, checked across the two files no existing gate can span.

`tests/test_drift_anchors.py` holds every AUTHORED site to `CLAUDE.md`'s
canonical pin, and it is thorough over the 120 tracked sites it can see. It has
one structural blind spot, and it is not an oversight: it iterates
`git ls-files`, and `data/rmdata/` is gitignored, so the extracted data tree is
invisible to it by construction. A pin bump that updated every document and left
`data/rmdata/current.txt` naming the old build would pass the whole suite.

That file is not decorative. `tools/rmdata_ingest.read_expected_build` reads it
and REFUSES a dump whose build disagrees, so a stale pointer does not fail
loudly at the point of the mistake; it fails later, as a build mismatch against
a dump that was perfectly correct.

Two checks here, and no production code.

1. `current.txt` agrees with `CLAUDE.md`.
2. `tools/rm_facts.py` prints two build lines at every session start and has
   never compared them. Importing them and asserting they agree is the whole
   gate, and it needs no edit to that frozen file.

THE SECOND CHECK HAS TO CLOSE ITS OWN HOLE. `game_build()` and `data_build()`
return the sentinels "not installed", "unparseable" and "none extracted" instead
of raising, so a machine with no game installed compares "not installed" against
"not installed"... which is not equality of two builds, it is equality of two
failures. The sentinels are therefore rejected BEFORE the comparison, or this is
a gate with nothing to catch anywhere but Legion.

The canonical-pin parse is IMPORTED from the drift-anchor module rather than
restated, so a reword of the `CLAUDE.md` line surfaces as one distinct failure
there instead of a phantom build mismatch here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests.test_drift_anchors import PIN, _canonical_pin
from tools.rm_facts import BUILD_SENTINELS, build_agreement, data_build, game_build

REPO = Path(__file__).resolve().parents[1]
CURRENT_TXT = REPO / "data" / "rmdata" / "current.txt"
HOOK = REPO / "tools" / "rm_facts.py"

# What each accessor returns INSTEAD of raising when its source is unavailable.
# Comparing two of these to each other is comparing two failures, not two
# builds, so they are excluded before any comparison is made.
#
# IMPORTED rather than restated, which is S7.2's lesson applied here: a
# hand-copied list of the sentinels drifts the moment one of them is renamed,
# and it drifts silently, because a skip guard checking for a string that can no
# longer occur simply stops skipping and starts comparing two failures.
SENTINELS = BUILD_SENTINELS


def test_the_extracted_data_pointer_agrees_with_claude_md():
    """The gitignored half of the build pin, which no drift anchor can reach."""
    if not CURRENT_TXT.is_file():
        pytest.skip(
            "data/rmdata/ is gitignored and regenerable - run "
            "tools/rmdata_extract.py to create it"
        )

    canonical = _canonical_pin()
    pointer = CURRENT_TXT.read_text(encoding="utf-8").strip()

    assert PIN.fullmatch(pointer), (
        f"data/rmdata/current.txt holds {pointer!r}, which is not a build id - "
        "it is read by tools/rmdata_ingest.read_expected_build and gates every "
        "dump"
    )
    assert pointer == canonical, (
        f"data/rmdata/current.txt names {pointer!r} but CLAUDE.md's canonical "
        f"pin is {canonical!r}. This file is gitignored, so tests/"
        "test_drift_anchors.py cannot see it and the whole suite passes while "
        "the two disagree. Re-run tools/rmdata_extract.py against the installed "
        "build, or correct the pin in CLAUDE.md."
    )


def test_rm_facts_reports_one_build_and_not_two():
    """The two lines rm_facts prints at session start must be the same build.

    They come from genuinely different places - the game install's VERSION file
    and the extracted data pointer - so agreement is a real cross-check and not
    a tautology. A session that bootstraps from a mismatch reads combat numbers
    extracted from a build the machine is no longer running.
    """
    installed = game_build()
    extracted = data_build()

    if installed in SENTINELS or extracted in SENTINELS:
        pytest.skip(
            f"one side is a sentinel rather than a build "
            f"(game_build={installed!r}, data_build={extracted!r}) - there is "
            "nothing to compare on this machine"
        )

    assert PIN.fullmatch(installed), f"game_build() returned {installed!r}"
    assert PIN.fullmatch(extracted), f"data_build() returned {extracted!r}"
    assert installed == extracted, (
        f"the game on disk is build {installed!r} but data/rmdata/ was "
        f"extracted from {extracted!r}. rm_facts.py prints both at every "
        "session start and has never compared them, so this has been readable "
        "in the banner and unenforced. Re-run tools/rmdata_extract.py."
    )


def test_build_agreement_reports_a_match():
    assert "MATCH" in build_agreement("1.1.13.0-r99712", "1.1.13.0-r99712")
    assert "MISMATCH" not in build_agreement("1.1.13.0-r99712", "1.1.13.0-r99712")


def test_build_agreement_reports_a_mismatch_and_names_both_builds():
    line = build_agreement("1.1.13.0-r99712", "1.0.10.4-r91333")
    assert "MISMATCH" in line
    assert "1.1.13.0-r99712" in line and "1.0.10.4-r91333" in line, (
        "a mismatch that does not say WHICH two builds disagree sends the "
        "operator back to the two lines above to work it out"
    )
    assert "rmdata_extract" in line, "say what to do about it, not just that it is wrong"


@pytest.mark.parametrize("sentinel", sorted(BUILD_SENTINELS))
@pytest.mark.parametrize("side", ["game", "data"])
def test_build_agreement_stands_down_on_a_sentinel(sentinel: str, side: str):
    """A sentinel on either side is an unavailable source, not a disagreement.

    Reporting MISMATCH on a machine with no game installed would be a false
    alarm at every single session start, which is the fastest way to teach an
    operator to ignore the line.
    """
    pair = (sentinel, "1.1.13.0-r99712") if side == "game" else ("1.1.13.0-r99712", sentinel)
    line = build_agreement(*pair)

    assert "NOT CHECKED" in line, f"expected a stand-down for {pair}, got {line!r}"
    assert "MISMATCH" not in line
    assert sentinel in line, "the stand-down must say which source was unavailable"


def test_two_equal_sentinels_are_not_reported_as_a_match():
    """The trap this whole guard exists for: equality of two FAILURES."""
    line = build_agreement("not installed", "not installed")
    assert "MATCH" not in line
    assert "NOT CHECKED" in line


def test_the_session_start_banner_carries_the_agreement_line():
    """End to end through the hook the operator actually sees."""
    import subprocess

    result = subprocess.run(
        [sys.executable, str(HOOK)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, "rm_facts must never break session start"
    assert "Build agreement:" in result.stdout, (
        f"the banner does not state whether the two build lines agree:\n"
        f"{result.stdout}"
    )


def test_the_sentinels_this_module_excludes_are_the_ones_rm_facts_returns():
    """The control on the skip above.

    A skip guard listing a sentinel string that the source no longer returns
    would let a real failure through as a comparison of two equal sentinels.
    Read from the frozen module's source so the two cannot drift apart silently.
    """
    source = (REPO / "tools" / "rm_facts.py").read_text(encoding="utf-8")
    for sentinel in SENTINELS:
        assert f'"{sentinel}"' in source, (
            f"tools/rm_facts.py no longer returns the sentinel {sentinel!r}, so "
            "the skip guard in this module is checking for a string that cannot "
            "occur - re-read game_build() and data_build() and update SENTINELS"
        )

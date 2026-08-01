"""Cross-file drift anchors - invariants no single-file test can hold.

Both checks here exist because the drift they catch is silent: nothing fails,
nothing looks wrong, and the cost lands sessions later.

1. The game build pin lives in 120 tracked sites (RECOUNTED 2026-08-01; this
   docstring said "~97", which no counting rule reproduces, and three
   independent recounts all returned 120). A bump that updates CLAUDE.md
   and misses a doc leaves a reader citing a build that is no longer installed.
2. The ledger cites commit hashes by its own stated format. A hash written from
   a worktree slice does not survive cherry-pick, so the citation silently
   stops resolving - and is only discovered when someone tries to use it.

Historical records legitimately name superseded values, so they are excluded
rather than allowlisted one value at a time.
"""

import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

# A build pin as V Rising writes it, e.g. 1.1.13.0-r99712.
PIN = re.compile(r"\b\d+\.\d+\.\d+\.\d+-r\d+\b")
CANONICAL_PIN = re.compile(r"Game build pin:\s*`([^`]+)`")

# The stale <root>\v3\ copy documented in docs/OPERATIONS.md and ADR-004. It is
# a real on-disk build that must keep its own pin, not drift onto the current
# one, so it is named here rather than excluded by file.
ALLOWED_PINS = {"1.0.10.4-r91333"}

# Fixture pins, deliberately impossible so they can never be mistaken for a
# real build. V Rising majors are 0 and 1, so an 8 or 9 cannot collide. Matching
# by shape rather than by value keeps tests/ in scope: a fixture asserting
# against the CURRENT build still has to move when the pin moves.
SENTINEL_PIN = re.compile(r"^[89]\.[89]\.[89]\.[89]-r\d+$")

# Records of what was true at the time. A superseded pin here is correct.
HISTORICAL = (
    "docs/history_notes.md",
    "docs/LEDGER.md",
    "docs/BRIDGE_SPIKES.md",
    "WAKEUP_NOTES.md",
    "docs/superpowers/",
)

# Backtick-quoted hex, which is how the ledger cites a commit.
CITED_SHA = re.compile(r"`([0-9a-f]{7,40})`")


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"],
        capture_output=True,
        text=True,
        check=True,
    )
    return out.stdout.splitlines()


def _canonical_pin() -> str:
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    match = CANONICAL_PIN.search(text)
    assert match, "CLAUDE.md no longer states the game build pin"
    return match.group(1)


def test_claude_md_states_a_parseable_build_pin():
    assert PIN.fullmatch(_canonical_pin())


def test_every_authored_build_pin_agrees_with_claude_md():
    """A bump must land on every site in the same commit, not just CLAUDE.md."""
    canonical = _canonical_pin()
    allowed = ALLOWED_PINS | {canonical}
    stragglers: list[str] = []

    for rel in _tracked():
        if any(rel.startswith(h) or rel == h for h in HISTORICAL):
            continue
        if not rel.endswith((".md", ".py", ".cs", ".json", ".ps1")):
            continue
        path = REPO / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for line_no, line in enumerate(text.splitlines(), 1):
            for found in PIN.findall(line):
                if found not in allowed and not SENTINEL_PIN.match(found):
                    stragglers.append(f"{rel}:{line_no} names {found}")

    assert not stragglers, (
        f"build pin is {canonical} but these sites disagree: {stragglers} - "
        "bump every site in one commit, or allowlist a deliberate exception"
    )


def test_every_sha_the_ledger_cites_resolves():
    """A worktree-slice hash does not survive cherry-pick. Catch it at write
    time, while the commit it meant to name is still findable.
    """
    text = (REPO / "docs" / "LEDGER.md").read_text(encoding="utf-8")
    shas = sorted(set(CITED_SHA.findall(text)))
    if not shas:
        pytest.skip("the ledger cites no commit hashes yet")

    dead = []
    for sha in shas:
        probe = subprocess.run(
            ["git", "-C", str(REPO), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        )
        if probe.returncode != 0:
            dead.append(sha)

    assert not dead, (
        f"docs/LEDGER.md cites {dead}, which do not resolve to a commit - "
        "a worktree-slice hash was written instead of the merged one"
    )

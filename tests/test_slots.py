"""Guards on the machine-wide concurrency governor Red Moon shares.

This is the ONE file Red Moon does not own. Three projects on Legion coordinate
THROUGH its on-disk protocol, so a divergence here is not a merge conflict
anyone notices - it is a silent concurrency bug in which two projects believe
they hold different buckets. The digest pin below IS the coordination: all three
trees hashing equal is the acceptance, not a note claiming they do.
"""
import hashlib
import re
from pathlib import Path

from ops import loop

REPO = Path(__file__).resolve().parents[1]
VENDORED = REPO / "ops" / "loop" / "slots.py"

# Agreed with Riot Commander 2026-08-01 and pinned in all three trees.
# Changing this value is a three-repo act, never a unilateral one.
AGREED_SHA256 = "95077a62527c9764e896e3bd1da9027e5efd2b15631feb725fe6138cee5054f9"

# Agreed bucket width for three participants: one slot each. RC's note is
# explicit that an unequal N makes the governor theatre - if RM sets 3 while the
# others set 2, the bucket is 3 wide whenever RM acquires first. There is no
# negotiation protocol; there is one number written in three files.
AGREED_MAX_SLOTS = 3


def test_the_shared_governor_is_byte_identical_to_the_agreed_digest():
    assert VENDORED.is_file(), "the shared governor is missing"
    digest = hashlib.sha256(VENDORED.read_bytes()).hexdigest()
    assert digest == AGREED_SHA256, (
        "ops/loop/slots.py has diverged from the agreed shared file.\n"
        "This file is byte-identical across three repos by contract. Do NOT fix\n"
        "this by updating AGREED_SHA256 - re-sync the file, or coordinate a new\n"
        "digest with the other two projects in the same day."
    )


def test_red_moon_configures_the_agreed_bucket_width():
    assert loop.MAX_CONCURRENT_SLOTS == AGREED_MAX_SLOTS


def test_the_shared_governor_names_no_red_moon_specific_value():
    """It stays project-neutral or it cannot be shared.

    Every project-specific value arrives as an argument. A Red Moon path, port
    or module name appearing in this file means someone localized a file that
    three repos hash for equality.
    """
    text = VENDORED.read_text(encoding="utf-8")
    for needle in ("RedMoon", "RedMoon.Bridge", "Bloodforge", "C:\\RedMoon", "rmdata"):
        assert needle not in text, f"{needle!r} localizes a file that must stay shared"


def test_the_shared_governor_survives_red_moon_authoring_rules():
    """7-bit ASCII and LF, checked here rather than only by the repo-wide guard.

    A vendored file that trips the ASCII gate cannot be committed at all, which
    would make the digest pin unsatisfiable. Worth its own assertion so the
    failure names the cause.
    """
    raw = VENDORED.read_bytes()
    assert not any(b > 127 for b in raw), "non-ascii byte in the shared governor"
    assert b"\r\n" not in raw, "CRLF in the shared governor would change its digest"


def test_the_bucket_root_is_the_shared_one():
    """RM must point at the EXISTING bucket, not stand up a second one.

    A second directory is worse than no governor: both look healthy and neither
    bounds the other. The name is a historical artifact from before this was
    shared and is deliberately NOT renamed - a half-applied rename across three
    repos produces exactly the two-bucket failure this guards.
    """
    from ops.loop import slots

    assert re.search(r"ProgramData", str(slots.DEFAULT_ROOT))
    assert str(slots.DEFAULT_ROOT).endswith("slots")

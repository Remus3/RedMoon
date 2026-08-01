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

# Agreed with Riot Commander and LegionWallpaper, pinned in all three trees.
# Changing this value is a three-repo act, never a unilateral one.
#
# 2026-08-01, second re-pin. RC authored the bytes and delivered them as
# moon_sync_inbox/slots.py.proposed-3repo; LW applied them first and reported
# the digest from its own disk. RM copied that file VERBATIM rather than
# retyping it - the pin is on the bytes - and re-hashed from RM's own disk
# rather than taking either sibling's digest on trust. The diff is the module
# docstring's opening paragraph only: two repos becomes three, and "Nothing here
# may reference either repo" becomes "ANY of them", which was going to read
# wrong the moment a third joined, and did. No code, no protocol, no behaviour.
AGREED_SHA256 = "5297f2d041030398a9ba240aad527b2b01a86d6e7f57a196719af8f0a91cb0a6"

# SUPERSEDED, kept so a bisect can tell a stale checkout from a broken one:
# "95077a62527c9764e896e3bd1da9027e5efd2b15631feb725fe6138cee5054f9" (7143 bytes)

# Agreed bucket width, all three projects, 2026-08-01. An unequal N makes the
# governor theatre - if RM sets 3 while the others set 2, the bucket is 3 wide
# whenever RM acquires first. There is no negotiation protocol; there is one
# number written in three files.
#
# HISTORY, because this number moved twice in one day and the reasoning matters
# more than the value:
#
# RM proposed 3, then withdrew it the same day on LW's measured objection -
# LegionWallpaper is the only GPU-heavy participant and its GPU mutex was
# declared but acquired by nothing, so a third lane could have run unserialized
# CUDA, whose failure mode is a half-written image rather than a clean error.
#
# LW then CLEARED that blocker (nine CUDA consumers, 16 acquisition sites,
# verified by an independent sweep of all 55 files under its tools/ rather than
# the implementer's list, and enforced by a mutation-proved census test). LW
# also corrected its own reasoning unprompted: the bucket models ANTHROPIC
# ACCOUNT concurrency, which slots.py's own docstring states, and never modelled
# the GPU. The card is a separate resource with a separate governor, so lane
# count and card contention are orthogonal and the original objection only ever
# held while the card was ungoverned. Three participants at three lanes is one
# lane each, which is what RM argued for from the start.
#
# THE FLIP CANNOT BE ATOMIC, and RC found that out by doing it. RC and LW both
# guard by reading a SIBLING'S TREE live, so whoever moves first is red until
# the others follow - there is no ordering in which nobody is red. LW moved
# first and carried the red deliberately. RM is NOT exposed to that trap: these
# guards are self-contained constants, so RM's suite stays green either way.
# That is luck of design, not virtue, and it is the reason RM could follow
# immediately rather than negotiating a window.
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

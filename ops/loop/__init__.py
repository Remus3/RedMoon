"""Red Moon's participation in the machine-wide concurrency governor.

THE ONE PLACE RED MOON IS NOT STANDALONE. `CLAUDE.md` opens by declaring that
Red Moon shares no code, data, keys or scheduled-task namespace with any other
project on this machine. This package is the single, deliberate exception,
authorized by the operator on 2026-08-01: `slots.py` is shared CODE, held
byte-identical across three repositories, and the lock directory it writes to is
shared DATA. Everything else in that sentence still holds - no shared keys, no
shared task namespace, no shared ports.

WHY THE EXCEPTION IS WORTH IT. Three projects fanning out headless agents on
Legion are three sets of agents against ONE account, which is one rate-limit
pool. The OS arbitrates CPU adequately and cannot see that pool at all. A
governor is the only thing that can, and a governor only governs if every
participant reads the same protocol from the same directory.

DO NOT EDIT `slots.py`. It is pinned by SHA256 in `tests/test_slots.py` and in
the other two repositories. Re-syncing it is a three-repo act performed in the
same day, never a unilateral edit. Its own docstring still says the file is
shared between TWO repos; that line is stale now that Red Moon has joined, and
correcting it requires a coordinated re-pin rather than a local fix, because the
digest is the contract.

NOTHING IN RED MOON CALLS THIS YET. There is no headless orchestrator to govern
(see `docs/LEDGER.md`). The file is vendored and pinned ahead of that work so
Red Moon joins the bucket as a deliberate act with a verifiable digest, rather
than discovering a divergence on the first real run.
"""
from __future__ import annotations

MAX_CONCURRENT_SLOTS = 2
"""Bucket width, agreed across all three projects on 2026-08-01.

ALL THREE PROJECTS MUST CARRY THE SAME NUMBER or the governor is theatre: if Red
Moon sets 3 while the others set 2, the bucket is 3 wide whenever Red Moon
acquires first. There is no negotiation protocol and there should not be - one
number, agreed out of band, written in three files, and asserted in each.

RED MOON PROPOSED 3 AND WITHDREW IT THE SAME DAY. The reasoning for 3 was that 2
was chosen when two loops existed, one slot each, so three participants at 2
means one project is always blocked - a throttle degenerating into a queue. That
reasoning is sound in general and WRONG FOR THIS MACHINE, for a reason Red Moon
could not see from its own tree:

LegionWallpaper is the only GPU-heavy participant - CUDA upscaling, SDXL
generation, inpainting - all on one card, and as of 2026-08-01 its GPU mutex was
DECLARED BUT ACQUIRED BY NOTHING. Raising the cap would have permitted a second
unserialized CUDA lane. The failure mode is not a longer queue: it is two
processes allocating VRAM mid-upscale, surfacing as a silently degraded or
half-written image rather than a clean error.

So 2 is a MEASURED blocker on a sibling's constraint, not a preference, and it
stays at 2 until LegionWallpaper reports its GPU mutex wired and measured.

WHEN IT IS REOPENED, ASK A BETTER QUESTION THAN N. LegionWallpaper's point,
recorded so it is not lost: the contention that matters on this machine is CUDA,
not lanes, and a lane count is a proxy for a resource it does not model. With a
real GPU mutex the honest answer may be to leave lanes at 2 permanently and let
the mutex govern the card directly.
"""

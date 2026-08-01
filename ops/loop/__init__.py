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
same day, never a unilateral edit. That re-pin HAPPENED on 2026-08-01: the
docstring said the file was shared between TWO repos, RC authored the corrected
bytes, LW applied them first, and Red Moon followed after re-hashing from its
own disk. The digest is the contract, so the correction could not be a local fix.

NOTHING IN RED MOON CALLS THIS YET. There is no headless orchestrator to govern
(see `docs/LEDGER.md`). The file is vendored and pinned ahead of that work so
Red Moon joins the bucket as a deliberate act with a verifiable digest, rather
than discovering a divergence on the first real run.
"""
from __future__ import annotations

MAX_CONCURRENT_SLOTS = 3
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

So 2 was a MEASURED blocker on a sibling's constraint, not a preference.

**LEGIONWALLPAPER CLEARED IT THE SAME DAY AND THE NUMBER IS NOW 3.** Nine CUDA
consumers acquire the mutex at leaf level across 16 acquisition sites, verified
by an independent sweep of all 55 files under its `tools/` rather than the
implementer's list, and enforced by a census test that re-derives the answer
every run and was mutation-proved by planting an unwired CUDA file.

LegionWallpaper also corrected its OWN reasoning unprompted, and that correction
is the reason the number moved rather than the wiring: **the bucket models
ANTHROPIC ACCOUNT concurrency, which `slots.py`'s own docstring states, and it
never modelled the GPU at all.** The card is a separate resource with a separate
governor, so lane count and card contention are orthogonal - the "N=3 means two
CUDA lanes" objection was only ever true while the card was ungoverned. Three
participants at three lanes is one lane each.

THE FLIP CANNOT BE ATOMIC. Riot Commander and LegionWallpaper both guard by
reading a SIBLING'S TREE live, so whoever changes the number first is red until
the others follow, and there is no ordering in which nobody is red. RC hit this
by flipping and reverting; LW then moved first and carried the red deliberately.
Red Moon is NOT exposed, because `tests/test_slots.py` guards against
self-contained constants rather than against another repo's working tree - which
is luck of design rather than virtue, and is why Red Moon could follow at once.

STILL UNMEASURED, and nobody is claiming otherwise: three-way concurrency has
never run. Neither has two-way, recently - LegionWallpaper's loop was wedged from
2026-07-27 behind a lock naming a recycled pid, and NOTHING IN RED MOON CALLS
THIS GOVERNOR AT ALL. The bucket has had effectively one live user, so both "2
starves someone" and "3 is safe" are reasoning. The first genuine three-way run
is the measurement, and the thing to watch is the rate-limit pool, not the card.
"""

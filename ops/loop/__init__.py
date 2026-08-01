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

MAX_CONCURRENT_SLOTS = 3
"""Bucket width, agreed with Riot Commander on 2026-08-01.

ALL THREE PROJECTS MUST CARRY THE SAME NUMBER or the governor is theatre: if Red
Moon sets 3 while the others set 2, the bucket is 3 wide whenever Red Moon
acquires first. There is no negotiation protocol and there should not be - one
number, agreed out of band, written in three files, and asserted in each.

3 preserves the one-slot-each posture that 2 gave the original two participants.
It is REASONING, not measurement: three-way concurrency has never run on this
machine. If the account rate-limits at 3, lower it in all three configs together
and record the measurement.
"""

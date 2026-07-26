---
description: Reconcile every Markdown doc against ground truth and fix drift.
---

Reconcile the documentation with reality.

1. Gather canonical facts by probing, not by reading docs: `git log --oneline -20`,
   `python -m pytest -q` for the real test count, `data/rmdata/current.txt` for
   the data build, the install `VERSION` for the game build, and `core/ports.py`
   for the ports.
2. Read every `.md` in the repository root and `docs/`.
3. Fix every stale number, path and claim against the facts from step 1.
4. Verify each cross-reference link resolves to a file that exists.
5. Flag orphaned or stale documents rather than silently deleting them.
6. Confirm `CLAUDE.md` is still under its 60 KB budget and carries no ledger
   entries.
7. Run `python tools/ascii_guard.py` and `python -m pytest` before committing.

---
description: End-of-session ritual - test, commit, push, sync docs, ledger entry.
---

Wrap this session.

1. Run `python -m pytest` and `python tools/ascii_guard.py`. Report the exact
   counts you observed. Do not proceed on a failure - fix it first.
2. Audit pending changes with `git status --porcelain` and `git diff --stat`.
3. Commit with a descriptive ASCII message and push if a remote exists.
4. Append the per-item completion entry to `docs/LEDGER.md`, newest first.
   Never append it to `CLAUDE.md`, which is size-budgeted and loaded every turn.
5. Update `WAKEUP_NOTES.md` with this session at full fidelity. Move anything
   older than the last two or three sessions to `docs/history_notes.md`.
6. Update `ROADMAP.md` if an item closed.
7. Write the next-session bootstrap into `NEXT_SESSION_PROMPT.md`.
8. Print a short banner: what shipped, the verification that proved it, and what
   is next.

Run independent steps in parallel.

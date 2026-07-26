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
5. Once the branch containing this entry is merged, amend the entry to include
   the resulting merge or commit hash. The hash cannot be known at authoring
   time in step 4 because the commit that will carry it does not exist yet,
   but the ledger's own stated format requires it - do not leave it blank.
6. Update `WAKEUP_NOTES.md` with this session at full fidelity. Move anything
   older than the last two or three sessions to `docs/history_notes.md`.
7. Update `ROADMAP.md` if an item closed.
8. Write the next-session bootstrap into `NEXT_SESSION_PROMPT.md`.
9. Print a short banner: what shipped, the verification that proved it, and what
   is next.
10. Print the ENTIRE next-session prompt inline in the chat, verbatim, in a
    fenced block. Writing it to `NEXT_SESSION_PROMPT.md` in step 8 does not
    satisfy this and neither does summarising it or pointing at the file. The
    next session starts from a cleared context and has only what the operator
    pastes into it, so the prompt must be copy-pasteable straight out of the
    chat. This applies whenever this ritual runs, whether `/done` was invoked
    explicitly or merely inferred from the operator wrapping up.

Run independent steps in parallel.

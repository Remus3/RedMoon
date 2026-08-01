---
name: reference-flashing-consoles-are-mcp-launchers
description: "Flashing consoles on Legion have TWO sources - npx MCP launchers AND Red Moon's own hooks, whose children allocated consoles until fixed 2026-08-01"
metadata: 
  node_type: memory
  type: reference
  originSessionId: d68e2314-d168-47bd-b990-b2e3da42e281
  modified: 2026-08-01T19:41:39.027Z
---

CORRECTED 2026-08-01. The original note concluded the flashing windows were NOT
Red Moon. That was right about the windows it saw and wrong to clear Red Moon,
and its central evidence could not have produced a positive.

**There are TWO sources and they are additive.**

1. **`cmd.exe /d /s /c npx ...` MCP server launchers** from concurrent
   `claude.exe` instances, each spawning its own `conhost.exe`. Still real. The
   remedy stands: prune unused entries under `enabledPlugins` in the USER
   `settings.json`. A sibling project's hooks wrapped in Git bash were captured
   live doing the same thing.
2. **Red Moon's own hooks, until fixed.** `pythonw.exe` is a GUI-subsystem
   image, so a hook launched with it has NO console. That makes the HOOK
   windowless and does NOT make its CHILDREN windowless - a console-subsystem
   child of a console-less parent must `AllocConsole`. `rm_facts.py` (the
   SessionStart hook) spawning `schtasks` was VISIBLE 5 of 5 runs for 2.0 to
   2.3 seconds, taking the foreground. FIXED in commit `379f6c6` with
   `creationflags=CREATE_NO_WINDOW`.

**Why the original probe could not have caught it,** which is the reusable part:
it filtered for `cmd.exe` while RM's children are `schtasks.exe`/`git.exe`; it
polled 120 s against a site that fires once per SessionStart; the git windows
last under one poll interval; and `Win32_Process` has NO console or window field,
so "never appeared in the trace as a console" was an inference from image name
rather than an observation. **A null result from an instrument that cannot
produce a positive is not evidence of absence.**

The same missing flag also silently broke a gate: `ruff` under `pythonw` returned
rc 1 with EMPTY stdout, so the ruff half of the precommit gate passed every
commit. Detail in `docs/LEDGER.md` entry 003r.

Related: [[project-redmoon-ports]], [[feedback-standing-execution-mode]].

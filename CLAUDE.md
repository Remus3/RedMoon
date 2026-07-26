# Red Moon - Agent Context

V Rising coaching and analysis project. Reads live game state from the
RedMoon.Bridge BepInEx plugin, computes combat and progression math in
Bloodforge, and serves a local dashboard. Standalone: Red Moon shares no code,
data, keys or scheduled-task namespace with any other project on this machine.

> **Living docs (read at session start):** `docs/ARCHITECTURE.md` -
> `docs/OPERATIONS.md` - `ROADMAP.md` - `docs/API.md`
> **Deep reference:** `docs/BLOODFORGE.md` (the combat engine)
> **Architectural decisions:** `docs/adr/README.md` - before re-litigating a past
> choice, check here first.

## Topology

| Machine | Role |
|---|---|
| **Legion** | Single PC. Runs V Rising, the RedMoon.Bridge plugin, Bloodforge, and the dashboard. |

The game host is config, not code: `RM_GAME_HOST` (default `127.0.0.1`) is where
every live reader finds the bridge. See `core/ports.py`.

| Service | Port |
|---|---|
| RedMoon.Bridge, client host (live game JSON) | 8777 |
| Dashboard (HTTPS) | 8778 |
| Vision server | 8779 |
| RedMoon.Bridge, dedicated-server host (ADR-005) | 8780 |
| Bloodforge engine | 8783 |

One plugin assembly loads in both hosts (ADR-004) and the port is a pure
function of the detected host, `core.ports.bridge_port_for_host` (ADR-005).
There is no bind-time race and no mandated start order.

## Paths

- Project root: `C:\RedMoon\`
- Python: `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe`
- Game install: `C:\Program Files (x86)\Steam\steamapps\common\VRising`
- Game build pin: `1.1.13.0-r99712`
- API key: `C:\RedMoon\API-Key-Claude.txt` (gitignored)
- Extracted game data: `data/rmdata/<build>/`, current build in
  `data/rmdata/current.txt`
- Health: `ops/runtime/health.json`
- Logs: `logs/YYYY-MM-DD.log`

## Hard rules

- **No em-dashes or en-dashes, ever. 7-bit ASCII in all authored content:**
  code, comments, docstrings, `.md`, commit messages, chat output. Use ` - `
  for a clause break, `-` otherwise. Also avoid smart quotes (U+2018 U+2019
  U+201C U+201D). **Why:** Windows PowerShell 5.1 ANSI-decodes a no-BOM `.ps1`,
  turning a UTF-8 em-dash inside a double-quoted string into a smart quote that
  the tokenizer treats as a string terminator, cascading into a parse failure.
  Enforced by `tools/ascii_guard.py` and the precommit gate.
- **Always `py_compile` before restarting a service.** Syntax errors crash
  silently under `pythonw.exe`.
- **Atomic writes only:** write a temp file in the destination directory, then
  `os.replace` onto the target. Consumers poll mid-write.
- **Never `Stop-Process`.** Use `taskkill /F /PID <pid>`.
- **Never write a port literal.** Import from `core/ports.py`.
- **Commit messages with special characters:** use `git commit -F <tmpfile>`
  (ASCII only) or a single-quoted here-string. Never a double-quoted here-string
  and never a piped string.
- **State assumptions explicitly before coding.**
- **Frozen files** (do not modify without explicit operator approval):
  `core/ports.py`, `core/tables.py`, `tools/ascii_guard.py`,
  `tools/precommit_gate.py`, `tools/text_first_guard.py`,
  `tools/pytest_guard.py`, `tools/rm_facts.py`, `ops/register_tasks.py`.

## Execution Efficiency and Tooling Rules

Default to fast, direct, text-based tools. Scale verification to blast radius.

- **R1** Files are Read / Edit / Write / Grep / Glob only. Never use computer-use
  or Windows-MCP to read or change a file.
- **R2** Runtime state comes from `curl -k https://127.0.0.1:8778/api/...` or
  from reading `ops/runtime/health.json`. Never screenshot to read a number.
- **R3** Visual tools are only for rendered-pixel, CSS and layout checks with no
  text equivalent, plus live-game capture.
- **R4** Prefer built-in tools over shell. When shell is needed, use absolute
  paths and one compound command rather than many round-trips.
- **R5** Classify every change into a tier and run only that tier's verification.
  **Tier 0** cosmetic (doc, comment, string): edit plus `py_compile` if Python.
  **Tier 1** local logic in one module: `py_compile` plus that module's tests.
  **Tier 2** schema, engine, scorer or `ENGINE_VERSION`: the full suite plus a
  service restart.
- **R6** Run the relevant suite once and trust the exit code. Re-run only if you
  edited since, or the tool pipe demonstrably glitched.
- **R7** Use the `verifier` subagent only for parallel-slice or subagent claims,
  or a real stale-pipe event.
- **R8** Never re-read a file you just edited to confirm it. Edit fails loudly.
- **R9** No subagents or worktrees under about three files. Work inline.
- **R10** Batch independent reads and greps into one message.

## Subagent-First Protocol

Use subagents for substantive design, build and research work.

- **Spec first, then act.** A plan subagent emits the spec before any code.
  Verify it against ground truth (grep the cited file and line, read live state,
  check git) before building. Never scaffold on assumptions.
- **Act via subagents:** worktree-isolated build agents on disjoint files, with
  a single merger, and a read-only `verifier` gate before any merge or any
  "done" claim.

## TDD First

All feature work and bug fixes follow TDD: write the failing characterization or
regression test first, then implement, then verify at the tier the change earns
before committing.

## Testing Discipline

Before writing any probe or test, grep the codebase to confirm every method,
field and data shape it will use actually exists, and cite file and line for
each. Never scaffold against an assumed API surface. Prefer assertions on
computed quantities over data-fragile comparisons.

## Verification

Before asserting external state - a key's validity, a process or PID, "X is
dead or missing or broken" - verify it live against the source of truth. Never
rely on a stale doc or another agent's unverified output. Re-probe first, then
assert. Never trust a subagent's claim about test counts, green CI or file
existence without an independent probe.

## Error Handling

Never surface a raw API error string (credit exhaustion, 400, rate limit) in any
user-facing panel. Catch it, render a friendly degraded-mode message such as
"coaching paused, retrying", and log the raw error under `logs/`.

## Python Conventions

When adding a required field to a dataclass, append it at the END with a
default. A mid-class required field breaks every existing positional
construction and its tests.

## Data Fixes

A data-corruption fix is not done until already-corrupted rows are backfilled
and recovered, not just future occurrences prevented. Plan the recovery pass in
the same fix and verify the historical rows are corrected.

## Session workflow

Scoped sessions - each focused task is one session.

- **Start:** `/clear`, then bootstrap from `CLAUDE.md`, `MEMORY.md`, `git log`,
  `WAKEUP_NOTES.md`, `docs/ARCHITECTURE.md` and `ROADMAP.md`.
- **End:** commit, update `WAKEUP_NOTES.md` (keep the last two or three sessions
  at full fidelity, archive older to `docs/history_notes.md`), push.
- `/clear` between roadmap items and between coding and reviewing modes.

## Session-End Ritual

When the operator says "wrap", `/done` or "end session": run the tests, commit
with a descriptive message, push, sync the living docs, append the per-item
entry to `docs/LEDGER.md` (never to `CLAUDE.md`), and confirm the suite is green
before declaring done.

## Output Constraints

Keep individual responses under 500 output tokens. Break long work into multiple
turns, or write verbose output to a file.

## Where to find current state

- Roadmap and open work: `ROADMAP.md`. Aspirational: `BACKLOG.md`.
- Per-item completion ledger: `docs/LEDGER.md` (append-only, newest first).
- Recent session fidelity: `WAKEUP_NOTES.md`.
- Architecture and module map: `docs/ARCHITECTURE.md`.
- Ops commands: `docs/OPERATIONS.md`.
- Deep archive: `docs/history_notes.md`.

## Useful commands

```
python -m pytest
python tools/ascii_guard.py
python tools/rmdata_extract.py
```

## Active priorities

`CLAUDE.md` is size-budgeted under 60 KB and is loaded every turn. Never append
per-item ledger entries here - append them to `docs/LEDGER.md`.

Cycle 1 (harness plus data floor) is DONE. Cycle 2 (RedMoon.Bridge) is the
current work. Cycles 3 through 8 are listed in `ROADMAP.md`.

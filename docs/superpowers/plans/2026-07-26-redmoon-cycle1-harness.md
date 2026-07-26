# Red Moon Cycle 1 (Harness + Data Floor) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up `C:\RedMoon\` as a standalone V Rising project whose Claude Code sessions behave like Riot Commander sessions, plus the offline data floor every later engine cycle depends on.

**Architecture:** A plain Python 3.14 repository. Enforcement lives in four hook scripts under `tools/` wired through `.claude/settings.json`. Doctrine lives in `CLAUDE.md` plus `docs/`. The data floor is a single idempotent extractor that reads the Steam install and writes a versioned, atomically-replaced directory under `data/rmdata/<build>/`. No runtime services, no network, no game modification in this cycle.

**Tech Stack:** Python 3.14.4, pytest 9.0.3, ruff 0.15.12, git. Standard library only - no third-party runtime dependencies.

## Global Constraints

Every task's requirements implicitly include this section.

- **Interpreter:** `C:\Users\Administrator\AppData\Local\Programs\Python\Python314\python.exe` (verified 3.14.4). Hooks invoke `pythonw.exe` from the same directory to avoid console flash.
- **7-bit ASCII only** in every authored file, including JSON, Markdown, Python, and commit messages. No em-dash (U+2014), no en-dash (U+2013), no smart quotes (U+2018 U+2019 U+201C U+201D). Use ` - ` for a clause break.
- **Atomic writes only:** write to a temp path in the destination directory, then `os.replace` onto the target. Never write a consumer-visible file in place.
- **Ports** are exactly `{8777 bridge, 8778 dashboard, 8779 vision, 8783 engine}`. Never 8888, 8889, 8893, or 2999 - those belong to Riot Commander, which runs concurrently on this machine.
- **No Riot Commander imports, paths, data, or `RC-` names.** Red Moon is standalone.
- **Game install root:** `C:\Program Files (x86)\Steam\steamapps\common\VRising`.
- **Build pin:** `1.1.13.0-r99712`, parsed from `VERSION` (`VRising: v1.1.13.0-r99712-b17 (202605251526)`).
- **Repo root:** `C:\RedMoon`. All paths below are relative to it unless absolute.
- **Commit style:** `type(scope): summary`, ASCII, imperative. Commit at the end of every task.
- **Test command:** `python -m pytest` from the repo root.

---

### Task 1: Repository foundation and the ASCII guard

**Files:**
- Create: `.gitattributes`, `.gitignore`, `pytest.ini`, `ruff.toml`
- Create: `tools/ascii_guard.py`
- Test: `tests/test_ascii_guard.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `tools.ascii_guard.scan_text(text: str) -> list[tuple[int, int, str]]` returning `(line_no, col_no, char)` for each codepoint above 127, 1-indexed. `tools.ascii_guard.is_authored(path: pathlib.Path) -> bool`. `tools.ascii_guard.scan_repo(root: pathlib.Path) -> dict[str, list[tuple[int, int, str]]]` keyed by repo-relative POSIX path, containing only files with findings. Task 7 imports all three.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ascii_guard.py`:

```python
from pathlib import Path

from tools.ascii_guard import is_authored, scan_repo, scan_text

REPO = Path(__file__).resolve().parents[1]


def test_scan_text_clean_returns_empty():
    assert scan_text("plain ascii - fine") == []


def test_scan_text_flags_em_dash_with_position():
    findings = scan_text("line one\nbad \u2014 dash")
    assert findings == [(2, 5, "\u2014")]


def test_scan_text_flags_smart_quotes_and_en_dash():
    chars = [f[2] for f in scan_text("\u2018a\u2019 \u201cb\u201d \u2013")]
    assert chars == ["\u2018", "\u2019", "\u201c", "\u201d", "\u2013"]


def test_is_authored_accepts_source_and_docs():
    assert is_authored(Path("tools/ascii_guard.py"))
    assert is_authored(Path("docs/ARCHITECTURE.md"))
    assert is_authored(Path(".claude/settings.json"))


def test_is_authored_rejects_binary_and_excluded_trees():
    assert not is_authored(Path("data/rmdata/1.1.13.0-r99712/strings.json"))
    assert not is_authored(Path("logs/2026-07-26.log"))
    assert not is_authored(Path(".git/COMMIT_EDITMSG"))
    assert not is_authored(Path("assets/icon.png"))


def test_repo_is_ascii_clean():
    findings = scan_repo(REPO)
    assert findings == {}, f"non-ascii in authored files: {findings}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ascii_guard.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'tools'`.

- [ ] **Step 3: Write the supporting config files**

Create `.gitattributes`:

```
* text=auto eol=lf
*.png binary
*.jpg binary
*.ico binary
*.dll binary
*.zip binary
```

Create `.gitignore`:

```
API-Key-Claude.txt
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
_scratch/
logs/
ops/runtime/
data/rmdata/
```

Create `pytest.ini`:

```
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -q
```

Create `ruff.toml`:

```
line-length = 100
target-version = "py314"

[lint]
select = ["E", "F", "W", "I", "UP", "B"]
```

Create empty `tools/__init__.py` and empty `tests/__init__.py` so `tools.ascii_guard` imports from the repo root.

- [ ] **Step 4: Write the implementation**

Create `tools/ascii_guard.py`:

```python
#!/usr/bin/env python3
"""7-bit ASCII guard for authored content (CLAUDE.md hard rule).

Windows PowerShell 5.1 ANSI-decodes a no-BOM .ps1, so a UTF-8 em-dash inside a
double-quoted string becomes a smart quote that terminates the string and
cascades into a parse failure. The rule is also standing operator style.
"""
from __future__ import annotations

import sys
from pathlib import Path

AUTHORED_SUFFIXES = frozenset(
    {".py", ".md", ".json", ".txt", ".ps1", ".bat", ".cmd", ".toml", ".ini", ".cs", ".yml"}
)

EXCLUDED_DIRS = frozenset(
    {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "logs", "_scratch", "assets"}
)

# Generated or third-party trees: correctness is owned by their producer, and
# game data legitimately carries non-ASCII text.
EXCLUDED_PREFIXES = ("data/rmdata/", "ops/runtime/")


def scan_text(text: str) -> list[tuple[int, int, str]]:
    """Return (line_no, col_no, char) for every codepoint above 127, 1-indexed."""
    findings: list[tuple[int, int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for col_no, char in enumerate(line, start=1):
            if ord(char) > 127:
                findings.append((line_no, col_no, char))
    return findings


def is_authored(path: Path) -> bool:
    """True when path is authored content the ASCII rule governs."""
    posix = path.as_posix()
    if any(posix.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False
    return path.suffix.lower() in AUTHORED_SUFFIXES


def scan_repo(root: Path) -> dict[str, list[tuple[int, int, str]]]:
    """Scan every authored file under root. Returns only files with findings."""
    results: dict[str, list[tuple[int, int, str]]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if not is_authored(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings = scan_text(text)
        if findings:
            results[rel.as_posix()] = findings
    return results


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    results = scan_repo(root)
    for rel, findings in results.items():
        for line_no, col_no, char in findings:
            print(f"{rel}:{line_no}:{col_no}: non-ascii U+{ord(char):04X}")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ascii_guard.py -v`
Expected: 6 passed.

- [ ] **Step 6: Verify the CLI entry point works**

Run: `python tools/ascii_guard.py; echo "exit=$?"`
Expected: no output, `exit=0`.

- [ ] **Step 7: Commit**

```bash
git add .gitattributes .gitignore pytest.ini ruff.toml tools tests
git commit -m "feat(tools): ascii guard plus repo config"
```

---

### Task 2: Port registry and the port guard

**Files:**
- Create: `core/__init__.py`, `core/ports.py`
- Test: `tests/test_ports.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `core.ports.BRIDGE`, `core.ports.DASHBOARD`, `core.ports.VISION`, `core.ports.ENGINE` (all `int`), `core.ports.ALL: frozenset[int]`, and `core.ports.GAME_HOST_ENV = "RM_GAME_HOST"`. Every later cycle imports these instead of writing a port literal.

- [ ] **Step 1: Write the failing test**

Create `tests/test_ports.py`:

```python
import re
from pathlib import Path

from core import ports

REPO = Path(__file__).resolve().parents[1]
FORBIDDEN = {8888, 8889, 8893, 2999}


def test_port_values_match_adr_003():
    assert ports.BRIDGE == 8777
    assert ports.DASHBOARD == 8778
    assert ports.VISION == 8779
    assert ports.ENGINE == 8783


def test_all_is_the_complete_disjoint_set():
    assert ports.ALL == frozenset({8777, 8778, 8779, 8783})
    assert ports.ALL.isdisjoint(FORBIDDEN)


def test_game_host_env_name():
    assert ports.GAME_HOST_ENV == "RM_GAME_HOST"


def test_no_riot_commander_port_literal_anywhere_in_source():
    pattern = re.compile(r"\b(8888|8889|8893|2999)\b")
    offenders = []
    for path in sorted(REPO.rglob("*.py")):
        rel = path.relative_to(REPO)
        if any(part in {".git", "__pycache__", "tests"} for part in rel.parts):
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(rel.as_posix())
    assert offenders == [], f"Riot Commander port literals found in {offenders}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_ports.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'core'`.

- [ ] **Step 3: Write the implementation**

Create empty `core/__init__.py`. Create `core/ports.py`:

```python
"""Red Moon port registry (ADR-003).

Deliberately disjoint from the other project running concurrently on this
machine. Import these constants; never write a port literal anywhere else - a
guard test greps the source for foreign port numbers, so naming them here (even
in a comment) would trip it. The full rationale lives in ADR-003.
"""
from __future__ import annotations

BRIDGE = 8777
"""RedMoon.Bridge BepInEx plugin, local live game JSON (cycle 2)."""

DASHBOARD = 8778
"""Dashboard, HTTPS (cycle 4)."""

VISION = 8779
"""Vision server (cycle 8, if it earns its place)."""

ENGINE = 8783
"""Bloodforge combat math server (cycle 3)."""

ALL = frozenset({BRIDGE, DASHBOARD, VISION, ENGINE})

GAME_HOST_ENV = "RM_GAME_HOST"
"""Environment variable naming the host every live reader talks to.

Defaults to 127.0.0.1. The game host is config, not code, so moving the game or
a dedicated server to another box never requires a code change.
"""
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_ports.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add core tests/test_ports.py
git commit -m "feat(core): port registry with disjointness guard"
```

---

### Task 3: Root doctrine documents

**Files:**
- Create: `CLAUDE.md`, `README.md`, `ROADMAP.md`, `BACKLOG.md`, `WAKEUP_NOTES.md`, `NEXT_SESSION_PROMPT.md`
- Test: `tests/test_root_docs.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `CLAUDE.md` containing the literal heading strings the test asserts. Task 4 links to these files from `docs/ARCHITECTURE.md`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_root_docs.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

REQUIRED = [
    "CLAUDE.md",
    "README.md",
    "ROADMAP.md",
    "BACKLOG.md",
    "WAKEUP_NOTES.md",
    "NEXT_SESSION_PROMPT.md",
]

REQUIRED_CLAUDE_SECTIONS = [
    "## Topology",
    "## Paths",
    "## Hard rules",
    "## Session workflow",
    "## Session-End Ritual",
    "## Output Constraints",
    "## Testing Discipline",
    "## Verification",
    "## Error Handling",
    "## Active priorities",
]


def test_every_root_doc_exists_and_is_non_empty():
    for name in REQUIRED:
        path = REPO / name
        assert path.is_file(), f"missing {name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty {name}"


def test_claude_md_has_every_required_section():
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    for heading in REQUIRED_CLAUDE_SECTIONS:
        assert heading in text, f"CLAUDE.md missing section {heading}"


def test_claude_md_stays_under_the_size_budget():
    size = (REPO / "CLAUDE.md").stat().st_size
    assert size < 60_000, f"CLAUDE.md is {size} bytes, budget is 60000"


def test_claude_md_names_the_ledger_as_the_entry_sink():
    text = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    assert "docs/LEDGER.md" in text


def test_no_riot_commander_references_in_root_docs():
    for name in REQUIRED:
        text = (REPO / name).read_text(encoding="utf-8")
        assert "Riot Commander" not in text, f"{name} references Riot Commander"
        assert "C:\\Riot" not in text, f"{name} references the RC path"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_root_docs.py -v`
Expected: FAIL, `missing CLAUDE.md`.

- [ ] **Step 3: Write `CLAUDE.md`**

Create `CLAUDE.md` with exactly these sections and content:

```markdown
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
| RedMoon.Bridge (live game JSON) | 8777 |
| Dashboard (HTTPS) | 8778 |
| Vision server | 8779 |
| Bloodforge engine | 8783 |

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
  `core/ports.py`, `tools/ascii_guard.py`, `tools/precommit_gate.py`,
  `tools/text_first_guard.py`, `tools/pytest_guard.py`.

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

Cycle 1 (harness plus data floor) is the current work. Cycles 2 through 8 are
listed in `ROADMAP.md`.
```

- [ ] **Step 4: Write the remaining root documents**

Create `README.md`:

```markdown
# Red Moon

V Rising coaching and analysis for a single Legion PC.

Red Moon reads live game state from a BepInEx plugin (RedMoon.Bridge), computes
combat, progression, economy and castle math in an engine called Bloodforge, and
serves a local dashboard.

- Game build pin: `1.1.13.0-r99712`
- Ports: bridge 8777, dashboard 8778, vision 8779, engine 8783
- Agent context and doctrine: `CLAUDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/adr/README.md`

## Status

Cycle 1 of 8: process harness plus the offline data floor. No runtime services
yet. See `ROADMAP.md`.

## Quick start

```
python -m pytest
python tools/rmdata_extract.py
```
```

Create `ROADMAP.md`:

```markdown
# Red Moon Roadmap

Each cycle is its own session with its own spec under `docs/superpowers/specs/`.

## Cycle 1 - Harness plus data floor (IN PROGRESS)

Process harness, enforcement hooks, doctrine docs, memory namespace, and the
offline extractor producing `data/rmdata/<build>/`.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`

## Cycle 2 - RedMoon.Bridge

BepInEx plugin serving live game JSON on 8777, plus the runtime
`PrefabCollectionSystem` dump that populates the cycle 1 table schemas with real
item and ability stat data.

## Cycle 3 - Bloodforge core

Combat math against V Blood bosses: weapon, spell school, gear tier, blood type
and quality, jewels, passives and resistances, producing DPS, EHP and
time-to-kill. Server on 8783, `ENGINE_VERSION` pinned to the game build.

## Cycle 4 - Dashboard

HTTPS dashboard on 8778 plus the coach loop.

## Cycle 5 - Progression route planner

V Blood dependency graph and tech and recipe unlocks.

## Cycle 6 - Recipe and refinement economy solver

## Cycle 7 - Castle and base optimizer

## Cycle 8 - Ops hardening

RM-Supervisor, `ops/runtime/health.json`, `RM-*` scheduled tasks, and the vision
tier on 8779 if it earns its place.
```

Create `BACKLOG.md`:

```markdown
# Red Moon Backlog

Aspirational. Nothing here is committed work. Promote an item to `ROADMAP.md`
before building it.

- Offline parser for the DOTS ECS blobs (`ContentArchives`, `EntityScenes`), so
  item stats need no running game. Rejected for cycle 1: per-patch
  reverse-engineering cost against a moving binary format.
- Overlay surface rendered on top of the game.
- Multi-player or dedicated-server support beyond a single local host.
- Screenshot and OCR tier as a bridge fallback.
```

Create `WAKEUP_NOTES.md`:

```markdown
# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-07-26 - Cycle 1 kickoff

Project created at `C:\RedMoon\`. Design spec and implementation plan written
and committed. Ground truth probed: V Rising build
`v1.1.13.0-r99712-b17 (202605251526)`, install at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`, game never launched (no
`AppData\LocalLow\Stunlock Studios`), dedicated server ships with the client.
Ports 8777, 8778, 8779 and 8783 confirmed free; the `RM-*` scheduled-task
namespace confirmed unused.

Key decision: item and ability stat data cannot be extracted offline. It arrives
in cycle 2 from the runtime bridge dump. Cycle 1 ships localization, difficulty
presets, settings schema, and empty typed tables.
```

Create `NEXT_SESSION_PROMPT.md`:

```markdown
# Next Session Prompt

Paste this to start the next Red Moon session.

---

Bootstrap Red Moon: read `CLAUDE.md`, `MEMORY.md`, `ROADMAP.md`,
`WAKEUP_NOTES.md` and `docs/ARCHITECTURE.md`, then `git log --oneline -10`.

Current work: cycle 2, RedMoon.Bridge. Write the spec first
(`docs/superpowers/specs/`), verify every claim against the running game and the
BepInEx surface before scaffolding, then plan, then build.

Do not start coding before the spec is approved.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_root_docs.py -v`
Expected: 5 passed.

- [ ] **Step 6: Verify the ASCII guard still passes over the new documents**

Run: `python tools/ascii_guard.py; echo "exit=$?"`
Expected: no output, `exit=0`.

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md README.md ROADMAP.md BACKLOG.md WAKEUP_NOTES.md NEXT_SESSION_PROMPT.md tests/test_root_docs.py
git commit -m "docs: root doctrine set for Red Moon"
```

---

### Task 4: Living docs and the ADR set

**Files:**
- Create: `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `docs/API.md`, `docs/BLOODFORGE.md`, `docs/LEDGER.md`, `docs/history_notes.md`
- Create: `docs/adr/README.md`, `docs/adr/ADR-001-separation-from-riot-commander.md`, `docs/adr/ADR-002-bepinex-bridge-live-source.md`, `docs/adr/ADR-003-port-map.md`
- Test: `tests/test_docs_and_adr.py`

**Interfaces:**
- Consumes: `core.ports` (ADR-003 must agree with it).
- Produces: an ADR index whose every link resolves. Later cycles append ADRs and rely on the index format `- [ADR-NNN](ADR-NNN-slug.md) - title`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_docs_and_adr.py`:

```python
import re
from pathlib import Path

from core import ports

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
ADR = DOCS / "adr"

REQUIRED_DOCS = [
    "ARCHITECTURE.md",
    "OPERATIONS.md",
    "API.md",
    "BLOODFORGE.md",
    "LEDGER.md",
    "history_notes.md",
]

INDEX_LINE = re.compile(r"^- \[(ADR-\d{3})\]\((ADR-\d{3}-[a-z0-9-]+\.md)\) - .+$")


def test_required_living_docs_exist_and_are_non_empty():
    for name in REQUIRED_DOCS:
        path = DOCS / name
        assert path.is_file(), f"missing docs/{name}"
        assert path.read_text(encoding="utf-8").strip(), f"empty docs/{name}"


def test_adr_index_links_all_resolve():
    index = (ADR / "README.md").read_text(encoding="utf-8")
    linked = [m.group(2) for line in index.splitlines() if (m := INDEX_LINE.match(line))]
    assert linked, "ADR index lists no ADRs"
    for filename in linked:
        assert (ADR / filename).is_file(), f"index links missing {filename}"


def test_every_adr_file_is_listed_in_the_index():
    index = (ADR / "README.md").read_text(encoding="utf-8")
    on_disk = sorted(p.name for p in ADR.glob("ADR-*.md"))
    for filename in on_disk:
        assert filename in index, f"{filename} exists but is not in the index"


def test_adr_003_agrees_with_the_port_registry():
    text = (ADR / "ADR-003-port-map.md").read_text(encoding="utf-8")
    for port in sorted(ports.ALL):
        assert str(port) in text, f"ADR-003 does not document port {port}"


def test_ledger_is_newest_first_and_documents_its_own_rule():
    text = (DOCS / "LEDGER.md").read_text(encoding="utf-8")
    assert "newest first" in text.lower()
    assert "CLAUDE.md" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_docs_and_adr.py -v`
Expected: FAIL, `missing docs/ARCHITECTURE.md`.

- [ ] **Step 3: Write the living docs**

Create `docs/ARCHITECTURE.md`:

```markdown
# Red Moon Architecture

## Shape

Red Moon is a plain Python 3.14 repository on a single machine. Nothing runs as
a service in cycle 1.

```
C:\RedMoon\
  CLAUDE.md            agent doctrine, loaded every turn
  core/ports.py        the only place a port number is written
  tools/               enforcement hooks and the data extractor
  data/schemas/        typed table schemas the bridge will fill
  data/rmdata/<build>/ extracted game data, gitignored, regenerable
  docs/                living docs, ADRs, specs and plans
  tests/               pytest suite
```

## Planned module map

| Module | Cycle | Responsibility |
|---|---|---|
| `core/ports.py` | 1 | Port registry and the game-host env name. |
| `tools/ascii_guard.py` | 1 | 7-bit ASCII enforcement over authored files. |
| `tools/rmdata_extract.py` | 1 | Offline extraction of the Steam install into a versioned data directory. |
| `bridge/` (C#) | 2 | BepInEx plugin. Live game JSON on 8777, plus the prefab and stat dump. |
| `agents/bloodforge/` | 3 | Combat math. DPS, EHP and time-to-kill against V Blood bosses. Server on 8783. |
| `dashboard/` | 4 | HTTPS dashboard on 8778 and the coach loop. |
| `ops/` | 8 | Supervisor, `runtime/health.json`, `RM-*` scheduled tasks. |

## Data flow

Cycle 1 is one direction and offline:

```
Steam install  ->  tools/rmdata_extract.py  ->  data/rmdata/<build>/
                                                data/rmdata/current.txt
```

From cycle 2 the live path is:

```
V Rising process
  -> RedMoon.Bridge (BepInEx, in-process)
  -> http://127.0.0.1:8777/state        live player and world state
  -> http://127.0.0.1:8777/dump/prefabs authoritative item and ability stats
```

The prefab dump writes the cycle 1 table schemas. That is the only way item stat
data enters the repository - it cannot be read offline, because identity and
stats live in binary DOTS ECS blobs, not in the localization file.

## Why the data floor is split

`StreamingAssets\Localization\English.json` maps a localization GUID to display
text. It carries no item identity and no stat line. The join from a PrefabGUID
to its localization key and its stat components exists only in the running
game's entity world. Cycle 1 therefore ships strings, difficulty presets and
settings, and leaves the tables empty but typed.
```

Create `docs/OPERATIONS.md`:

```markdown
# Red Moon Operations

## Verify the repository

```
python -m pytest
python tools/ascii_guard.py
```

Exit code 0 from the guard means every authored file is 7-bit ASCII.

## Refresh extracted game data

```
python tools/rmdata_extract.py
```

Idempotent. Writes `data/rmdata/<build>/` and updates `data/rmdata/current.txt`.
Re-running against an unchanged install produces byte-identical output.

Run it after any Steam update. The build string comes from the install's
`VERSION` file, so a game update lands in a new directory and leaves the old one
intact.

## Scheduled tasks

All Red Moon tasks are named `RM-*`. The namespace is exclusive to this project.

| Task | Trigger | Action |
|---|---|---|
| `RM-DataRefresh` | Daily | Runs `tools/rmdata_extract.py`. No-op unless the build changed. |

Register or remove them:

```
python ops/register_tasks.py --install
python ops/register_tasks.py --remove
```

Inspect them:

```
schtasks /query /tn RM-DataRefresh /v /fo LIST
```

## Process rules

- Never `Stop-Process`. Use `taskkill /F /PID <pid>`.
- Always `py_compile` before restarting a service. Under `pythonw.exe` a syntax
  error is silent.
- Use `pythonw.exe` for background work so no console window flashes.
```

Create `docs/API.md`:

```markdown
# Red Moon API

No HTTP surface exists in cycle 1. This document records the contracts later
cycles must implement, so consumers can be written against a stable shape.

## RedMoon.Bridge, port 8777 (cycle 2)

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"ok": true, "build": "<game build>", "plugin": "<version>"}` |
| GET | `/state` | Live player and world state. Null when no character is loaded. |
| GET | `/dump/prefabs` | Full prefab table: PrefabGUID, localization key, component stats. |

## Bloodforge, port 8783 (cycle 3)

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"ok": true, "engine_version": "...", "build": "..."}` |
| POST | `/rank` | Ranked loadouts for a target V Blood boss. |

## Dashboard, port 8778 (cycle 4)

| Method | Path | Returns |
|---|---|---|
| GET | `/` | Dashboard page, HTTPS. |
| GET | `/api/state` | Merged bridge and engine state for the UI. |
```

Create `docs/BLOODFORGE.md`:

```markdown
# Bloodforge

The Red Moon combat and build engine. Not implemented until cycle 3. This
document is its design contract.

## Purpose

Given a loadout and a target, compute real numbers rather than opinions:

- Damage per second, effective health, and time-to-kill against a specific
  V Blood boss stat line.
- Ranked loadout alternatives and the single highest-value swap.

## Inputs

| Input | Source |
|---|---|
| Weapon type and tier | `data/rmdata/<build>/tables/items.json` (cycle 2) |
| Spell school loadout | `tables/abilities.json` |
| Blood type and quality | `tables/blood_types.json` |
| Gear score, jewels, passives | Live bridge state, port 8777 |
| Boss stat line and resistances | `tables/vbloods.json` |
| Difficulty multipliers | `data/rmdata/<build>/difficulty/` |

## Versioning

`ENGINE_VERSION` is pinned to the game build it was validated against. A game
update forces a data refresh and an explicit revalidation before the version is
bumped. Never bump the version in the same commit as an unvalidated data change.

## Non-goals

- No machine-learned win prediction.
- No opinion-based tier lists. Every ranking traces to a computed quantity.
```

Create `docs/LEDGER.md`:

```markdown
# Red Moon Ledger

Append-only, **newest first**. One entry per completed roadmap item.

Entries belong here and never in `CLAUDE.md`, which is size-budgeted and loaded
into context every turn.

Format:

```
## <item number> - <title> (YYYY-MM-DD)
What shipped, the verification that proved it, and the commit or merge hash.
```

---

(No entries yet. Cycle 1 is in progress.)
```

Create `docs/history_notes.md`:

```markdown
# Red Moon History Notes

Deep archive. Pruned `WAKEUP_NOTES.md` entries and closed context land here so
the working documents stay short.

(No entries yet.)
```

- [ ] **Step 4: Write the ADR set**

Create `docs/adr/README.md`:

```markdown
# Architectural Decision Records

Before re-litigating a past choice, read the relevant record here first.

- [ADR-001](ADR-001-separation-from-riot-commander.md) - Red Moon is a standalone project
- [ADR-002](ADR-002-bepinex-bridge-live-source.md) - A BepInEx plugin is the live game data source
- [ADR-003](ADR-003-port-map.md) - Port map

## Format

One file per decision, named `ADR-NNN-kebab-slug.md`, with sections Context,
Decision, Consequences and Status. Add a line to the list above in the same
commit; a test asserts the index and the directory agree.
```

Create `docs/adr/ADR-001-separation-from-riot-commander.md`:

```markdown
# ADR-001 - Red Moon is a standalone project

**Status:** Accepted, 2026-07-26

## Context

Red Moon reproduces a working method proven on an existing League of Legends
project on the same machine: doctrine in `CLAUDE.md`, enforcement hooks, living
docs, an ADR index, an append-only ledger, a memory namespace, and a
subagent-first build protocol. The obvious shortcut is to share code, tooling or
data between the two.

The two domains have nothing in common at runtime. One reads a vendor-supplied
live API over HTTP; the other must reach into a Unity DOTS entity world through
a mod. Their data models, patch cadences and failure modes are unrelated.

## Decision

Red Moon shares **no** code, data, keys, ports or scheduled-task namespace with
any other project on this machine. What is reproduced is the method, by writing
fresh files, not by importing or symlinking.

Concretely: its own git repository at `C:\RedMoon\`, its own Anthropic key at
`C:\RedMoon\API-Key-Claude.txt`, its own memory namespace, the `RM-` prefix for
scheduled tasks, and the port set in ADR-003.

## Consequences

- Doctrine drift between the projects is expected and acceptable. Each evolves
  against its own domain.
- Improvements do not propagate automatically. Porting one is a deliberate act.
- Neither project can break the other by refactoring shared code, because there
  is none.
- A test asserts no root document mentions the other project by name or path.
```

Create `docs/adr/ADR-002-bepinex-bridge-live-source.md`:

```markdown
# ADR-002 - A BepInEx plugin is the live game data source

**Status:** Accepted, 2026-07-26

## Context

V Rising ships no live-state API. Four options were considered for reading live
game state:

1. A BepInEx plugin serving local JSON from inside the game process.
2. Screen capture with OCR.
3. Parsing the shipped dedicated server's logs and save files.
4. No live read at all, planning offline only.

Item and ability stat data is a related problem with the same answer. Identity
and stats live in binary DOTS ECS blobs (`ContentArchives`, and 1402
`EntityScenes` files). The shipped `Localization\English.json` maps a
localization GUID to display text and carries no stats, so no offline join
exists.

## Decision

A BepInEx plugin, RedMoon.Bridge, is the live source. It serves JSON on
`127.0.0.1:8777` and additionally dumps the prefab collection at runtime, which
is the authoritative and only practical source of item and ability stat data.

Offline ECS blob parsing is rejected: it is a large reverse-engineering effort
against a binary format that moves every patch.

Seeding from third-party community GUID dumps is rejected for the repository:
unlicensed for redistribution and stale each patch. It remains available as a
local, gitignored convenience if ever needed.

## Consequences

- The plugin must be rebuilt against each game update. This is the standing
  maintenance cost of the decision and is accepted.
- Red Moon is scoped to solo and private-host play. The plugin is not for
  official servers.
- Cycle 1 ships empty but typed tables. No engine work can begin before the
  bridge exists.
- Every stat number in Red Moon is first-party, read from the running game, and
  refreshes itself on patch rather than rotting.
```

Create `docs/adr/ADR-003-port-map.md`:

```markdown
# ADR-003 - Port map

**Status:** Accepted, 2026-07-26

## Context

Another project runs continuously on this machine and holds ports 8888, 8889 and
8893, and reads a vendor API on 2999. Red Moon must be able to run at the same
time without contention, and a port collision surfaces as a confusing runtime
failure rather than a clear error.

## Decision

Red Moon owns exactly four ports:

| Service | Port |
|---|---|
| RedMoon.Bridge, live game JSON | 8777 |
| Dashboard, HTTPS | 8778 |
| Vision server | 8779 |
| Bloodforge engine | 8783 |

These are declared once, in `core/ports.py`. No port literal may appear anywhere
else in the source. A test enforces both the values and the absence of the other
project's ports.

All four were confirmed free on this machine on 2026-07-26.

## Consequences

- Both projects run concurrently without contention.
- Changing a port is a one-line change plus an ADR amendment.
- The guard test fails loudly if a literal creeps back in.
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_docs_and_adr.py -v`
Expected: 5 passed.

- [ ] **Step 6: Commit**

```bash
git add docs tests/test_docs_and_adr.py
git commit -m "docs: living docs and ADR 001 through 003"
```

---

### Task 5: The offline data extractor

**Files:**
- Create: `tools/rmdata_extract.py`
- Test: `tests/test_rmdata_extract.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `tools.rmdata_extract.DEFAULT_INSTALL: Path`
  - `tools.rmdata_extract.parse_build_id(version_text: str) -> str` - `"VRising: v1.1.13.0-r99712-b17 (202605251526)"` becomes `"1.1.13.0-r99712"`. Raises `ValueError` on an unparseable string.
  - `tools.rmdata_extract.resolve_codes(text: str, codes: dict[str, str]) -> str` - substitutes localization markup codes, leaving unknown codes untouched.
  - `tools.rmdata_extract.load_localization(loc_path: Path) -> tuple[dict[str, str], dict[str, str]]` returning `(strings_by_guid, codes)`.
  - `tools.rmdata_extract.write_json_atomic(path: Path, payload: object) -> None`
  - `tools.rmdata_extract.extract(install_root: Path, repo_root: Path) -> Path` returning the build directory it wrote.
  - Cycle 2 imports `extract` and `parse_build_id`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_rmdata_extract.py`:

```python
import hashlib
import json
from pathlib import Path

import pytest

from tools.rmdata_extract import (
    DEFAULT_INSTALL,
    extract,
    load_localization,
    parse_build_id,
    resolve_codes,
    write_json_atomic,
)

BUILD = "1.1.13.0-r99712"


def test_parse_build_id_from_the_real_version_string():
    assert parse_build_id("VRising: v1.1.13.0-r99712-b17 (202605251526)") == BUILD


def test_parse_build_id_rejects_garbage():
    with pytest.raises(ValueError):
        parse_build_id("not a version")


def test_resolve_codes_substitutes_known_markup():
    codes = {"</c>": "</color>", "<red1>": "<color=#C52443>"}
    assert resolve_codes("<red1>hot</c>", codes) == "<color=#C52443>hot</color>"


def test_resolve_codes_leaves_unknown_markup_untouched():
    assert resolve_codes("<mystery>x", {"</c>": "</color>"}) == "<mystery>x"


def test_load_localization_returns_strings_and_codes(tmp_path):
    src = tmp_path / "English.json"
    src.write_text(
        json.dumps(
            {
                "Codes": [{"Key": "</c>", "Value": "</color>", "Description": ""}],
                "Nodes": [{"Guid": "abc-123", "Text": "Bear Form</c>"}],
            }
        ),
        encoding="utf-8",
    )
    strings, codes = load_localization(src)
    assert codes == {"</c>": "</color>"}
    assert strings == {"abc-123": "Bear Form</color>"}


def test_write_json_atomic_leaves_no_temp_file(tmp_path):
    target = tmp_path / "out.json"
    write_json_atomic(target, {"a": 1})
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.json"]


def test_write_json_atomic_overwrites_cleanly(tmp_path):
    target = tmp_path / "out.json"
    write_json_atomic(target, {"a": 1})
    write_json_atomic(target, {"b": 2})
    assert json.loads(target.read_text(encoding="utf-8")) == {"b": 2}


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_produces_the_expected_layout(tmp_path):
    build_dir = extract(DEFAULT_INSTALL, tmp_path)
    assert build_dir.name == BUILD
    assert (build_dir / "strings.json").is_file()
    assert (build_dir / "codes.json").is_file()
    assert (build_dir / "meta.json").is_file()
    for name in ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal"):
        assert (build_dir / "difficulty" / f"{name}.json").is_file()
    for name in ("ServerGameSettings", "ServerHostSettings"):
        assert (build_dir / "settings" / f"{name}.json").is_file()
    current = (tmp_path / "data" / "rmdata" / "current.txt").read_text(encoding="utf-8")
    assert current.strip() == BUILD


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_populates_strings(tmp_path):
    build_dir = extract(DEFAULT_INSTALL, tmp_path)
    strings = json.loads((build_dir / "strings.json").read_text(encoding="utf-8"))
    assert len(strings) > 1000
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in strings.items())


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_is_idempotent(tmp_path):
    def digest(root: Path) -> dict[str, str]:
        out = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return out

    first = digest(extract(DEFAULT_INSTALL, tmp_path))
    second = digest(extract(DEFAULT_INSTALL, tmp_path))
    assert first == second
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_rmdata_extract.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'tools.rmdata_extract'`.

- [ ] **Step 3: Write the implementation**

Create `tools/rmdata_extract.py`:

```python
#!/usr/bin/env python3
"""Extract the offline data floor from a V Rising install.

Produces a versioned, regenerable directory under data/rmdata/<build>/. Only
data that genuinely exists offline is written: the localization string table,
the difficulty presets, and the shipped settings files.

Item and ability stat data is deliberately NOT produced here. Identity and stats
live in binary DOTS ECS blobs, and the join from a PrefabGUID to its stats
exists only in the running game's entity world. See ADR-002. The bridge fills
data/schemas/ backed tables at runtime in cycle 2.

Idempotent: re-running against an unchanged install rewrites byte-identical
output. Every consumer-visible file is written atomically.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

DEFAULT_INSTALL = Path(r"C:\Program Files (x86)\Steam\steamapps\common\VRising")

_BUILD_RE = re.compile(r"v(?P<build>\d+\.\d+\.\d+\.\d+-r\d+)")

DIFFICULTY_PRESETS = ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal")
SETTINGS_FILES = ("ServerGameSettings", "ServerHostSettings")


def parse_build_id(version_text: str) -> str:
    """Extract the build pin from the install's VERSION file contents.

    "VRising: v1.1.13.0-r99712-b17 (202605251526)" -> "1.1.13.0-r99712"
    """
    match = _BUILD_RE.search(version_text)
    if not match:
        raise ValueError(f"unparseable VERSION string: {version_text!r}")
    return match.group("build")


def resolve_codes(text: str, codes: dict[str, str]) -> str:
    """Substitute localization markup codes. Unknown codes are left untouched."""
    for key, value in codes.items():
        if key in text:
            text = text.replace(key, value)
    return text


def load_localization(loc_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Read English.json into (strings_by_guid, codes).

    The file is UTF-8 with a BOM, hence utf-8-sig.
    """
    payload = json.loads(loc_path.read_text(encoding="utf-8-sig"))
    codes = {entry["Key"]: entry["Value"] for entry in payload.get("Codes", [])}
    strings = {
        entry["Guid"]: resolve_codes(entry.get("Text", ""), codes)
        for entry in payload.get("Nodes", [])
        if entry.get("Guid")
    }
    return strings, codes


def write_json_atomic(path: Path, payload: object) -> None:
    """Write JSON to path atomically. Consumers may poll mid-write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _copy_json(src: Path, dest: Path) -> None:
    """Re-serialize a shipped JSON file so output is normalized and stable."""
    write_json_atomic(dest, json.loads(src.read_text(encoding="utf-8-sig")))


def extract(install_root: Path, repo_root: Path) -> Path:
    """Extract the data floor. Returns the build directory written."""
    version_text = (install_root / "VERSION").read_text(encoding="utf-8").strip()
    build = parse_build_id(version_text)

    streaming = install_root / "VRising_Data" / "StreamingAssets"
    build_dir = repo_root / "data" / "rmdata" / build
    build_dir.mkdir(parents=True, exist_ok=True)

    strings, codes = load_localization(streaming / "Localization" / "English.json")
    write_json_atomic(build_dir / "strings.json", strings)
    write_json_atomic(build_dir / "codes.json", codes)

    for name in DIFFICULTY_PRESETS:
        _copy_json(
            streaming / "GameDifficultyPresets" / f"{name}.json",
            build_dir / "difficulty" / f"{name}.json",
        )

    for name in SETTINGS_FILES:
        _copy_json(
            streaming / "Settings" / f"{name}.json",
            build_dir / "settings" / f"{name}.json",
        )

    write_json_atomic(
        build_dir / "meta.json",
        {
            "build": build,
            "version_string": version_text,
            "install_root": str(install_root),
            "string_count": len(strings),
            "code_count": len(codes),
            "schema_version": 1,
        },
    )

    pointer = repo_root / "data" / "rmdata" / "current.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    tmp = pointer.with_name(pointer.name + ".tmp")
    tmp.write_text(build + "\n", encoding="utf-8")
    os.replace(tmp, pointer)

    return build_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract the V Rising data floor.")
    parser.add_argument("--install", type=Path, default=DEFAULT_INSTALL)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    if not args.install.is_dir():
        print(f"install not found: {args.install}", file=sys.stderr)
        return 1

    build_dir = extract(args.install, args.repo)
    meta = json.loads((build_dir / "meta.json").read_text(encoding="utf-8"))
    print(f"build {meta['build']}: {meta['string_count']} strings -> {build_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_rmdata_extract.py -v`
Expected: 10 passed. If V Rising is not installed, the 3 integration tests skip and 7 pass.

- [ ] **Step 5: Run the extractor for real and inspect the output**

Run: `python tools/rmdata_extract.py`
Expected: `build 1.1.13.0-r99712: <N> strings -> C:\RedMoon\data\rmdata\1.1.13.0-r99712`, with N over 1000.

Run it a second time and confirm identical output and no `.tmp` files left behind:

```bash
python tools/rmdata_extract.py
ls data/rmdata/1.1.13.0-r99712
find data -name "*.tmp"
```

Expected: the same line, the listed layout, and no `.tmp` results.

- [ ] **Step 6: Confirm the extracted data is gitignored**

Run: `git status --porcelain data/`
Expected: no output. `data/rmdata/` is ignored, because it is regenerable and carries non-ASCII game text.

- [ ] **Step 7: Commit**

```bash
git add tools/rmdata_extract.py tests/test_rmdata_extract.py
git commit -m "feat(tools): offline data floor extractor"
```

---

### Task 6: Typed table schemas the bridge will fill

**Files:**
- Create: `data/schemas/items.schema.json`, `data/schemas/abilities.schema.json`, `data/schemas/vbloods.schema.json`, `data/schemas/blood_types.schema.json`, `data/schemas/recipes.schema.json`
- Create: `core/tables.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `core.tables.SCHEMA_DIR: Path`, `core.tables.TABLE_NAMES: tuple[str, ...]`, `core.tables.load_schema(name: str) -> dict`, `core.tables.empty_table(name: str, build: str) -> dict`, and `core.tables.validate_table(table: dict, schema: dict) -> list[str]` returning human-readable problems (empty list means valid). Cycle 2's bridge dump writes tables that must pass `validate_table`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_schemas.py`:

```python
import json

import pytest

from core.tables import (
    SCHEMA_DIR,
    TABLE_NAMES,
    empty_table,
    load_schema,
    validate_table,
)


def test_every_declared_table_has_a_schema_file():
    for name in TABLE_NAMES:
        assert (SCHEMA_DIR / f"{name}.schema.json").is_file(), f"missing schema for {name}"


def test_no_stray_schema_files():
    on_disk = sorted(p.name.removesuffix(".schema.json") for p in SCHEMA_DIR.glob("*.schema.json"))
    assert on_disk == sorted(TABLE_NAMES)


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_schema_shape(name):
    schema = load_schema(name)
    assert schema["table"] == name
    assert schema["schema_version"] == 1
    assert isinstance(schema["fields"], dict) and schema["fields"]
    assert isinstance(schema["required"], list) and schema["required"]
    for field in schema["required"]:
        assert field in schema["fields"], f"{name}: required field {field} is not declared"
    for field, spec in schema["fields"].items():
        assert spec["type"] in {"string", "number", "integer", "boolean", "array", "object"}
        assert spec["description"].strip(), f"{name}.{field} has no description"


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_empty_table_validates(name):
    table = empty_table(name, "1.1.13.0-r99712")
    assert table["rows"] == []
    assert validate_table(table, load_schema(name)) == []


def test_validate_table_rejects_a_missing_required_field():
    schema = load_schema("items")
    table = empty_table("items", "1.1.13.0-r99712")
    table["rows"] = [{"prefab_guid": 1}]
    problems = validate_table(table, schema)
    assert problems
    assert any("name" in problem for problem in problems)


def test_validate_table_rejects_a_wrong_type():
    schema = load_schema("items")
    table = empty_table("items", "1.1.13.0-r99712")
    row = {field: "x" for field in schema["required"]}
    row["prefab_guid"] = "not an integer"
    table["rows"] = [row]
    problems = validate_table(table, schema)
    assert any("prefab_guid" in problem for problem in problems)


def test_validate_table_rejects_a_bad_envelope():
    schema = load_schema("items")
    problems = validate_table({"rows": []}, schema)
    assert any("build" in problem for problem in problems)


def test_schema_files_are_ascii():
    for path in SCHEMA_DIR.glob("*.schema.json"):
        text = path.read_text(encoding="utf-8")
        assert all(ord(c) <= 127 for c in text), f"{path.name} is not ascii"
        json.loads(text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'core.tables'`.

- [ ] **Step 3: Write the schema files**

Create `data/schemas/items.schema.json`:

```json
{
  "table": "items",
  "schema_version": 1,
  "description": "Equipment and consumables. Filled by the cycle 2 bridge prefab dump.",
  "required": ["prefab_guid", "name", "category", "tier"],
  "fields": {
    "prefab_guid": {"type": "integer", "description": "Stable in-game PrefabGUID hash."},
    "name": {"type": "string", "description": "Resolved English display name."},
    "localization_guid": {"type": "string", "description": "Key into strings.json."},
    "category": {"type": "string", "description": "weapon, chest, legs, gloves, boots, cloak, jewel, consumable, other."},
    "tier": {"type": "integer", "description": "Gear tier, 0 when the item has none."},
    "gear_score": {"type": "number", "description": "Contribution to character gear score."},
    "stats": {"type": "object", "description": "Stat modifier name to numeric value."},
    "weapon_type": {"type": "string", "description": "Weapon family when category is weapon, otherwise empty."}
  }
}
```

Create `data/schemas/abilities.schema.json`:

```json
{
  "table": "abilities",
  "schema_version": 1,
  "description": "Spells and weapon abilities. Filled by the cycle 2 bridge prefab dump.",
  "required": ["prefab_guid", "name", "school"],
  "fields": {
    "prefab_guid": {"type": "integer", "description": "Stable in-game PrefabGUID hash."},
    "name": {"type": "string", "description": "Resolved English display name."},
    "localization_guid": {"type": "string", "description": "Key into strings.json."},
    "school": {"type": "string", "description": "blood, chaos, frost, illusion, storm, unholy, or weapon."},
    "slot": {"type": "string", "description": "primary, travel, or spell."},
    "cooldown": {"type": "number", "description": "Base cooldown in seconds."},
    "power_scaling": {"type": "number", "description": "Coefficient applied to spell or physical power."},
    "damage_type": {"type": "string", "description": "physical, spell, or none."},
    "effects": {"type": "array", "description": "Applied effect identifiers, such as crowd control or damage over time."}
  }
}
```

Create `data/schemas/vbloods.schema.json`:

```json
{
  "table": "vbloods",
  "schema_version": 1,
  "description": "V Blood bosses. Stat lines and unlocks. Filled by the cycle 2 bridge prefab dump.",
  "required": ["prefab_guid", "name", "level"],
  "fields": {
    "prefab_guid": {"type": "integer", "description": "Stable in-game PrefabGUID hash."},
    "name": {"type": "string", "description": "Resolved English display name."},
    "localization_guid": {"type": "string", "description": "Key into strings.json."},
    "level": {"type": "integer", "description": "Boss gear level."},
    "max_health": {"type": "number", "description": "Base health pool before difficulty multipliers."},
    "physical_power": {"type": "number", "description": "Base physical power."},
    "spell_power": {"type": "number", "description": "Base spell power."},
    "resistances": {"type": "object", "description": "Resistance name to numeric value."},
    "blood_type": {"type": "string", "description": "Blood type dropped on defeat."},
    "unlocks": {"type": "array", "description": "PrefabGUIDs of recipes and abilities granted on defeat."},
    "region": {"type": "string", "description": "Map region the boss spawns in."}
  }
}
```

Create `data/schemas/blood_types.schema.json`:

```json
{
  "table": "blood_types",
  "schema_version": 1,
  "description": "Blood types and their quality-scaled bonuses. Filled by the cycle 2 bridge prefab dump.",
  "required": ["prefab_guid", "name"],
  "fields": {
    "prefab_guid": {"type": "integer", "description": "Stable in-game PrefabGUID hash."},
    "name": {"type": "string", "description": "Resolved English display name, such as Warrior or Rogue."},
    "localization_guid": {"type": "string", "description": "Key into strings.json."},
    "bonuses": {"type": "array", "description": "Ordered bonus tiers, each with a quality threshold and scaled stat values."}
  }
}
```

Create `data/schemas/recipes.schema.json`:

```json
{
  "table": "recipes",
  "schema_version": 1,
  "description": "Crafting and refinement recipes. Filled by the cycle 2 bridge prefab dump.",
  "required": ["prefab_guid", "output_guid", "ingredients"],
  "fields": {
    "prefab_guid": {"type": "integer", "description": "Stable in-game PrefabGUID hash of the recipe."},
    "output_guid": {"type": "integer", "description": "PrefabGUID of the produced item."},
    "output_amount": {"type": "integer", "description": "Units produced per craft."},
    "ingredients": {"type": "array", "description": "Objects with prefab_guid and amount."},
    "station_guid": {"type": "integer", "description": "PrefabGUID of the required crafting station."},
    "craft_duration": {"type": "number", "description": "Seconds per craft at base speed."}
  }
}
```

- [ ] **Step 4: Write the implementation**

Create `core/tables.py`:

```python
"""Typed table registry for extracted game data.

Cycle 1 ships schemas and empty tables. The cycle 2 bridge prefab dump fills the
rows, and every write must pass validate_table first. See ADR-002.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"

TABLE_NAMES = ("items", "abilities", "vbloods", "blood_types", "recipes")

_TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def load_schema(name: str) -> dict:
    """Load the schema document for a table."""
    if name not in TABLE_NAMES:
        raise KeyError(f"unknown table {name!r}")
    path = SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def empty_table(name: str, build: str) -> dict:
    """Return a valid, empty table envelope for a build."""
    schema = load_schema(name)
    return {
        "table": name,
        "build": build,
        "schema_version": schema["schema_version"],
        "rows": [],
    }


def validate_table(table: dict, schema: dict) -> list[str]:
    """Return human-readable problems. An empty list means the table is valid."""
    problems: list[str] = []

    for key in ("table", "build", "schema_version", "rows"):
        if key not in table:
            problems.append(f"envelope is missing {key}")
    if problems:
        return problems

    if table["table"] != schema["table"]:
        problems.append(f"table is {table['table']!r}, schema is {schema['table']!r}")
    if table["schema_version"] != schema["schema_version"]:
        problems.append(
            f"schema_version is {table['schema_version']}, "
            f"schema declares {schema['schema_version']}"
        )
    if not isinstance(table["rows"], list):
        problems.append("rows is not a list")
        return problems

    fields = schema["fields"]
    for index, row in enumerate(table["rows"]):
        if not isinstance(row, dict):
            problems.append(f"row {index} is not an object")
            continue
        for field in schema["required"]:
            if field not in row:
                problems.append(f"row {index} is missing required field {field}")
        for field, value in row.items():
            spec = fields.get(field)
            if spec is None:
                problems.append(f"row {index} has undeclared field {field}")
                continue
            expected = _TYPE_MAP[spec["type"]]
            # bool is a subclass of int; never accept it as a number.
            if isinstance(value, bool) and spec["type"] in {"integer", "number"}:
                problems.append(f"row {index} field {field} is a boolean, expected {spec['type']}")
            elif not isinstance(value, expected):
                problems.append(
                    f"row {index} field {field} is {type(value).__name__}, "
                    f"expected {spec['type']}"
                )
    return problems
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_schemas.py -v`
Expected: 16 passed (6 plain tests, plus 2 parametrized tests expanding across the 5 tables).

- [ ] **Step 6: Commit**

```bash
git add data/schemas core/tables.py tests/test_schemas.py
git commit -m "feat(data): typed table schemas and validator"
```

---

### Task 7: Enforcement hooks

**Files:**
- Create: `tools/precommit_gate.py`, `tools/text_first_guard.py`, `tools/pytest_guard.py`, `tools/rm_facts.py`
- Create: `.claude/settings.json`
- Test: `tests/test_hooks.py`

**Interfaces:**
- Consumes: `tools.ascii_guard.scan_text`, `core.ports`.
- Produces: `tools.precommit_gate.staged_files() -> list[str]`, `tools.precommit_gate.check_staged(repo: Path) -> list[str]` returning blocking reasons. `tools.text_first_guard.DENY: frozenset[str]`, `tools.text_first_guard.decide(payload: dict) -> dict | None` returning the PreToolUse deny document or `None` to allow.

Hook contract, verified against a working installation: a PreToolUse hook reads a JSON payload on stdin with a `tool_name` key, and blocks by printing `{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "..."}}` to stdout. It must always exit 0 and must never raise - a crashing guard would block every tool call.

- [ ] **Step 1: Write the failing test**

Create `tests/test_hooks.py`:

```python
import json
import subprocess
import sys
from pathlib import Path

from tools import precommit_gate, text_first_guard

REPO = Path(__file__).resolve().parents[1]
SETTINGS = REPO / ".claude" / "settings.json"


def run_hook(script: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "tools" / script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def test_text_first_guard_denies_a_screen_text_reader():
    decision = text_first_guard.decide({"tool_name": "mcp__Windows-MCP__Scrape"})
    assert decision is not None
    inner = decision["hookSpecificOutput"]
    assert inner["hookEventName"] == "PreToolUse"
    assert inner["permissionDecision"] == "deny"
    assert "8778" in inner["permissionDecisionReason"]


def test_text_first_guard_allows_screenshots_and_ordinary_tools():
    assert text_first_guard.decide({"tool_name": "mcp__computer-use__screenshot"}) is None
    assert text_first_guard.decide({"tool_name": "Read"}) is None
    assert text_first_guard.decide({}) is None


def test_text_first_guard_honours_the_escape_hatch(tmp_path, monkeypatch):
    flag = tmp_path / "allow_visual.flag"
    flag.write_text("", encoding="utf-8")
    monkeypatch.setattr(text_first_guard, "FLAG", flag)
    assert text_first_guard.decide({"tool_name": "mcp__Windows-MCP__Scrape"}) is None


def test_text_first_guard_exits_zero_on_malformed_stdin():
    result = run_hook("text_first_guard.py", {})
    assert result.returncode == 0


def test_precommit_gate_blocks_a_non_ascii_staged_file(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    bad = tmp_path / "note.md"
    bad.write_text("a \u2014 dash\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.md"], cwd=tmp_path, check=True)
    reasons = precommit_gate.check_staged(tmp_path)
    assert reasons
    assert "note.md" in reasons[0]
    assert "U+2014" in reasons[0]


def test_precommit_gate_passes_a_clean_staged_file(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    good = tmp_path / "note.md"
    good.write_text("a - dash\n", encoding="utf-8")
    subprocess.run(["git", "add", "note.md"], cwd=tmp_path, check=True)
    assert precommit_gate.check_staged(tmp_path) == []


def test_settings_json_is_valid_and_wires_every_hook():
    settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    wired = json.dumps(settings["hooks"])
    for script in ("precommit_gate.py", "text_first_guard.py", "pytest_guard.py", "rm_facts.py"):
        assert script in wired, f"{script} is not wired into settings.json"
    assert "C:\\\\RedMoon" in wired or "C:\\RedMoon" in wired


def test_settings_json_references_no_other_project():
    text = SETTINGS.read_text(encoding="utf-8")
    assert "Riot" not in text
    assert all(ord(c) <= 127 for c in text)


def test_rm_facts_runs_and_reports_ports():
    result = run_hook("rm_facts.py", {"hook_event_name": "SessionStart"})
    assert result.returncode == 0
    assert "8777" in result.stdout
    assert "1.1.13.0-r99712" in result.stdout or "not installed" in result.stdout
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_hooks.py -v`
Expected: FAIL, `ImportError: cannot import name 'precommit_gate'`.

- [ ] **Step 3: Write `tools/text_first_guard.py`**

```python
#!/usr/bin/env python3
"""PreToolUse text-first backstop (CLAUDE.md R1 to R3).

Denies the pure screen-text and clipboard readers, which always have a text
alternative: file content goes through Read and Grep, runtime state through the
dashboard API or ops/runtime/health.json.

Scope is deliberately narrow so a sanctioned visual ritual is never wedged.
Pixel screenshots, live game capture, DOM checks, clicks and typing are all
allowed. The escape hatch ops/runtime/allow_visual.flag allows everything.

The guard never raises. A crashing guard must not block tools.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import ports  # noqa: E402

DENY = frozenset(
    {
        "mcp__Windows-MCP__Scrape",
        "mcp__computer-use__read_clipboard",
    }
)

FLAG = Path(__file__).resolve().parents[1] / "ops" / "runtime" / "allow_visual.flag"

REASON = (
    "Text-first (CLAUDE.md R1-R2): do not read text or state off the screen. "
    "File content -> Read or Grep. Runtime state -> "
    f"curl -k https://127.0.0.1:{ports.DASHBOARD}/api/state or Read "
    "ops/runtime/health.json. Override only when no text path exists: create "
    "ops/runtime/allow_visual.flag."
)


def decide(payload: dict) -> dict | None:
    """Return the PreToolUse deny document, or None to allow."""
    if payload.get("tool_name", "") not in DENY:
        return None
    if FLAG.exists():
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    }


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        decision = decide(payload)
        if decision is not None:
            sys.stdout.write(json.dumps(decision))
    except (ValueError, TypeError, OSError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write `tools/precommit_gate.py`**

```python
#!/usr/bin/env python3
"""PreToolUse commit gate.

Blocks a commit whose staged authored files contain non-ASCII codepoints, and
reports net-new ruff findings on staged Python files. See CLAUDE.md hard rules.

Never raises: a crashing gate must not block tooling.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.ascii_guard import is_authored, scan_text  # noqa: E402

REPO = Path(__file__).resolve().parents[1]


def staged_files(repo: Path | None = None) -> list[str]:
    """Repo-relative POSIX paths of files staged for commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
        cwd=str(repo or REPO),
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def check_staged(repo: Path | None = None) -> list[str]:
    """Return blocking reasons. An empty list means the commit may proceed."""
    root = Path(repo or REPO)
    reasons: list[str] = []
    python_files: list[str] = []

    for rel in staged_files(root):
        path = root / rel
        if not path.is_file():
            continue
        if not is_authored(Path(rel)):
            continue
        if path.suffix == ".py":
            python_files.append(rel)
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for line_no, col_no, char in scan_text(text):
            reasons.append(
                f"{rel}:{line_no}:{col_no} non-ascii U+{ord(char):04X} - "
                "authored content must be 7-bit ASCII (CLAUDE.md hard rule)"
            )

    if python_files:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", *python_files],
            cwd=str(root),
            capture_output=True,
            text=True,
        )
        if result.returncode not in (0, 1):
            return reasons
        if result.returncode == 1:
            for line in result.stdout.splitlines():
                if line.strip() and not line.startswith("Found "):
                    reasons.append(f"ruff: {line.strip()}")

    return reasons


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        command = str(payload.get("tool_input", {}).get("command", ""))
        if "git commit" not in command:
            return 0
        reasons = check_staged()
        if reasons:
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Commit blocked:\n" + "\n".join(reasons[:20]),
                }
            }
            sys.stdout.write(json.dumps(out))
    except (ValueError, TypeError, OSError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Write `tools/pytest_guard.py`**

```python
#!/usr/bin/env python3
"""PostToolUse edit guard.

py_compile only by default, because a syntax error crashes silently under
pythonw.exe. Set RM_FULL_SUITE=1 to run the whole suite after every edit during
a tier 2 batch (CLAUDE.md R5).

Never raises and never blocks. It reports to stdout only.
"""
from __future__ import annotations

import json
import os
import py_compile
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        path_text = str(payload.get("tool_input", {}).get("file_path", ""))
        if path_text.endswith(".py") and Path(path_text).is_file():
            try:
                py_compile.compile(path_text, doraise=True)
            except py_compile.PyCompileError as exc:
                sys.stdout.write(f"py_compile FAILED: {exc}\n")
                return 0

        if os.environ.get("RM_FULL_SUITE") == "1":
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=str(REPO),
                capture_output=True,
                text=True,
            )
            sys.stdout.write(result.stdout[-2000:])
    except (ValueError, TypeError, OSError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6: Write `tools/rm_facts.py`**

```python
#!/usr/bin/env python3
"""SessionStart facts probe.

Prints live Red Moon state so a session bootstraps from ground truth rather than
from a stale document: game install and build, extracted data build, port
occupancy, and RM-* scheduled tasks.

Never raises. A failing probe must not break session start.
"""
from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

# A hook is launched by absolute path, so sys.path[0] is tools/, not the repo
# root. Bootstrap the root before importing anything from core or tools.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import ports  # noqa: E402
from tools.rmdata_extract import DEFAULT_INSTALL, parse_build_id  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

PORT_LABELS = {
    ports.BRIDGE: "bridge",
    ports.DASHBOARD: "dashboard",
    ports.VISION: "vision",
    ports.ENGINE: "engine",
}


def port_busy(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.2)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def game_build() -> str:
    version = DEFAULT_INSTALL / "VERSION"
    if not version.is_file():
        return "not installed"
    try:
        return parse_build_id(version.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return "unparseable"


def data_build() -> str:
    pointer = REPO / "data" / "rmdata" / "current.txt"
    if not pointer.is_file():
        return "none extracted"
    return pointer.read_text(encoding="utf-8").strip()


def scheduled_tasks() -> list[str]:
    result = subprocess.run(
        ["schtasks", "/query", "/fo", "csv", "/nh"],
        capture_output=True,
        text=True,
    )
    names = []
    for line in result.stdout.splitlines():
        name = line.split(",")[0].strip('"').lstrip("\\")
        if name.startswith("RM-") and name not in names:
            names.append(name)
    return names


def main() -> int:
    try:
        lines = ["# Red Moon live state (rm_facts.py)", ""]
        lines.append(f"- Game build: {game_build()}")
        lines.append(f"- Extracted data build: {data_build()}")
        states = ", ".join(
            f"{label} {port} {'BUSY' if port_busy(port) else 'free'}"
            for port, label in sorted(PORT_LABELS.items())
        )
        lines.append(f"- Ports: {states}")
        tasks = scheduled_tasks()
        lines.append(f"- RM-* scheduled tasks: {', '.join(tasks) if tasks else 'none'}")
        sys.stdout.write("\n".join(lines) + "\n")
    except (OSError, ValueError):
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 7: Write `.claude/settings.json`**

Note the doubled backslashes: this is JSON. `pythonw.exe` avoids a console flash.

```json
{
  "env": {
    "PYTHONUTF8": "1",
    "PYTHONIOENCODING": "utf-8",
    "PYTHONPATH": "C:\\RedMoon"
  },
  "permissions": {
    "allow": [
      "Bash(taskkill:*)",
      "Bash(schtasks:*)"
    ],
    "deny": []
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit:*)",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\\\Users\\\\Administrator\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python314\\\\pythonw.exe\" \"C:\\\\RedMoon\\\\tools\\\\precommit_gate.py\"",
            "timeout": 60
          }
        ]
      },
      {
        "matcher": "mcp__Windows-MCP__Scrape|mcp__computer-use__read_clipboard",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\\\Users\\\\Administrator\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python314\\\\pythonw.exe\" \"C:\\\\RedMoon\\\\tools\\\\text_first_guard.py\"",
            "timeout": 10
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\\\Users\\\\Administrator\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python314\\\\pythonw.exe\" \"C:\\\\RedMoon\\\\tools\\\\pytest_guard.py\"",
            "timeout": 60
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"C:\\\\Users\\\\Administrator\\\\AppData\\\\Local\\\\Programs\\\\Python\\\\Python314\\\\pythonw.exe\" \"C:\\\\RedMoon\\\\tools\\\\rm_facts.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 8: Run the tests to verify they pass**

Run: `python -m pytest tests/test_hooks.py -v`
Expected: 9 passed.

- [ ] **Step 9: Prove the gate blocks a real em-dash commit**

```bash
printf 'a \xe2\x80\x94 dash\n' > _scratch_probe.md
git add _scratch_probe.md
python -c "from tools.precommit_gate import check_staged; import sys; r=check_staged(); print('\n'.join(r)); sys.exit(1 if r else 0)"
```

Expected: a line naming `_scratch_probe.md` and `U+2014`, exit code 1. Then clean up:

```bash
git restore --staged _scratch_probe.md
rm _scratch_probe.md
```

- [ ] **Step 10: Commit**

```bash
git add tools/precommit_gate.py tools/text_first_guard.py tools/pytest_guard.py tools/rm_facts.py .claude/settings.json tests/test_hooks.py
git commit -m "feat(hooks): ascii commit gate, text-first guard, edit guard, facts probe"
```

---

### Task 8: Subagent, slash commands, and the memory namespace

**Files:**
- Create: `.claude/agents/verifier.md`
- Create: `.claude/commands/done.md`, `.claude/commands/root-cause-fix.md`, `.claude/commands/sync-docs.md`
- Create: `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\MEMORY.md` and four memory entries
- Test: `tests/test_claude_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: the `verifier` agent name, referenced by `CLAUDE.md` R7.

- [ ] **Step 1: Write the failing test**

Create `tests/test_claude_config.py`:

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLAUDE_DIR = REPO / ".claude"
MEMORY = Path(r"C:\Users\Administrator\.claude\projects\C--RedMoon\memory")

REQUIRED_COMMANDS = ["done.md", "root-cause-fix.md", "sync-docs.md"]


def test_verifier_agent_exists_with_frontmatter():
    text = (CLAUDE_DIR / "agents" / "verifier.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: verifier" in text
    assert "description:" in text


def test_every_required_command_exists_and_is_non_empty():
    for name in REQUIRED_COMMANDS:
        path = CLAUDE_DIR / "commands" / name
        assert path.is_file(), f"missing command {name}"
        assert path.read_text(encoding="utf-8").strip()


def test_commands_reference_the_ledger_not_claude_md():
    text = (CLAUDE_DIR / "commands" / "done.md").read_text(encoding="utf-8")
    assert "docs/LEDGER.md" in text


def test_claude_dir_is_ascii():
    for path in CLAUDE_DIR.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8")
            assert all(ord(c) <= 127 for c in text), f"{path} is not ascii"


def test_memory_namespace_is_seeded():
    index = MEMORY / "MEMORY.md"
    assert index.is_file(), "memory index not seeded"
    text = index.read_text(encoding="utf-8")
    for entry in ("project_redmoon_ports", "project_vrising_build_pin", "user_operator_profile"):
        assert entry in text, f"{entry} not listed in MEMORY.md"
        assert (MEMORY / f"{entry}.md").is_file(), f"{entry}.md missing"


def test_memory_entries_have_frontmatter():
    for path in MEMORY.glob("*.md"):
        if path.name == "MEMORY.md":
            continue
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---"), f"{path.name} has no frontmatter"
        assert "name:" in text and "description:" in text and "type:" in text
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_claude_config.py -v`
Expected: FAIL, `FileNotFoundError` for the verifier agent.

- [ ] **Step 3: Write the verifier subagent**

Create `.claude/agents/verifier.md`:

```markdown
---
name: verifier
description: Ground-truth verification subagent. Independently re-runs the test suite from a clean state, confirms cited files exist on disk, and cross-checks an implementing agent's claims against what actually happened. Use before trusting any "green" or "shipped" claim. Read-only.
tools: Bash, Read, Grep, Glob
---

You verify claims. You never edit.

Given a claim - "the suite is green", "the file exists", "the extractor is
idempotent" - do this:

1. Re-run the relevant command yourself, fresh, from the repository root. Never
   carry forward a count another agent reported.
2. Confirm every cited file actually exists on disk. List it.
3. Report the exact numbers you observed this run, and the exact command that
   produced them.
4. State a verdict: CONFIRMED or REFUTED, with the evidence inline.

If the claim is partly true, say which part failed. Never round a partial pass
up to a pass. An unverifiable claim is REFUTED, not CONFIRMED.
```

- [ ] **Step 4: Write the slash commands**

Create `.claude/commands/done.md`:

```markdown
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
```

Create `.claude/commands/root-cause-fix.md`:

```markdown
---
description: Root-cause-first TDD loop for a bug or data fix.
---

Fix the reported problem at its root, not at its symptom.

1. Write a failing reproduction test FIRST, before touching any production code.
   Run it and paste the failure.
2. Find the root cause. State it in one sentence.
3. Grep for every sibling case sharing that same root cause - other callers,
   other modes, duplicate code paths. Cite file and line for each. A narrow
   first fix that misses siblings is the normal failure mode here.
4. Add a test covering each sibling.
5. Write the minimal fix.
6. Run the tier-appropriate suite and report the exact counts.
7. Check for already-corrupted data. A fix that only prevents future occurrences
   leaves existing bad rows wrong. Plan and run the backfill in this same
   change, and verify the historical rows are corrected.
```

Create `.claude/commands/sync-docs.md`:

```markdown
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
```

- [ ] **Step 5: Seed the memory namespace**

Create `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\MEMORY.md`:

```markdown
# Memory index

One line per entry. Topic files hold the detail; this is the map.

## Orientation
- [Operator profile](user_operator_profile.md) - solo developer, terse and direct
- [V Rising build pin](project_vrising_build_pin.md) - 1.1.13.0-r99712, install path

## Project facts
- [Port map](project_redmoon_ports.md) - 8777 bridge, 8778 dashboard, 8779 vision, 8783 engine
- [Stats need the bridge](project_stats_require_bridge.md) - no offline item stat data exists
```

Create `project_redmoon_ports.md`:

```markdown
---
name: project_redmoon_ports
description: Red Moon owns ports 8777, 8778, 8779 and 8783, deliberately disjoint from the other project on this machine.
metadata:
  type: project
---

Red Moon ports: 8777 RedMoon.Bridge, 8778 dashboard, 8779 vision, 8783
Bloodforge. Declared once in `core/ports.py`; a test fails on any port literal
elsewhere in the source.

**Why:** another project runs continuously on this machine holding 8888, 8889
and 8893. Both must run concurrently without contention.

**How to apply:** import from `core.ports`. Never write a port number inline.
See ADR-003 and [[project_vrising_build_pin]].
```

Create `project_vrising_build_pin.md`:

```markdown
---
name: project_vrising_build_pin
description: V Rising build 1.1.13.0-r99712 at the Steam default path is the data pin for Red Moon.
metadata:
  type: project
---

Game build `1.1.13.0-r99712`, parsed from `VERSION`
(`VRising: v1.1.13.0-r99712-b17 (202605251526)`), installed at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`. The client install also
ships the dedicated server.

**Why:** extracted data is written per build, so a Steam update lands in a new
directory instead of corrupting the old one.

**How to apply:** after any game update run `python tools/rmdata_extract.py` and
re-validate before bumping any engine version. See
[[project_stats_require_bridge]].
```

Create `project_stats_require_bridge.md`:

```markdown
---
name: project_stats_require_bridge
description: V Rising item and ability stats cannot be extracted offline; only the runtime bridge dump provides them.
metadata:
  type: project
---

`StreamingAssets\Localization\English.json` maps a localization GUID to display
text and carries no item identity and no stat line. Identity and stats live in
binary DOTS ECS blobs (`ContentArchives`, 1402 `EntityScenes` files). No offline
join exists.

**Why:** this was measured on 2026-07-26, not assumed. It is why the cycle 1
tables ship empty but typed.

**How to apply:** do not re-pitch an offline extractor for item stats, and do
not seed the repository from third-party GUID dumps. The authoritative source is
the cycle 2 RedMoon.Bridge runtime prefab dump. See ADR-002 and
[[project_redmoon_ports]].
```

Create `user_operator_profile.md`:

```markdown
---
name: user_operator_profile
description: Solo developer on a single Windows machine; wants terse, honest, evidence-backed answers.
metadata:
  type: user
---

Solo developer working on one Windows machine (Legion). Runs several independent
projects side by side and expects them not to interfere.

**Why:** the operator reads output quickly and values a verified number over a
confident sentence.

**How to apply:** be terse. Lead with the finding. Probe live state before
asserting it. Never claim green without showing the count you observed this run.
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `python -m pytest tests/test_claude_config.py -v`
Expected: 6 passed.

- [ ] **Step 7: Commit**

```bash
git add .claude tests/test_claude_config.py
git commit -m "feat(claude): verifier subagent, slash commands, memory seed"
```

Note: the memory files live outside the repository and are not committed. That is
correct - the memory namespace is per-machine state, not project source.

---

### Task 9: Scheduled task registration and the full-suite gate

**Files:**
- Create: `ops/__init__.py`, `ops/register_tasks.py`
- Test: `tests/test_register_tasks.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `ops.register_tasks.TASKS: dict[str, dict]`, `ops.register_tasks.build_create_command(name: str) -> list[str]`, `ops.register_tasks.build_delete_command(name: str) -> list[str]`. Cycle 8 adds supervisor tasks to `TASKS`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_register_tasks.py`:

```python
from ops.register_tasks import TASKS, build_create_command, build_delete_command


def test_data_refresh_task_is_declared():
    assert "RM-DataRefresh" in TASKS
    spec = TASKS["RM-DataRefresh"]
    assert spec["schedule"] == "DAILY"
    assert "rmdata_extract.py" in spec["script"]


def test_every_task_name_uses_the_rm_prefix():
    for name in TASKS:
        assert name.startswith("RM-"), f"{name} does not use the RM- prefix"


def test_create_command_is_well_formed():
    argv = build_create_command("RM-DataRefresh")
    assert argv[0] == "schtasks"
    assert "/create" in argv
    assert "/tn" in argv and "RM-DataRefresh" in argv
    assert "/sc" in argv and "DAILY" in argv
    joined = " ".join(argv)
    assert "pythonw.exe" in joined
    assert "rmdata_extract.py" in joined


def test_delete_command_is_forced_and_targeted():
    argv = build_delete_command("RM-DataRefresh")
    assert argv[:2] == ["schtasks", "/delete"]
    assert "RM-DataRefresh" in argv
    assert "/f" in argv


def test_unknown_task_raises():
    import pytest

    with pytest.raises(KeyError):
        build_create_command("RM-DoesNotExist")
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_register_tasks.py -v`
Expected: FAIL, `ModuleNotFoundError: No module named 'ops'`.

- [ ] **Step 3: Write the implementation**

Create empty `ops/__init__.py`. Create `ops/register_tasks.py`:

```python
#!/usr/bin/env python3
"""Register and remove Red Moon scheduled tasks.

All task names use the RM- prefix. That namespace is exclusive to this project;
never create or remove a task under any other prefix from here.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PYTHONW = Path(
    r"C:\Users\Administrator\AppData\Local\Programs\Python\Python314\pythonw.exe"
)

TASKS: dict[str, dict] = {
    "RM-DataRefresh": {
        "script": str(REPO / "tools" / "rmdata_extract.py"),
        "schedule": "DAILY",
        "start_time": "05:30",
        "description": "Re-extract the V Rising data floor. No-op unless the build changed.",
    },
}


def build_create_command(name: str) -> list[str]:
    """schtasks argv that creates the named task."""
    spec = TASKS[name]
    action = f'"{PYTHONW}" "{spec["script"]}"'
    return [
        "schtasks",
        "/create",
        "/tn",
        name,
        "/tr",
        action,
        "/sc",
        spec["schedule"],
        "/st",
        spec["start_time"],
        "/rl",
        "HIGHEST",
        "/f",
    ]


def build_delete_command(name: str) -> list[str]:
    """schtasks argv that removes the named task."""
    if name not in TASKS:
        raise KeyError(f"unknown task {name!r}")
    return ["schtasks", "/delete", "/tn", name, "/f"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage RM-* scheduled tasks.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true")
    group.add_argument("--remove", action="store_true")
    group.add_argument("--show", action="store_true")
    args = parser.parse_args()

    for name in TASKS:
        if args.show:
            print(f"{name}: {' '.join(build_create_command(name))}")
            continue
        argv = build_create_command(name) if args.install else build_delete_command(name)
        result = subprocess.run(argv, capture_output=True, text=True)
        print(f"{name}: exit {result.returncode} {result.stdout.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_register_tasks.py -v`
Expected: 5 passed.

- [ ] **Step 5: Preview the task command without touching the system**

Run: `python ops/register_tasks.py --show`
Expected: one line naming `RM-DataRefresh` with the full `schtasks /create` argv. Do not install it in this task; installation is an operator decision.

- [ ] **Step 6: Run the whole suite and the guard**

```bash
python -m pytest
python tools/ascii_guard.py
```

Expected: all tests pass, guard exits 0. Record the exact test count - it goes in the ledger entry.

- [ ] **Step 7: Write the cycle 1 ledger entry**

Append to `docs/LEDGER.md`, directly under the `---`, replacing the placeholder line:

```markdown
## 001 - Cycle 1: harness plus data floor (2026-07-26)

Shipped the Red Moon process harness and the offline data floor. ASCII guard,
port registry, doctrine documents, living docs, ADR-001 through ADR-003, the
data extractor, typed table schemas, four enforcement hooks, the verifier
subagent, three slash commands, the memory namespace seed, and RM-DataRefresh
registration.

Verified: `python -m pytest` reports <N> passed; `python tools/ascii_guard.py`
exits 0; `python tools/rmdata_extract.py` is idempotent and writes
`data/rmdata/1.1.13.0-r99712/`; the commit gate blocks a staged em-dash.

Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`
Plan: `docs/superpowers/plans/2026-07-26-redmoon-cycle1-harness.md`
```

Replace `<N>` with the count observed in step 6. Do not carry a count forward
from anywhere else.

- [ ] **Step 8: Commit**

```bash
git add ops tests/test_register_tasks.py docs/LEDGER.md
git commit -m "feat(ops): RM-DataRefresh task registration and cycle 1 ledger entry"
```

---

## Cycle 1 acceptance

Run these from `C:\RedMoon`. All six correspond to the spec's success criteria.

1. `git log --oneline` shows the spec, the plan, and nine task commits.
2. `python -m pytest` passes.
3. `python tools/ascii_guard.py` exits 0.
4. `python tools/rmdata_extract.py` twice produces byte-identical output and
   `data/rmdata/current.txt` reads `1.1.13.0-r99712`.
5. Staging a file containing an em-dash makes `check_staged()` return a
   blocking reason naming `U+2014`.
6. Opening a Claude Code session at `C:\RedMoon` loads `CLAUDE.md`, prints the
   `rm_facts` banner, and shows no content from any other project.

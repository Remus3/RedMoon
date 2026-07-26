# Red Moon - Harness + Data Floor (Cycle 1) Design

Date: 2026-07-26
Status: APPROVED (operator, 2026-07-26)
Scope: cycle 1 of an 8-cycle program. Cycles 2-8 get their own specs.

## 1. Purpose

Stand up `C:\RedMoon\` as a standalone V Rising coaching/analysis project that
reproduces the Riot Commander (RC) working method - the rules, rituals, docs
layout, enforcement hooks, memory namespace and subagent protocol - so that a
Claude Code session opened at `C:\RedMoon\` behaves the way an RC session
behaves, applied to V Rising instead of League of Legends.

Red Moon shares no code, no data, no keys and no scheduled-task namespace with
RC. RC is referenced only as a design ancestor in ADR-001.

## 2. Ground truth probed 2026-07-26

- `C:\RedMoon\` existed, empty, not a git repository.
- V Rising installed at
  `C:\Program Files (x86)\Steam\steamapps\common\VRising`.
- Build string, from `VERSION`: `VRising: v1.1.13.0-r99712-b17 (202605251526)`.
- Game had never been launched: no
  `C:\Users\Administrator\AppData\LocalLow\Stunlock Studios`.
- The client install ships the dedicated server at `VRising_Server\VRisingServer.exe`.
- `VRising_Data\StreamingAssets\Localization\English.json` is 1125933 bytes and
  has shape `{"Codes": [{Key, Value, Description}], "Nodes": [{Guid, Text}]}`.
  It carries localization GUID to display text only. It does NOT carry item
  identity or any stat line.
- `VRising_Data\StreamingAssets\GameDifficultyPresets\` holds
  `Difficulty_Easy.json`, `Difficulty_Normal.json`, `Difficulty_Brutal.json`.
- `VRising_Data\StreamingAssets\Settings\` holds `ServerGameSettings.json`,
  `ServerHostSettings.json`, `ClientSettings.json`, `InputSettings.json`,
  `ServerListPrioritySettings.json`.
- Item and ability stat data lives in DOTS ECS blobs: `StreamingAssets\ContentArchives\`
  and 1402 files under `StreamingAssets\EntityScenes\` (`*.entities` +
  `*.entityheader`). Binary, patch-versioned.

## 3. Naming and topology

| Concept | RC | Red Moon |
|---|---|---|
| Umbrella project | Riot Commander | Red Moon (RM), `C:\RedMoon\` |
| Combat/build engine | Daemon Slayer (DS) | Bloodforge (BF), `agents/bloodforge/` |
| Live game read | Riot Live Client API | RedMoon.Bridge (BepInEx plugin) |

Ports, chosen disjoint from RC so both projects can run on Legion at once:

| Service | RC port | Red Moon port |
|---|---|---|
| Dashboard (HTTPS) | 8888 | 8778 |
| Vision server | 8889 | 8779 |
| Engine server | 8893 | 8783 |
| Live game read | 2999 | 8777 |

Single machine (Legion), 1-PC from day one. The game host is config not code:
`RM_GAME_HOST` defaults to `127.0.0.1`, mirroring RC's `core/game_host.py`, so a
future dedicated server on another box is a config change.

## 4. Cycle 1 deliverables

### 4a. Process harness

Root documents:

- `CLAUDE.md` - hard rules: 7-bit ASCII only (no em-dash, no en-dash, no smart
  quotes), atomic writes only, `py_compile` before restart, never `Stop-Process`
  (use `taskkill /F /PID`), restart via `restart_trigger.txt`, frozen-file list,
  tiered verification R1-R11, TDD-first, subagent-first protocol, session
  workflow, `/done` ritual, 500-token output cap.
- `ROADMAP.md`, `BACKLOG.md`, `WAKEUP_NOTES.md`, `README.md`,
  `NEXT_SESSION_PROMPT.md`.

`docs/`:

- `ARCHITECTURE.md`, `OPERATIONS.md`, `API.md`
- `BLOODFORGE.md` (the `DAEMON_SLAYER.md` analog)
- `LEDGER.md` - append-only, newest-first, per-item completion entries. Never
  appended to `CLAUDE.md`.
- `history_notes.md` - deep archive.
- `adr/README.md` plus ADR-001 (separation from RC), ADR-002 (BepInEx bridge as
  the live source, with the patch-rebuild cost and solo/private-only
  constraint), ADR-003 (port map).

`.claude/`:

- `settings.json` wiring three enforcement hooks and a SessionStart hook.
  - PreToolUse `tools/precommit_gate.py` on `git commit` and PowerShell: blocks
    banned glyphs and net-new ruff findings on staged lines.
  - PostToolUse `tools/pytest_guard.py`: `py_compile` only by default;
    `RM_FULL_SUITE=1` restores the full suite for a tier-2 batch.
  - PreToolUse `tools/text_first_guard.py`: denies pure screen-text readers and
    points at the text path. Escape hatch `ops/runtime/allow_visual.flag`.
  - SessionStart `tools/rm_facts.py`: probes bridge `:8777`, Bloodforge `:8783`,
    dashboard `:8778`, and `RM-*` scheduled tasks, and prints the caveman output
    dialect banner.
- `agents/verifier.md` - read-only ground-truth verification subagent.
- `commands/` - ports of `/done`, `/root-cause-fix`, `/sync-all-md`,
  `/weekly-hygiene`, `/ship-batch`, `/game-monitor`.

`tools/`: the four scripts above plus `strip_em_dashes.py`.

Memory: seed `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\`
with `MEMORY.md` and starter entries (operator profile, V Rising build pin, port
map, ASCII rule). Separate namespace; RC memories never load in a Red Moon
session.

Testing: `pytest.ini`, `tests/`, ruff config, and two guard tests. The ASCII
guard walks all authored text in the repository and fails on any codepoint above
127. The port guard asserts every port constant in the codebase is drawn from
the ADR-003 set {8777, 8778, 8779, 8783}; it does not read anything from RC.

Secrets: `.gitignore` covers `API-Key-Claude.txt`, `logs/`, `ops/runtime/`,
`data/rmdata/`, `__pycache__/`, and `_scratch/`. The Anthropic key lives at
`C:\RedMoon\API-Key-Claude.txt`, gitignored, and is a distinct key from either
RC key.

Line endings: `.gitattributes` pins `* text=auto eol=lf` with binary paths marked
`-text`, so the repository never accumulates CRLF churn in diffs. Observed need:
the initial spec commit emitted a `LF will be replaced by CRLF` warning.

Repository: `git init`, first commit. No remote until the operator asks.

### 4b. Data floor

`tools/rmdata_extract.py` writes `data/rmdata/1.1.13.0-r99712/` plus a
`current.txt` pointer, using the DDragon-mirror pattern:

- Full localization string table, GUID to text, with `Codes` colour markup
  resolved.
- The three `GameDifficultyPresets` multiplier sets.
- The `ServerGameSettings` and `ServerHostSettings` schema with defaults.

Canonical typed schemas, versioned and test-guarded, shipped EMPTY in cycle 1
for the bridge to fill in cycle 2: `items.json`, `abilities.json`,
`vbloods.json`, `blood_types.json`, `recipes.json`.

`RM-DataRefresh` scheduled-task spec (the `RC-DDragonMirrorRefresh` analog):
re-extracts when the `VERSION` build string changes.

### 4c. Explicitly NOT in cycle 1

No item or ability stat data. It cannot be obtained offline: the identity and
stat join lives in the binary DOTS blobs. The authoritative join
(PrefabGUID -> localization key -> stat components) is dumped at runtime by
RedMoon.Bridge in cycle 2. Decision recorded: wait for the bridge rather than
seed from a third-party community GUID dump or reverse-engineer the ECS blobs.
The ECS-blob parser is rejected for the same reason RC rejected deep `.rofl`
packet parsing: per-patch re-RE cost against a moving binary format.

## 5. Program staging (cycles 2-8)

Each is a separate session with its own spec.

2. RedMoon.Bridge - BepInEx plugin, live JSON on `:8777`, plus the
   `PrefabCollectionSystem` dump that populates the cycle-1 schemas.
3. Bloodforge core - combat math against V Blood bosses: weapon, spell school,
   gear tier, blood type and quality, jewels, passives, resistances, to DPS,
   EHP and time-to-kill. Server on `:8783`. `ENGINE_VERSION` pinned to the game
   build.
4. Dashboard on `:8778` HTTPS plus the coach loop.
5. Progression route planner - V Blood dependency graph and tech/recipe unlocks.
6. Recipe and refinement economy solver.
7. Castle and base optimizer.
8. Ops hardening - `RM-Supervisor`, `ops/runtime/health.json`, `RM-*` scheduled
   tasks, vision tier on `:8779` if it earns its place.

## 6. Conventions applying to every cycle

- TDD-first: failing characterization or regression test, then implementation,
  then the tier-appropriate suite, then commit.
- Atomic writes only: write to a temp path, then `replace` onto the target.
- Tiered verification: cosmetic and single-module edits do not pay the full
  suite tax; schema, engine and `ENGINE_VERSION` edits do.
- Error handling: no raw API error string ever reaches a UI panel. Render a
  friendly degraded-mode message and log the raw error under `logs/`.
- 7-bit ASCII in all authored content, hook-enforced.
- State assumptions explicitly before coding. Verify against ground truth before
  asserting external state.

## 7. Assumptions

- The operator's five DLC packs (Sinister Evolution, Dracula's Relics,
  Founder's Pack Eldest Bloodline, Legacy of Castlevania Premium, Eternal
  Dominance) are cosmetic and do not alter combat math. The cycle-2 bridge dump
  includes their prefabs regardless, so a wrong assumption here costs nothing.
- Solo or private-host play. The bridge is client-side and is not intended for
  official servers.
- Build `1.1.13.0-r99712` is the data pin. A Steam update invalidates
  `data/rmdata/<build>/` and triggers `RM-DataRefresh`.
- No GitHub remote until the operator asks for one.

## 8. Success criteria for cycle 1

1. `git log` in `C:\RedMoon\` shows an initial commit and this spec.
2. Opening a Claude Code session at `C:\RedMoon\` loads `CLAUDE.md`, the Red
   Moon memory namespace, and the SessionStart facts banner, with no RC content
   present.
3. The ASCII precommit gate rejects a staged file containing an em-dash.
4. `python tools/rmdata_extract.py` produces `data/rmdata/1.1.13.0-r99712/`
   plus `current.txt`, and the run is idempotent.
5. `pytest` passes, including the ASCII guard test and the port-disjointness
   test.
6. `/done` runs end to end in the Red Moon repository.

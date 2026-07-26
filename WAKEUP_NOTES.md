# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-07-26 - Cycle 1 COMPLETE and merged

Cycle 1 shipped end to end. Branch `cycle-1-harness`, 34 commits, merged into
`master` as `2a493ea`. Ledger entry 001 carries the detail.

State at close, all verified live rather than reported:

- `python -m pytest` 106 passed, `python -m ruff check .` clean,
  `python tools/ascii_guard.py` exits 0.
- `python tools/rmdata_extract.py` writes `data/rmdata/1.1.13.0-r99712/` with
  8379 localization strings and 28 markup codes, byte-identical across runs, and
  seeds `tables/` with five empty validated envelopes for the cycle 2 bridge.
- Remote is `https://github.com/Remus3/RedMoon` (private). `master` pushed.
- `RM-DataRefresh` is installed and Ready, next run 05:30 daily.
- Memory namespace live at
  `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\`, restorable from
  the committed seed in `docs/memory_seed/`.

Two findings worth carrying forward, both caught by review rather than by
running code:

1. The precommit gate was wired with `"matcher": "Bash(git commit:*)"` -
   permission-rule syntax in a field matched against the tool name - so it never
   fired for the whole cycle despite being unit-tested and documented. Fixed to
   `Bash|PowerShell`, with a test that now rejects specifier syntax in any
   matcher. Worth remembering: a hook passing its unit tests says nothing about
   whether it is wired.
2. `docs/BLOODFORGE.md` named `data/rmdata/<build>/tables/*.json` as Bloodforge's
   inputs, but nothing created that directory and `empty_table()` had no
   production caller. Cycle 2 would have invented the path by accident. The
   extractor now produces the seam, never clobbering a populated table.

Parked items and every review ruling are archived in `docs/history_notes.md`.

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

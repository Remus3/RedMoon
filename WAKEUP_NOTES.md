# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-07-26 - Cycle 2 spec APPROVED, no code yet

Spec written and approved: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`.
ADR-004 records the ruling. No C# exists yet. Suite still 106 passed,
`ascii_guard` exit 0, both observed this session rather than carried forward.

Ground truth probed live, all of it new:

- The install holds TWO full game copies. Root is `v1.1.13.0-r99712-b17`, the
  pinned build and the one Steam launches. `v3\` is a stale `v1.0.10.4-r91333`
  copy that must never receive BepInEx. The installer asserts VERSION first.
- IL2CPP, not Mono (`GameAssembly.dll`). Loader is BepInExPack V Rising
  `1.733.2`, wrapping BepInEx 6.0.0 bleeding-edge `be.733` on CoreCLR net6.
- `VRising_Server\VERSION` reads `VRisingServer: v1.1.13.0-r99712-b17
  (202605251709)`. Same semantic build as the client, DIFFERENT prefix and
  trailing timestamp, so the install assert compares the semantic build only.
- The game was launched once. `AppData\LocalLow\Stunlock Studios\VRising\` now
  exists with `Player.log`, `Settings\v4\ClientSettings.json`, `CloudSaves\` and
  `ConsoleProfile\`. No save directory, because no world was created.
- Only SDK present is .NET 10.0.301. The plugin targets net6.0. That path is an
  unresolved build risk, not a working config.

Operator rulings: the plugin targets BOTH hosts (client and dedicated server,
ADR-004, overriding the client-only recommendation); `/state` becomes an
envelope carrying `state: null` plus a build stamp and `docs/API.md` was amended
to match; generating `RmPorts.g.cs` into the `test_ports.py` allowlist is
approved; the C# test project is deferred past cycle 2; and downloading the
BepInEx pack is authorized for the next session only.

Two things the next session must settle BEFORE writing code:

1. Port 8777 arbitration when both hosts run at once has a chosen answer, not a
   clean one - bind-time first-come, loser stands down, plus a procedural
   "start the server first". That is procedure, not enforcement. Minting a fifth
   port instead needs an ADR-003 amendment and that call belongs before
   implementation.
2. `PrefabCollectionSystem` is an UNVERIFIED label carried from `ROADMAP.md`. It
   is not a confirmed type name. Six spikes (S1 to S6) remain open and block
   implementation.

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

# Red Moon

Combat and progression math for [V Rising](https://playvrising.com/), computed
from the game's own data rather than from a wiki.

Red Moon has three parts. **RedMoon.Bridge** is a BepInEx plugin that exposes
the running game's state over local HTTP. **The extractor** pulls the game's
static tables - items, recipes, abilities, V Bloods, blood types, ability stats
- off disk into versioned JSON keyed to the exact game build. **Bloodforge** is
the engine that turns those into damage, DPS and effective-HP numbers.

Everything runs on one machine, over loopback, against a game you already own.

## Status

**In development, and honest about it.** What works today:

| Part | State |
|---|---|
| RedMoon.Bridge plugin | Working. Serves `/health`, `/state`, `/dump/*` and `/record/*` in both the game client and the dedicated server. |
| Static data extraction | Working. 3,038 rows across six tables for build `1.1.13.0-r99712`, every count asserted by test. |
| Bloodforge damage and DPS | Working, with one term unresolved (below). |
| Effective HP, time-to-kill | **Withheld on purpose.** See below. |
| Dashboard | Not built. Planned, designed, no code yet. |

There is no packaged release and no installer. This is a working repository, not
a product.

### Why some numbers are missing rather than wrong

Two things Red Moon would need are not readable from the data as it stands:

- **Which power stat drives a given ability.** The game exposes `PhysicalPower`
  and `SpellPower`, and nothing in the extracted tables says which one a
  particular ability scales from. It is not inferable from the damage type - a
  single ability contradicts the obvious rule. Resolving it needs one measured
  in-game cast, and that measurement has not been taken.
- **Boss maximum health.** It does not exist on the prefab. It only exists on a
  spawned instance in a live world, so any time-to-kill needs a running game.

Rather than defaulting these to zero or guessing, Red Moon **omits the fields
entirely** - the key is absent, not null, not `0`, not `-1` - and a test refuses
to let an embargoed field be emitted. A missing number is recoverable. A
confident wrong one is not.

The same rule runs through the data: an ability with no damage coefficient is
distinguishable from one whose coefficient is genuinely `0.0`, because those two
sit one row apart in the real tables and conflating them is wrong about the most
common weapon in the game.

## Requirements

- Windows, and a V Rising install (client, dedicated server, or both)
- Game build `1.1.13.0-r99712` - the extracted data is keyed to it, and the
  ingest refuses a dump whose values disagree with the promoted tables for the
  same build
- [BepInEx](https://github.com/BepInEx/BepInEx) IL2CPP for the plugin
- Python 3.14 and the .NET SDK for the plugin build

## Quick start

Run the test suite - it needs no game running and no game data:

```bash
python -m pytest
```

Extract the static tables from your install:

```bash
python tools/rmdata_extract.py
```

Build the bridge plugin:

```bash
dotnet build bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj -c Release
```

`docs/OPERATIONS.md` covers deploying the plugin, launching a local dedicated
server, and reading live state.

## Ports

All loopback. The plugin's port is a function of which host loaded it, so one
assembly serves both without a bind-time race.

| Service | Port |
|---|---|
| RedMoon.Bridge, game client | 8777 |
| Dashboard (planned) | 8778 |
| Vision server (planned) | 8779 |
| RedMoon.Bridge, dedicated server | 8780 |
| Bloodforge engine (planned - a library today, not a service) | 8783 |

## Documentation

- `docs/ARCHITECTURE.md` - module map and data flow
- `docs/BLOODFORGE.md` - the combat engine in detail
- `docs/API.md` - bridge endpoints
- `docs/OPERATIONS.md` - build, deploy, run
- `docs/adr/README.md` - architectural decisions and why they went the way they
  did
- `ROADMAP.md` - what is next, including the open measurement gaps

## Contributing

This is a personal project built for one machine, so there is no support
promise and no roadmap negotiation. Issues and pull requests are still welcome,
particularly corrections backed by a measurement - a count, a probe, a repro.
Claims about the game's internals are only useful here with the evidence
attached.

Two house rules that will otherwise trip a pull request: all authored content is
7-bit ASCII, and every feature or fix starts with a failing test.

## License

Licensed under the Apache License, Version 2.0. See `LICENSE` and `NOTICE`.

Copyright 2026 Moonbeam.

V Rising is a trademark of Stunlock Studios. This project is not affiliated with
or endorsed by Stunlock Studios, and redistributes no game assets. The extracted
data directory is generated locally from your own install and is not committed.

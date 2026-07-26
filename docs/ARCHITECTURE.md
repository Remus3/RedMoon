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

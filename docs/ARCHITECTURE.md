# Red Moon Architecture

## Shape

Red Moon is a Python 3.14 repository on a single machine, plus one C# BepInEx
plugin that loads inside the game process. As of cycle 2 the only long-lived
process is that plugin, which lives and dies with its host game.

```
C:\RedMoon\
  CLAUDE.md            agent doctrine, loaded every turn
  core/                ports, table schemas, the bridge client
  tools/               enforcement hooks, the extractor, the ingest and the probe
  bridge/src/RedMoon.Bridge/   the BepInEx plugin (C#, net6.0)
  data/schemas/        typed table schemas
  data/rmdata/<build>/ extracted and dumped game data, gitignored, regenerable
  docs/                living docs, ADRs, specs and plans
  tests/               pytest suite
```

## Module map

| Module | Cycle | Responsibility |
|---|---|---|
| `core/ports.py` | 1 | Port registry, the game-host env name, and `bridge_port_for_host`. |
| `core/tables.py` | 1 | The five table names and their shallow schemas. |
| `core/table_deep.py` | 1 | The nested per-table contracts the shallow schema cannot express. |
| `core/bridge_client.py` | 2 | HTTP client for the live bridge. |
| `tools/ascii_guard.py` | 1 | 7-bit ASCII enforcement over authored files. |
| `tools/rmdata_extract.py` | 1 | Offline extraction of the Steam install into a versioned data directory. |
| `tools/install_bepinex.py` | 2 | VERSION-asserting BepInEx installer for both hosts. |
| `tools/gen_bridge_ports.py` | 2 | Generates `RmPorts.g.cs` so the plugin holds no port literal. |
| `tools/rmdata_ingest.py` | 2 | Validates, gates and promotes a dump into `data/rmdata/<build>/tables/`. |
| `tools/bridge_probe.py` | 2 | Liveness probe, including `--motion-diff`. |
| `bridge/src/RedMoon.Bridge/` | 2 | The plugin: host detect, listener, prefab dump, state read, localization, `GET /record/*`. |
| `bloodforge/` | 3 | Combat math. DPS, EHP and time-to-kill against V Blood bosses. Server on 8783 when it exists. |
| `bloodforge/embargo.py` | 3 | The per-field publication gate. Landed one commit AHEAD of the arithmetic. |
| `bloodforge/damage.py`, `dps.py` | 3 | The per-application damage model and the DPS cycle. |
| `bloodforge/series.py` | 3 | Pure functions over a recorded health series. Isolation rule, discard reasons, observed cadence. |
| `bloodforge/powerstat.py` | 3 | The H1-versus-H2 evaluator for the section 3.3 experiment. |
| `tools/anchor_record.py` | 3 | Drives `GET /record/*` and writes a validated anchor run. Re-exports `bloodforge/series.py`. |
| `tools/find_target.py` | 3 | Lists SPAWNED units, so an anchor run has a subject. |
| `dashboard/` | 4 | HTTPS dashboard on 8778 and the coach loop. |
| `ops/` | 8 | Supervisor, `runtime/health.json`, `RM-*` scheduled tasks. |

## Data flow

Cycle 1 is one direction and offline. It ships strings, difficulty presets and
settings, and leaves the tables empty but typed:

```
Steam install  ->  tools/rmdata_extract.py  ->  data/rmdata/<build>/
                                                data/rmdata/current.txt
```

From cycle 2 the live path fills those tables:

```
V Rising process (client or dedicated server)
  -> RedMoon.Bridge (BepInEx, in-process)
  -> http://<RM_GAME_HOST>:<port>/state          live player and world state
  -> http://<RM_GAME_HOST>:<port>/dump/prefabs   authoritative item and ability stats
  -> tools/rmdata_ingest.py --accept
  -> data/rmdata/<build>/tables/*.json
```

The port is a pure function of the detected host, never a literal: 8777 in the
client, 8780 in the dedicated server (ADR-005). One assembly loads in both
(ADR-004), so there is no bind-time race and no mandated start order.

## Why the data floor is split

`StreamingAssets\Localization\English.json` maps a localization GUID to display
text. It carries no item identity and no stat line, and the offline join from a
prefab to that GUID does not exist - it was measured at 0 of 425 on seven key
forms, with a name heuristic reaching only 53. Identity and stats live in binary
DOTS ECS blobs, so the prefab dump is the only route by which item stat data
enters this repository.

The join DOES exist at runtime, through
`GameDataSystem.ManagedDataRegistry.TryGet<ManagedItemData>`, and it resolves
425 of 425 - but only in the CLIENT host. The dedicated server does not load
managed presentation data and resolves 0 of 425. Every dump therefore carries
its own `localization` counter block, so a saved payload states for itself which
host produced it and whether the field was writable there.

## Where the measurements live

`docs/BRIDGE_SPIKES.md` is the record of what was observed against build
`1.1.13.0-r99712` and how. Nothing there is recalled or inferred. A spike is
closed by running something, and several entries in it are corrections of
earlier entries that had been written down as measured.

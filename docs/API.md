# Red Moon API

No HTTP surface exists in cycle 1. This document records the contracts later
cycles must implement, so consumers can be written against a stable shape.

## RedMoon.Bridge, ports 8777 and 8780 (cycle 2)

Served from inside a running V Rising host process. Per ADR-004 one plugin
assembly loads in EITHER host - the client at the install root or the shipped
dedicated server. Per ADR-005 each host binds its OWN port, chosen by the host
it detects at load, so both can serve at once and neither has to win a race:

| Host | Port | Constant |
|---|---|---|
| V Rising client | 8777 | `core.ports.BRIDGE` |
| V Rising dedicated server | 8780 | `core.ports.BRIDGE_SERVER` |

`/health` still reports which host answered, in `host`. Under ADR-005 that field
asserts that the plugin's host detection agrees with the port it bound; a
mismatch means detection is broken. Consumers reach either host through
`core/bridge_client.py` and never write a port or a URL.

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"ok": true, "build": "<game build>", "plugin": "<version>", "host": "client\|server", ...}` |
| GET | `/state` | An envelope: `{"ok": true, "build": "<game build>", "plugin": "<version>", "captured_at": "<iso8601>", "snapshot_age_s": <number>, "state": <object or null>}`. The `state` MEMBER is `null` when no character is loaded; the response body is never the bare literal `null`. |
| GET | `/dump/prefabs` | Full prefab table: PrefabGUID, localization key, component stats. Optional `?table=<name>` narrows to one table; omitting it returns the full dump. Rows only - the `core.tables` envelope is added by `tools/rmdata_ingest.py`, never by the plugin (decision D3). Carries a mandatory `unmapped` array naming every prefab the dumper could not classify. |

The `/state` envelope is deliberate and was approved on 2026-07-26 (cycle 2
design decision D6). A bare `null` body cannot be told apart from a broken
bridge and carries no build stamp, so a consumer could not tell whether the state
it read belonged to the pinned build. The null semantics are preserved exactly,
one level down. Endpoints may gain additive fields; the fields named here are
promises.

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

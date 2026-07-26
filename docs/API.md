# Red Moon API

No HTTP surface exists in cycle 1. This document records the contracts later
cycles must implement, so consumers can be written against a stable shape.

## RedMoon.Bridge, port 8777 (cycle 2)

Served from inside a running V Rising host process. Per ADR-004 the plugin loads
in EITHER host - the client at the install root or the shipped dedicated server -
and exactly one of them owns the port at a time. `/health` reports which one
answered, in `host`.

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"ok": true, "build": "<game build>", "plugin": "<version>", "host": "client\|server", ...}` |
| GET | `/state` | An envelope: `{"ok": true, "build": "<game build>", "plugin": "<version>", "captured_at": "<iso8601>", "snapshot_age_s": <number>, "state": <object or null>}`. The `state` MEMBER is `null` when no character is loaded; the response body is never the bare literal `null`. |
| GET | `/dump/prefabs` | Full prefab table: PrefabGUID, localization key, component stats. |

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

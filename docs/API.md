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

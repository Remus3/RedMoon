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

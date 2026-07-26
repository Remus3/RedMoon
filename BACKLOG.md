# Red Moon Backlog

Aspirational. Nothing here is committed work. Promote an item to `ROADMAP.md`
before building it.

- Offline parser for the DOTS ECS blobs (`ContentArchives`, `EntityScenes`), so
  item stats need no running game. Rejected for cycle 1: per-patch
  reverse-engineering cost against a moving binary format.
- Overlay surface rendered on top of the game.
- Multi-player or dedicated-server support beyond a single local host.
- Screenshot and OCR tier as a bridge fallback.
- Automated V Rising launch plus OBS capture, so a validation session starts and
  records itself instead of being driven by hand. Raised by the operator
  2026-07-26 during cycle 2. Scope is not settled: at minimum an `RM-*` launch
  task for the client and the dedicated server, an OBS scene and profile pinned
  to the game window, and a capture start and stop hook. It is an ops concern, so
  it belongs with cycle 8 rather than in the middle of the bridge, and it was
  deliberately NOT started inside the cycle 2 spike chain.

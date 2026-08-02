# Red Moon

V Rising coaching and analysis for a single Legion PC.

Red Moon reads live game state from a BepInEx plugin (RedMoon.Bridge), computes
combat, progression, economy and castle math in an engine called Bloodforge, and
serves a local dashboard.

- Game build pin: `1.1.13.0-r99712`
- Ports: bridge client 8777, dashboard 8778, vision 8779, bridge server 8780,
  engine 8783
- Agent context and doctrine: `CLAUDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- Decisions: `docs/adr/README.md`

## Status

Cycle 1 of 8: process harness plus the offline data floor. No runtime services
yet. See `ROADMAP.md`.

## Quick start

```
python -m pytest
python tools/rmdata_extract.py
```

## License

Licensed under the Apache License, Version 2.0. See `LICENSE` and `NOTICE`.

Copyright 2026 Moonbeam.

V Rising is a trademark of Stunlock Studios. This project is not affiliated
with or endorsed by Stunlock Studios, and redistributes no game assets.

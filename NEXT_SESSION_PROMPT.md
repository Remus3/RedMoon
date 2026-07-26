# Next Session Prompt

Paste this to start the next Red Moon session.

---

Bootstrap Red Moon: read `CLAUDE.md`, `MEMORY.md`, `ROADMAP.md`,
`WAKEUP_NOTES.md` and `docs/ARCHITECTURE.md`, then `git log --oneline -10`.

Cycle 1 is complete and merged (`2a493ea`). Current work is **cycle 2,
RedMoon.Bridge**: a BepInEx plugin serving live game JSON on `127.0.0.1:8777`,
plus the runtime `PrefabCollectionSystem` dump that fills the five empty table
envelopes cycle 1 seeded at `data/rmdata/<build>/tables/`.

Write the spec first, into `docs/superpowers/specs/`. Before scaffolding
anything, verify against ground truth rather than assumption:

- The game has never been launched on this machine. Launch it once so the
  `AppData\LocalLow\Stunlock Studios` tree exists before making claims about
  save or log locations.
- Confirm the BepInEx version and loader that actually works against build
  `1.1.13.0-r99712`, and confirm the plugin API surface by reading it, not by
  recalling it. ADR-002 records that the plugin must be rebuilt each patch -
  that cost is accepted, not a surprise to relitigate.
- Read `core/tables.py` for the envelope contract every dump must satisfy
  (`validate_table` must return an empty list), and `docs/API.md` for the three
  endpoint shapes already promised.

Known trip hazards recorded by the cycle 1 final review:

- `validate_table` is a shallow gate. It cannot see inside
  `recipes.ingredients`, `blood_types.bonuses` or `items.stats`. Do not read a
  passing validation as a shape guarantee on the first real dump.
- The port-literal guard scans `.cs` now, so the bridge must not hardcode 8777.
- `extract()` never clobbers a populated table file, so a re-extract is safe
  once the bridge has written real rows.

Do not start coding before the spec is approved.

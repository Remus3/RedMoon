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
- A falsification path for Bloodforge output, so a computed DPS, EHP or
  time-to-kill can be checked against an observed kill rather than only against
  its own inputs. Raised 2026-08-01. **Cycle 3's six acceptance criteria are all
  about SOURCING INPUTS - none of them requires the computed number to be right,
  so all six can pass with a confidently wrong TTK.** That is the cycle 2 lesson
  ("a real measurement can answer the RIGHT question about the WRONG SUBJECT")
  one level up: sourcing every field correctly says nothing about whether the
  math over them is sound. V Rising has no rewind or replay file, so the anchor
  has to be a recorded combat log or a hand-timed kill against a known V Blood
  with a known loadout, n small but non-zero. Scope is not settled: what gets
  recorded, how a run is identified, and what tolerance counts as agreement are
  all open. This does NOT block cycle 3 phase 2, which is ingest rather than
  math, but it must be settled BEFORE the combat-math spec opens - a
  time-to-kill published against an unfalsifiable model is the `items.tier`
  mistake with a bigger blast radius.
- A declared and displayed default subject vector for Bloodforge. Raised
  2026-08-01. A time-to-kill is meaningless without a target, so the moment the
  engine computes one it must pick a default V Blood, a default gear level and a
  default blood quality. Whatever it picks silently ranks every weapon and every
  build for every user who does not override it, which makes an unexamined
  default a structural bias rather than a cosmetic one. The 65 `vbloods` rows on
  disk mean this is a choice among knowns, not a guess. Two parts: write down
  the default vector and WHY each component was chosen, and have the consuming
  surface state the assumption on screen rather than burying it. Belongs with
  cycle 3's combat-math spec for the choice and cycle 4 for the display.

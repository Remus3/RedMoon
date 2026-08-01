"""Bloodforge - the Red Moon combat and build engine.

Design contract: docs/BLOODFORGE.md. Falsification protocol:
docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md.

This package opens with its EMBARGO and not with its math, deliberately. Gap 7
is settled and not discharged: nothing has yet checked a computed number against
an observed kill, so every output this engine will produce is unvalidated. An
embargo written before the first serializer has one emit site to cover. An
embargo written after has to find them all.
"""
from __future__ import annotations

ENGINE_VERSION = "0.1.0+1.1.13.0-r99712"
"""The engine revision, pinned to the game build it is validated against.

Format is <semver>+<game build pin>. Both halves are load-bearing:

* the semver moves when the MATH changes, so an anchor recorded against one
  revision cannot silently vouch for another (falsification spec B.1 reserves
  engine_version in the run manifest for exactly this);
* the build pin moves when the GAME changes, which re-arms the embargo
  automatically and is the same drift-anchor idiom tests/test_drift_anchors.py
  already applies to every other authored pin.

It did not exist before 2026-08-01. docs/BLOODFORGE.md:56-60 and ROADMAP both
described it as pinned while a repo-wide grep over *.py, *.cs and *.json
returned nothing, which is the plainest possible case of a document describing
an intention as a fact. 0.1.0 because no math is implemented yet: the version
starts below 1 and the embargo, not the number, is what makes that safe.

NEVER bump this in the same commit as an unvalidated data change
(docs/BLOODFORGE.md:60).
"""

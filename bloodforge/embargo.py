"""The publication embargo on dps, ehp and ttk_seconds.

Decision D of the falsification spec, in code. The rule, stated so it is
testable:

  R-EMBARGO. For any subject S, Bloodforge may serialize ttk_seconds only if a
  validated anchor set exists for S's comparable class. Absent that, the key is
  ABSENT from the payload - not null, not 0, not -1. dps and ehp follow the same
  rule with their own lift conditions.

The idiom is the strongest one in this repository and it is already load-bearing
three times over: items.tier has no source on this build and is declared and
never emitted (tests/test_schemas.py:34-56); vbloods.max_health is
instance-only, measured 0 on the prefab against 8107 on the live instance
(data/schemas/vbloods.schema.json); ability_stats.power_stat is PROVEN ABSENT
across all 51 components on the _Hit entity (tests/test_ability_stats.py:67-76).
In all three the absent KEY is the honest signal and a zero would be a lie.

WHY THE LIFT IS PER FIELD. The three outputs need different evidence, and
merging them would either embargo a computable number or publish an
uncomputable one:

  dps         needs coefficients, cast time and cooldown. All on disk today,
              over 1818 promoted ability_stats rows. No health denominator.
              Lifts on the per-hit gate alone.
  ehp         needs the player side, which the recorder gets free from the same
              tick. Lifts on the EHP gate.
  ttk_seconds needs a health DENOMINATOR that does not exist on disk at all,
              plus an active-time median over three comparable runs. Lifts on
              the per-hit gate AND the TTK gate AND n >= 3.

There is ONE gate function and the serializer iterates its result. That is what
makes tests/test_embargo.py total rather than a spot check: there is no second
code path that can emit an embargoed field.

WHAT THIS DOES NOT COVER, per D.5: diagnostics under logs/ and anything under
_scratch/. A model whose numbers cannot be looked at cannot be debugged. The
embargo is on PUBLICATION to a user surface - the engine API and the dashboard,
whose ports are named in core/ports.py and are deliberately not written here -
and any file a user is told to read.
"""
from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"

ANCHOR_DIRNAME = "anchors"
"""Subdirectory of data/ holding one JSON file per recorded run.

It does not exist yet and that is the current, correct state of the world: no
anchor run has been taken. load_anchors returns [] for a missing directory so
the embargo fails CLOSED on a fresh checkout rather than raising.
"""

EMBARGOED_FIELDS = frozenset({"dps", "ehp", "ttk_seconds"})
"""Every field that may not be published without evidence.

A field added to a Bloodforge payload that is not listed here is NOT embargoed.
That is a deliberate allowlist-of-secrets rather than a denylist-of-safe: the
three names are the three quantities the whole engine exists to produce, and a
fourth computed output would be a design change large enough to touch this line.
"""

QUALITY_BUCKET = 10
"""Blood quality tolerance, in points, from the B.2 matching rule.

Quality scales every blood magnitude at runtime and none of them are on the
prefab (all 13 blood_types rows carry stat NAMES with
value_source: blood_quality_scaled_at_runtime), so an exact match would make two
otherwise identical runs incomparable over a difference the engine cannot even
price yet.
"""

_IDENTITY_KEYS = (
    "game_build",
    "engine_version",
    "boss_prefab_guid",
    "difficulty",
    "blood_type",
    "equipped_item_guids",
)
"""The B.2 tuple that must agree EXACTLY for two runs to be pooled.

difficulty is in here because of ROADMAP gap 9: boss level, power and health are
all difficulty-scaled, so vbloods.json is implicitly a NORMAL table and a Brutal
run is a different subject rather than a noisier sample of the same one. It is
compared as the whole verbatim modifier object, never as a label, because a
server may override any modifier independently of its GameDifficulty string.

equipped_item_guids is a MAP of slot to prefab_guid rather than a gear score,
because gear_score is present on 117 of 425 item rows and on 0 of the 205
weapons. A scalar gear level is not sourceable for the slot that matters most.

Pooling across subjects is precisely how a model gets fitted to noise, so this
is strict by intent.
"""


def load_schema(name: str) -> dict:
    """Load a Bloodforge-side schema document by name.

    Separate from core.tables.load_schema, which raises KeyError for any name
    outside its frozen TABLE_NAMES tuple. The anchor is not extracted game data:
    adding it to that registry would make tools/rmdata_extract seed an empty
    anchor table into every build directory. core/tables.py is also a FROZEN
    file. So the anchor gets its own loader and reuses only validate_table,
    which takes a schema DICT and needs no registry at all.
    """
    return json.loads((SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def load_anchors(directory: Path | str) -> list[dict]:
    """Read every anchor run in a directory, sorted by filename.

    A missing directory yields [], which is the state today and must not raise:
    an exception here would be caught somewhere upstream and the embargo would
    fail OPEN, which is the one failure mode this module exists to prevent.
    """
    path = Path(directory)
    if not path.is_dir():
        return []
    anchors = []
    for entry in sorted(path.glob("*.json")):
        anchors.append(json.loads(entry.read_text(encoding="utf-8")))
    return anchors


def comparable(subject: Mapping, manifest: Mapping) -> bool:
    """True when a recorded run may be pooled with a subject, per B.2.

    Exact agreement on the identity tuple, and blood quality within one bucket.
    """
    for key in _IDENTITY_KEYS:
        if key not in subject or key not in manifest:
            return False
        if subject[key] != manifest[key]:
            return False

    left = subject.get("blood_quality")
    right = manifest.get("blood_quality")
    if not isinstance(left, int) or not isinstance(right, int):
        return False
    return abs(left // QUALITY_BUCKET - right // QUALITY_BUCKET) <= 1


def _passed(anchor: Mapping, gate: str) -> bool:
    """True only for a recorded, explicit pass.

    A missing gates block, a missing gate, or any value other than the literal
    string reads as NOT passed. Every unknown state must withhold.
    """
    gates = anchor.get("gates")
    if not isinstance(gates, Mapping):
        return False
    return gates.get(gate) == "pass"


def publishable_fields(subject: Mapping, anchors: Iterable[Mapping]) -> frozenset[str]:
    """Return the subset of EMBARGOED_FIELDS that may be serialized for subject.

    An empty frozenset - today's answer for every subject in existence - means
    the payload carries none of the three.
    """
    matching = [
        anchor
        for anchor in anchors
        if isinstance(anchor, Mapping)
        and isinstance(anchor.get("manifest"), Mapping)
        and comparable(subject, anchor["manifest"])
    ]

    per_hit = [anchor for anchor in matching if _passed(anchor, "per_hit")]
    lifted = set()
    if per_hit:
        lifted.add("dps")
    if any(_passed(anchor, "ehp") for anchor in matching):
        lifted.add("ehp")
    if len([anchor for anchor in per_hit if _passed(anchor, "ttk")]) >= 3:
        lifted.add("ttk_seconds")
    return frozenset(lifted)


def apply_embargo(
    payload: Mapping,
    subject: Mapping,
    anchors: Sequence[Mapping],
) -> dict:
    """Return payload with every unlifted embargoed field REMOVED.

    Removed, not zeroed and not nulled. A consumer that finds no ttk_seconds
    must render a degraded-mode message naming the reason, per the CLAUDE.md
    error-handling rule:

      time-to-kill withheld: no validated anchor for this subject on build
      1.1.13.0-r99712

    Fields outside EMBARGOED_FIELDS pass through untouched.
    """
    allowed = publishable_fields(subject, anchors)
    return {
        key: value
        for key, value in payload.items()
        if key not in EMBARGOED_FIELDS or key in allowed
    }

"""The publication embargo on Bloodforge's three computed outputs.

Gap 7 is SETTLED and NOT DISCHARGED: the falsification protocol exists
(docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md) but no
anchor run has been taken, so nothing can tell us whether a computed dps, ehp or
ttk_seconds is right. Decision D of that spec therefore embargoes all three
until their per-field lift conditions are met, following the strongest idiom in
this repository: DECLARED AND NEVER EMITTED, already governing items.tier
(tests/test_schemas.py:34-56), vbloods.max_health and ability_stats.power_stat
(tests/test_ability_stats.py:67-76).

The gate is built BEFORE the combat math so the math cannot leak while it is
being written. That ordering is the whole point: an embargo added after a
serializer exists has to find every emit site, and an embargo added before it
only has to be the one site there is.

ABSENT means the KEY is missing. Not null, not 0, not -1. A consumer that sees
no ttk_seconds renders a degraded-mode message per the CLAUDE.md error-handling
rule; a consumer that sees ttk_seconds: 0 believes the boss dies instantly.
"""
from __future__ import annotations

import json

import pytest

from bloodforge import ENGINE_VERSION
from bloodforge.embargo import (
    EMBARGOED_FIELDS,
    apply_embargo,
    comparable,
    load_anchors,
    load_schema,
    publishable_fields,
)
from core.tables import validate_table

BUILD = "1.1.13.0-r99712"

# A sentinel pin, deliberately impossible so it can never be mistaken for a real
# build. Same shape tests/test_drift_anchors.py:37 already reserves.
OTHER_BUILD = "9.9.9.9-r00001"

# The default subject vector, falsification spec section E.1. Dracula is the
# only boss with a measured live max_health on record (8107 on entity 322945,
# docs/BRIDGE_SPIKES.md:1393), which is why it is the default target at all.
NORMAL = {"LevelIncrease": 0, "MaxHealthModifier": 1.0, "PowerModifier": 1.0}
BRUTAL = {"LevelIncrease": 3, "MaxHealthModifier": 1.25, "PowerModifier": 1.7}

SUBJECT = {
    "game_build": BUILD,
    "engine_version": ENGINE_VERSION,
    "boss_prefab_guid": -327335305,
    "difficulty": NORMAL,
    "blood_type": "BloodType_Warrior",
    "blood_quality": 100,
    "equipped_item_guids": {"weapon": -1173681254},
}


def _anchor(**overrides) -> dict:
    """A minimal VALID anchor: manifest identity plus recorded gate verdicts."""
    anchor = {
        "manifest": dict(SUBJECT),
        "gates": {"per_hit": "pass", "ttk": "pass", "ehp": "pass"},
    }
    for key, value in overrides.items():
        if key in ("per_hit", "ttk", "ehp"):
            anchor["gates"][key] = value
        else:
            anchor["manifest"][key] = value
    return anchor


# ---------------------------------------------------------------------------
# D.4.3 - the total test. With no anchors, no computed field is publishable.
# ---------------------------------------------------------------------------


def test_no_ttk_is_emitted_without_an_anchor():
    """The headline rule. Assert absence of the KEY, mirroring
    tests/test_schemas.py:58-62, which asserts a row WITHOUT tier validates."""
    payload = apply_embargo(
        {"subject": "dracula", "dps": 812.5, "ehp": 4210.0, "ttk_seconds": 61.2},
        SUBJECT,
        anchors=[],
    )
    assert "ttk_seconds" not in payload
    assert "dps" not in payload
    assert "ehp" not in payload
    assert payload["subject"] == "dracula", "the embargo strips three keys, not the payload"


def test_publishable_fields_is_empty_with_no_anchors():
    assert publishable_fields(SUBJECT, []) == frozenset()


def test_embargoed_fields_are_exactly_the_three_the_spec_names():
    assert EMBARGOED_FIELDS == frozenset({"dps", "ehp", "ttk_seconds"})


# ---------------------------------------------------------------------------
# D.2 - the lift conditions are PER FIELD, and that is the point.
# ---------------------------------------------------------------------------


def test_per_hit_gate_alone_lifts_dps_and_nothing_else():
    """dps needs coefficients, cast time and cooldown, all on disk over 1818
    ability_stats rows, and NO health denominator. ttk_seconds needs the
    instance-only max_health, so one passing run cannot lift it."""
    anchors = [_anchor(ttk="fail", ehp="fail")]
    assert publishable_fields(SUBJECT, anchors) == frozenset({"dps"})


def test_ehp_gate_alone_lifts_ehp_and_nothing_else():
    anchors = [_anchor(per_hit="fail", ttk="fail")]
    assert publishable_fields(SUBJECT, anchors) == frozenset({"ehp"})


def test_ttk_needs_three_comparable_runs_not_one():
    """C.2 is a median over n >= 3. Two passing runs do not lift it."""
    two = [_anchor(), _anchor()]
    assert "ttk_seconds" not in publishable_fields(SUBJECT, two)
    three = [_anchor(), _anchor(), _anchor()]
    assert "ttk_seconds" in publishable_fields(SUBJECT, three)


def test_ttk_needs_the_per_hit_gate_too():
    """C.2 without C.1 is NOT a pass. A single aggregate gate passes through
    cancelling errors: damage 20 percent high times uptime 20 percent low lands
    on the right TTK for the wrong reason."""
    runs = [_anchor(per_hit="fail") for _ in range(3)]
    assert "ttk_seconds" not in publishable_fields(SUBJECT, runs)


# ---------------------------------------------------------------------------
# D.4.5 - a build bump RE-ARMS the embargo automatically.
# ---------------------------------------------------------------------------


def test_an_anchor_for_another_build_does_not_lift_the_embargo():
    anchors = [_anchor(game_build=OTHER_BUILD) for _ in range(3)]
    assert publishable_fields(SUBJECT, anchors) == frozenset()


def test_an_anchor_from_another_engine_version_does_not_lift_the_embargo():
    """The manifest reserves engine_version so an anchor cannot be silently
    compared across engine revisions (falsification spec B.1)."""
    anchors = [_anchor(engine_version="0.0.0-sentinel") for _ in range(3)]
    assert publishable_fields(SUBJECT, anchors) == frozenset()


# ---------------------------------------------------------------------------
# B.2 - the matching rule. Pooling across subjects is how a model gets fitted
# to noise, so comparability is strict and tested in both directions.
# ---------------------------------------------------------------------------


def test_difficulty_is_part_of_the_identity():
    """ROADMAP gap 9: boss level, power and health are difficulty-scaled, so
    vbloods.json is implicitly a NORMAL table. A Brutal anchor is a different
    subject, not a noisier sample of the same one."""
    assert not comparable(SUBJECT, {**SUBJECT, "difficulty": BRUTAL})


def test_a_different_boss_is_a_different_subject():
    assert not comparable(SUBJECT, {**SUBJECT, "boss_prefab_guid": -496360395})


def test_a_different_weapon_is_a_different_subject():
    other = {**SUBJECT, "equipped_item_guids": {"weapon": -1}}
    assert not comparable(SUBJECT, other)


def test_blood_quality_matches_within_one_ten_point_bucket():
    assert comparable(SUBJECT, {**SUBJECT, "blood_quality": 95})
    assert not comparable(SUBJECT, {**SUBJECT, "blood_quality": 84})


def test_an_identical_manifest_is_comparable_with_itself():
    assert comparable(SUBJECT, dict(SUBJECT))


# ---------------------------------------------------------------------------
# D.4.1 - the anchor schema, and what the frozen machinery can actually gate.
# ---------------------------------------------------------------------------


def test_anchor_schema_declares_the_liveness_control_on_every_sample():
    """A.4 step 1 and A.5: a series whose samples carry carries_prefab_marker
    true is DISCARDED, not analysed. The prefab reads Health.Value 0, so a
    recorder latched onto it records a flat zero series and, on a naive reading,
    an instantaneous kill (falsification spec 1.3)."""
    schema = load_schema("anchor")
    assert "carries_prefab_marker" in schema["required"]
    assert "health_value" in schema["required"]
    assert "health_max" in schema["required"]


def test_a_recorded_sample_passes_the_frozen_shallow_gate():
    """The anchor series reuses core.tables.validate_table, which takes a schema
    DICT and so does not need the frozen TABLE_NAMES registry."""
    schema = load_schema("anchor")
    table = {
        "table": "anchor",
        "build": BUILD,
        "schema_version": schema["schema_version"],
        "rows": [
            {
                "index": 0,
                "captured_at": "2026-08-01T12:00:00Z",
                "prefab_guid": -327335305,
                "carries_prefab_marker": False,
                "health_value": 8107.0,
                "health_max": 8107.0,
                "is_dead": False,
            }
        ],
    }
    assert validate_table(table, schema) == []


def test_a_fifth_envelope_key_passes_the_frozen_gate():
    """REASONED and now PROBED. The open question was whether an anchor may
    carry its manifest as a fifth envelope key beside table, build,
    schema_version and rows. validate_table checks that the four REQUIRED keys
    are present and rejects undeclared fields on ROWS only (core/tables.py:89-92)
    - it never enumerates envelope keys. So it passes, and the manifest does not
    have to be a second file."""
    schema = load_schema("anchor")
    table = {
        "table": "anchor",
        "build": BUILD,
        "schema_version": schema["schema_version"],
        "rows": [],
        "manifest": dict(SUBJECT),
    }
    assert validate_table(table, schema) == []


def test_deep_problems_cannot_gate_the_anchor_and_the_spec_is_corrected():
    """Falsification spec D.4.1 says the anchor is validated by validate_table
    AND core.table_deep.deep_problems. Half true, measured here: deep_problems
    raises KeyError for any name outside the frozen TABLE_NAMES tuple
    (core/table_deep.py:356-357), and core/tables.py is a FROZEN file. The
    anchor is not a game data table and must not be added to that registry - the
    extractor would seed an empty one per build. Pinned as a test so the
    correction cannot be lost."""
    from core.table_deep import deep_problems

    with pytest.raises(KeyError):
        deep_problems("anchor", {"rows": []})


# ---------------------------------------------------------------------------
# The engine version. It did not exist anywhere in code before this commit.
# ---------------------------------------------------------------------------


def test_engine_version_names_the_build_it_is_pinned_to():
    """docs/BLOODFORGE.md:56-60: ENGINE_VERSION is pinned to the game build it
    was validated against. A repo-wide grep for it returned nothing before
    2026-08-01, while ROADMAP and BLOODFORGE both described it as pinned."""
    assert ENGINE_VERSION.endswith(BUILD)


def test_load_anchors_of_an_empty_directory_is_empty(tmp_path):
    assert load_anchors(tmp_path) == []


def test_load_anchors_reads_a_written_anchor(tmp_path):
    (tmp_path / "run.json").write_text(json.dumps(_anchor()), encoding="utf-8")
    assert len(load_anchors(tmp_path)) == 1


def test_load_anchors_of_a_missing_directory_is_empty(tmp_path):
    """No anchor directory means no anchors, which is the state today. It must
    not raise, or the embargo fails open on a fresh checkout."""
    assert load_anchors(tmp_path / "nope") == []

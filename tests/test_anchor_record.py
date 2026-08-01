"""The anchor writer: wire translation, the A.5 checklist, isolated deltas.

tools/anchor_record.py drives the bridge recorder endpoints and writes a
VALIDATED run to data/anchors/<run_id>.json. These tests pin the four things
that can silently produce a wrong anchor:

1. The wire carries blood_type_guid as an INT and the anchor schema declares
   blood_type as a STRING. A row that ships the guid is rejected by
   core.tables.validate_table, which refuses undeclared fields on ROWS
   (core/tables.py:89-92). The join goes through tables/blood_types.json.
2. The manifest may not DEFAULT a field it cannot source. A.5.6 discards a run
   whose manifest has a defaulted field, so an unsourceable field is ABSENT and
   named in known_holes - the same DECLARED AND NEVER EMITTED idiom the embargo
   already runs on.
3. The A.5 checklist returns NAMED REASONS, not a bool. A discarded run is
   recorded with its reason and never repaired.
4. An ISOLATED delta is bracketed by no-change on BOTH sides. At 4 Hz -
   SampleEveryFrames = 15 in Plugin.cs:41, a ceiling and not a knob - several
   hits of a hits_per_cast up to 4 ability land inside one 250 ms window, so the
   per-hit gate runs over isolated deltas only and never over all deltas.
"""
from __future__ import annotations

import json

import pytest

from bloodforge import ENGINE_VERSION
from bloodforge.embargo import load_schema
from core.tables import validate_table
from tools import anchor_record as ar

BUILD = "1.1.13.0-r99712"

# Measured on disk 2026-08-01 by counting the promoted rows, not by reading the
# prose that describes them. Falsification spec B.1 names the same six.
PROMOTED = {
    "items": (425, 4),
    "recipes": (663, 2),
    "abilities": (54, 1),
    "vbloods": (65, 2),
    "blood_types": (13, 2),
    "ability_stats": (1818, 1),
}

DRACULA = -327335305
WARRIOR_BLOOD = -516976528

NORMAL = {"LevelIncrease": 0, "MaxHealthModifier": 1.0, "PowerModifier": 1.0}


def _wire_sample(index: int, health: float, **overrides) -> dict:
    """One sample in the wire shape the bridge sends, before translation."""
    sample = {
        "index": index,
        "captured_at": ar.stamp(index * ar.TICK_INTERVAL_S),
        "prefab_guid": DRACULA,
        "carries_prefab_marker": False,
        "health_value": health,
        "health_max": 8107.0,
        "is_dead": False,
        "player_health_value": 1500.0,
        "player_health_max": 1500.0,
        "blood_quality": 100.0,
        "blood_type_guid": WARRIOR_BLOOD,
    }
    sample.update(overrides)
    return sample


def _start_run(**overrides) -> dict:
    """The `run` object /record/start returns on a successful arm."""
    run = {
        "boss_prefab_guid": DRACULA,
        "boss_prefab_name": "CHAR_Vampire_Dracula_VBlood",
        "boss_entity_index": 322945,
        "carries_prefab_marker": False,
        "boss_max_health_observed": 8107.0,
        "boss_health_value_at_arm": 8107.0,
        "boss_resistances_observed": {
            "physical": 0.0,
            "spell": 0.0,
            "fire": 0.0,
            "corruption": 0.5,
        },
        "boss_unit_level": 91.0,
        "player_resolved": True,
        "player_unit_level": 91.0,
        "player_max_health": 1500.0,
        "player_unit_stats": {
            "UnitStats.PhysicalPower": 120.0,
            "UnitStats.SpellPower": 40.0,
        },
        "operator_note": "first anchor attempt",
    }
    run.update(overrides)
    return run


META = {
    "build": BUILD,
    "version_string": "VRising: v1.1.13.0-r99712-b17 (202605251526)",
    "schema_version": 1,
}

HEALTH = {"ok": True, "build": BUILD, "plugin": "0.4.0", "host": "client"}


def _manifest(**kwargs) -> dict:
    args = {
        "start_run": _start_run(),
        "meta": META,
        "health": HEALTH,
        "fingerprint": ar.table_fingerprint(),
        "difficulty": NORMAL,
        "boss_level": 91,
        "captured_at": "2026-08-01T12:00:00Z",
        # The cadence is MEASURED from the series and there is no nominal rate
        # to fall back on, so a manifest without a series cannot state one.
        "rows": ar.translate_samples([_wire_sample(i, 8107.0 - i) for i in range(4)], {}),
    }
    args.update(kwargs)
    return ar.build_manifest(**args)


# ---------------------------------------------------------------------------
# 1. Wire to schema. The blood_type join, and no undeclared field on a ROW.
# ---------------------------------------------------------------------------


def test_translate_joins_the_blood_type_guid_to_a_name_and_drops_the_guid():
    """The wire carries an int; the schema declares a string. A row that keeps
    blood_type_guid is an undeclared field and validate_table rejects it."""
    rows = ar.translate_samples([_wire_sample(0, 8107.0)], {WARRIOR_BLOOD: "BloodType_Warrior"})
    assert rows[0]["blood_type"] == "BloodType_Warrior"
    assert "blood_type_guid" not in rows[0]


def test_translate_omits_blood_type_when_the_guid_joins_nothing():
    """OMITTED, never defaulted to a name. An unjoinable guid is a real and
    different statement from a known blood type."""
    rows = ar.translate_samples([_wire_sample(0, 8107.0)], {})
    assert "blood_type" not in rows[0]
    assert "blood_type_guid" not in rows[0]


def test_translate_keeps_only_fields_the_schema_declares():
    wire = _wire_sample(0, 8107.0, entity_index=322945, debug_scratch="ignore me")
    rows = ar.translate_samples([wire], {WARRIOR_BLOOD: "BloodType_Warrior"})
    declared = set(load_schema("anchor")["fields"])
    assert set(rows[0]) <= declared


def test_translate_omits_the_player_block_when_the_character_was_not_resolved():
    """The wire OMITS the last four when the character could not be resolved
    that tick. Omitted rather than zeroed: a zero player health is a real and
    different statement (anchor.schema.json, player_health_value)."""
    wire = _wire_sample(0, 8107.0)
    for key in ("player_health_value", "player_health_max", "blood_quality", "blood_type_guid"):
        del wire[key]
    rows = ar.translate_samples([wire], {WARRIOR_BLOOD: "BloodType_Warrior"})
    assert "player_health_value" not in rows[0]
    assert "blood_quality" not in rows[0]


def test_a_translated_envelope_passes_the_frozen_shallow_gate():
    """Five envelope keys, manifest included. validate_table requires four and
    rejects undeclared fields on ROWS only, so the fifth passes and a run cannot
    be separated from the statement of what it measured."""
    envelope = ar.build_envelope(
        rows=ar.translate_samples(
            [_wire_sample(i, 8107.0 - i) for i in range(4)],
            {WARRIOR_BLOOD: "BloodType_Warrior"},
        ),
        manifest=_manifest(),
        build=BUILD,
    )
    assert set(envelope) == {"table", "build", "schema_version", "rows", "manifest"}
    assert validate_table(envelope, load_schema("anchor")) == []


# ---------------------------------------------------------------------------
# 2. The B.1 manifest. Sourced or ABSENT, never defaulted.
# ---------------------------------------------------------------------------


def test_manifest_sources_build_plugin_and_engine_rather_than_defaulting_them():
    manifest = _manifest()
    assert manifest["game_build"] == BUILD
    assert manifest["game_version_string"] == META["version_string"]
    assert manifest["plugin_version"] == "0.4.0"
    assert manifest["bridge_host"] == "client"
    assert manifest["engine_version"] == ENGINE_VERSION


def test_manifest_records_difficulty_as_the_verbatim_object_never_as_a_label():
    """A server may override any modifier independently of its GameDifficulty
    string, so a label is not enough. Brutal is 1.25 health, 1.7 power and +3
    levels against Normal's neutral values."""
    manifest = _manifest()
    assert manifest["difficulty"] == NORMAL
    assert not isinstance(manifest["difficulty"], str)


def test_manifest_omits_equipped_items_when_the_operator_did_not_supply_them():
    """The hole is made EXPLICIT, not filled. A.5.6 discards a run whose
    manifest has a defaulted field, so an empty map would be worse than nothing:
    it is a positive claim that the player was naked."""
    manifest = _manifest()
    assert "equipped_item_guids" not in manifest
    assert "jewels_and_passives" not in manifest
    assert "equipped_item_guids" in manifest["known_holes"]
    assert "jewels_and_passives" in manifest["known_holes"]


def test_manifest_records_equipped_items_when_the_operator_did_supply_them():
    manifest = _manifest(equipped_item_guids={"weapon": -1173681254})
    assert manifest["equipped_item_guids"] == {"weapon": -1173681254}
    assert "equipped_item_guids" not in manifest["known_holes"]


def test_manifest_never_copies_boss_resistances_from_disk():
    """B.1: the four values are read LIVE. The disk values are PREFAB values and
    the whole point of constraint 1 is that prefab and instance can disagree."""
    live = {"physical": 0.0, "spell": 0.0, "fire": 12.0, "corruption": 0.5}
    manifest = _manifest(start_run=_start_run(boss_resistances_observed=live))
    assert manifest["boss_resistances_observed"] == live


def test_manifest_omits_the_boss_denominator_when_the_arm_did_not_observe_one():
    run = _start_run()
    del run["boss_max_health_observed"]
    manifest = _manifest(start_run=run)
    assert "boss_max_health_observed" not in manifest
    assert "boss_max_health_observed" in manifest["known_holes"]


def test_manifest_records_the_observed_sample_rate_measured_from_the_series():
    """MEASURED, never a constant. 1.99 Hz on the dedicated server against the
    4 Hz both specs assume, because the rate is frames-per-sample times the
    HOST's frame rate and the two hosts do not share one."""
    slow = 0.5
    rows = ar.translate_samples(
        [_wire_sample(i, 8107.0 - i, captured_at=ar.stamp(i * slow)) for i in range(8)],
        {},
    )
    manifest = _manifest(rows=rows)
    assert manifest["observed_sample_interval_s_median"] == pytest.approx(slow)
    assert manifest["observed_sample_rate_hz"] == pytest.approx(2.0)


def test_manifest_omits_the_observed_rate_when_the_series_cannot_supply_one():
    manifest = _manifest(rows=[])
    assert "observed_sample_rate_hz" not in manifest
    assert "observed_sample_rate_hz" in manifest["known_holes"]


def test_table_fingerprint_is_counted_from_disk_not_copied_from_a_document():
    fingerprint = ar.table_fingerprint()
    assert set(fingerprint) == set(PROMOTED)
    for name, (rows, schema_version) in PROMOTED.items():
        assert fingerprint[name] == {"rows": rows, "schema_version": schema_version}, name


def test_run_id_carries_the_instant_the_boss_and_a_hash_of_the_manifest():
    manifest = _manifest()
    run_id = manifest["run_id"]
    stamp, guid, digest = run_id.rsplit("-", 2)
    # A minus sign inside a dash-delimited id is ambiguous and most V Blood
    # guids are negative, so the sign is carried as a leading letter and
    # rsplit recovers exactly three parts.
    assert guid == f"{ar.NEGATIVE_GUID_PREFIX}{abs(DRACULA)}"
    assert stamp.startswith("2026")
    assert len(digest) == ar.RUN_ID_HASH_CHARS
    assert ar.SEPARATOR_SAFE.fullmatch(run_id), "run_id is used as a Windows filename stem"


def test_run_id_changes_when_any_manifest_field_changes():
    assert _manifest()["run_id"] != _manifest(boss_level=57)["run_id"]


def test_run_id_is_stable_for_an_identical_manifest():
    assert _manifest()["run_id"] == _manifest()["run_id"]


# ---------------------------------------------------------------------------
# 3. The A.5 validity checklist. Named reasons, never a bool.
# ---------------------------------------------------------------------------


def _clean_series(count: int = 8) -> list[dict]:
    rows = ar.translate_samples(
        [_wire_sample(i, 8107.0 - i * 1000.0) for i in range(count)],
        {WARRIOR_BLOOD: "BloodType_Warrior"},
    )
    rows[-1]["health_value"] = 0.0
    rows[-1]["is_dead"] = True
    return rows


def test_a_clean_series_has_no_reasons_and_is_valid():
    result = ar.check_run(_clean_series(), DRACULA, _manifest())
    assert result["reasons"] == []
    assert result["valid"] is True


def test_a_prefab_marker_sample_discards_the_run_rather_than_smoothing_it():
    """The prefab reads Health.Value 0, so a recorder latched onto it records a
    flat zero series that a naive reading turns into an instantaneous kill."""
    rows = _clean_series()
    rows[3]["carries_prefab_marker"] = True
    result = ar.check_run(rows, DRACULA, _manifest())
    assert "carries_prefab_marker_true" in result["reasons"]
    assert result["valid"] is False


def test_a_series_with_no_live_sample_is_discarded():
    rows = _clean_series()
    for row in rows:
        row["health_max"] = 0.0
    assert "no_live_sample" in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_a_sample_restating_another_guid_discards_the_run():
    """A sample that restates a guid other than the queried one means the
    recorder followed a stale entity handle."""
    rows = _clean_series()
    rows[2]["prefab_guid"] = -496360395
    assert "prefab_guid_mismatch" in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_a_run_that_did_not_start_from_full_health_is_MARKED_partial_not_discarded():
    """A.5.3: excluded from the TTK gate while REMAINING USABLE for the per-hit
    gate. That distinction is the whole reason check_run returns marks as well
    as reasons."""
    rows = _clean_series()
    rows[0]["health_value"] = rows[0]["health_max"] / 2
    result = ar.check_run(rows, DRACULA, _manifest())
    assert result["reasons"] == []
    assert "partial" in result["marks"]
    assert result["valid"] is True


def test_a_series_with_no_terminal_sample_is_discarded():
    rows = _clean_series()
    rows[-1]["health_value"] = 500.0
    rows[-1]["is_dead"] = False
    assert "no_terminal_sample" in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_is_dead_alone_is_a_terminal_sample_because_the_entity_may_be_destroyed_first():
    """The OR is not laziness. HealthConstants.DestroyOnDeath exists, so the
    entity may vanish before a zero sample lands."""
    rows = _clean_series()
    rows[-1]["health_value"] = 400.0
    rows[-1]["is_dead"] = True
    assert "no_terminal_sample" not in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_a_gap_over_three_tick_intervals_discards_the_run():
    """A larger gap means the tick stalled and the series cannot be integrated."""
    rows = _clean_series()
    rows[4]["captured_at"] = ar.stamp(4 * ar.TICK_INTERVAL_S + 1.0)
    for i in range(5, len(rows)):
        rows[i]["captured_at"] = ar.stamp(i * ar.TICK_INTERVAL_S + 1.0)
    assert "tick_gap_exceeded" in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_the_gap_threshold_follows_the_OBSERVED_cadence_not_a_hardcoded_750_ms():
    """MEASURED 2026-08-01 on a live dedicated server: the sample interval is
    min 0.500 s, median 0.502 s, max 0.503 s over n=55. That is 1.99 Hz, not the
    4 Hz both specs assert - SampleEveryFrames = 15 is right, but the dedicated
    server runs at 29.9 fps under -batchMode -nographics, so 15 frames is 502 ms.
    The 4 Hz figure was inferred from an ASSUMED 60 fps and has never been
    measured on either host.

    The rule is "no gap greater than 3 TICK INTERVALS". The parenthesised
    "about 750 ms" is only true at 4 Hz, so hardcoding it would discard a 2 Hz
    run for a single stalled tick that the actual rule permits.
    """
    slow = 0.5
    wire = [_wire_sample(i, 8107.0 - i, captured_at=ar.stamp(i * slow)) for i in range(8)]
    wire[-1]["is_dead"] = True
    wire[-1]["health_value"] = 0.0

    within = ar.translate_samples(wire, {})
    for i in range(4, len(within)):
        within[i]["captured_at"] = ar.stamp(i * slow + 0.9)  # a 1.4 s gap, under 3 x 0.5
    assert "tick_gap_exceeded" not in ar.check_run(within, DRACULA, _manifest())["reasons"]

    beyond = ar.translate_samples(wire, {})
    for i in range(4, len(beyond)):
        beyond[i]["captured_at"] = ar.stamp(i * slow + 1.1)  # a 1.6 s gap, over it
    assert "tick_gap_exceeded" in ar.check_run(beyond, DRACULA, _manifest())["reasons"]


def test_the_validity_result_states_the_cadence_the_run_was_taken_at():
    """A run that does not say what rate it was taken at cannot be compared with
    one taken on the other host - the cycle 2 lesson exactly, where a real
    measurement answered the right question about the wrong subject."""
    slow = 0.5
    wire = [_wire_sample(i, 8107.0 - i, captured_at=ar.stamp(i * slow)) for i in range(8)]
    wire[-1]["is_dead"] = True
    rows = ar.translate_samples(wire, {})
    result = ar.check_run(rows, DRACULA, _manifest())
    assert result["observed_sample_interval_s_median"] == pytest.approx(slow)
    assert result["observed_sample_rate_hz"] == pytest.approx(2.0)
    assert result["gap_threshold_s"] == pytest.approx(3 * slow)


def test_a_series_too_short_to_have_an_interval_states_an_unknown_cadence():
    """Sourced from the series or ABSENT. There is no nominal rate to fall back
    on: the 4 Hz figure is unmeasured on both hosts."""
    rows = ar.translate_samples([_wire_sample(0, 8107.0, is_dead=True)], {})
    result = ar.check_run(rows, DRACULA, _manifest())
    assert result["observed_sample_rate_hz"] is None
    assert "tick_gap_exceeded" not in result["reasons"]


def test_stamps_carry_millisecond_resolution():
    """The wire stamps yyyy-MM-ddTHH:mm:ss.fffZ. The envelope's whole-second
    stamp gave four consecutive samples the same instant and destroyed every
    timing derived from the series."""
    assert ar.stamp(1.25) == "2026-01-01T00:00:01.250Z"
    assert ar.parse_stamp("2026-08-01T17:39:23.422Z").microsecond == 422000


def test_exactly_three_tick_intervals_is_within_tolerance():
    rows = _clean_series()
    for i in range(4, len(rows)):
        rows[i]["captured_at"] = ar.stamp(i * ar.TICK_INTERVAL_S + 2 * ar.TICK_INTERVAL_S)
    assert "tick_gap_exceeded" not in ar.check_run(rows, DRACULA, _manifest())["reasons"]


def test_an_incomplete_manifest_discards_the_run_and_names_the_field():
    """A.5.6, and it names the field rather than saying 'incomplete', because a
    discarded run is recorded WITH ITS REASON and never repaired."""
    manifest = _manifest()
    del manifest["difficulty"]
    reasons = ar.check_run(_clean_series(), DRACULA, manifest)["reasons"]
    assert "manifest_incomplete:difficulty" in reasons


def test_the_two_declared_holes_do_not_make_a_manifest_incomplete():
    """equipped_item_guids and jewels_and_passives are DECLARED holes, not
    defaulted fields. A run without them is still valid; it is simply not
    comparable, which the embargo enforces on its own."""
    reasons = ar.check_run(_clean_series(), DRACULA, _manifest())["reasons"]
    assert not [r for r in reasons if r.startswith("manifest_incomplete")]


def test_a_discarded_run_records_every_reason_it_failed():
    rows = _clean_series()
    rows[0]["carries_prefab_marker"] = True
    rows[2]["prefab_guid"] = 1
    rows[-1]["is_dead"] = False
    rows[-1]["health_value"] = 9.0
    result = ar.check_run(rows, DRACULA, _manifest())
    assert set(result["reasons"]) >= {
        "carries_prefab_marker_true",
        "prefab_guid_mismatch",
        "no_terminal_sample",
    }


# ---------------------------------------------------------------------------
# 4. Isolated deltas. Bracketed by no-change on BOTH sides.
# ---------------------------------------------------------------------------


def _series_from_values(values: list[float]) -> list[dict]:
    return ar.translate_samples([_wire_sample(i, v) for i, v in enumerate(values)], {})


def test_an_isolated_delta_is_bracketed_by_no_change_on_each_side():
    rows = _series_from_values([100.0, 100.0, 90.0, 90.0, 80.0, 80.0])
    deltas = ar.isolated_deltas(rows)
    assert [d["delta"] for d in deltas] == [10.0, 10.0]
    assert [d["index"] for d in deltas] == [2, 4]


def test_a_run_of_consecutive_drops_yields_no_isolated_delta():
    """A 4 Hz series CANNOT isolate every hit: abilities with hits_per_cast up
    to 4 exist and several land inside one 250 ms window. The protocol does not
    attempt to attribute every delta - it refuses the ones it cannot."""
    rows = _series_from_values([100.0, 100.0, 90.0, 80.0, 70.0, 70.0])
    assert ar.isolated_deltas(rows) == []


def test_a_drop_at_the_very_first_or_last_sample_is_not_isolated():
    """There is no bracketing sample on the missing side, so the window cannot
    be shown to contain exactly one ability application."""
    assert ar.isolated_deltas(_series_from_values([100.0, 90.0, 90.0, 90.0])) == []
    assert ar.isolated_deltas(_series_from_values([90.0, 90.0, 90.0, 80.0])) == []


def test_a_health_INCREASE_is_not_a_delta():
    """Passive regeneration is readable and is NOT part of the anchor-time
    model. A heal is not a hit."""
    assert ar.isolated_deltas(_series_from_values([80.0, 80.0, 100.0, 100.0])) == []


def test_isolated_deltas_ignore_samples_carrying_the_prefab_marker():
    rows = _series_from_values([100.0, 100.0, 90.0, 90.0])
    rows[2]["carries_prefab_marker"] = True
    assert ar.isolated_deltas(rows) == []


# ---------------------------------------------------------------------------
# 5. The writer. Atomic, validated, and it refuses to write an invalid table.
# ---------------------------------------------------------------------------


def test_write_anchor_validates_before_writing_and_refuses_an_invalid_envelope(tmp_path):
    envelope = ar.build_envelope(rows=[{"index": 0}], manifest=_manifest(), build=BUILD)
    with pytest.raises(ValueError) as excinfo:
        ar.write_anchor(envelope, tmp_path)
    assert "missing required field" in str(excinfo.value)
    assert list(tmp_path.iterdir()) == [], "nothing is written when validation fails"


def test_write_anchor_writes_one_file_named_for_the_run(tmp_path):
    manifest = _manifest()
    envelope = ar.build_envelope(
        rows=ar.translate_samples([_wire_sample(0, 8107.0)], {}),
        manifest=manifest,
        build=BUILD,
    )
    path = ar.write_anchor(envelope, tmp_path)
    assert path.name == f"{manifest['run_id']}.json"
    assert json.loads(path.read_text(encoding="utf-8"))["manifest"]["run_id"] == manifest["run_id"]
    assert not list(tmp_path.glob("*.tmp*")), "the temp file is replaced, not left behind"


def test_write_anchor_leaves_no_partial_file_a_consumer_could_poll(tmp_path):
    """CLAUDE.md atomic-write rule: temp file in the DESTINATION directory, then
    os.replace. Consumers poll mid-write."""
    envelope = ar.build_envelope(
        rows=ar.translate_samples([_wire_sample(0, 8107.0)], {}),
        manifest=_manifest(),
        build=BUILD,
    )
    ar.write_anchor(envelope, tmp_path)
    assert len(list(tmp_path.iterdir())) == 1


# ---------------------------------------------------------------------------
# 6. Degraded mode. A raw HTTP or API error never reaches the operator.
# ---------------------------------------------------------------------------


def test_a_bridge_error_envelope_becomes_a_friendly_message():
    friendly = ar.friendly_error({"ok": False, "error": "subject_not_spawned"})
    assert "subject_not_spawned" not in friendly
    assert "spawn" in friendly.lower()


def test_an_unknown_error_code_still_degrades_rather_than_leaking_the_raw_body():
    friendly = ar.friendly_error({"ok": False, "error": "HTTPError 500: <html>boom</html>"})
    assert "<html>" not in friendly
    assert "500" not in friendly
    assert friendly


def test_no_port_literal_is_written_anywhere_in_the_tool():
    """CLAUDE.md: never write a port literal, import from core/ports.py - and
    core/ports.py has an allowlist test that catches one even in a docstring."""
    from pathlib import Path

    source = (Path(ar.__file__)).read_text(encoding="utf-8")
    from core import ports

    for port in sorted(ports.ALL):
        assert str(port) not in source, f"port literal {port} in tools/anchor_record.py"

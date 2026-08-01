"""Tests for tools/rmdata_ingest.py, the bridge prefab-dump ingest.

Every test drives the tool through a tmp_path repo root. The real
data/rmdata tree is never touched, and no test needs a network: --from-file
is the operator's saved-dump path and it is also the test harness.
"""
import json

import pytest

from core.tables import TABLE_NAMES, TABLES_DIRNAME, load_schema
from tools import rmdata_ingest
from tools.rmdata_extract import seed_tables

BUILD = "9.9.9.9-r12345"
OTHER_BUILD = "8.8.8.8-r00001"


def good_tables():
    """Rows that pass BOTH the shallow gate and the deep nested gate."""
    return {
        "items": [
            {
                "prefab_guid": 101,
                "name": "Merciless Nightstalker",
                "localization_guid": "guid-item-1",
                "category": "weapon",
                "tier": 4,
                "gear_score": 42.5,
                "stats": [{"stat": "PhysicalPower", "modification": "Add", "value": 12.5},
                          {"stat": "AttackSpeed", "modification": "AddToBase", "value": 0.2}],
                "weapon_type": "sword",
                "ability_group_guids": [801, 802],
            },
            {
                "prefab_guid": 102,
                "name": "Dawnthorn Chestguard",
                "localization_guid": "guid-item-2",
                "category": "chest",
                "tier": 3,
                "gear_score": 30.0,
                "stats": [{"stat": "PhysicalPower", "modification": "Add", "value": 4.0},
                          {"stat": "MaxHealth", "modification": "Add", "value": 90.0}],
                "weapon_type": "",
                # ADR-006's shape, reused for the L1 link: an empty list says the
                # equip-buff chain RAN and this item grants nothing. A chest
                # granting no ability is the ordinary case, so the fixture
                # carries one rather than only the interesting weapon row.
                "ability_group_guids": [],
            },
        ],
        "abilities": [
            {
                "prefab_guid": 201,
                "name": "Chaos Volley",
                "school": "chaos",
                "slot": "spell",
                "cooldown": 8.0,
                "power_scaling": 1.25,
                "damage_type": "spell",
                "effects": [11, 12],
            }
        ],
        "vbloods": [
            {
                "prefab_guid": 301,
                "name": "Alpha Wolf",
                "level": 16,
                "max_health": 1200.0,
                "physical_power": 20.0,
                "spell_power": 0.0,
                # The four measured keys only. holy, silver, garlic and sun have
                # no unit-side field on this build and are omitted, never zeroed.
                "resistances": {"physical": 10.0, "spell": -5.0,
                                "fire": 0.0, "corruption": 0.0},
                "blood_type": "Warrior",
                "unlocks": [401, 402],
                "region": "Farbane Woods",
            }
        ],
        "blood_types": [
            {
                "prefab_guid": 401,
                "name": "Warrior",
                "localization_guid": "guid-blood-1",
                "bonuses": [
                    {
                        "slot": "primary",
                        "tier": 1,
                        "buff_guid": 4011,
                        "buff_name": "AB_BloodBuff_Warrior_Tier1",
                        "stats": [{"stat": "PhysicalPower", "modification": "Add"}],
                        "value_source": "blood_quality_scaled_at_runtime",
                    },
                    {
                        "slot": "primary",
                        "tier": 2,
                        "buff_guid": 4012,
                        "buff_name": "AB_BloodBuff_Warrior_Tier2",
                        "stats": [
                            {"stat": "PhysicalPower", "modification": "Add"},
                            {"stat": "PhysicalCriticalStrikeChance", "modification": "Add"},
                        ],
                        "value_source": "blood_quality_scaled_at_runtime",
                    },
                ],
            }
        ],
        "recipes": [
            {
                "prefab_guid": 501,
                "output_guid": 101,
                "output_amount": 1,
                "ingredients": [
                    {"prefab_guid": 601, "amount": 8},
                    {"prefab_guid": 602, "amount": 4},
                ],
                "station_guids": [701],
                "craft_duration": 12.0,
            }
        ],
        # Two rows so the fixture covers BOTH measured shapes: a group that
        # reaches damage and carries coefficients, and one that reaches none and
        # therefore omits every coefficient field rather than zeroing it. Cycle 2
        # measured 912 of 1474 groups in the second case, so the omitting row is
        # the majority shape and not an edge case.
        "ability_stats": [
            {
                "prefab_guid": 801,
                "name": "AB_Spear_AThousandSpears_Stab_AbilityGroup",
                "is_weapon_ability": True,
                "ability_type": "Primary",
                "cast_time": 0.35,
                "post_cast_time": 0.1,
                "cooldown": 0.0,
                "global_cooldown": 1.5,
                "coefficient": 1.0,
                "raw_damage_value": 0.0,
                "raw_damage_percent": 0.0,
                "damage_type": "physical",
                "hits_per_cast": 1,
                "hit_triggers": 1,
                "gameplay_events_on_hit": 0,
                "spawn_prefabs_on_cast": 1,
                "damage_modifier_per_hit": 0.0,
                "multiply_main_factor_with_stacks": False,
            },
            {
                "prefab_guid": 802,
                "name": "AB_Spear_AThousandSpears_Travel_AbilityGroup",
                "is_weapon_ability": True,
                "ability_type": "Travel",
                "cast_time": 0.2,
                "post_cast_time": 0.0,
                "cooldown": 8.0,
                "global_cooldown": 1.5,
                "spawn_prefabs_on_cast": 1,
            },
        ],
    }


def dump_payload(build=BUILD, tables=None, unmapped=None):
    """A /dump/prefabs response, shaped per the spec section 6 example."""
    tables = good_tables() if tables is None else tables
    return {
        "ok": True,
        "build": build,
        "plugin": "0.1.0",
        "captured_at": "2026-07-26T18:07:52Z",
        "elapsed_ms": 37,
        "counts": {name: len(tables.get(name, [])) for name in TABLE_NAMES},
        "tables": tables,
        "unmapped": [
            {"prefab_guid": 900, "reason": "no recognised stat component"},
            {"prefab_guid": 901, "reason": "no recognised stat component"},
            {"prefab_guid": 902, "reason": "unknown category"},
        ]
        if unmapped is None
        else unmapped,
    }


@pytest.fixture
def repo(tmp_path):
    """A tmp repo root with data/rmdata/current.txt and a seeded tables dir."""
    root = tmp_path / "repo"
    build_dir = root / "data" / "rmdata" / BUILD
    (build_dir / TABLES_DIRNAME).mkdir(parents=True)
    (root / "data" / "rmdata" / "current.txt").write_text(BUILD + "\n", encoding="utf-8")
    seed_tables(build_dir, BUILD)
    return root


def write_dump(tmp_path, payload):
    path = tmp_path / "dump.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def run(repo_root, dump_path, *extra):
    return rmdata_ingest.main(
        ["--repo", str(repo_root), "--from-file", str(dump_path), *extra]
    )


def tables_dir(repo_root, build=BUILD):
    return repo_root / "data" / "rmdata" / build / TABLES_DIRNAME


def incoming_dir(repo_root, build=BUILD):
    return tables_dir(repo_root, build) / rmdata_ingest.INCOMING_DIRNAME


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_rows_are_wrapped_in_the_frozen_core_tables_envelope(repo, tmp_path):
    """The envelope comes from core.tables.empty_table, never hand-built."""
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump) == 0

    quarantined = read_json(incoming_dir(repo) / "items.json")
    assert quarantined["table"] == "items"
    assert quarantined["build"] == BUILD
    assert quarantined["schema_version"] == load_schema("items")["schema_version"]
    assert [row["prefab_guid"] for row in quarantined["rows"]] == [101, 102]
    assert set(quarantined) == {"table", "build", "schema_version", "rows"}


def test_build_mismatch_is_refused_and_nothing_is_written(repo, tmp_path, capsys):
    """A dump from a silently-updated game must never land in the old build dir."""
    dump = write_dump(tmp_path, dump_payload(build=OTHER_BUILD))
    assert run(repo, dump) != 0

    captured = capsys.readouterr()
    assert OTHER_BUILD in captured.err and BUILD in captured.err
    assert not incoming_dir(repo).exists()
    for name in TABLE_NAMES:
        assert read_json(tables_dir(repo) / f"{name}.json")["rows"] == []


def test_without_accept_only_the_quarantine_path_is_written(repo, tmp_path):
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump) == 0

    assert read_json(incoming_dir(repo) / "items.json")["rows"]
    for name in TABLE_NAMES:
        assert read_json(tables_dir(repo) / f"{name}.json")["rows"] == []


def test_accept_promotes_the_quarantined_content_atomically(repo, tmp_path):
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump, "--accept") == 0

    for name in TABLE_NAMES:
        live = read_json(tables_dir(repo) / f"{name}.json")
        assert live == read_json(incoming_dir(repo) / f"{name}.json")
        assert len(live["rows"]) == len(good_tables()[name])
    # Atomic means temp-then-replace: no .tmp debris is left behind.
    assert not list(tables_dir(repo).glob("*.tmp"))
    assert read_json(tables_dir(repo) / "items.json")["rows"][0]["name"] == (
        "Merciless Nightstalker"
    )


def test_a_shallow_gate_failure_is_not_promoted(repo, tmp_path, capsys):
    tables = good_tables()
    tables["items"][0]["tier"] = "four"  # declared integer
    dump = write_dump(tmp_path, dump_payload(tables=tables))

    assert run(repo, dump, "--accept") != 0
    assert "tier" in capsys.readouterr().err
    assert read_json(tables_dir(repo) / "items.json")["rows"] == []


def test_a_deep_gate_failure_is_not_promoted(repo, tmp_path, capsys):
    """THE hazard the deep gate exists for.

    core.tables.validate_table is SHALLOW. It confirms recipes.ingredients is a
    list and stops there - it cannot see that an entry's amount is a string
    rather than an integer. These rows therefore PASS the shallow gate and a
    green validate_table would have promoted structurally broken data into the
    live table path. core.table_deep.deep_problems is what catches it, so this
    test asserts the shallow gate is clean AND the run still refuses.
    """
    tables = good_tables()
    tables["recipes"][0]["ingredients"] = [{"prefab_guid": 601, "amount": "eight"}]
    dump = write_dump(tmp_path, dump_payload(tables=tables))

    from core.table_deep import deep_problems
    from core.tables import validate_table

    envelope = {
        "table": "recipes",
        "build": BUILD,
        "schema_version": load_schema("recipes")["schema_version"],
        "rows": tables["recipes"],
    }
    assert validate_table(envelope, load_schema("recipes")) == []  # shallow is blind
    assert deep_problems("recipes", envelope)  # deep is not

    assert run(repo, dump, "--accept") != 0
    assert "ingredients" in capsys.readouterr().err
    assert read_json(tables_dir(repo) / "recipes.json")["rows"] == []


def test_census_reports_observed_nested_key_sets_and_numeric_ranges():
    census = rmdata_ingest.shape_census(good_tables())

    # items.stats became a list of {stat, modification, value} at schema_version
    # 2, so the census now reports the ENTRY keys rather than stat names as keys.
    # The census still earns its keep: it is what showed the real dump carries
    # three modification kinds, which is why the schema changed at all.
    stats = census["items"]["stats"]
    assert set(stats["keys"]) == {"stat", "modification", "value"}
    assert stats["keys"]["value"]["min"] == 0.2
    assert stats["keys"]["value"]["max"] == 90.0
    assert stats["keys"]["value"]["count"] == 4
    assert stats["keys"]["stat"]["types"] == ["str"]
    assert stats["cardinality"] == {"min": 2, "max": 2, "total": 4}

    ingredients = census["recipes"]["ingredients"]
    assert set(ingredients["keys"]) == {"prefab_guid", "amount"}
    assert ingredients["keys"]["amount"]["min"] == 4
    assert ingredients["keys"]["amount"]["max"] == 8
    assert ingredients["entry_kinds"] == ["dict"]

    # A container nested one level inside a list of objects is censused too.
    # MEASURED shape: stats is a LIST of {stat, modification} with no magnitude,
    # so the census reports its cardinality and entry keys, not a value range.
    nested = census["blood_types"]["bonuses[].stats"]
    assert nested["cardinality"]["total"] == 3
    assert set(nested["keys"]) == {"stat", "modification"}

    effects = census["abilities"]["effects"]
    assert effects["entry_kinds"] == ["int"]
    assert effects["cardinality"]["total"] == 2


def test_census_output_is_printed(repo, tmp_path, capsys):
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump) == 0
    out = capsys.readouterr().out
    assert "modification" in out
    assert "ingredients" in out


def test_unmapped_is_reported_with_its_length(repo, tmp_path, capsys):
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump) == 0
    out = capsys.readouterr().out
    assert "unmapped" in out
    assert "3" in out

    summary = rmdata_ingest.unmapped_summary(dump_payload())
    assert summary["count"] == 3
    assert summary["sample"][0]["prefab_guid"] == 900


def test_table_filter_ingests_only_that_table(repo, tmp_path):
    dump = write_dump(tmp_path, dump_payload())
    assert run(repo, dump, "--table", "items", "--accept") == 0

    assert read_json(tables_dir(repo) / "items.json")["rows"]
    assert read_json(tables_dir(repo) / "recipes.json")["rows"] == []


def test_seed_tables_leaves_a_populated_table_and_the_incoming_dir_alone(tmp_path):
    """Constructed and RUN, not read off rmdata_extract.py lines 126 to 128.

    That loop deletes any file in tables/ whose stem is not a known table name.
    It guards on path.is_file(), so the _incoming DIRECTORY should survive, and
    an already-populated table file should be skipped by the earlier loop.
    """
    build_dir = tmp_path / "data" / "rmdata" / BUILD
    tables = build_dir / TABLES_DIRNAME
    incoming = tables / rmdata_ingest.INCOMING_DIRNAME
    incoming.mkdir(parents=True)

    populated = {
        "table": "items",
        "build": BUILD,
        "schema_version": load_schema("items")["schema_version"],
        "rows": good_tables()["items"],
    }
    (tables / "items.json").write_text(json.dumps(populated), encoding="utf-8")
    (incoming / "items.json").write_text(json.dumps(populated), encoding="utf-8")
    (tables / "leftover_old_schema.json").write_text("{}", encoding="utf-8")

    seed_tables(build_dir, BUILD)

    assert read_json(tables / "items.json") == populated
    assert incoming.is_dir()
    assert read_json(incoming / "items.json") == populated
    assert not (tables / "leftover_old_schema.json").exists()


def test_bridge_unreachable_is_a_clean_nonzero_exit(repo, monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise rmdata_ingest.BridgeUnreachable("bridge unreachable: no client bridge answered")

    monkeypatch.setattr(rmdata_ingest, "get_json", boom)

    assert rmdata_ingest.main(["--repo", str(repo), "--host", "client"]) != 0
    captured = capsys.readouterr()
    assert "bridge" in captured.err.lower()
    assert "Traceback" not in captured.err
    assert not incoming_dir(repo).exists()


# ---------------------------------------------------------------------------
# the localization join census
#
# MEASURED on the dedicated server: 0 of 425 equippables resolve through
# ManagedDataRegistry (BRIDGE_SPIKES.md, section E). Whether the CLIENT host
# registers the managed data is a per-host question, so the dump must CARRY its
# own join counters and the ingest must print them. Reading a plugin log to find
# out whether a field is writable on this host is not a contract.
# ---------------------------------------------------------------------------


def test_localization_summary_reports_a_missing_block_as_owed():
    """A dump with no localization block is a dumper that owes the counters.

    Same rule as unmapped: absent is reported, never silently treated as zero.
    """
    summary = rmdata_ingest.localization_summary({})

    assert summary["present"] is False
    lines = rmdata_ingest.format_localization(summary)
    assert any("MISSING" in line for line in lines)


def test_localization_summary_reports_a_measured_absence_without_calling_it_an_error():
    """registry present, 0 of 425 resolved - the measured server-host result.

    This is a FINDING, not a failure, and the census must not read as one.
    """
    summary = rmdata_ingest.localization_summary(
        {
            "localization": {
                "registry": "present",
                "attempted": 425,
                "resolved": 0,
                "empty_key": 0,
                "missed": 425,
                "quiet_hits": 0,
            }
        }
    )

    assert summary["present"] is True
    assert summary["attempted"] == 425
    assert summary["resolved"] == 0
    assert summary["rate"] == 0.0
    assert summary["writable"] is False

    text = " ".join(rmdata_ingest.format_localization(summary))
    assert "0 of 425" in text
    assert "registry=present" in text
    # the without-logging control belongs in the operator's line, because it is
    # what separates "not registered" from "the logging path refused it"
    assert "quiet_hits=0" in text


def test_localization_summary_reports_a_working_join_as_writable():
    summary = rmdata_ingest.localization_summary(
        {
            "localization": {
                "registry": "present",
                "attempted": 425,
                "resolved": 425,
                "empty_key": 0,
                "missed": 0,
                "quiet_hits": 0,
            }
        }
    )

    assert summary["rate"] == 1.0
    assert summary["writable"] is True
    assert "425 of 425" in " ".join(rmdata_ingest.format_localization(summary))


def test_localization_summary_survives_zero_attempts():
    """A table-filtered dump attempts nothing. No divide by zero, no rate."""
    summary = rmdata_ingest.localization_summary(
        {"localization": {"registry": "absent", "attempted": 0, "resolved": 0}}
    )

    assert summary["rate"] is None
    assert summary["writable"] is False
    assert "registry=absent" in " ".join(rmdata_ingest.format_localization(summary))


def test_localization_census_is_printed_by_a_real_ingest(repo, capsys):
    """The counters reach the operator through the ingest, not through a log."""
    payload = dump_payload()
    payload["localization"] = {
        "registry": "present",
        "attempted": 2,
        "resolved": 2,
        "empty_key": 0,
        "missed": 0,
        "quiet_hits": 0,
    }
    dump = repo / "dump.json"
    dump.write_text(json.dumps(payload), encoding="utf-8")

    rmdata_ingest.main(["--repo", str(repo), "--from-file", str(dump), "--accept"])

    assert "2 of 2" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# prefab_guid uniqueness
#
# MEASURED 2026-07-26 on both hosts: the dump emitted 56 ability rows over 54
# distinct prefab_guids (AB_Blood_BloodRite_AbilityGroup and
# AB_Blood_Shadowbolt_AbilityGroup twice each) and the SERVER emitted 66 vblood
# rows over 65 distinct (CHAR_Vampire_Dracula_VBlood twice). The duplicate rows
# were byte-identical, so nothing downstream would have raised - the count was
# simply wrong, and 66 had already been written into ROADMAP.md as the V Blood
# total.
#
# prefab_guid is the join key every cycle 3 consumer will use. A table that
# repeats it is broken whether or not the repeated rows agree.
# ---------------------------------------------------------------------------


def test_duplicate_prefab_guid_is_a_gate_failure_even_when_rows_are_identical():
    rows = good_tables()["items"]
    duplicated = rows + [dict(rows[0])]

    problems = rmdata_ingest.duplicate_key_problems({"items": duplicated})

    assert problems, "an exactly repeated prefab_guid passed the gate"
    assert "101" in " ".join(problems)
    assert "items" in " ".join(problems)


def test_distinct_prefab_guids_pass_the_uniqueness_gate():
    assert rmdata_ingest.duplicate_key_problems(good_tables()) == []


def test_rows_without_a_prefab_guid_are_not_folded_together():
    """A missing key is the shallow gate's problem to report, not this one's.
    Treating two absent keys as a collision would mask the real error."""
    assert rmdata_ingest.duplicate_key_problems({"items": [{}, {}]}) == []


def test_a_duplicated_row_fails_a_real_ingest_and_nothing_is_promoted(repo):
    payload = dump_payload()
    payload["tables"]["vbloods"] = payload["tables"]["vbloods"] + [
        dict(payload["tables"]["vbloods"][0])
    ]
    dump = repo / "dump.json"
    dump.write_text(json.dumps(payload), encoding="utf-8")

    code = rmdata_ingest.main(["--repo", str(repo), "--from-file", str(dump), "--accept"])

    assert code != 0
    promoted = repo / "data" / "rmdata" / BUILD / TABLES_DIRNAME / "vbloods.json"
    assert read_json(promoted)["rows"] == [], "a duplicated dump was promoted anyway"

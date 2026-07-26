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
                "resistances": {"fire": 10.0, "holy": -5.0},
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
                "station_guid": 701,
                "craft_duration": 12.0,
            }
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

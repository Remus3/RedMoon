import json

import pytest

from core.table_deep import deep_problems
from core.tables import (
    SCHEMA_DIR,
    TABLE_NAMES,
    empty_table,
    load_schema,
    validate_table,
)


def test_every_declared_table_has_a_schema_file():
    for name in TABLE_NAMES:
        assert (SCHEMA_DIR / f"{name}.schema.json").is_file(), f"missing schema for {name}"


EXPECTED_SCHEMA_VERSIONS = {
    "items": 4,
    "abilities": 1,
    "vbloods": 2,
    "blood_types": 2,
    "recipes": 2,
    "ability_stats": 1,
}


def test_every_table_has_a_pinned_schema_version():
    assert sorted(EXPECTED_SCHEMA_VERSIONS) == sorted(TABLE_NAMES)


def test_items_tier_is_declared_but_not_required():
    """
    items.tier was FABRICATED as 0 on every one of the 425 rows in the first
    real dump. An exhaustive field scan across all 169 interop assemblies for
    build 1.1.13.0-r99712 returned 67 Tier-shaped fields and ZERO on a
    per-item-prefab component; Rarity returns zero hits anywhere in ProjectM,
    and ProjectM.ItemData, the real item-definition component, has no tier.
    So no real source exists on this build.

    The field stays DECLARED because validate_table rejects UNDECLARED fields
    and several fixtures still pass a tier. It stops being REQUIRED so the
    dumper can omit it, the way localization_guid and station_guid are already
    omitted, rather than emit a placeholder a cycle 3 consumer would read as
    real. The rejected near-miss is recorded in the schema description:
    ArmorLevelSource.Level is exactly 10x tier on 117 of 425 rows, but that
    divisor is calibrated against the _T0x name token, the value is already
    emitted as gear_score, and headgear, cloaks and bags carry no level
    component at all.
    """
    schema = load_schema("items")
    assert "tier" not in schema["required"], "tier has no measured source and must not be required"
    assert "tier" in schema["fields"], "tier must stay declared or validate_table rejects fixtures"


def test_items_row_without_tier_validates():
    schema = load_schema("items")
    table = empty_table("items", "1.1.13.0-r99712")
    table["rows"] = [{"prefab_guid": 1, "name": "Copper Sword", "category": "weapon"}]
    assert validate_table(table, schema) == []


def test_items_localization_guid_is_declared_optional():
    """
    MEASURED: the prefab-to-localization join does not exist offline. All 8379
    strings.json keys are dashed UUIDs; zero of 425 item rows join by prefab
    name, by prefab_guid in decimal, or in any of six hex forms. The join is a
    runtime read through GameDataSystem.ManagedDataRegistry, so the field stays
    optional and is omitted until the dumper can perform that read.
    """
    schema = load_schema("items")
    assert "localization_guid" in schema["fields"]
    assert "localization_guid" not in schema["required"]


def test_no_stray_schema_files():
    on_disk = sorted(p.name.removesuffix(".schema.json") for p in SCHEMA_DIR.glob("*.schema.json"))
    assert on_disk == sorted(TABLE_NAMES)


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_schema_shape(name):
    schema = load_schema(name)
    assert schema["table"] == name
    # Pinned per table rather than a blanket 1, so a bump is a deliberate edit
    # here and an accidental one still fails. items went to 2 on 2026-07-26 when
    # the first real dump showed stats cannot be a name-to-number map.
    assert schema["schema_version"] == EXPECTED_SCHEMA_VERSIONS[name]
    assert isinstance(schema["fields"], dict) and schema["fields"]
    assert isinstance(schema["required"], list) and schema["required"]
    for field in schema["required"]:
        assert field in schema["fields"], f"{name}: required field {field} is not declared"
    for field, spec in schema["fields"].items():
        assert spec["type"] in {"string", "number", "integer", "boolean", "array", "object"}
        assert spec["description"].strip(), f"{name}.{field} has no description"


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_empty_table_validates(name):
    table = empty_table(name, "1.1.13.0-r99712")
    assert table["rows"] == []
    assert validate_table(table, load_schema(name)) == []


def test_validate_table_rejects_a_missing_required_field():
    schema = load_schema("items")
    table = empty_table("items", "1.1.13.0-r99712")
    table["rows"] = [{"prefab_guid": 1}]
    problems = validate_table(table, schema)
    assert problems
    assert any("name" in problem for problem in problems)


def test_validate_table_rejects_a_wrong_type():
    schema = load_schema("items")
    table = empty_table("items", "1.1.13.0-r99712")
    row = {field: "x" for field in schema["required"]}
    row["prefab_guid"] = "not an integer"
    table["rows"] = [row]
    problems = validate_table(table, schema)
    assert any("prefab_guid" in problem for problem in problems)


def test_validate_table_rejects_a_bad_envelope():
    schema = load_schema("items")
    problems = validate_table({"rows": []}, schema)
    assert any("build" in problem for problem in problems)


def test_schema_files_are_ascii():
    for path in SCHEMA_DIR.glob("*.schema.json"):
        text = path.read_text(encoding="utf-8")
        assert all(ord(c) <= 127 for c in text), f"{path.name} is not ascii"
        json.loads(text)


# ---------------------------------------------------------------------------
# recipes.station_guids - ADR-006
# ---------------------------------------------------------------------------


def test_recipes_station_field_is_plural_at_schema_version_2():
    """ADR-006. MEASURED: 35 WorkstationRecipesBuffer prefabs hold 693 recipe
    references and 23 RefinementstationRecipesBuffer prefabs hold 249, which is
    942 references over 663 recipes. A recipe appears at several stations, so a
    single integer cannot hold the answer and a first-station-wins value would be
    indistinguishable from a measured one."""
    schema = load_schema("recipes")

    assert schema["schema_version"] == 2
    assert "station_guid" not in schema["fields"], (
        "the singular station_guid survives, so a consumer can still read it"
    )
    assert schema["fields"]["station_guids"]["type"] == "array"
    assert "station_guids" not in schema["required"], (
        "a recipe reachable from no station is real and must still validate"
    )


def test_a_recipe_row_carrying_many_stations_passes_both_gates():
    row = {
        "prefab_guid": 401,
        "output_guid": 402,
        "output_amount": 1,
        "ingredients": [{"prefab_guid": 403, "amount": 8}],
        "station_guids": [-1937548008, 1922056553],
        "craft_duration": 10.0,
    }
    envelope = empty_table("recipes", "9.9.9.9-r12345")
    envelope["rows"] = [row]

    assert validate_table(envelope, load_schema("recipes")) == []
    assert deep_problems("recipes", envelope) == []


def test_an_empty_station_list_is_valid_and_is_not_the_same_as_the_field_missing():
    """ADR-006 decision 2: an empty array says "measured, reachable from no
    station". A missing field says "not measured". Collapsing them would make
    the inversion unfalsifiable."""
    base = {
        "prefab_guid": 401,
        "output_guid": 402,
        "ingredients": [],
    }
    for rows in ([dict(base, station_guids=[])], [dict(base)]):
        envelope = empty_table("recipes", "9.9.9.9-r12345")
        envelope["rows"] = rows
        assert validate_table(envelope, load_schema("recipes")) == []

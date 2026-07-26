import json

import pytest

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
    "items": 2,
    "abilities": 1,
    "vbloods": 1,
    "blood_types": 1,
    "recipes": 1,
}


def test_every_table_has_a_pinned_schema_version():
    assert sorted(EXPECTED_SCHEMA_VERSIONS) == sorted(TABLE_NAMES)


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

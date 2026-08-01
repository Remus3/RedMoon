"""Typed table registry for extracted game data.

Cycle 1 ships schemas and empty tables. The cycle 2 bridge prefab dump fills the
rows, and every write must pass validate_table first. See ADR-002.
"""
from __future__ import annotations

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "data" / "schemas"

TABLE_NAMES = ("items", "abilities", "vbloods", "blood_types", "recipes", "ability_stats")
"""Every table the extractor seeds and the ingest gate knows about.

ability_stats joined at cycle 3 phase 2. It is a SEPARATE table from abilities
rather than more columns on it, because the two have different key spaces:
abilities is keyed on the ability GROUP that a spell-school asset names, and
covers spell-school abilities only, while ability_stats is keyed on the ability
GROUP for EVERY group that reaches damage, weapon groups included. See ADR-007.
"""

TABLES_DIRNAME = "tables"
"""Subdirectory of data/rmdata/<build>/ holding one JSON file per table.

tools/rmdata_extract.extract creates it and seeds an empty envelope per table
name, so the path the cycle 2 bridge dumps into already exists and already has
the envelope shape. See docs/BLOODFORGE.md for the consumer side.
"""

_TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


def load_schema(name: str) -> dict:
    """Load the schema document for a table."""
    if name not in TABLE_NAMES:
        raise KeyError(f"unknown table {name!r}")
    path = SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def empty_table(name: str, build: str) -> dict:
    """Return a valid, empty table envelope for a build."""
    schema = load_schema(name)
    return {
        "table": name,
        "build": build,
        "schema_version": schema["schema_version"],
        "rows": [],
    }


def validate_table(table: dict, schema: dict) -> list[str]:
    """Return human-readable problems. An empty list means the table is valid."""
    problems: list[str] = []

    for key in ("table", "build", "schema_version", "rows"):
        if key not in table:
            problems.append(f"envelope is missing {key}")
    if problems:
        return problems

    if table["table"] != schema["table"]:
        problems.append(f"table is {table['table']!r}, schema is {schema['table']!r}")
    if table["schema_version"] != schema["schema_version"]:
        problems.append(
            f"schema_version is {table['schema_version']}, "
            f"schema declares {schema['schema_version']}"
        )
    if not isinstance(table["rows"], list):
        problems.append("rows is not a list")
        return problems

    fields = schema["fields"]
    for index, row in enumerate(table["rows"]):
        if not isinstance(row, dict):
            problems.append(f"row {index} is not an object")
            continue
        for field in schema["required"]:
            if field not in row:
                problems.append(f"row {index} is missing required field {field}")
        for field, value in row.items():
            spec = fields.get(field)
            if spec is None:
                problems.append(f"row {index} has undeclared field {field}")
                continue
            expected = _TYPE_MAP[spec["type"]]
            # bool is a subclass of int; never accept it as a number.
            if isinstance(value, bool) and spec["type"] in {"integer", "number"}:
                problems.append(f"row {index} field {field} is a boolean, expected {spec['type']}")
            elif not isinstance(value, expected):
                problems.append(
                    f"row {index} field {field} is {type(value).__name__}, "
                    f"expected {spec['type']}"
                )
    return problems

"""Nested-shape gate for extracted game tables.

core.tables.validate_table is a shallow gate: it type-checks top-level row
fields only. It confirms that recipes.ingredients is a list and that items.stats
is an object, but it cannot see inside either. Three of the five shipped schemas
carry an "UNVALIDATED NESTED SHAPE" note in their description saying exactly
that. This module promotes that prose into assertions.

Style mirrors validate_table: never raise on bad data, accumulate human-readable
problems, and name the row index in every message. A KeyError is raised only for
an unknown table name, matching load_schema.

Contracts asserted here:

1. recipes.ingredients   - list of objects, each with an integer prefab_guid and
                           an integer amount, and no undeclared keys.
2. blood_types.bonuses   - list of objects, each with a numeric quality
                           threshold and a stats mapping of name to number,
                           ordered by ascending quality.
3. items.stats           - object mapping string keys to numeric values, flat.
4. vbloods.resistances   - object mapping string keys to numeric values.
5. vbloods.unlocks and abilities.effects - lists of scalars of a single
                           consistent type across the list.

bool is a subclass of int in Python, so a boolean is never accepted where a
number or an integer is expected. core/tables.py line 88 guards the same trap at
the top level.

A nested field that is absent from a row is not this module's problem, and a
nested field whose top-level type is already wrong belongs to validate_table, so
both are skipped rather than reported.
"""
from __future__ import annotations

from collections.abc import Callable

from core.tables import TABLE_NAMES

INGREDIENT_KEYS = ("prefab_guid", "amount")
"""The only keys a recipes.ingredients entry may carry (recipes schema line 10)."""

BONUS_QUALITY_KEY = "quality"
BONUS_STATS_KEY = "stats"

SCALAR_LIST_TYPES = (int, str)
"""Scalar kinds a single-type list may hold. bool is rejected separately."""


def _is_number(value: object) -> bool:
    """True for an int or float that is not a bool."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_integer(value: object) -> bool:
    """True for an int that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _kind(value: object) -> str:
    """Type name for a problem message."""
    return type(value).__name__


def _check_number_mapping(index: int, field: str, value: object, problems: list[str]) -> None:
    """Assert value maps string keys to flat numeric values."""
    if not isinstance(value, dict):
        return  # validate_table owns the top-level type
    for key, entry in value.items():
        if not isinstance(key, str):
            problems.append(f"row {index} field {field} has a non-string key {key!r}")
            continue
        if isinstance(entry, (dict, list)):
            problems.append(
                f"row {index} field {field} key {key} is nested {_kind(entry)}, expected a number"
            )
        elif not _is_number(entry):
            problems.append(
                f"row {index} field {field} key {key} is {_kind(entry)}, expected a number"
            )


def _check_ingredients(index: int, field: str, value: object, problems: list[str]) -> None:
    """Assert every ingredient is an object of integer prefab_guid and amount."""
    if not isinstance(value, list):
        return
    for position, entry in enumerate(value):
        where = f"row {index} field {field}[{position}]"
        if not isinstance(entry, dict):
            problems.append(f"{where} is {_kind(entry)}, expected an object")
            continue
        for key in INGREDIENT_KEYS:
            if key not in entry:
                problems.append(f"{where} is missing {key}")
                continue
            if not _is_integer(entry[key]):
                problems.append(
                    f"{where} {key} is {_kind(entry[key])}, expected an integer"
                )
        for key in entry:
            if key not in INGREDIENT_KEYS:
                problems.append(f"{where} has undeclared key {key}")


def _check_bonuses(index: int, field: str, value: object, problems: list[str]) -> None:
    """Assert bonus tiers carry a numeric quality plus stats, ascending by quality."""
    if not isinstance(value, list):
        return
    thresholds: list[float] = []
    ordered = True
    for position, entry in enumerate(value):
        where = f"row {index} field {field}[{position}]"
        if not isinstance(entry, dict):
            problems.append(f"{where} is {_kind(entry)}, expected an object")
            ordered = False
            continue
        if BONUS_QUALITY_KEY not in entry:
            problems.append(f"{where} is missing {BONUS_QUALITY_KEY}")
            ordered = False
        elif not _is_number(entry[BONUS_QUALITY_KEY]):
            problems.append(
                f"{where} {BONUS_QUALITY_KEY} is {_kind(entry[BONUS_QUALITY_KEY])}, "
                f"expected a number"
            )
            ordered = False
        else:
            thresholds.append(float(entry[BONUS_QUALITY_KEY]))
        if BONUS_STATS_KEY not in entry:
            problems.append(f"{where} is missing {BONUS_STATS_KEY}")
        elif not isinstance(entry[BONUS_STATS_KEY], dict):
            problems.append(
                f"{where} {BONUS_STATS_KEY} is {_kind(entry[BONUS_STATS_KEY])}, "
                f"expected an object"
            )
        else:
            _check_number_mapping(
                index, f"{field}[{position}].{BONUS_STATS_KEY}", entry[BONUS_STATS_KEY], problems
            )
    if ordered and thresholds != sorted(thresholds):
        problems.append(
            f"row {index} field {field} thresholds {thresholds} do not ascend"
        )


def _check_scalar_list(index: int, field: str, value: object, problems: list[str]) -> None:
    """Assert the list holds scalars of one consistent type, all int or all str."""
    if not isinstance(value, list):
        return
    seen: set[str] = set()
    for position, entry in enumerate(value):
        where = f"row {index} field {field}[{position}]"
        if isinstance(entry, bool) or not isinstance(entry, SCALAR_LIST_TYPES):
            problems.append(f"{where} is {_kind(entry)}, expected an integer or a string")
            continue
        seen.add(_kind(entry))
    if len(seen) > 1:
        problems.append(
            f"row {index} field {field} mixes types {sorted(seen)}, expected one consistent type"
        )


_Check = Callable[[int, str, object, list[str]], None]

_CHECKS: dict[str, tuple[tuple[str, _Check], ...]] = {
    "recipes": (("ingredients", _check_ingredients),),
    "blood_types": (("bonuses", _check_bonuses),),
    "items": (("stats", _check_number_mapping),),
    "vbloods": (
        ("resistances", _check_number_mapping),
        ("unlocks", _check_scalar_list),
    ),
    "abilities": (("effects", _check_scalar_list),),
}


def deep_problems(name: str, table: dict) -> list[str]:
    """Return nested-shape problems for a table envelope.

    An empty list means every documented nested contract holds. Raises KeyError
    for an unknown table name, matching core.tables.load_schema.
    """
    if name not in TABLE_NAMES:
        raise KeyError(f"unknown table {name!r}")

    problems: list[str] = []
    rows = table.get("rows") if isinstance(table, dict) else None
    if not isinstance(rows, list):
        return problems  # validate_table owns a broken envelope

    checks = _CHECKS.get(name, ())
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            continue  # validate_table already reports a non-object row
        for field, check in checks:
            if field in row:
                check(index, field, row[field], problems)
    return problems

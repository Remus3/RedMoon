"""Tests for the nested-shape gate in core.table_deep.

core.tables.validate_table is shallow: it type-checks top-level row fields only.
Three shipped schemas say so in prose ("UNVALIDATED NESTED SHAPE"). These tests
pin the promoted assertions, one passing and one failing fixture per contract.
A validator with no negative test is a dead gate.
"""
import pytest

from core.table_deep import deep_problems
from core.tables import TABLE_NAMES, empty_table

BUILD = "1.1.13.0-r99712"

VALID_ROWS = {
    "items": {
        "prefab_guid": 1,
        "name": "Copper Sword",
        "category": "weapon",
        "tier": 1,
        "gear_score": 12.0,
        "stats": {"PhysicalPower": 3.0, "AttackSpeed": 0.1},
        "weapon_type": "sword",
    },
    "abilities": {
        "prefab_guid": 2,
        "name": "Chaos Volley",
        "school": "chaos",
        "effects": ["ignite", "knockback"],
    },
    "vbloods": {
        "prefab_guid": 3,
        "name": "Alpha Wolf",
        "level": 16,
        "resistances": {"fire": 10, "holy": 0.5},
        "unlocks": [101, 102],
    },
    "blood_types": {
        "prefab_guid": 4,
        "name": "Warrior",
        "bonuses": [
            {"quality": 0.0, "stats": {"PhysicalPower": 1.0}},
            {"quality": 30.0, "stats": {"PhysicalPower": 5.0}},
        ],
    },
    "recipes": {
        "prefab_guid": 5,
        "output_guid": 6,
        "output_amount": 1,
        "ingredients": [{"prefab_guid": 7, "amount": 4}],
        "craft_duration": 3.0,
    },
}


def _table(name: str, *rows: dict) -> dict:
    table = empty_table(name, BUILD)
    table["rows"] = list(rows)
    return table


def _second_row_table(name: str, bad_row: dict) -> dict:
    """A clean row at index 0 and the offending row at index 1.

    Every negative test asserts "row 1" appears in a problem, so a test cannot
    pass on an unrelated problem raised against the clean row.
    """
    return _table(name, dict(VALID_ROWS[name]), bad_row)


def _assert_flags_row_1(problems: list[str]) -> None:
    assert problems, "expected at least one problem, got a clean result"
    assert any("row 1" in problem for problem in problems), problems


# --- framing -----------------------------------------------------------------


def test_unknown_table_name_raises_key_error():
    with pytest.raises(KeyError):
        deep_problems("not_a_table", empty_table("items", BUILD))


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_clean_empty_rows_table_returns_empty(name):
    assert deep_problems(name, empty_table(name, BUILD)) == []


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_valid_row_of_every_table_returns_empty(name):
    assert deep_problems(name, _table(name, VALID_ROWS[name])) == []


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_absent_nested_field_is_not_a_problem(name):
    row = {"prefab_guid": 1, "name": "bare"}
    assert deep_problems(name, _table(name, row)) == []


@pytest.mark.parametrize("name", TABLE_NAMES)
def test_wrong_top_level_nested_type_does_not_crash(name):
    """validate_table owns this; deep_problems must not raise on it."""
    row = dict(VALID_ROWS[name])
    for field in ("ingredients", "bonuses", "stats", "resistances", "unlocks", "effects"):
        if field in row:
            row[field] = 12345
    assert isinstance(deep_problems(name, _table(name, row)), list)


def test_rows_that_are_not_objects_do_not_crash():
    table = _table("items", "not a row")
    assert isinstance(deep_problems("items", table), list)


def test_missing_rows_key_does_not_crash():
    assert deep_problems("items", {"table": "items"}) == []


# --- contract 1: recipes.ingredients -----------------------------------------


def test_recipes_ingredients_valid_passes():
    row = dict(VALID_ROWS["recipes"])
    row["ingredients"] = [{"prefab_guid": 10, "amount": 2}, {"prefab_guid": 11, "amount": 40}]
    assert deep_problems("recipes", _table("recipes", row)) == []


def test_recipes_ingredient_missing_amount_is_caught():
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [{"prefab_guid": 10}]
    problems = deep_problems("recipes", _second_row_table("recipes", bad))
    _assert_flags_row_1(problems)
    assert any("amount" in problem for problem in problems), problems


def test_recipes_ingredient_amount_as_string_is_caught():
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [{"prefab_guid": 10, "amount": "4"}]
    problems = deep_problems("recipes", _second_row_table("recipes", bad))
    _assert_flags_row_1(problems)
    assert any("amount" in problem for problem in problems), problems


def test_recipes_ingredient_undeclared_key_is_caught():
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [{"prefab_guid": 10, "amount": 4, "quality": 3}]
    problems = deep_problems("recipes", _second_row_table("recipes", bad))
    _assert_flags_row_1(problems)
    assert any("quality" in problem for problem in problems), problems


def test_recipes_ingredient_that_is_not_an_object_is_caught():
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [10]
    _assert_flags_row_1(deep_problems("recipes", _second_row_table("recipes", bad)))


def test_recipes_ingredient_boolean_amount_is_caught():
    """bool is a subclass of int; it must never pass an integer check."""
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [{"prefab_guid": 10, "amount": True}]
    problems = deep_problems("recipes", _second_row_table("recipes", bad))
    _assert_flags_row_1(problems)
    assert any("amount" in problem for problem in problems), problems


def test_recipes_ingredient_boolean_prefab_guid_is_caught():
    bad = dict(VALID_ROWS["recipes"])
    bad["ingredients"] = [{"prefab_guid": False, "amount": 4}]
    problems = deep_problems("recipes", _second_row_table("recipes", bad))
    _assert_flags_row_1(problems)
    assert any("prefab_guid" in problem for problem in problems), problems


# --- contract 2: blood_types.bonuses -----------------------------------------


def test_blood_types_bonuses_valid_passes():
    row = dict(VALID_ROWS["blood_types"])
    row["bonuses"] = [
        {"quality": 0, "stats": {"PhysicalPower": 1}},
        {"quality": 30.5, "stats": {"PhysicalPower": 5.0, "SpellPower": 2}},
        {"quality": 100, "stats": {"PhysicalPower": 9.0}},
    ]
    assert deep_problems("blood_types", _table("blood_types", row)) == []


def test_blood_types_bonuses_out_of_threshold_order_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [
        {"quality": 30.0, "stats": {"PhysicalPower": 5.0}},
        {"quality": 10.0, "stats": {"PhysicalPower": 1.0}},
    ]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("ascend" in problem for problem in problems), problems


def test_blood_types_bonus_boolean_quality_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"quality": True, "stats": {"PhysicalPower": 1.0}}]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("quality" in problem for problem in problems), problems


def test_blood_types_bonus_boolean_stat_value_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"quality": 10.0, "stats": {"PhysicalPower": True}}]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("PhysicalPower" in problem for problem in problems), problems


def test_blood_types_bonus_stat_value_as_string_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"quality": 10.0, "stats": {"PhysicalPower": "5"}}]
    _assert_flags_row_1(deep_problems("blood_types", _second_row_table("blood_types", bad)))


def test_blood_types_bonus_missing_quality_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"stats": {"PhysicalPower": 5.0}}]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("quality" in problem for problem in problems), problems


def test_blood_types_bonus_stats_not_a_mapping_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"quality": 10.0, "stats": [1, 2]}]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("stats" in problem for problem in problems), problems


# --- contract 3: items.stats -------------------------------------------------


def test_items_stats_valid_passes():
    row = dict(VALID_ROWS["items"])
    row["stats"] = {"PhysicalPower": 3, "AttackSpeed": 0.125, "MaxHealth": -2.5}
    assert deep_problems("items", _table("items", row)) == []


def test_items_stats_string_value_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = {"PhysicalPower": "3.0"}
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("PhysicalPower" in problem for problem in problems), problems


def test_items_stats_nested_object_value_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = {"PhysicalPower": {"base": 3.0, "scaled": 4.0}}
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("PhysicalPower" in problem for problem in problems), problems


def test_items_stats_nested_list_value_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = {"PhysicalPower": [3.0]}
    _assert_flags_row_1(deep_problems("items", _second_row_table("items", bad)))


def test_items_stats_boolean_value_is_caught():
    """bool is a subclass of int; it must never pass a number check."""
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = {"PhysicalPower": True}
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("PhysicalPower" in problem for problem in problems), problems


def test_items_stats_non_string_key_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = {7: 3.0}
    _assert_flags_row_1(deep_problems("items", _second_row_table("items", bad)))


# --- contract 4: vbloods.resistances -----------------------------------------


def test_vbloods_resistances_valid_passes():
    row = dict(VALID_ROWS["vbloods"])
    row["resistances"] = {"fire": 10, "holy": 0.5, "garlic": -1}
    assert deep_problems("vbloods", _table("vbloods", row)) == []


def test_vbloods_resistances_string_value_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["resistances"] = {"fire": "ten"}
    problems = deep_problems("vbloods", _second_row_table("vbloods", bad))
    _assert_flags_row_1(problems)
    assert any("fire" in problem for problem in problems), problems


def test_vbloods_resistances_boolean_value_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["resistances"] = {"fire": False}
    problems = deep_problems("vbloods", _second_row_table("vbloods", bad))
    _assert_flags_row_1(problems)
    assert any("fire" in problem for problem in problems), problems


def test_vbloods_resistances_nested_value_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["resistances"] = {"fire": {"base": 10}}
    _assert_flags_row_1(deep_problems("vbloods", _second_row_table("vbloods", bad)))


# --- contract 5: single-type scalar lists ------------------------------------


def test_vbloods_unlocks_all_int_passes():
    row = dict(VALID_ROWS["vbloods"])
    row["unlocks"] = [101, 102, 103]
    assert deep_problems("vbloods", _table("vbloods", row)) == []


def test_vbloods_unlocks_all_str_passes():
    row = dict(VALID_ROWS["vbloods"])
    row["unlocks"] = ["AB_Blood_Volley", "AB_Blood_Rage"]
    assert deep_problems("vbloods", _table("vbloods", row)) == []


def test_vbloods_unlocks_mixed_type_list_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["unlocks"] = [101, "AB_Blood_Rage"]
    problems = deep_problems("vbloods", _second_row_table("vbloods", bad))
    _assert_flags_row_1(problems)
    assert any("unlocks" in problem for problem in problems), problems


def test_vbloods_unlocks_boolean_entry_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["unlocks"] = [101, True]
    _assert_flags_row_1(deep_problems("vbloods", _second_row_table("vbloods", bad)))


def test_vbloods_unlocks_non_scalar_entry_is_caught():
    bad = dict(VALID_ROWS["vbloods"])
    bad["unlocks"] = [{"prefab_guid": 101}]
    _assert_flags_row_1(deep_problems("vbloods", _second_row_table("vbloods", bad)))


def test_abilities_effects_all_str_passes():
    row = dict(VALID_ROWS["abilities"])
    row["effects"] = ["ignite", "knockback", "chill"]
    assert deep_problems("abilities", _table("abilities", row)) == []


def test_abilities_effects_mixed_type_list_is_caught():
    bad = dict(VALID_ROWS["abilities"])
    bad["effects"] = ["ignite", 42]
    problems = deep_problems("abilities", _second_row_table("abilities", bad))
    _assert_flags_row_1(problems)
    assert any("effects" in problem for problem in problems), problems


def test_abilities_effects_empty_list_passes():
    row = dict(VALID_ROWS["abilities"])
    row["effects"] = []
    assert deep_problems("abilities", _table("abilities", row)) == []

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
        "stats": [
            {"stat": "PhysicalPower", "modification": "Add", "value": 3.0},
            {"stat": "AttackSpeed", "modification": "AddToBase", "value": 0.1},
        ],
        "weapon_type": "sword",
        "ability_group_guids": [-1301247792, 900],
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
        # The four measured keys. holy, silver, garlic and sun have no
        # unit-side field on this build and are omitted rather than zeroed, so
        # the fixture does not show one. The gate itself polices value types and
        # deliberately not key NAMES: a future build adding a field is data.
        "resistances": {"physical": 10, "spell": 0.5, "fire": 0, "corruption": 0},
        "unlocks": [101, 102],
    },
    "ability_stats": {
        "prefab_guid": 8,
        "name": "AB_Spear_AThousandSpears_Stab_AbilityGroup",
        "is_weapon_ability": True,
        "cast_time": 0.35,
        "cooldown": 0.0,
        "coefficient": 1.0,
        "damage_type": "physical",
        "hits_per_cast": 1,
    },
    "blood_types": {
        "prefab_guid": 4,
        "name": "Warrior",
        "bonuses": [
            {"slot": "primary", "tier": 1, "buff_guid": 11,
             "buff_name": "AB_BloodBuff_Warrior_Tier1",
             "stats": [{"stat": "PhysicalPower", "modification": "Add"}],
             "value_source": "blood_quality_scaled_at_runtime"},
            {"slot": "primary", "tier": 2, "buff_guid": 12,
             "buff_name": "AB_BloodBuff_Warrior_Tier2",
             "stats": [{"stat": "PhysicalPower", "modification": "Add"}],
             "value_source": "blood_quality_scaled_at_runtime"},
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


def _bonus(**overrides) -> dict:
    """A measured-shape bonus entry: slot, 1-based tier, buff, stat NAMES."""
    entry = {
        "slot": "primary",
        "tier": 1,
        "buff_guid": 11,
        "buff_name": "AB_BloodBuff_Warrior_Tier1",
        "stats": [{"stat": "PhysicalPower", "modification": "Add"}],
        "value_source": "blood_quality_scaled_at_runtime",
    }
    entry.update(overrides)
    return entry


def test_blood_types_bonuses_valid_passes():
    row = dict(VALID_ROWS["blood_types"])
    row["bonuses"] = [
        _bonus(tier=1),
        _bonus(tier=2),
        _bonus(slot="secondary", tier=1),
        _bonus(slot="secondary", tier=2),
    ]
    assert deep_problems("blood_types", _table("blood_types", row)) == []


def test_blood_types_bonuses_out_of_tier_order_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [_bonus(tier=3), _bonus(tier=1)]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("ascend" in problem for problem in problems), problems


def test_blood_types_tiers_ascend_within_a_slot_not_across_the_list():
    """The measured row is primary 1..5 then secondary 1..4. A single global
    ascent check would reject real data, so this is a regression gate on the
    gate itself."""
    row = dict(VALID_ROWS["blood_types"])
    row["bonuses"] = [
        _bonus(tier=1), _bonus(tier=2), _bonus(tier=3), _bonus(tier=4), _bonus(tier=5),
        _bonus(slot="secondary", tier=1), _bonus(slot="secondary", tier=2),
    ]
    assert deep_problems("blood_types", _table("blood_types", row)) == []


def test_blood_types_bonus_boolean_tier_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [_bonus(tier=True)]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("tier" in problem for problem in problems), problems


def test_blood_types_bonus_unknown_slot_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [_bonus(slot="tertiary")]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("slot" in problem for problem in problems), problems


def test_blood_types_bonus_missing_buff_guid_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    entry = _bonus()
    del entry["buff_guid"]
    bad["bonuses"] = [entry]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("buff_guid" in problem for problem in problems), problems


def test_blood_types_bonus_stat_entry_missing_modification_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [_bonus(stats=[{"stat": "PhysicalPower"}])]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("modification" in problem for problem in problems), problems


def test_blood_types_bonus_numeric_stat_value_is_rejected():
    """schema_version 1 carried a name-to-number mapping. MEASURED: the prefab
    holds no magnitudes at all, so a number here is stale data, not a bonus."""
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [{"quality": 10.0, "stats": {"PhysicalPower": 5.0}}]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("quality" in problem for problem in problems), problems


def test_blood_types_bonus_stats_not_a_list_is_caught():
    bad = dict(VALID_ROWS["blood_types"])
    bad["bonuses"] = [_bonus(stats={"PhysicalPower": 1})]
    problems = deep_problems("blood_types", _second_row_table("blood_types", bad))
    _assert_flags_row_1(problems)
    assert any("stats" in problem for problem in problems), problems


# --- contract 3: items.stats -------------------------------------------------


def test_items_stats_valid_passes():
    row = dict(VALID_ROWS["items"])
    row["stats"] = [
        {"stat": "PhysicalPower", "modification": "Add", "value": 3},
        {"stat": "AttackSpeed", "modification": "AddToBase", "value": 0.125},
        {"stat": "MaxHealth", "modification": "MultiplyBaseAdd", "value": -2.5},
    ]
    assert deep_problems("items", _table("items", row)) == []


def test_an_item_with_no_stat_entries_passes():
    """MEASURED: 0 to 6 entries per item over 425 items, so an empty list is a
    real observation and not a broken read."""
    row = dict(VALID_ROWS["items"])
    row["stats"] = []
    assert deep_problems("items", _table("items", row)) == []


def test_items_stats_string_value_is_caught():
    """THE REGRESSION THIS BLOCK EXISTS FOR. items.stats became a LIST at
    schema_version 2 and the deep gate was not moved with it - it kept calling
    the object-shaped mapping check, which returns early on a list. Every one of
    these cases passed silently until 2026-08-01, while the schema description
    said validate_table was shallow and core/table_deep.py was what inspected
    the entries. Both gates were blind."""
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = [{"stat": "PhysicalPower", "modification": "Add", "value": "3.0"}]
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("value" in problem for problem in problems), problems


def test_items_stats_boolean_value_is_caught():
    """bool is a subclass of int; it must never pass a number check."""
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = [{"stat": "PhysicalPower", "modification": "Add", "value": True}]
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("value" in problem for problem in problems), problems


def test_items_stats_entry_that_is_not_an_object_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = ["PhysicalPower"]
    _assert_flags_row_1(deep_problems("items", _second_row_table("items", bad)))


def test_items_stats_missing_modification_is_caught():
    """The whole reason stats stopped being a map: PhysicalPower Add 10 and
    PhysicalPower AddToBase 10 are different stats a map renders identically.
    An entry that drops the modification has thrown away that distinction."""
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = [{"stat": "PhysicalPower", "value": 10.0}]
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("modification" in problem for problem in problems), problems


def test_items_stats_undeclared_key_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = [
        {"stat": "PhysicalPower", "modification": "Add", "value": 1.0, "softcap": 2.0}
    ]
    problems = deep_problems("items", _second_row_table("items", bad))
    _assert_flags_row_1(problems)
    assert any("softcap" in problem for problem in problems), problems


def test_items_stats_non_string_stat_name_is_caught():
    bad = dict(VALID_ROWS["items"])
    bad["stats"] = [{"stat": 7, "modification": "Add", "value": 1.0}]
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


# ---------------------------------------------------------------------------
# recipes.station_guids - ADR-006
# ---------------------------------------------------------------------------


def _recipes(rows):
    envelope = empty_table("recipes", BUILD)
    envelope["rows"] = rows
    return envelope


def _recipe(**extra):
    row = {"prefab_guid": 401, "output_guid": 402, "ingredients": []}
    row.update(extra)
    return row


def test_station_guids_accepts_a_sorted_integer_list():
    envelope = _recipes([_recipe(station_guids=[-1937548008, 1922056553])])
    assert deep_problems("recipes", envelope) == []


def test_station_guids_accepts_the_empty_list():
    """ADR-006: measured, reachable from no station. A real answer."""
    assert deep_problems("recipes", _recipes([_recipe(station_guids=[])])) == []


def test_station_guids_rejects_a_string_entry():
    """PrefabGUIDs are signed integers. A guid that arrives as text has been
    through a stringifying hop, which is exactly the corruption this gate is for."""
    problems = deep_problems("recipes", _recipes([_recipe(station_guids=["1922056553"])]))
    assert problems
    assert "station_guids[0]" in problems[0]


def test_station_guids_rejects_a_boolean_entry():
    """bool subclasses int in Python, so an unguarded isinstance check lets True
    through as a PrefabGUID of 1."""
    assert deep_problems("recipes", _recipes([_recipe(station_guids=[True])]))


def test_station_guids_rejects_a_repeated_station():
    """A station listed twice for one recipe double-counts it in any economy
    solver, and the dumper builds the list from a set, so a repeat means the
    inversion is broken rather than that the game says so."""
    problems = deep_problems("recipes", _recipes([_recipe(station_guids=[7, 7])]))
    assert problems
    assert "7" in problems[0]


def test_station_guids_rejects_an_unsorted_list():
    """The schema says sorted ascending. Order is the only thing that makes two
    dumps of the same world byte-comparable."""
    assert deep_problems("recipes", _recipes([_recipe(station_guids=[9, 3])]))

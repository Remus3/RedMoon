"""Cycle 3 phase 2: the schema'd dump.

Characterization gates for the three schema moves the approved input spike
specifies - `vbloods` to schema_version 2, `ability_stats` new at 1, and `items`
to schema_version 4 - plus the count assertion the cycle 2 duplicate-row defect
earned.

Every claim these tests encode was MEASURED in phase 1 and is recorded in
docs/BRIDGE_SPIKES.md with the component and field named. Nothing here is
recalled from the game's documentation, because there is none.

The counts gate is the one worth explaining. Four per-ROW gates - the shallow
schema, the deep nested contract, the census and the unmapped array - all passed
a dump that emitted 66 vblood rows over 65 distinct guids, because every
duplicate pair was byte-identical and each individual row was perfect. The only
symptom was the COUNT, and 66 had already been written into ROADMAP.md as the V
Blood total. A count that is merely whatever the dumper emitted is not an
assertion, so the expected counts are pinned as constants and the ingest refuses
a dump that disagrees.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.table_deep import deep_problems
from core.tables import (
    SCHEMA_DIR,
    TABLE_NAMES,
    empty_table,
    load_schema,
    validate_table,
)
from tools import rmdata_ingest

BUILD = "9.9.9.9-r12345"


# ---------------------------------------------------------------------------
# ability_stats - the new table, ADR-007
# ---------------------------------------------------------------------------


def test_ability_stats_is_a_declared_table():
    assert "ability_stats" in TABLE_NAMES
    assert (SCHEMA_DIR / "ability_stats.schema.json").is_file()


def test_ability_stats_is_keyed_on_the_ability_group_not_the_ability():
    """ADR-007. The coefficient key space is the ability GROUP, because
    coefficients do not need a school and a weapon ability has none. That is
    what dissolves ROADMAP cycle 3 gap 3: phase 1 measured that
    ProjectM.WeaponAbilityData tells a weapon group from a spell group BY
    COMPONENT, so no <Weapon>SpellSchoolAsset has to exist for a weapon ability
    to be addressable."""
    schema = load_schema("ability_stats")
    assert schema["schema_version"] == 1
    assert schema["required"] == ["prefab_guid", "name"]
    assert "school" not in schema["fields"], (
        "school belongs to the identity table; a coefficient row must not need one"
    )
    assert "is_weapon_ability" in schema["fields"]


def test_ability_stats_power_stat_is_declared_and_proven_absent():
    """A5, PROVEN ABSENT in phase 1: no power-selector member exists across all
    51 components enumerated on the _Hit entity, and MainType is the only
    discriminator present. Same rule as items.tier - DECLARED so a consumer can
    see the field was considered, never EMITTED, and absent means unsourced
    rather than physical."""
    schema = load_schema("ability_stats")
    assert "power_stat" in schema["fields"]
    assert "power_stat" not in schema["required"]
    assert "PROVEN ABSENT" in schema["fields"]["power_stat"]["description"]


def test_a_measured_ability_stats_row_passes_both_gates():
    row = {
        "prefab_guid": -1301247792,
        "name": "AB_Spear_AThousandSpears_Stab_AbilityGroup",
        "is_weapon_ability": True,
        "ability_type": "Primary",
        "cast_time": 0.35,
        "post_cast_time": 0.1,
        "cooldown": 0.0,
        "global_cooldown": 0.0,
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
    }
    envelope = empty_table("ability_stats", BUILD)
    envelope["rows"] = [row]
    assert validate_table(envelope, load_schema("ability_stats")) == []
    assert deep_problems("ability_stats", envelope) == []


def test_a_group_that_reaches_no_damage_omits_every_coefficient_field():
    """Cycle 2 MEASURED 912 of 1474 groups reaching no damage prefab, and that a
    second spawn hop adds exactly zero. Those groups genuinely do not reach
    damage, so they ship with the coefficient OMITTED, not zeroed."""
    envelope = empty_table("ability_stats", BUILD)
    envelope["rows"] = [{"prefab_guid": 7, "name": "AB_Nothing_AbilityGroup"}]
    assert validate_table(envelope, load_schema("ability_stats")) == []
    assert deep_problems("ability_stats", envelope) == []


def test_ability_stats_duplicate_guids_are_refused():
    """More than one entity can carry the same PrefabGUID, so the cross-row gate
    has to cover the new table too."""
    rows = [{"prefab_guid": 7, "name": "a"}, {"prefab_guid": 7, "name": "a"}]
    problems = rmdata_ingest.duplicate_key_problems({"ability_stats": rows})
    assert any("ability_stats" in problem and "7" in problem for problem in problems)


# ---------------------------------------------------------------------------
# vbloods schema 2 - the boss stat line, ROADMAP cycle 3 gap 1
# ---------------------------------------------------------------------------


def test_vbloods_is_at_schema_version_2():
    assert load_schema("vbloods")["schema_version"] == 2


def test_a_boss_row_carrying_the_stat_line_passes_both_gates():
    row = {
        "prefab_guid": -327335305,
        "name": "CHAR_Vampire_Dracula_VBlood",
        "level": 91,
        "max_health": 5000.0,
        "physical_power": 100.0,
        "spell_power": 100.0,
        "resistances": {"physical": 0.0, "spell": 0.0, "fire": 0.0, "corruption": 0.0},
    }
    envelope = empty_table("vbloods", BUILD)
    envelope["rows"] = [row]
    assert validate_table(envelope, load_schema("vbloods")) == []
    assert deep_problems("vbloods", envelope) == []


ABSENT_RESISTANCES = ("holy", "silver", "garlic", "sun")


def test_the_four_absent_resistances_are_named_in_the_schema_as_absent():
    """PROVEN ABSENT in phase 1 by full enumeration: across all 150 components on
    three bosses spanning levels 16, 57 and 91 there is no Holy, Silver, Garlic
    or Sun resistance member on the unit. ProjectM.ResistanceData carries
    per-RATING coefficients only, so it is a GLOBAL tuning block rather than a
    per-boss vector. A zero here would be indistinguishable from a real zero."""
    description = load_schema("vbloods")["fields"]["resistances"]["description"]
    for name in ABSENT_RESISTANCES:
        assert name in description, f"the schema never says {name} is absent"
    assert "PROVEN ABSENT" in description


def _dumper_source() -> str:
    return (
        Path(__file__).resolve().parents[1]
        / "bridge" / "src" / "RedMoon.Bridge" / "PrefabDumper.cs"
    ).read_text(encoding="utf-8")


def test_max_health_is_declared_but_never_emitted():
    """PHASE 3, MEASURED. ProjectM.Health.MaxHealth reads 0 on all 65 V Blood
    PREFABS. The control says what that zero means: 19 typed fields compared
    between the Dracula prefab (29012) and its live instance (322945), 17
    IDENTICAL, and MaxHealth 0 against 8107. So it is INSTANCE-ONLY, not spawn
    scaling - 0 to 8107 is not a ratio and there is no factor to recover.

    Emitting the prefab's 0 would put a fabricated value under the denominator
    of every time-to-kill, which is the items.tier mistake with a bigger blast
    radius. Declared so a consumer can see the field was considered; never
    written."""
    schema = load_schema("vbloods")
    assert "max_health" in schema["fields"]
    assert "max_health" not in schema["required"]
    assert "NEVER EMITTED" in schema["fields"]["max_health"]["description"]
    assert '"max_health"' not in _dumper_source().replace('\\"', '"'), (
        "the dumper emits max_health, which reads 0 on all 65 prefabs"
    )


def test_the_vblood_selector_requires_the_prefab_marker():
    """A spawned boss carries the SAME PrefabGUID as its prefab, and the two do
    NOT agree - Health differs. Without this test the row was whichever entity
    the world walk reached first.

    Cycle 2 saw this exact pair as "66 vblood rows over 65 distinct" and fixed
    the COUNT by deduping on first write, which silently converted a duplicate
    into an ORDER-DEPENDENT CHOICE between two disagreeing entities. The count
    looked right afterwards, which is why nothing caught it for a cycle."""
    text = _dumper_source()
    marker = "CarriesPrefabMarker"
    assert marker in text, "the vblood selector does not test the prefab marker"

    # The LAST mention of the want flag is the guard itself; the first is its
    # declaration. Slicing from the first would end at the guard's own flag and
    # miss every condition after it.
    vblood = text.split("wantVbloods")[-1].split("seenVbloods.Add")[0]
    assert marker in vblood, (
        "the prefab marker is tested somewhere, but not in the vblood selector"
    )


def test_the_dumper_never_writes_an_absent_resistance_key():
    text = (
        Path(__file__).resolve().parents[1]
        / "bridge"
        / "src"
        / "RedMoon.Bridge"
        / "PrefabDumper.cs"
    ).read_text(encoding="utf-8")
    for name in ABSENT_RESISTANCES:
        assert f'\\"{name}\\"' not in text, (
            f"PrefabDumper.cs emits a {name} resistance, which is PROVEN ABSENT on the unit"
        )


# ---------------------------------------------------------------------------
# items schema 4 - the L1 link
# ---------------------------------------------------------------------------


def test_items_is_at_schema_version_4_with_a_plural_ability_link():
    schema = load_schema("items")
    assert schema["schema_version"] == 4
    assert schema["fields"]["ability_group_guids"]["type"] == "array"
    assert "ability_group_guids" not in schema["required"], (
        "an item that grants no ability is real and must still validate"
    )


def test_an_item_row_carrying_ability_groups_passes_both_gates():
    row = {
        "prefab_guid": 1,
        "name": "Item_Weapon_Spear_T06_Iron_Reinforced",
        "category": "weapon",
        "weapon_type": "Spear",
        "stats": [{"stat": "PhysicalPower", "modification": "Add", "value": 10.0}],
        "ability_group_guids": [-1301247792, 5, 900],
    }
    envelope = empty_table("items", BUILD)
    envelope["rows"] = [row]
    assert validate_table(envelope, load_schema("items")) == []
    assert deep_problems("items", envelope) == []


@pytest.mark.parametrize(
    "guids, needle",
    [
        ([5, 5], "repeats"),
        ([900, 5], "ascending"),
        (["5"], "expected an integer"),
        ([True], "expected an integer"),
    ],
)
def test_the_ability_link_is_gated_the_same_way_the_station_link_is(guids, needle):
    """ADR-006's shape, reused. Every property asserted here is a property of the
    dumper's INVERSION rather than of the game: integers because a stringifying
    hop would show up, unique because the dumper accumulates into a set, and
    ascending because order is the only thing that makes two dumps of the same
    world byte-comparable."""
    envelope = empty_table("items", BUILD)
    envelope["rows"] = [
        {"prefab_guid": 1, "name": "x", "category": "weapon", "ability_group_guids": guids}
    ]
    problems = deep_problems("items", envelope)
    assert any(needle in problem for problem in problems), problems


def test_an_empty_ability_list_is_valid_and_differs_from_the_field_being_missing():
    """The ADR-006 rule, applied to the new link: [] says the equip-buff chain
    ran and this item grants nothing, a MISSING field says the chain did not
    run. Collapsing them would make the join unfalsifiable."""
    base = {"prefab_guid": 1, "name": "x", "category": "chest"}
    for rows in ([dict(base, ability_group_guids=[])], [dict(base)]):
        envelope = empty_table("items", BUILD)
        envelope["rows"] = rows
        assert validate_table(envelope, load_schema("items")) == []
        assert deep_problems("items", envelope) == []


def test_items_stats_entries_are_gated_rather_than_silently_skipped():
    """items.stats became a LIST at schema_version 2, and the deep gate still
    routed it through the object-shaped mapping check, which returns early on a
    list. So the one nested container the schema description says is unvalidated
    by the shallow gate was in fact unvalidated by BOTH gates. Found while
    bumping the same table to 4."""
    envelope = empty_table("items", BUILD)
    envelope["rows"] = [
        {
            "prefab_guid": 1,
            "name": "x",
            "category": "weapon",
            "stats": [{"stat": "PhysicalPower", "modification": "Add", "value": "ten"}],
        }
    ]
    problems = deep_problems("items", envelope)
    assert any("value" in problem for problem in problems), problems


# ---------------------------------------------------------------------------
# the count assertion - cycle 2 lesson 4
# ---------------------------------------------------------------------------


def test_every_table_has_a_pinned_expected_count():
    assert sorted(rmdata_ingest.EXPECTED_ROWS) == sorted(TABLE_NAMES)


def test_the_expected_counts_are_the_cycle_two_measurements():
    for name, count in (
        ("items", 425),
        ("recipes", 663),
        ("abilities", 54),
        ("vbloods", 65),
        ("blood_types", 13),
    ):
        assert rmdata_ingest.EXPECTED_ROWS[name] == count


def test_a_short_table_is_refused_by_count_even_when_every_row_is_valid():
    """The defect this exists for: 66 byte-identical-duplicate vblood rows, each
    individually perfect, refused by nothing."""
    problems = rmdata_ingest.count_problems({"vbloods": [{"prefab_guid": i} for i in range(64)]})
    assert any("vbloods" in problem and "64" in problem and "65" in problem for problem in problems)


def test_a_table_at_its_pinned_count_raises_no_problem():
    rows = [{"prefab_guid": i} for i in range(rmdata_ingest.EXPECTED_ROWS["vbloods"])]
    assert rmdata_ingest.count_problems({"vbloods": rows}) == []


def test_a_table_absent_from_the_dump_is_not_a_count_problem():
    """A --table run ingests one table. The count gate must not manufacture a
    failure for the four that were never asked for."""
    assert rmdata_ingest.count_problems({}) == []


def test_the_new_schema_file_is_ascii_and_parses():
    text = (SCHEMA_DIR / "ability_stats.schema.json").read_text(encoding="utf-8")
    assert all(ord(c) <= 127 for c in text)
    json.loads(text)

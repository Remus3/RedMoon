"""Section 4 of the combat math spec: DPS, and the denominator that is a MAX.

  ability_dps(G,T) = applied(G,T) / cycle(G)
  cycle(G) = max( cast_time + post_cast_time, cooldown, global_cooldown )

`cycle` being a maximum rather than a sum is the single easiest thing in this
spec to get wrong, and getting it wrong is invisible: a summed cycle produces a
plausible smaller number on every cooldown ability. So the first test here is a
mutation test in assertion form - it computes what a summing implementation
would return and asserts the module does NOT return that.

Coverage re-counted independently over the 1818 promoted rows and agreeing with
the spec: cast_time 1815, post_cast_time 1815, cooldown 1818, global_cooldown
1691, and cooldown == 0 on 352.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bloodforge import ENGINE_VERSION
from bloodforge.damage import (
    UNDEFINED_POWER_STAT,
    UNDEFINED_REDUCTION,
    PlayerPower,
    PowerHypothesis,
    Undefined,
    applied,
    defined,
)
from bloodforge.dps import (
    UNDEFINED_CYCLE,
    WeaponDps,
    ability_dps,
    cycle,
    weapon_sustained_dps,
)
from bloodforge.embargo import apply_embargo

BUILD = "1.1.13.0-r99712"
TABLES = Path(__file__).resolve().parents[1] / "data" / "rmdata" / BUILD / "tables"


def _rows(table: str) -> list[dict]:
    return json.loads((TABLES / f"{table}.json").read_text(encoding="utf-8"))["rows"]


ABILITY_STATS = _rows("ability_stats")
ITEMS = _rows("items")
VBLOODS = _rows("vbloods")
BY_NAME = {row["name"]: row for row in ABILITY_STATS}
BY_GUID = {row["prefab_guid"]: row for row in ABILITY_STATS}

DRACULA = next(row for row in VBLOODS if row["name"] == "CHAR_Vampire_Dracula_VBlood")
PLAYER = PlayerPower(physical_power=100.0, spell_power=40.0)
H1 = PowerHypothesis.DAMAGE_TYPE_SELECTS
H2 = PowerHypothesis.ABILITY_KIND_SELECTS

# The section E.1 default weapon.
GREATSWORD = next(
    row for row in ITEMS if row["name"] == "Item_Weapon_GreatSword_Legendary_T08"
)


# ---------------------------------------------------------------------------
# 4.1 the denominator
# ---------------------------------------------------------------------------


def test_cycle_is_a_maximum_and_a_summing_implementation_would_fail_here():
    """AB_Frost_CrystalLance_AbilityGroup: cast 1.0, post 0.25, cooldown 8.0,
    global_cooldown 0.2. The three windows OVERLAP - a cooldown runs DURING the
    cast, not after it - so the cycle is 8.0 and not 9.45. A summing model
    understates the cycle by 18 percent here and therefore overstates DPS by the
    same, on every cooldown ability in the corpus."""
    row = BY_NAME["AB_Frost_CrystalLance_AbilityGroup"]
    assert (row["cast_time"], row["post_cast_time"]) == (1.0, 0.25)
    assert (row["cooldown"], row["global_cooldown"]) == (8.0, 0.2)

    summed = (
        row["cast_time"] + row["post_cast_time"] + row["cooldown"]
        + row["global_cooldown"]
    )
    assert summed == pytest.approx(9.45)
    assert cycle(row) == pytest.approx(8.0)
    assert cycle(row) != pytest.approx(summed)


def test_the_max_form_disagrees_with_the_sum_form_on_most_of_the_corpus():
    """Not a one-row coincidence. Counted over every row with a defined cycle:
    the two forms agree only where at most one window is nonzero."""
    disagree = 0
    total = 0
    for row in ABILITY_STATS:
        value = cycle(row)
        if not defined(value):
            continue
        total += 1
        summed = (
            row["cast_time"]
            + row.get("post_cast_time", 0.0)
            + row["cooldown"]
            + row.get("global_cooldown", 0.0)
        )
        if abs(summed - value) > 1e-9:
            disagree += 1
    assert total == 1815
    assert disagree > total * 0.9, (
        f"only {disagree} of {total} rows distinguish max from sum"
    )


def test_a_zero_cooldown_primary_gets_its_cycle_from_cast_plus_recovery():
    """This is what makes the max-form necessary rather than merely correct:
    cooldown is 0 on 352 of 1818 rows, and taking cycle = cooldown would give
    those a zero denominator."""
    assert sum(1 for row in ABILITY_STATS if row["cooldown"] == 0) == 352

    row = BY_NAME["AB_Vampire_GreatSword_Primary_Moving_AbilityGroup"]
    assert row["cooldown"] == 0.0
    assert row["global_cooldown"] == 0.0
    assert (row["cast_time"], row["post_cast_time"]) == (0.5, 0.2)
    assert cycle(row) == pytest.approx(0.7)


def test_cooldown_wins_when_it_is_longer_than_the_cast():
    row = BY_NAME["AB_Unholy_WardOfTheDamned_AbilityGroup"]
    assert (row["cast_time"], row["post_cast_time"]) == (0.1, 0.2)
    assert row["cooldown"] == 11.0
    assert cycle(row) == pytest.approx(11.0)


def test_the_three_rows_missing_cast_time_have_no_cycle_and_no_dps():
    """Spec 4.1. Exactly 3 of 1818 rows lack cast_time, and the same 3 lack
    post_cast_time - the cast hop did not resolve for them at all. Their cycle
    is UNDEFINED, not zero and not cooldown-only."""
    missing = [row["name"] for row in ABILITY_STATS if "cast_time" not in row]
    assert sorted(missing) == [
        "AB_Bandit_Mugger_GapCloser_Group",
        "AB_Interact_OpenContainer_Blood_NoEssence_AbilityGroup",
        "AB_Interact_OpenContainer_DisabledDummy_AbilityGroup",
    ]
    assert sum(1 for row in ABILITY_STATS if "cast_time" in row) == 1815
    assert sum(1 for row in ABILITY_STATS if "post_cast_time" in row) == 1815

    for name in missing:
        row = BY_NAME[name]
        assert "cooldown" in row  # cooldown alone is NOT enough
        result = cycle(row)
        assert isinstance(result, Undefined), name
        assert result.reason == UNDEFINED_CYCLE


def test_a_missing_global_cooldown_drops_out_of_the_max():
    """global_cooldown is absent on 127 of 1818 rows. Dropping an absent window
    from a max is arithmetically the same as treating it as 0, which is why it
    is safe here and would NOT be safe in a sum."""
    absent = [row for row in ABILITY_STATS if "global_cooldown" not in row]
    assert len(absent) == 1818 - 1691 == 127

    row = BY_NAME["AB_Charm_AbilityGroup"]
    assert "global_cooldown" not in row
    assert (row["cast_time"], row["post_cast_time"], row["cooldown"]) == (0.5, 0.6, 0.5)
    assert cycle(row) == pytest.approx(1.1)


def test_a_zero_cycle_produces_no_dps_rather_than_an_infinity():
    """Two rows in 1818 have every window at zero. Dividing by that is not a
    very large DPS, it is no DPS."""
    zeroed = [
        row["name"]
        for row in ABILITY_STATS
        if defined(cycle(row)) and cycle(row) == 0.0
    ]
    assert sorted(zeroed) == [
        "AB_Nun_VBlood_HealCommand_AbilityGroup",
        "AB_Undead_ArenaChampion_AddToDuel_AbilityGroup",
    ]
    for name in zeroed:
        row = dict(BY_NAME[name])
        row.update(
            coefficient=1.0,
            raw_damage_value=0.0,
            raw_damage_percent=0.0,
            damage_type="physical",
            hits_per_cast=1,
            vblood_damage_modifier=1.0,
            damage_modifier_per_hit=0.0,
        )
        assert defined(applied(row, DRACULA, hypothesis=H1, player=PLAYER))
        result = ability_dps(row, DRACULA, hypothesis=H1, player=PLAYER)
        assert isinstance(result, Undefined)
        assert result.reason == UNDEFINED_CYCLE


# ---------------------------------------------------------------------------
# 4.1 the quotient
# ---------------------------------------------------------------------------


def test_ability_dps_is_applied_over_cycle_on_the_default_weapon_primary():
    """coefficient 0.7, hits_per_cast 3, PhysicalPower 100 under H1, physical
    reduction 0.0, vblood modifier 1.0 -> applied 210.0 over a 0.7 cycle."""
    row = BY_NAME["AB_Vampire_GreatSword_Primary_Moving_AbilityGroup"]
    assert applied(row, DRACULA, hypothesis=H1, player=PLAYER) == pytest.approx(210.0)
    assert cycle(row) == pytest.approx(0.7)
    assert ability_dps(row, DRACULA, hypothesis=H1, player=PLAYER) == pytest.approx(
        300.0
    )


def test_dps_is_withheld_whenever_applied_is_withheld():
    """The absence propagates upward unchanged and keeps its reason, so a
    consumer can say WHY it has no number."""
    holy = next(r for r in ABILITY_STATS if r.get("damage_type") == "holy")
    result = ability_dps(holy, DRACULA, hypothesis=H1, player=PLAYER)
    assert isinstance(result, Undefined)
    assert result.reason == UNDEFINED_REDUCTION

    npc = next(
        r
        for r in ABILITY_STATS
        if r.get("damage_type") == "corruption"
    )
    result = ability_dps(npc, DRACULA, hypothesis=H2, player=PLAYER)
    assert isinstance(result, Undefined)
    assert result.reason == UNDEFINED_POWER_STAT


def test_a_group_with_no_damage_block_has_a_cycle_but_no_dps():
    """The longbow again. It has a perfectly good denominator and no numerator,
    which is precisely the state a model that reads only timings would miss."""
    row = BY_NAME["AB_Vampire_Longbow_Primary_AbilityGroup"]
    assert cycle(row) == pytest.approx(5.25)
    assert isinstance(ability_dps(row, DRACULA, hypothesis=H1, player=PLAYER), Undefined)


# ---------------------------------------------------------------------------
# 4.2 the weapon level, which may never be rendered unlabelled
# ---------------------------------------------------------------------------


def test_the_default_weapon_has_three_links_and_two_of_them_reach_no_damage():
    """Spec 1.5. Two thirds of the default weapon's kit is unpriceable, which is
    what makes the labelling non-negotiable."""
    assert GREATSWORD["prefab_guid"] == -1173681254
    assert GREATSWORD["ability_group_guids"] == [
        -2095151729,  # AB_GreatSword_LeapAttack_AbilityGroup   - no damage block
        -1428882023,  # AB_Vampire_GreatSword_Primary_Moving_AbilityGroup
        -1181502209,  # AB_GreatSword_GreatCleaver_AbilityGroup - no damage block
    ]
    reached = [BY_GUID[guid] for guid in GREATSWORD["ability_group_guids"]]
    assert [("coefficient" in row) for row in reached] == [False, True, False]


def test_weapon_dps_cannot_be_rendered_without_its_priced_and_unpriceable_lists():
    result = weapon_sustained_dps(
        GREATSWORD, BY_GUID, DRACULA, hypothesis=H1, player=PLAYER
    )
    assert isinstance(result, WeaponDps)
    assert result.dps == pytest.approx(300.0)
    assert result.priced == ("AB_Vampire_GreatSword_Primary_Moving_AbilityGroup",)
    assert result.unpriceable == (
        "AB_GreatSword_LeapAttack_AbilityGroup",
        "AB_GreatSword_GreatCleaver_AbilityGroup",
    )
    # The number and its caveat are one object: there is no way to obtain the
    # float without also holding the two lists.
    assert set(vars(result)) == {"dps", "priced", "unpriceable", "label"}
    assert "1 of 3" in result.label
    assert "sustained single-ability" in result.label


def test_a_weapon_whose_every_group_is_unpriceable_yields_no_number():
    fishing = {
        "name": "Item_Weapon_Test_AllUnpriceable",
        "prefab_guid": 1,
        "ability_group_guids": [-2095151729, -1181502209],
    }
    result = weapon_sustained_dps(
        fishing, BY_GUID, DRACULA, hypothesis=H1, player=PLAYER
    )
    assert isinstance(result.dps, Undefined)
    assert result.priced == ()
    assert len(result.unpriceable) == 2


def test_rotation_dps_is_not_attempted():
    """Spec 4.2. Nothing on disk supplies an ability ordering, so a rotation DPS
    would be a model of a PLAYER presented as a property of a WEAPON. No such
    function exists, and the weapon helper does not sum its groups."""
    import bloodforge.dps as dps_module

    for banned in ("rotation_dps", "loadout_dps", "effective_dps", "total_dps"):
        assert not hasattr(dps_module, banned), banned

    # Summing the priced groups is the shape a rotation would take. Assert the
    # helper does not do it, using a weapon with more than one priced group.
    priced_pair = {
        "name": "Item_Weapon_Test_TwoPriced",
        "prefab_guid": 2,
        "ability_group_guids": [
            -1428882023,  # GreatSword primary, dps 300.0
            BY_NAME["AB_Unholy_WardOfTheDamned_AbilityGroup"]["prefab_guid"],
        ],
    }
    result = weapon_sustained_dps(
        priced_pair, BY_GUID, DRACULA, hypothesis=H1, player=PLAYER
    )
    ward_dps = ability_dps(
        BY_NAME["AB_Unholy_WardOfTheDamned_AbilityGroup"],
        DRACULA,
        hypothesis=H1,
        player=PLAYER,
    )
    assert len(result.priced) == 2
    assert result.dps == pytest.approx(300.0)
    assert result.dps != pytest.approx(300.0 + ward_dps)


# ---------------------------------------------------------------------------
# The embargo, which neither module may route around
# ---------------------------------------------------------------------------


def test_a_payload_built_from_these_modules_still_loses_its_dps_key():
    """Today's state of the world: no anchor run exists, so load_anchors returns
    [] and publishable_fields returns the empty set for every subject alive.
    These modules compute INTERNAL values and publication goes through
    apply_embargo, which is where the key disappears."""
    row = BY_NAME["AB_Vampire_GreatSword_Primary_Moving_AbilityGroup"]
    value = ability_dps(row, DRACULA, hypothesis=H1, player=PLAYER)
    assert defined(value)

    subject = {
        "game_build": BUILD,
        "engine_version": ENGINE_VERSION,
        "boss_prefab_guid": DRACULA["prefab_guid"],
        "difficulty": {"LevelIncrease": 0, "MaxHealthModifier": 1.0,
                       "PowerModifier": 1.0},
        "blood_type": "BloodType_Warrior",
        "blood_quality": 100,
        "equipped_item_guids": {"weapon": GREATSWORD["prefab_guid"]},
    }
    payload = {
        "ability_group": row["name"],
        "hypothesis": H1.value,
        "dps": value,
        "ehp": 1234.0,
        "ttk_seconds": 27.0,
    }
    published = apply_embargo(payload, subject, [])
    assert "dps" not in published
    assert "ehp" not in published
    assert "ttk_seconds" not in published
    assert published == {"ability_group": row["name"], "hypothesis": "H1"}


def test_neither_module_serializes_an_embargoed_name_itself():
    """There is exactly one emit site and it is bloodforge.embargo. A module
    here that wrote a dps key into a dict would be a second one."""
    import bloodforge.damage as damage_module
    import bloodforge.dps as dps_module

    for module in (damage_module, dps_module):
        source = Path(module.__file__).read_text(encoding="utf-8")
        code = "\n".join(
            line
            for line in source.splitlines()
            if not line.lstrip().startswith("#")
        )
        for quoted in ('"dps"', "'dps'", '"ehp"', "'ehp'",
                       '"ttk_seconds"', "'ttk_seconds'"):
            assert quoted not in code, f"{module.__name__} names {quoted}"

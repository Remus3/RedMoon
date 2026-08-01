"""Section 2 of the combat math spec: the per-application damage model.

Every assertion here is pinned to a row READ from
data/rmdata/1.1.13.0-r99712/tables/ability_stats.json or vbloods.json, not to a
hand-written fixture, because the whole point of section 1 of the spec is that
six previously recorded facts moved when someone counted the promoted rows
instead of reading the prose about them.

The counts asserted below were re-counted independently while writing this file
and every one agrees with the spec:

  1818 ability_stats rows, 732 carrying a damage block, and all five damage
  fields present on exactly those same 732
  damage_type over the 732: physical 579, spell 93, holy 27, corruption 18,
  fire 15 - so 42 are unpriceable
  hit_triggers 0 on all 732, multiply_main_factor_with_stacks false on all 732
  vblood_damage_modifier 1.0 on 728 and 0.33 on 4
  damage_modifier_per_hit nonzero on 3, all three with hits_per_cast 1
  raw_damage_percent nonzero on 1, raw_damage_value nonzero on 1
  65 vbloods, physical 0 on all 65, spell 0 on all 65, corruption 0.5 on all
  65, fire an integer rating 0 on 61 and 50/50/70/75 on 4, holy absent entirely
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from bloodforge.damage import (
    DEFINED_REDUCTION_TYPES,
    NO_DAMAGE_BLOCK,
    UNDEFINED_POWER_STAT,
    UNDEFINED_REDUCTION,
    UNDEFINED_REDUCTION_TYPES,
    UNSOURCED_POOL,
    PlayerPower,
    PowerHypothesis,
    Undefined,
    applied,
    base,
    cast,
    defined,
    has_damage_block,
    per_hit,
    power_stat,
    reduction,
    vs_class,
)

BUILD = "1.1.13.0-r99712"
TABLES = Path(__file__).resolve().parents[1] / "data" / "rmdata" / BUILD / "tables"


def _rows(table: str) -> list[dict]:
    return json.loads((TABLES / f"{table}.json").read_text(encoding="utf-8"))["rows"]


ABILITY_STATS = _rows("ability_stats")
VBLOODS = _rows("vbloods")
BY_NAME = {row["name"]: row for row in ABILITY_STATS}
DAMAGE_ROWS = [row for row in ABILITY_STATS if "coefficient" in row]

# The section E.1 default target. Physical and spell resistance 0.0, corruption
# 0.5, fire rating 0, no holy field at all.
DRACULA = next(row for row in VBLOODS if row["name"] == "CHAR_Vampire_Dracula_VBlood")

# A plausible live player vector. The two stats are deliberately far apart so
# that any test which confuses them fails loudly rather than by a rounding
# margin. Section 3.3 relies on exactly that separation in the real experiment.
PLAYER = PlayerPower(physical_power=100.0, spell_power=40.0)

H1 = PowerHypothesis.DAMAGE_TYPE_SELECTS
H2 = PowerHypothesis.ABILITY_KIND_SELECTS


# ---------------------------------------------------------------------------
# The corpus itself. If any of these move, every number below is suspect.
# ---------------------------------------------------------------------------


def test_the_damage_block_is_all_or_nothing_over_1818_rows():
    """Spec 1.1. A group reaching no _Hit prefab omits coefficient,
    raw_damage_value, raw_damage_percent, damage_type and hits_per_cast
    TOGETHER, so "no damage block" is a state and not a missing field."""
    assert len(ABILITY_STATS) == 1818
    block = (
        "coefficient",
        "raw_damage_value",
        "raw_damage_percent",
        "damage_type",
        "hits_per_cast",
    )
    with_block = [row for row in ABILITY_STATS if "coefficient" in row]
    assert len(with_block) == 732
    for field in block:
        assert sum(1 for row in ABILITY_STATS if field in row) == 732, field
    assert all(has_damage_block(row) for row in with_block)
    assert not any(
        has_damage_block(row) for row in ABILITY_STATS if "coefficient" not in row
    )


def test_damage_type_census_leaves_42_groups_unpriceable():
    """Spec 1.2. 27 holy plus 15 fire."""
    census: dict[str, int] = {}
    for row in DAMAGE_ROWS:
        census[row["damage_type"]] = census.get(row["damage_type"], 0) + 1
    assert census == {
        "physical": 579,
        "spell": 93,
        "holy": 27,
        "corruption": 18,
        "fire": 15,
    }
    withheld = sum(
        count for kind, count in census.items() if kind in UNDEFINED_REDUCTION_TYPES
    )
    assert withheld == 42


# ---------------------------------------------------------------------------
# 2.2 reduction is a PARTIAL function on three of five types
# ---------------------------------------------------------------------------


def test_reduction_is_defined_on_exactly_three_of_five_types():
    assert DEFINED_REDUCTION_TYPES == frozenset({"physical", "spell", "corruption"})
    assert UNDEFINED_REDUCTION_TYPES == frozenset({"fire", "holy"})
    assert not (DEFINED_REDUCTION_TYPES & UNDEFINED_REDUCTION_TYPES)


def test_reduction_reads_the_three_defined_types_off_every_one_of_the_65_bosses():
    assert len(VBLOODS) == 65
    for boss in VBLOODS:
        assert reduction(boss, "physical") == 0.0
        assert reduction(boss, "spell") == 0.0
        assert reduction(boss, "corruption") == 0.5


def test_reduction_is_undefined_for_fire_and_holy_and_that_is_not_zero():
    """The load-bearing distinction. A zero reduction is a REAL claim - the
    boss takes full damage - and an unknown one is the absence of a claim. An
    implementation that returns 0.0 for fire would publish full-damage numbers
    against the four bosses that actually carry a 50, 50, 70 or 75 rating."""
    fire = reduction(DRACULA, "fire")
    holy = reduction(DRACULA, "holy")
    assert isinstance(fire, Undefined)
    assert isinstance(holy, Undefined)
    assert fire.reason == UNDEFINED_REDUCTION
    assert holy.reason == UNDEFINED_REDUCTION
    assert not defined(fire)
    assert not defined(holy)
    # And the two are NOT the same absence: one is an unread global constant,
    # the other is a field that does not exist on any unit.
    assert fire.detail != holy.detail

    zero = reduction(DRACULA, "physical")
    assert defined(zero)
    assert zero == 0.0
    assert zero is not fire


def test_the_fire_rating_is_present_and_is_not_a_reduction():
    """ROADMAP gap 8 in one assertion. The fire value on the unit is an integer
    RATING that needs an unread global constant to become a reduction, so it
    must never be handed back as one even though it is sitting right there in
    the same resistances map as the three that are."""
    ratings = sorted(boss["resistances"]["fire"] for boss in VBLOODS)
    assert ratings.count(0) == 61
    assert ratings[-4:] == [50, 50, 70, 75]
    for boss in VBLOODS:
        assert isinstance(reduction(boss, "fire"), Undefined)


def test_holy_has_no_unit_side_field_at_all():
    for boss in VBLOODS:
        assert "holy" not in boss["resistances"]
        assert set(boss["resistances"]) == {"physical", "spell", "corruption", "fire"}


def test_an_undefined_reduction_cannot_be_used_as_a_number_by_accident():
    """Undefined supports no arithmetic. A caller that forgets to check gets a
    TypeError at the first operation rather than a wrong float downstream."""
    fire = reduction(DRACULA, "fire")
    with pytest.raises(TypeError):
        1.0 - fire
    with pytest.raises(TypeError):
        float(fire)


def test_the_four_resistance_values_are_never_averaged():
    """The averaging prohibition of spec 2.2, encoded twice.

    The four values are not commensurable: physical and spell are float
    resistances, corruption is already a reduction, fire is an integer rating on
    a different scale entirely. A mean over them is meaningless in a way no unit
    test on its output could detect, so the guard is on the API surface and on
    the source.
    """
    import bloodforge.damage as damage_module

    # No aggregate exists to call.
    for banned in ("mean_reduction", "average_reduction", "overall_reduction",
                   "scalar_reduction", "combined_reduction"):
        assert not hasattr(damage_module, banned), banned

    source = Path(damage_module.__file__).read_text(encoding="utf-8")
    code = "\n".join(
        line for line in source.splitlines() if not line.strip().startswith("#")
    )
    # Strip the module docstring, which names the prohibition in prose.
    body = code.split('"""', 2)[-1]
    for token in ("statistics", "fmean", "mean(", "sum(reduction", "/ len("):
        assert token not in body, f"{token} suggests an average over resistances"


# ---------------------------------------------------------------------------
# 3. P(G) is UNDEFINED and must be named by the caller
# ---------------------------------------------------------------------------


def test_computing_damage_requires_naming_a_hypothesis():
    """P(G) has no default anywhere in the module. power_stat is PROVEN ABSENT
    from the data and the two live hypotheses are undecided, so a caller that
    does not say which one it is computing under gets no number at all."""
    row = BY_NAME["AB_Unholy_WardOfTheDamned_AbilityGroup"]
    with pytest.raises(TypeError):
        base(row)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        base(row, player=PLAYER)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        applied(row, DRACULA, hypothesis=H1)  # type: ignore[call-arg]


def test_the_one_discriminator_row_separates_h1_from_h2():
    """Spec 3.3. AB_Unholy_WardOfTheDamned_AbilityGroup is the only row in 1818
    that is a spell-school ability with damage_type physical, so it is the only
    subject in the corpus where the two hypotheses predict different numbers."""
    row = BY_NAME["AB_Unholy_WardOfTheDamned_AbilityGroup"]
    assert row["prefab_guid"] == -1136860480
    assert row["spell_school"] == "unholy"
    assert row["damage_type"] == "physical"
    assert row["coefficient"] == 1.0
    assert row["hits_per_cast"] == 1
    assert row["is_weapon_ability"] is False

    assert power_stat(row, hypothesis=H1, player=PLAYER) == ("PhysicalPower", 100.0)
    assert power_stat(row, hypothesis=H2, player=PLAYER) == ("SpellPower", 40.0)

    # coefficient 1.0 and one hit, so applied IS the power stat.
    assert applied(row, DRACULA, hypothesis=H1, player=PLAYER) == 100.0
    assert applied(row, DRACULA, hypothesis=H2, player=PLAYER) == 40.0


def test_it_is_the_only_such_row_in_the_corpus():
    discriminators = [
        row["name"]
        for row in DAMAGE_ROWS
        if "spell_school" in row
        and row["damage_type"] == "physical"
        and row["coefficient"]
    ]
    assert discriminators == ["AB_Unholy_WardOfTheDamned_AbilityGroup"]


def test_the_weapon_side_cannot_discriminate_by_exhaustion():
    """Spec 3.2. Zero rows are is_weapon_ability true with a non-physical
    damage_type AND a nonzero coefficient, so no weapon ability can tell the two
    hypotheses apart."""
    assert [
        row["name"]
        for row in DAMAGE_ROWS
        if row.get("is_weapon_ability")
        and row["damage_type"] != "physical"
        and row["coefficient"]
    ] == []


def test_h1_is_undefined_for_the_three_types_it_does_not_name():
    """H1 is stated over Physical and Spell only. corruption, fire and holy get
    NO power stat under it, which is a consequence of the hypothesis and not an
    oversight to be papered over with a default."""
    corruption = next(row for row in DAMAGE_ROWS if row["damage_type"] == "corruption")
    result = power_stat(corruption, hypothesis=H1, player=PLAYER)
    assert isinstance(result, Undefined)
    assert result.reason == UNDEFINED_POWER_STAT
    assert isinstance(base(corruption, hypothesis=H1, player=PLAYER), Undefined)


def test_h2_is_undefined_when_the_ability_kind_is_unreadable():
    """H2 selects on the KIND, which is readable only where WeaponAbilityData or
    a spell school is present. On 688 of the 732 damage rows neither component
    is there, so H2 is silent on the great majority of the corpus. Counted here
    rather than asserted from prose."""
    unreadable = [
        row
        for row in DAMAGE_ROWS
        if not row.get("is_weapon_ability") and "spell_school" not in row
    ]
    assert len(unreadable) == 688
    result = power_stat(unreadable[0], hypothesis=H2, player=PLAYER)
    assert isinstance(result, Undefined)
    assert result.reason == UNDEFINED_POWER_STAT


# ---------------------------------------------------------------------------
# 2.1 the equation, term by term
# ---------------------------------------------------------------------------


def test_base_is_the_sum_of_all_three_terms():
    """coefficient * P + raw_damage_value + raw_damage_percent * pool. Checked
    on the one real row with a nonzero raw_damage_value, where a model reading
    only the coefficient would be wrong by exactly 0.01."""
    row = BY_NAME["AB_Charm_AbilityGroup"]
    assert row["coefficient"] == 0.0
    assert row["raw_damage_value"] == 0.01
    assert row["raw_damage_percent"] == 0.0
    assert row["damage_type"] == "spell"
    # H1: spell -> SpellPower 40.0, times coefficient 0.0, plus the flat 0.01.
    assert base(row, hypothesis=H1, player=PLAYER) == pytest.approx(0.01)


def test_a_nonzero_raw_damage_percent_produces_no_number_because_the_pool_is_unsourced():
    """Spec 2.3. Nothing on disk says which pool - current health, max health,
    or the caster's - and the field is nonzero on exactly one row of 732."""
    golem = BY_NAME["AB_Shapeshift_Golem_T02_Group"]
    assert golem["raw_damage_percent"] == 0.3
    assert golem["coefficient"] == 0.0

    result = base(golem, hypothesis=H1, player=PLAYER)
    assert isinstance(result, Undefined)
    assert result.reason == UNSOURCED_POOL
    assert isinstance(applied(golem, DRACULA, hypothesis=H1, player=PLAYER), Undefined)

    # The golem story: coefficient 0 AND raw_damage_percent 0.3 together, so a
    # model reading only the coefficient prices this at exactly zero rather than
    # withholding it. That silent zero is what this test exists to prevent.
    assert [row["name"] for row in DAMAGE_ROWS if row["raw_damage_percent"]] == [
        "AB_Shapeshift_Golem_T02_Group"
    ]


def test_per_hit_ramps_linearly_and_the_first_hit_is_unmodified():
    row = BY_NAME["AB_Vampire_GreatSword_Primary_Moving_AbilityGroup"]
    assert row["hits_per_cast"] == 3
    assert row["damage_modifier_per_hit"] == 0.0
    one = base(row, hypothesis=H1, player=PLAYER)
    assert per_hit(row, 1, hypothesis=H1, player=PLAYER) == pytest.approx(one)
    assert per_hit(row, 3, hypothesis=H1, player=PLAYER) == pytest.approx(one)
    # coefficient 0.7 against PhysicalPower 100.0, three identical hits.
    assert one == pytest.approx(70.0)
    assert cast(row, hypothesis=H1, player=PLAYER) == pytest.approx(210.0)


def test_the_linear_ramp_is_pinned_to_the_three_real_nonzero_rows():
    """Spec 2.4. The ramp FORM is an arbitrary, untested choice among three that
    fit the field name. It is unobservable on this build because all three rows
    carrying a nonzero modifier have hits_per_cast 1, which makes the term
    identically zero in every computation the engine can currently do.

    This test is the tripwire: if a future build gives a multi-hit ability a
    nonzero modifier, the hits_per_cast assertion below fails and someone has to
    go and find out which of the three forms is real.
    """
    expected = {
        "AB_Prog_Boomerang_Group": -0.2,
        "AB_Frost_CrystalLance_AbilityGroup": 0.5,
        "AB_Illusion_WraithSpear_AbilityGroup": -0.25,
    }
    nonzero = {
        row["name"]: row["damage_modifier_per_hit"]
        for row in DAMAGE_ROWS
        if row["damage_modifier_per_hit"]
    }
    assert nonzero == expected

    for name in expected:
        row = BY_NAME[name]
        assert row["hits_per_cast"] == 1, (
            f"{name} became multi-hit: the ramp form is now OBSERVABLE and the "
            "arbitrary linear choice in bloodforge/damage.py must be verified"
        )
        # With one hit the modifier cannot move anything: i - 1 is 0.
        assert cast(row, hypothesis=H1, player=PLAYER) == pytest.approx(
            per_hit(row, 1, hypothesis=H1, player=PLAYER)
        )


def test_the_ramp_would_bite_on_a_multi_hit_row_if_one_existed():
    """The linear form itself, exercised on a synthetic row so that the choice
    is at least pinned somewhere. -0.2 over 3 hits gives 1.0, 0.8, 0.6."""
    row = dict(BY_NAME["AB_Prog_Boomerang_Group"], hits_per_cast=3)
    one = base(row, hypothesis=H1, player=PLAYER)
    assert per_hit(row, 1, hypothesis=H1, player=PLAYER) == pytest.approx(one)
    assert per_hit(row, 2, hypothesis=H1, player=PLAYER) == pytest.approx(0.8 * one)
    assert per_hit(row, 3, hypothesis=H1, player=PLAYER) == pytest.approx(0.6 * one)
    assert cast(row, hypothesis=H1, player=PLAYER) == pytest.approx(2.4 * one)


def test_vblood_damage_modifier_is_applied_even_though_it_is_1_on_728_of_732():
    """Spec 1.3. Being 1.0 almost everywhere is exactly what makes an omission
    invisible: it would be correct on 728 rows and wrong on 4, and the 4 are
    golem-form abilities nobody would think to check."""
    modifiers = [row["vblood_damage_modifier"] for row in DAMAGE_ROWS]
    assert sum(1 for value in modifiers if value == 1.0) == 728
    reduced = [row for row in DAMAGE_ROWS if row["vblood_damage_modifier"] == 0.33]
    assert len(reduced) == 4

    row = reduced[0]
    assert vs_class(row, DRACULA, hypothesis=H1, player=PLAYER) == pytest.approx(
        0.33 * cast(row, hypothesis=H1, player=PLAYER)
    )


def test_no_real_corruption_row_can_be_priced_under_either_hypothesis():
    """A discrepancy with spec section 7, found by counting.

    Section 7 lists `applied` for corruption groups as COMPUTABLE once P(G) is
    decided. It is not, and the reason is on the POWER side rather than the
    resistance side: all 18 corruption damage groups are NPC abilities carrying
    neither WeaponAbilityData nor a spell school, so H2 has no kind to select on
    - and H1 is stated over Physical and Spell only, so it has nothing to say
    about a corruption MainType either. Deciding the section 3.3 experiment
    would still leave all 18 unpriced.
    """
    corruption = [r for r in DAMAGE_ROWS if r["damage_type"] == "corruption"]
    assert len(corruption) == 18
    assert all(
        not row.get("is_weapon_ability") and "spell_school" not in row
        for row in corruption
    )
    for row in corruption:
        for hypothesis in (H1, H2):
            result = applied(row, DRACULA, hypothesis=hypothesis, player=PLAYER)
            assert isinstance(result, Undefined)
            assert result.reason == UNDEFINED_POWER_STAT


def test_applied_divides_out_the_reduction_and_corruption_actually_halves():
    """corruption reads 0.5 on all 65, so it is the only defined type whose
    reduction is not a no-op and the only one where forgetting the term would
    double the answer. Nothing real reaches it - see the test above - so the
    arithmetic is pinned on a synthetic row built from a real one. The synthetic
    part is a single added spell_school, which is exactly the field whose
    absence blocks the real row."""
    real = next(r for r in DAMAGE_ROWS if r["damage_type"] == "corruption")
    assert real["name"] == "AB_Blackfang_CarverBoss_SingleThrow_AbilityGroup"
    assert real["coefficient"] == 1.0
    assert real["hits_per_cast"] == 1

    row = dict(real, spell_school="unholy")
    assert vs_class(row, DRACULA, hypothesis=H2, player=PLAYER) == pytest.approx(40.0)
    assert applied(row, DRACULA, hypothesis=H2, player=PLAYER) == pytest.approx(20.0)


def test_a_holy_or_fire_ability_produces_no_applied_number():
    """And the withheld reason names the TARGET side, ahead of any power-stat
    blocker, because a reduction that does not exist cannot be fixed by running
    the section 3.3 experiment."""
    for kind in ("holy", "fire"):
        row = next(r for r in DAMAGE_ROWS if r["damage_type"] == kind)
        result = applied(row, DRACULA, hypothesis=H2, player=PLAYER)
        assert isinstance(result, Undefined), kind
        assert result.reason == UNDEFINED_REDUCTION, kind


# ---------------------------------------------------------------------------
# 2.5 / 1.1 what must NOT happen
# ---------------------------------------------------------------------------


def test_no_damage_block_is_a_different_state_from_coefficient_zero():
    """Spec 1.1, corrected fact 2. AB_Vampire_Longbow_Primary_AbilityGroup has
    no damage block whatever - it declares spawn_prefabs_on_cast 8 and cast_time
    5, a draw rather than a swing, and reaches no _Hit prefab in one hop.
    AB_Spear_AThousandSpears_Stab_AbilityGroup carries a GENUINE coefficient of
    0.0. The two differ by a whole block, not by one field, and they must not
    produce the same result."""
    longbow = BY_NAME["AB_Vampire_Longbow_Primary_AbilityGroup"]
    assert "coefficient" not in longbow
    assert longbow["spawn_prefabs_on_cast"] == 8
    assert longbow["cast_time"] == 5
    assert not has_damage_block(longbow)

    spear = BY_NAME["AB_Spear_AThousandSpears_Stab_AbilityGroup"]
    assert spear["coefficient"] == 0.0
    assert has_damage_block(spear)

    missing = base(longbow, hypothesis=H1, player=PLAYER)
    assert isinstance(missing, Undefined)
    assert missing.reason == NO_DAMAGE_BLOCK

    genuine = base(spear, hypothesis=H1, player=PLAYER)
    assert defined(genuine)
    assert genuine == 0.0
    assert applied(spear, DRACULA, hypothesis=H1, player=PLAYER) == 0.0


def test_hit_triggers_and_stacks_are_constant_and_deliberately_absent_from_the_math():
    """Spec 2.5. Both are single-valued over all 732 rows, so neither can inform
    anything, and a model that read them would be fitting a constant."""
    assert {row["hit_triggers"] for row in DAMAGE_ROWS} == {0}
    assert {row["multiply_main_factor_with_stacks"] for row in DAMAGE_ROWS} == {False}

    import bloodforge.damage as damage_module

    source = Path(damage_module.__file__).read_text(encoding="utf-8")
    body = source.split('"""', 2)[-1]
    code = "\n".join(
        line
        for line in body.splitlines()
        if not line.strip().startswith("#") and '"""' not in line
    )
    for field in ("hit_triggers", "multiply_main_factor_with_stacks"):
        assert field not in code, f"{field} must not enter the math"


def test_crit_and_blood_bonuses_are_not_attempted():
    """Spec 2.5: SpellCriticalStrikeChance appears on 1 of 205 weapons with no
    multiplier sourced, and all 13 blood_types rows carry stat NAMES with no
    magnitudes. Neither is modelled, and PlayerPower carries no field that would
    let one sneak in."""
    assert set(vars(PLAYER)) == {"physical_power", "spell_power"}

    blood = _rows("blood_types")
    assert len(blood) == 13
    for row in blood:
        for bonus in row["bonuses"]:
            assert bonus["value_source"] == "blood_quality_scaled_at_runtime"
            for stat in bonus["stats"]:
                # A stat NAME and a modification kind, and no magnitude anywhere.
                assert set(stat) == {"stat", "modification"}

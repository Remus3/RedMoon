"""P(G) - which power stat a coefficient multiplies, and the one row that says.

power_stat is PROVEN ABSENT from the data: no power-selector member exists
across all 51 components on the _Hit entity, and MainType is the only
discriminator present. Two hypotheses survive:

  H1  damage_type selects. MainType Physical multiplies UnitStats.PhysicalPower,
      Spell multiplies SpellPower.
  H2  the ability KIND selects. A weapon ability multiplies PhysicalPower, a
      spell-school ability multiplies SpellPower, regardless of MainType.

THE DEFAULT SUBJECT VECTOR CANNOT SEPARATE THEM. Measured over the promoted
tables: 31 of the 32 distinct weapon-linked damage groups are damage_type
physical, and over 205 weapons PhysicalPower AddToBase appears on 203 while
SpellPower appears on exactly 1. So a per-hit gate against GreatSword versus
Dracula passes at 2 percent under BOTH hypotheses and decides nothing. And zero
rows are is_weapon_ability true with a non-physical damage_type and a nonzero
coefficient, so the weapon side is dead by EXHAUSTION, not by sampling.

Exactly one row in 1818 separates them, and this module's first duty is to
re-count that rather than trust it.
"""
from __future__ import annotations

import pytest

from bloodforge import powerstat
from tools import anchor_record as ar

WARD_GUID = -1136860480
WARD_NAME = "AB_Unholy_WardOfTheDamned_AbilityGroup"

PHYSICAL_POWER = 120.0
SPELL_POWER = 40.0

STATS = {
    "UnitStats.PhysicalPower": PHYSICAL_POWER,
    "UnitStats.SpellPower": SPELL_POWER,
}


def _series_from_drops(drops: list[float], start: float = 100000.0) -> list[dict]:
    """A synthetic series with one ISOLATED delta per entry in `drops`.

    Each health level is held for two consecutive samples, which is the minimum
    that brackets every drop with a no-change sample on each side. At 4 Hz that
    is a 500 ms cadence - slower than any real rotation, which is exactly why a
    real run may not yield 30 isolated deltas (falsification spec open question
    4) and why the honest response to a short run is to POOL, never to lower n.
    """
    values: list[float] = []
    health = start
    for drop in [*drops, 0.0]:
        values.extend([health, health])
        health -= drop
    return _rows_from_values(values)


def _series(per_hit: float, hits: int = 30) -> list[dict]:
    return _series_from_drops([per_hit] * hits)


def _rows_from_values(values: list[float]) -> list[dict]:
    wire = [
        {
            "index": i,
            "captured_at": ar.stamp(i * ar.TICK_INTERVAL_S),
            "prefab_guid": WARD_GUID,
            "carries_prefab_marker": False,
            "health_value": float(v),
            "health_max": float(values[0]),
            "is_dead": False,
        }
        for i, v in enumerate(values)
    ]
    return ar.translate_samples(wire, {})


def _run(rows: list[dict]) -> dict:
    return {"rows": rows, "manifest": {"player_unit_stats": dict(STATS)}}


# ---------------------------------------------------------------------------
# 1. The discriminator is verified by COUNTING, not by trusting a number.
# ---------------------------------------------------------------------------


def test_exactly_one_row_in_the_corpus_separates_the_two_hypotheses():
    """A spell-school ability whose damage_type is physical. If a future build
    adds a second, THIS test is what says so - which is the whole reason
    discriminators returns the full candidate list rather than one row."""
    candidates = powerstat.discriminators()
    assert len(candidates) == 1, [row["name"] for row in candidates]
    assert candidates[0]["prefab_guid"] == WARD_GUID
    assert candidates[0]["name"] == WARD_NAME


def test_the_discriminator_is_a_designed_experiment_and_its_terms_are_inert():
    """coefficient exactly 1.0 and hits_per_cast 1 mean the prediction is
    literally 'the observed delta EQUALS one of the two power stats' - no
    arithmetic to get wrong and no multi-hit aliasing at 4 Hz. damage_type
    physical means reduction is 0.0 and DEFINED, so the boss side contributes
    nothing either."""
    row = powerstat.ward_row()
    assert row["coefficient"] == 1.0
    assert row["hits_per_cast"] == 1
    assert row["damage_type"] == "physical"
    assert row["spell_school"] == "unholy"
    assert row["ability_type"] == "SpellSlot2", "must be player-castable"
    assert row["raw_damage_value"] == 0
    assert row["raw_damage_percent"] == 0
    assert row["damage_modifier_per_hit"] == 0
    assert row["vblood_damage_modifier"] == 1.0


def test_the_weapon_side_is_dead_by_exhaustion_not_by_sampling():
    """Zero rows are is_weapon_ability true with a non-physical damage_type and
    a nonzero coefficient. Counted live, because a count is the only thing that
    can retire a hypothesis."""
    assert powerstat.weapon_side_candidates() == []


# ---------------------------------------------------------------------------
# 2. predict. The two hypotheses disagree on the Ward and agree everywhere else.
# ---------------------------------------------------------------------------


def test_the_two_hypotheses_predict_different_numbers_on_the_ward():
    row = powerstat.ward_row()
    assert powerstat.predict("H1", row, STATS) == PHYSICAL_POWER
    assert powerstat.predict("H2", row, STATS) == SPELL_POWER


def test_the_two_hypotheses_agree_on_a_physical_weapon_ability():
    """The finding that invalidates the obvious plan, in one assertion."""
    row = {
        "name": "AB_Vampire_GreatSword_Primary_Moving_AbilityGroup",
        "damage_type": "physical",
        "is_weapon_ability": True,
        "coefficient": 0.7,
        "hits_per_cast": 3,
    }
    assert powerstat.predict("H1", row, STATS) == powerstat.predict("H2", row, STATS)


def test_predict_refuses_a_row_whose_near_inert_terms_are_not_inert():
    """This module owns ONE experiment, not the damage model. A row with a live
    raw_damage_percent needs pool(T), which is UNSOURCED. No number is better
    than a number computed from a pool nobody identified."""
    row = {**powerstat.ward_row(), "raw_damage_percent": 0.3}
    assert powerstat.predict("H1", row, STATS) is None


def test_predict_is_undefined_rather_than_defaulted_for_an_unselectable_row():
    """H1 selects on Physical or Spell only. A corruption group selects no power
    stat under H1, and 0.0 would be a lie."""
    row = {**powerstat.ward_row(), "damage_type": "corruption", "spell_school": None}
    assert powerstat.predict("H1", row, STATS) is None
    assert powerstat.predict("H2", row, STATS) is None


def test_predict_rejects_an_unknown_hypothesis_rather_than_guessing():
    with pytest.raises(ValueError):
        powerstat.predict("H3", powerstat.ward_row(), STATS)


# ---------------------------------------------------------------------------
# 3. evaluate. A verdict per hypothesis, and INDETERMINATE when it must be.
# ---------------------------------------------------------------------------


def test_a_series_whose_deltas_equal_physical_power_survives_H1():
    result = powerstat.evaluate(_run(_series(PHYSICAL_POWER)), player_stats=STATS)
    assert result["verdict"] == "H1"
    assert result["hypotheses"]["H1"]["verdict"] == "pass"
    assert result["hypotheses"]["H2"]["verdict"] == "fail"
    assert result["n_isolated_deltas"] == 30


def test_a_series_whose_deltas_equal_spell_power_survives_H2():
    result = powerstat.evaluate(_run(_series(SPELL_POWER)), player_stats=STATS)
    assert result["verdict"] == "H2"
    assert result["hypotheses"]["H2"]["verdict"] == "pass"
    assert result["hypotheses"]["H1"]["verdict"] == "fail"


def test_equal_power_stats_are_INDETERMINATE_and_never_a_winner():
    """The exact trap the default subject falls into. When the two predictions
    are within the band of each other the evidence cannot separate them, and a
    verdict would be an artefact of which branch was checked first."""
    equal = {"UnitStats.PhysicalPower": 77.0, "UnitStats.SpellPower": 77.0}
    result = powerstat.evaluate(_run(_series(77.0)), player_stats=equal)
    assert result["verdict"] == "indeterminate"
    assert result["separation"]["separable"] is False
    assert result["hypotheses"]["H1"]["verdict"] == "pass"
    assert result["hypotheses"]["H2"]["verdict"] == "pass"


def test_equal_t0_power_stats_are_a_PRECONDITION_not_an_afterthought():
    """MEASURED live 2026-08-01: on the test character armed against, both
    UnitStats.PhysicalPower and UnitStats.SpellPower read exactly 10. So the
    indeterminate branch is not hypothetical - it is what a default character
    produces, and the experiment is only separable when the CASTER's two power
    stats actually differ. No winner may be returned no matter how clean the
    deltas are, and that is checked before the deltas are even counted."""
    both_ten = {"UnitStats.PhysicalPower": 10.0, "UnitStats.SpellPower": 10.0}
    result = powerstat.evaluate(_run(_series(10.0)), player_stats=both_ten)
    assert result["verdict"] == "indeterminate"
    assert result["power_stats"]["separable"] is False
    assert result["power_stats"]["PhysicalPower"] == 10.0
    assert result["power_stats"]["SpellPower"] == 10.0


def test_equal_t0_power_stats_win_even_over_an_insufficient_delta_count():
    """The precondition is a property of the SUBJECT, not of the measurement.
    Collecting more deltas from the same caster cannot help."""
    both_ten = {"UnitStats.PhysicalPower": 10.0, "UnitStats.SpellPower": 10.0}
    result = powerstat.evaluate(_run(_series(10.0, hits=4)), player_stats=both_ten)
    assert result["verdict"] == "indeterminate"
    assert result["n_isolated_deltas"] == 4


def test_a_separable_caster_reports_both_power_stat_values_too():
    """The reader must be able to see WHY the run was or was not separable."""
    result = powerstat.evaluate(_run(_series(PHYSICAL_POWER)), player_stats=STATS)
    assert result["power_stats"]["PhysicalPower"] == PHYSICAL_POWER
    assert result["power_stats"]["SpellPower"] == SPELL_POWER
    assert result["power_stats"]["separable"] is True


def test_fewer_than_thirty_isolated_deltas_is_insufficient_not_a_pass():
    """C.1 sets n >= 30 because the gate is on a MEDIAN, which needs enough
    isolated deltas to be robust to a few mis-attributed windows."""
    result = powerstat.evaluate(_run(_series(PHYSICAL_POWER, hits=29)), player_stats=STATS)
    assert result["n_isolated_deltas"] == 29
    assert result["verdict"] == "insufficient_data"


def test_a_prefab_marker_sample_DISCARDS_the_run_rather_than_smoothing_it():
    """The prefab reads Health.Value 0, so a recorder latched onto it records a
    flat zero series that a naive reading turns into an instantaneous kill. The
    run is discarded WITH ITS REASON and never repaired."""
    rows = _series(PHYSICAL_POWER)
    rows[7]["carries_prefab_marker"] = True
    result = powerstat.evaluate(_run(rows), player_stats=STATS)
    assert result["verdict"] == "discarded"
    assert "carries_prefab_marker_true" in result["discard_reasons"]
    assert "hypotheses" not in result or result["hypotheses"] == {}


def test_a_flat_zero_series_is_discarded_rather_than_read_as_an_instant_kill():
    rows = _rows_from_values([0.0] * 64)
    for row in rows:
        row["carries_prefab_marker"] = True
    result = powerstat.evaluate(_run(rows), player_stats=STATS)
    assert result["verdict"] == "discarded"


def test_a_max_ape_outlier_fails_even_when_the_median_is_tight():
    """A tight median with one 300 percent outlier means one ability is modelled
    completely wrongly and the median hid it."""
    drops = [PHYSICAL_POWER] * 29 + [PHYSICAL_POWER * 4]
    result = powerstat.evaluate(_run(_series_from_drops(drops)), player_stats=STATS)
    assert result["n_isolated_deltas"] == 30
    assert result["hypotheses"]["H1"]["median_ape"] <= powerstat.MEDIAN_APE_BAND
    assert result["hypotheses"]["H1"]["max_ape"] > powerstat.MAX_APE_BAND
    assert result["hypotheses"]["H1"]["verdict"] == "fail"


def test_a_verdict_always_carries_the_sample_of_one_caveat_in_the_STRUCTURE():
    """A pass says which hypothesis survives on ONE row and does NOT prove the
    rule holds corpus-wide. That limit belongs in the returned structure, not in
    a docstring nobody reads."""
    result = powerstat.evaluate(_run(_series(PHYSICAL_POWER)), player_stats=STATS)
    assert result["sample_of_one"] is True
    assert WARD_NAME in result["caveat"]
    assert "corpus-wide" in result["caveat"]
    assert result["ability"]["prefab_guid"] == WARD_GUID


def test_the_caveat_is_present_even_on_a_discarded_run():
    rows = _series(PHYSICAL_POWER)
    rows[7]["carries_prefab_marker"] = True
    result = powerstat.evaluate(_run(rows), player_stats=STATS)
    assert result["sample_of_one"] is True
    assert result["caveat"]


def test_evaluate_reads_the_player_stats_from_the_manifest_when_not_passed():
    result = powerstat.evaluate(_run(_series(PHYSICAL_POWER)))
    assert result["verdict"] == "H1"


def test_evaluate_withholds_a_verdict_when_no_player_stats_can_be_sourced():
    """UNSOURCED, not zero. A power stat defaulted to 0 makes every prediction
    0 and every APE 100 percent, which reads as a decisive FAIL for both
    hypotheses when it is really an absent input."""
    run = {"rows": _series(PHYSICAL_POWER), "manifest": {}}
    result = powerstat.evaluate(run)
    assert result["verdict"] == "unsourced"


def test_a_flat_series_with_no_isolated_deltas_does_not_raise():
    """A REGRESSION TEST against a real recorded series.

    The recorder's first live run held 56 samples flat at 8107, because nothing
    on a headless dedicated server damages the boss. evaluate() reached
    statistics.median([]) and raised StatisticsError.

    A flat series is not a corner case. It is what an aborted run produces, what
    a recorder armed on the wrong subject produces, and above all what a
    recorder LATCHED ONTO THE PREFAB produces - the prefab reads Health.Value 0,
    so its series is perfectly flat. A traceback there is strictly worse than
    the naive reading the liveness controls exist to prevent, because it invites
    a re-run instead of an inspection of the run that was actually taken.
    """
    rows = [
        {
            "index": i,
            "captured_at": f"2026-08-01T17:43:{10 + i // 2:02d}.{(i % 2) * 502:03d}Z",
            "prefab_guid": -327335305,
            "carries_prefab_marker": False,
            "health_value": 8107.0,
            "health_max": 8107.0,
            "is_dead": False,
        }
        for i in range(56)
    ]
    stats = {"UnitStats.PhysicalPower": 90.0, "UnitStats.SpellPower": 30.0}
    result = powerstat.evaluate({"rows": rows, "manifest": {"player_unit_stats": stats}})

    # insufficient_data rather than indeterminate, and the distinction is the
    # point: this caster's two power stats DO differ (90 against 30), so the
    # subject is separable and the honest complaint is that the series carried
    # nothing to separate it with. Reporting indeterminate here would blame the
    # loadout for an empty recording.
    assert result["verdict"] == "insufficient_data", result["verdict"]
    for report in result["hypotheses"].values():
        assert report["verdict"] == "insufficient_data", report
        assert report["median_ape"] is None

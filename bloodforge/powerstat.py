"""P(G) - which power stat a coefficient multiplies, and the one row that decides.

Section 3 of the combat-math spec, in code. It is the single most important open
question in the engine: `power_stat` is PROVEN ABSENT from the data - no
power-selector member exists across all 51 components on the `_Hit` entity, and
`MainType` is the only discriminator present - and the `ability_stats` schema
forbids inferring it, saying outright that a consumer must not read `damage_type`
as a power selector without evidence the combat-math spec has not yet produced.

TWO HYPOTHESES SURVIVE.

  H1  `damage_type` selects. `MainType` Physical multiplies
      `UnitStats.PhysicalPower`, Spell multiplies `SpellPower`.
  H2  the ability KIND selects. A weapon ability multiplies `PhysicalPower`, a
      spell-school ability multiplies `SpellPower`, regardless of `MainType`.

THE DEFAULT SUBJECT VECTOR CANNOT SEPARATE THEM, and that finding is what makes
this module necessary rather than obvious. MEASURED over the promoted tables: 31
of the 32 distinct weapon-linked damage groups are `damage_type` physical, and
over 205 weapons `PhysicalPower AddToBase` appears on 203 while `SpellPower`
appears on exactly 1. So for every weapon ability a player will realistically
use, H1 and H2 predict THE SAME NUMBER, and a per-hit gate against GreatSword
versus Dracula passes at 2 percent under both and decides nothing. MEASURED:
ZERO rows are `is_weapon_ability` true with a non-physical `damage_type` and a
nonzero coefficient, so the weapon side is dead by EXHAUSTION, not by sampling -
which is why `weapon_side_candidates` exists and returns a list rather than a
bool. Only a count can retire a hypothesis.

EXACTLY ONE ROW IN 1818 SEPARATES THEM: `AB_Unholy_WardOfTheDamned_AbilityGroup`,
prefab_guid -1136860480, `spell_school` unholy so H2 predicts SpellPower,
`damage_type` physical so H1 predicts PhysicalPower. It is close to a designed
experiment. `coefficient` is exactly 1.0 and `hits_per_cast` is 1, so the
prediction is not "some arithmetic on a power stat" but literally "the observed
health delta EQUALS one of the two power stats" - no coefficient multiplication
to get wrong and no multi-hit aliasing inside a 250 ms window at 4 Hz. Every
near-inert term sits at its inert value, so nothing else can move the number.
`damage_type` physical means `reduction` is 0.0 and DEFINED, so the boss side
contributes nothing either. And it is `SpellSlot2`, so it is player-castable.
The experiment needs no boss, no V Blood and no health denominator, which makes
it the cheapest run in the whole protocol and the first one to take.

WHAT THIS MODULE REFUSES TO DO, in order of how tempting each is:

* Return a winner when the evidence cannot separate the hypotheses. When the two
  predictions land within the C.1 band of each other the verdict is
  INDETERMINATE, whatever the APEs say - that is the exact trap the default
  subject falls into, and a verdict there would be an artefact of which branch
  was checked first.
* Read a missing power stat as zero. A defaulted 0 makes every prediction 0 and
  every APE 100 percent, which reads as a decisive FAIL for both hypotheses when
  it is really an absent input.
* Smooth a series carrying the prefab marker. The prefab reads `Health.Value` 0,
  so a recorder latched onto it records a flat zero series that a naive reading
  turns into an instantaneous kill. Such a run is DISCARDED with its reason.
* Let a pass be read as a general law. One row is a sample of one. The caveat is
  returned IN THE STRUCTURE, not left in a docstring nobody reads.

This module does NOT implement the damage model - `bloodforge/damage.py` owns
that. `predict` computes the one narrow form the experiment needs and REFUSES
any row whose near-inert terms are not at their inert values, because the moment
`raw_damage_percent` is live the prediction needs `pool(T)`, which is UNSOURCED.

`isolated_deltas` and `per_hit_discard_reasons` come from `bloodforge/series.py`
and are shared verbatim with the writer, which re-exports them. Two copies of
the isolation rule could drift, and catching that class of divergence is what
the whole falsification protocol is for.
"""
from __future__ import annotations

import json
import statistics
from collections.abc import Mapping, Sequence
from pathlib import Path

from bloodforge.series import isolated_deltas, per_hit_discard_reasons
from core import tables

RMDATA_DIR = Path(__file__).resolve().parents[1] / "data" / "rmdata"

HYPOTHESES = ("H1", "H2")

MEDIAN_APE_BAND = 0.02
"""C.1 primary gate: median absolute percentage error over the isolated deltas.

2 percent and not a rounder number. The observed quantity is the game's own
arithmetic read through a control-verified typed accessor, so the residual error
sources are float32 rounding (well under 0.01 percent at these magnitudes),
passive regeneration inside one 250 ms window, and aliasing bounded by the
isolation requirement. 2 percent is about an order of magnitude above that floor
and an order of magnitude below the errors that matter: a wrong power stat moves
a per-hit number by tens of percent, which a 10 percent band would hide, while a
1 percent band would fail on regeneration alone.
"""

MAX_APE_BAND = 0.10
"""C.1 additionally: the MAXIMUM APE over the same n.

A tight median with one 300 percent outlier means one ability is modelled
completely wrongly and the median hid it.
"""

MIN_ISOLATED_DELTAS = 30
"""C.1 n. The gate is on a MEDIAN, which needs enough isolated deltas to be
robust to a few mis-attributed windows. If a real run comes back under 30 the
honest responses are to pool across comparable runs or to raise the tick rate
for the duration of a recording - NEVER to lower n."""

WARD_PREFAB_GUID = -1136860480
WARD_NAME = "AB_Unholy_WardOfTheDamned_AbilityGroup"

PHYSICAL_POWER_STAT = "PhysicalPower"
SPELL_POWER_STAT = "SpellPower"

_STAT_PREFIX = "UnitStats."
"""The wire spells player stats as UnitStats.PhysicalPower (the recorder's
player_unit_stats block). The bare name is accepted as a fallback so a hand-built
subject vector is not silently read as an absent stat."""

CAVEAT = (
    "ONE ROW IS A SAMPLE OF ONE. A pass says which hypothesis survives on "
    f"{WARD_NAME}, the only row in 1818 whose spell school and damage type "
    "disagree, and it does NOT prove the rule holds corpus-wide. It is the only "
    "evidence this build affords: 31 of the 32 weapon-linked damage groups are "
    "physical and zero rows are is_weapon_ability true with a non-physical "
    "damage type and a nonzero coefficient, so no second discriminator exists "
    "to corroborate it. That limit belongs in the ledger entry, not a footnote."
)


# ---------------------------------------------------------------------------
# Counting. Every number below is re-derived from the promoted rows.
# ---------------------------------------------------------------------------


def _current_build() -> str:
    return (RMDATA_DIR / "current.txt").read_text(encoding="utf-8").strip()


def load_ability_stats(build: str | None = None) -> list[dict]:
    """The promoted ability_stats rows, 1818 on this build."""
    path = (
        RMDATA_DIR
        / (build or _current_build())
        / tables.TABLES_DIRNAME
        / "ability_stats.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _has_damage_block(row: Mapping) -> bool:
    """The damage block is ALL-OR-NOTHING: 732 of 1818 rows carry one and every
    one of the 732 carries `coefficient`. A group that reaches no `_Hit` prefab
    omits the whole block, so presence of `coefficient` IS presence of damage."""
    return "coefficient" in row


def discriminators(rows: Sequence[Mapping] | None = None) -> list[dict]:
    """Every row that can separate H1 from H2: a SPELL-school ability whose
    `damage_type` is physical.

    Returns the FULL candidate list rather than one row, and that is the point.
    The number one is a measurement, not a constant: if a future build adds a
    second discriminator, the test asserting this list has exactly one member is
    what tells you, and the second row is then available for corroboration
    instead of being invisible behind a hardcoded guid.

    The filter is deliberately broad - a damage block, physical, any spell
    school - so a new candidate cannot be masked by an extra condition tuned to
    the row we already know about.
    """
    rows = load_ability_stats() if rows is None else rows
    return [
        dict(row)
        for row in rows
        if _has_damage_block(row)
        and row.get("damage_type") == "physical"
        and row.get("spell_school")
    ]


def weapon_side_candidates(rows: Sequence[Mapping] | None = None) -> list[dict]:
    """Every row that would separate the hypotheses from the WEAPON side.

    Empty on this build, and the emptiness is the finding: the weapon side is a
    dead end by EXHAUSTION rather than by sampling. The one weapon ability with
    `damage_type` spell, `AB_Spear_AThousandSpears_Stab_AbilityGroup`, carries
    `coefficient` a genuine 0.0, so it scales with no power stat at all and
    cannot discriminate either - which is why a nonzero coefficient is part of
    the filter and not an afterthought.
    """
    rows = load_ability_stats() if rows is None else rows
    return [
        dict(row)
        for row in rows
        if row.get("is_weapon_ability")
        and _has_damage_block(row)
        and row.get("damage_type") not in (None, "physical")
        and row.get("coefficient")
    ]


def ward_row(rows: Sequence[Mapping] | None = None) -> dict:
    """The discriminator row itself, looked up by guid.

    By guid rather than off `discriminators()[0]`, so that a change in the
    candidate SET fails the test that counts candidates rather than silently
    changing which row this returns.
    """
    rows = load_ability_stats() if rows is None else rows
    for row in rows:
        if row.get("prefab_guid") == WARD_PREFAB_GUID:
            return dict(row)
    raise LookupError(
        f"{WARD_NAME} ({WARD_PREFAB_GUID}) is not in the promoted ability_stats "
        "table - the one experiment that can decide P(G) has no subject on this build"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------


def _stat(player_stats: Mapping | None, name: str) -> float | None:
    """A live player stat, or None. NEVER 0.0 for an absent stat."""
    if not isinstance(player_stats, Mapping):
        return None
    for key in (f"{_STAT_PREFIX}{name}", name):
        value = player_stats.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return None


def _is_inert(row: Mapping) -> bool:
    """True when every near-inert damage term sits at its inert value.

    Each of these is correct-looking everywhere it is exercised and hides a
    small population where it is not: `raw_damage_value` is 0 on 731 of 732 rows,
    `raw_damage_percent` on 731, `damage_modifier_per_hit` on 729, and
    `vblood_damage_modifier` is 1.0 on 728. This module refuses any row where
    one is live, because the moment `raw_damage_percent` is nonzero the
    prediction needs `pool(T)` and nothing on disk says which pool that is.
    """
    for name in ("raw_damage_value", "raw_damage_percent", "damage_modifier_per_hit"):
        if row.get(name, 0):
            return False
    return row.get("vblood_damage_modifier", 1) == 1


def power_stat_for(hypothesis: str, row: Mapping) -> str | None:
    """Which UnitStats power stat the hypothesis says this row multiplies.

    None means the hypothesis SELECTS NOTHING for this row, which is a real and
    different statement from selecting a stat that happens to be zero.
    """
    if hypothesis not in HYPOTHESES:
        raise ValueError(f"unknown hypothesis {hypothesis!r}, expected one of {HYPOTHESES}")

    if hypothesis == "H1":
        return {
            "physical": PHYSICAL_POWER_STAT,
            "spell": SPELL_POWER_STAT,
        }.get(row.get("damage_type"))

    if row.get("is_weapon_ability"):
        return PHYSICAL_POWER_STAT
    if row.get("spell_school"):
        return SPELL_POWER_STAT
    return None


def predict(hypothesis: str, row: Mapping, player_stats: Mapping | None) -> float | None:
    """The predicted health delta for one CAST of `row` under `hypothesis`.

    `coefficient * P * hits_per_cast`, and nothing else. That is the whole model
    this module is entitled to: the discriminator's `damage_type` is physical so
    `reduction` is 0.0 and defined, its `vblood_damage_modifier` is 1.0, and
    every additive term is 0. The full term-by-term model lives in
    `bloodforge/damage.py`.

    None - never 0.0 - when the hypothesis selects no stat, when the stat is not
    in the recorded player block, or when any near-inert term is live.
    """
    stat = power_stat_for(hypothesis, row)
    if stat is None or not _is_inert(row):
        return None
    value = _stat(player_stats, stat)
    if value is None:
        return None
    coefficient = row.get("coefficient")
    if not isinstance(coefficient, (int, float)) or isinstance(coefficient, bool):
        return None
    hits = row.get("hits_per_cast", 1) or 1
    return float(coefficient) * value * float(hits)


# ---------------------------------------------------------------------------
# Evaluation against a recorded run
# ---------------------------------------------------------------------------


def caster_separability(player_stats: Mapping | None) -> dict:
    """Can THIS caster's two power stats tell H1 from H2 at all?

    A first-class PRECONDITION of the experiment, not a check on the result.
    MEASURED live 2026-08-01: on the test character the recorder armed against,
    UnitStats.PhysicalPower and UnitStats.SpellPower BOTH read exactly 10. The
    indeterminate branch is therefore not a hypothetical corner - it is what a
    default character produces, and the two hypotheses are separated only when
    the caster's two power stats actually differ.

    Both values are returned so a reader can see WHY a run was indeterminate
    rather than having to infer it from a verdict.
    """
    physical = _stat(player_stats, PHYSICAL_POWER_STAT)
    spell = _stat(player_stats, SPELL_POWER_STAT)
    report: dict = {
        PHYSICAL_POWER_STAT: physical,
        SPELL_POWER_STAT: spell,
        "relative_difference": None,
        "separable": False,
    }
    if physical is None or spell is None:
        report["reason"] = "a power stat was not recorded at t0"
        return report

    scale = max(abs(physical), abs(spell))
    relative = abs(physical - spell) / scale if scale else 0.0
    report["relative_difference"] = relative
    report["separable"] = relative > MEDIAN_APE_BAND
    if not report["separable"]:
        report["reason"] = (
            "the caster's PhysicalPower and SpellPower agree to within the C.1 "
            "band, so no series taken on this caster can separate H1 from H2. "
            "Collecting more deltas cannot help - re-run on a caster whose two "
            "power stats differ."
        )
    return report


def _apes(observed: Sequence[float], predicted: float) -> list[float] | None:
    if not predicted:
        return None
    return [abs(value - predicted) / abs(predicted) for value in observed]


def _hypothesis_report(
    hypothesis: str,
    row: Mapping,
    player_stats: Mapping | None,
    observed: Sequence[float],
) -> dict:
    predicted = predict(hypothesis, row, player_stats)
    report: dict = {
        "power_stat": power_stat_for(hypothesis, row),
        "predicted": predicted,
    }
    apes = _apes(observed, predicted) if predicted is not None else None
    if apes is None:
        report.update({"median_ape": None, "max_ape": None, "verdict": "unsourced"})
        return report

    if not apes:
        # ZERO isolated deltas. MEASURED against a real recorded series: the
        # first live run of the recorder held 56 samples flat at 8107, because
        # nothing on a headless server damages the boss, and statistics.median
        # raises StatisticsError on an empty list rather than reporting that
        # there was nothing to measure.
        #
        # It is not a corner case, it is one of the shapes this evaluator most
        # needs to survive. A flat series is what an aborted run, a recorder
        # armed on the wrong subject, and above all a recorder LATCHED ONTO THE
        # PREFAB all produce - the prefab reads Health.Value 0, so its series is
        # perfectly flat, and a crash there is strictly worse than the naive
        # reading the controls exist to prevent, because a traceback invites a
        # re-run rather than an inspection of the run that was taken.
        report.update({"median_ape": None, "max_ape": None,
                       "verdict": "insufficient_data"})
        return report

    report["median_ape"] = statistics.median(apes)
    report["max_ape"] = max(apes)
    if len(observed) < MIN_ISOLATED_DELTAS:
        report["verdict"] = "insufficient_data"
    elif report["median_ape"] <= MEDIAN_APE_BAND and report["max_ape"] <= MAX_APE_BAND:
        report["verdict"] = "pass"
    else:
        report["verdict"] = "fail"
    return report


def evaluate(
    run: Mapping,
    row: Mapping | None = None,
    player_stats: Mapping | None = None,
) -> dict:
    """Evaluate a recorded run against H1 and H2. Never returns an unearned winner.

    `run` is an anchor envelope: `rows` of samples plus, optionally, a
    `manifest` carrying `player_unit_stats` from the arm tick. `row` defaults to
    the discriminator and `player_stats` to the manifest block.

    The verdict ladder, in order, and every rung exists because of a specific way
    this could produce a confident wrong answer:

      discarded          the series failed a per-hit control. The prefab-marker
                         case is the one that matters: a flat zero series reads
                         as an instantaneous kill.
      unsourced          a power stat was not recorded. Not zero.
      indeterminate      the CASTER's PhysicalPower and SpellPower agree to
                         within the C.1 band, so no series taken on this caster
                         can separate the hypotheses. Checked BEFORE the deltas
                         are even counted, because it is a property of the
                         SUBJECT rather than of the measurement: collecting more
                         deltas from the same caster cannot help. MEASURED live -
                         both stats read exactly 10 on the character the recorder
                         armed against - so this is the ordinary case, not a
                         corner.
      insufficient_data  fewer than 30 isolated deltas. n is never lowered.
      H1 / H2            exactly one hypothesis survives the band.
      both_fail          neither does, which falsifies both and is a real result.

    Only the per-hit subset of A.5 is applied. A.5.3 marks a run that did not
    start from full health as `partial` and keeps it usable for the per-hit gate,
    and A.5.4's terminal sample supports a TTK denominator this experiment does
    not need.
    """
    row = ward_row() if row is None else dict(row)
    manifest = run.get("manifest") if isinstance(run, Mapping) else None
    if player_stats is None and isinstance(manifest, Mapping):
        player_stats = manifest.get("player_unit_stats")

    rows = list(run.get("rows", [])) if isinstance(run, Mapping) else []

    result: dict = {
        "ability": {"name": row.get("name"), "prefab_guid": row.get("prefab_guid")},
        "sample_of_one": True,
        "caveat": CAVEAT,
        "bands": {
            "median_ape": MEDIAN_APE_BAND,
            "max_ape": MAX_APE_BAND,
            "min_isolated_deltas": MIN_ISOLATED_DELTAS,
        },
        "discard_reasons": per_hit_discard_reasons(rows),
        "hypotheses": {},
    }

    if result["discard_reasons"]:
        result["n_isolated_deltas"] = 0
        result["verdict"] = "discarded"
        return result

    deltas = isolated_deltas(rows)
    observed = [delta["delta"] for delta in deltas]
    result["n_isolated_deltas"] = len(observed)
    result["power_stats"] = caster_separability(player_stats)

    predictions = {h: predict(h, row, player_stats) for h in HYPOTHESES}
    if any(value is None for value in predictions.values()):
        result["verdict"] = "unsourced"
        result["hypotheses"] = {
            h: _hypothesis_report(h, row, player_stats, observed) for h in HYPOTHESES
        }
        return result

    first, second = (predictions[h] for h in HYPOTHESES)
    scale = max(abs(first), abs(second))
    relative = abs(first - second) / scale if scale else 0.0
    result["separation"] = {
        "predicted_H1": first,
        "predicted_H2": second,
        "relative_difference": relative,
        "separable": relative > MEDIAN_APE_BAND,
    }

    result["hypotheses"] = {
        h: _hypothesis_report(h, row, player_stats, observed) for h in HYPOTHESES
    }

    if not result["power_stats"]["separable"]:
        # THE PRECONDITION, and it outranks every other rung below: no winner
        # may be returned no matter how clean or how numerous the deltas are.
        result["verdict"] = "indeterminate"
        return result

    if len(observed) < MIN_ISOLATED_DELTAS:
        result["verdict"] = "insufficient_data"
        return result

    if not result["separation"]["separable"]:
        result["verdict"] = "indeterminate"
        return result

    survivors = [h for h in HYPOTHESES if result["hypotheses"][h]["verdict"] == "pass"]
    if len(survivors) == 1:
        result["verdict"] = survivors[0]
    elif survivors:
        result["verdict"] = "indeterminate"
    else:
        result["verdict"] = "both_fail"
    return result

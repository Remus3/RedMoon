"""Section 2 of the combat math spec: damage for ONE application of an ability.

  base(G)       = coefficient(G) * P(G)
                + raw_damage_value(G)
                + raw_damage_percent(G) * pool(T)

  per_hit(G,i)  = base(G) * (1 + damage_modifier_per_hit(G) * (i - 1))

  cast(G)       = sum over i = 1..hits_per_cast of per_hit(G,i)

  vs_class(G,T) = cast(G) * vblood_damage_modifier(G)

  applied(G,T)  = vs_class(G,T) * (1 - reduction(T, damage_type(G)))

`applied` is the quantity the falsification spec's C.1 gate compares against an
isolated Health.Value delta at 2 percent median APE. Nothing here is validated:
no anchor run exists, and publication of anything derived from these numbers
goes through bloodforge.embargo.apply_embargo, which this module never calls and
never routes around.

THE CENTRAL DESIGN CHOICE: three of the five terms above are UNSOURCED on this
build, and each one is unsourced in a different way. A function that returned a
float regardless would be inventing a number in three places at once, so every
entry point here returns either a float or an Undefined carrying the reason it
has nothing to say. Undefined supports no arithmetic at all - no __float__, no
__sub__ - so a caller who forgets to check gets a TypeError at the first
operation rather than a plausible wrong number four calls downstream. That is
the items.tier / vbloods.max_health / ability_stats.power_stat idiom one level
down: the absence is the honest signal and a zero would be a lie.

The three holes, and what closes each:

  P(G)                 UNDEFINED. power_stat is PROVEN ABSENT from the data and
                       two hypotheses are live. Closed by the section 3.3
                       experiment. Modelled here as a REQUIRED keyword argument
                       so that computing a damage number forces the caller to
                       name which hypothesis it is computing under. There is no
                       default anywhere in this module and there must never be
                       one.
  pool(T)              UNSOURCED. Nothing on disk says whether a percent term
                       fractions current health, max health, or the caster's.
                       Closed by recording one AB_Shapeshift_Golem_T02_Group
                       application against two targets of different max health.
  reduction(T, fire)   UNDEFINED. An integer RATING needing the unread global
  reduction(T, holy)   constant ResistanceData.FireResistance_DamageReduction-
                       PerRating (ROADMAP gap 8); holy has no unit-side field at
                       all across 150 enumerated components. 42 of 732 damage
                       groups are withheld between them.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

# ---------------------------------------------------------------------------
# Withheld reasons
# ---------------------------------------------------------------------------

NO_DAMAGE_BLOCK = "no_damage_block"
"""The group reaches no _Hit prefab, so it declares no damage at all.

DIFFERENT from a coefficient of 0.0, and the difference is load-bearing. The
block is all-or-nothing over the promoted corpus: zero of the 732 damage rows
omit coefficient, and a group that reaches nothing omits all five block fields
together. AB_Spear_AThousandSpears_Stab_AbilityGroup carries a genuine 0.0;
AB_Vampire_Longbow_Primary_AbilityGroup carries no block whatever.
"""

UNDEFINED_REDUCTION = "undefined_reduction"
"""The target has no readable reduction for this damage type. Holy and fire."""

UNSOURCED_POOL = "unsourced_pool"
"""raw_damage_percent is nonzero and nothing on disk says which pool it is of."""

UNDEFINED_POWER_STAT = "undefined_power_stat"
"""The chosen hypothesis assigns no power stat to this ability."""


@dataclass(frozen=True)
class Undefined:
    """A computation that produced NO NUMBER, and why.

    Deliberately not a float subclass, not None, and not zero. It carries no
    numeric protocol, so any arithmetic on it raises TypeError immediately.
    """

    reason: str
    detail: str = ""


def defined(value: float | Undefined) -> bool:
    """True when value is a real number rather than a withheld one."""
    return not isinstance(value, Undefined)


# ---------------------------------------------------------------------------
# 2.2 reduction, a PARTIAL function on three of five damage types
# ---------------------------------------------------------------------------

DEFINED_REDUCTION_TYPES = frozenset({"physical", "spell", "corruption"})
"""The three types with a readable unit-side field.

  physical    -> UnitStats.PhysicalResistance,        reads 0.0 on all 65 bosses
  spell       -> UnitStats.SpellResistance,           reads 0.0 on all 65
  corruption  -> UnitStats.CorruptionDamageReduction, reads 0.5 on all 65

Because fire is the only resistance that VARIES across the 65 and it is exactly
the one that cannot be priced, every priceable boss on this build differs from
every other only by level-derived power and by health.
"""

UNDEFINED_REDUCTION_TYPES = frozenset({"fire", "holy"})
"""The two that withhold 42 of the 732 damage groups: 27 holy and 15 fire."""

# THE AVERAGING PROHIBITION. The four values a unit carries are NOT
# commensurable and must never be combined into one number: physical and spell
# are float resistances, corruption is already a reduction, and fire is an
# integer rating on a scale whose conversion constant has not been read. There
# is deliberately no aggregate in this module - no mean, no scalar summary - and
# tests/test_damage.py asserts on both the API surface and this source that none
# appears. The same prohibition is why bloodforge publishes EHP as a MAP of
# damage type to value and never as one scalar.

_FIRE_DETAIL = (
    "fire resistance is an integer RATING, not a reduction; it needs the "
    "unread global ResistanceData.FireResistance_DamageReductionPerRating "
    "(ROADMAP gap 8). It is 0 on 61 bosses and 50, 50, 70 or 75 on 4."
)
_HOLY_DETAIL = (
    "no holy field exists on the unit at all, proven absent across 150 "
    "enumerated components. There is nothing to convert."
)
_UNKNOWN_DETAIL = (
    "damage type is outside the five that appear on the promoted corpus; "
    "MainType declares ten members and no unit-side field was measured for it."
)


def reduction(target: Mapping, damage_type: str) -> float | Undefined:
    """The fraction of incoming damage of this type that the target removes.

    Returns a float ONLY for the three defined types. A returned 0.0 is a real
    claim - this boss takes full physical damage - and is a different statement
    from the Undefined that fire and holy return. Callers must handle the
    undefined case and must never default it to zero: doing so would publish
    full-damage numbers against the four bosses that actually carry a fire
    rating.
    """
    if damage_type in DEFINED_REDUCTION_TYPES:
        resistances = target.get("resistances")
        if not isinstance(resistances, Mapping) or damage_type not in resistances:
            return Undefined(
                UNDEFINED_REDUCTION,
                f"target carries no readable {damage_type} resistance",
            )
        return float(resistances[damage_type])
    if damage_type == "fire":
        return Undefined(UNDEFINED_REDUCTION, _FIRE_DETAIL)
    if damage_type == "holy":
        return Undefined(UNDEFINED_REDUCTION, _HOLY_DETAIL)
    return Undefined(UNDEFINED_REDUCTION, _UNKNOWN_DETAIL)


# ---------------------------------------------------------------------------
# 3. P(G), which the caller must name
# ---------------------------------------------------------------------------


class PowerHypothesis(Enum):
    """The two live hypotheses for which power stat a coefficient multiplies.

    Neither is decided. power_stat is PROVEN ABSENT from the data: no
    power-selector member exists across all 51 components on the _Hit entity,
    and MainType is the only discriminator present.

    DAMAGE_TYPE_SELECTS (H1): MainType Physical multiplies PhysicalPower and
    Spell multiplies SpellPower. Stated over those two members ONLY, so it
    assigns nothing to a corruption, fire or holy MainType. That is a
    consequence of the hypothesis as written and is reported as undefined rather
    than papered over.

    ABILITY_KIND_SELECTS (H2): a weapon ability multiplies PhysicalPower and a
    spell-school ability multiplies SpellPower, regardless of MainType. Readable
    only where WeaponAbilityData or a spell school is present, which over the
    732 damage rows is 26 plus 18; the other 688 are NPC abilities carrying
    neither, and H2 is silent on all of them.

    The default subject vector cannot separate the two: 31 of the 32 distinct
    weapon-linked damage groups are physical, and the one that is not has
    coefficient 0.0. AB_Unholy_WardOfTheDamned_AbilityGroup is the only row in
    1818 where they predict different numbers - spell school unholy, MainType
    physical, coefficient exactly 1.0, one hit - which makes its prediction
    literally "the observed health delta equals one of the two power stats".
    """

    DAMAGE_TYPE_SELECTS = "H1"
    ABILITY_KIND_SELECTS = "H2"


@dataclass(frozen=True)
class PlayerPower:
    """The caster's two live power stats, read from the same tick.

    Both come from StateReader's UnitStats. Nothing else belongs in here: crit
    is NOT ATTEMPTED (SpellCriticalStrikeChance appears on 1 of 205 weapons and
    no multiplier is sourced) and blood bonuses are DECLARED AND OMITTED (all 13
    blood_types rows carry stat NAMES with value_source
    blood_quality_scaled_at_runtime and no magnitudes at all).
    """

    physical_power: float
    spell_power: float


def power_stat(
    row: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> tuple[str, float] | Undefined:
    """Return (stat name, value) for P(G) under the named hypothesis.

    hypothesis and player are REQUIRED keyword arguments with no defaults, here
    and in every function below that reaches this one. That is the whole point:
    a damage number cannot be produced without naming the hypothesis it was
    produced under, so no caller can accidentally publish one hypothesis's
    answer as if it were settled.
    """
    if hypothesis is PowerHypothesis.DAMAGE_TYPE_SELECTS:
        kind = row.get("damage_type")
        if kind == "physical":
            return ("PhysicalPower", player.physical_power)
        if kind == "spell":
            return ("SpellPower", player.spell_power)
        return Undefined(
            UNDEFINED_POWER_STAT,
            f"H1 selects on MainType and is stated over Physical and Spell "
            f"only; this group is {kind!r}",
        )

    if hypothesis is PowerHypothesis.ABILITY_KIND_SELECTS:
        # Measured: 0 of 732 damage rows carry both, so the order below is not
        # a tie-break that anything currently exercises.
        if row.get("is_weapon_ability"):
            return ("PhysicalPower", player.physical_power)
        if "spell_school" in row:
            return ("SpellPower", player.spell_power)
        return Undefined(
            UNDEFINED_POWER_STAT,
            "H2 selects on the ability KIND and this group carries neither "
            "WeaponAbilityData nor a spell school, so it has no readable kind",
        )

    raise ValueError(f"unknown power hypothesis: {hypothesis!r}")


# ---------------------------------------------------------------------------
# 2.1 the equation
# ---------------------------------------------------------------------------

_BLOCK_FIELDS = (
    "coefficient",
    "raw_damage_value",
    "raw_damage_percent",
    "damage_type",
    "hits_per_cast",
)


def has_damage_block(row: Mapping) -> bool:
    """True when the group reached a _Hit prefab and declares damage.

    All five fields or none: measured over the promoted corpus, 732 of 1818 rows
    carry every one and 1086 carry not one of them.
    """
    return all(field in row for field in _BLOCK_FIELDS)


def base(
    row: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """coefficient * P + raw_damage_value + raw_damage_percent * pool.

    No target is taken because the third term is either zero - on 731 of 732
    rows - or unsourced. When raw_damage_percent is nonzero the pool is unknown
    and there is no number to give, so a target would not help.

    That third term is what makes the golem story coherent.
    AB_Shapeshift_Golem_T02_Group has coefficient 0 AND raw_damage_percent 0.3
    together, so a model reading only the coefficient prices every golem ability
    at exactly zero instead of withholding it, and reports a confident nothing.
    """
    if not has_damage_block(row):
        return Undefined(
            NO_DAMAGE_BLOCK,
            "the group reaches no _Hit prefab; this is not a coefficient of 0.0",
        )

    if row["raw_damage_percent"]:
        return Undefined(
            UNSOURCED_POOL,
            "raw_damage_percent is a fraction of a pool and nothing on disk "
            "says which - current health, max health, or the caster's",
        )

    power = power_stat(row, hypothesis=hypothesis, player=player)
    if isinstance(power, Undefined):
        return power
    _, value = power

    return row["coefficient"] * value + row["raw_damage_value"]


def per_hit(
    row: Mapping,
    index: int,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """Damage of the index-th hit of one cast, index counted from 1.

    THE RAMP FORM IS AN ARBITRARY, UNTESTED CHOICE. Three forms fit the field
    name damage_modifier_per_hit equally well: the linear ramp implemented here,
    a geometric one, and a flat modifier applied to every hit after the first.
    The schema records only that phase 1 named the field alongside the stacks
    flag as the two that exist for repeated hits.

    It is UNOBSERVABLE on this build. The field is nonzero on 3 of 732 rows -
    AB_Prog_Boomerang_Group -0.2, AB_Frost_CrystalLance_AbilityGroup +0.5,
    AB_Illusion_WraithSpear_AbilityGroup -0.25 - and all three have
    hits_per_cast 1, which makes (index - 1) zero and the whole term identically
    zero in every computation this engine can currently perform. The three forms
    therefore cannot be told apart by anything on disk.

    tests/test_damage.py pins those three rows. If a future build gives a
    multi-hit ability a nonzero modifier, that test is what fails, and this
    docstring is what the person reading the failure needs.
    """
    if index < 1:
        raise ValueError(f"hit index is 1-based, got {index}")
    if has_damage_block(row) and index > row["hits_per_cast"]:
        raise ValueError(
            f"hit index {index} exceeds hits_per_cast {row['hits_per_cast']}"
        )

    value = base(row, hypothesis=hypothesis, player=player)
    if isinstance(value, Undefined):
        return value
    return value * (1.0 + row["damage_modifier_per_hit"] * (index - 1))


def cast(
    row: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """Total damage of one cast, over hits_per_cast hits.

    hits_per_cast is the LENGTH of the _Hit entity's DealDamageOnGameplayEvent
    buffer - a measured count, range 1 to 4 over the corpus with no zeros.
    """
    value = base(row, hypothesis=hypothesis, player=player)
    if isinstance(value, Undefined):
        return value

    total = 0.0
    for index in range(1, row["hits_per_cast"] + 1):
        total += value * (1.0 + row["damage_modifier_per_hit"] * (index - 1))
    return total


def vs_class(
    row: Mapping,
    target: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """One cast against a V Blood, after the per-target-CLASS multiplier.

    IMPLEMENTED EVEN THOUGH IT IS 1.0 ON 728 OF 732 ROWS, and 1.0 on all 409
    weapon-linked damage rows, because being 1.0 almost everywhere is exactly
    what makes an omission invisible. Dropping the term would be correct in 99.5
    percent of cases and silently wrong on the 4 golem-form NPC abilities that
    carry 0.33 - the ones nobody would think to check.

    ProjectM.EntityTypeModifiers carries 23 such multipliers. VBlood is the one
    a boss time-to-kill multiplies by and the only one read here; the other 22
    are real, readable by the same hop, and NOT ATTEMPTED because no cycle 3
    consumer reads them. The target argument is taken because the multiplier is
    conditional on the target's class, and every row of the vbloods table is by
    construction a V Blood.
    """
    total = cast(row, hypothesis=hypothesis, player=player)
    if isinstance(total, Undefined):
        return total
    return total * row["vblood_damage_modifier"]


def applied(
    row: Mapping,
    target: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """Damage actually taken by the target from one cast.

    The reduction is checked BEFORE the power stat so that a holy or fire
    ability reports the target-side blocker. That ordering carries information:
    an undefined reduction cannot be fixed by running the section 3.3
    experiment, while an undefined power stat can.
    """
    if not has_damage_block(row):
        return Undefined(
            NO_DAMAGE_BLOCK,
            "the group reaches no _Hit prefab; this is not a coefficient of 0.0",
        )

    removed = reduction(target, row["damage_type"])
    if isinstance(removed, Undefined):
        return removed

    dealt = vs_class(row, target, hypothesis=hypothesis, player=player)
    if isinstance(dealt, Undefined):
        return dealt
    return dealt * (1.0 - removed)


# NOT IN THE MODEL, each deliberately and each for a measured reason.
#
# hit_triggers                     0 on all 732 damage rows, one distinct
#                                  value. It carries no information on this
#                                  build, so a model that read it would be
#                                  fitting a constant and would look like it
#                                  was doing something.
# multiply_main_factor_with_stacks false on all 732. Same.
# crit                             SpellCriticalStrikeChance appears on 1 of
#                                  205 weapons and no crit multiplier is
#                                  sourced anywhere. NOT ATTEMPTED.
# blood bonuses                    all 13 blood_types rows carry stat NAMES
#                                  with value_source
#                                  blood_quality_scaled_at_runtime and no
#                                  magnitudes. DECLARED AND OMITTED.
# jewels, passives, gear sets      no source measured at all.

"""Section 4 of the combat math spec: damage per second, and its denominator.

  ability_dps(G,T) = applied(G,T) / cycle(G)

  cycle(G) = max( cast_time(G) + post_cast_time(G),
                  cooldown(G),
                  global_cooldown(G) )

THE CYCLE IS A MAXIMUM, NOT A SUM. The three windows OVERLAP: a cooldown runs
DURING the cast, not after it. Summing them understates the cycle and therefore
overstates DPS on every cooldown ability in the corpus, and it does so quietly -
the answer stays plausible, just wrong. On AB_Frost_CrystalLance_AbilityGroup
the sum is 9.45 seconds against a true 8.0.

The max form is also what makes a primary attack computable at all. cooldown
reads 0 on 352 of the 1818 promoted rows, so a cycle taken from the cooldown
alone would divide by zero on every one of them; those get their cycle from cast
plus recovery instead.

Nothing here is validated and nothing here publishes. Every quantity is
INTERNAL, and the gate between it and a user surface is
bloodforge.embargo.apply_embargo, which strips the whole family until an anchor
run lifts it. This module never calls it and never routes around it.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from bloodforge.damage import (
    PlayerPower,
    PowerHypothesis,
    Undefined,
    applied,
)

UNDEFINED_CYCLE = "undefined_cycle"
"""The ability declares no usable time window, so it has no denominator.

Two populations, both measured and both small. Three of 1818 rows carry neither
cast_time nor post_cast_time - the cast hop did not resolve for them - and two
more declare every window at zero. Dividing by either is not a very large DPS;
it is no DPS.
"""

_MISSING_CAST = (
    "the group reaches no _Cast entity, so it declares neither cast_time nor "
    "post_cast_time and has no time window to divide by"
)
_ZERO_CYCLE = (
    "every declared window is zero, so the ability has no duration to spread "
    "its damage over"
)


def cycle(row: Mapping) -> float | Undefined:
    """The seconds one use of this ability occupies, as a MAXIMUM.

    MEASURED coverage over the 1818 promoted rows: cast_time on 1815,
    post_cast_time on 1815 (the same three rows lack both), cooldown on all
    1818, global_cooldown on 1691.

    An absent global_cooldown is DROPPED from the maximum. That is
    arithmetically identical to treating it as zero here - it can only lose a
    max against non-negative terms - and it is written as a drop rather than a
    default so that the same code cannot be copied into a sum, where the two
    would differ.

    A row missing cast_time has an UNDEFINED cycle. It is not recoverable from
    the cooldown alone: an ability with a 7 second cooldown and an unknown cast
    might occupy 7 seconds or 12, and the difference is the whole answer.
    """
    if "cast_time" not in row or "post_cast_time" not in row:
        return Undefined(UNDEFINED_CYCLE, _MISSING_CAST)

    windows = [row["cast_time"] + row["post_cast_time"]]
    if "cooldown" in row:
        windows.append(row["cooldown"])
    if "global_cooldown" in row:
        windows.append(row["global_cooldown"])
    return float(max(windows))


def ability_dps(
    row: Mapping,
    target: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> float | Undefined:
    """Sustained damage per second of repeating this ONE ability forever.

    hypothesis and player are required keyword arguments for the reason given in
    bloodforge.damage: P(G) is undecided, so a number cannot be produced without
    naming which hypothesis produced it.

    A withheld numerator propagates upward with its reason intact, so a consumer
    can render a degraded-mode message that says WHY rather than a bare dash.
    The numerator is evaluated first because its blockers are the informative
    ones: a group with no damage block still has a perfectly good denominator,
    which is exactly the state a model reading only timings would miss.
    """
    numerator = applied(row, target, hypothesis=hypothesis, player=player)
    if isinstance(numerator, Undefined):
        return numerator

    denominator = cycle(row)
    if isinstance(denominator, Undefined):
        return denominator
    if denominator == 0.0:
        return Undefined(UNDEFINED_CYCLE, _ZERO_CYCLE)

    return numerator / denominator


@dataclass(frozen=True)
class WeaponDps:
    """A weapon-level number that cannot be separated from its caveat.

    The number and the two lists are ONE object on purpose. Section 1.5 of the
    spec makes the labelling non-negotiable: the default weapon
    Item_Weapon_GreatSword_Legendary_T08 carries three ability group links and
    two of them - LeapAttack and GreatCleaver - reach no damage block at all, so
    two thirds of the default weapon's kit is unpriceable. A caller handed a
    bare float would render it as "the GreatSword's DPS" and be wrong by
    everything the other two abilities do.
    """

    dps: float | Undefined
    priced: tuple[str, ...]
    unpriceable: tuple[str, ...]
    label: str


def weapon_sustained_dps(
    item_row: Mapping,
    stats_by_guid: Mapping[int, Mapping],
    target: Mapping,
    *,
    hypothesis: PowerHypothesis,
    player: PlayerPower,
) -> WeaponDps:
    """Sustained DPS of a weapon's single best priceable ability, plus its lists.

    ROTATION DPS IS NOT ATTEMPTED, and this is not it. A loadout's real DPS
    requires an ability ORDERING and nothing on disk supplies one:
    AbilityGroupInfo.MinRange and MaxRange exist and are not modelled, while
    positioning, weaving and cooldown alignment have no source whatever. A
    rotation DPS would be a model of a PLAYER presented as a property of a
    WEAPON. So this helper does NOT sum its groups - summing is the shape a
    rotation takes - it reports the largest single-ability figure and names the
    ability it came from.

    A DESIGN CHOICE THE SPEC DID NOT SETTLE. Section 4.2 calls the publishable
    weapon figure a PRIMARY-ONLY sustained DPS, but section 1.4 measured that
    ability_type reads Secondary on every weapon primary in the corpus and that
    slot cannot be derived from that field (proposed ROADMAP gap 11). Nothing
    else on disk identifies a primary either. So this function does not claim to
    have found the primary: it takes the best PRICED group and puts that group's
    name in the label. On the default GreatSword the two coincide, because the
    primary is the only group that reaches damage at all.
    """
    guids = list(item_row.get("ability_group_guids", ()))

    priced: list[str] = []
    unpriceable: list[str] = []
    best_name = ""
    best: float | None = None

    for guid in guids:
        row = stats_by_guid.get(guid)
        if row is None:
            unpriceable.append(f"prefab_guid {guid}")
            continue
        name = row.get("name", f"prefab_guid {guid}")
        value = ability_dps(row, target, hypothesis=hypothesis, player=player)
        if isinstance(value, Undefined):
            unpriceable.append(name)
            continue
        priced.append(name)
        if best is None or value > best:
            best = value
            best_name = name

    total = len(guids)
    if best is None:
        headline: float | Undefined = Undefined(
            "no_priceable_group",
            f"all {total} linked ability groups of "
            f"{item_row.get('name', 'this weapon')} are unpriceable",
        )
        label = (
            f"no sustained single-ability DPS: 0 of {total} linked ability "
            f"groups priced"
        )
    else:
        headline = best
        label = (
            f"sustained single-ability DPS, {best_name}; "
            f"{len(priced)} of {total} linked ability groups priced, "
            f"{len(unpriceable)} unpriceable"
        )

    return WeaponDps(
        dps=headline,
        priced=tuple(priced),
        unpriceable=tuple(unpriceable),
        label=label,
    )

"""Pure functions over a recorded health series. No CLI, no IO, no bridge.

WHAT THIS MODULE IS FOR. A recorded run is a list of health samples, and two
different consumers ask questions of it: `tools/anchor_record.py` writes the run
and runs the A.5 checklist over it, and `bloodforge/powerstat.py` evaluates the
section 3.3 power-stat experiment against it. Both need the SAME isolation rule
and the SAME discard reasons.

They used to get them by the engine importing the writer, which is the wrong
direction - `bloodforge/` is the engine and `tools/` is a script. The other
option on the table was to duplicate the two functions, which is worse: two
copies of the isolation rule can drift, and catching that class of silent
divergence is the entire reason the falsification protocol exists. So the pure
layer lives here, the writer re-exports it, and `tests/test_series.py` asserts
the re-export by IDENTITY so a future copy-paste fails loudly.

NOTHING HERE MAY TREAT THE SAMPLE RATE AS A CONSTANT. `SampleEveryFrames = 15`
(`Plugin.cs:41`) is a FRAME count, so the rate is frames-per-sample times the
HOST's frame rate and the two hosts do not share one. MEASURED 2026-08-01 on a
live dedicated server: median interval 0.502 s over n=55, which is 1.99 Hz at
29.9 fps under -batchMode -nographics, against the 4 Hz both cycle 3 specs
assume. The client rate is still unmeasured. Every threshold and every reported
cadence in this module is derived from the series being examined (ROADMAP
gap 12).
"""
from __future__ import annotations

import statistics
from collections.abc import Mapping, Sequence
from datetime import datetime

GAP_TICK_MULTIPLE = 3
"""A.5.5, as the spec actually states the rule: no gap greater than 3 TICK
INTERVALS. The spec's parenthesised "about 750 ms" is only true at 4 Hz - at the
measured 1.99 Hz three intervals is about 1506 ms, so a hardcoded 750 ms would
discard a run for a single stalled tick that the rule permits. The threshold is
computed from the observed median interval of the series being checked.

Known limit, stated rather than discovered later: a series that stalls for MOST
of its length raises its own median and hides the stall. The gap check catches
an isolated stall, which is what it is for; a systematically slow run is caught
by the manifest stating a cadence that does not match the comparison run's.
"""


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def parse_stamp(text: str) -> datetime:
    """Parse a UTC ISO 8601 instant, with or without a fractional part.

    Tolerant of both the wire's millisecond form and a microsecond one, because
    a stamp that cannot be parsed is indistinguishable from a stalled tick and
    would discard the run for the wrong reason.
    """
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def sample_intervals(rows: Sequence[Mapping]) -> list[float]:
    """Seconds between consecutive stamped samples, in order."""
    moments: list[datetime] = []
    for row in rows:
        text = row.get("captured_at")
        if not text:
            continue
        moments.append(parse_stamp(text))
    return [
        (later - earlier).total_seconds()
        for earlier, later in zip(moments, moments[1:], strict=False)
    ]


def observed_cadence(rows: Sequence[Mapping]) -> dict:
    """The cadence a series was ACTUALLY taken at, measured from its own stamps.

    Sourced from the series or ABSENT. There is no nominal rate to fall back on:
    the rate is frames-per-sample times the HOST's frame rate, the two hosts do
    not share one, and neither has been measured at 60 fps. A run that does not
    state its cadence cannot be compared with one taken on the other host - the
    cycle 2 lesson exactly, where a real measurement answered the right question
    about the wrong subject.
    """
    intervals = sample_intervals(rows)
    if not intervals:
        return {
            "observed_sample_interval_s_median": None,
            "observed_sample_rate_hz": None,
            "gap_threshold_s": None,
            "observed_sample_interval_s_min": None,
            "observed_sample_interval_s_max": None,
            "interval_count": 0,
        }
    median = statistics.median(intervals)
    return {
        "observed_sample_interval_s_median": median,
        "observed_sample_rate_hz": (1.0 / median) if median else None,
        "gap_threshold_s": GAP_TICK_MULTIPLE * median,
        "observed_sample_interval_s_min": min(intervals),
        "observed_sample_interval_s_max": max(intervals),
        "interval_count": len(intervals),
    }


# ---------------------------------------------------------------------------
# The per-hit subset of the A.5 validity checklist. Named reasons, never a bool.
# ---------------------------------------------------------------------------


def _gap_exceeded(rows: Sequence[Mapping]) -> bool:
    """True when any interval exceeds GAP_TICK_MULTIPLE times the OBSERVED median.

    The threshold comes from the series, never from a constant. See
    GAP_TICK_MULTIPLE for why the spec's "about 750 ms" cannot be hardcoded.
    """
    try:
        intervals = sample_intervals(rows)
    except ValueError:
        return True  # an unparseable stamp is not a series that can be integrated
    if not intervals:
        return False
    threshold = GAP_TICK_MULTIPLE * statistics.median(intervals)
    return any(interval > threshold for interval in intervals)


def per_hit_discard_reasons(
    rows: Sequence[Mapping],
    queried_guid: int | None = None,
) -> list[str]:
    """The subset of A.5 that a PER-HIT run must pass, as named reasons.

    A.5.3 says a run that did not start from full health is marked `partial` and
    is excluded from the TTK gate WHILE REMAINING USABLE for the per-hit gate,
    and A.5.4's terminal sample and A.5.6's manifest exist to support a TTK
    denominator. None of that is needed to compare one isolated delta against a
    predicted hit, and the section 3.3 power-stat experiment needs no boss, no
    V Blood and no denominator at all - it is the cheapest run in the protocol
    precisely because this subset is all it has to satisfy.
    """
    reasons: list[str] = []

    if any(row.get("carries_prefab_marker") for row in rows):
        reasons.append("carries_prefab_marker_true")

    live = [
        row
        for row in rows
        if not row.get("carries_prefab_marker") and (row.get("health_max") or 0) > 0
    ]
    if not live:
        reasons.append("no_live_sample")

    if queried_guid is not None and any(
        row.get("prefab_guid") != queried_guid for row in rows
    ):
        reasons.append("prefab_guid_mismatch")

    if _gap_exceeded(rows):
        reasons.append("tick_gap_exceeded")

    return reasons


# ---------------------------------------------------------------------------
# Isolated deltas
# ---------------------------------------------------------------------------


def isolated_deltas(rows: Sequence[Mapping]) -> list[dict]:
    """Every health drop bracketed by at least one NO-CHANGE sample on each side.

    That bracketing is the only available evidence that a window contained
    exactly one ability application. A 4 Hz series cannot isolate every hit -
    abilities with hits_per_cast up to 4 exist and several land inside one
    250 ms window - so the protocol does not attempt to attribute every delta.
    It refuses the ones it cannot, and the per-hit gate runs over what is left.

    A health INCREASE is never a delta: passive regeneration is readable and is
    deliberately not part of the anchor-time model, and a heal is not a hit.
    """
    found: list[dict] = []
    for i in range(1, len(rows) - 1):
        window = (rows[i - 2] if i >= 2 else None, rows[i - 1], rows[i], rows[i + 1])
        before_before, before, current, after = window
        if before_before is None:
            continue
        if any(row.get("carries_prefab_marker") for row in window):
            continue

        values = [row.get("health_value") for row in window]
        if any(value is None for value in values):
            continue

        quiet_left = values[0] == values[1]
        quiet_right = values[2] == values[3]
        drop = values[1] - values[2]
        if drop <= 0 or not (quiet_left and quiet_right):
            continue

        found.append(
            {
                "index": current.get("index", i),
                "captured_at": current.get("captured_at"),
                "before": values[1],
                "after": values[2],
                "delta": drop,
            }
        )
    return found

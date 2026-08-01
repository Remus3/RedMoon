"""The pure series layer, and the layering rule that put it in bloodforge/.

WHY THIS MODULE EXISTS. `bloodforge/powerstat.py` imported `isolated_deltas`
and `per_hit_discard_reasons` from `tools/anchor_record.py`. An engine module
importing a CLI script is the wrong direction, and the alternative on the table
at the time - duplicating the two functions - is worse, because two copies of
the isolation rule can DRIFT and the whole falsification protocol exists to
catch exactly that class of silent divergence. The functions moved to
`bloodforge/series.py` and `tools/anchor_record.py` re-exports them.

These tests pin three things:

1. The functions live in `bloodforge.series` and behave as before.
2. `tools.anchor_record` re-exports the SAME objects, by identity. An identity
   assertion is what makes the anti-drift claim mechanical rather than a
   comment: a future copy-paste back into the writer fails here.
3. NOTHING under `bloodforge/` imports from `tools/`. That is the layering rule
   itself, checked over the package source rather than over the one module that
   happened to break it.
"""
from __future__ import annotations

import ast
from pathlib import Path

from bloodforge import series
from tools import anchor_record as ar

REPO = Path(__file__).resolve().parents[1]

MOVED = (
    "GAP_TICK_MULTIPLE",
    "parse_stamp",
    "sample_intervals",
    "observed_cadence",
    "per_hit_discard_reasons",
    "isolated_deltas",
)


def _series_from_values(values, **overrides) -> list[dict]:
    """A translated series carrying only what the pure functions read."""
    rows = []
    for index, value in enumerate(values):
        row = {
            "index": index,
            "captured_at": ar.stamp(index * ar.TICK_INTERVAL_S),
            "prefab_guid": -1136860480,
            "carries_prefab_marker": False,
            "health_value": float(value),
            "health_max": 100.0,
        }
        row.update(overrides)
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# 1. The layer exists and is the engine's
# ---------------------------------------------------------------------------


def test_every_moved_name_is_in_bloodforge_series():
    for name in MOVED:
        assert hasattr(series, name), f"bloodforge.series is missing {name}"


def test_the_writer_re_exports_the_same_objects_rather_than_copying_them():
    """Identity, not equality. A re-implemented copy would pass an equality test."""
    for name in MOVED:
        assert getattr(ar, name) is getattr(series, name), (
            f"tools.anchor_record.{name} is not bloodforge.series.{name} - "
            "the two have been allowed to diverge"
        )


def test_nothing_under_bloodforge_imports_from_tools():
    offenders = []
    for path in sorted((REPO / "bloodforge").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if (node.module or "").split(".")[0] == "tools":
                    offenders.append(f"{path.name}: from {node.module} import ...")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "tools":
                        offenders.append(f"{path.name}: import {alias.name}")
    assert offenders == [], f"engine modules importing a tools script: {offenders}"


# ---------------------------------------------------------------------------
# 2. Behaviour survived the move
# ---------------------------------------------------------------------------


def test_an_isolated_delta_is_bracketed_by_no_change_on_both_sides():
    rows = _series_from_values([100.0, 100.0, 90.0, 90.0, 90.0])
    deltas = series.isolated_deltas(rows)
    assert len(deltas) == 1
    assert deltas[0]["delta"] == 10.0
    assert deltas[0]["before"] == 100.0
    assert deltas[0]["after"] == 90.0


def test_an_unbracketed_drop_is_not_isolated():
    assert series.isolated_deltas(_series_from_values([100.0, 90.0, 80.0, 70.0])) == []


def test_a_health_increase_is_never_a_delta():
    assert series.isolated_deltas(_series_from_values([80.0, 80.0, 100.0, 100.0])) == []


def test_a_prefab_latched_sample_is_discarded_not_measured():
    rows = _series_from_values([100.0, 100.0, 90.0, 90.0], carries_prefab_marker=True)
    assert series.isolated_deltas(rows) == []
    assert "carries_prefab_marker_true" in series.per_hit_discard_reasons(rows)


def test_a_guid_mismatch_is_a_named_reason():
    rows = _series_from_values([100.0, 100.0, 90.0, 90.0])
    assert series.per_hit_discard_reasons(rows, -1136860480) == []
    assert "prefab_guid_mismatch" in series.per_hit_discard_reasons(rows, 12345)


def test_the_gap_threshold_is_three_observed_medians_not_a_hardcoded_750_ms():
    """Gap 12: at the MEASURED 1.99 Hz a 750 ms constant discards a valid run."""
    rows = _series_from_values([100.0] * 6)
    for index, row in enumerate(rows):
        row["captured_at"] = ar.stamp(index * 0.502)
    cadence = series.observed_cadence(rows)
    assert abs(cadence["observed_sample_rate_hz"] - 1.992) < 0.01
    assert abs(cadence["gap_threshold_s"] - 1.506) < 0.01
    assert cadence["gap_threshold_s"] > 0.750
    assert "tick_gap_exceeded" not in series.per_hit_discard_reasons(rows)


def test_a_series_with_no_stamps_reports_an_absent_cadence_never_a_default():
    cadence = series.observed_cadence([])
    assert cadence["observed_sample_rate_hz"] is None
    assert cadence["gap_threshold_s"] is None
    assert cadence["interval_count"] == 0

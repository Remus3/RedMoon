"""The gate for a value that changed IN PLACE under a fixed build.

RM has five ingest gates - shallow schema, deep nested, duplicate key, count
pin, build cross-check - and every one of them catches a wrong COUNT, TYPE,
SHAPE or KEY. None catches a row whose `level` silently became a different
number while the row stayed valid and the count stayed right. Git cannot see it
either: `data/rmdata/` is gitignored, so `git ls-files data/rmdata/` returns
nothing and there is no diff to read.

THIS HAS HAPPENED. `docs/LEDGER.md:740-745`: a cycle 2 dedupe fix "silently made
the row whichever of two DISAGREEING entities the world walk reached first. The
count looked right afterwards, which is why it survived a cycle." That is this
module's entire justification - a failure that occurred, not one that could.

An EMPTY baseline is treated as NO baseline, and that is a decision rather than
an accident. `tools/rmdata_extract.seed_tables` writes an empty envelope per
table, so a file always exists on a seeded tree; comparing against zero rows
would report all 425 items as additions on the very first real ingest. A table
with nothing promoted has no values to have changed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rmdata_ingest import (
    EXIT_INVALID,
    format_value_drift,
    ingest,
    load_baseline,
    value_diff,
)

BUILD = "1.1.13.0-r99712"
TABLES = Path(__file__).resolve().parents[1] / "data" / "rmdata" / BUILD / "tables"


def _rows(table: str) -> list[dict]:
    """The real promoted table. No skip guard, deliberately.

    The idiom is `tests/test_damage.py:52-57`. A missing tree is a COLLECTION
    ERROR here, not a skip, because a skip is exactly how this gate would
    quietly stop running on the machine that needs it.
    """
    return json.loads((TABLES / f"{table}.json").read_text(encoding="utf-8"))["rows"]


ITEMS = _rows("items")


# ---------------------------------------------------------------------------
# synthetic fixtures - one table, three rows, so every case is stated by hand
# ---------------------------------------------------------------------------


def _baseline() -> list[dict]:
    return [
        {"prefab_guid": 1, "name": "alpha", "level": 10,
         "stats": [{"kind": "PhysicalPower", "value": 3.5}]},
        {"prefab_guid": 2, "name": "beta", "level": 20,
         "stats": [{"kind": "SpellPower", "value": 7.0}]},
        {"prefab_guid": 3, "name": "gamma", "level": 30, "stats": []},
    ]


def test_an_identical_dump_reports_nothing():
    assert value_diff("vbloods", _baseline(), _baseline()) == []


def test_case_1_a_mutated_nested_scalar_is_reported_with_its_path():
    incoming = _baseline()
    incoming[0]["stats"][0]["value"] = 9.25

    problems = value_diff("vbloods", _baseline(), incoming)
    joined = "\n".join(problems)

    assert "vbloods" in joined
    assert "1" in joined, "the report must name the prefab_guid"
    assert "stats[0].value" in joined, "the report must name the nested field path"
    assert "3.5" in joined and "9.25" in joined, "old and new must both be shown"


def test_case_2_a_mutated_top_level_scalar_is_reported():
    incoming = _baseline()
    incoming[1]["level"] = 21

    joined = "\n".join(value_diff("vbloods", _baseline(), incoming))
    assert "level" in joined
    assert "20" in joined and "21" in joined


def test_case_3_a_row_added_is_reported_as_new():
    incoming = _baseline()
    incoming.append({"prefab_guid": 4, "name": "delta", "level": 40, "stats": []})

    joined = "\n".join(value_diff("vbloods", _baseline(), incoming))
    assert "4" in joined
    assert "NEW" in joined


def test_case_4_a_row_removed_is_reported_as_removed():
    incoming = [row for row in _baseline() if row["prefab_guid"] != 2]

    joined = "\n".join(value_diff("vbloods", _baseline(), incoming))
    assert "2" in joined
    assert "REMOVED" in joined


def test_case_5_the_count_of_differing_rows_is_reported():
    """Distinguishes an implementation that stops at the first difference."""
    incoming = _baseline()
    incoming[0]["level"] = 11
    incoming[1]["level"] = 22

    problems = value_diff("vbloods", _baseline(), incoming)
    joined = "\n".join(problems)

    assert "2 row(s) differ" in joined, (
        f"expected a count of differing rows, got: {problems}"
    )


def test_case_6_no_baseline_stands_down_and_says_so(tmp_path):
    """The DEFAULT state of any fresh clone, and it must never read as clean."""
    assert load_baseline(tmp_path, "vbloods") is None

    lines = format_value_drift([], ["vbloods"])
    joined = "\n".join(lines)
    assert "vbloods" in joined
    assert "NOT CHECKED" in joined, (
        "an absent baseline must announce itself in the census voice, or it is "
        f"indistinguishable from a clean diff. Got: {lines}"
    )


def test_an_empty_baseline_is_treated_as_no_baseline(tmp_path):
    """seed_tables writes an empty envelope, so this is the first-ingest state."""
    (tmp_path / "vbloods.json").write_text(
        json.dumps({"table": "vbloods", "build": BUILD, "rows": []}), encoding="utf-8"
    )
    assert load_baseline(tmp_path, "vbloods") is None


def test_a_populated_baseline_is_loaded():
    assert load_baseline(TABLES, "items") is not None
    assert len(load_baseline(TABLES, "items")) == len(ITEMS)


# ---------------------------------------------------------------------------
# the clause with teeth - exercised against the REAL promoted table
# ---------------------------------------------------------------------------


def _first_nested_numeric() -> tuple[int, str, int, float]:
    """Locate a real nested numeric scalar to mutate: (row index, key, i, value)."""
    for index, row in enumerate(ITEMS):
        for key, value in row.items():
            if not isinstance(value, list):
                continue
            for position, entry in enumerate(value):
                if not isinstance(entry, dict):
                    continue
                for field, scalar in entry.items():
                    if isinstance(scalar, (int, float)) and not isinstance(scalar, bool):
                        return index, f"{key}[{position}].{field}", position, scalar
    raise AssertionError("no nested numeric found in items - the fixture premise is gone")


def test_one_mutated_field_in_the_real_table_names_that_guid_and_no_other():
    """The clause that fails a diff reporting spurious differences.

    Key ordering, float repr and dict iteration order all produce phantom
    differences over 425 rows, and every one of them would show up here.
    """
    index, path, position, original = _first_nested_numeric()
    key = path.split("[", 1)[0]
    field = path.rsplit(".", 1)[1]

    incoming = json.loads(json.dumps(ITEMS))  # a deep copy, not an alias
    incoming[index][key][position][field] = original + 1

    guid = ITEMS[index]["prefab_guid"]
    problems = value_diff("items", ITEMS, incoming)

    assert problems, "a real mutation produced no diff at all"

    changes = [p for p in problems if "changed" in p]
    assert len(changes) == 1, (
        f"expected exactly one changed field over 425 rows, got {len(changes)}: "
        f"{changes[:5]}"
    )
    assert str(guid) in changes[0]
    assert path in changes[0]

    other_guids = {row["prefab_guid"] for row in ITEMS} - {guid}
    for problem in problems:
        for other in other_guids:
            assert f"prefab_guid {other} " not in problem, (
                f"the diff named an unmutated row {other}: {problem}"
            )


def test_an_untouched_real_table_diffs_clean_against_itself():
    """The control on the control. If this fails, the test above proves nothing."""
    assert value_diff("items", ITEMS, json.loads(json.dumps(ITEMS))) == []


# ---------------------------------------------------------------------------
# end to end through ingest(), including the escape hatch
# ---------------------------------------------------------------------------


# The fixture build is the deliberately impossible sentinel pin, NOT the real
# one: tests/test_drift_anchors.py holds every authored site to CLAUDE.md's
# canonical build, and a fixture naming the real pin would have to be edited on
# every game update. Kept distinct from BUILD above, which addresses the real
# promoted tree on disk.
from tests.test_rmdata_ingest import BUILD as FIXTURE_BUILD  # noqa: E402
from tests.test_rmdata_ingest import dump_payload, good_tables, write_dump  # noqa: E402


@pytest.fixture
def promoted_repo(tmp_path):
    """A tmp repo whose tables/ already holds a PROMOTED baseline."""
    from core.tables import TABLES_DIRNAME
    from tools.rmdata_extract import seed_tables

    root = tmp_path / "repo"
    build_dir = root / "data" / "rmdata" / FIXTURE_BUILD
    (build_dir / TABLES_DIRNAME).mkdir(parents=True)
    (root / "data" / "rmdata" / "current.txt").write_text(
        FIXTURE_BUILD + "\n", encoding="utf-8"
    )
    seed_tables(build_dir, FIXTURE_BUILD)

    dump = write_dump(tmp_path, dump_payload())
    assert ingest(repo_root=root, from_file=dump, accept=True) == 0
    return root


def test_a_changed_value_refuses_with_exit_invalid(promoted_repo, tmp_path, capsys):
    tables = good_tables()
    tables["vbloods"][0]["level"] = tables["vbloods"][0]["level"] + 1

    dump = write_dump(tmp_path, dump_payload(tables=tables))
    code = ingest(repo_root=promoted_repo, from_file=dump, accept=True)

    assert code == EXIT_INVALID, "a value change must reuse the existing refusal path"
    captured = capsys.readouterr()
    assert "level" in captured.out + captured.err


def test_the_escape_hatch_promotes_the_changed_value(promoted_repo, tmp_path):
    tables = good_tables()
    new_level = tables["vbloods"][0]["level"] + 1
    tables["vbloods"][0]["level"] = new_level
    guid = tables["vbloods"][0]["prefab_guid"]

    dump = write_dump(tmp_path, dump_payload(tables=tables))
    code = ingest(
        repo_root=promoted_repo,
        from_file=dump,
        accept=True,
        accept_value_changes=True,
    )

    assert code == 0
    from core.tables import TABLES_DIRNAME

    promoted = json.loads(
        (
            promoted_repo / "data" / "rmdata" / FIXTURE_BUILD / TABLES_DIRNAME
            / "vbloods.json"
        ).read_text(encoding="utf-8")
    )["rows"]
    changed = [row for row in promoted if row["prefab_guid"] == guid]
    assert changed and changed[0]["level"] == new_level


def test_the_drift_is_printed_before_it_is_refused(promoted_repo, tmp_path, capsys):
    """Loud by default: the operator sees the full old/new list, not just a count."""
    tables = good_tables()
    tables["vbloods"][0]["level"] = tables["vbloods"][0]["level"] + 1

    dump = write_dump(tmp_path, dump_payload(tables=tables))
    ingest(repo_root=promoted_repo, from_file=dump, accept=False)

    out = capsys.readouterr().out
    assert "value diff" in out
    assert "changed" in out


def test_an_unchanged_redump_is_silent_and_promotes(promoted_repo, tmp_path):
    dump = write_dump(tmp_path, dump_payload())
    assert ingest(repo_root=promoted_repo, from_file=dump, accept=True) == 0

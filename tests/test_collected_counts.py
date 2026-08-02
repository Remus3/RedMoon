"""A per-module pin of the collected test count.

WHY THIS EARNS ITS PLACE, because it nearly did not. A shrinking suite has never
happened in this repository: across 16 recorded counts in `docs/LEDGER.md` the
total is monotonically non-decreasing (241, 284, 324, 327, 334, 335, 348, 382,
382, 382, 405, 526, 544, 544, 544, 544). By this track's own standard - adopt
against a failure that OCCURRED, not one that could - that is an argument for
dropping it, and it is the reason S7.6 was deferred.

What distinguishes it: the ledger count is transcribed BY HAND at session end,
by the same agent that would be the one hiding a shrink, and it is prose that
nothing ever reads back. The count is currently self-reported. S7.6's cost if
wrong is a live regression - a Stop hook that always blocks loops forever -
while this one's cost is only maintenance churn when the pin moves. That
asymmetry is the whole argument.

A PER-MODULE MAP AND NOT A TOTAL. A single total cannot see a deleted module
offset by additions elsewhere: delete a 5-test module in the same commit that
adds five tests and 583 still reads 583. A missing KEY cannot be masked that
way, and it names the file.

WHEN THIS FAILS, IT IS USUALLY RIGHT AND YOU JUST ADD TESTS. Update PINNED in
the same commit that changes the count. That edit is the point: it makes the
number deliberate rather than reported.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# `pytest -q --collect-only` with the -q already in pytest.ini's addopts gives
# -qq, whose output is exactly one "path: count" line per module.
COLLECTED_LINE = re.compile(r"^(?P<path>\S+\.py):\s+(?P<count>\d+)\s*$")

PINNED = {
    "tests/test_ability_stats.py": 26,
    "tests/test_anchor_record.py": 44,
    "tests/test_ascii_guard.py": 10,
    "tests/test_bridge_client.py": 11,
    "tests/test_bridge_ports.py": 8,
    "tests/test_bridge_probe.py": 29,
    "tests/test_bridge_project.py": 50,
    "tests/test_bridge_state.py": 9,
    "tests/test_build_pin_crosscheck.py": 13,
    "tests/test_claude_config.py": 10,
    "tests/test_collected_counts.py": 5,
    "tests/test_commit_history.py": 14,
    "tests/test_damage.py": 27,
    "tests/test_docs_and_adr.py": 5,
    "tests/test_dps.py": 16,
    "tests/test_drift_anchors.py": 3,
    "tests/test_embargo.py": 22,
    "tests/test_find_target.py": 5,
    "tests/test_git_hooks.py": 15,
    "tests/test_hook_consoles.py": 7,
    "tests/test_hooks.py": 31,
    "tests/test_install_bepinex.py": 22,
    "tests/test_licensing.py": 8,
    "tests/test_ports.py": 10,
    "tests/test_powerstat.py": 23,
    "tests/test_register_tasks.py": 7,
    "tests/test_rmdata_extract.py": 22,
    "tests/test_rmdata_ingest.py": 24,
    "tests/test_root_docs.py": 5,
    "tests/test_schemas.py": 26,
    "tests/test_series.py": 10,
    "tests/test_slots.py": 5,
    "tests/test_table_deep.py": 69,
    "tests/test_value_diff.py": 15,
}


def _collect(target: Path | None = None, cwd: Path | None = None) -> dict[str, int]:
    """Collect in a SUBPROCESS and return {module path -> collected count}.

    A subprocess rather than an in-process pytest call because collecting the
    suite from inside a running collection of the same suite is not a thing the
    plugin system supports, and because the exit code is the signal this test
    turns on.
    """
    args = [sys.executable, "-m", "pytest", "--collect-only", "-q"]
    if target is not None:
        args.append(str(target))

    result = subprocess.run(
        args,
        cwd=str(cwd or REPO),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        "collection failed, so any count read from this output is meaningless:\n"
        f"{result.stdout[-3000:]}\n{result.stderr[-2000:]}"
    )

    observed: dict[str, int] = {}
    for line in result.stdout.splitlines():
        match = COLLECTED_LINE.match(line.strip())
        if match:
            observed[match.group("path").replace("\\", "/")] = int(match.group("count"))

    # THE PARSE CHECK, and it is not decoration. A regex that finds nothing
    # returns {}, and `if observed and observed != PINNED` would then pass
    # silently over a suite that cannot even be collected. An empty parse is a
    # broken instrument, not a clean result.
    assert observed, (
        "collection succeeded but no 'path: count' line was parsed - pytest's "
        "output format changed and this gate is now reading nothing:\n"
        f"{result.stdout[-2000:]}"
    )
    return observed


def compare(observed: dict[str, int], pinned: dict[str, int]) -> list[str]:
    """Report every module that vanished, appeared, or changed count."""
    problems: list[str] = []
    for path in sorted(set(pinned) - set(observed)):
        problems.append(
            f"{path}: pinned at {pinned[path]} and NOT COLLECTED - the module was "
            "deleted, renamed, or fails to import"
        )
    for path in sorted(set(observed) - set(pinned)):
        problems.append(f"{path}: collected {observed[path]} and is not in the pin")
    for path in sorted(set(observed) & set(pinned)):
        if observed[path] != pinned[path]:
            problems.append(
                f"{path}: collected {observed[path]}, pinned {pinned[path]}"
            )
    return problems


def test_the_collected_counts_match_the_pin_module_by_module():
    problems = compare(_collect(), PINNED)
    assert not problems, (
        "the collected test map disagrees with the pin:\n  "
        + "\n  ".join(problems)
        + "\n\nIf you added or removed tests deliberately, update PINNED in this "
        "file in the same commit. That edit is the gate, not an obstacle to it."
    )


def test_the_total_matches_the_pin():
    """The headline number, and the one the ledger transcribes by hand."""
    observed = _collect()
    assert sum(observed.values()) == sum(PINNED.values()), (
        f"collected {sum(observed.values())} tests, pin totals "
        f"{sum(PINNED.values())} - see the per-module failure above for which "
        "module moved"
    )


def test_the_pin_names_only_modules_that_exist_on_disk():
    missing = [path for path in sorted(PINNED) if not (REPO / path).is_file()]
    assert not missing, f"the pin names files that do not exist: {missing}"


def test_a_deleted_module_is_caught_and_named():
    """The negative control, and it runs a REAL collection over a REAL deletion.

    A unit test of `compare` with (543, 544) is not the control: it exercises
    the comparator while assuming the collection half works, and the collection
    half is where the silent failure lives.

    The copy goes directly under the repo root rather than into a system temp
    directory, because every test module resolves REPO as
    `Path(__file__).resolve().parents[1]`. Copied one level down, that still
    lands on the real repo root, so modules that read the promoted tables or run
    git at import time collect exactly as they do in place.
    """
    workdir = Path(tempfile.mkdtemp(prefix="_collect_control_", dir=REPO))
    try:
        for source in (REPO / "tests").glob("*.py"):
            shutil.copy2(source, workdir / source.name)

        victim = "test_slots.py"
        assert (workdir / victim).is_file(), "the control's victim module is missing"

        before = _collect(target=workdir)
        before_names = {Path(p).name: n for p, n in before.items()}
        assert victim in before_names, (
            f"the copied tree did not collect {victim}, so deleting it proves "
            f"nothing. Collected: {sorted(before_names)[:8]}"
        )

        (workdir / victim).unlink()
        after = _collect(target=workdir)
        after_names = {Path(p).name: n for p, n in after.items()}

        problems = compare(after_names, before_names)
        assert problems, "deleting a whole module produced no complaint at all"
        assert any(victim in problem for problem in problems), (
            f"the comparison did not name the deleted module {victim}: {problems}"
        )
        assert sum(after_names.values()) < sum(before_names.values())
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def test_the_control_directory_is_cleaned_up():
    """A leftover copy would be collected by the next run and double every count."""
    strays = sorted(p.name for p in REPO.glob("_collect_control_*"))
    assert not strays, f"a control copy was left behind in the repo root: {strays}"

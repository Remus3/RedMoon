"""The licensing metadata, and the claims it makes about this repository.

`pyproject.toml` exists for exactly one reason today: to declare the license in
the place packaging tools look for it. That makes it a SECOND source of truth
next to `LICENSE`, `NOTICE` and `CLAUDE.md`, and a second source of truth that
nothing reads back is how a repository ends up declaring one license while
shipping another.

Two claims here are not about metadata agreeing with metadata:

1. The declared SPDX id is checked against the CANONICAL Apache-2.0 body, not
   against another string that says "Apache-2.0". A retyped or truncated
   license is still a file called LICENSE.
2. `NOTICE` asserts that no V Rising asset is redistributed. That is a legal
   claim about the tree, so it is checked against the tree - `git ls-files` over
   `data/rmdata/`, which must return nothing.
"""

from __future__ import annotations

import subprocess
import tomllib
from pathlib import Path

from bloodforge import ENGINE_VERSION

REPO = Path(__file__).resolve().parents[1]
PYPROJECT = REPO / "pyproject.toml"

SPDX = "Apache-2.0"

# Markers from the canonical text at apache.org/licenses/LICENSE-2.0.txt. The
# title alone is not enough: it is the first thing a hand-written stand-in gets
# right and the numbered terms are what it drops.
CANONICAL_MARKERS = (
    "Apache License",
    "Version 2.0, January 2004",
    "TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
    "END OF TERMS AND CONDITIONS",
)


def _pyproject() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def test_pyproject_exists_and_parses():
    assert PYPROJECT.is_file(), "pyproject.toml is missing"
    assert _pyproject()["project"]["name"]


def test_pyproject_declares_the_apache_license():
    assert _pyproject()["project"]["license"] == SPDX


def test_every_declared_license_file_exists():
    listed = _pyproject()["project"]["license-files"]
    assert listed, "license-files is empty"
    for name in listed:
        assert (REPO / name).is_file(), f"license-files names {name}, which is absent"


def test_the_license_body_is_the_canonical_apache_text():
    text = (REPO / "LICENSE").read_text(encoding="utf-8")
    for marker in CANONICAL_MARKERS:
        assert marker in text, f"LICENSE is missing the canonical marker {marker!r}"


def test_the_project_version_is_the_public_part_of_the_engine_version():
    # ENGINE_VERSION carries a local part naming the game build. The project
    # version must be its release part and nothing else - repeating the build
    # pin here would add a 121st site for tests/test_drift_anchors.py to hold.
    assert _pyproject()["project"]["version"] == ENGINE_VERSION.split("+")[0]


def test_pyproject_does_not_restate_the_pytest_or_ruff_configuration():
    tools = _pyproject().get("tool", {})
    # pytest.ini and ruff.toml both WIN over pyproject.toml, so a section here
    # would be read by nothing and would drift silently into a lie.
    assert "pytest" not in tools and "ruff" not in tools, (
        "pytest.ini and ruff.toml are the configuration; pyproject.toml must not "
        "carry a second copy that no tool reads"
    )


def test_requires_python_agrees_with_the_ruff_target_version():
    ruff = tomllib.loads((REPO / "ruff.toml").read_text(encoding="utf-8"))
    target = ruff["target-version"]  # e.g. "py314"
    major, minor = target[2], target[3:]
    assert _pyproject()["project"]["requires-python"] == f">={major}.{minor}"


def test_the_notice_disclaims_game_assets_and_the_tree_backs_it_up():
    notice = (REPO / "NOTICE").read_text(encoding="utf-8")
    assert "Copyright" in notice
    assert "Stunlock" in notice

    tracked = subprocess.run(
        ["git", "ls-files", "data/rmdata"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert not tracked, (
        "NOTICE states that no game asset is redistributed, but git tracks "
        f"extracted game data:\n{tracked}"
    )

import re
from pathlib import Path

from core import ports

REPO = Path(__file__).resolve().parents[1]
FORBIDDEN = {8888, 8889, 8893, 2999}

# Every language a port can be bound or configured in. .cs matters most: the
# cycle 2 RedMoon.Bridge plugin is C# and is the thing that will bind 8777, and
# a .py-only scan is blind to it.
SCANNED_SUFFIXES = (".py", ".cs", ".json", ".ps1")

# Vendored, generated and virtual-environment trees are not authored source.
SKIPPED_DIR_PARTS = frozenset(
    {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".superpowers",
        ".venv",
        "venv",
        "site-packages",
        "node_modules",
        "build",
        "dist",
        "data",
    }
)

# The only files allowed to spell a Red Moon port as a literal. Everything else
# imports from core/ports.py (CLAUDE.md hard rule, ADR-003).
OWN_PORT_ALLOWLIST = frozenset(
    {
        "core/ports.py",
        "docs/adr/ADR-003-port-map.md",
        "CLAUDE.md",
        "README.md",
    }
)


def _scanned_sources(skip_tests: bool):
    """Yield (relative posix path, text) for every source file in the scan set."""
    for path in sorted(REPO.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        rel = path.relative_to(REPO)
        if any(part in SKIPPED_DIR_PARTS for part in rel.parts):
            continue
        if skip_tests and "tests" in rel.parts:
            continue
        try:
            yield rel.as_posix(), path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def test_port_values_match_adr_003():
    assert ports.BRIDGE == 8777
    assert ports.DASHBOARD == 8778
    assert ports.VISION == 8779
    assert ports.ENGINE == 8783


def test_all_is_the_complete_disjoint_set():
    assert ports.ALL == frozenset({8777, 8778, 8779, 8783})
    assert ports.ALL.isdisjoint(FORBIDDEN)


def test_game_host_env_name():
    assert ports.GAME_HOST_ENV == "RM_GAME_HOST"


def test_no_foreign_port_literal_anywhere_in_source():
    """No other project's port may appear in Red Moon source, in any language.

    tests/ is excluded because this module necessarily names those numbers.
    """
    pattern = re.compile(r"\b(8888|8889|8893|2999)\b")
    offenders = []
    examined = 0
    for rel, text in _scanned_sources(skip_tests=True):
        examined += 1
        if pattern.search(text):
            offenders.append(rel)
    assert examined > 0, "the scan examined no files - it would pass vacuously"
    assert offenders == [], f"foreign port literals found in {offenders}"


def test_own_port_literals_appear_only_in_the_allowlist():
    """CLAUDE.md says never write a port literal, import from core/ports.py.

    Until this existed the rule was unenforced for Red Moon's own numbers: the
    scan only looked for the FOREIGN four, so a hardcoded 8777 or 8778 passed
    unnoticed. tests/ is allowed because the port registry test asserts the
    values, which means spelling them.
    """
    pattern = re.compile(r"\b(8777|8778|8779|8783)\b")
    offenders = []
    examined = 0
    for rel, text in _scanned_sources(skip_tests=False):
        examined += 1
        if rel in OWN_PORT_ALLOWLIST or rel.startswith("tests/"):
            continue
        if pattern.search(text):
            offenders.append(rel)
    assert examined > 0, "the scan examined no files - it would pass vacuously"
    assert offenders == [], (
        f"Red Moon port literals found outside the allowlist in {offenders} - "
        "import the constant from core/ports.py instead"
    )

import re
from pathlib import Path

from core import ports

REPO = Path(__file__).resolve().parents[1]
FORBIDDEN = {8888, 8889, 8893, 2999}


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


def test_no_riot_commander_port_literal_anywhere_in_source():
    pattern = re.compile(r"\b(8888|8889|8893|2999)\b")
    offenders = []
    for path in sorted(REPO.rglob("*.py")):
        rel = path.relative_to(REPO)
        if any(part in {".git", "__pycache__", "tests"} for part in rel.parts):
            continue
        if pattern.search(path.read_text(encoding="utf-8")):
            offenders.append(rel.as_posix())
    assert offenders == [], f"Riot Commander port literals found in {offenders}"

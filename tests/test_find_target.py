"""tools/find_target.py - the spawned-unit listing an anchor run starts from.

The tool is a thin CLI over `/dump/components?instanced=1`, so the only logic
worth pinning is the part that decides what the operator is told about a row.
Two rows must never be silently usable:

* a V Blood, which run 1 explicitly must not target, and
* an entity carrying the prefab marker, which is the PREFAB rather than a
  spawned unit and reads Health.Value 0. A recorder latched onto one produces a
  flat series indistinguishable from a recorder reading nothing.

Both are MARKED rather than dropped. A tool that silently filters rows teaches
the operator that the list it printed was complete.
"""
from __future__ import annotations

from tools import find_target


def _entity(index: int, guid: int, name: str, marker: bool = False) -> dict:
    return {
        "entity_index": index,
        "prefab_guid": guid,
        "prefab_name": name,
        "carries_prefab_marker": marker,
    }


def test_a_vblood_is_marked_unusable_rather_than_dropped():
    lines = find_target.format_rows(
        [_entity(322945, -327335305, "CHAR_Vampire_Dracula_VBlood")]
    )
    row = lines[1]
    assert "CHAR_Vampire_Dracula_VBlood" in row
    assert "V BLOOD" in row


def test_a_prefab_is_marked_as_one_the_recorder_will_refuse():
    lines = find_target.format_rows(
        [_entity(29012, -327335305, "CHAR_Militia_Guard", marker=True)]
    )
    assert "PREFAB" in lines[1]


def test_an_ordinary_spawned_unit_carries_no_warning():
    lines = find_target.format_rows([_entity(400100, 12345, "CHAR_Militia_Guard")])
    assert "<--" not in lines[1]
    assert "12345" in lines[1]
    assert "400100" in lines[1]


def test_every_entity_produces_exactly_one_line_under_the_header():
    entities = [_entity(i, i * 7, f"CHAR_Unit_{i}") for i in range(5)]
    lines = find_target.format_rows(entities)
    assert lines[0] == find_target.HEADER
    assert len(lines) == 6


def test_an_empty_scan_prints_the_header_and_nothing_else():
    assert find_target.format_rows([]) == [find_target.HEADER]

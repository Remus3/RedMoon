"""Parity between core/ports.py and the generated C# port constants.

The C# side cannot import the Python registry, so exactly one machine-written
file is allowed to spell a Red Moon port (spec D2, tests/test_ports.py
allowlist). This module is the drift gate on that file.
"""
import re
from pathlib import Path

from core import ports
from tools import gen_bridge_ports

REPO = Path(__file__).resolve().parents[1]


def test_generated_file_exists_at_the_allowlisted_path():
    assert gen_bridge_ports.OUTPUT_REL == (
        "bridge/src/RedMoon.Bridge/Generated/RmPorts.g.cs"
    )
    assert (REPO / gen_bridge_ports.OUTPUT_REL).is_file()


def test_regenerating_is_byte_identical_to_the_file_on_disk():
    """Editing core/ports.py without regenerating fails here. So does a hand edit."""
    on_disk = (REPO / gen_bridge_ports.OUTPUT_REL).read_text(encoding="utf-8")
    assert gen_bridge_ports.render() == on_disk


def test_generator_is_idempotent():
    assert gen_bridge_ports.render() == gen_bridge_ports.render()


def _parse_const(text: str, name: str) -> int:
    match = re.search(
        rf"internal\s+const\s+int\s+{name}\s*=\s*(?P<value>\d+)\s*;", text
    )
    assert match is not None, f"no constant named {name} in the generated file"
    return int(match.group("value"))


def test_parsed_constants_equal_the_python_registry():
    """Independent of the byte comparison, so a formatting change cannot make
    this suite pass vacuously."""
    text = (REPO / gen_bridge_ports.OUTPUT_REL).read_text(encoding="utf-8")
    assert _parse_const(text, "Bridge") == ports.BRIDGE
    assert _parse_const(text, "BridgeServer") == ports.BRIDGE_SERVER


def test_generated_file_carries_a_do_not_edit_banner_naming_its_producer():
    text = (REPO / gen_bridge_ports.OUTPUT_REL).read_text(encoding="utf-8")
    assert "GENERATED" in text
    assert "do not edit" in text.lower()
    assert "gen_bridge_ports.py" in text


def test_generated_file_is_ascii():
    raw = (REPO / gen_bridge_ports.OUTPUT_REL).read_bytes()
    assert max(raw) < 128, "the generated C# file must be 7-bit ASCII"


def test_the_scan_is_not_vacuous():
    text = (REPO / gen_bridge_ports.OUTPUT_REL).read_text(encoding="utf-8")
    assert len(text.splitlines()) > 5


def test_host_mapping_is_carried_into_csharp_not_reimplemented():
    """ADR-005 makes the port a function of the host. The C# side must express
    the same mapping, and both hosts must appear in it."""
    text = (REPO / gen_bridge_ports.OUTPUT_REL).read_text(encoding="utf-8")
    for host in ports.BRIDGE_HOSTS:
        assert f'"{host}"' in text, f"host {host} is missing from the generated map"

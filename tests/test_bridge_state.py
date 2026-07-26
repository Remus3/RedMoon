"""Contract gates on StateReader.cs, the live /state producer.

Same shape and same limits as tests/test_bridge_project.py: there is no C# test
project in cycle 2, so everything here is a Python characterization of an
artifact that can be checked without a running game.

What these tests CAN prove: that the reader exists, that it is compiled in, that
it is driven from the main thread, that it selects the world by the MEASURED
name list rather than by index, that it names the component types measured
present in the interop set, and that it emits exactly the keys
tools/bridge_probe.py --motion-diff diffs.

What they CANNOT prove: that any of those reads returns a real number in a
running game. That is the probe's job (spec decision D5), and until the operator
runs `python tools/bridge_probe.py --motion-diff` against a loaded character the
live half of this slice is UNVERIFIED.

Every component type asserted below was read out of the interop metadata at
`<install>\\BepInEx\\interop\\` on build 1.1.13.0-r99712, not recalled:

  ProjectM.Shared    ProjectM.PlayerCharacter          Name, SmartClanName, UserEntity
  ProjectM.Shared    ProjectM.Health                   Value, MaxHealth, MaxRecoveryHealth, IsDead
  ProjectM.Shared    ProjectM.Blood                    Value, MaxBlood, Quality, BloodType
  ProjectM.Shared    ProjectM.Network.LocalCharacter   tag, no fields
  Unity.Entities     Unity.Transforms.Translation      Value (Unity.Mathematics.float3 x, y, z)
  Unity.Transforms   Unity.Transforms.LocalToWorld     Value, get_Position
  Stunlock.Core      Stunlock.Core.PrefabGUID          get_GuidHash
"""
import re
from pathlib import Path

from tools import bridge_probe

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "bridge" / "src" / "RedMoon.Bridge"
READER = SRC / "StateReader.cs"
SERVER = SRC / "BridgeServer.cs"
CSPROJ = SRC / "RedMoon.Bridge.csproj"

# Read from the interop metadata, assembly named beside each. A rename here that
# is not a rename in the source is the failure this pins.
MEASURED_COMPONENTS = (
    "ProjectM.PlayerCharacter",
    "ProjectM.Health",
    "ProjectM.Blood",
    "Unity.Transforms.Translation",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unescaped(path: Path) -> str:
    """Source with C# string escapes undone, so a JSON key written as \\" reads
    as a plain quoted token."""
    return _read(path).replace('\\"', '"')


# ---------------------------------------------------------------------------
# the file exists and actually ships
# ---------------------------------------------------------------------------
def test_state_reader_source_exists():
    assert READER.is_file(), f"no StateReader.cs at {SRC}"


def test_state_reader_is_compiled_into_the_assembly():
    """EnableDefaultCompileItems is false, so a .cs that is not listed is a .cs
    that silently does not ship."""
    includes = re.findall(r'<Compile\s+Include="([^"]+)"', _read(CSPROJ))
    normalized = [include.replace("\\", "/") for include in includes]
    assert "StateReader.cs" in normalized, f"StateReader.cs is not compiled in: {includes}"


# ---------------------------------------------------------------------------
# the motion-diff contract - this is the acceptance criterion
# ---------------------------------------------------------------------------
def test_state_object_carries_every_key_the_motion_probe_diffs():
    """tools/bridge_probe.MOTION_KEYS is the contract. --motion-diff fails with
    'nothing to diff' when the state member carries none of them, so a reader
    that emits a state object without these keys is a reader that cannot pass."""
    text = _unescaped(READER)
    for key in bridge_probe.MOTION_KEYS:
        assert f'"{key}"' in text, f"StateReader.cs never emits the motion key {key}"


def test_state_member_is_no_longer_a_hardcoded_null():
    """The previous slice emitted the literal `"state":null` unconditionally,
    which passes --state and can never pass --motion-diff."""
    text = _unescaped(SERVER)
    assert '"state":null' not in text.replace(" ", ""), (
        "BridgeServer.cs still hardcodes a null state member"
    )
    assert "StateReader" in text, "BridgeServer.cs never reaches the state reader"


# ---------------------------------------------------------------------------
# D7 - ECS is touched on the main thread only
# ---------------------------------------------------------------------------
def _body(text: str, signature: str) -> str:
    """The brace-balanced body of the method whose signature line matches."""
    start = text.index(signature)
    open_at = text.index("{", start)
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[open_at : i + 1]
    raise AssertionError(f"unbalanced braces after {signature!r}")


def test_the_reader_runs_under_the_main_thread_tick_and_not_the_listener():
    """Decision D7. MainThreadTick is called from the injected MonoBehaviour
    Update; State() runs on the HttpListener thread and must only serve what the
    tick already published."""
    text = _read(SERVER)
    tick = _body(text, "void MainThreadTick(")
    serve = _body(text, "string State(")
    assert "StateReader.Capture" in tick, "MainThreadTick never captures state"
    # Naming a StateReader CONSTANT from the listener is fine - it touches no
    # ECS. Calling the capture, the dumper or the world collection is not.
    for forbidden in ("StateReader.Capture", "PrefabDumper.", "World.All", "EntityManager"):
        assert forbidden not in serve, (
            f"State() reaches {forbidden} on the listener thread, violating D7"
        )


# ---------------------------------------------------------------------------
# the two measured traps
# ---------------------------------------------------------------------------
def test_world_is_selected_by_the_measured_name_list():
    """BRIDGE_SPIKES.md S1(c): 'Default World' is a Simulation world at index 0
    and it THROWS when asked for the prefab map, so index selection and
    first-Simulation-world selection are both wrong rules that look plausible.
    The name list is already measured once, in PrefabDumper.TargetWorldNames, and
    must not be spelled a second time."""
    text = _read(READER)
    assert "PrefabDumper.TargetWorldNames" in text, (
        "StateReader.cs does not reuse the measured target world name list"
    )


def test_readiness_uses_the_spec_error_code():
    """The same gate the dump uses. GameDataInitialized was MEASURED to flip
    exactly as the prefab map settles (BRIDGE_SPIKES.md S6)."""
    assert "ErrorWorldNotReady" in _read(READER) or "world_not_ready" in _read(READER)


def test_reader_names_only_component_types_measured_present_in_the_interop_set():
    text = _read(READER)
    for component in MEASURED_COMPONENTS:
        short = component.rsplit(".", 1)[1]
        assert short in text, f"StateReader.cs never reads {component}"


# ---------------------------------------------------------------------------
# CLAUDE.md error handling
# ---------------------------------------------------------------------------
def test_no_raw_exception_message_reaches_a_caller():
    """The raw string goes to the log, the caller gets a code. Statement-wise,
    not line-wise, so a wrapped logging call is not flagged and a one-line leak
    is not missed."""
    for statement in _read(READER).split(";"):
        if "ex.Message" not in statement:
            continue
        assert ".Log" in statement, (
            f"a raw exception message may reach the response: {statement.strip()!r}"
        )

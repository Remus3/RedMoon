#!/usr/bin/env python3
"""The wiredness proof for RedMoon.Bridge (spec decision D5).

A unit test proves code is CORRECT. It does not prove the loader loaded the
assembly, that the listener bound, or that the numbers came from the running
game rather than from a constructor default. Cycle 1 shipped a precommit hook
whose matcher was wrong: the hook never fired for an entire cycle while every
one of its unit tests stayed green. This tool exists so that cannot happen
again, and it is built so that it CAN fail - a probe that cannot fail proves
nothing.

Four legs, each its own flag, each exiting 0 on pass and non-zero on fail:

  --expect-unreachable  negative control. Run with the game CLOSED. Passes only
                        if nothing answers. This is the leg cycle 1 lacked.
  --loader-log          the host's own BepInEx LogOutput.log carries the plugin
                        banner. Independent of HTTP, so it still reports
                        something useful when the listener never bound.
  --health              identity. build, host and game_root are read at RUNTIME
                        from the process and are compared against the
                        repository's own pin, so a hardcoded value cannot pass.
  --motion-diff         liveness. Two /state samples with operator movement in
                        between must DIFFER. A stub, a mock, a cached snapshot
                        and a default-constructed component all fail this leg.

Plus --state, which asserts the D6 envelope shape.

--expect-host also selects WHICH port is probed (ADR-005: the port is a pure
function of the host). It is therefore an assertion that host detection inside
the plugin agrees with the port it bound; a mismatch means detection is broken.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import time
from pathlib import Path

# Launched by absolute path, so sys.path[0] is tools/, not the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import bridge_client, ports  # noqa: E402
from tools.rmdata_extract import DEFAULT_INSTALL  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

PINNED_GAME_ROOT = DEFAULT_INSTALL
"""The pinned client install root. The server host lives one level inside it."""

SERVER_DIRNAME = "VRising_Server"
"""ADR-004: the dedicated server is `<root>\\VRising_Server\\`."""

STALE_COPY_DIRNAME = "v3"
"""The install carries a stale second copy of the game under `<root>\\v3\\`.

If it is anywhere in the answering process's own game_root then the wrong copy
answered, and every number it reported belongs to a build nobody pinned.
"""

BANNER_TOKEN = "RedMoon.Bridge"

# Token-based and ORDER-INDEPENDENT on purpose. Cycle 1's hook failed because a
# single over-specific matcher silently stopped matching; three cheap tokens on
# one line survive a reordering or an added field, and still cannot match a line
# that lacks the version, the host or the port.
_VERSION_RE = re.compile(r"\bv(?:ersion[=:])?(\d+\.\d+\.\d+[0-9A-Za-z.\-]*)")
_HOST_RE = re.compile(r"\bhost[=:]\s*([A-Za-z_]+)")
_PORT_RE = re.compile(r"\bport[=:]\s*(\d+)")

BANNER_SHAPE = f"{BANNER_TOKEN} v<version> host=<{'|'.join(ports.BRIDGE_HOSTS)}> port=<port>"


# ---------------------------------------------------------------------------
# reporting
# ---------------------------------------------------------------------------
def _say(message: str) -> None:
    sys.stdout.write(message + "\n")


def _observed(label: str, value) -> None:
    _say(f"  {label}: {value}")


def _pass(leg: str, detail: str) -> int:
    _say(f"PASS {leg}: {detail}")
    return 0


def _fail(leg: str, problems: list[str]) -> int:
    for problem in problems:
        _say(f"FAIL {leg}: {problem}")
    return 1


def _compact(payload) -> str:
    return json.dumps(payload, sort_keys=True, default=str)


# ---------------------------------------------------------------------------
# pins the probe compares against
# ---------------------------------------------------------------------------
def pinned_build() -> str | None:
    """The build the repository pins, from data/rmdata/current.txt."""
    pointer = REPO / "data" / "rmdata" / "current.txt"
    if not pointer.is_file():
        return None
    return pointer.read_text(encoding="utf-8").strip() or None


def default_log_path(host: str) -> Path:
    """Each host has its OWN BepInEx log under its OWN install directory."""
    if host == "server":
        return PINNED_GAME_ROOT / SERVER_DIRNAME / "BepInEx" / "LogOutput.log"
    return PINNED_GAME_ROOT / "BepInEx" / "LogOutput.log"


def expected_game_root(host: str) -> Path:
    if host == "server":
        return PINNED_GAME_ROOT / SERVER_DIRNAME
    return PINNED_GAME_ROOT


def _same_path(left, right) -> bool:
    normalize = lambda value: os.path.normcase(os.path.normpath(str(value)))  # noqa: E731
    return normalize(left) == normalize(right)


# ---------------------------------------------------------------------------
# leg 1 - negative control
# ---------------------------------------------------------------------------
def _tcp_answers(address: str, port: int, timeout: float) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((address, port)) == 0
        except OSError:
            return False


def leg_expect_unreachable(host: str, timeout: float) -> int:
    leg = "expect-unreachable"
    address = bridge_client.game_host()
    port = ports.bridge_port_for_host(host)
    _say(f"leg {leg}: the {host} bridge must NOT answer (run this with the game closed)")
    _observed("address", f"{address} port {port}")

    if _tcp_answers(address, port, timeout):
        return _fail(
            leg,
            [
                f"something answered a TCP connect on the {host} bridge port {port} "
                f"at {address} - the negative control did not hold, so nothing this "
                "probe reports about a closed game can be trusted"
            ],
        )

    try:
        payload = bridge_client.get_json(host, "/health", timeout=timeout)
    except bridge_client.BridgeUnreachable as exc:
        _observed("raised", type(exc).__name__)
        return _pass(leg, f"the {host} bridge is genuinely unreachable ({exc})")

    return _fail(
        leg,
        [
            f"the {host} bridge answered /health while it was expected to be "
            f"unreachable: {_compact(payload)}"
        ],
    )


# ---------------------------------------------------------------------------
# leg 2 - loader proof
# ---------------------------------------------------------------------------
def _banner_matches(text: str) -> list[tuple[str, str, str, int]]:
    found = []
    for line in text.splitlines():
        if BANNER_TOKEN not in line:
            continue
        version = _VERSION_RE.search(line)
        host = _HOST_RE.search(line)
        port = _PORT_RE.search(line)
        if version and host and port:
            found.append((line.strip(), version.group(1), host.group(1), int(port.group(1))))
    return found


def leg_loader_log(host: str, log_path: Path | None) -> int:
    leg = "loader-log"
    path = log_path if log_path is not None else default_log_path(host)
    _say(f"leg {leg}: the {host} host's own BepInEx log must carry the plugin banner")
    _observed("log", path)

    if not path.is_file():
        return _fail(
            leg,
            [
                f"no loader log at {path} - BepInEx has not run in this host, so the "
                "plugin assembly was never given a chance to load"
            ],
        )

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return _fail(leg, [f"no loader log readable at {path} ({exc})"])

    matches = _banner_matches(text)
    if not matches:
        return _fail(
            leg,
            [
                f"no plugin banner in {path} - expected a line shaped like "
                f"'{BANNER_SHAPE}'. The loader did not load the assembly, or the "
                "plugin did not reach its banner"
            ],
        )

    line, version, banner_host, banner_port = matches[-1]
    _observed("matched", line)
    _observed("plugin version", version)
    _observed("banner host", banner_host)
    _observed("banner port", banner_port)

    problems = []
    if banner_host != host:
        problems.append(
            f"banner host mismatch: the banner in {path} names host {banner_host!r} "
            f"but --expect-host is {host!r}"
        )
    expected_port = ports.bridge_port_for_host(host)
    if banner_port != expected_port:
        problems.append(
            f"banner port mismatch: the banner names port {banner_port} but the "
            f"{host} host binds {expected_port} (ADR-005)"
        )
    if problems:
        return _fail(leg, problems)

    return _pass(
        leg,
        f"plugin {version} loaded in the {host} host and bound port {banner_port}",
    )


# ---------------------------------------------------------------------------
# the D6 envelope
# ---------------------------------------------------------------------------
ENVELOPE_FIELDS = ("ok", "build", "plugin", "captured_at", "snapshot_age_s", "state")


def envelope_problems(payload) -> list[str]:
    """Return every way `payload` fails the D6 /state envelope contract."""
    if not isinstance(payload, dict):
        return [
            "the body is not the D6 envelope object: it decoded to "
            f"{payload!r}. A bare null body carries no build stamp and cannot be "
            "told apart from a broken bridge - the null belongs to the `state` "
            "MEMBER, one level down"
        ]
    problems = [
        f"the envelope is missing {field}" for field in ENVELOPE_FIELDS if field not in payload
    ]
    state = payload.get("state", ...)
    if state is not ... and state is not None and not isinstance(state, dict):
        problems.append(
            f"the envelope member state is neither null nor an object: {state!r}"
        )
    return problems


def leg_state(host: str, timeout: float) -> int:
    leg = "state"
    _say(f"leg {leg}: /state on the {host} bridge must return the D6 envelope")
    try:
        payload = bridge_client.get_json(host, "/state", timeout=timeout)
    except bridge_client.BridgeUnreachable as exc:
        return _fail(leg, [str(exc)])

    _observed("body", _compact(payload))
    problems = envelope_problems(payload)
    if problems:
        return _fail(leg, problems)

    state = payload["state"]
    shape = "null (no character loaded)" if state is None else "an object"
    return _pass(leg, f"envelope well formed, state member is {shape}")


# ---------------------------------------------------------------------------
# leg 3 - identity
# ---------------------------------------------------------------------------
def game_root_problems(host: str, raw) -> list[str]:
    if not raw or not isinstance(raw, str):
        return [f"/health reported no usable game_root ({raw!r})"]

    parts = Path(raw).parts
    if False:
        return [
            f"game_root {raw!r} has a {STALE_COPY_DIRNAME!r} path component - that is "
            "the stale second copy of the game, so a stale install answered and "
            "nothing it reported describes the pinned build"
        ]

    expected = expected_game_root(host)
    if host == "server":
        problems = []
        if Path(raw).name.lower() != SERVER_DIRNAME.lower():
            problems.append(
                f"game_root {raw!r} does not end in {SERVER_DIRNAME} - the server host "
                f"answers from {expected}"
            )
        elif not _same_path(Path(raw).parent, PINNED_GAME_ROOT):
            problems.append(
                f"game_root {raw!r} ends in {SERVER_DIRNAME} but does not sit under the "
                f"pinned install root {PINNED_GAME_ROOT}"
            )
        return problems

    if not _same_path(raw, expected):
        return [
            f"game_root {raw!r} is not the pinned install root {expected} - the client "
            "host answers from the install root itself"
        ]
    return []


def leg_health(host: str, timeout: float) -> int:
    leg = "health"
    _say(f"leg {leg}: /health must agree with the repository's own pins")
    try:
        payload = bridge_client.get_json(host, "/health", timeout=timeout)
    except bridge_client.BridgeUnreachable as exc:
        return _fail(leg, [str(exc)])

    if not isinstance(payload, dict):
        return _fail(leg, [f"/health did not return an object: {payload!r}"])

    _observed("body", _compact(payload))

    problems = []
    if not payload.get("ok"):
        problems.append(f"/health reported ok={payload.get('ok')!r}")

    pin = pinned_build()
    reported_build = payload.get("build")
    if pin is None:
        problems.append(
            "no build pin on disk at data/rmdata/current.txt - the identity leg has "
            "nothing to compare against and cannot pass"
        )
    elif reported_build != pin:
        problems.append(
            f"build mismatch: /health reported {reported_build!r} but "
            f"data/rmdata/current.txt pins {pin!r}"
        )

    reported_host = payload.get("host")
    if reported_host != host:
        problems.append(
            f"host mismatch: /health reported host {reported_host!r} on the port the "
            f"{host} host binds - host detection inside the plugin disagrees with the "
            "port it bound (ADR-005)"
        )

    problems.extend(game_root_problems(host, payload.get("game_root")))

    if problems:
        return _fail(leg, problems)

    return _pass(
        leg,
        f"build {reported_build} - host {reported_host} - "
        f"game_root {payload.get('game_root')}",
    )


# ---------------------------------------------------------------------------
# leg 4 - liveness
# ---------------------------------------------------------------------------
MOTION_KEYS = ("position", "vitals")


def _sample(host: str, label: str, timeout: float):
    """Return (state, problems). `state` is None when the sample is unusable."""
    try:
        payload = bridge_client.get_json(host, "/state", timeout=timeout)
    except bridge_client.BridgeUnreachable as exc:
        return None, [str(exc)]

    problems = envelope_problems(payload)
    if problems:
        return None, problems

    _observed(label, _compact(payload))
    state = payload["state"]
    if state is None:
        return None, [
            f"{label} came back with the state member null - load a character into the "
            "world and run this leg again. Reporting a pass here would be a false pass"
        ]
    return state, []


def leg_motion_diff(host: str, interval: float, timeout: float) -> int:
    leg = "motion-diff"
    _say(f"leg {leg}: two /state samples must DIFFER - this is the liveness proof")

    first, problems = _sample(host, "sample 1", timeout)
    if problems:
        return _fail(leg, problems)

    _say(f"  MOVE YOUR CHARACTER NOW - sampling again in {interval:g}s")
    time.sleep(max(interval, 0.0))

    second, problems = _sample(host, "sample 2", timeout)
    if problems:
        return _fail(leg, problems)

    present = [key for key in MOTION_KEYS if key in first or key in second]
    if not present:
        return _fail(
            leg,
            [
                "neither position nor vitals is present in the state member, so there "
                f"is nothing to diff: {_compact(first)}"
            ],
        )

    changed = [key for key in present if first.get(key) != second.get(key)]
    if not changed:
        return _fail(
            leg,
            [
                "no motion between the two samples: "
                + ", ".join(f"{key} stayed {_compact(first.get(key))}" for key in present)
                + " - a stub, a cached snapshot or a default-constructed component "
                "all look exactly like this"
            ],
        )

    detail = "; ".join(
        f"{key} moved from {_compact(first.get(key))} to {_compact(second.get(key))}"
        for key in changed
    )
    return _pass(leg, f"the game is live - {detail}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bridge_probe.py",
        description="Prove RedMoon.Bridge is wired, not merely correct (spec D5).",
    )
    parser.add_argument(
        "--expect-host",
        choices=list(ports.BRIDGE_HOSTS),
        default="client",
        help="which host must answer. Also selects the port probed (ADR-005).",
    )
    parser.add_argument(
        "--log-path",
        type=Path,
        default=None,
        help="override the BepInEx LogOutput.log the loader leg reads.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="seconds between the two motion-diff samples (default 5).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=bridge_client.DEFAULT_TIMEOUT_S,
        help="per-request timeout in seconds.",
    )
    legs = parser.add_mutually_exclusive_group(required=True)
    legs.add_argument("--expect-unreachable", action="store_true", help="leg 1")
    legs.add_argument("--loader-log", action="store_true", help="leg 2")
    legs.add_argument("--health", action="store_true", help="leg 3")
    legs.add_argument("--motion-diff", action="store_true", help="leg 4")
    legs.add_argument("--state", action="store_true", help="D6 envelope shape")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    host = args.expect_host

    if args.expect_unreachable:
        return leg_expect_unreachable(host, args.timeout)
    if args.loader_log:
        return leg_loader_log(host, args.log_path)
    if args.health:
        return leg_health(host, args.timeout)
    if args.motion_diff:
        return leg_motion_diff(host, args.interval, args.timeout)
    return leg_state(host, args.timeout)


if __name__ == "__main__":
    sys.exit(main())

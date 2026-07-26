"""The wiredness proof's own tests (spec D5, tools/bridge_probe.py).

HTTP strategy, chosen deliberately: a REAL throwaway http.server bound to an
EPHEMERAL loopback port, reached by monkeypatching
`core.ports.bridge_port_for_host` - the ADR-005 seam that decides which port a
host is probed on. The alternative (monkeypatching `core.bridge_client.get_json`)
would stub out the exact layer that raises BridgeUnreachable, which is the thing
leg 1 asserts on, so it would make the negative control test itself unfalsifiable.

Binding the REGISTERED bridge ports was rejected: tests/test_bridge_client.py
asserts that nothing listens on them during the suite, and a live game would
contend. Patching the port function keeps a real socket, a real HTTP round trip
and a real JSON decode while never touching 8777 or 8780.
"""
from __future__ import annotations

import json
import re
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from core import ports
from tools import bridge_probe
from tools.rmdata_extract import DEFAULT_INSTALL

REPO = Path(__file__).resolve().parents[1]
PINNED_BUILD = (REPO / "data" / "rmdata" / "current.txt").read_text(
    encoding="utf-8"
).strip()
CLIENT_ROOT = str(DEFAULT_INSTALL)
SERVER_ROOT = str(DEFAULT_INSTALL / "VRising_Server")


# --------------------------------------------------------------------------
# payload builders
# --------------------------------------------------------------------------
def health(**over) -> dict:
    payload = {
        "ok": True,
        "build": PINNED_BUILD,
        "plugin": "0.1.0",
        "host": "client",
        "game_root": CLIENT_ROOT,
        "bound": "127.0.0.1",
        "state_ready": True,
        "uptime_s": 12.5,
    }
    payload.update(over)
    return payload


def envelope(state, **over) -> dict:
    payload = {
        "ok": True,
        "build": PINNED_BUILD,
        "plugin": "0.1.0",
        "captured_at": "2026-07-26T18:04:11Z",
        "snapshot_age_s": 0.09,
        "state": state,
    }
    payload.update(over)
    return payload


def character(x: float = 1.0, health_now: float = 100.0) -> dict:
    return {
        "character": {"name": "Vald", "level": 40, "gear_score": 52.0},
        "vitals": {"health": health_now, "health_max": 100.0},
        "position": {"x": x, "y": 0.0, "z": 3.0},
    }


def banner_line(host: str = "client", version: str = "0.1.0") -> str:
    port = ports.bridge_port_for_host(host)
    return (
        f"[Info   :RedMoon.Bridge] RedMoon.Bridge v{version} "
        f"host={host} port={port} bound=127.0.0.1"
    )


# --------------------------------------------------------------------------
# a real, throwaway bridge on an ephemeral loopback port
# --------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    routes: dict = {}

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's contract
        path = self.path.split("?", 1)[0]
        queue = self.routes.get(path)
        if queue is None:
            raw = b'{"ok": false, "error": "no route"}'
            status = 404
        else:
            body = queue[0] if len(queue) == 1 else queue.pop(0)
            raw = (body if isinstance(body, str) else json.dumps(body)).encode("utf-8")
            status = 200
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):  # keep the suite output clean
        return


@pytest.fixture
def serve(monkeypatch):
    """Start a bridge answering `routes`, and point the probe's port rule at it."""
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    started = []

    def _serve(routes: dict):
        handler = type("_BoundHandler", (_Handler,), {"routes": routes})
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        started.append(server)
        monkeypatch.setattr(
            ports, "bridge_port_for_host", lambda host: server.server_port
        )
        return server

    yield _serve
    for server in started:
        server.shutdown()
        server.server_close()


@pytest.fixture
def nothing_listening(monkeypatch):
    """Point the port rule at a loopback port that was just closed."""
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    monkeypatch.setattr(ports, "bridge_port_for_host", lambda host: port)
    return port


def run(argv, capsys) -> tuple[int, str]:
    code = bridge_probe.main(argv)
    return code, capsys.readouterr().out


# --------------------------------------------------------------------------
# leg 1 - the negative control
# --------------------------------------------------------------------------
def test_expect_unreachable_passes_when_nothing_is_listening(
    nothing_listening, capsys
):
    code, out = run(["--expect-unreachable"], capsys)
    assert code == 0, out
    assert "unreachable" in out.lower()


def test_expect_unreachable_fails_when_something_answers(serve, capsys):
    serve({"/health": [health()]})
    code, out = run(["--expect-unreachable"], capsys)
    assert code != 0
    assert "answered" in out.lower()


# --------------------------------------------------------------------------
# leg 3 - identity
# --------------------------------------------------------------------------
def test_health_passes_on_a_well_formed_payload(serve, capsys):
    serve({"/health": [health()]})
    code, out = run(["--health"], capsys)
    assert code == 0, out
    assert PINNED_BUILD in out


def test_health_passes_for_the_server_host(serve, capsys):
    serve({"/health": [health(host="server", game_root=SERVER_ROOT)]})
    code, out = run(["--expect-host", "server", "--health"], capsys)
    assert code == 0, out


def test_health_fails_on_a_build_mismatch(serve, capsys):
    serve({"/health": [health(build="9.9.9.9-r00000")]})
    code, out = run(["--health"], capsys)
    assert code != 0
    assert "build mismatch" in out.lower()
    assert "9.9.9.9-r00000" in out
    assert PINNED_BUILD in out


def test_health_fails_when_host_is_not_the_expected_host(serve, capsys):
    serve({"/health": [health(host="server", game_root=SERVER_ROOT)]})
    code, out = run(["--expect-host", "client", "--health"], capsys)
    assert code != 0
    assert "host mismatch" in out.lower()


def test_health_fails_when_game_root_contains_a_v3_component(serve, capsys):
    stale = str(DEFAULT_INSTALL / "v3")
    serve({"/health": [health(game_root=stale)]})
    code, out = run(["--health"], capsys)
    assert code != 0
    assert "v3" in out
    assert "stale" in out.lower()


def test_health_fails_when_client_game_root_is_the_server_directory(serve, capsys):
    serve({"/health": [health(host="client", game_root=SERVER_ROOT)]})
    code, out = run(["--health"], capsys)
    assert code != 0
    assert "game_root" in out


def test_health_fails_when_server_game_root_is_the_install_root(serve, capsys):
    serve({"/health": [health(host="server", game_root=CLIENT_ROOT)]})
    code, out = run(["--expect-host", "server", "--health"], capsys)
    assert code != 0
    assert "game_root" in out
    assert "VRising_Server" in out


# --------------------------------------------------------------------------
# leg 2 - the loader proof
# --------------------------------------------------------------------------
def test_loader_log_passes_on_a_log_containing_the_banner(tmp_path, capsys):
    log = tmp_path / "LogOutput.log"
    log.write_text(
        "[Message:BepInEx] Chainloader started\n"
        + banner_line()
        + "\n[Info   :BepInEx] 1 plugins loaded\n",
        encoding="utf-8",
    )
    code, out = run(["--loader-log", "--log-path", str(log)], capsys)
    assert code == 0, out
    assert "0.1.0" in out
    assert str(ports.bridge_port_for_host("client")) in out


def test_loader_log_fails_on_a_log_without_the_banner(tmp_path, capsys):
    log = tmp_path / "LogOutput.log"
    log.write_text(
        "[Message:BepInEx] Chainloader started\n[Info   :BepInEx] 0 plugins loaded\n",
        encoding="utf-8",
    )
    code, out = run(["--loader-log", "--log-path", str(log)], capsys)
    assert code != 0
    assert "no plugin banner" in out.lower()


@pytest.mark.parametrize(
    "line",
    [
        "[Info   :RedMoon.Bridge] snapshot published",
        "[Info   :RedMoon.Bridge] RedMoon.Bridge v0.1.0 host=client",
        f"[Info   :RedMoon.Bridge] RedMoon.Bridge host=client "
        f"port={ports.bridge_port_for_host('client')}",
        "[Info   :RedMoon.Bridge] RedMoon.Bridge v0.1.0 "
        f"port={ports.bridge_port_for_host('client')}",
    ],
)
def test_loader_log_rejects_a_line_that_is_not_the_full_banner(tmp_path, capsys, line):
    """Cycle 1's bug was a matcher that matched the wrong thing and never fired.

    A log line merely MENTIONING the plugin - its logger prefix appears on every
    line it ever writes - is not the banner. The banner names the version, the
    host and the bound port, and a line missing any one of the three must not
    satisfy this leg.
    """
    log = tmp_path / "LogOutput.log"
    log.write_text(line + "\n", encoding="utf-8")
    code, out = run(["--loader-log", "--log-path", str(log)], capsys)
    assert code != 0
    assert "no plugin banner" in out.lower()


def test_loader_log_fails_when_the_banner_names_the_other_host(tmp_path, capsys):
    log = tmp_path / "LogOutput.log"
    log.write_text(banner_line("server") + "\n", encoding="utf-8")
    code, out = run(["--loader-log", "--log-path", str(log)], capsys)
    assert code != 0
    assert "host mismatch" in out.lower()


def test_loader_log_fails_when_the_log_is_missing(tmp_path, capsys):
    missing = tmp_path / "absent" / "LogOutput.log"
    code, out = run(["--loader-log", "--log-path", str(missing)], capsys)
    assert code != 0
    assert "no loader log" in out.lower()


def test_default_log_path_is_each_hosts_own_log():
    client = bridge_probe.default_log_path("client")
    server = bridge_probe.default_log_path("server")
    assert client == DEFAULT_INSTALL / "BepInEx" / "LogOutput.log"
    assert server == DEFAULT_INSTALL / "VRising_Server" / "BepInEx" / "LogOutput.log"


# --------------------------------------------------------------------------
# leg 4 - liveness
# --------------------------------------------------------------------------
def test_motion_diff_fails_when_the_two_samples_are_identical(serve, capsys):
    sample = envelope(character())
    serve({"/state": [sample, sample]})
    code, out = run(["--motion-diff", "--interval", "0"], capsys)
    assert code != 0
    assert "no motion" in out.lower()


def test_motion_diff_passes_when_a_position_changes(serve, capsys):
    serve({"/state": [envelope(character(x=1.0)), envelope(character(x=9.5))]})
    code, out = run(["--motion-diff", "--interval", "0"], capsys)
    assert code == 0, out
    assert "position" in out.lower()


def test_motion_diff_passes_when_only_a_vital_changes(serve, capsys):
    serve(
        {
            "/state": [
                envelope(character(health_now=100.0)),
                envelope(character(health_now=71.5)),
            ]
        }
    )
    code, out = run(["--motion-diff", "--interval", "0"], capsys)
    assert code == 0, out
    assert "vitals" in out.lower()


def test_motion_diff_fails_when_state_is_null_rather_than_reporting_a_pass(
    serve, capsys
):
    serve({"/state": [envelope(None), envelope(None)]})
    code, out = run(["--motion-diff", "--interval", "0"], capsys)
    assert code != 0
    assert "load a character" in out.lower()
    assert "no motion" not in out.lower()


def test_motion_diff_prints_both_samples(serve, capsys):
    serve({"/state": [envelope(character(x=1.0)), envelope(character(x=9.5))]})
    code, out = run(["--motion-diff", "--interval", "0"], capsys)
    assert code == 0, out
    assert "sample 1" in out.lower()
    assert "sample 2" in out.lower()


# --------------------------------------------------------------------------
# the D6 envelope
# --------------------------------------------------------------------------
def test_state_accepts_a_null_state_member(serve, capsys):
    serve({"/state": [envelope(None)]})
    code, out = run(["--state"], capsys)
    assert code == 0, out


def test_state_accepts_a_populated_state_member(serve, capsys):
    serve({"/state": [envelope(character())]})
    code, out = run(["--state"], capsys)
    assert code == 0, out


def test_state_rejects_a_bare_null_body(serve, capsys):
    serve({"/state": ["null"]})
    code, out = run(["--state"], capsys)
    assert code != 0
    assert "envelope" in out.lower()


def test_state_rejects_a_missing_envelope_field(serve, capsys):
    body = envelope(None)
    del body["snapshot_age_s"]
    serve({"/state": [body]})
    code, out = run(["--state"], capsys)
    assert code != 0
    assert "snapshot_age_s" in out


# --------------------------------------------------------------------------
# house rules
# --------------------------------------------------------------------------
def test_probe_contains_no_port_or_url_literal():
    text = Path(bridge_probe.__file__).read_text(encoding="utf-8")
    assert not re.search(r"\b87\d\d\b", text), "a port literal leaked into the probe"
    assert "127.0.0.1:" not in text, "a composed URL literal leaked into the probe"


def test_exactly_one_leg_is_required(capsys):
    with pytest.raises(SystemExit):
        bridge_probe.main([])
    with pytest.raises(SystemExit):
        bridge_probe.main(["--health", "--state"])

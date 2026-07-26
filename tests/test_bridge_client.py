"""URL composition for the bridge. No consumer may write a URL or a port."""
import re
from pathlib import Path

import pytest

from core import bridge_client, ports

MODULE_PATH = Path(bridge_client.__file__)


def test_default_host_is_loopback(monkeypatch):
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    assert bridge_client.game_host() == "127.0.0.1"


def test_game_host_env_overrides_the_default(monkeypatch):
    monkeypatch.setenv(ports.GAME_HOST_ENV, "legion-rm")
    assert bridge_client.game_host() == "legion-rm"
    assert bridge_client.base_url("client") == f"http://legion-rm:{ports.BRIDGE}"


def test_blank_env_value_falls_back_rather_than_composing_an_empty_host(monkeypatch):
    monkeypatch.setenv(ports.GAME_HOST_ENV, "   ")
    assert bridge_client.game_host() == "127.0.0.1"


def test_base_url_uses_the_port_for_the_named_host(monkeypatch):
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    assert bridge_client.base_url("client") == f"http://127.0.0.1:{ports.BRIDGE}"
    assert bridge_client.base_url("server") == f"http://127.0.0.1:{ports.BRIDGE_SERVER}"


def test_the_two_hosts_never_compose_the_same_url(monkeypatch):
    """ADR-005 exists precisely so these differ."""
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    assert bridge_client.base_url("client") != bridge_client.base_url("server")


def test_unknown_host_raises_rather_than_defaulting():
    for bad in ("Client", "", "both", "dedicated"):
        with pytest.raises(ValueError):
            bridge_client.base_url(bad)


def test_endpoint_url_joins_without_doubling_or_dropping_the_slash(monkeypatch):
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    expected = f"http://127.0.0.1:{ports.BRIDGE}/health"
    assert bridge_client.endpoint_url("client", "health") == expected
    assert bridge_client.endpoint_url("client", "/health") == expected


def test_endpoint_url_carries_a_query_string(monkeypatch):
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    url = bridge_client.endpoint_url("server", "/dump/prefabs", {"table": "items"})
    assert url == f"http://127.0.0.1:{ports.BRIDGE_SERVER}/dump/prefabs?table=items"


def test_module_contains_no_url_or_port_literal():
    """The whole point of the module: composition happens here, from constants."""
    text = MODULE_PATH.read_text(encoding="utf-8")
    assert not re.search(r"\b87\d\d\b", text), "a port literal leaked into the client"
    assert "127.0.0.1:" not in text, "a composed URL literal leaked into the client"


def test_unreachable_bridge_raises_the_typed_error(monkeypatch):
    """A closed bridge is the normal case, not an exception the caller must
    distinguish from a bug. Leg 1 of the wiredness proof depends on this."""
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    with pytest.raises(bridge_client.BridgeUnreachable):
        # Nothing is listening on the bridge ports during the suite.
        bridge_client.get_json("client", "/health", timeout=0.25)


def test_bridge_unreachable_message_names_the_host_and_url(monkeypatch):
    monkeypatch.delenv(ports.GAME_HOST_ENV, raising=False)
    try:
        bridge_client.get_json("server", "/health", timeout=0.25)
    except bridge_client.BridgeUnreachable as exc:
        assert "server" in str(exc)
        assert str(ports.BRIDGE_SERVER) in str(exc)
    else:
        raise AssertionError("expected BridgeUnreachable")

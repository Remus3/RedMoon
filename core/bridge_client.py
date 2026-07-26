"""The one place a Red Moon consumer composes a URL for RedMoon.Bridge.

Two things are deliberately NOT the caller's business: which port a host binds
(ADR-005 makes that a function of the host) and where the game lives (the
RM_GAME_HOST environment variable, so moving the game to another box stays a
config change). A consumer names the HOST it wants - "client" or "server" - and
nothing else.

Read-only. Cycle 2 has no write path into the game (spec section 3).
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from core import ports

DEFAULT_GAME_HOST = "127.0.0.1"
"""Loopback. The bind is the security boundary for cycle 2, so this default is
also the only value with no network exposure."""

DEFAULT_TIMEOUT_S = 2.0


class BridgeUnreachable(RuntimeError):
    """The bridge did not answer.

    Raised for a refused connection, a timeout, a DNS failure or a non-JSON
    body. A closed game is the ordinary case rather than a defect, so callers
    catch this one type instead of unpacking urllib's error hierarchy. Leg 1 of
    the wiredness proof (spec D5) is an assertion that this is raised.
    """


def game_host() -> str:
    """Return the host every live reader talks to.

    A blank or whitespace-only environment value falls back to the default
    rather than composing an empty authority, which would otherwise produce a
    URL that fails much later and much less clearly.
    """
    value = os.environ.get(ports.GAME_HOST_ENV, "")
    return value.strip() or DEFAULT_GAME_HOST


def base_url(host: str) -> str:
    """Return the scheme, host and port for a bridge host.

    Raises ValueError for an unrecognised host, via bridge_port_for_host. That
    is deliberate: silently defaulting an unknown host onto the client's port is
    exactly the "read the wrong world while believing it read the right one"
    failure ADR-005 exists to remove.
    """
    return f"http://{game_host()}:{ports.bridge_port_for_host(host)}"


def endpoint_url(host: str, path: str, query: dict[str, str] | None = None) -> str:
    """Compose a full endpoint URL. `path` may be given with or without a slash."""
    url = f"{base_url(host)}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    return url


def get_json(
    host: str,
    path: str,
    query: dict[str, str] | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
) -> dict:
    """GET an endpoint and decode its JSON body.

    An HTTP error status is NOT unreachable - the bridge answered, and its
    error envelope carries a code and a friendly message the caller wants to
    see. Those bodies are decoded and returned like any other.
    """
    url = endpoint_url(host, path, query)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raw = exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise BridgeUnreachable(
            f"bridge unreachable: no {host} bridge answered at {url} ({exc})"
        ) from exc

    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BridgeUnreachable(
            f"bridge unreachable: the {host} bridge at {url} "
            f"returned a body that is not JSON ({exc})"
        ) from exc

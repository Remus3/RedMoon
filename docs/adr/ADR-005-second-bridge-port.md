# ADR-005 - A second bridge port instead of arbitration

**Status:** Accepted, 2026-07-26
**Amends:** ADR-003 (port map), which declared exactly four ports.
**Depends on:** ADR-004 (one plugin assembly, two hosts).

## Context

ADR-004 rules that RedMoon.Bridge loads into BOTH V Rising hosts: the client at
the install root and the dedicated server under `VRising_Server\`. Both can run
at once on this machine - the operator plays the client against a locally hosted
dedicated server. Two listeners cannot both hold port 8777.

The approved cycle 2 spec answered this with bind-time first-come: whoever binds
first owns 8777, the loser writes a stand-down banner and serves nothing, and an
operating procedure mandates starting the dedicated server first so first-come
resolves to the server. The spec named that honestly - it is a procedure, not an
enforcement - and left the alternative open for a ruling before implementation.

## Decision

Red Moon owns FIVE ports. The bridge binds a port selected by the host it
detects at load:

| Host | Port | Constant |
|---|---|---|
| V Rising client | 8777 | `ports.BRIDGE` |
| V Rising dedicated server | 8780 | `ports.BRIDGE_SERVER` |

`core.ports.bridge_port_for_host(host)` is the single rule. It is total over
`("client", "server")` and raises on anything else, so an unrecognised host is a
loud failure rather than a silent default onto the client's port.

The client keeps 8777 rather than yielding it to the server. Solo client is the
dominant topology, and `tools/rm_facts.py` is frozen and already probes 8777, so
the common case keeps working with no change to a frozen file. The dedicated
server is the additive topology and takes the additive port.

8780 was confirmed free on this machine on 2026-07-26, alongside a re-check of
the original four.

## Consequences

What this removes from the cycle 2 spec:

- The stand-down path in `HttpService.cs`. There is no losing host.
- The mandated server-first start order. Start order stops mattering.
- Acceptance criterion 5b and its live-gate leg, the arbitration negative
  control. There is no arbitration left to control for.
- Risk R15 as written. Contention cannot occur; the residual risk is a wrong
  host detection, which is R17 and spike S1 territory.

What this costs:

- One more port in the registry and one more generated C# constant.
- A Python consumer must now say WHICH host it wants. `core/bridge_client.py`
  takes a host and composes its URL from `bridge_port_for_host`. No consumer
  writes a URL or a port literal, so the cost is a parameter, not a rule change.

What it buys beyond tidiness: both hosts can serve simultaneously. Under
first-come they could not. Cycle 3 Bloodforge wants the prefab dump, which is
expected to live in the server's simulation world; cycle 4 wants live player
state, which is in the client. With one contended port those two consumers are
in conflict whenever both hosts run. With two ports they are not.

`/health` still reports `host`, and `tools/bridge_probe.py` still takes
`--expect-host`. Their role changes from safety mechanism to assertion: the port
now determines which host answers, and `--expect-host` proves the plugin agrees
with the port it bound. A mismatch means host detection is wrong, which is
exactly the failure worth catching.

## Alternatives rejected

**Keep bind-time first-come.** Rejected. It leans on an operating procedure a
future session will not remember, it makes "the consumer read the wrong world"
a live failure mode mitigated only by an assertion the consumer has to opt into,
and it costs more code than the port it saves.

**Give the server 8777 and move the client.** Rejected. It reads better on the
theory that the server is authoritative, but it breaks the frozen
`tools/rm_facts.py` probe for the topology the operator actually runs most.

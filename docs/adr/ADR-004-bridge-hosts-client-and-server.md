# ADR-004 - RedMoon.Bridge targets both the client and the dedicated server

**Status:** Accepted, 2026-07-26

## Context

ADR-002 settled that a BepInEx plugin, RedMoon.Bridge, is the live game data
source. It did not say which V Rising process the plugin loads into.

The install ships two hosts: `VRising.exe` at the install root, and
`VRising_Server\VRisingServer.exe`. They are different processes with different
ECS worlds. The client is where the operator's live session actually is, and
where character, gear, blood, cooldowns and the world clock are observed as
played. The dedicated server is the host where a server simulation world is
unambiguously present, and item stats and prefab data are expected to live in a
server world.

The cycle 2 design draft scoped the plugin to the CLIENT alone. That scoping
rested on an unverified assumption: that when V Rising is played solo or as a
private host, the server simulation world is created inside the client process
and is therefore reachable in-process. The assumption was flagged as a spike, but
the whole design depended on it, so a NO answer would have invalidated the cycle
rather than costing it a feature.

## Decision

RedMoon.Bridge targets BOTH hosts. One assembly, two install targets:

| Host | Loader and plugin install into |
|---|---|
| Client | the game ROOT, the directory `VRising.exe` launches from |
| Dedicated server | `<root>\VRising_Server\`, where `VRisingServer.exe` launches from |

The plugin detects at load which host it is in, selects the worlds it reads
accordingly, and reports the result in `/health` as a `host` field valued
`client` or `server`.

Port 8777 is arbitrated at bind time, because both hosts can be running at once
on one machine and only one listener can hold the port:

1. Each host attempts the bind exactly once at plugin initialization. Whoever
   binds first owns 8777 for the life of that process.
2. The loser STANDS DOWN. It does not retry, does not fall back to another port,
   and does not throw into the game. It writes one banner line naming the
   condition and serves nothing. A silent second listener on a shifted port is
   worse than no listener, because it lets a consumer read the wrong world while
   believing it read the right one.
3. The operating procedure mandates starting the dedicated server BEFORE the
   client in the dual-host case, so first-come resolves deterministically to the
   server, which holds the authoritative simulation world.
4. `/health` reports `host` so a consumer can always tell which host answered,
   and `tools/bridge_probe.py --expect-host` fails when it is not the expected
   one.
5. No fifth Red Moon port is minted. A genuinely concurrent dual-serve topology
   would need an ADR-003 amendment and is deliberately out of cycle 2.

## Consequences

Accepted costs, stated rather than discovered later:

- TWO INSTALL TARGETS TO VERIFY PER PATCH. The assembly still builds once, but
  the per-patch VERIFICATION roughly doubles: `tools/install_bepinex.py` asserts
  two distinct target profiles, the DLL is deployed twice, and the four-leg live
  wiredness proof runs once per host. A host that is not re-proved after a patch
  is silently unwired, which is precisely the failure the wiredness proof exists
  to catch, now with a second place to hide.
- A HOST-DETECTION PATH inside the plugin. New surface that did not exist in the
  client-only design, in the blast radius of every patch, and with an unknown
  mechanism. It is a spike output, not an assumption; no detection path is
  scaffolded against a guessed process or assembly name.
- A PORT-COLLISION PATH, answered by the arbitration above. It carries its own
  live negative control: with the server started first and the client second,
  the client must log its stand-down and must not be listening.
- POSSIBLE INTEROP DIVERGENCE. Whether the two hosts generate the same
  Il2CppInterop assembly set is unknown. If they diverge, one assembly must
  compile against the intersection and reach host-specific types behind the host
  detection. This is checked before any reference is pinned.

What it buys:

- Red Moon reads live state in either topology - solo, private host, or a local
  dedicated server - without a second plugin.
- The design no longer depends on the unverified in-client-server-world claim.
  If that claim is false, the client target loses a feature instead of the cycle
  losing its premise.
- ADR-002's scope is unchanged: solo and private-host play. Targeting the shipped
  dedicated server is not official-server use.

# Architectural Decision Records

Before re-litigating a past choice, read the relevant record here first.

- [ADR-001](ADR-001-separation-from-riot-commander.md) - Red Moon is a standalone project
- [ADR-002](ADR-002-bepinex-bridge-live-source.md) - A BepInEx plugin is the live game data source
- [ADR-003](ADR-003-port-map.md) - Port map
- [ADR-004](ADR-004-bridge-hosts-client-and-server.md) - RedMoon.Bridge targets both the client and the dedicated server
- [ADR-005](ADR-005-second-bridge-port.md) - A second bridge port instead of arbitration (amends ADR-003)

## Format

One file per decision, named `ADR-NNN-kebab-slug.md`, with sections Context,
Decision, Consequences and Status. Add a line to the list above in the same
commit; a test asserts the index and the directory agree.

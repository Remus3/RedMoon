# Architectural Decision Records

Before re-litigating a past choice, read the relevant record here first.

- [ADR-001](ADR-001-separation-from-riot-commander.md) - Red Moon is a standalone project
- [ADR-002](ADR-002-bepinex-bridge-live-source.md) - A BepInEx plugin is the live game data source
- [ADR-003](ADR-003-port-map.md) - Port map
- [ADR-004](ADR-004-bridge-hosts-client-and-server.md) - RedMoon.Bridge targets both the client and the dedicated server
- [ADR-005](ADR-005-second-bridge-port.md) - A second bridge port instead of arbitration (amends ADR-003)
- [ADR-006](ADR-006-recipe-stations-are-plural.md) - A recipe has many stations, so `station_guid` becomes `station_guids`
- [ADR-007](ADR-007-coefficients-are-keyed-on-the-ability-group.md) - The coefficient key space is the ability GROUP, not the ability and not the school
- [ADR-008](ADR-008-cycle-4-frontend-stack.md) - Cycle 4 renders server-side HTML with no frontend framework

## Format

One file per decision, named `ADR-NNN-kebab-slug.md`, with sections Context,
Decision, Consequences and Status. Add a line to the list above in the same
commit; a test asserts the index and the directory agree.

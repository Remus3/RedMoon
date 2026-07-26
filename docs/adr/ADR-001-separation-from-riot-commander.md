# ADR-001 - Red Moon is a standalone project

**Status:** Accepted, 2026-07-26

## Context

Red Moon reproduces a working method proven on Riot Commander, an existing
League of Legends project on the same machine: doctrine in `CLAUDE.md`,
enforcement hooks, living docs, an ADR index, an append-only ledger, a memory
namespace, and a subagent-first build protocol. The obvious shortcut is to
share code, tooling or data between the two.

The two domains have nothing in common at runtime. One reads a vendor-supplied
live API over HTTP; the other must reach into a Unity DOTS entity world through
a mod. Their data models, patch cadences and failure modes are unrelated.

## Decision

Red Moon shares **no** code, data, keys, ports or scheduled-task namespace with
Riot Commander or any other project on this machine. What is reproduced is the
method, by writing fresh files, not by importing or symlinking.

Concretely: its own git repository at `C:\RedMoon\`, its own Anthropic key at
`C:\RedMoon\API-Key-Claude.txt`, its own memory namespace, the `RM-` prefix for
scheduled tasks, and the port set in ADR-003.

## Consequences

- Doctrine drift between the projects is expected and acceptable. Each evolves
  against its own domain.
- Improvements do not propagate automatically. Porting one is a deliberate act.
- Neither project can break the other by refactoring shared code, because there
  is none.
- A test asserts no root document mentions Riot Commander by name or path.

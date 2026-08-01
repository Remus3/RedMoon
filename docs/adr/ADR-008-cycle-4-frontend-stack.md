# ADR-008 - Cycle 4 renders server-side HTML with no frontend framework

## Context

Cycle 4 is the HTTPS dashboard on port 8778 (ADR-003). Nothing is built: the
port exists in `core/ports.py`, the cycle has a ROADMAP heading, and there is no
code. That made the frontend stack an open question, and an open question that
would have been answered by whoever wrote the first file rather than by a
decision.

The question was forced now, deliberately, because it is not neutral. Red Moon's
own link-ingest review scored `CCR-04` (Augments, an npm and JS-framework API
doc injector) at **2 today and about 5 if cycle 4 adopts a framework**
(`docs/research/LINK_INGEST.md`, stage 2b). A corpus entry whose value depends on
an undeclared choice is a signal that the choice is load-bearing.

Three concept agents were run over disjoint lenses - what the dashboard OBSERVES,
what it COACHES, and how it shows PROVENANCE - and each was asked independently
what stack its own concepts implied. **All three returned no-framework without
being told the others' answers.** The reasons they gave were different, which is
what makes the agreement worth something.

Measured facts behind the ruling, each verified against the tree rather than
recalled:

- **The bridge serves exactly 5 GET routes and has no push transport of any
  kind** - `/health`, `/state`, `/dump/prefabs`, `/dump/components`,
  `/dump/statcontrol` (`bridge/src/RedMoon.Bridge/BridgeServer.cs:346-405`). So
  the dashboard server must poll the bridge no matter what the browser does, and
  the transport question only ever applied to the browser leg.
- **There is no `package.json` anywhere in the repository.** Adopting a
  framework does not add a dependency, it adds a dependency SYSTEM - a build
  step, a lockfile, and a `node_modules` tree - to a repo that is Python plus C#
  and has neither.
- **The data is small and mostly static.** The six promoted tables are about
  2,038 rows total and change once per game patch. A cross-table filter is a
  linear scan.
- **The genuinely hard problems on this surface are semantic, not rendering.**
  The five-state uncertainty vocabulary (COMPUTED, MEASURED ZERO, OMITTED,
  UNSOURCED-ON-BUILD, EMBARGOED), an honest display of four resistances that
  must never be averaged, and a subject bar that states its own defaults are all
  problems a framework does not touch.
- `ops/runtime/health.json` does not exist, and `ROADMAP.md:217` places it in
  cycle 8. Cycle 4 has no ops state to consume and must derive its own.

## Decision

**Cycle 4 renders server-side HTML from a Python standard-library server on
8778, plus roughly 200 lines of hand-written vanilla JavaScript and inline SVG.
No framework, no build step, no `package.json`, no `node_modules`.**

Four consequences are part of the decision rather than discovered later.

1. **The transport is tiered, not uniform.** A single transport for everything
   would be wrong given how differently the sources change:

   | Tier | Source | Transport | Why |
   |---|---|---|---|
   | A | `/state` | SSE, 2 Hz | The bridge republishes its snapshot at about 4 Hz (`StateReader.cs:74-77`); sampling above 2 Hz buys duplicates. |
   | B | `/health` | Same SSE stream, separate event | Cheap, and it shares the connection. |
   | C | The promoted tables | Plain GET with an ETag on the build stamp | Changes once per game patch. |
   | D | `/dump/*` | Explicit operator action ONLY | A dump runs on the game's MAIN THREAD under a global gate (`BridgeServer.cs:279-308`, `:448`). A timer here would hitch the live game. |

2. **The SSE stream must carry a heartbeat and must debounce.** This is not
   inherited from the reference - it is a correction TO it. The `CCR-120`
   reference (`claude-task-viewer`) was read at source and has neither, which is
   merely sloppy there and would be fatal here: Red Moon's stream idles for
   HOURS because the game is usually not running, and a silent idle stream is
   indistinguishable from a dead one.

3. **`tools/ascii_guard.py` must learn the new suffixes.** `AUTHORED_SUFFIXES`
   today is `.py .md .json .txt .ps1 .bat .cmd .toml .ini .cs .yml` and does
   **not** include `.js`, `.html` or `.css`. Cycle 4's first frontend file would
   otherwise sit outside the project's own 7-bit-ASCII hard rule. That file is
   FROZEN, so the amendment needs explicit operator approval and must land
   BEFORE the first frontend file, not after.

4. **The browser never talks to 8777 or 8780.** All bridge access is proxied
   through 8778. Partly this is ordinary isolation, and partly it is that
   `tests/test_ports.py` scans `.py`, `.cs`, `.json` and `.ps1` and would not
   see a port literal hard-coded in a `.js` file.

## Consequences

**Good.**

- No build step means the repo's existing gates - the precommit gate, the ASCII
  guard, the port-literal test - keep working on the frontend once consequence 3
  lands. A framework would have put the shipped artifact behind a compiler that
  none of those gates inspect.
- `CCR-04` stays at 2 and is closed rather than parked, which removes the only
  corpus entry whose score was contingent on an undeclared decision.
- The reference implementation proves vanilla suffices at this scale.

**Costs, stated rather than discovered later.**

- Hand-written DOM updates are more error-prone than declarative rendering, and
  there is no component model. The mitigation is scope: tier A is the only
  live-updating region, and it is one vitals tape plus a small status block.
- If cycle 5's progression planner needs an interactive dependency graph, this
  decision should be REVISITED rather than worked around. Revisiting it is
  cheap precisely because there is no build system to dismantle.
- Server-rendered HTML from a stdlib server means no hot reload.

**Explicitly not decided here.** Which concepts ship, in what order. That is
`docs/research/DASHBOARD_CONCEPTS.md`.

## Status

Accepted, 2026-08-01, by operator ruling after a three-lens agent adjudication.
Nothing is implemented; this decision governs the first file written.

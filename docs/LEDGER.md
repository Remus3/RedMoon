# Red Moon Ledger

Append-only, **newest first**. One entry per completed roadmap item.

Entries belong here and never in `CLAUDE.md`, which is size-budgeted and loaded
into context every turn.

Format:

```
## <item number> - <title> (YYYY-MM-DD)
What shipped, the verification that proved it, and the commit or merge hash.
```

---

## 001 - Cycle 1: harness plus data floor (2026-07-26)

Shipped the Red Moon process harness and the offline data floor. ASCII guard,
port registry, doctrine documents, living docs, ADR-001 through ADR-003, the
data extractor, typed table schemas, four enforcement hooks, the verifier
subagent, three slash commands, the memory namespace seed, and RM-DataRefresh
registration.

Closed out by the whole-branch review fix wave: the precommit gate's hook
matcher was a permission-rule specifier, which never matches a tool name, so the
gate had never fired; the extractor now creates the `tables/` seam cycle 2 dumps
into; the port-literal rule is enforced for Red Moon's own ports across `.py`,
`.cs`, `.json` and `.ps1`; and the memory namespace has a committed seed under
`docs/memory_seed/` with a drift guard.

Verified: `python -m pytest` reports 106 passed; `python -m ruff check .` is
clean; `python tools/ascii_guard.py` exits 0; `python tools/rmdata_extract.py`
is idempotent and writes `data/rmdata/1.1.13.0-r99712/`; the commit gate blocks
a staged em-dash.

Merge: `2a493ea` (branch `cycle-1-harness`, 34 commits, merged into `master`)
Spec: `docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`
Plan: `docs/superpowers/plans/2026-07-26-redmoon-cycle1-harness.md`
Execution record: `docs/history_notes.md`

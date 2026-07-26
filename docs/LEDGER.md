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

## 002a - Cycle 2 part 1: ADR-005, the Python half, and the spike environment (2026-07-26)

Cycle 2 is NOT done. This is a partial entry for the part that shipped, written
so the next session does not re-derive it. Entry 002 proper is appended when the
plugin is live-proved.

**ADR-005 minted a fifth port and struck the arbitration.** The approved spec
answered the port-8777 collision between the two ADR-004 hosts with bind-time
first-come plus a procedural "start the dedicated server first". That was
procedure, not enforcement. Ruled instead: the client binds 8777, the dedicated
server binds 8780, and the choice is a pure function of the detected host via
`core.ports.bridge_port_for_host`, which is total over the two hosts and raises
otherwise. Struck as a consequence: the stand-down path, install step 6b,
acceptance criterion 5b and risk R15. Both hosts can now serve at once, which
first-come could not do and which cycle 3 and cycle 4 actually need. The client
kept 8777 because solo client is the dominant topology and the frozen
`tools/rm_facts.py` already probes that number. `core/ports.py` is frozen and
ADR-003 was Accepted; both edits were operator-approved before the change.

**Shipped:** `tools/gen_bridge_ports.py`, `core/bridge_client.py`,
`core/table_deep.py`, `tools/install_bepinex.py`, `tools/rmdata_ingest.py`,
`tools/bridge_probe.py`, `bridge/Directory.Build.props`, the generated
`RmPorts.g.cs`, ADR-005, and `docs/BRIDGE_SPIKES.md`.

**Verified, all observed in one run after the last edit rather than carried
forward from a subagent's report:** `python -m pytest` reports **241 passed**
(was 106); `python -m ruff check .` is clean; `python tools/ascii_guard.py`
exits 0.

**Verified live against the real install, not against a fixture:**

- Both v3 negative controls REFUSE with `v3-path-component` and write nothing.
- The client profile pointed at `VRising_Server` refuses with
  `client-target-is-server-dir`.
- HONEST CORRECTION to acceptance criterion 2: the fourth negative control,
  `--target server` pointed at the root, is UNREACHABLE rather than refused. The
  installer takes `--root` and derives the server target from it, so the
  mismatch cannot be expressed. Prevented by construction beats refused, but it
  is not the control the spec asked for and is not recorded as one.
- BepInEx 1.733.2 installed into both hosts, 233 files each, Thunderstore
  metadata correctly dropped, `v3\` untouched.
- The dedicated server launched once and generated 169 Il2CppInterop assemblies.

**Spikes closed by measurement:** S4 (a net6.0 library builds under SDK 10.0.301
with no targeting pack and no `global.json` - neither fallback is needed, R2
retired for the bare TFM) and S3a (`ProjectM.PrefabCollectionSystem` is REAL in
`ProjectM.Shared.dll` - the unverified roadmap label is CONFIRMED, not
corrected). S3 is partially resolved: the component types are located and named,
the field mapping is not done. S1, S2, S5 and S6 remain OPEN.

**Not done, and not claimed:** no plugin C# is written, nothing is built against
the interop set, and no leg of the D5 wiredness proof has run. Leg 4 structurally
requires the operator to load a character and move it.

Commits: `9fbce0c` (ADR-005), `251803b` (the Python half), branch
`cycle-2-bridge`.
Spec: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`
Spike findings: `docs/BRIDGE_SPIKES.md`

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

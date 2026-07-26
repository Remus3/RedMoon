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

## 002b - Cycle 2 part 2: the probe plugin closes seven spikes (2026-07-26)

Cycle 2 is still NOT done and no bridge code exists yet. This is the spike-closure
entry. Entry 002 proper is appended when the plugin is live-proved.

**The artifact is a probe, not the bridge.** `_scratch\rmprobe\`, a minimal
enumerate-and-log BepInEx plugin, built and deployed into both hosts before any
bridge code, because S1(b), S1(c), S1(d), S2, S5 and S6 are not answerable from
static metadata. Scratch and deliberately not committed, the same rule as
`_scratch\typedump\`: regenerable, and it must not become a second plugin to
maintain per patch. It compiles the SAME generated `RmPorts.g.cs` the real plugin
will, so the no-port-literal rule holds even in scratch, and it reads ECS only
from `Update()` while its listener thread serves a constant, so it exercises both
halves of D7 without violating D7 or risk R4.

**R17 CLOSED, and the obvious diff was the wrong one.** The client was launched
and generated its own `BepInEx\interop\`: 172 files, 169 `.dll`, matching the
server exactly - which also explains the previously recorded "169 assemblies" as
the dll count, so no correction was owed. Assembly name sets are identical. All
169 SHA256 hashes differ, and that is NOT a divergence signal: Il2CppInterop
codegen is non-deterministic, so a hash diff reports total divergence between any
two generations and would have manufactured a blocking finding. The type-level
diff is the one that decides the `.csproj`: 97 client-only and 591 server-only
types, almost all of it per-build codegen noise
(`__JobReflectionRegistrationOutput__<hash>`, `__UnmanagedPostProcessorOutput__<hash>`,
closure and iterator types), with the real divergence confined to 499 server-only
netcode serializers, about 17 server-only send-priority types in `ProjectM`, and
client-only Rukhanka animation types. None is needed. `ProjectM.Shared`,
`Stunlock.Core`, `Unity.Entities` and `ProjectM.Gameplay.Systems` have zero real
divergence and every design-needed type was checked present in both sets by name.

**S4 fully closed and R2 retired.** The build succeeds with the entire reference
set added, not just the bare target framework. `Paths.BepInExVersion` returns a
`SemanticVersioning.Version`, which forces one non-obvious reference.

**S1(a)** is `World.All`. **S1(d)** is `BepInEx.Paths.ProcessName`, measured as
`VRising` and `VRisingServer`. **S1(c)**: the server's target world is named
`Server` with 710 systems, and selection must be BY NAME - `Default World` is also
a Simulation world, sits at index 0, and throws `ArgumentException` when asked for
the prefab map, while `LoadingWorld0` throws `InvalidOperationException`. Those
two exceptions are the natural `world_not_ready` path and a genuine negative
control that a stub cannot produce. **S2**: an Il2Cpp-injected `MonoBehaviour`
`Update` reaches main thread 1 in both hosts, so no Harmony patch is needed and
D7 is implementable as written. **S5 and R11**: `HttpListener` binds and serves in
both hosts concurrently, which is the ADR-005 payoff observed rather than argued,
and after `taskkill /F` the port holds no LISTEN while
`bridge_probe.py --expect-unreachable` passes. **S6 partial**: the prefab lookup
map reports `Count` 1189 in under a millisecond, so reading it needs no chunking;
the dump itself is still unmeasured. **S3 advanced**: `items` and `recipes` are
mapped, and the headline is that `EquippableData` carries NO stats, only a
`BuffGuid`, so `items.stats` is a two-hop read through the buff prefab's
`DynamicBuffer<ModifyUnitStatBuff_DOTS>`.

**One real defect, found by the probe rather than by a test.** The suite carried a
test whose comment read "nothing is listening on the bridge ports during the
suite" and which depended on it being true. The probe bound the client port, the
connection succeeded, and the test failed with no defect anywhere in the code
under test - the mirror image of cycle 1's gate that could not fail. Fixed by
pointing `RM_GAME_HOST` at `192.0.2.1`, RFC 5737 TEST-NET-1, so unreachability is
a property of the test rather than of the machine.

**Left open, honestly.** S1(b) has only the client MAIN MENU sample: two worlds,
no prefab-carrying world, so a client-side dump is UNPROVEN. The remainder of S3
is gated behind the same in-game sample. The operator chose to wrap rather than
load a character.

Verification, all observed in one run after the last edit: `python -m pytest` 245
passed, `python -m ruff check .` clean, `python tools/ascii_guard.py` exit 0. The
245 was observed with the probe still bound to the client port and answering
`curl`, which is the exact condition that broke the old test.

Commits: `9a036d2`, `46ec231`, `003d027`, plus the docs sync.

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

**Process incident, recorded rather than buried.** `251803b` was committed while
a build subagent was still live, and it captured that agent's file mid-mutation
test: the v3 guard in `tools/bridge_probe.py` is committed as `if False:` in
that one commit. Verified directly with `git show 251803b:tools/bridge_probe.py`
rather than taken on the agent's report. The guard is CORRECT at `d614a09` and
at HEAD, the working tree is clean, and a fresh full run after the fact is 245
passed / ruff clean / ascii_guard 0. No history rewrite: the defect existed in
one intermediate commit and is fixed in the next, which is what a branch is for.

The lesson is the standing one and it was paid for again here: do not commit
while agents are live, and check `git show --stat` after every commit. A green
suite taken moments before a `git add -A` does not describe what `git add -A`
actually staged.

Worth carrying separately: that agent's own mutation testing found a real hole
in its tests. A mutation making the loader-log banner matcher accept any line
containing `RedMoon.Bridge` SURVIVED 25 tests, because the negative fixture
carried no banner token at all - cycle 1's exact failure mode, a gate that
cannot fail. Four parametrized tests were added and the mutation then failed.
This is the second time in two cycles that the bug was "the check never checked".

Consequence for the not-yet-written plugin: `Plugin.cs` MUST emit a banner
carrying all three tokens, version, host and port, in the shape
`RedMoon.Bridge v<semver> host=<client|server> port=<n>`. The matcher is
token-based and order-independent by design, but it requires all three.

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

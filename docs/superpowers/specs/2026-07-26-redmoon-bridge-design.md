# Red Moon - RedMoon.Bridge (Cycle 2) Design

Date: 2026-07-26
Status: APPROVED, 2026-07-26
Scope: cycle 2 of an 8-cycle program. Cycle 1 spec:
`docs/superpowers/specs/2026-07-26-redmoon-harness-design.md`

## Operator rulings, 2026-07-26

The open questions this spec carried to approval are now settled. These rulings
are authoritative and override anything below that disagrees with them. The body
of the spec has been amended to match; this section is the short index.

1. **D1 is OVERRIDDEN.** The plugin targets BOTH the client and the dedicated
   server, not the client alone. One assembly, two install targets. The costs
   are accepted and stated in D1: two install targets to verify per patch, a
   host-detection path inside the plugin, and an explicit arbitration rule for
   port 8777 when both hosts run at once on one machine. ADR-004 records this.
2. **D6 is APPROVED.** `/state` returns an envelope carrying a `state` member
   that is `null` when no character is loaded, plus a build stamp. `docs/API.md`
   was amended in this same pass so the promised shape and the implemented shape
   agree.
3. **D2 is APPROVED.** Generating `bridge/src/RedMoon.Bridge/Generated/RmPorts.g.cs`
   from `core/ports.py` and adding that one path to `OWN_PORT_ALLOWLIST` in
   `tests/test_ports.py` is authorized.
4. **The C# test project deferral is APPROVED.** No `RedMoon.Bridge.Tests`
   project in cycle 2. This is a settled ruling, not an open question. It is
   revisited only if spike S3 produces a substantial pure mapping layer, and any
   revisit is recorded in `docs/LEDGER.md`.
5. **Download authorization is granted for the NEXT session only.** Claude may
   fetch `https://thunderstore.io/package/download/BepInEx/BepInExPack_V_Rising/1.733.2/`
   and extract it, subject to a VERSION assert on the target folder before any
   write. The grant is scoped to that one URL and that one session and does not
   generalize to any other download. See section 8, step 0.
6. **ADR-004 is written**, at `docs/adr/ADR-004-bridge-hosts-client-and-server.md`,
   and listed in `docs/adr/README.md`.

STILL OPEN. The six technical spikes in section 9 (S1, S2, S3 with S3a, S4, S5,
S6) are UNRESOLVED by these rulings. Nothing in this section confirms a type
name, a world name, a component name, a build configuration or a listener
mechanism. The ruling on D1 widens what S1 must confirm; it does not answer it.

## 1. Purpose

Build RedMoon.Bridge, the BepInEx plugin that is the live game data source for
Red Moon (ADR-002). It serves read-only JSON on loopback port 8777 from inside
the running V Rising process, and dumps the prefab collection so the cycle 1
table schemas can be filled with first-party item, ability, V Blood, blood type
and recipe data.

ADR-002 is settled. Offline ECS blob parsing and third-party GUID dumps are
rejected, and the plugin is rebuilt each patch. This spec does not relitigate
that and proposes no alternative to the plugin.

## 2. Ground truth probed 2026-07-26

Probed live this session. Do not contradict without re-probing.

- Install root: `C:\Program Files (x86)\Steam\steamapps\common\VRising`.
  `VERSION` = `v1.1.13.0-r99712-b17 (202605251526)`. This is the pinned build
  and the one Steam launches (`VRising.exe`, observed PID 6832).
- The install ALSO contains a full legacy copy at `v3\`, whose `VERSION` is
  `v1.0.10.4-r91333-b12`. It is NOT what launches. See section 4.8, the v3 trap.
- IL2CPP build: `GameAssembly.dll` is present at the root. Not Mono.
- The game was launched once.
  `%USERPROFILE%\AppData\LocalLow\Stunlock Studios\VRising\` now exists with
  `Player.log`, `Settings\v4\ClientSettings.json`,
  `CloudSaves\<steamid>\steam_autocloud.vdf` and `ConsoleProfile\`. No save
  directory appeared, because no world has been created yet.
- Loader: BepInExPack V Rising, latest `1.733.2`, wrapping BepInEx 6.0.0
  bleeding-edge `be.733`, CoreCLR .NET 6 runtime with Il2CppInterop. Download:
  `https://thunderstore.io/package/download/BepInEx/BepInExPack_V_Rising/1.733.2/`
  The payload extracts to a host directory: `BepInEx/`, `dotnet/`,
  `.doorstop_version`, `doorstop_config.ini`, `winhttp.dll`. Under the D1 ruling
  that directory is the game root for the client target and
  `<root>\VRising_Server\` for the dedicated-server target. Whether this pack
  installs into a dedicated-server folder unchanged was NOT probed this session;
  it is part of spike S1.
- `dotnet --list-sdks` = `10.0.301` at `C:\Program Files\dotnet\sdk`. The plugin
  targets `net6.0`. See risk R2; this is a build-time risk to resolve during
  implementation, not an asserted fact.

Verified from the repository this session:

- `tools/rmdata_extract.py` lines 116 to 124: `seed_tables` skips any table file
  that already exists. The never-clobber claim in `ROADMAP.md` is TRUE, and
  re-extraction stays safe after the bridge writes real rows.
- `core/tables.py` lines 74 to 95: `validate_table` type-checks top-level row
  fields only. It is a SHALLOW gate. See decision D4.
- `tests/test_ports.py` lines 100 to 113: Red Moon's own port literals are
  banned in `.cs` outside a four-entry allowlist. See decision D2.
- `tools/ascii_guard.py` lines 13 to 35: `.cs` is scanned, and `_scratch` is
  excluded. Both files are frozen. See decision D8.

## 3. Goal and non-goals

### Goal

1. A BepInEx plugin, ONE assembly, that loads in EITHER V Rising host - the
   client at the install root, or the dedicated server under `VRising_Server\` -
   binds `127.0.0.1:8777` in whichever host owns the port, and serves `/health`,
   `/state` and `/dump/prefabs`.
2. A Python-side ingest path that pulls the prefab dump and fills
   `data/rmdata/<build>/tables/*.json` through `core.tables.validate_table`,
   with a nested-shape audit on top.
3. A LIVE wiredness proof that the plugin is actually loaded and actually
   reading the game, not merely passing unit tests.
4. A build and install procedure that cannot target the wrong game copy.

### Non-goals

- No write path into the game. Cycle 2 is strictly read-only. No commands, no
  entity mutation, no cheats.
- No combat math. That is Bloodforge, cycle 3.
- No dashboard, no UI, no coach loop. Cycle 4.
- No authentication and no TLS on 8777. Loopback bind is the security boundary.
- No SIMULTANEOUS dual serve. Both hosts carry the plugin, but only one of them
  owns 8777 at a time; the loser stands down cleanly. A second bridge port for a
  second concurrent host is NOT minted in cycle 2 and would need an ADR-003
  amendment. See decision D1.
- No official-server use. ADR-002 scopes Red Moon to solo and private-host play.
- No C# combat, ranking or validation logic. See decision D3.

## 4. Decisions

### D1. The plugin targets BOTH the client and the dedicated server

OPERATOR RULING, 2026-07-26. The draft of this spec scoped cycle 2 to the client
process alone. That is OVERRIDDEN. The plugin must load in either host. Recorded
in ADR-004.

The install ships both `VRising.exe` at the root and
`VRising_Server\VRisingServer.exe`. Cycle 2 instruments BOTH. There is ONE plugin
assembly and TWO install targets:

| Host | BepInEx pack goes into | Plugin DLL goes into |
|---|---|---|
| Client | the game ROOT, the directory `VRising.exe` launches from | `<root>\BepInEx\plugins\RedMoon.Bridge\` |
| Dedicated server | `<root>\VRising_Server\`, the directory `VRisingServer.exe` launches from | `<root>\VRising_Server\BepInEx\plugins\RedMoon.Bridge\` |

Justification. The two hosts answer different halves of the same question. The
client process is where the operator's LIVE session actually is: character, gear,
blood, cooldowns, the world clock as played. The dedicated server is the host
where a server simulation world is unambiguously present, which is where item
stats and prefab data are expected to live. Targeting both means Red Moon reads
live state in either topology - solo, private host, or a locally hosted dedicated
server - without a second plugin and without the design depending on an
unverified claim about which worlds a solo client happens to contain.

What this costs, stated plainly rather than buried:

1. TWO INSTALL TARGETS TO VERIFY PER PATCH. ADR-002 already accepts a per-patch
   rebuild. This ruling roughly doubles the per-patch VERIFICATION work, not the
   build work: one assembly still builds once, but `install_bepinex.py` must
   assert two distinct target profiles, the DLL is deployed twice, and the
   four-leg wiredness proof of D5 runs once PER HOST. A host that is not
   re-proved after a patch is a host that is silently unwired, which is exactly
   the failure D5 exists to catch.
2. A HOST-DETECTION PATH INSIDE THE PLUGIN. The plugin must determine at load
   which host it is running in and select which worlds it reads accordingly, and
   it must report that determination in `/health` as a `host` field with the
   value `client` or `server`. This is new surface that did not exist in the
   client-only design, it is in the blast radius of every patch, and the
   mechanism for detecting the host is NOT KNOWN. It is folded into spike S1
   rather than assumed; do not scaffold a detection path against a guessed
   process name or assembly name.
3. A PORT-COLLISION QUESTION, answered below. Both hosts can be running at once
   on one machine: the operator plays the client while a dedicated server runs
   locally. 8777 is a single port and two listeners cannot both hold it.

ARBITRATION OF 8777 WHEN BOTH HOSTS RUN AT ONCE. The rule is bind-time
first-come, made deterministic by a mandated start order, and made observable by
`/health`:

1. The bind is attempted exactly once per host at plugin initialization. Whoever
   binds first OWNS 8777 for the life of that process.
2. The loser STANDS DOWN. On an address-already-in-use failure the plugin does
   NOT retry, does NOT fall back to a different port, and does NOT throw into
   the game. It writes one banner line naming the condition, records
   `bound: null` in its own log, and serves nothing for the rest of the session.
   A silent second listener on a shifted port is worse than no listener: it makes
   a consumer read the wrong world while believing it read the right one.
3. The OPERATING PROCEDURE mandates the start order in the dual-host case: the
   dedicated server is started BEFORE the client. First-come therefore resolves
   to the SERVER, which is the host holding the authoritative simulation world.
   This is a procedure, not an enforcement; the enforcement is that whoever loses
   says so loudly.
4. `/health` carries `host` (`client` or `server`) so a consumer can always tell
   WHICH host answered, rather than inferring it. `tools/bridge_probe.py` gains
   `--expect-host <client|server>` and fails if the answering host is not the
   expected one. Without this, a consumer that wanted the server and silently got
   the client is indistinguishable from success.
5. NO SECOND PORT is minted in cycle 2. ADR-003 declares exactly four Red Moon
   ports and a concurrent dual-serve topology would need a fifth. That is an
   ADR-003 amendment, deliberately deferred out of cycle 2. The BepInEx config
   entry for the port still defaults to `RmPorts.Bridge` (D2); an operator who
   overrides it is off the supported path and owns the result.

Spike S1 is KEPT and RESTATED. It no longer confirms a client-only assumption.
It now confirms ECS world access IN EACH HOST: enumerate and record the world
names visible to the plugin in the client process, and separately in the
dedicated-server process, and determine the host-detection mechanism. The old
claim - that a solo client contains a server simulation world - is downgraded
from a load-bearing assumption to an open question, because the design no longer
depends on it: if it is false, the client target still serves what the client
world has and the dedicated-server target covers the simulation world.

### D2. The port reaches C# by generation from `core/ports.py`, never by hand

Constraint: the C# side cannot import `core/ports.py`, and
`tests/test_ports.py::test_own_port_literals_appear_only_in_the_allowlist` bans
a `8777` literal in any `.cs` file outside a four-entry allowlist. Writing the
literal by hand violates a CLAUDE.md hard rule and fails the suite.

Decision, APPROVED by the operator 2026-07-26 including the `tests/test_ports.py`
allowlist edit:

1. `tools/gen_bridge_ports.py` imports `core.ports` and emits exactly one
   generated C# file, `bridge/src/RedMoon.Bridge/Generated/RmPorts.g.cs`,
   containing a single `internal const int Bridge` whose value is
   `ports.BRIDGE`. The file carries a "GENERATED, do not edit" banner naming its
   producer.
2. `tests/test_ports.py` gains that one path to `OWN_PORT_ALLOWLIST`. That file
   is a guard but is NOT on the frozen list in `CLAUDE.md`, so the edit is in
   scope. It is the only new place a Red Moon port may be spelled.
3. Every other `.cs` file reads `RmPorts.Bridge`. The BepInEx config entry for
   the port uses `RmPorts.Bridge` as its default value, so the loader-visible
   configuration also derives from `core/ports.py`.

The two are kept equal by `tests/test_bridge_ports.py`, which:

- regenerates the file into memory and asserts it is byte-identical to the file
  on disk. Editing `core/ports.py` without regenerating fails. Hand-editing the
  `.cs` fails. This is the drift gate.
- parses the emitted constant with a regex and asserts the integer equals
  `core.ports.BRIDGE`. This is a direct equality assertion, independent of the
  byte comparison, so a change to the generator's formatting cannot make the
  test pass vacuously.
- asserts the scan examined a non-zero number of files, mirroring the
  anti-vacuous assertion style already used in `tests/test_ports.py`.

`tools/ascii_guard.py` already scans `.cs`, so the generated file is covered by
the ASCII rule with no change to a frozen file.

The Python consumers reach the bridge through `core/bridge_client.py`, which
composes the URL from `core.ports.BRIDGE` and the host named by
`core.ports.GAME_HOST_ENV`, defaulting to `127.0.0.1`. No consumer writes a
URL literal.

### D3. The plugin SERVES; Python VALIDATES and WRITES

The plugin serves the prefab dump over HTTP. It never writes into
`C:\RedMoon\`. `tools/rmdata_ingest.py` pulls the dump, wraps rows in the
`core.tables` envelope, validates, and writes the table files.

Justification:

1. Single source of truth. `core/tables.py` is frozen and owns the envelope
   contract (`table`, `build`, `schema_version`, `rows`) and the schema
   documents under `data/schemas/`. Reimplementing that contract in C# creates a
   second definition that must be kept in sync by hand across every game patch.
   The port-literal problem in D2 is the same class of problem, and it is being
   solved the same way: one definition, mechanically propagated.
2. Minimum per-patch rebuild surface. ADR-002 accepts that the plugin is rebuilt
   every patch. Every line of logic in C# is a line that must be re-verified
   against a moving IL2CPP surface. Serialization of rows is unavoidable;
   validation, schema versioning and atomic file placement are not.
3. Blast radius. The plugin runs inside the game process. A validation bug that
   throws there can destabilize or crash the operator's session. The same bug in
   Python fails a script and exits non-zero.
4. Atomic writes. CLAUDE.md mandates temp-then-`os.replace` in the destination
   directory, and `tools/rmdata_extract.py` already implements exactly that in
   `write_json_atomic`. Reusing it is free; reimplementing it in C# is not.
5. The never-clobber rule already lives in Python, in
   `rmdata_extract.seed_tables`. Keeping the write path in Python keeps that
   rule enforceable in one place.

The plugin's responsibility is therefore: read the ECS world, project it to
plain rows, serialize, serve. Nothing else.

### D4. First ingest gets a nested-shape audit and a shape census

Recorded hazard: `core.tables.validate_table` is a SHALLOW gate. It type-checks
top-level row fields only. It confirms that `recipes.ingredients` is a list,
that `blood_types.bonuses` is a list, that `items.stats` is an object and that
`vbloods.resistances` is an object. It cannot see inside any of them. The
schemas themselves say this out loud: three of the five carry an
"UNVALIDATED NESTED SHAPE" note in their `description`. A passing
`validate_table` on the first real dump is NOT a shape guarantee.

Additional checks covering the nested shapes on first ingest:

1. `core/table_deep.py`, a NEW module (`core/tables.py` is frozen, so it is not
   extended). It exposes `deep_problems(name, table) -> list[str]` and asserts
   the documented nested contracts:
   - `recipes.ingredients`: a list of objects, each with an integer
     `prefab_guid` and an integer `amount`, and no undeclared keys.
   - `blood_types.bonuses`: a list of objects, each with a numeric quality
     threshold and a mapping of stat name to numeric value, ordered by ascending
     threshold.
   - `items.stats`: an object mapping string keys to numeric values, no nesting.
   - `vbloods.resistances`: an object mapping string keys to numeric values.
   - `vbloods.unlocks` and `abilities.effects`: lists of scalars of a single
     consistent type.
   Every rule is a documented claim from the shipped schema `description`
   fields, promoted from prose into an assertion.
2. A SHAPE CENSUS. The nested contracts above are documented intent, not
   observed fact; the first dump is a discovery event. Ingest therefore prints,
   for every nested container, the observed key set, the observed value types
   per key, cardinality, and the min and max of each numeric key. The operator
   reads the census once and either confirms the contract or amends
   `core/table_deep.py` and the schema `description` in the same commit.
3. QUARANTINE. Ingest never writes straight into the live table path. It writes
   to `data/rmdata/<build>/tables/_incoming/<name>.json`, runs `validate_table`,
   then `deep_problems`, then the census. Promotion to
   `data/rmdata/<build>/tables/<name>.json` happens only under an explicit
   `--accept` flag. This makes the first ingest a reviewed step rather than an
   automatic overwrite, and it protects the never-clobber property recorded in
   D6 below.

Note for the implementer: `tables/_incoming/` must be created and cleared by
ingest, and `seed_tables` deletes any file in `tables/` whose stem is not a
known table name (`rmdata_extract.py` lines 126 to 128). `_incoming` is a
DIRECTORY, and that loop only unlinks files (`path.is_file()`), so the two do
not collide. Confirm this with a test rather than by reading; see section 10.

### D5. Wiredness is proved live, with a negative control

Recorded hazard: a plugin passing its unit tests says nothing about whether it
is WIRED. Cycle 1 shipped a precommit gate whose hook matcher was a permission
specifier that never matches a tool name, so the gate never fired for an entire
cycle while its tests were green. A unit test proves the code is correct; it
does not prove the loader loaded it, that the bind happened, or that the numbers
came from the game rather than from a constructor default.

The cycle 2 wiredness proof is `tools/bridge_probe.py`, and it has four legs.
All four must be recorded, with their output, in the `docs/LEDGER.md` entry.

Per decision D1 the proof runs ONCE PER HOST. Legs 1 to 3 are run against the
client target and again against the dedicated-server target, each with the other
host closed so the arbitration in D1 cannot confuse which process answered. Leg 4
is run in whichever host the operator's character actually lives in; on the
dedicated-server target it is run with the operator connected to that server.
A host whose legs were not run is UNPROVEN, and D5's own rule applies: a leg that
is SKIPPED counts as FAILED.

1. NEGATIVE CONTROL. Run the probe with both hosts closed. It must exit non-zero
   with a clear "bridge unreachable" message. A probe that cannot fail proves
   nothing. This leg is what cycle 1 lacked.
2. LOADER PROOF. The host's own `BepInEx\LogOutput.log` contains the plugin
   banner line, with the plugin version, the detected host and the bound port,
   written at plugin initialization. Each host has its OWN log under its OWN
   install directory, so this leg is read from `<root>\BepInEx\LogOutput.log` for
   the client and `<root>\VRising_Server\BepInEx\LogOutput.log` for the server.
   This is independent of HTTP: it proves the loader loaded the assembly even if
   the listener failed to bind, and it is the ONLY leg that still reports
   something useful for a host that stood down from the port under D1.
3. IDENTITY PROOF. `/health` returns 200 with a `build` equal to the contents of
   `data/rmdata/current.txt`, a `host` equal to the target under test, and a
   `game_root` equal to that target's own directory - the pinned install root for
   the client, `<root>\VRising_Server` for the server. Critically, `build`,
   `host` and `game_root` are read at RUNTIME from the process, not compiled in
   as constants, so this leg simultaneously proves the plugin is in-process,
   proves WHICH host answered, and proves it is in a real target and not the
   `v3\` copy. A stale or hardcoded value cannot pass, because the probe compares
   against the repository's own pin and against `--expect-host`.
4. LIVENESS PROOF, the two-sample motion diff. The operator loads a character
   and moves it. The probe reads `/state` twice with the movement in between and
   asserts that position, or a vital, CHANGED between samples. A stub, a mock,
   a cached snapshot and a plugin that reads a default-constructed component all
   fail this leg. This is the assertion that a unit test structurally cannot
   make.

Free ambient signal, already present: `tools/rm_facts.py` is a SessionStart hook
that already probes 8777. It is frozen and needs no change. Once the bridge is
real, every session banner reports its state, so a bridge that silently stops
being wired surfaces at the next session start rather than at the next cycle.

### D6. The `/state` envelope, APPROVED 2026-07-26

`docs/API.md` already promises three endpoint shapes, and cycle 2 honours all
three. `/health` and `/dump/prefabs` are honoured exactly, with additive fields
only.

`/state` is CLARIFIED, and this is called out loudly because it touches a
promised contract. `docs/API.md` says "Live player and world state. Null when no
character is loaded." Read literally that means the response body is the JSON
literal `null`. Cycle 2 instead returns an envelope whose `state` MEMBER is
`null`:

```
{"ok": true, "build": "...", "plugin": "...", "captured_at": "...",
 "snapshot_age_s": 0.18, "state": null}
```

Justification: a bare `null` body makes "no character is loaded" and "the bridge
is broken and returned nothing useful" indistinguishable to the caller, and it
carries no build stamp, so a consumer cannot tell whether the state it just read
belongs to the pinned build or to a silently updated game. CLAUDE.md's error
handling rule requires a degraded-mode message rather than a bare failure, and a
bare `null` is a bare failure. The `null` semantics are preserved exactly, one
level down.

OPERATOR RULING, 2026-07-26: APPROVED. The envelope stands, carrying
`state: null` plus a build stamp. The literal-`null`-body alternative is
rejected and is not revisited.

Action taken: `docs/API.md` WAS AMENDED in the same pass that recorded this
ruling, ahead of the plugin, so the promised contract and the implemented
contract never disagree. The `/state` row in the bridge table now states the
envelope and the `state: null` semantics explicitly. No further API.md change is
owed for D6; the remaining API.md work is the additive `/health` and
`/dump/prefabs` fields, which land with the plugin.

### D7. Threading: a main-thread tick publishes an immutable snapshot

The HTTP listener runs on its own thread. Unity DOTS ECS structures are not safe
to read from an arbitrary thread while the simulation runs.

Decision: the plugin's ECS reads happen only on the game's main thread, on a
throttled tick (target 4 Hz, configurable). The tick projects the world into a
plain immutable snapshot object, serializes it to a JSON string once, and
publishes it by atomic reference swap. The listener thread never touches ECS; it
returns the currently published string. `snapshot_age_s` in every response tells
the consumer how stale the read is, which is also what makes leg 4 of D5
meaningful.

`/dump/prefabs` is the exception: it is a one-shot, expensive, operator-
triggered read. It is produced by scheduling work onto the main thread and
having the listener thread wait on completion with a timeout, returning HTTP 503
and a friendly error code on timeout rather than blocking the listener forever.

The exact mechanism for scheduling onto the main thread from a BepInEx plugin is
a spike, S2.

### D8. Build intermediates land outside the scanned tree

`tools/ascii_guard.py` is FROZEN, it scans `.cs`, and it must exit 0. A .NET
build writes generated `.cs` files under `obj/`, produced by NuGet and MSBuild,
whose content Red Moon does not control and which may contain non-ASCII. Those
files would be scanned and could break the hard ASCII gate through no fault of
authored content.

Decision: `bridge/Directory.Build.props` redirects `BaseIntermediateOutputPath`
and `BaseOutputPath` to `_scratch\bridge-build\`. `_scratch` is already in
`ascii_guard.EXCLUDED_DIRS` (line 29) and already in `.gitignore`, so no frozen
file is touched and no build artifact enters the repository or the ASCII scan.

`tests/test_ports.py::SKIPPED_DIR_PARTS` gains `_scratch` in the same change,
so the port scan does not walk build output either.

`.gitignore` gains `_scratch/bridge-build/` explicitly (redundant with the
existing `_scratch/` entry, but self-documenting) and `bridge/**/bin/` plus
`bridge/**/obj/` as belt and braces if a developer builds without the props
file. `.gitattributes` already marks `*.dll` binary.

### The v3 trap

The install contains a complete second copy of the game at
`<root>\v3\`, whose `VERSION` is `v1.0.10.4-r91333-b12`. It is NOT what Steam
launches. Installing BepInEx there produces a loader that never loads, a plugin
that never runs, and a debugging session chasing a bind failure that never
happened.

Every installer step therefore ASSERTS the target before writing a single byte.
Under decision D1 there are TWO target profiles, and `tools/install_bepinex.py`
takes `--target client|server` and applies the matching profile. It refuses to
proceed unless ALL of the assertions for the selected profile hold.

Shared by both profiles:

- `GameAssembly.dll` exists in the target directory, confirming the IL2CPP build.
- The resolved absolute target path does not have `v3` as its final component,
  and no path component anywhere in it is `v3`.
- The PINNED ROOT (the target for `client`, the target's parent for `server`)
  has a `VERSION` file containing the pinned string `v1.1.13.0-r99712-b17`, and
  `parse_build_id(VERSION)` equals the contents of `data/rmdata/current.txt`,
  reusing the parser already in `tools/rmdata_extract.py` rather than writing a
  second one.

`client` profile only:

- `VRising.exe` exists in the target directory.
- The target directory is the pinned install root itself.

`server` profile only:

- `VRisingServer.exe` exists in the target directory.
- The resolved target's final path component is `VRising_Server`, and its parent
  passes the pinned-root assertions above.
- PROBED 2026-07-26, resolved: `VRising_Server\` DOES carry its own `VERSION`
  file, reading `VRisingServer: v1.1.13.0-r99712-b17 (202605251709)`. Note the
  differences from the client's `VRising: v1.1.13.0-r99712-b17 (202605251526)` -
  the product prefix differs, and so does the trailing timestamp. The installer
  therefore asserts the server `VERSION` on the SEMANTIC build only, that is
  `1.1.13.0-r99712-b17`, and must NOT require byte equality with the client's
  line. It reports both lines it read.

The `v3\` directory is used as the installer's NEGATIVE CONTROL in the
acceptance criteria: pointing the installer at it under EITHER profile must
refuse, loudly, and change nothing. Pointing the `client` profile at
`VRising_Server\`, or the `server` profile at the root, must also refuse: a
profile/target mismatch is the second most likely way to install into the wrong
place now that there are two right places.

## 5. Repository layout added

```
bridge/
  README.md                      how to build, install and probe
  RedMoon.Bridge.sln
  Directory.Build.props          output and intermediate paths -> _scratch/
  global.json                    SDK pin, IF spike S4 says one is needed
  src/RedMoon.Bridge/
    RedMoon.Bridge.csproj        net6.0, BepInEx + Il2CppInterop references
    Plugin.cs                    BepInEx entry point, config, banner line
    HostDetect.cs                client-or-server detection (D1), blocked by S1
    HttpService.cs               loopback listener, routing, error envelopes,
                                 stand-down on a lost bind (D1)
    Snapshot.cs                  immutable snapshot type + atomic publish
    StateReader.cs               ECS -> snapshot projection (main thread)
    PrefabDumper.cs              prefab collection -> table rows
    Json.cs                      minimal serializer helpers
    Generated/
      RmPorts.g.cs               GENERATED by tools/gen_bridge_ports.py
core/
  bridge_client.py               URL composition from ports + RM_GAME_HOST
  table_deep.py                  nested-shape assertions (D4)
tools/
  gen_bridge_ports.py            core/ports.py -> RmPorts.g.cs
  install_bepinex.py             VERSION-asserting installer, --target
                                 client|server (D1, D8, v3 trap)
  bridge_probe.py                the four-leg wiredness proof, --expect-host (D5)
  rmdata_ingest.py               dump -> quarantine -> validate -> promote
tests/
  test_bridge_ports.py           port parity and drift
  test_bridge_project.py         layout, csproj TFM, no stray port literals
  test_bridge_client.py          URL composition, RM_GAME_HOST override
  test_table_deep.py             nested-shape assertions, positive and negative
  test_rmdata_ingest.py          envelope wrap, quarantine, promotion, refusal
  test_install_bepinex.py        refusal cases per target profile, including the
                                 v3 negative control and profile/target mismatch
docs/
  adr/ADR-004-bridge-hosts-client-and-server.md
```

ADR-004 is written and indexed as part of the approval pass, ahead of the
implementation, because it records a ruling rather than an implementation
outcome.

Modified existing files: `tests/test_ports.py` (allowlist plus `_scratch` skip),
`.gitignore`, `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`,
`docs/adr/README.md`, `ROADMAP.md`, `docs/LEDGER.md`.

No frozen file is modified. `core/ports.py`, `core/tables.py`,
`tools/ascii_guard.py`, `tools/precommit_gate.py`, `tools/text_first_guard.py`,
`tools/pytest_guard.py`, `tools/rm_facts.py` and `ops/register_tasks.py` are all
untouched by design; where a change would have been natural, the design routes
around it (D4 adds `core/table_deep.py`, D8 redirects into `_scratch`).

## 6. Endpoint contracts

Bind: `127.0.0.1` on the port from `RmPorts.Bridge`. Loopback only, enforced at
bind time rather than by inspecting the request, so no firewall prompt appears
and no non-loopback client can connect. All endpoints are GET and read-only.
Exactly one host serves these at a time, per the D1 arbitration; the host that
lost the bind serves nothing and says so in its log.

All payloads below are SHAPE illustrations. Numeric values are placeholders.
No PrefabGUID, component name or stat key in this document is a verified value
from the game; the real key sets are discovered by spikes S1 and S3 and by the
shape census in D4.

### GET /health

Honours `docs/API.md` exactly, plus additive fields.

```
200 OK
{
  "ok": true,
  "build": "1.1.13.0-r99712",
  "plugin": "0.1.0",
  "host": "client",
  "game_root": "C:\\Program Files (x86)\\Steam\\steamapps\\common\\VRising",
  "bound": "127.0.0.1",
  "worlds": ["<world name>", "<world name>"],
  "state_ready": true,
  "snapshot_age_s": 0.18,
  "uptime_s": 132.4
}
```

`build`, `host` and `game_root` are read at runtime, which is what makes leg 3 of
the wiredness proof meaningful. `host` is `client` or `server` and is the D1
disambiguator: it tells a consumer WHICH host answered when both are installed,
and `bridge_probe.py --expect-host` asserts on it. `game_root` is the answering
host's own directory, so on the server target it ends in `VRising_Server`.
`worlds` is the list of ECS worlds the plugin can see IN THAT HOST, and it
doubles as the output of spike S1 in production - the two hosts are expected to
report different world sets, and what those sets actually are is exactly what S1
must discover rather than what this document may assert.

### GET /state

See decision D6 for the flagged clarification of the null semantics.

No character loaded:

```
200 OK
{"ok": true, "build": "1.1.13.0-r99712", "plugin": "0.1.0",
 "captured_at": "2026-07-26T18:04:11Z", "snapshot_age_s": 0.21,
 "state": null}
```

Character loaded. The `state` field set is PROVISIONAL and depends on spike S3;
fields that turn out to be unreachable are omitted rather than faked, and the
omission is recorded in the ledger.

```
200 OK
{
  "ok": true,
  "build": "1.1.13.0-r99712",
  "plugin": "0.1.0",
  "captured_at": "2026-07-26T18:04:11Z",
  "snapshot_age_s": 0.09,
  "state": {
    "character": {"name": "<character name>", "level": 0, "gear_score": 0.0},
    "vitals": {"health": 0.0, "health_max": 0.0},
    "blood": {"type": "<blood type name>", "quality": 0.0, "amount": 0.0},
    "power": {"physical": 0.0, "spell": 0.0, "resource_yield": 0.0},
    "equipment": [
      {"slot": "chest", "prefab_guid": 0, "tier": 0, "gear_score": 0.0}
    ],
    "abilities": [
      {"slot": "spell_1", "prefab_guid": 0, "cooldown_remaining_s": 0.0}
    ],
    "position": {"x": 0.0, "y": 0.0, "z": 0.0},
    "world": {"day": 0, "time_of_day": 0.0, "blood_moon": false}
  }
}
```

`position` and `vitals` are the fields leg 4 of the wiredness proof samples
twice.

Which of these fields are reachable may DIFFER BETWEEN HOSTS under decision D1 -
a presentation world and a simulation world do not necessarily carry the same
components. The rule in the paragraph above governs: a field that is unreachable
in a given host is OMITTED, never faked, and the per-host omission set is
recorded in the ledger alongside the S1 and S3 findings.

### GET /dump/prefabs

Honours `docs/API.md`: full prefab table, PrefabGUID, localization key,
component stats. Additive optional query parameter `?table=<name>` narrows the
response to one table; omitting it returns the full dump, so the promised
behaviour is the default.

Rows use exactly the field names in `data/schemas/*.schema.json`. The plugin
emits ROWS ONLY. It does not emit the `core.tables` envelope; Python owns that
(decision D3).

```
200 OK
{
  "ok": true,
  "build": "1.1.13.0-r99712",
  "plugin": "0.1.0",
  "captured_at": "2026-07-26T18:07:52Z",
  "elapsed_ms": 0,
  "counts": {"items": 0, "abilities": 0, "vbloods": 0,
             "blood_types": 0, "recipes": 0},
  "tables": {
    "items": [
      {"prefab_guid": 0, "name": "<display name>",
       "localization_guid": "<guid>", "category": "chest", "tier": 0,
       "gear_score": 0.0, "stats": {"<stat key>": 0.0}, "weapon_type": ""}
    ],
    "abilities": [
      {"prefab_guid": 0, "name": "<display name>",
       "localization_guid": "<guid>", "school": "blood", "slot": "spell",
       "cooldown": 0.0, "power_scaling": 0.0, "damage_type": "spell",
       "effects": []}
    ],
    "vbloods": [
      {"prefab_guid": 0, "name": "<display name>",
       "localization_guid": "<guid>", "level": 0, "max_health": 0.0,
       "physical_power": 0.0, "spell_power": 0.0,
       "resistances": {"<resist key>": 0.0}, "blood_type": "<name>",
       "unlocks": [], "region": "<region>"}
    ],
    "blood_types": [
      {"prefab_guid": 0, "name": "<display name>",
       "localization_guid": "<guid>",
       "bonuses": [{"quality": 0.0, "stats": {"<stat key>": 0.0}}]}
    ],
    "recipes": [
      {"prefab_guid": 0, "output_guid": 0, "output_amount": 0,
       "ingredients": [{"prefab_guid": 0, "amount": 0}],
       "station_guid": 0, "craft_duration": 0.0}
    ]
  },
  "unmapped": [
    {"prefab_guid": 0, "reason": "no recognised stat component"}
  ]
}
```

`unmapped` is mandatory and non-optional in the design. A prefab the dumper
cannot classify must be REPORTED, never silently dropped. On the first dump the
size and content of `unmapped` is the single most informative signal about how
much of the game the dumper actually understands, and it is reviewed alongside
the shape census.

### Error envelope

Per the CLAUDE.md error-handling rule, no raw exception string reaches a
consumer. The raw error goes to the BepInEx log; the response carries a code and
a friendly message.

```
503 Service Unavailable
{"ok": false, "error": "world_not_ready",
 "message": "game world is not loaded yet, retrying"}
```

Codes: `world_not_ready`, `dump_timeout`, `not_found`, `internal`.

## 7. Table-fill data flow

```
V Rising HOST process, pinned build. Either:
  the client at the install root, or
  the dedicated server at <root>\VRising_Server\ (decision D1)
  RedMoon.Bridge  (same assembly in both; one of them owns 8777)
    main-thread tick  -> immutable snapshot -> atomic publish
    listener thread   -> serves the published snapshot
  |
  |  GET http://127.0.0.1:8777/dump/prefabs
  v
tools/rmdata_ingest.py
  1. read data/rmdata/current.txt              -> expected build
  2. compare with the dump's "build" field     -> REFUSE on mismatch
  3. wrap rows with core.tables.empty_table    -> envelope from the frozen module
  4. write data/rmdata/<build>/tables/_incoming/<name>.json   (atomic)
  5. core.tables.validate_table                -> SHALLOW gate, must be clean
  6. core.table_deep.deep_problems             -> NESTED gate, must be clean
  7. print the shape census                    -> operator reads it once
  8. --accept only:
     promote _incoming/<name>.json -> tables/<name>.json      (atomic)
```

Properties this preserves:

- The envelope, the schema version and the validation gate stay in Python, in
  the frozen `core/tables.py`, exactly once (D3).
- Nothing is written to a live table path until the operator accepts (D4).
- Every write is temp-then-replace, per the CLAUDE.md atomic-write rule, reusing
  the existing `write_json_atomic` helper.
- The build cross-check makes it impossible to ingest a dump from a
  silently-updated game into the previous build's directory.
- `tools/rmdata_extract.py` remains safe to re-run afterwards. Verified against
  source: `seed_tables` at lines 116 to 124 skips any table file that already
  exists, so a routine re-extract or an `RM-DataRefresh` firing will not replace
  a populated dump with an empty envelope.

## 8. Build and install procedure

Under decision D1 this procedure has TWO install targets. Steps 1 and 4 happen
once; steps 2, 3, 5 and 6 are run once per target.

Step 0, prerequisites. Obtain the BepInEx pack.

```
https://thunderstore.io/package/download/BepInEx/BepInExPack_V_Rising/1.733.2/
```

DOWNLOAD AUTHORIZATION, operator-granted 2026-07-26, scoped to the NEXT SESSION
ONLY. Claude may fetch exactly that URL and extract the archive. Conditions:

- The grant covers that ONE URL and ONE session. It does not generalize to any
  other file, any other version of the pack, any mirror, or any later session.
  A later session re-asks.
- The VERSION assert on the target folder runs BEFORE any write, per the v3-trap
  section and the per-profile assertions in it. Extraction into a game directory
  that has not passed its profile's assertions is forbidden, not merely
  discouraged.
- The extraction destination for the first hop is `_scratch\`, which is
  gitignored and excluded from the ASCII guard. Nothing from the pack enters the
  repository.
- Outside that grant the standing rule is unchanged: the operator downloads
  files and performs any elevated action; Claude does not.

Step 1, generate the port constant.

```
python C:\RedMoon\tools\gen_bridge_ports.py
python -m pytest C:\RedMoon\tests\test_bridge_ports.py
```

Step 2, install the loader, ONCE PER TARGET. Dry run FIRST, mirroring the
`ops/register_tasks.py --show` pattern already established in
`docs/OPERATIONS.md`.

```
python C:\RedMoon\tools\install_bepinex.py --pack <zip> --target client --show
python C:\RedMoon\tools\install_bepinex.py --pack <zip> --target client --install
python C:\RedMoon\tools\install_bepinex.py --pack <zip> --target server --show
python C:\RedMoon\tools\install_bepinex.py --pack <zip> --target server --install
```

`--show` prints the resolved target, the selected profile, the `VERSION` string
it read and from which directory, and every file it would write, and changes
nothing. `--install` re-runs every assertion for that profile and aborts on any
failure. The pack payload lands in the target directory: `BepInEx/`, `dotnet/`,
`.doorstop_version`, `doorstop_config.ini`, `winhttp.dll` - in the game ROOT for
the client target, and in `<root>\VRising_Server\` for the server target. The
two installs are independent trees; neither shares a `BepInEx\` with the other.

Step 3, first launch of EACH host after installing its loader. Launch the client
once, and start the dedicated server once, and for each confirm that its own
`BepInEx\LogOutput.log` exists and that its own `BepInEx\interop\` has been
populated with the generated Il2CppInterop assemblies. Those assemblies are the
plugin's compile-time references and do not exist until that loader has run once.
This ordering is mandatory: the plugin cannot be built before this step.

FLAGGED, unverified: whether the client's and the server's `interop\` trees
produce the SAME assembly set is not known. If they diverge, a single assembly
targeting both hosts must compile against the INTERSECTION of the two, and any
host-specific type is reached behind the host detection of D1. Which of the two
is the case is an output of spike S1, and no reference set may be pinned in the
`.csproj` before that is known.

Step 4, build the plugin.

```
dotnet build C:\RedMoon\bridge\RedMoon.Bridge.sln -c Release
```

Output lands under `_scratch\bridge-build\` per decision D8.

Step 5, deploy the same DLL into BOTH targets.

```
<root>\BepInEx\plugins\RedMoon.Bridge\RedMoon.Bridge.dll
<root>\VRising_Server\BepInEx\plugins\RedMoon.Bridge\RedMoon.Bridge.dll
```

Step 6, launch and prove, ONCE PER HOST, with the other host CLOSED so the D1
arbitration cannot make it ambiguous which process answered.

```
python C:\RedMoon\tools\bridge_probe.py --expect-unreachable        (both closed)

  client host running, server closed:
python C:\RedMoon\tools\bridge_probe.py --health --expect-host client
python C:\RedMoon\tools\bridge_probe.py --state  --expect-host client
python C:\RedMoon\tools\bridge_probe.py --motion-diff

  server host running, client closed:
python C:\RedMoon\tools\bridge_probe.py --health --expect-host server
python C:\RedMoon\tools\bridge_probe.py --state  --expect-host server
python C:\RedMoon\tools\bridge_probe.py --motion-diff   (operator connected)
```

Step 6b, prove the arbitration. Start the dedicated server, then start the
client. `--health --expect-host server` must succeed, and the CLIENT's
`BepInEx\LogOutput.log` must carry the stand-down line from D1 clause 2. This is
the negative control for the port-collision path: without it, a client that
crashed on the failed bind and a client that stood down cleanly look identical
from the outside.

Step 7, dump and ingest. Run against the host that spike S1 and S3 show actually
carries the prefab collection; record WHICH host produced the accepted dump in
the ledger, since a dump is now provenance-bearing in a way it was not under the
client-only design.

```
python C:\RedMoon\tools\rmdata_ingest.py            (quarantine + census)
python C:\RedMoon\tools\rmdata_ingest.py --accept   (promote)
```

Step 8, re-extraction safety check.

```
python C:\RedMoon\tools\rmdata_extract.py
git status --short data/rmdata/
```

The populated tables must be unchanged.

## 9. Spikes: what is NOT known

Everything in this section is UNVERIFIED. No type name, namespace, method
signature or component name below has been confirmed against build
`1.1.13.0-r99712` in this session. Nothing here may be treated as fact, and no
code may be scaffolded against it before the spike runs. This section exists
precisely because CLAUDE.md forbids scaffolding against an assumed API surface.

The verified facts are only these: the build is IL2CPP (`GameAssembly.dll` is
present at the root), the loader is BepInExPack V Rising 1.733.2 wrapping
BepInEx 6.0.0 `be.733` on CoreCLR .NET 6 with Il2CppInterop, and V Rising is a
Unity DOTS ECS game whose item and ability data lives in ECS blobs (ADR-002).

**S1. Reaching the ECS world IN EACH HOST, and detecting which host.** Restated
2026-07-26 for the D1 ruling. It no longer confirms a client-only assumption; it
confirms world access in BOTH hosts. Four questions: (a) how a BepInEx plugin
obtains a handle to the running ECS world; (b) what the worlds are called in the
CLIENT process; (c) what the worlds are called in the DEDICATED SERVER process,
which is a separate enumeration and not an inference from (b); (d) by what
mechanism the plugin determines at load which host it is in, since D1 requires a
`host` value of `client` or `server` in `/health` and requires host-dependent
world selection. Method: after step 3 of the install procedure, enumerate the
loaded worlds from the plugin and log their names, separately in each host;
enumerate the generated assemblies under each host's own `BepInEx\interop\`, list
their namespaces, and DIFF the two sets. Output: the concrete world-acquisition
code path, the host-detection mechanism, the per-host `worlds` array that
`/health` reports, and whether the two interop assembly sets agree. BLOCKS:
`StateReader.cs`, `PrefabDumper.cs`, `HostDetect.cs`, the `.csproj` reference
set, and which host step 7's dump is taken from.

The question the old S1 asked - whether a server simulation world exists inside
the client process when playing solo - is still worth answering and is still in
scope here, but it is no longer load-bearing: under D1 a NO answer costs a
feature in the client target rather than invalidating the design.

**S2. Scheduling work onto the game's main thread.** Decision D7 requires ECS
reads to happen on the main thread while the HTTP listener runs on its own
thread. The mechanism is not known: candidates include a BepInEx plugin
`Update`-style callback, a Harmony patch on a system's update method, or an
Il2CppInterop-provided hook. Which of these exists and is stable on
BepInEx 6 `be.733` must be determined empirically. BLOCKS: `Plugin.cs`,
`HttpService.cs` and the whole snapshot model.

**S3. Which component types carry item stats.** The prefab entity for an item
carries its stats in one or more ECS component types whose names are not known.
The same applies to ability cooldowns and scaling, V Blood stat lines and
resistances, blood type bonus tiers, and recipe ingredient lists. Method:
enumerate the component types present on a small sample of known prefab
entities, log the type names and field layouts, and map them onto the five
schemas by inspection. Output: the field-by-field mapping table that
`PrefabDumper.cs` implements, plus a confirmed or corrected `/state` field set
for section 6. BLOCKS: `PrefabDumper.cs`, the provisional `/state` field set,
and the D4 nested contracts.

**S3a. The prefab collection type.** `ROADMAP.md` and the cycle 1 spec both
refer to `PrefabCollectionSystem`. That name comes from prior project notes and
was NOT verified against this build's interop assemblies in this session. The
real type name, namespace and the shape of its GUID-to-entity mapping are
outputs of S3, not inputs. If the name turns out to be different, the roadmap
and the cycle 1 spec are corrected rather than the finding.

**S4. Building net6.0 with a .NET 10 SDK.** `dotnet --list-sdks` reports only
`10.0.301`. The plugin must target `net6.0` to match the loader's CoreCLR
runtime. A modern SDK can generally build an older target framework given the
targeting pack, but the .NET 6 targeting pack is not confirmed present on this
machine, and .NET 6 is out of support, so a `NETSDK1045`-class error or a
missing-targeting-pack error is plausible. This is stated as a BUILD-TIME RISK
to resolve during implementation, not as a working configuration. Resolution
order: (1) attempt the build as-is; (2) if it fails, install the .NET 6
targeting pack; (3) if a `global.json` SDK pin is required, add one at
`bridge/global.json` and record why. Do not assume any of these is unnecessary
until the build has actually succeeded. BLOCKS: everything downstream of step 4.

**S5. HTTP listener viability in-process.** Whether a .NET `HttpListener`, or a
raw socket listener, binds and serves reliably from inside the IL2CPP host
process under BepInEx 6 CoreCLR, and whether it shuts down cleanly on game exit
without leaving the port bound. A leaked bind means the next launch fails to
serve and the failure looks like a plugin bug. Output: the listener
implementation choice and the shutdown path.

**S6. Dump cost.** The number of prefabs is unknown, and a full dump may be
large enough to stall the main thread visibly or exceed a naive client timeout.
Output: the observed `elapsed_ms` and payload size, feeding the chunking
decision. If the dump stalls the frame budget unacceptably, it is split across
several ticks; that is an implementation detail behind the same endpoint and
does not change the contract.

## 10. Test plan, by tier per CLAUDE.md R5

R5 defines tiers 0 to 2. Cycle 2 does not add a tier. It adds a LIVE GATE that
sits on top of tier 2 for the specific changes that can only be proved against
the running game.

### Tier 0, cosmetic

Doc, comment and string edits: `docs/API.md`, `docs/ARCHITECTURE.md`,
`docs/OPERATIONS.md`, ADR-004, `ROADMAP.md`, `docs/LEDGER.md`, `bridge/README.md`.

```
python C:\RedMoon\tools\ascii_guard.py
```

Plus `py_compile` if a Python file was touched. Note that `.cs` files are in
`ascii_guard.AUTHORED_SUFFIXES`, so a comment edit in the plugin is a tier 0
change that still pays the ASCII scan.

### Tier 1, local logic in one module

Python, `py_compile` plus that module's tests only.

- `tests/test_bridge_ports.py` - regeneration is byte-identical; the parsed
  constant equals `core.ports.BRIDGE`; the scan is non-vacuous.
- `tests/test_bridge_client.py` - URL composition; `RM_GAME_HOST` override is
  honoured; the default is `127.0.0.1`; no URL literal in the module.
- `tests/test_table_deep.py` - one PASSING and one FAILING fixture per nested
  contract. The failing fixtures are the point: a validator with no negative
  test is the same class of dead gate as the cycle 1 precommit hook. Specific
  negatives: an ingredient missing `amount`; an ingredient whose `amount` is a
  string; an `items.stats` value that is a string; an `items.stats` value that
  is a nested object; a `blood_types.bonuses` list out of threshold order; a
  boolean where a number is expected (mirroring the bool-is-not-a-number guard
  already in `core/tables.py` line 88).
- `tests/test_rmdata_ingest.py` - rows are wrapped in the `core.tables`
  envelope; a build mismatch against `current.txt` is REFUSED; quarantine files
  land under `_incoming/` and never in the live path without `--accept`;
  promotion is atomic; a dump that fails the shallow gate is not promoted; a
  dump that passes the shallow gate but fails the deep gate is not promoted
  (this is the test that encodes hazard D4); and `rmdata_extract.seed_tables`
  leaves both a populated table and the `_incoming` directory alone.
- `tests/test_install_bepinex.py` - refusal on a wrong `VERSION` string; refusal
  on a path whose final component is `v3`; refusal when `GameAssembly.dll` is
  absent; refusal when the parsed build disagrees with `current.txt`; and
  `--show` writes nothing. Per the D1 ruling, also: each profile's own executable
  assertion (`VRising.exe` for `client`, `VRisingServer.exe` for `server`);
  refusal when `--target client` is pointed at a `VRising_Server`-shaped fixture
  and when `--target server` is pointed at a root-shaped one; and the
  `server` profile reading the PARENT directory's `VERSION`. Driven against
  temporary fixture directories, never against the real install.
- `tests/test_bridge_project.py` - the expected files exist under `bridge/`,
  including `HostDetect.cs`; the `.csproj` targets `net6.0`;
  `Directory.Build.props` redirects output into `_scratch`; no `.cs` file other
  than the generated one contains a Red Moon port literal.

C# unit tests: DEFERRED for cycle 2. SETTLED by operator ruling 2026-07-26; this
is not an open question and is not re-raised during implementation. It is a
deliberate choice rather than an oversight. Almost every line of the plugin
either touches
Il2CppInterop or is a data projection whose correctness depends on the S3
mapping, and neither can be meaningfully unit tested without the game. The
pure-function surface that could be tested (the JSON writer, the snapshot buffer
swap) is small and is exercised end to end by the live gate. The single stated
condition for revisiting: if S3 turns out to produce a substantial pure mapping
layer, a `RedMoon.Bridge.Tests` project targeting the same TFM is added and the
revisit is recorded in `docs/LEDGER.md`. Nothing else reopens it.

Worth naming honestly: the D1 ruling makes host detection a new piece of C#
logic that is NOT covered by this deferral's justification, because it is not
obviously an Il2CppInterop call or an S3-dependent projection. Whether it is
pure enough to unit test is unknown until S1 says what the mechanism is. If it
turns out to be a pure function over something like a process or assembly name,
it is the most likely first inhabitant of the deferred test project.

### Tier 2, schema, engine, scorer or ENGINE_VERSION

Any change to `data/schemas/*.json`, `core/table_deep.py`, the ingest path, or
the endpoint contracts:

```
python C:\RedMoon\tools\gen_bridge_ports.py
python -m pytest
python -m ruff check .
python C:\RedMoon\tools\ascii_guard.py
dotnet build C:\RedMoon\bridge\RedMoon.Bridge.sln -c Release
```

Plus redeploy of the DLL and a game restart, which is the cycle 2 equivalent of
R5's "service restart".

### The live gate

Required for any change to `Plugin.cs`, `HostDetect.cs`, `HttpService.cs`,
`StateReader.cs`, `PrefabDumper.cs`, or the endpoint contracts. Tier 2 first,
then the legs of decision D5, RUN ONCE PER HOST per the D1 ruling, with output
recorded in `docs/LEDGER.md`:

1. Probe with both hosts closed exits non-zero.
2. That host's own `BepInEx\LogOutput.log` carries the plugin banner.
3. `/health` build, host and game_root match the repository pin, the expected
   host and that host's own directory.
4. The two-sample motion diff shows a changed value.
5. The arbitration control: server started first, client second, `--expect-host
   server` succeeds and the client logged its stand-down.

A live gate leg that is SKIPPED counts as FAILED, and that now includes a whole
HOST that was not exercised. A skipped test and a hook that never fires are the
same failure mode, and cycle 1 already paid for that lesson once. The D1 ruling
doubles the number of places this lesson can be re-learned, which is the honest
price of covering both hosts.

## 11. Risk register

| ID | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | BepInEx installed into `v3\`, or into the wrong one of the two D1 targets | Total: loader never loads, plugin never runs, and the symptom looks like a bind failure | `install_bepinex.py` takes `--target client\|server` and asserts that profile: `GameAssembly.dll`, the profile's own executable, a non-`v3` path, and the pinned root's VERSION; `v3\` and a profile/target mismatch are both acceptance negative controls; `/health` reports `host` and `game_root` at runtime |
| R2 | Only a .NET 10 SDK is present; the plugin targets net6.0 | Blocks the build entirely | Spike S4. Resolution order is attempt, then targeting pack, then `global.json`. Not assumed to work |
| R3 | IL2CPP type and component names are unknown | The dumper and state reader cannot be written | Spikes S1, S3, S3a. No code is scaffolded against an assumed surface (CLAUDE.md Testing Discipline). `PrefabCollectionSystem` is treated as an unverified label |
| R4 | Reading ECS from the listener thread | Crashes or corrupts the operator's game session | Decision D7: main-thread tick, immutable snapshot, atomic publish. The listener never touches ECS |
| R5 | Shallow validation passes on a malformed first dump | Bloodforge is built on silently wrong nested data in cycle 3, and the error surfaces as bad combat math much later | Decision D4: `core/table_deep.py`, the shape census, and the quarantine-then-accept flow. Negative tests are mandatory |
| R6 | The plugin passes its tests but is not wired | An entire cycle of false confidence, exactly as with the cycle 1 precommit gate | Decision D5: four-leg live proof with a negative control and a two-sample motion diff that a stub cannot pass |
| R7 | A port literal drifts between Python and C# | Silent connection failure that looks like a dead plugin | Decision D2: generation plus a byte-identity drift test plus a direct equality assertion; the existing `tests/test_ports.py` scan already covers `.cs` |
| R8 | Build output breaks the frozen ASCII guard | `tools/ascii_guard.py` cannot exit 0, blocking every commit | Decision D8: intermediates and output redirected into `_scratch`, which is already excluded by the frozen guard |
| R9 | Steam updates the game | The plugin stops loading; `data/rmdata/<build>/` is invalidated | Accepted standing cost per ADR-002. `/health` compares the runtime build against `current.txt`, so the mismatch is reported rather than silently tolerated. `RM-DataRefresh` already handles the data side |
| R10 | The dump stalls the main thread or times out | A visible hitch, or a failed dump | Spike S6, `elapsed_ms` in the payload, `dump_timeout` error code, chunking across ticks if needed |
| R11 | The listener leaks its bind on game exit | The next launch cannot serve, and the symptom mimics a plugin bug | Spike S5; explicit shutdown path on plugin unload; `bridge_probe.py --expect-unreachable` detects a stale bind after exit |
| R12 | Anti-cheat interaction | Unknown; potentially an account risk if used online | ADR-002 already scopes Red Moon to solo and private-host play. Cycle 2 does not change that scope. NOT verified in this session and NOT assumed safe for official servers |
| R13 | The dumper silently drops prefabs it cannot classify | Tables look complete but are missing whole categories | The `unmapped` array is mandatory in the `/dump/prefabs` payload and is reviewed alongside the census |
| R14 | Ingest overwrites a good dump with a bad one | Loss of hard-won first-party data | Quarantine plus explicit `--accept`; `rmdata_extract.seed_tables` never clobbers (verified, lines 116 to 124); `data/rmdata/` is gitignored, so a bad promotion is not recoverable from git and the quarantine step is the only safety net |
| R15 | Both hosts run at once and contend for 8777 (new, from the D1 ruling) | Two listeners cannot both bind; worse, a consumer silently reads the wrong host's world while believing it read the right one | Decision D1 arbitration: one bind attempt, the loser stands down loudly and serves nothing, mandated server-first start order, `host` in `/health`, `bridge_probe.py --expect-host`, and install step 6b as the explicit negative control |
| R16 | Two install targets doubles the per-patch VERIFICATION surface (new, from the D1 ruling) | A host that is not re-proved after a patch is silently unwired for a whole cycle: failure mode R6 with a second place to hide | Accepted cost, recorded in ADR-004. D5 runs once per host and a skipped leg counts as FAILED; acceptance criteria 4 and 5 are per-host and both hosts' output goes into the ledger |
| R17 | The client and server `interop\` assembly sets diverge (new, from the D1 ruling) | One assembly cannot reference a type present in only one host: either the build breaks or the plugin throws at load in the other host | Spike S1 diffs the two `interop\` trees before any reference is pinned; the `.csproj` compiles against the intersection and any host-specific type is reached behind the D1 host detection |

## 12. Assumptions

Stated explicitly before coding, per CLAUDE.md.

1. The plugin targets BOTH hosts (decision D1, ADR-004): one assembly loads in
   the client at the install root and in the dedicated server under
   `VRising_Server\`. Assumed and NOT yet verified: that BepInEx installs and
   loads in the dedicated-server folder the same way it does in the root, that a
   host-detection mechanism exists, and that the two hosts' interop assembly sets
   are compatible enough for one assembly. All three are spike S1, confirmed
   before any dependent code is written. NOT assumed any more, and downgraded to
   a question S1 also answers: whether a solo client contains a server simulation
   world. The design no longer depends on the answer.
2. Build `1.1.13.0-r99712` is the pin for all of cycle 2. A Steam update during
   the cycle invalidates the plugin build and the data directory, and the cycle
   pauses for a rebuild rather than continuing against a mixed state.
3. The operator performs any elevated action. Claude does not download files,
   with ONE narrow exception: the next-session-only, single-URL BepInEx pack
   grant recorded in section 8, step 0. That grant expires with that session.
4. The five DLC packs are cosmetic and do not alter combat math. Carried forward
   unchanged from the cycle 1 spec. The dump includes their prefabs regardless,
   so a wrong assumption costs nothing.
5. Loopback binding is a sufficient security boundary for cycle 2. No auth, no
   TLS, no non-loopback listener, no write endpoints.
6. `RM_GAME_HOST` remains the single knob for where a Python consumer looks for
   the bridge, defaulting to `127.0.0.1`, so moving the game to another box
   stays a config change.
7. Nested-shape contracts in `core/table_deep.py` are derived from the shipped
   schema `description` text, which is documented INTENT. The first shape census
   is authoritative over the intent, and a disagreement amends the schema and the
   validator together in one commit.

## 13. Acceptance criteria for cycle 2 being done

1. `python C:\RedMoon\tools\gen_bridge_ports.py` is idempotent, and
   `python -m pytest` is green including `tests/test_bridge_ports.py`.
   `python -m ruff check .` is clean. `python C:\RedMoon\tools\ascii_guard.py`
   exits 0 with the C# project present in the tree.
2. `python C:\RedMoon\tools\install_bepinex.py --show` pointed at
   `<root>\v3` REFUSES under BOTH `--target client` and `--target server`, names
   the reason, and writes nothing. `--target client` pointed at
   `<root>\VRising_Server` and `--target server` pointed at the root also REFUSE.
   Every refusal's output is recorded in the ledger. These are the R1 negative
   controls.
3. `dotnet build C:\RedMoon\bridge\RedMoon.Bridge.sln -c Release` succeeds, and
   the resolution of spike S4 (targeting pack, `global.json`, or neither) is
   recorded as fact rather than assumption.
4. The SAME DLL is deployed into BOTH targets - `<root>\BepInEx\plugins\...` and
   `<root>\VRising_Server\BepInEx\plugins\...` - each host launches normally, and
   EACH host's own `LogOutput.log` contains the plugin banner line with the
   plugin version, the detected host and the bound port. Neither host crashes,
   hangs or regresses in startup time with the plugin present. A host that was
   not launched is not done.
5. The four-leg live wiredness proof passes ONCE PER HOST, with the other host
   closed, and every leg's output for BOTH hosts is pasted into the
   `docs/LEDGER.md` entry:
   a. probe with both hosts closed exits non-zero with "bridge unreachable";
   b. `/health` returns 200 with `build` equal to `data/rmdata/current.txt`,
      `host` equal to `--expect-host`, and `game_root` equal to that host's own
      directory - the pinned root for the client and `...\VRising_Server` for the
      server, and never `...\v3`;
   c. `/state` returns `state: null` with no character loaded, and non-null with
      a character loaded;
   d. the two-sample motion diff shows a changed position or vital.
5b. The D1 arbitration is proved live, per install step 6b: with the dedicated
   server started first and the client started second, `--health
   --expect-host server` succeeds and the CLIENT's `LogOutput.log` carries the
   stand-down line. The client must not crash, and must not be listening on any
   port. This is the R15 negative control and it is a leg like any other: skipped
   counts as failed.
6. `/dump/prefabs` returns 200 with non-zero `counts` for all five tables, the
   `unmapped` array is recorded in the ledger with its size and a sample, and the
   ledger records WHICH host produced the dump and why that host was chosen.
   If both hosts can dump, the counts from each are compared and any difference
   is explained rather than averaged over.
7. Ingest completes the full path: quarantine written, `validate_table` clean,
   `deep_problems` clean, shape census reviewed by the operator and pasted into
   the ledger, `--accept` promotes. Every promoted table file has `rows` longer
   than zero and a `build` matching the pin.
8. `python C:\RedMoon\tools\rmdata_extract.py` is re-run after promotion and
   `git status --short data/rmdata/` shows the populated tables unchanged. This
   proves the never-clobber property against REAL rows rather than against the
   empty envelopes it was tested with in cycle 1.
9. Spikes S1 through S6 are all closed, with their findings written down.
   S1 is closed only when it reports BOTH hosts' world sets, the host-detection
   mechanism, and the interop-set diff. Any invented or unverified type name from
   the roadmap or the cycle 1 spec, including `PrefabCollectionSystem`, is either
   confirmed or corrected in place.
10. ADR-004 is committed and listed in `docs/adr/README.md` (done in the approval
    pass, ahead of implementation). `docs/API.md` carries the D6 envelope (done
    in the approval pass) and gains the additive fields including `host`.
    `ARCHITECTURE.md` marks `bridge/` as shipped and names both install targets.
    `OPERATIONS.md` documents the build, the two installs, the per-host probe,
    the server-first start order and the ingest commands. `ROADMAP.md` marks
    cycle 2 DONE and cycle 3 CURRENT. `docs/LEDGER.md` entry 002 is appended.

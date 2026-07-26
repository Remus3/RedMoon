# Red Moon Operations

## Verify the repository

```
python -m pytest
python tools/ascii_guard.py
```

Exit code 0 from the guard means every authored file is 7-bit ASCII.

## Refresh extracted game data

```
python tools/rmdata_extract.py
```

Idempotent. Writes `data/rmdata/<build>/` and updates `data/rmdata/current.txt`.
Re-running against an unchanged install produces byte-identical output.

Run it after any Steam update. The build string comes from the install's
`VERSION` file, so a game update lands in a new directory and leaves the old one
intact.

## RedMoon.Bridge, build and install

One plugin assembly, TWO install targets (ADR-004). Each host binds its own
port, chosen from the host it detects at load (ADR-005), so both can run at
once and the start order does not matter.

| Host | Install directory | Port |
|---|---|---|
| Client | the game root, where `VRising.exe` lives | 8777 |
| Dedicated server | `<root>\VRising_Server\` | 8780 |

There is a stale second copy of the whole game at `<root>\v3\`, build
`v1.0.10.4-r91333-b12`. It is NOT what Steam launches and must never receive
BepInEx. Installing there produces a loader that never loads and a debugging
session chasing a bind failure that never happened. Every installer step asserts
its target before writing a byte, and pointing it at `v3\` refuses under either
profile.

Generate the C# port constants from the Python registry. Never hand-write them:

```
python tools/gen_bridge_ports.py
```

`--check` exits non-zero if the generated file has drifted from `core/ports.py`.

Install the loader, once per target. Dry run FIRST - `--show` prints the resolved
target, the profile, every `VERSION` string it read and from where, and every
file it would write, and changes nothing:

```
python tools/install_bepinex.py --pack <zip> --target client --show
python tools/install_bepinex.py --pack <zip> --target client --install
python tools/install_bepinex.py --pack <zip> --target server --show
python tools/install_bepinex.py --pack <zip> --target server --install
```

Then launch EACH host once before building the plugin. That first launch is what
populates `BepInEx\interop\` with the generated Il2CppInterop assemblies, and
those assemblies are the plugin's compile-time references. Building before this
step cannot work.

```
dotnet build bridge\RedMoon.Bridge.sln -c Release
```

Build output lands under `_scratch\bridge-build\`, outside the ASCII-scanned
tree. Deploy the SAME DLL into both targets:

```
<root>\BepInEx\plugins\RedMoon.Bridge\RedMoon.Bridge.dll
<root>\VRising_Server\BepInEx\plugins\RedMoon.Bridge\RedMoon.Bridge.dll
```

## Prove the bridge is wired

A passing test suite says nothing about whether the plugin is LOADED. Cycle 1
shipped a hook whose matcher never matched, so it never fired for a whole cycle
while its unit tests stayed green. These legs are the proof, and they run once
per host. A leg that is skipped counts as failed.

```
python tools/bridge_probe.py --expect-unreachable            (game closed)
python tools/bridge_probe.py --loader-log  --expect-host client
python tools/bridge_probe.py --health      --expect-host client
python tools/bridge_probe.py --state       --expect-host client
python tools/bridge_probe.py --motion-diff --expect-host client
```

Repeat with `--expect-host server` against the dedicated server. Under ADR-005
`--expect-host` also selects which port is probed, so the two hosts no longer
have to be closed for each other's run.

## Ingest the prefab dump

The plugin serves rows. Python validates and writes them (decision D3). Nothing
reaches a live table path until the operator accepts it:

```
python tools/rmdata_ingest.py            quarantine, validate, print the census
python tools/rmdata_ingest.py --accept   promote into data/rmdata/<build>/tables/
```

Read the shape census before accepting. `core.tables.validate_table` is a
SHALLOW gate - it cannot see inside `recipes.ingredients`, `blood_types.bonuses`
or `items.stats` - so a clean validate is not a shape guarantee. The census is
what turns the first dump into a reviewed discovery rather than an automatic
overwrite.

Afterwards, confirm re-extraction still cannot clobber the real rows:

```
python tools/rmdata_extract.py
git status --short data/rmdata/
```

## Scheduled tasks

All Red Moon tasks are named `RM-*`. The namespace is exclusive to this project.

| Task | Trigger | Action |
|---|---|---|
| `RM-DataRefresh` | Daily | Runs `tools/rmdata_extract.py`. No-op unless the build changed. |

Run the dry run first. `--show` prints the exact `schtasks` command line each
task would be created with and changes nothing, so the quoting of the Python
path and the script path can be checked before a privileged call is made:

```
python ops/register_tasks.py --show
```

Then register or remove them. Both need an elevated shell:

```
python ops/register_tasks.py --install
python ops/register_tasks.py --remove
```

Inspect a registered task:

```
schtasks /query /tn RM-DataRefresh /v /fo LIST
```

## Restore the memory namespace

The Red Moon memory namespace lives outside the repository at
`C:\Users\Administrator\.claude\projects\C--RedMoon\memory\` and is not
committed there. `docs/memory_seed/` holds a byte-for-byte copy. If the
namespace is lost, recreate the directory and copy the seed into it:

```
python -c "import pathlib,shutil; d=pathlib.Path.home()/'.claude/projects/C--RedMoon/memory'; d.mkdir(parents=True,exist_ok=True); [shutil.copyfile(p,d/p.name) for p in pathlib.Path('docs/memory_seed').glob('*.md')]"
```

`tests/test_claude_config.py` asserts the live files and the seed agree, so
editing a memory entry means updating its seed in the same commit.

## Process rules

- Never `Stop-Process`. Use `taskkill /F /PID <pid>`.
- Always `py_compile` before restarting a service. Under `pythonw.exe` a syntax
  error is silent.
- Use `pythonw.exe` for background work so no console window flashes.

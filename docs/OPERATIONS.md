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

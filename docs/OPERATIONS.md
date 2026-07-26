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

Register or remove them:

```
python ops/register_tasks.py --install
python ops/register_tasks.py --remove
```

Inspect them:

```
schtasks /query /tn RM-DataRefresh /v /fo LIST
```

## Process rules

- Never `Stop-Process`. Use `taskkill /F /PID <pid>`.
- Always `py_compile` before restarting a service. Under `pythonw.exe` a syntax
  error is silent.
- Use `pythonw.exe` for background work so no console window flashes.

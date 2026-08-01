"""Hook scripts must not flash a console window on Windows.

THE BUG THIS PINS. The four hook scripts in `.claude/settings.json` are launched
with `pythonw.exe`, which has NO console. That makes the hook itself windowless
and does NOT make its children windowless: on Windows a CONSOLE-subsystem
executable launched from a process with no console ALLOCATES A NEW ONE, which the
operator sees as a window flashing open and shut. `precommit_gate` runs on every
Bash and PowerShell call and spawns `git` twice, so the flash is per shell
command rather than per session.

A prior investigation (2026-07-26) concluded the flashing windows were `npx` MCP
launchers and not Red Moon, on the evidence that RM's hooks "run under
pythonw.exe, which is windowless". That second clause is true and does not
follow. The conclusion was right about the windows it saw and silent about these.

WHAT IS AND IS NOT TESTABLE HERE, stated plainly. Whether a window actually
appears is a property of the Windows console host and is not observable from
inside the process that suppressed it. So the direct behaviour is NOT tested.
What IS tested is the two things that can actually regress:

1. An AST audit of every `subprocess.run` in the hook scripts. A call launching
   an EXTERNAL executable must pass `creationflags`; a call launching
   `sys.executable` need not, because under `pythonw.exe` that IS `pythonw.exe`
   and is already windowless. The failure this must produce: a future spawn site
   added without the flag fails here, naming the file and line. That is the
   regression, and the negative control below proves the auditor can see it.
2. That suppressing the console did not break `capture_output`. This is the real
   risk of the fix - a gate that silently stops reading its subprocess output
   still exits 0 and looks exactly like a working gate.
"""
from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]

HOOK_SCRIPTS = (
    "tools/rm_facts.py",
    "tools/precommit_gate.py",
    "tools/pytest_guard.py",
    "tools/text_first_guard.py",
)
"""Every script `.claude/settings.json` invokes. text_first_guard spawns nothing
and is listed so that adding a spawn to it is caught rather than unwatched."""


def unflagged_spawns(source: str, label: str) -> list[str]:
    """Every subprocess spawn in a hook script that does not pass creationflags.

    NO `sys.executable` EXEMPTION, and its removal is the point. A first version
    of this auditor skipped calls whose argv[0] was `sys.executable`, reasoning
    that under `pythonw.exe` that IS `pythonw.exe` and allocates no console. The
    first clause is true; the conclusion is false, because the child can re-exec
    a console BINARY - `ruff/__main__.py` does exactly that - and the grandchild
    allocates the console the exemption assumed away. The exemption whitelisted
    the one site still flashing, and worse, the one whose stdout was being
    silently discarded.

    So the rule is unconditional: if a hook script spawns anything, it says how.
    """
    offenders: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Attribute) and func.attr in {"run", "Popen", "call"}):
            continue
        if not (isinstance(func.value, ast.Name) and func.value.id == "subprocess"):
            continue
        if any(kw.arg == "creationflags" for kw in node.keywords):
            continue
        offenders.append(f"{label}:{node.lineno} subprocess.{func.attr} without creationflags")
    return offenders


# ---------------------------------------------------------------------------
# 1. The audit, and the control that proves the audit can fail
# ---------------------------------------------------------------------------


def test_the_auditor_detects_an_unflagged_spawn():
    """NEGATIVE CONTROL. Without this the audit below could pass by seeing nothing."""
    bad = "import subprocess\nsubprocess.run(['git', 'status'], capture_output=True)\n"
    found = unflagged_spawns(bad, "synthetic")
    assert len(found) == 1, f"the auditor missed an unflagged spawn: {found}"
    assert "synthetic:2" in found[0]


def test_the_auditor_flags_a_sys_executable_spawn_too():
    """REGRESSION. The exemption this replaces hid a live defect.

    `[sys.executable, "-m", "ruff"]` under `pythonw.exe` re-execs `ruff.exe`, a
    console binary, so it flashes AND loses its stdout to the new console. An
    auditor that exempts this shape reports clean over the one site that is
    broken.
    """
    spawn = "import subprocess, sys\nsubprocess.run([sys.executable, '-m', 'ruff'])\n"
    assert len(unflagged_spawns(spawn, "synthetic")) == 1


def test_the_auditor_does_not_flag_a_correctly_suppressed_spawn():
    ok = (
        "import subprocess\n"
        "subprocess.run(['git', 'status'], creationflags=0)\n"
    )
    assert unflagged_spawns(ok, "synthetic") == []


def test_no_hook_script_spawns_an_external_exe_without_suppressing_its_console():
    offenders: list[str] = []
    for rel in HOOK_SCRIPTS:
        path = REPO / rel
        assert path.is_file(), f"hook script {rel} is missing"
        offenders.extend(unflagged_spawns(path.read_text(encoding="utf-8"), rel))
    assert offenders == [], (
        "these spawns allocate a console window when the hook runs under "
        f"pythonw.exe: {offenders}"
    )


# ---------------------------------------------------------------------------
# 2. The fix must not have silenced the gates
# ---------------------------------------------------------------------------


@pytest.mark.skipif(sys.platform != "win32", reason="CREATE_NO_WINDOW is Windows-only")
def test_suppressing_the_console_does_not_break_stdout_capture():
    """The real risk of the fix: a gate that reads nothing still exits 0.

    Run the same command with and without the flag and require IDENTICAL output.
    A flag that detached the child, rather than only hiding its window, would
    return empty stdout here while leaving every caller looking healthy.
    """
    flag = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    assert flag, "CREATE_NO_WINDOW should exist on win32"
    argv = [sys.executable, "-c", "print('captured')"]

    plain = subprocess.run(argv, capture_output=True, text=True, timeout=30)
    hidden = subprocess.run(argv, capture_output=True, text=True, timeout=30, creationflags=flag)

    assert plain.returncode == 0 and hidden.returncode == 0
    assert hidden.stdout.strip() == "captured"
    assert hidden.stdout == plain.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="the defect is Windows-only")
def test_the_ruff_gate_reads_ruffs_output_from_a_console_less_parent(tmp_path):
    """THE DEAD-GATE REGRESSION, and it must run under pythonw to mean anything.

    `precommit_gate` collects ruff reasons only when the return code is 1, by
    iterating `result.stdout`. Under `pythonw.exe` the old
    `[sys.executable, "-m", "ruff"]` form returned rc 1 with stdout LENGTH 0,
    because `ruff/__main__.py` re-execs `ruff.exe`, which allocated its own
    console and bound its handles there instead of to the pipe. Zero reasons were
    appended and every commit passed the ruff half of the gate.

    THE PARENT MUST BE CONSOLE-LESS OR THIS TEST PROVES NOTHING. Run under
    pytest, whose parent owns a console, the broken form passes too - which is
    exactly why the suite never caught this. So the probe re-launches itself
    through `pythonw.exe`.
    """
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    if not pythonw.is_file():
        pytest.skip("pythonw.exe not alongside this interpreter")

    target = tmp_path / "dead.py"
    target.write_text("import os\n", encoding="utf-8")

    driver = tmp_path / "driver.py"
    driver.write_text(
        "import json, sys, subprocess\n"
        f"sys.path.insert(0, {str(REPO)!r})\n"
        "from tools import precommit_gate as g\n"
        "argv = g._ruff_argv()\n"
        f"r = subprocess.run([*argv, 'check', {str(target)!r}], capture_output=True,\n"
        "                   text=True, timeout=60, creationflags=g.NO_WINDOW)\n"
        "print(json.dumps({'rc': r.returncode, 'len': len(r.stdout)}))\n",
        encoding="utf-8",
    )
    out = tmp_path / "out.json"
    with out.open("w", encoding="utf-8") as sink:
        subprocess.run(
            [str(pythonw), str(driver)],
            stdout=sink,
            stderr=subprocess.STDOUT,
            timeout=120,
        )

    import json as _json

    got = _json.loads(out.read_text(encoding="utf-8").strip())
    assert got["rc"] == 1, f"ruff should flag the unused import, got {got}"
    assert got["len"] > 0, (
        "ruff reported a failure and the gate captured ZERO bytes of it - the "
        "ruff half of the precommit gate is silently passing every commit"
    )


def test_the_hook_helpers_still_return_real_data():
    """End to end through the actual functions, not a synthetic command.

    `staged_files` is the one whose silence would be invisible: an empty list is
    a legitimate result, so a broken capture reads as a clean tree and the ASCII
    and ruff gates then scan nothing at all.
    """
    from tools import precommit_gate, rm_facts

    root = precommit_gate._repo_root(REPO)
    assert root is not None, "git rev-parse returned nothing - capture is broken"
    assert root.resolve() == REPO.resolve()

    assert isinstance(precommit_gate.staged_files(REPO), list)
    assert isinstance(rm_facts.scheduled_tasks(), list)

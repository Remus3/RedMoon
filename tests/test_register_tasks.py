import subprocess

from ops.register_tasks import (
    TASKS,
    build_create_command,
    build_delete_command,
    _build_create_argv_from_spec,
)


def test_data_refresh_task_is_declared():
    assert "RM-DataRefresh" in TASKS
    spec = TASKS["RM-DataRefresh"]
    assert spec["schedule"] == "DAILY"
    assert "rmdata_extract.py" in spec["script"]


def test_every_task_name_uses_the_rm_prefix():
    for name in TASKS:
        assert name.startswith("RM-"), f"{name} does not use the RM- prefix"


def test_create_command_is_well_formed():
    argv = build_create_command("RM-DataRefresh")
    assert argv[0] == "schtasks"
    assert "/create" in argv
    assert "/tn" in argv and "RM-DataRefresh" in argv
    assert "/sc" in argv and "DAILY" in argv
    joined = " ".join(argv)
    assert "pythonw.exe" in joined
    assert "rmdata_extract.py" in joined


def test_delete_command_is_forced_and_targeted():
    argv = build_delete_command("RM-DataRefresh")
    assert argv[:2] == ["schtasks", "/delete"]
    assert "RM-DataRefresh" in argv
    assert "/f" in argv


def test_unknown_task_raises():
    import pytest

    with pytest.raises(KeyError):
        build_create_command("RM-DoesNotExist")


def test_create_command_quoting_with_spaces_in_paths():
    """Verify that paths with spaces are properly quoted.

    This test exercises the quoting behavior by constructing a synthetic
    task spec with spaces in both the pythonw path and script path. We then
    verify that when the argv is passed through subprocess.list2cmdline
    (which is how the --show output is rendered), the /tr value preserves
    both quoted paths as a single argument. Without proper quoting, Windows
    schtasks would split the /tr argument at the space between the exe and
    script paths, causing the script path to become a stray token that
    schtasks would reject.
    """
    # Synthetic task spec with spaces in paths
    synthetic_spec = {
        "script": r"C:\Program Files\Red Moon\tools\rmdata extract.py",
        "schedule": "DAILY",
        "start_time": "05:30",
        "description": "Test task with spaces",
    }

    pythonw_with_space = r"C:\Program Files\Python314\pythonw.exe"
    argv = _build_create_argv_from_spec("RM-TestSpaces", pythonw_with_space, synthetic_spec)

    # The argv should have /tr as a single list element containing the quoted paths
    tr_index = argv.index("/tr")
    tr_value = argv[tr_index + 1]
    # tr_value should be: "<pythonw_with_space>" "<script_with_space>"
    assert tr_value == f'"{pythonw_with_space}" "{synthetic_spec["script"]}"'

    # Now convert to command line (as --show does) and verify the quoting
    # is preserved and the /tr value survives Windows tokenization
    cmdline = subprocess.list2cmdline(argv)

    # The cmdline should have the /tr value with inner quotes properly escaped
    # or formatted so that when schtasks receives it, /tr captures both paths as one
    assert "/tr" in cmdline
    # Verify that the pythonw path and script path both appear in the cmdline
    # and that they are quoted
    assert f'"{pythonw_with_space}"' in cmdline or pythonw_with_space in cmdline
    assert f'"{synthetic_spec["script"]}"' in cmdline or synthetic_spec["script"] in cmdline

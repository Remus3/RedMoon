from ops.register_tasks import TASKS, build_create_command, build_delete_command


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

import ctypes
import subprocess
import sys

from ops.register_tasks import (
    TASKS,
    _build_create_argv_from_spec,
    build_create_command,
    build_delete_command,
    main,
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


def _tokenize(cmdline: str) -> list[str]:
    """Tokenize a command line using Windows CommandLineToArgvW API.

    This mimics what the actual Windows shell does when parsing a command line,
    ensuring that our list2cmdline output is faithful to real execution.
    """
    # Set up the function signature for CommandLineToArgvW
    kernel32 = ctypes.WinDLL("kernel32", use_errno=True)
    shell32 = ctypes.WinDLL("shell32", use_errno=True)

    # CommandLineToArgvW(LPCWSTR lpCmdLine, int *pNumArgs) -> LPWSTR*
    shell32.CommandLineToArgvW.argtypes = [
        ctypes.c_wchar_p,
        ctypes.POINTER(ctypes.c_int),
    ]
    shell32.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)

    argc = ctypes.c_int(0)
    argv = shell32.CommandLineToArgvW(cmdline, ctypes.byref(argc))

    if not argv:
        return []

    try:
        # Extract the argument strings from the array
        result = []
        for i in range(argc.value):
            result.append(argv[i])
        return result
    finally:
        kernel32.LocalFree(argv)


def test_create_command_quoting_round_trips_with_spaces():
    """TEST A: Verify /tr value survives Windows tokenization with spaces.

    Build a create command for a synthetic spec whose executable and script
    paths both contain spaces. Render with subprocess.list2cmdline. Tokenize
    back using CommandLineToArgvW. Assert the /tr value comes back as exactly
    ONE argument containing both quoted paths.

    This test FAILS if the /tr value is built unquoted, because the inner space
    would split it into two tokens and the element after /tr would be only the
    executable path, not the full quoted action string.
    """
    # Synthetic task spec with spaces in both paths
    synthetic_spec = {
        "script": r"C:\Program Files\Red Moon\tools\rmdata extract.py",
        "schedule": "DAILY",
        "start_time": "05:30",
        "description": "Test task with spaces",
    }

    pythonw_with_space = r"C:\Program Files\Python314\pythonw.exe"
    argv = _build_create_argv_from_spec(
        "RM-TestSpaces", pythonw_with_space, synthetic_spec
    )

    # The argv should have /tr as a single list element containing the quoted paths
    tr_index = argv.index("/tr")
    tr_value = argv[tr_index + 1]
    expected_tr_value = f'"{pythonw_with_space}" "{synthetic_spec["script"]}"'
    assert tr_value == expected_tr_value

    # Render to command line as --show does
    cmdline = subprocess.list2cmdline(argv)

    # Tokenize back using the real Windows API
    tokenized = _tokenize(cmdline)

    # Find /tr in the tokenized result and assert the next element equals
    # the original /tr value (both paths intact, not split)
    tr_idx = tokenized.index("/tr")
    tokenized_tr_value = tokenized[tr_idx + 1]

    # This assertion FAILS if quoting is broken - the inner space would cause
    # the value to split, and we'd get only the pythonw path
    assert tokenized_tr_value == expected_tr_value


def test_main_show_uses_list2cmdline_not_space_join(capsys):
    """TEST B: Verify main() --show uses subprocess.list2cmdline.

    Call main() with --show flag and capture stdout. Assert the output
    uses proper quoting via list2cmdline. Assert it is NOT equal to the
    naive space-join version.

    This test FAILS if main()'s --show path is reverted to ' '.join(argv),
    because the output would differ from the properly quoted version.
    """
    # Patch sys.argv to pass --show to main()
    original_argv = sys.argv
    try:
        sys.argv = ["ops/register_tasks.py", "--show"]
        main()
    finally:
        sys.argv = original_argv

    # Capture the output
    captured = capsys.readouterr()
    output_line = captured.out.strip()

    # Build what the correct output should be
    argv = build_create_command("RM-DataRefresh")
    correct_cmdline = subprocess.list2cmdline(argv)
    expected_line = f"RM-DataRefresh: {correct_cmdline}"

    # Build what the broken (space-join) version would be
    broken_cmdline = " ".join(argv)
    broken_line = f"RM-DataRefresh: {broken_cmdline}"

    # Assert the output matches the correct version
    assert output_line == expected_line

    # Assert it is NOT the broken version (this is the key assertion that
    # makes the test fail if someone reverts to space-join)
    assert output_line != broken_line

"""Tests for tools/install_bepinex.py.

Every test runs against a synthetic install tree under tmp_path. Nothing here
ever reads or writes the real V Rising install: an installer whose test suite
touches the live game directory is the exact failure the tool exists to stop.

Ground truth these fixtures mirror (probed live, install build 1.1.13.0-r99712):
  <root>/VERSION                 "VRising: v1.1.13.0-r99712-b17 (202605251526)"
  <root>/VRising_Server/VERSION  "VRisingServer: v1.1.13.0-r99712-b17 (202605251709)"
  <root>/v3/VERSION              "VRising: v1.0.10.4-r91333-b12 (202504301836)"
The server line differs from the client line in BOTH product prefix and trailing
timestamp. Only the semantic build matches, so only the semantic build is
asserted on.
"""

import zipfile
from pathlib import Path

import pytest

from tools.install_bepinex import (
    InstallRefused,
    main,
    plan_pack,
    resolve_target,
    verify,
)

BUILD = "1.1.13.0-r99712"
CLIENT_VERSION = "VRising: v1.1.13.0-r99712-b17 (202605251526)"
SERVER_VERSION = "VRisingServer: v1.1.13.0-r99712-b17 (202605251709)"
STALE_V3_VERSION = "VRising: v1.0.10.4-r91333-b12 (202504301836)"


def make_repo(tmp_path: Path, pin: str = BUILD) -> Path:
    """A minimal repo root carrying only data/rmdata/current.txt."""
    repo = tmp_path / "repo"
    pointer = repo / "data" / "rmdata" / "current.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    pointer.write_text(pin + "\n", encoding="utf-8")
    return repo


def make_client_dir(
    path: Path,
    version: str = CLIENT_VERSION,
    assembly: bool = True,
    exe: bool = True,
) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "VERSION").write_text(version, encoding="utf-8")
    if assembly:
        (path / "GameAssembly.dll").write_bytes(b"il2cpp")
    if exe:
        (path / "VRising.exe").write_bytes(b"client")
    return path


def make_server_dir(
    path: Path,
    version: str = SERVER_VERSION,
    assembly: bool = True,
    exe: bool = True,
) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    (path / "VERSION").write_text(version, encoding="utf-8")
    if assembly:
        (path / "GameAssembly.dll").write_bytes(b"il2cpp")
    if exe:
        (path / "VRisingServer.exe").write_bytes(b"server")
    return path


def make_install(tmp_path: Path, name: str = "VRising") -> Path:
    """A full synthetic install: root, the stale v3 copy, and the server."""
    root = make_client_dir(tmp_path / name)
    make_client_dir(root / "v3", version=STALE_V3_VERSION)
    make_server_dir(root / "VRising_Server")
    return root


def make_pack(
    path: Path,
    wrapper: str | None = None,
    winhttp: bool = True,
    metadata: bool = False,
) -> Path:
    """A small but structurally real BepInEx pack zip.

    metadata=True reproduces the shape of the real Thunderstore download
    (BepInExPack_V_Rising-1.733.2.zip): the payload nested one directory deep,
    alongside icon.png / manifest.json / README.md at the archive root. Those
    three are Thunderstore packaging, not payload, and must never land in the
    game directory.
    """
    prefix = f"{wrapper}/" if wrapper else ""
    members = {
        f"{prefix}BepInEx/config/.keep": b"",
        f"{prefix}BepInEx/core/BepInEx.Unity.IL2CPP.dll": b"core",
        f"{prefix}BepInEx/patchers/.keep": b"",
        f"{prefix}BepInEx/plugins/.keep": b"",
        f"{prefix}dotnet/System.Runtime.dll": b"dotnet",
        f"{prefix}.doorstop_version": b"4.0.0",
        f"{prefix}changelog.txt": b"1.733.2\n",
        f"{prefix}doorstop_config.ini": b"[General]\nenabled=true\n",
    }
    if winhttp:
        members[f"{prefix}winhttp.dll"] = b"doorstop"
    if metadata:
        members["icon.png"] = b"\x89PNG"
        members["manifest.json"] = b'{"name": "BepInExPack_V_Rising"}'
        members["README.md"] = b"# BepInExPack V Rising\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in members.items():
            archive.writestr(name, data)
    return path


THUNDERSTORE_METADATA = ("icon.png", "manifest.json", "README.md")


def snapshot(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def run(argv: list[str]) -> int:
    return main([str(a) for a in argv])


# ---------------------------------------------------------------------------
# Refusals. Each asserts a non-zero exit AND that the named assertion appears
# in the reason, so a test cannot pass on the wrong refusal.
# ---------------------------------------------------------------------------


def test_refuses_a_wrong_version_string(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_client_dir(tmp_path / "VRising", version="not a version at all")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])

    assert code != 0
    assert "unparseable-version" in capsys.readouterr().err


def test_refuses_a_path_with_v3_as_a_component(tmp_path, capsys):
    """The v3 trap: a complete stale second copy that Steam never launches."""
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    trap = root / "v3"
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", trap, "--repo", repo, "--show"])

    err = capsys.readouterr().err
    assert code != 0
    assert "v3-path-component" in err


def test_refuses_a_v3_component_that_is_not_the_final_component(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path / "v3")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])

    err = capsys.readouterr().err
    assert code != 0
    assert "v3-path-component" in err


def test_refuses_when_game_assembly_is_absent(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_client_dir(tmp_path / "VRising", assembly=False)
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])

    assert code != 0
    assert "missing-game-assembly" in capsys.readouterr().err


def test_refuses_when_the_parsed_build_disagrees_with_current_txt(tmp_path, capsys):
    repo = make_repo(tmp_path, pin="9.9.9.9-r00001")
    root = make_client_dir(tmp_path / "VRising")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])

    err = capsys.readouterr().err
    assert code != 0
    assert "build-mismatch" in err
    assert BUILD in err and "9.9.9.9-r00001" in err


def test_refuses_client_target_pointed_at_a_server_shaped_dir(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip")

    code = run(
        [
            "--pack", pack, "--target", "client",
            "--root", root / "VRising_Server", "--repo", repo, "--show",
        ]
    )

    assert code != 0
    assert "client-target-is-server-dir" in capsys.readouterr().err


def test_refuses_server_target_pointed_at_a_root_shaped_fixture(tmp_path, capsys):
    """A root-shaped tree has no VRising_Server child to descend into."""
    repo = make_repo(tmp_path)
    root = make_client_dir(tmp_path / "VRising")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "server", "--root", root, "--repo", repo, "--show"])

    err = capsys.readouterr().err
    assert code != 0
    assert "target-not-a-directory" in err
    assert "VRising_Server" in err


def test_refuses_server_target_whose_dir_is_a_client_copy(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_client_dir(tmp_path / "VRising")
    make_client_dir(root / "VRising_Server")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "server", "--root", root, "--repo", repo, "--show"])

    assert code != 0
    assert "missing-server-exe" in capsys.readouterr().err


def test_refuses_a_pack_archive_without_winhttp(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip", winhttp=False)

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])

    assert code != 0
    assert "pack-missing-winhttp" in capsys.readouterr().err


def test_plan_pack_refuses_an_archive_without_a_bepinex_directory(tmp_path):
    pack = tmp_path / "bad.zip"
    with zipfile.ZipFile(pack, "w") as archive:
        archive.writestr("winhttp.dll", b"doorstop")
        archive.writestr("doorstop_config.ini", b"x")

    with pytest.raises(InstallRefused, match="pack-missing-bepinex"):
        plan_pack(pack)


# ---------------------------------------------------------------------------
# Acceptance
# ---------------------------------------------------------------------------


def test_server_profile_reads_the_parent_version_and_accepts_a_differing_line(tmp_path):
    """The subtle case.

    The server's own VERSION shares neither product prefix nor timestamp with
    the client's. Requiring byte equality would refuse the real, correct
    install. Only the semantic build is allowed to matter.
    """
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)

    resolution = verify(root, "server", repo)

    assert resolution.target == resolve_target(root, "server")
    assert resolution.pinned_root == root.resolve()
    assert resolution.build == BUILD

    read = dict(resolution.versions)
    assert read[str(root.resolve())] == CLIENT_VERSION
    assert read[str(resolution.target)] == SERVER_VERSION
    assert read[str(resolution.target)] != read[str(resolution.pinned_root)]
    assert not read[str(resolution.target)].startswith("VRising:")
    assert "202605251709" in read[str(resolution.target)]
    assert "202605251526" in read[str(resolution.pinned_root)]


def test_server_profile_refuses_when_the_parent_root_build_is_wrong(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    (root / "VERSION").write_text(STALE_V3_VERSION, encoding="utf-8")
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "server", "--root", root, "--repo", repo, "--show"])

    assert code != 0
    assert "build-mismatch" in capsys.readouterr().err


def test_show_reports_both_version_lines_for_the_server_profile(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "server", "--root", root, "--repo", repo, "--show"])

    out = capsys.readouterr().out
    assert code == 0
    assert CLIENT_VERSION in out
    assert SERVER_VERSION in out
    assert "winhttp.dll" in out


def test_show_writes_nothing(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip")

    before = snapshot(root)
    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--show"])
    after = snapshot(root)

    assert code == 0
    assert before == after
    capsys.readouterr()


def test_install_places_the_files(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip")

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--install"])

    assert code == 0, capsys.readouterr().err
    assert (root / "winhttp.dll").read_bytes() == b"doorstop"
    assert (root / "BepInEx" / "core" / "BepInEx.Unity.IL2CPP.dll").read_bytes() == b"core"
    assert (root / "dotnet" / "System.Runtime.dll").read_bytes() == b"dotnet"
    assert (root / ".doorstop_version").read_bytes() == b"4.0.0"
    assert (root / "doorstop_config.ini").is_file()
    assert not (root / "v3" / "winhttp.dll").exists()
    assert not (root / "VRising_Server" / "winhttp.dll").exists()
    assert not list(root.rglob("*.rmtmp"))


def test_install_strips_a_thunderstore_wrapper_directory(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip", wrapper="BepInExPack_V_Rising")

    code = run(["--pack", pack, "--target", "server", "--root", root, "--repo", repo, "--install"])
    target = root / "VRising_Server"

    assert code == 0, capsys.readouterr().err
    assert (target / "winhttp.dll").read_bytes() == b"doorstop"
    assert (target / "BepInEx" / "core" / "BepInEx.Unity.IL2CPP.dll").is_file()
    assert not (target / "BepInExPack_V_Rising").exists()
    assert not (root / "winhttp.dll").exists()


def test_install_refuses_before_writing_a_single_byte(tmp_path, capsys):
    repo = make_repo(tmp_path, pin="9.9.9.9-r00001")
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip")

    before = snapshot(root)
    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--install"])
    after = snapshot(root)

    assert code != 0
    assert "build-mismatch" in capsys.readouterr().err
    assert before == after


PAYLOAD = {
    "BepInEx/config/.keep",
    "BepInEx/core/BepInEx.Unity.IL2CPP.dll",
    "BepInEx/patchers/.keep",
    "BepInEx/plugins/.keep",
    "dotnet/System.Runtime.dll",
    ".doorstop_version",
    "changelog.txt",
    "doorstop_config.ini",
    "winhttp.dll",
}


def test_plan_pack_derives_members_from_the_archive(tmp_path):
    pack = make_pack(tmp_path / "pack.zip", wrapper="BepInExPack_V_Rising")
    assert set(plan_pack(pack)) == PAYLOAD


def test_plan_pack_on_the_real_thunderstore_shape_drops_the_metadata(tmp_path):
    """Shaped exactly like BepInExPack_V_Rising-1.733.2.zip: a single payload
    wrapper directory alongside three Thunderstore metadata files at the root.
    """
    pack = make_pack(tmp_path / "pack.zip", wrapper="BepInExPack_V_Rising", metadata=True)
    plan = plan_pack(pack)
    assert set(plan) == PAYLOAD
    for name in THUNDERSTORE_METADATA:
        assert name not in plan


def test_plan_pack_derives_the_wrapper_rather_than_hardcoding_its_name(tmp_path):
    pack = make_pack(tmp_path / "pack.zip", wrapper="SomeOtherPackName", metadata=True)
    assert set(plan_pack(pack)) == PAYLOAD


def test_install_of_the_real_thunderstore_shape_writes_payload_only(tmp_path, capsys):
    repo = make_repo(tmp_path)
    root = make_install(tmp_path)
    pack = make_pack(tmp_path / "pack.zip", wrapper="BepInExPack_V_Rising", metadata=True)

    code = run(["--pack", pack, "--target", "client", "--root", root, "--repo", repo, "--install"])

    assert code == 0, capsys.readouterr().err
    assert (root / "winhttp.dll").read_bytes() == b"doorstop"
    assert (root / ".doorstop_version").is_file()
    assert (root / "doorstop_config.ini").is_file()
    assert (root / "BepInEx" / "core" / "BepInEx.Unity.IL2CPP.dll").is_file()
    assert (root / "dotnet" / "System.Runtime.dll").is_file()
    for name in THUNDERSTORE_METADATA:
        assert not (root / name).exists(), f"{name} is Thunderstore packaging, not payload"
    assert not (root / "BepInExPack_V_Rising").exists()


def test_plan_pack_refuses_a_traversing_member(tmp_path):
    pack = tmp_path / "evil.zip"
    with zipfile.ZipFile(pack, "w") as archive:
        archive.writestr("winhttp.dll", b"doorstop")
        archive.writestr("BepInEx/core/x.dll", b"core")
        archive.writestr("../escaped.dll", b"nope")

    with pytest.raises(InstallRefused, match="pack-unsafe-member"):
        plan_pack(pack)

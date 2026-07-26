#!/usr/bin/env python3
"""Install the BepInEx loader pack into a V Rising game directory.

This tool refuses far more than it copies. Installing into the wrong directory
is the highest-impact failure available here: it produces a loader that never
loads, and then a debugging session chasing a bind failure that never happened.
So every path into a write is gated on assertions that name themselves when
they fail.

The install carries three directories that look interchangeable and are not:

  <root>/                 the client Steam launches. VRising.exe.
  <root>/v3/              a COMPLETE STALE SECOND COPY, build 1.0.10.4-r91333.
                          Steam never launches it. It must never receive
                          BepInEx. Any target path with a "v3" component
                          anywhere is refused outright.
  <root>/VRising_Server/  the dedicated server. VRisingServer.exe.

The server carries its own VERSION file, and it agrees with the client's on the
semantic build ONLY:

  <root>/VERSION                 VRising: v1.1.13.0-r99712-b17 (202605251526)
  <root>/VRising_Server/VERSION  VRisingServer: v1.1.13.0-r99712-b17 (202605251709)

The product prefix differs and so does the trailing timestamp. Requiring byte
equality would refuse the real, correct install, so the pin is asserted through
parse_build_id - the same parser tools/rmdata_extract.py uses - and never by
string comparison of the whole line.

Usage:
    python tools/install_bepinex.py --pack <zip> --target client|server
                                    [--show | --install]
                                    [--root <dir>] [--repo <dir>]

--show resolves and asserts everything, prints what it found and what it would
write, and changes nothing. --install re-runs every assertion and aborts before
writing a single byte if any of them fails.
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# Run as a script, sys.path[0] is tools/, not the repo root. Bootstrap the root
# before importing anything from the project.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.rmdata_extract import parse_build_id  # noqa: E402

DEFAULT_ROOT = Path(r"C:\Program Files (x86)\Steam\steamapps\common\VRising")
DEFAULT_REPO = Path(__file__).resolve().parents[1]

SERVER_DIRNAME = "VRising_Server"
STALE_COPY_COMPONENT = "v3"
GAME_ASSEMBLY = "GameAssembly.dll"
CLIENT_EXE = "VRising.exe"
SERVER_EXE = "VRisingServer.exe"
VERSION_FILENAME = "VERSION"

# The doorstop shim is the one member that proves this is a loader pack and not
# some other archive. BepInEx/ proves the pack half of it.
DOORSTOP_SHIM = "winhttp.dll"
BEPINEX_DIRNAME = "BepInEx"

PROFILES = ("client", "server")


class InstallRefused(Exception):
    """A named assertion failed. The message leads with the assertion's name."""


@dataclass
class Resolution:
    """Everything the assertions established, for reporting and for install."""

    profile: str
    target: Path
    pinned_root: Path
    build: str
    versions: list[tuple[str, str]] = field(default_factory=list)


def read_pin(repo_root: Path) -> str:
    """The build this repo is pinned to, from data/rmdata/current.txt."""
    pointer = repo_root / "data" / "rmdata" / "current.txt"
    if not pointer.is_file():
        raise InstallRefused(f"missing-build-pin: no {pointer}")
    pin = pointer.read_text(encoding="utf-8").strip()
    if not pin:
        raise InstallRefused(f"missing-build-pin: {pointer} is empty")
    return pin


def read_version(directory: Path) -> str:
    """The VERSION line in a game directory, verbatim."""
    path = directory / VERSION_FILENAME
    if not path.is_file():
        raise InstallRefused(f"missing-version-file: no {path}")
    return path.read_text(encoding="utf-8").strip()


def build_of(directory: Path) -> tuple[str, str]:
    """Return (version_line, semantic_build) for a game directory."""
    line = read_version(directory)
    try:
        return line, parse_build_id(line)
    except ValueError as exc:
        raise InstallRefused(f"unparseable-version: {directory / VERSION_FILENAME}: {exc}") from exc


def resolve_target(root: Path, profile: str) -> Path:
    """The absolute directory that would receive the pack.

    The client target is the install root itself. The server target is the
    VRising_Server child, unless root already names it, so both
    --root <install> and --root <install>/VRising_Server work.
    """
    root = Path(root).resolve()
    if profile == "client":
        return root
    if root.name == SERVER_DIRNAME:
        return root
    return root / SERVER_DIRNAME


def assert_no_stale_copy(path: Path) -> None:
    """Refuse any path with a "v3" component ANYWHERE, not just at the end."""
    for part in path.parts:
        if part.lower() == STALE_COPY_COMPONENT:
            raise InstallRefused(
                f"v3-path-component: {path} descends through the stale "
                f"{STALE_COPY_COMPONENT} copy, which Steam never launches"
            )


def verify(root: Path, profile: str, repo_root: Path) -> Resolution:
    """Run every assertion for the profile. Raises InstallRefused on any failure."""
    if profile not in PROFILES:
        raise InstallRefused(f"unknown-profile: {profile!r}")

    pin = read_pin(Path(repo_root))
    target = resolve_target(root, profile)

    # Ordered so the most structural refusal wins: a caller pointed at the
    # wrong tree should be told that, not told about a missing file inside it.
    assert_no_stale_copy(target)

    if not target.is_dir():
        raise InstallRefused(f"target-not-a-directory: {target}")

    if profile == "client":
        if target.name == SERVER_DIRNAME:
            raise InstallRefused(
                f"client-target-is-server-dir: {target} is the dedicated server, "
                "use --target server"
            )
        pinned_root = target
    else:
        if target.name != SERVER_DIRNAME:
            raise InstallRefused(
                f"server-target-name: {target} final component is not {SERVER_DIRNAME}"
            )
        pinned_root = target.parent

    if not (target / GAME_ASSEMBLY).is_file():
        raise InstallRefused(
            f"missing-game-assembly: no {target / GAME_ASSEMBLY}, so this is not "
            "the IL2CPP build BepInEx loads into"
        )

    exe = CLIENT_EXE if profile == "client" else SERVER_EXE
    if not (target / exe).is_file():
        raise InstallRefused(f"missing-{profile}-exe: no {target / exe}")

    versions: list[tuple[str, str]] = []
    pinned_line, pinned_build = build_of(pinned_root)
    versions.append((str(pinned_root), pinned_line))

    if pinned_build != pin:
        raise InstallRefused(
            f"build-mismatch: {pinned_root / VERSION_FILENAME} parses to "
            f"{pinned_build}, repo is pinned to {pin}"
        )

    if profile == "server":
        # The server line differs from the client's in product prefix AND
        # timestamp. Only the semantic build may be asserted on.
        server_line, server_build = build_of(target)
        versions.append((str(target), server_line))
        if server_build != pin:
            raise InstallRefused(
                f"server-build-mismatch: {target / VERSION_FILENAME} parses to "
                f"{server_build}, repo is pinned to {pin}"
            )

    return Resolution(
        profile=profile,
        target=target,
        pinned_root=pinned_root,
        build=pin,
        versions=versions,
    )


def plan_pack(pack_path: Path) -> dict[str, str]:
    """Map each payload file's target-relative path to its archive member name.

    The member list is derived from the archive, never hardcoded. Some
    Thunderstore packs nest the payload one directory deep and sit it beside
    packaging files (icon.png, manifest.json, README.md) that must NOT land in
    the game directory. The wrapper is detected by where the doorstop shim
    actually is: at the archive root, or exactly one directory down. Anything
    outside the payload root is packaging and is dropped.
    """
    pack_path = Path(pack_path)
    if not pack_path.is_file():
        raise InstallRefused(f"pack-not-found: {pack_path}")

    try:
        with zipfile.ZipFile(pack_path) as archive:
            members = [info.filename for info in archive.infolist() if not info.is_dir()]
    except zipfile.BadZipFile as exc:
        raise InstallRefused(f"pack-not-a-zip: {pack_path}: {exc}") from exc

    if not members:
        raise InstallRefused(f"pack-empty: {pack_path}")

    names = {name.replace("\\", "/") for name in members}
    prefix = ""
    if DOORSTOP_SHIM not in names:
        tops = {name.split("/", 1)[0] for name in names if "/" in name}
        if len(tops) == 1:
            wrapper = next(iter(tops))
            if f"{wrapper}/{DOORSTOP_SHIM}" in names:
                prefix = wrapper + "/"

    plan: dict[str, str] = {}
    for member in members:
        norm = member.replace("\\", "/")
        if prefix:
            if not norm.startswith(prefix):
                continue  # packaging beside the payload root
            rel = norm[len(prefix) :]
        else:
            rel = norm
        if not rel:
            continue
        parts = PurePosixPath(rel).parts
        if norm.startswith("/") or ".." in parts or ":" in rel:
            raise InstallRefused(f"pack-unsafe-member: {member} escapes the target directory")
        plan[rel] = member

    if DOORSTOP_SHIM not in plan:
        raise InstallRefused(
            f"pack-missing-winhttp: {pack_path} has no {DOORSTOP_SHIM}, "
            "so it is not a BepInEx loader pack"
        )
    if not any(PurePosixPath(rel).parts[0] == BEPINEX_DIRNAME for rel in plan):
        raise InstallRefused(
            f"pack-missing-bepinex: {pack_path} has no {BEPINEX_DIRNAME}/ directory, "
            "so it is not a BepInEx loader pack"
        )
    return plan


def extract_pack(pack_path: Path, plan: dict[str, str], target: Path) -> list[Path]:
    """Write every planned member into target. Each file lands atomically."""
    written: list[Path] = []
    with zipfile.ZipFile(pack_path) as archive:
        for rel in sorted(plan):
            dest = target.joinpath(*PurePosixPath(rel).parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(plan[rel]) as source:
                data = source.read()
            tmp = dest.with_name(dest.name + ".rmtmp")
            tmp.write_bytes(data)
            os.replace(tmp, dest)
            written.append(dest)
    return written


def report(resolution: Resolution, plan: dict[str, str], pack_path: Path) -> str:
    lines = [
        f"profile:     {resolution.profile}",
        f"target:      {resolution.target}",
        f"pinned root: {resolution.pinned_root}",
        f"build pin:   {resolution.build}",
        f"pack:        {pack_path}",
        "versions read:",
    ]
    for directory, line in resolution.versions:
        lines.append(f"  {directory}/{VERSION_FILENAME}: {line}")
    lines.append(f"files ({len(plan)}):")
    lines += [f"  {resolution.target / Path(rel)}" for rel in sorted(plan)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install the BepInEx loader pack into a V Rising game directory."
    )
    parser.add_argument("--pack", type=Path, required=True, help="path to the BepInEx pack zip")
    parser.add_argument("--target", choices=PROFILES, required=True)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--show", action="store_true", help="report only, write nothing (default)")
    mode.add_argument("--install", action="store_true", help="write the pack into the target")
    args = parser.parse_args(argv)

    try:
        resolution = verify(args.root, args.target, args.repo)
        plan = plan_pack(args.pack)
    except InstallRefused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(report(resolution, plan, args.pack))

    if not args.install:
        print("show only: nothing written")
        return 0

    written = extract_pack(args.pack, plan, resolution.target)
    print(f"installed {len(written)} files into {resolution.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

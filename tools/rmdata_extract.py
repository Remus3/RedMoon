#!/usr/bin/env python3
"""Extract the offline data floor from a V Rising install.

Produces a versioned, regenerable directory under data/rmdata/<build>/. Only
data that genuinely exists offline is written: the localization string table,
the difficulty presets, and the shipped settings files.

Item and ability stat ROWS are deliberately NOT produced here. Identity and
stats live in binary DOTS ECS blobs, and the join from a PrefabGUID to its stats
exists only in the running game's entity world. See ADR-002. What is produced is
the seam itself: <build>/tables/ with one empty, schema-valid envelope per name
in core.tables.TABLE_NAMES, which the cycle 2 bridge dump fills in place.

Idempotent: re-running against an unchanged install rewrites byte-identical
output. Every consumer-visible file is written atomically.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Run as a script, sys.path[0] is tools/, not the repo root. Bootstrap the root
# before importing anything from core.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.tables import (  # noqa: E402
    TABLE_NAMES,
    TABLES_DIRNAME,
    empty_table,
    load_schema,
    validate_table,
)

DEFAULT_INSTALL = Path(r"C:\Program Files (x86)\Steam\steamapps\common\VRising")

_BUILD_RE = re.compile(r"v(?P<build>\d+\.\d+\.\d+\.\d+-r\d+)")

DIFFICULTY_PRESETS = ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal")
SETTINGS_FILES = ("ServerGameSettings", "ServerHostSettings")


def parse_build_id(version_text: str) -> str:
    """Extract the build pin from the install's VERSION file contents.

    "VRising: v1.1.13.0-r99712-b17 (202605251526)" -> "1.1.13.0-r99712"
    """
    match = _BUILD_RE.search(version_text)
    if not match:
        raise ValueError(f"unparseable VERSION string: {version_text!r}")
    return match.group("build")


def resolve_codes(text: str, codes: dict[str, str]) -> str:
    """Substitute localization markup codes. Unknown codes are left untouched."""
    # Order dependent: if one key is a substring of another, whichever is
    # substituted first wins, and that order is the order of the "Codes" array
    # in the shipped English.json. No such overlap exists in build
    # 1.1.13.0-r99712, so this is a latent hazard, not a live bug - if a future
    # build introduces overlapping keys, substitute longest key first.
    for key, value in codes.items():
        if key in text:
            text = text.replace(key, value)
    return text


def load_localization(loc_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Read English.json into (strings_by_guid, codes).

    The file is UTF-8 with a BOM, hence utf-8-sig.
    """
    payload = json.loads(loc_path.read_text(encoding="utf-8-sig"))
    codes = {entry["Key"]: entry["Value"] for entry in payload.get("Codes", [])}
    strings = {
        entry["Guid"]: resolve_codes(entry.get("Text", ""), codes)
        for entry in payload.get("Nodes", [])
        if entry.get("Guid")
    }
    return strings, codes


def write_json_atomic(path: Path, payload: object) -> None:
    """Write JSON to path atomically. Consumers may poll mid-write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.replace(tmp, path)


def _copy_json(src: Path, dest: Path) -> None:
    """Re-serialize a shipped JSON file so output is normalized and stable."""
    write_json_atomic(dest, json.loads(src.read_text(encoding="utf-8-sig")))


def seed_tables(build_dir: Path, build: str) -> Path:
    """Create <build_dir>/tables/ and seed one empty envelope per table name.

    An existing table file is left EXACTLY as it is. The cycle 2 bridge dumps
    real rows into these same files, and a routine re-extract (a Steam update,
    or RM-DataRefresh) must never clobber a populated dump with an empty one.

    A file whose stem is not a known table name is a leftover from an older
    schema set and is deleted, so the directory never accumulates orphans that
    a consumer might read as live. Nothing is logged: this is a regenerable
    data directory, not a service.
    """
    tables_dir = build_dir / TABLES_DIRNAME
    tables_dir.mkdir(parents=True, exist_ok=True)

    for name in TABLE_NAMES:
        path = tables_dir / f"{name}.json"
        if path.exists():
            continue
        table = empty_table(name, build)
        problems = validate_table(table, load_schema(name))
        if problems:
            raise ValueError(f"seeded {name} table is invalid: {problems}")
        write_json_atomic(path, table)

    for path in tables_dir.iterdir():
        if path.is_file() and path.stem not in TABLE_NAMES:
            path.unlink()

    return tables_dir


def extract(install_root: Path, repo_root: Path) -> Path:
    """Extract the data floor. Returns the build directory written."""
    version_text = (install_root / "VERSION").read_text(encoding="utf-8").strip()
    build = parse_build_id(version_text)

    streaming = install_root / "VRising_Data" / "StreamingAssets"
    build_dir = repo_root / "data" / "rmdata" / build
    build_dir.mkdir(parents=True, exist_ok=True)

    strings, codes = load_localization(streaming / "Localization" / "English.json")
    write_json_atomic(build_dir / "strings.json", strings)
    write_json_atomic(build_dir / "codes.json", codes)

    for name in DIFFICULTY_PRESETS:
        _copy_json(
            streaming / "GameDifficultyPresets" / f"{name}.json",
            build_dir / "difficulty" / f"{name}.json",
        )

    for name in SETTINGS_FILES:
        _copy_json(
            streaming / "Settings" / f"{name}.json",
            build_dir / "settings" / f"{name}.json",
        )

    seed_tables(build_dir, build)

    write_json_atomic(
        build_dir / "meta.json",
        {
            "build": build,
            "version_string": version_text,
            "install_root": str(install_root),
            "string_count": len(strings),
            "code_count": len(codes),
            "schema_version": 1,
        },
    )

    pointer = repo_root / "data" / "rmdata" / "current.txt"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    tmp = pointer.with_name(pointer.name + ".tmp")
    tmp.write_text(build + "\n", encoding="utf-8")
    os.replace(tmp, pointer)

    return build_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract the V Rising data floor.")
    parser.add_argument("--install", type=Path, default=DEFAULT_INSTALL)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    if not args.install.is_dir():
        print(f"install not found: {args.install}", file=sys.stderr)
        return 1

    build_dir = extract(args.install, args.repo)
    meta = json.loads((build_dir / "meta.json").read_text(encoding="utf-8"))
    print(f"build {meta['build']}: {meta['string_count']} strings -> {build_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

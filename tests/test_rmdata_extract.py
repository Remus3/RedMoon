import hashlib
import json
from pathlib import Path

import pytest

from core.tables import TABLE_NAMES, TABLES_DIRNAME, load_schema, validate_table
from tools.rmdata_extract import (
    DEFAULT_INSTALL,
    extract,
    load_localization,
    parse_build_id,
    resolve_codes,
    write_json_atomic,
)

BUILD = "1.1.13.0-r99712"

FAKE_BUILD = "9.9.9.9-r12345"


@pytest.fixture
def fake_install(tmp_path):
    """Build a minimal but complete synthetic install tree under tmp_path.

    Mirrors the real install's shape so extract() gets real coverage of its
    own orchestration on machines without V Rising installed.
    """
    root = tmp_path / "fake_install"
    root.mkdir()
    (root / "VERSION").write_text(
        "VRising: v9.9.9.9-r12345-b01 (202601010000)", encoding="utf-8"
    )

    streaming = root / "VRising_Data" / "StreamingAssets"

    loc_dir = streaming / "Localization"
    loc_dir.mkdir(parents=True)
    (loc_dir / "English.json").write_text(
        json.dumps(
            {
                "Codes": [
                    {"Key": "</c>", "Value": "</color>", "Description": ""},
                    {"Key": "<red1>", "Value": "<color=#C52443>", "Description": ""},
                ],
                "Nodes": [
                    {"Guid": "guid-1", "Text": "<red1>Blood</c>"},
                    {"Guid": "guid-2", "Text": "Bear Form"},
                    {"Guid": "guid-3", "Text": "Wolf Form"},
                ],
            }
        ),
        encoding="utf-8-sig",
    )

    difficulty_dir = streaming / "GameDifficultyPresets"
    difficulty_dir.mkdir(parents=True)
    (difficulty_dir / "Difficulty_Easy.json").write_text(
        json.dumps({"Name": "Easy", "Multiplier": 0.5}), encoding="utf-8-sig"
    )
    (difficulty_dir / "Difficulty_Normal.json").write_text(
        json.dumps({"Name": "Normal", "Multiplier": 1.0}), encoding="utf-8-sig"
    )
    (difficulty_dir / "Difficulty_Brutal.json").write_text(
        json.dumps({"Name": "Brutal", "Multiplier": 2.0}), encoding="utf-8-sig"
    )

    settings_dir = streaming / "Settings"
    settings_dir.mkdir(parents=True)
    (settings_dir / "ServerGameSettings.json").write_text(
        json.dumps({"ServerName": "fake-game", "MaxPlayers": 40}),
        encoding="utf-8-sig",
    )
    (settings_dir / "ServerHostSettings.json").write_text(
        json.dumps({"ServerName": "fake-host", "Port": 9876}),
        encoding="utf-8-sig",
    )

    return root


def test_parse_build_id_from_the_real_version_string():
    assert parse_build_id("VRising: v1.1.13.0-r99712-b17 (202605251526)") == BUILD


def test_parse_build_id_rejects_garbage():
    with pytest.raises(ValueError):
        parse_build_id("not a version")


def test_resolve_codes_substitutes_known_markup():
    codes = {"</c>": "</color>", "<red1>": "<color=#C52443>"}
    assert resolve_codes("<red1>hot</c>", codes) == "<color=#C52443>hot</color>"


def test_resolve_codes_leaves_unknown_markup_untouched():
    assert resolve_codes("<mystery>x", {"</c>": "</color>"}) == "<mystery>x"


def test_load_localization_returns_strings_and_codes(tmp_path):
    src = tmp_path / "English.json"
    src.write_text(
        json.dumps(
            {
                "Codes": [{"Key": "</c>", "Value": "</color>", "Description": ""}],
                "Nodes": [{"Guid": "abc-123", "Text": "Bear Form</c>"}],
            }
        ),
        encoding="utf-8",
    )
    strings, codes = load_localization(src)
    assert codes == {"</c>": "</color>"}
    assert strings == {"abc-123": "Bear Form</color>"}


def test_write_json_atomic_leaves_no_temp_file(tmp_path):
    target = tmp_path / "out.json"
    write_json_atomic(target, {"a": 1})
    assert json.loads(target.read_text(encoding="utf-8")) == {"a": 1}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.json"]


def test_write_json_atomic_overwrites_cleanly(tmp_path):
    target = tmp_path / "out.json"
    write_json_atomic(target, {"a": 1})
    write_json_atomic(target, {"b": 2})
    assert json.loads(target.read_text(encoding="utf-8")) == {"b": 2}


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_produces_the_expected_layout(tmp_path):
    build_dir = extract(DEFAULT_INSTALL, tmp_path)
    assert build_dir.name == BUILD
    assert (build_dir / "strings.json").is_file()
    assert (build_dir / "codes.json").is_file()
    assert (build_dir / "meta.json").is_file()
    for name in ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal"):
        assert (build_dir / "difficulty" / f"{name}.json").is_file()
    for name in ("ServerGameSettings", "ServerHostSettings"):
        assert (build_dir / "settings" / f"{name}.json").is_file()
    current = (tmp_path / "data" / "rmdata" / "current.txt").read_text(encoding="utf-8")
    assert current.strip() == BUILD


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_populates_strings(tmp_path):
    build_dir = extract(DEFAULT_INSTALL, tmp_path)
    strings = json.loads((build_dir / "strings.json").read_text(encoding="utf-8"))
    assert len(strings) > 1000
    assert all(isinstance(k, str) and isinstance(v, str) for k, v in strings.items())


@pytest.mark.skipif(not DEFAULT_INSTALL.is_dir(), reason="V Rising not installed")
def test_extract_is_idempotent(tmp_path):
    def digest(root: Path) -> dict[str, str]:
        out = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return out

    first = digest(extract(DEFAULT_INSTALL, tmp_path))
    second = digest(extract(DEFAULT_INSTALL, tmp_path))
    assert first == second


def test_extract_against_fake_install_produces_the_expected_layout(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    assert build_dir.name == FAKE_BUILD
    assert (build_dir / "strings.json").is_file()
    assert (build_dir / "codes.json").is_file()
    assert (build_dir / "meta.json").is_file()
    for name in ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal"):
        assert (build_dir / "difficulty" / f"{name}.json").is_file()
    for name in ("ServerGameSettings", "ServerHostSettings"):
        assert (build_dir / "settings" / f"{name}.json").is_file()


def test_extract_against_fake_install_strings_match_load_localization(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    loc_path = (
        fake_install
        / "VRising_Data"
        / "StreamingAssets"
        / "Localization"
        / "English.json"
    )
    expected_strings, expected_codes = load_localization(loc_path)

    strings = json.loads((build_dir / "strings.json").read_text(encoding="utf-8"))
    codes = json.loads((build_dir / "codes.json").read_text(encoding="utf-8"))

    assert strings == expected_strings
    assert codes == expected_codes
    assert strings["guid-1"] == "<color=#C52443>Blood</color>"
    assert strings["guid-2"] == "Bear Form"
    assert strings["guid-3"] == "Wolf Form"


def test_extract_against_fake_install_difficulty_and_settings_round_trip(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    streaming = fake_install / "VRising_Data" / "StreamingAssets"

    for name in ("Difficulty_Easy", "Difficulty_Normal", "Difficulty_Brutal"):
        src = json.loads(
            (streaming / "GameDifficultyPresets" / f"{name}.json").read_text(
                encoding="utf-8-sig"
            )
        )
        out = json.loads(
            (build_dir / "difficulty" / f"{name}.json").read_text(encoding="utf-8")
        )
        assert out == src

    for name in ("ServerGameSettings", "ServerHostSettings"):
        src = json.loads(
            (streaming / "Settings" / f"{name}.json").read_text(encoding="utf-8-sig")
        )
        out = json.loads(
            (build_dir / "settings" / f"{name}.json").read_text(encoding="utf-8")
        )
        assert out == src


def test_extract_against_fake_install_meta_json_shape(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    meta = json.loads((build_dir / "meta.json").read_text(encoding="utf-8"))
    assert meta["build"] == FAKE_BUILD
    assert meta["string_count"] == 3
    assert meta["code_count"] == 2
    assert meta["schema_version"] == 1


def test_extract_against_fake_install_writes_current_pointer(fake_install, tmp_path):
    extract(fake_install, tmp_path)
    current = (tmp_path / "data" / "rmdata" / "current.txt").read_text(encoding="utf-8")
    assert current.strip() == FAKE_BUILD


def test_extract_against_fake_install_is_idempotent(fake_install, tmp_path):
    def digest(root: Path) -> dict[str, str]:
        out = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return out

    first = digest(extract(fake_install, tmp_path))
    second = digest(extract(fake_install, tmp_path))
    assert first == second


def test_extract_seeds_one_table_file_per_table_name(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    tables_dir = build_dir / TABLES_DIRNAME
    assert tables_dir.is_dir(), "extract did not create the tables/ seam"
    written = {p.stem for p in tables_dir.iterdir() if p.is_file()}
    assert written == set(TABLE_NAMES)


def test_every_seeded_table_file_validates_against_its_own_schema(fake_install, tmp_path):
    """docs/BLOODFORGE.md names these paths as cycle 3 inputs. Whatever extract
    puts there must already satisfy the schema the consumer will validate with,
    or cycle 2 inherits a seam that is wrong on its first read.
    """
    build_dir = extract(fake_install, tmp_path)
    tables_dir = build_dir / TABLES_DIRNAME
    for name in TABLE_NAMES:
        table = json.loads((tables_dir / f"{name}.json").read_text(encoding="utf-8"))
        problems = validate_table(table, load_schema(name))
        assert problems == [], f"{name}.json does not validate: {problems}"
        assert table["table"] == name
        assert table["build"] == FAKE_BUILD
        assert table["rows"] == []


def test_re_extract_never_clobbers_a_populated_table(fake_install, tmp_path):
    """A later bridge dump lands in these files. A routine re-extract - a Steam
    update, or the daily RM-DataRefresh - must leave a populated table alone.
    """
    build_dir = extract(fake_install, tmp_path)
    populated = build_dir / TABLES_DIRNAME / "items.json"

    dumped = json.loads(populated.read_text(encoding="utf-8"))
    dumped["rows"] = [
        {"prefab_guid": 12345, "name": "Copper Sword", "category": "weapon", "tier": 1}
    ]
    assert validate_table(dumped, load_schema("items")) == []
    write_json_atomic(populated, dumped)
    before = populated.read_bytes()

    extract(fake_install, tmp_path)

    assert populated.read_bytes() == before, "re-extract clobbered a populated table"
    assert json.loads(populated.read_text(encoding="utf-8"))["rows"] == dumped["rows"]


def test_re_extract_removes_a_table_file_with_an_unknown_name(fake_install, tmp_path):
    build_dir = extract(fake_install, tmp_path)
    stale = build_dir / TABLES_DIRNAME / "weapon_mods.json"
    stale.write_text('{"table": "weapon_mods"}', encoding="utf-8")

    extract(fake_install, tmp_path)

    assert not stale.exists(), "a table file from a retired schema survived a re-extract"
    assert {p.stem for p in (build_dir / TABLES_DIRNAME).iterdir()} == set(TABLE_NAMES)


def test_extract_is_idempotent_with_the_tables_present(fake_install, tmp_path):
    def digest(root: Path) -> dict[str, str]:
        out = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        return out

    first_dir = extract(fake_install, tmp_path)
    assert (first_dir / TABLES_DIRNAME).is_dir()
    first = digest(first_dir)
    second = digest(extract(fake_install, tmp_path))
    assert first == second
    assert any(f"{TABLES_DIRNAME}/" in rel for rel in first), (
        "the digest saw no table files - this idempotency check would be vacuous"
    )


def test_extract_raises_and_does_not_publish_pointer_on_missing_source(fake_install, tmp_path):
    missing = (
        fake_install
        / "VRising_Data"
        / "StreamingAssets"
        / "GameDifficultyPresets"
        / "Difficulty_Brutal.json"
    )
    missing.unlink()

    with pytest.raises(FileNotFoundError):
        extract(fake_install, tmp_path)

    assert not (tmp_path / "data" / "rmdata" / "current.txt").exists()

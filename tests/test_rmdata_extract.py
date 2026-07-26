import hashlib
import json
from pathlib import Path

import pytest

from tools.rmdata_extract import (
    DEFAULT_INSTALL,
    extract,
    load_localization,
    parse_build_id,
    resolve_codes,
    write_json_atomic,
)

BUILD = "1.1.13.0-r99712"


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

#!/usr/bin/env python3
"""Drive the RedMoon.Bridge recorder and write a VALIDATED anchor run.

Decision A of the falsification spec, on the Python side. The bridge records a
boss `Health.Value` time series on its own main-thread tick; this tool arms it,
stops it, translates what comes back into the anchor schema, builds the B.1
manifest, runs the A.5 validity checklist and writes the result atomically to
`data/anchors/<run_id>.json`.

WHAT THIS TOOL EXISTS TO PREVENT, stated before what it does:

* A run that cannot be told apart from another run. Two anchors are comparable
  only when their identity tuples agree (B.2), so a manifest that DEFAULTS a
  field it could not source is worse than one that omits it - the default makes
  two different subjects look identical. A.5.6 therefore discards a run whose
  manifest has a defaulted field, and every unsourceable field here is ABSENT
  and named in `known_holes`.
* A recording of the wrong subject. A spawned boss carries the SAME PrefabGUID
  as its prefab and the two do not agree; the prefab reads `Health.Value` 0, so
  a recorder latched onto it records a flat zero series that a naive reading
  turns into an instantaneous kill. Every sample restates `prefab_guid` and
  `carries_prefab_marker`, and a single marked sample DISCARDS the run.
* A per-hit number read out of a window that contained more than one hit. The
  sample rate is HOST-DEPENDENT and was never measured until 2026-08-01:
  `SampleEveryFrames = 15` (`Plugin.cs:41`) is a FRAME count, and the dedicated
  server samples at 1.99 Hz because it runs at 29.9 fps, against the 4 Hz both
  specs assume (ROADMAP gap 12). Abilities with `hits_per_cast` up to 4 exist
  and several land inside one window, so the per-hit gate runs over ISOLATED
  deltas only, and every threshold is derived from the series itself.

THE TRANSLATION IS NOT COSMETIC. The wire carries `blood_type_guid` as an int;
the anchor schema declares `blood_type` as a STRING and declares no guid field
at all. `core.tables.validate_table` rejects undeclared fields on ROWS
(`core/tables.py:89-92`), so a row that ships the guid through fails the gate.
The join goes through `tables/blood_types.json`, and an unjoinable guid yields
an ABSENT `blood_type` rather than a placeholder name.

WHAT VALIDATES THE ENVELOPE, and what deliberately does not: the five-key
envelope goes through `bloodforge.embargo.load_schema("anchor")` plus
`core.tables.validate_table`. `core.table_deep.deep_problems` CANNOT gate it -
that function raises KeyError for any name outside the frozen TABLE_NAMES tuple
(`core/table_deep.py:356-357`) and the anchor is not extracted game data. Both
facts are pinned by `tests/test_embargo.py`.

WHERE THE PURE SERIES FUNCTIONS LIVE. `parse_stamp`, `sample_intervals`,
`observed_cadence`, `per_hit_discard_reasons` and `isolated_deltas` are in
`bloodforge/series.py` and are RE-EXPORTED here. They used to live here and
`bloodforge/powerstat.py` imported them from a `tools/` script, which is the
wrong direction for an engine module. Duplicating them was the worse option:
two copies of the isolation rule can drift, and that is the exact failure mode
this protocol exists to catch. `tests/test_series.py` asserts the re-export by
IDENTITY, so a copy pasted back into this file fails loudly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Launched by absolute path, so sys.path[0] is tools/, not the repo root. Same
# idiom tools/bridge_probe.py already uses.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bloodforge import ENGINE_VERSION  # noqa: E402
from bloodforge.embargo import load_schema  # noqa: E402

# RE-EXPORTED, not re-implemented. See the layering note above; the identity of
# these objects with bloodforge.series' own is asserted by tests/test_series.py.
from bloodforge.series import (  # noqa: E402,F401
    GAP_TICK_MULTIPLE,
    isolated_deltas,
    observed_cadence,
    parse_stamp,
    per_hit_discard_reasons,
    sample_intervals,
)
from core import bridge_client, tables  # noqa: E402

REPO = Path(__file__).resolve().parents[1]

RMDATA_DIR = REPO / "data" / "rmdata"
ANCHOR_DIR = REPO / "data" / "anchors"
LOG_DIR = REPO / "logs"

TICK_INTERVAL_S = 0.25
"""A NOMINAL sample interval, for synthesizing offsets only. NOT a threshold.

The 4 Hz figure written throughout both specs is an INFERENCE from an assumed
60 fps and has never been measured on either host. MEASURED 2026-08-01 on a live
dedicated server: min 0.500 s, median 0.502 s, max 0.503 s over n=55 intervals,
which is 1.99 Hz. SampleEveryFrames = 15 (Plugin.cs:41) is right; the dedicated
server runs at 29.9 fps under -batchMode -nographics, so 15 frames is 502 ms. A
60 fps client should give about 4 Hz, and that is still unmeasured.

The rate is therefore a property of the HOST, not of the protocol, and nothing
in this module may treat it as a constant. Every threshold and every reported
cadence is derived from the series itself.
"""

ANCHOR_TABLE = "anchor"

ANCHOR_EPOCH = datetime(2026, 1, 1, tzinfo=UTC)
"""Reference instant for `stamp`, so a series can be described by OFFSETS alone.

The offsets are what matter to every consumer here - gap detection, isolation,
active time - and an absolute wall clock in a synthesized or replayed series is
noise that makes two identical series compare unequal.
"""

STAMP_SECONDS_FORMAT = "%Y-%m-%dT%H:%M:%S."
STAMP_SUBSECOND_DIGITS = 3
"""MILLISECONDS, matching the wire contract's yyyy-MM-ddTHH:mm:ss.fffZ.

Sub-second resolution is not decoration and this was measured, not reasoned: the
bridge envelope's whole-second stamp gave four consecutive samples the same
instant and destroyed every timing derived from the series. At a two-to-four
sample-per-second cadence a second-resolution stamp cannot distinguish a clean
run from a stalled tick.
"""

RUN_ID_STAMP_FORMAT = "%Y%m%dT%H%M%SZ"
"""ISO 8601 BASIC format for the run_id, because run_id is a Windows filename
stem and NTFS forbids the colon that the extended format uses."""

RUN_ID_HASH_CHARS = 12
NEGATIVE_GUID_PREFIX = "n"
"""A minus sign inside a dash-delimited identifier is ambiguous, and most V Blood
prefab guids are negative. The sign is carried as a leading letter so that
run_id.rsplit("-", 2) recovers exactly three parts."""

SEPARATOR_SAFE = re.compile(r"[A-Za-z0-9._-]+")
"""What may appear in a run_id, which is used directly as a filename stem."""

REQUIRED_MANIFEST_FIELDS = (
    "game_build",
    "game_version_string",
    "plugin_version",
    "bridge_host",
    "engine_version",
    "boss_prefab_guid",
    "boss_prefab_name",
    "boss_entity_index",
    "carries_prefab_marker",
    "boss_max_health_observed",
    "boss_resistances_observed",
    "boss_unit_level",
    "boss_level",
    "difficulty",
    "player_unit_level",
    "player_max_health",
    "player_unit_stats",
    "table_fingerprint",
    "observed_sample_rate_hz",
    "observed_sample_interval_s_median",
    "run_id",
)
"""Every B.1 field that HAS a source on this build. A.5.6 discards a run missing
any of them, naming the field, because a discarded run is recorded with its
reason and never repaired."""

ACKNOWLEDGED_HOLES = ("equipped_item_guids", "jewels_and_passives")
"""B.1 records these as KNOWN HOLES rather than as defaulted fields.

They are operator-supplied CLI inputs. jewels_and_passives is NOT ATTEMPTED as a
structured field - no jewel or passive source has been measured - and
equipped_item_guids is a MAP of slot to prefab_guid rather than a gear score
because gear_score is present on 117 of 425 item rows and on 0 of the 205
weapons, so a scalar gear level is not sourceable for the slot that matters most.

Their absence does not discard a run. It does keep the run from ever being
comparable to a subject under bloodforge.embargo._IDENTITY_KEYS, which is the
honest outcome: the embargo stays armed rather than lifting on an unidentified
loadout.
"""

FRIENDLY_ERRORS = {
    "subject_not_spawned": (
        "the boss is not spawned in the world yet, so nothing was recorded. "
        "Wait for the SUBJECT to appear rather than for a ready flag - the "
        "instance can take around twenty seconds to follow its prefab - then "
        "arm again."
    ),
    "already_recording": (
        "a recording is already armed. Stop it first, or check its progress "
        "with the status subcommand."
    ),
    "not_recording": "nothing is armed, so there is no series to stop.",
    "bad_request": (
        "the recorder rejected those arguments. Check the boss prefab guid "
        "against data/rmdata/<build>/tables/vbloods.json."
    ),
    "unreachable": (
        "no bridge answered. Start V Rising with the RedMoon.Bridge plugin "
        "loaded, or point RM_GAME_HOST at the machine running it."
    ),
}

GENERIC_ERROR = (
    "the bridge could not complete that request - the raw detail is in the "
    "log under logs/ and is deliberately not shown here."
)


# ---------------------------------------------------------------------------
# Time
# ---------------------------------------------------------------------------


def stamp(offset_s: float = 0.0, base: datetime | None = None) -> str:
    """Format a UTC instant `offset_s` seconds after `base` (default the epoch)."""
    moment = ((base or ANCHOR_EPOCH) + timedelta(seconds=offset_s)).astimezone(UTC)
    fraction = moment.microsecond // (10 ** (6 - STAMP_SUBSECOND_DIGITS))
    return (
        moment.strftime(STAMP_SECONDS_FORMAT)
        + f"{fraction:0{STAMP_SUBSECOND_DIGITS}d}Z"
    )


# ---------------------------------------------------------------------------
# Disk sources. Every one of these is a SOURCE; nothing here invents a value.
# ---------------------------------------------------------------------------


def current_build() -> str:
    return (RMDATA_DIR / "current.txt").read_text(encoding="utf-8").strip()


def build_dir(build: str | None = None) -> Path:
    return RMDATA_DIR / (build or current_build())


def load_meta(build: str | None = None) -> dict:
    """data/rmdata/<build>/meta.json - the build pin and the version string.

    The b-number and timestamp in version_string distinguish two installs
    sharing a pin, which a build pin alone cannot.
    """
    return json.loads((build_dir(build) / "meta.json").read_text(encoding="utf-8"))


def load_table(name: str, build: str | None = None) -> dict:
    path = build_dir(build) / tables.TABLES_DIRNAME / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_blood_type_names(build: str | None = None) -> dict[int, str]:
    """prefab_guid to name over the 13 promoted blood_types rows.

    NAMES ONLY, and that is the whole content of the table: every magnitude is
    scaled from blood quality at runtime and none are on the prefab, so the
    blood contribution is DECLARED AND OMITTED from computation.
    """
    rows = load_table("blood_types", build)["rows"]
    return {row["prefab_guid"]: row["name"] for row in rows if "prefab_guid" in row}


def vblood_level(prefab_guid: int, build: str | None = None) -> int | None:
    """Join a boss guid to tables/vbloods.json for its level, or None.

    None rather than 0. vbloods.json is implicitly a NORMAL table - boss level,
    power and health are all difficulty-scaled - which is why the manifest also
    carries the verbatim difficulty object beside this.
    """
    for row in load_table("vbloods", build)["rows"]:
        if row.get("prefab_guid") == prefab_guid:
            return row.get("level")
    return None


def read_difficulty(name: str, build: str | None = None) -> tuple[dict, dict]:
    """Return (V Blood modifier block, the whole file) read VERBATIM.

    Never a label. Brutal sets V Blood MaxHealthModifier 1.25, PowerModifier 1.7
    and LevelIncrease 3 against Normal's 1.0, 1.0 and 0, and a server may
    override any of them independently of its GameDifficulty string - the
    shipped ServerGameSettings.json carries GameDifficulty "Normal" alongside
    separately settable modifier blocks. So the object is recorded, not the name.
    """
    path = build_dir(build) / "difficulty" / f"Difficulty_{name}.json"
    whole = json.loads(path.read_text(encoding="utf-8"))
    return whole.get("UnitStatModifiers_VBlood", {}), whole


def table_fingerprint(build: str | None = None) -> dict[str, dict]:
    """The six promoted tables with schema_version and row count, COUNTED.

    Counted from disk rather than copied from any document, because copying is
    how this project has three times recorded a number that the rows disagreed
    with. A later re-check that finds a different fingerprint is comparing a
    different input set and may not be pooled.
    """
    fingerprint: dict[str, dict] = {}
    for name in tables.TABLE_NAMES:
        table = load_table(name, build)
        fingerprint[name] = {
            "rows": len(table["rows"]),
            "schema_version": table["schema_version"],
        }
    return fingerprint


# ---------------------------------------------------------------------------
# Wire to schema
# ---------------------------------------------------------------------------


def _anchor_row_fields() -> frozenset[str]:
    return frozenset(load_schema(ANCHOR_TABLE)["fields"])


def translate_samples(
    wire_samples: Iterable[Mapping],
    blood_type_names: Mapping[int, str],
) -> list[dict]:
    """Translate wire samples into anchor rows.

    Three things happen and each one is load-bearing:

    1. blood_type_guid (int, on the wire) becomes blood_type (string, in the
       schema) through the 13-row join. An unjoinable guid drops the field
       entirely rather than inventing a name.
    2. Any field the schema does not declare is dropped, because validate_table
       rejects undeclared fields on ROWS and a rejected envelope is not written.
    3. A field the wire OMITTED stays omitted. The last four sample fields are
       absent when the character could not be resolved that tick, and a zero
       player health is a real and different statement from an unresolved one.
    """
    declared = _anchor_row_fields()
    rows: list[dict] = []
    for sample in wire_samples:
        row = {key: value for key, value in sample.items() if key in declared}
        guid = sample.get("blood_type_guid")
        if guid is not None:
            name = blood_type_names.get(guid)
            if name is not None:
                row["blood_type"] = name
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# The B.1 manifest
# ---------------------------------------------------------------------------


def _canonical(payload: Mapping) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def manifest_hash(manifest: Mapping) -> str:
    """A short digest over the manifest with run_id excluded.

    Excluded because run_id contains the digest. Any other field moving moves
    the digest, which is what makes a run_id a statement about its own contents
    rather than a timestamp with decoration.
    """
    without = {key: value for key, value in manifest.items() if key != "run_id"}
    digest = hashlib.sha256(_canonical(without).encode("utf-8")).hexdigest()
    return digest[:RUN_ID_HASH_CHARS]


def _guid_token(guid: int) -> str:
    return str(guid).replace("-", NEGATIVE_GUID_PREFIX)


def make_run_id(manifest: Mapping, captured_at: str) -> str:
    """`<utc_iso8601_basic>-<boss_prefab_guid>-<short_hash_of_manifest>`."""
    when = parse_stamp(captured_at).astimezone(UTC).strftime(RUN_ID_STAMP_FORMAT)
    guid = _guid_token(int(manifest.get("boss_prefab_guid", 0)))
    return f"{when}-{guid}-{manifest_hash(manifest)}"


def build_manifest(
    start_run: Mapping,
    meta: Mapping,
    health: Mapping,
    fingerprint: Mapping,
    difficulty: Mapping | None = None,
    difficulty_verbatim: Mapping | None = None,
    boss_level: int | None = None,
    equipped_item_guids: Mapping | None = None,
    jewels_and_passives: str | None = None,
    operator_note: str | None = None,
    captured_at: str | None = None,
    build: str | None = None,
    rows: Sequence[Mapping] | None = None,
) -> dict:
    """Assemble the B.1 manifest. ANY FIELD THAT CANNOT BE SOURCED IS OMITTED.

    Never defaulted. A.5.6 discards a run whose manifest has a defaulted field,
    and the reason is not pedantry: the identity tuple in B.2 decides which runs
    may be pooled, so a defaulted field silently makes two different subjects
    look like two samples of one. Every omission is named in `known_holes`, so
    the hole is a statement rather than a silence.
    """
    manifest: dict = {}

    def put(key: str, value) -> None:
        if value is not None:
            manifest[key] = value

    put("game_build", meta.get("build"))
    put("game_version_string", meta.get("version_string"))
    put("plugin_version", health.get("plugin"))
    put("bridge_host", health.get("host"))
    manifest["engine_version"] = ENGINE_VERSION

    for key in (
        "boss_prefab_guid",
        "boss_prefab_name",
        "boss_entity_index",
        "carries_prefab_marker",
        "boss_max_health_observed",
        "boss_health_value_at_arm",
        "boss_resistances_observed",
        "boss_unit_level",
    ):
        put(key, start_run.get(key))

    guid = start_run.get("boss_prefab_guid")
    if boss_level is None and guid is not None:
        try:
            boss_level = vblood_level(int(guid), build)
        except (OSError, ValueError, KeyError):
            boss_level = None
    put("boss_level", boss_level)

    put("difficulty", dict(difficulty) if difficulty else None)
    put("difficulty_verbatim", dict(difficulty_verbatim) if difficulty_verbatim else None)

    for key in ("player_unit_level", "player_max_health", "player_unit_stats"):
        put(key, start_run.get(key))
    put("player_resolved", start_run.get("player_resolved"))

    put("equipped_item_guids", dict(equipped_item_guids) if equipped_item_guids else None)
    put("jewels_and_passives", jewels_and_passives or None)

    manifest["table_fingerprint"] = dict(fingerprint)

    # MEASURED from the series, never from a constant. 1.99 Hz on the dedicated
    # server against the 4 Hz both specs assume - the rate is frames-per-sample
    # times the HOST's frame rate, and the two hosts do not share one.
    cadence = observed_cadence(rows or [])
    for key in (
        "observed_sample_rate_hz",
        "observed_sample_interval_s_median",
        "observed_sample_interval_s_min",
        "observed_sample_interval_s_max",
    ):
        put(key, cadence.get(key))

    put("operator_note", operator_note or start_run.get("operator_note"))

    manifest["known_holes"] = sorted(
        name
        for name in (*REQUIRED_MANIFEST_FIELDS, *ACKNOWLEDGED_HOLES)
        if name != "run_id" and name not in manifest
    )

    when = captured_at or stamp(base=datetime.now(UTC))
    manifest["run_id"] = make_run_id(manifest, when)
    return manifest


def manifest_problems(manifest: Mapping) -> list[str]:
    """A.5.6, one named reason per missing REQUIRED field.

    The two ACKNOWLEDGED_HOLES are not required: B.1 records them as known holes
    rather than as defaulted fields, and a run without them is valid but never
    comparable, which the embargo already enforces on its own.
    """
    return [
        f"manifest_incomplete:{name}"
        for name in REQUIRED_MANIFEST_FIELDS
        if manifest.get(name) is None
    ]


# ---------------------------------------------------------------------------
# The A.5 validity checklist. Named reasons, never a bool.
# ---------------------------------------------------------------------------


def check_run(
    rows: Sequence[Mapping],
    queried_guid: int | None = None,
    manifest: Mapping | None = None,
) -> dict:
    """The full A.5 checklist over a series.

    Returns named REASONS rather than a bool, plus MARKS, because A.5 has two
    different kinds of failure and collapsing them loses the useful one. A
    reason discards the run; a mark narrows what the run may be used for. A
    discarded run is recorded WITH ITS REASON and never repaired.
    """
    reasons = per_hit_discard_reasons(rows, queried_guid)
    marks: list[str] = []

    if not rows:
        reasons.append("empty_series")
    else:
        first = rows[0]
        if first.get("health_value") != first.get("health_max"):
            marks.append("partial")

        terminal = any(
            (row.get("health_value") is not None and row["health_value"] <= 0)
            or row.get("is_dead") is True
            for row in rows
        )
        if not terminal:
            reasons.append("no_terminal_sample")

    if manifest is not None:
        reasons.extend(manifest_problems(manifest))

    result = {"reasons": reasons, "marks": marks, "valid": not reasons}
    result.update(observed_cadence(rows))
    return result


# ---------------------------------------------------------------------------
# The envelope and the atomic write
# ---------------------------------------------------------------------------


def build_envelope(rows: Sequence[Mapping], manifest: Mapping, build: str | None = None) -> dict:
    """The FIVE-key envelope: table, build, schema_version, rows AND manifest.

    The fifth key was reasoned and is now probed (tests/test_embargo.py):
    validate_table requires the four and rejects undeclared fields on ROWS only,
    so an extra envelope key passes. Keeping the manifest in the same file as
    the series means a run cannot be separated from the statement of what it
    measured.
    """
    schema = load_schema(ANCHOR_TABLE)
    return {
        "table": ANCHOR_TABLE,
        "build": build or current_build(),
        "schema_version": schema["schema_version"],
        "rows": [dict(row) for row in rows],
        "manifest": dict(manifest),
    }


def write_anchor(envelope: Mapping, directory: Path | str | None = None) -> Path:
    """Validate, then write atomically to <directory>/<run_id>.json.

    Validation first, and nothing is written on failure: a rejected envelope on
    disk would be indistinguishable from an accepted one to load_anchors, which
    is how an unvalidated run would end up lifting an embargo.

    Atomic per the CLAUDE.md rule - a temp file in the DESTINATION directory,
    then os.replace - because consumers poll mid-write.
    """
    problems = tables.validate_table(dict(envelope), load_schema(ANCHOR_TABLE))
    if problems:
        raise ValueError("anchor envelope is invalid: " + "; ".join(problems))

    target_dir = Path(directory) if directory is not None else ANCHOR_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    run_id = envelope.get("manifest", {}).get("run_id")
    if not run_id or not SEPARATOR_SAFE.fullmatch(str(run_id)):
        raise ValueError(f"manifest carries no usable run_id ({run_id!r})")

    target = target_dir / f"{run_id}.json"
    temp = target_dir / f".{run_id}.json.tmp"
    temp.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, target)
    return target


# ---------------------------------------------------------------------------
# Degraded mode. A raw HTTP or API string never reaches the operator.
# ---------------------------------------------------------------------------


def friendly_error(payload: Mapping) -> str:
    """Map a bridge error envelope to an operator-facing message.

    PURE - it does no IO, so a caller decides when the raw detail is logged. Per
    the CLAUDE.md error-handling rule the raw string never reaches a user
    surface: an unrecognised code degrades to GENERIC_ERROR rather than being
    echoed, because an echoed body is how a status line ends up carrying an HTML
    error page.
    """
    code = payload.get("error")
    if isinstance(code, str) and code in FRIENDLY_ERRORS:
        return FRIENDLY_ERRORS[code]
    return GENERIC_ERROR


def log_raw(detail: str) -> None:
    """Append the raw detail to logs/YYYY-MM-DD.log. Best effort by design.

    D.5: the embargo does not cover diagnostics under logs/. A model whose
    numbers cannot be looked at cannot be debugged. A failure to log must never
    become the reason a recording is lost, so this swallows its own IO errors.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        day = datetime.now(UTC).strftime("%Y-%m-%d")
        line = f"{stamp(base=datetime.now(UTC))} anchor_record {detail}\n"
        with (LOG_DIR / f"{day}.log").open("a", encoding="utf-8") as handle:
            handle.write(line)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# The bridge calls
# ---------------------------------------------------------------------------


class RecorderError(RuntimeError):
    """A recorder call that did not succeed, carrying only a friendly message."""


def _call(host: str, path: str, query: dict[str, str] | None = None) -> dict:
    try:
        payload = bridge_client.get_json(host, path, query)
    except bridge_client.BridgeUnreachable as exc:
        log_raw(f"{path} unreachable: {exc}")
        raise RecorderError(FRIENDLY_ERRORS["unreachable"]) from None
    if not isinstance(payload, Mapping) or not payload.get("ok"):
        detail = payload if isinstance(payload, Mapping) else {"error": "malformed"}
        log_raw(f"{path} returned {json.dumps(payload, default=str)}")
        raise RecorderError(friendly_error(detail))
    return dict(payload)


def record_start(host: str, guid: int, note: str = "") -> dict:
    return _call(host, "/record/start", {"guid": str(guid), "note": note})


def record_status(host: str) -> dict:
    return _call(host, "/record/status")


def record_stop(host: str) -> dict:
    return _call(host, "/record/stop")


def health(host: str) -> dict:
    return _call(host, "/health")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _describe(result: Mapping) -> str:
    reasons = result.get("reasons") or []
    marks = result.get("marks") or []
    if reasons:
        return "DISCARDED - " + ", ".join(reasons)
    return "VALID" + (f" - marked {', '.join(marks)}" if marks else "")


def cmd_start(args: argparse.Namespace) -> int:
    payload = record_start(args.host, args.guid, args.note)
    run = payload.get("run", {})
    print(
        f"armed on {run.get('boss_prefab_name')} "
        f"({run.get('boss_prefab_guid')}) entity {run.get('boss_entity_index')}"
    )
    print(
        f"max health observed {run.get('boss_max_health_observed')} - "
        f"health at arm {run.get('boss_health_value_at_arm')}"
    )
    if not run.get("player_resolved"):
        print("NOTE: the player character did not resolve, so the EHP gate has no input.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    payload = record_status(args.host)
    print(
        f"armed={payload.get('armed')} guid={payload.get('guid')} "
        f"samples={payload.get('sample_count')} dropped={payload.get('dropped')} "
        f"since={payload.get('started_at')}"
    )
    return 0


def cmd_stop(args: argparse.Namespace) -> int:
    payload = record_stop(args.host)
    build = args.build or current_build()

    difficulty, verbatim = (None, None)
    if args.difficulty:
        try:
            difficulty, verbatim = read_difficulty(args.difficulty, build)
        except OSError as exc:
            log_raw(f"difficulty read failed: {exc}")
            print(
                "the difficulty file could not be read, so the run is written "
                "without it and is not comparable to any subject."
            )

    equipped = json.loads(args.equipped) if args.equipped else None
    rows = translate_samples(payload.get("samples", []), load_blood_type_names(build))

    manifest = build_manifest(
        start_run=payload,
        meta=load_meta(build),
        health=health(args.host),
        fingerprint=table_fingerprint(build),
        difficulty=difficulty,
        difficulty_verbatim=verbatim,
        equipped_item_guids=equipped,
        jewels_and_passives=args.jewels,
        operator_note=args.note,
        build=build,
        rows=rows,
    )
    envelope = build_envelope(rows, manifest, build)

    result = check_run(rows, payload.get("boss_prefab_guid"), manifest)
    envelope["manifest"]["validity"] = result
    envelope["manifest"]["run_id"] = manifest["run_id"]

    path = write_anchor(envelope, args.out)
    print(f"wrote {path}")
    print(f"{len(rows)} samples, {payload.get('dropped', 0)} dropped")
    rate = result.get("observed_sample_rate_hz")
    print(
        f"observed cadence {rate:.2f} Hz "
        f"(median interval {result['observed_sample_interval_s_median']:.3f} s)"
        if rate
        else "observed cadence UNKNOWN - too few stamped samples to measure one"
    )
    print(f"{len(isolated_deltas(rows))} isolated deltas")
    print(_describe(result))
    if manifest.get("known_holes"):
        print("known holes: " + ", ".join(manifest["known_holes"]))
    return 0 if result["valid"] else 1


def _load_envelope(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def cmd_validate(args: argparse.Namespace) -> int:
    envelope = _load_envelope(args.file)
    problems = tables.validate_table(envelope, load_schema(ANCHOR_TABLE))
    for problem in problems:
        print(f"schema: {problem}")
    manifest = envelope.get("manifest", {})
    result = check_run(
        envelope.get("rows", []),
        manifest.get("boss_prefab_guid"),
        manifest,
    )
    print(_describe(result))
    return 0 if result["valid"] and not problems else 1


def cmd_isolate(args: argparse.Namespace) -> int:
    envelope = _load_envelope(args.file)
    deltas = isolated_deltas(envelope.get("rows", []))
    for delta in deltas:
        print(f"{delta['index']:>6}  {delta['captured_at']}  {delta['delta']}")
    print(f"{len(deltas)} isolated deltas of {len(envelope.get('rows', []))} samples")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anchor_record",
        description=(
            "Drive the RedMoon.Bridge recorder and write a validated anchor run. "
            "The bridge host is named, never its port - ADR-005 makes the port a "
            "pure function of the host and core/ports.py is the one place it is "
            "written down."
        ),
    )
    parser.add_argument(
        "--host",
        default=bridge_client.ports.BRIDGE_HOSTS[0],
        choices=bridge_client.ports.BRIDGE_HOSTS,
        help="which V Rising host the bridge is loaded into",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="arm the recorder on a boss")
    start.add_argument("--guid", type=int, required=True, help="boss prefab guid")
    start.add_argument("--note", default="", help="what the operator is trying to do")
    start.set_defaults(func=cmd_start)

    status = subparsers.add_parser("status", help="how the armed recording is going")
    status.set_defaults(func=cmd_status)

    stop = subparsers.add_parser("stop", help="stop, translate, validate and write")
    stop.add_argument("--out", default=str(ANCHOR_DIR), help="output directory")
    stop.add_argument("--build", default=None, help="override the build pin")
    stop.add_argument(
        "--difficulty",
        default=None,
        help=(
            "which Difficulty_<name>.json the world was running. Recorded "
            "VERBATIM as an object. Omitted rather than guessed, and a run "
            "without it is never comparable to any subject."
        ),
    )
    stop.add_argument(
        "--equipped",
        default=None,
        help='JSON map of slot to item prefab_guid, e.g. \'{"weapon": -1173681254}\'',
    )
    stop.add_argument(
        "--jewels",
        default=None,
        help="free-text jewels and passives note. NOT ATTEMPTED as a structured field.",
    )
    stop.add_argument("--note", default=None, help="operator note for the manifest")
    stop.set_defaults(func=cmd_stop)

    validate = subparsers.add_parser("validate", help="offline A.5 checklist over a written run")
    validate.add_argument("file")
    validate.set_defaults(func=cmd_validate)

    isolate = subparsers.add_parser("isolate", help="offline isolated-delta extraction")
    isolate.add_argument("file")
    isolate.set_defaults(func=cmd_isolate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except RecorderError as exc:
        print(str(exc))
        return 2
    except (OSError, ValueError) as exc:
        log_raw(f"{args.command} failed: {exc}")
        print(GENERIC_ERROR)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

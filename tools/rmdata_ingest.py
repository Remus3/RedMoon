#!/usr/bin/env python3
"""Ingest the RedMoon.Bridge prefab dump into the versioned table directory.

The plugin serves rows over HTTP and never writes into C:\\RedMoon (spec
decision D3). Every envelope, every gate and every file write lives here, on the
Python side, exactly once.

The pipeline is spec section 7, in order:

  1. read data/rmdata/current.txt              -> expected build
  2. compare with the dump's "build" field     -> REFUSE on mismatch
  3. wrap rows with core.tables.empty_table    -> envelope from the frozen module
  4. write <build>/tables/_incoming/<name>.json            (atomic)
  5. core.tables.validate_table                -> SHALLOW gate, must be clean
  6. core.table_deep.deep_problems             -> NESTED gate, must be clean
  7. print the shape census                    -> operator reads it once
  8. --accept only:
     promote _incoming/<name>.json -> tables/<name>.json   (atomic)
  9. --accept only: empty _incoming/, so PROMOTED and PENDING are
     distinguishable on disk. A refused or unaccepted run leaves it populated.

Two properties are worth naming out loud.

The build cross-check at step 2 is what makes it impossible to ingest a dump
from a silently-updated game into the previous build's directory, so it runs
before anything at all is created on disk.

The census at step 7 is the point of the FIRST ingest, which is a discovery
event and not a confirmation. validate_table is shallow and cannot see inside
recipes.ingredients, blood_types.bonuses or items.stats, so a clean pass proves
nothing about nested shape. The census reports what was actually observed - key
sets, value types per key, cardinality, and the numeric range of every numeric
key - and the operator reads it once and either confirms the documented contract
or amends core/table_deep.py and the schema description. The census is a pure
function returning a structure; printing sits on top of it.

_incoming/ is a DIRECTORY. tools/rmdata_extract.seed_tables deletes files in
tables/ whose stem is not a known table name, but it guards on path.is_file(),
so the two do not collide. tests/test_rmdata_ingest.py proves that by running
seed_tables rather than by reading it.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Run as a script, sys.path[0] is tools/, not the repo root. Bootstrap the root
# before importing anything from core.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.bridge_client import BridgeUnreachable, get_json  # noqa: E402
from core.ports import BRIDGE_HOSTS  # noqa: E402
from core.table_deep import deep_problems  # noqa: E402
from core.tables import (  # noqa: E402
    TABLE_NAMES,
    TABLES_DIRNAME,
    empty_table,
    load_schema,
    validate_table,
)
from tools.rmdata_extract import parse_build_id, write_json_atomic  # noqa: E402

INCOMING_DIRNAME = "_incoming"
"""Quarantine subdirectory of tables/. Nothing reaches the live path unaccepted."""

DUMP_PATH = "/dump/prefabs"

DEFAULT_HOST = "server"

UNMAPPED_SAMPLE = 5

EXIT_OK = 0
EXIT_REFUSED = 1
EXIT_INVALID = 2


# ---------------------------------------------------------------------------
# build resolution
# ---------------------------------------------------------------------------


def normalize_build(text: str) -> str:
    """Return a bare build id from either a bare id or a full VERSION string.

    current.txt holds "1.1.13.0-r99712". An operator pasting the install's
    VERSION line instead would hold "VRising: v1.1.13.0-r99712-b17 (...)".
    parse_build_id handles the second form and raises on the first, so the bare
    form is the fallback. Both sides of the build comparison go through here, so
    the comparison is always like for like.
    """
    text = text.strip()
    try:
        return parse_build_id(text)
    except ValueError:
        return text


def read_expected_build(repo_root: Path) -> str:
    """Read data/rmdata/current.txt. Raises FileNotFoundError when absent."""
    pointer = repo_root / "data" / "rmdata" / "current.txt"
    return normalize_build(pointer.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# shape census - pure functions, printing lives further down
# ---------------------------------------------------------------------------


def _is_number(value: object) -> bool:
    """True for an int or float that is not a bool. bool is a subclass of int."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _key_slot(keys: dict, key: str) -> dict:
    return keys.setdefault(key, {"count": 0, "types": set(), "min": None, "max": None})


def _record_key(keys: dict, key: str, value: object) -> None:
    """Fold one observed key/value into the per-key census."""
    slot = _key_slot(keys, str(key))
    slot["count"] += 1
    slot["types"].add(type(value).__name__)
    if _is_number(value):
        slot["min"] = value if slot["min"] is None else min(slot["min"], value)
        slot["max"] = value if slot["max"] is None else max(slot["max"], value)


def _field_slot(fields: dict, path: str) -> dict:
    return fields.setdefault(
        path,
        {
            "container_kinds": set(),
            "entry_kinds": set(),
            "occurrences": 0,
            "cardinality": {"min": None, "max": None, "total": 0},
            "keys": {},
        },
    )


def _observe(fields: dict, path: str, value: object) -> None:
    """Fold one nested container into the census, recursing one level.

    A list of objects whose entries themselves carry a container - the shape
    blood_types.bonuses has, with a stats mapping per tier - is censused under a
    "bonuses[].stats" path, so nesting is reported rather than flattened away.
    """
    slot = _field_slot(fields, path)
    slot["occurrences"] += 1
    slot["container_kinds"].add(type(value).__name__)

    size = len(value)
    card = slot["cardinality"]
    card["total"] += size
    card["min"] = size if card["min"] is None else min(card["min"], size)
    card["max"] = size if card["max"] is None else max(card["max"], size)

    if isinstance(value, dict):
        for key, entry in value.items():
            _record_key(slot["keys"], key, entry)
        return

    for entry in value:
        slot["entry_kinds"].add(type(entry).__name__)
        if isinstance(entry, dict):
            for key, sub in entry.items():
                _record_key(slot["keys"], key, sub)
                if isinstance(sub, (dict, list)):
                    _observe(fields, f"{path}[].{key}", sub)


def _finalize(fields: dict) -> dict:
    """Turn the accumulating sets into sorted lists and sort every mapping."""
    result = {}
    for path in sorted(fields):
        slot = fields[path]
        result[path] = {
            "container_kinds": sorted(slot["container_kinds"]),
            "entry_kinds": sorted(slot["entry_kinds"]),
            "occurrences": slot["occurrences"],
            "cardinality": slot["cardinality"],
            "keys": {
                key: {
                    "count": slot["keys"][key]["count"],
                    "types": sorted(slot["keys"][key]["types"]),
                    "min": slot["keys"][key]["min"],
                    "max": slot["keys"][key]["max"],
                }
                for key in sorted(slot["keys"])
            },
        }
    return result


def shape_census(tables: dict[str, list]) -> dict[str, dict]:
    """Return the observed shape of every nested container in every table.

    Per table, per nested field path: the observed key set, the observed value
    types per key, the cardinality, and the min and max of each numeric key.
    Observation only - this function judges nothing.
    """
    census: dict[str, dict] = {}
    for name in sorted(tables):
        rows = tables[name]
        if not isinstance(rows, list):
            continue
        fields: dict = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            for field, value in row.items():
                if isinstance(value, (dict, list)):
                    _observe(fields, field, value)
        if fields:
            census[name] = _finalize(fields)
    return census


def unmapped_summary(payload: dict, sample_size: int = UNMAPPED_SAMPLE) -> dict:
    """Report the dump's unmapped array. A prefab the dumper could not classify.

    Never silently dropped: on the first dump the size of unmapped is the single
    most informative signal about how much of the game the dumper understands.
    """
    entries = payload.get("unmapped")
    if not isinstance(entries, list):
        return {"count": 0, "sample": [], "present": False}
    return {"count": len(entries), "sample": entries[:sample_size], "present": True}


def duplicate_key_problems(tables: dict[str, list]) -> list[str]:
    """Report any table that repeats a prefab_guid.

    MEASURED 2026-07-26: the dump emitted 56 ability rows over 54 distinct guids
    on BOTH hosts, and 66 vblood rows over 65 distinct on the server. Every
    duplicate pair was byte-identical, so no shape gate and no deep gate could
    see it - the rows were individually valid and the COUNT was the lie. 66 had
    already been written down as the V Blood total.

    prefab_guid is the join key cycle 3 will index on. Identical duplicates are
    not benign: they double-count, and a consumer building a dict silently keeps
    whichever row it read last.

    A row with no prefab_guid is skipped rather than folded in with the other
    keyless rows. That is the shallow gate's error to report, and collapsing
    them here would hide it behind a bogus collision.
    """
    problems: list[str] = []
    for name in sorted(tables):
        rows = tables[name]
        if not isinstance(rows, list):
            continue
        seen: dict[object, int] = {}
        for row in rows:
            if not isinstance(row, dict) or "prefab_guid" not in row:
                continue
            guid = row["prefab_guid"]
            seen[guid] = seen.get(guid, 0) + 1
        repeated = sorted((guid, n) for guid, n in seen.items() if n > 1)
        for guid, n in repeated:
            problems.append(
                f"{name}: prefab_guid {guid} appears {n} times - the key must be unique"
            )
    return problems


EXPECTED_ROWS_BUILD = "1.1.13.0-r99712"
"""The build EXPECTED_ROWS was measured on.

A row count is a fact about ONE build, not about V Rising. Pinning the counts
without pinning the build they came from would make the gate assert 425 items
against a game that had since shipped more, which is the cycle 2 lesson exactly:
a real measurement answering the right question about the wrong subject.

So the gate applies only to this build, and on any other build it stands down
and SAYS SO in the census rather than passing quietly. A silent stand-down would
read as "the counts were checked", which is the failure this whole gate exists
to prevent.
"""

EXPECTED_ROWS = {
    "items": 425,
    "recipes": 663,
    "abilities": 54,
    "vbloods": 65,
    "blood_types": 13,
    "ability_stats": 1818,
}
"""The row count each table must have on build 1.1.13.0-r99712.

WHY A CONSTANT AND NOT A REPORTED NUMBER. Four per-row gates - the shallow
schema, the deep nested contract, the census and the unmapped array - all passed
a dump that emitted 66 vblood rows over 65 distinct guids. Every duplicate pair
was byte-identical, so each individual row was perfect and the only symptom was
the COUNT; by then 66 had already been written into ROADMAP.md as the V Blood
total. A count that is merely whatever the dumper emitted asserts nothing.

The first five are the cycle 2 measurements, re-confirmed on both hosts after the
dedupe fix.

ability_stats is pinned at the count its FIRST run MEASURED, 2026-08-01 on the
dedicated server, together with the chain that produced it: one row per entity
carrying DynamicBuffer<ProjectM.AbilityGroupStartAbilitiesBuffer>, which is what
MAKES an entity an ability group. Coefficient fields are omitted on the groups
that reach no damage prefab rather than the rows being dropped, so this is the
GROUP population and not the damage-dealing subset: 732 of the 1818 reach damage.

THE NUMBER WAS PREDICTED AS 1474 AND MEASURED AS 1818, and the gap is the whole
reason this pin has to be a measurement. 1474 is cycle 2's figure and it counted
a NAME-selected population - prefabs whose name ends `_AbilityGroup`, of which
this dump finds 1476. The other 341 rows carry the buffer under a different
naming convention (`_Group`, `_Abilitygroup`, `_UNUSED` and others) and are
ability groups by COMPONENT, which is the selector this project's own rule
prefers: a marker component is a fact, a name suffix is a guess about Stunlock's
conventions. NOT RECONCILED and stated rather than smoothed over: 1476 is two
above cycle 2's 1474, and nothing in this dump explains the two.

The assertion exists to catch DRIFT tomorrow, which is a different job from
validating today's dump.

A build bump moves these numbers, and moving them is meant to be a deliberate
edit here rather than a silent pass.
"""


def count_applies(build: str) -> bool:
    """True when the pinned counts describe the build being ingested."""
    return normalize_build(build) == EXPECTED_ROWS_BUILD


def format_counts(tables: dict[str, list], build: str) -> list[str]:
    """Render the count gate's verdict, including when it stood down.

    Printed on every ingest. The stand-down line is the point: an operator who
    sees no count output at all cannot tell a passing gate from an absent one.
    """
    observed = ", ".join(f"{name}={len(tables[name])}" for name in sorted(tables)
                         if isinstance(tables[name], list))
    if not count_applies(build):
        return [
            f"counts: {observed}",
            f"  NOT ASSERTED - the pinned counts were measured on "
            f"{EXPECTED_ROWS_BUILD} and this dump is {normalize_build(build)}",
        ]
    return [f"counts: {observed}", f"  asserted against the {EXPECTED_ROWS_BUILD} pin"]


def count_problems(tables: dict[str, list], build: str = EXPECTED_ROWS_BUILD) -> list[str]:
    """Report any table whose row count is not the pinned expected count.

    A table absent from the dump raises nothing: `--table` ingests one table and
    the gate must not manufacture four failures for the ones nobody asked for.
    A table with no pinned count also raises nothing, so adding a table to the
    dump is not blocked on measuring it first - but TABLE_NAMES and EXPECTED_ROWS
    are asserted to agree in tests/test_ability_stats.py, so the gap cannot
    survive a commit.

    A dump from a DIFFERENT build raises nothing either, per EXPECTED_ROWS_BUILD,
    and format_counts prints the stand-down so it is never mistaken for a pass.
    """
    problems: list[str] = []
    if not count_applies(build):
        return problems
    for name in sorted(tables):
        rows = tables[name]
        if not isinstance(rows, list) or name not in EXPECTED_ROWS:
            continue
        expected = EXPECTED_ROWS[name]
        if len(rows) != expected:
            problems.append(
                f"{name}: {len(rows)} rows, expected {expected} - "
                f"a count that disagrees with the pin is either a real change in "
                f"the game data or a duplicate no per-row gate can see"
            )
    return problems


def localization_summary(payload: dict) -> dict:
    """Report the dump's prefab-to-localization join counters.

    The join is a PER-HOST fact, not a build fact. MEASURED on the dedicated
    server, `ManagedDataRegistry.TryGet<ManagedItemData>` returns false for all
    425 equippables and the without-logging control agrees, so `localization_guid`
    is unwritable there. Whether the client host registers the managed data is a
    different question with a different answer, and the only honest way to know
    which host produced a dump is for the dump to carry its own counters.

    `quiet_hits` is the control and is reported alongside the miss count: a
    nonzero value means the data IS registered and the logging path refused it,
    which is a completely different diagnosis from "not registered".
    """
    block = payload.get("localization")
    if not isinstance(block, dict):
        return {"present": False, "registry": "", "attempted": 0, "resolved": 0,
                "empty_key": 0, "missed": 0, "quiet_hits": 0,
                "rate": None, "writable": False}

    def count(key: str) -> int:
        value = block.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    attempted = count("attempted")
    resolved = count("resolved")
    # No attempts means no evidence either way. A rate of 0.0 would read as a
    # measured absence, which is a stronger claim than the data supports.
    rate = (resolved / attempted) if attempted > 0 else None

    return {
        "present": True,
        "registry": str(block.get("registry", "")),
        "attempted": attempted,
        "resolved": resolved,
        "empty_key": count("empty_key"),
        "missed": count("missed"),
        "quiet_hits": count("quiet_hits"),
        "rate": rate,
        "writable": resolved > 0,
    }


def format_localization(summary: dict) -> list[str]:
    """Render the join counters as operator-readable lines.

    A zero rate is stated as a measurement, never as an error: 0 of 425 on the
    server host is the recorded finding, and a census that shouted about it
    would train the operator to ignore the line that matters.
    """
    if not summary["present"]:
        return ["localization: MISSING from the payload - the dumper owes these counters"]

    head = (
        f"localization: {summary['resolved']} of {summary['attempted']} resolved"
        f" registry={summary['registry'] or '?'}"
        f" empty_key={summary['empty_key']}"
        f" missed={summary['missed']}"
        f" quiet_hits={summary['quiet_hits']}"
    )
    lines = [head]
    if summary["writable"]:
        lines.append("  localization_guid is WRITABLE on the host that took this dump")
    elif summary["rate"] is None:
        lines.append("  no equippable was attempted - this dump is evidence of nothing here")
    elif summary["quiet_hits"] > 0:
        lines.append("  registered but the logging path refused it - NOT an absence")
    else:
        lines.append("  measured ABSENT on the host that took this dump, so the field is omitted")
    return lines


def format_census(census: dict, unmapped: dict) -> list[str]:
    """Render the census structure as operator-readable lines."""
    lines = ["", "shape census - observed, not asserted:"]
    if not census:
        lines.append("  (no nested containers observed)")
    for name in sorted(census):
        lines.append(f"  {name}")
        for path, slot in census[name].items():
            card = slot["cardinality"]
            kinds = "/".join(slot["container_kinds"]) or "?"
            entry = "/".join(slot["entry_kinds"])
            head = (
                f"    {path}: {kinds}"
                f" occurrences={slot['occurrences']}"
                f" cardinality min={card['min']} max={card['max']} total={card['total']}"
            )
            if entry:
                head += f" entries={entry}"
            lines.append(head)
            if not slot["keys"]:
                lines.append("      keys: (none)")
            for key, stats in slot["keys"].items():
                types = ",".join(stats["types"])
                span = ""
                if stats["min"] is not None:
                    span = f" range=[{stats['min']}, {stats['max']}]"
                lines.append(f"      {key}: n={stats['count']} types={types}{span}")

    lines.append("")
    if not unmapped["present"]:
        lines.append("unmapped: MISSING from the payload - the dumper owes this array")
    else:
        lines.append(f"unmapped: {unmapped['count']} prefab(s) the dumper could not classify")
        for entry in unmapped["sample"]:
            lines.append(f"  {entry}")
        if unmapped["count"] > len(unmapped["sample"]):
            lines.append(f"  ... {unmapped['count'] - len(unmapped['sample'])} more")
    return lines


# ---------------------------------------------------------------------------
# ingest
# ---------------------------------------------------------------------------


def wrap_rows(name: str, build: str, rows: list) -> dict:
    """Wrap rows in the frozen core.tables envelope. Never hand-build one."""
    table = empty_table(name, build)
    table["rows"] = rows
    return table


def fetch_dump(host: str, from_file: Path | None, table: str | None) -> dict:
    """Load the dump from a saved file, or GET it from the bridge."""
    if from_file is not None:
        return json.loads(from_file.read_text(encoding="utf-8"))
    query = {"table": table} if table else None
    return get_json(host, DUMP_PATH, query)


def _clear_incoming(incoming: Path) -> None:
    """Create the quarantine directory and clear any earlier attempt from it."""
    incoming.mkdir(parents=True, exist_ok=True)
    for path in incoming.iterdir():
        if path.is_file():
            path.unlink()


def ingest(
    repo_root: Path,
    host: str = DEFAULT_HOST,
    accept: bool = False,
    from_file: Path | None = None,
    table: str | None = None,
    out=None,
    err=None,
) -> int:
    """Run the section 7 pipeline. Returns a process exit code."""
    out = sys.stdout if out is None else out
    err = sys.stderr if err is None else err

    def fail(code: int, message: str) -> int:
        print(message, file=err)
        return code

    if table is not None and table not in TABLE_NAMES:
        return fail(
            EXIT_REFUSED,
            f"refused: unknown table {table!r}, expected one of {TABLE_NAMES}",
        )

    # 1. expected build
    try:
        expected = read_expected_build(repo_root)
    except OSError as exc:
        return fail(EXIT_REFUSED, f"refused: cannot read data/rmdata/current.txt ({exc})")
    if not expected:
        return fail(EXIT_REFUSED, "refused: data/rmdata/current.txt is empty")

    # 2. the dump, then the build cross-check. Nothing is created on disk until
    # the builds agree.
    try:
        payload = fetch_dump(host, from_file, table)
    except BridgeUnreachable as exc:
        return fail(EXIT_REFUSED, f"refused: {exc}")
    except OSError as exc:
        return fail(EXIT_REFUSED, f"refused: cannot read the dump file ({exc})")
    except json.JSONDecodeError as exc:
        return fail(EXIT_REFUSED, f"refused: the dump is not JSON ({exc})")

    if not isinstance(payload, dict):
        return fail(EXIT_REFUSED, "refused: the dump is not a JSON object")
    if payload.get("ok") is False:
        return fail(
            EXIT_REFUSED,
            f"refused: the bridge returned {payload.get('error', 'an error')} "
            f"({payload.get('message', 'no message')})",
        )

    dumped = normalize_build(str(payload.get("build", "")))
    if not dumped:
        return fail(EXIT_REFUSED, "refused: the dump carries no build field")
    if dumped != expected:
        return fail(
            EXIT_REFUSED,
            f"refused: build mismatch - the dump is {dumped!r} but "
            f"data/rmdata/current.txt expects {expected!r}. Re-run "
            f"tools/rmdata_extract.py against the updated install first.",
        )

    tables = payload.get("tables")
    if not isinstance(tables, dict):
        return fail(EXIT_REFUSED, "refused: the dump carries no tables object")

    names = [table] if table else [name for name in TABLE_NAMES if name in tables]
    missing = [name for name in names if not isinstance(tables.get(name), list)]
    if missing:
        return fail(EXIT_REFUSED, f"refused: the dump has no rows list for {missing}")
    if not names:
        return fail(EXIT_REFUSED, "refused: the dump carries no known tables")

    tables_dir = repo_root / "data" / "rmdata" / expected / TABLES_DIRNAME
    incoming = tables_dir / INCOMING_DIRNAME
    _clear_incoming(incoming)

    # 3 and 4. envelope from the frozen module, then an atomic quarantine write.
    problems: list[str] = []
    for name in names:
        envelope = wrap_rows(name, expected, tables[name])
        write_json_atomic(incoming / f"{name}.json", envelope)

        # 5. shallow gate.
        shallow = validate_table(envelope, load_schema(name))
        problems.extend(f"{name}: {problem}" for problem in shallow)

        # 6. deep nested gate. The shallow gate cannot see inside
        # recipes.ingredients, blood_types.bonuses or items.stats, so a clean
        # shallow pass is not a shape guarantee.
        deep = deep_problems(name, envelope)
        problems.extend(f"{name}: {problem}" for problem in deep)

    # The uniqueness gate runs over the whole set at once because it is a
    # cross-ROW fact: every individual row here already passed both the shallow
    # and the deep gate, and the defect is only visible in the collection.
    problems.extend(duplicate_key_problems({name: tables[name] for name in names}))

    # The count gate runs last of the three cross-row checks and for the same
    # reason the uniqueness one exists: a defect that is invisible per row and
    # visible only in the collection. A duplicate shows up in both, but a
    # SILENTLY DROPPED row shows up only here.
    problems.extend(count_problems({name: tables[name] for name in names}, expected))

    # 7. census. Printed even on a failed gate - the census is how the operator
    # finds out WHY the shape is wrong.
    censused = {name: tables[name] for name in names}
    for line in format_census(shape_census(censused), unmapped_summary(payload)):
        print(line, file=out)
    for line in format_localization(localization_summary(payload)):
        print(line, file=out)
    for line in format_counts({name: tables[name] for name in names}, expected):
        print(line, file=out)

    counts = ", ".join(f"{name}={len(tables[name])}" for name in names)
    print(f"\nquarantined {counts} -> {incoming}", file=out)

    if problems:
        print(
            f"refused: {len(problems)} validation problem(s), nothing promoted. "
            f"The rows stay in {incoming} for inspection.",
            file=err,
        )
        for problem in problems[:50]:
            print(f"  {problem}", file=err)
        if len(problems) > 50:
            print(f"  ... {len(problems) - 50} more", file=err)
        return EXIT_INVALID

    if not accept:
        print(
            "validated. The live table path is untouched - re-run with --accept to promote.",
            file=out,
        )
        return EXIT_OK

    # 8. promotion, atomic, via the same temp-then-replace helper.
    for name in names:
        payload_json = json.loads((incoming / f"{name}.json").read_text(encoding="utf-8"))
        write_json_atomic(tables_dir / f"{name}.json", payload_json)

    # 9. and the quarantine is emptied, because PROMOTED and PENDING have to be
    # distinguishable on disk. Promotion COPIES rather than moves - the read
    # above is what re-validates what is written - so without this the two
    # directories hold byte-identical files and nothing says which state the
    # tree is in. Observed on the real tree 2026-08-01: six stale files from an
    # earlier accepted run, indistinguishable from six awaiting --accept.
    # Deliberately AFTER the writes and only on the success path: a refused run
    # and a validated-but-unaccepted run both leave the rows here, which is the
    # state _incoming/ exists to represent.
    _clear_incoming(incoming)

    print(f"promoted {len(names)} table(s) -> {tables_dir}", file=out)
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest the RedMoon.Bridge prefab dump.")
    parser.add_argument(
        "--host",
        choices=BRIDGE_HOSTS,
        default=DEFAULT_HOST,
        help="which V Rising host serves the bridge (default: %(default)s)",
    )
    parser.add_argument(
        "--accept",
        action="store_true",
        help="promote the quarantined tables into the live table path",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        default=None,
        help="ingest a saved dump instead of hitting the bridge",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="repo root holding data/rmdata (default: this checkout)",
    )
    parser.add_argument(
        "--table",
        default=None,
        choices=TABLE_NAMES,
        help="ingest one table only (default: every table in the dump)",
    )
    args = parser.parse_args(argv)

    return ingest(
        repo_root=args.repo,
        host=args.host,
        accept=args.accept,
        from_file=args.from_file,
        table=args.table,
    )


if __name__ == "__main__":
    sys.exit(main())

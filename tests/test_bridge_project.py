"""Contract gates on the C# half of RedMoon.Bridge.

There is no C# test project in cycle 2 (operator ruling: deferred). Everything
here is therefore a PYTHON characterization of an artifact or a contract that can
be checked without a running game:

  * the project file - target framework, assembly name, the generated port file
    it must compile, and the absence of any port literal of its own;
  * the reference set, which BRIDGE_SPIKES.md S4 measured as building clean with
    zero warnings;
  * the loader banner, checked with the SAME matcher tools/bridge_probe.py uses,
    so the banner and its probe cannot drift apart;
  * the /state envelope field set, checked against the same probe's D6 list;
  * the emitted table row shapes, run through the real core.tables and
    core.table_deep gates.

What these tests explicitly CANNOT prove: that the assembly loads, that the
listener binds, or that any number came from the running game. That is
tools/bridge_probe.py's job and it needs the game (spec decision D5).
"""
import json
import re
from pathlib import Path

from core import ports
from core.table_deep import deep_problems
from core.tables import load_schema, validate_table
from tools import bridge_probe, rmdata_ingest

REPO = Path(__file__).resolve().parents[1]
BRIDGE = REPO / "bridge"
SRC = BRIDGE / "src" / "RedMoon.Bridge"
CSPROJ = SRC / "RedMoon.Bridge.csproj"
PROPS = BRIDGE / "Directory.Build.props"

SOURCE_FILES = ("Plugin.cs", "HostDetect.cs", "BridgeServer.cs", "PrefabDumper.cs",
                "Localization.cs")

GENERATED_REL = "Generated/RmPorts.g.cs"

# BRIDGE_SPIKES.md S4: this exact set built clean, exit 0, zero warnings, in the
# spike plugin. SemanticVersioning is not optional - Paths.BepInExVersion and the
# BepInPlugin attribute both hand back a SemanticVersioning.Version.
REQUIRED_REFERENCES = frozenset(
    {
        "BepInEx.Core",
        "BepInEx.Unity.Common",
        "BepInEx.Unity.IL2CPP",
        "Il2CppInterop.Runtime",
        "SemanticVersioning",
        "0Harmony",
        "Il2Cppmscorlib",
        "Il2CppSystem",
        "Il2CppSystem.Core",
        "UnityEngine.CoreModule",
        "Unity.Entities",
        "Unity.Collections",
        "Unity.Mathematics",
        "Stunlock.Core",
        "ProjectM",
        "ProjectM.Shared",
        "ProjectM.Gameplay.Systems",
        # Localization.cs touches ManagedItemData.Name, a
        # Stunlock.Localization.LocalizationKey. R17 re-run across this assembly:
        # 48 types in both hosts, zero divergence in either direction.
        "Stunlock.Localization",
    }
)

# All five tables are mapped against build 1.1.13.0-r99712 as of the cycle 2
# measurement pass (BRIDGE_SPIKES.md, sections A to F): the ability school is
# SpellSchoolAbility.AbilityGroup on the *SpellSchoolAsset prefab, the V Blood
# level is UnitLevel.Level, and the blood bonus tiers are the two
# UnitBloodTypeBuffs buffers.
WRITABLE_TABLES = ("items", "recipes", "abilities", "vbloods", "blood_types",
                   "ability_stats")
UNWRITABLE_TABLES = ()

PORT_LITERALS = re.compile(r"\b(?:" + "|".join(str(port) for port in sorted(ports.ALL)) + r")\b")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _unescaped(path: Path) -> str:
    """Source with C# string escapes undone, so a JSON key written as \\" reads
    as a plain quoted token. Without this every key search below is vacuous."""
    return _read(path).replace('\\"', '"')


def _target_frameworks(text: str) -> list[str]:
    return re.findall(r"<TargetFramework>([^<]+)</TargetFramework>", text)


# ---------------------------------------------------------------------------
# the project file
# ---------------------------------------------------------------------------
def test_the_project_and_its_sources_exist_at_the_spec_layout():
    assert CSPROJ.is_file(), f"no project file at {CSPROJ}"
    for name in SOURCE_FILES:
        assert (SRC / name).is_file(), f"no {name} at {SRC}"


def test_effective_target_framework_is_net6_and_nothing_contradicts_it():
    """BepInEx 6 on this install runs CoreCLR .NET 6.0.7 (BRIDGE_SPIKES.md)."""
    declared = _target_frameworks(_read(CSPROJ)) + _target_frameworks(_read(PROPS))
    assert set(declared) == {"net6.0"}, f"conflicting target frameworks {declared}"


def test_assembly_name_is_the_shipped_dll_name():
    assert "<AssemblyName>RedMoon.Bridge</AssemblyName>" in _read(CSPROJ)


def test_project_compiles_the_generated_port_file():
    """The C# side cannot import core/ports.py, so it must compile the render."""
    text = _read(CSPROJ)
    includes = re.findall(r'<Compile\s+Include="([^"]+)"', text)
    normalized = [include.replace("\\", "/") for include in includes]
    assert GENERATED_REL in normalized, f"RmPorts.g.cs is not compiled in: {includes}"


def test_project_file_carries_no_port_literal():
    """CLAUDE.md hard rule. tests/test_ports.py scans .py/.cs/.json/.ps1 and is
    blind to .csproj, so the project file needs its own gate."""
    offenders = PORT_LITERALS.findall(_read(CSPROJ))
    assert offenders == [], f"port literals in the project file: {offenders}"


def test_reference_set_is_the_one_measured_to_build_clean():
    text = _read(CSPROJ)
    referenced = set(re.findall(r'<Reference\s+Include="([^"]+)"', text))
    missing = REQUIRED_REFERENCES - referenced
    assert missing == set(), f"missing references measured as needed: {sorted(missing)}"


def test_every_reference_resolves_through_a_hint_path_variable():
    """Absolute paths repeated per reference rot silently when the install moves."""
    text = _read(CSPROJ)
    hints = re.findall(r"<HintPath>([^<]+)</HintPath>", text)
    assert hints, "no HintPath elements - the references cannot resolve"
    for hint in hints:
        assert hint.startswith("$("), f"HintPath {hint!r} does not use an MSBuild property"


# ---------------------------------------------------------------------------
# the loader banner - the probe's matcher is the contract
# ---------------------------------------------------------------------------
def _banner_format() -> str:
    text = _read(SRC / "Plugin.cs")
    match = re.search(r'BannerFormat\s*=\s*"(?P<fmt>[^"]*)"', text)
    assert match is not None, "Plugin.cs declares no BannerFormat constant"
    return match.group("fmt")


def test_banner_format_carries_all_three_placeholders():
    fmt = _banner_format()
    for slot in ("{0}", "{1}", "{2}"):
        assert slot in fmt, f"BannerFormat {fmt!r} has no {slot} placeholder"


def test_rendered_banner_satisfies_the_probes_own_matcher():
    """A matcher that accepts any line containing RedMoon.Bridge survived mutation
    testing once already. bridge_probe._banner_matches wants version, host AND
    port, so rendering the real format through it is the gate."""
    fmt = _banner_format()
    for host in ports.BRIDGE_HOSTS:
        port = ports.bridge_port_for_host(host)
        rendered = fmt.replace("{0}", "0.1.0").replace("{1}", host).replace("{2}", str(port))
        matches = bridge_probe._banner_matches(rendered)
        assert len(matches) == 1, f"banner {rendered!r} did not match for host {host}"
        _line, version, banner_host, banner_port = matches[0]
        assert version == "0.1.0"
        assert banner_host == host
        assert banner_port == port


def test_banner_is_not_matched_when_a_token_is_dropped():
    """The gate above would be worthless if the matcher accepted anything."""
    fmt = _banner_format()
    truncated = fmt.split("{2}")[0].replace("{0}", "0.1.0").replace("{1}", "client")
    assert bridge_probe._banner_matches(truncated) == []


def test_plugin_version_is_read_back_rather_than_spelled_twice():
    """One version literal reaches the BepInPlugin attribute; the banner and
    /health read it back off that attribute at runtime."""
    text = _read(SRC / "Plugin.cs")
    assert "MetadataHelper.GetMetadata" in text, "the plugin does not read its own metadata"
    literals = re.findall(r'"(\d+\.\d+\.\d+)"', text)
    assert len(literals) == 1, f"the version literal appears {len(literals)} times: {literals}"


# ---------------------------------------------------------------------------
# host detection and the endpoints
# ---------------------------------------------------------------------------
def test_host_detect_reads_the_measured_mechanism_and_names_both_hosts():
    text = _read(SRC / "HostDetect.cs")
    assert "Paths.ProcessName" in text, "host detection does not read Paths.ProcessName"
    for host in ports.BRIDGE_HOSTS:
        assert f'"{host}"' in text, f"HostDetect.cs never returns {host!r}"


def test_state_endpoint_names_every_d6_envelope_field():
    """tools/bridge_probe.ENVELOPE_FIELDS is the D6 contract. If a field is
    renamed there and not here, this fails rather than the probe failing live."""
    text = _unescaped(SRC / "BridgeServer.cs")
    for field in bridge_probe.ENVELOPE_FIELDS:
        assert f'"{field}"' in text, f"BridgeServer.cs never emits the envelope field {field}"


def test_health_endpoint_names_its_promised_fields():
    text = _unescaped(SRC / "BridgeServer.cs")
    for field in ("host", "port", "game_root", "plugin", "build", "world", "ready"):
        assert f'"{field}"' in text, f"BridgeServer.cs never emits the /health field {field}"


def test_readiness_failure_uses_the_spec_error_code():
    text = _read(SRC / "BridgeServer.cs") + _read(SRC / "PrefabDumper.cs")
    assert "world_not_ready" in text
    assert "GameDataInitialized" in _read(SRC / "PrefabDumper.cs"), (
        "the dump is not gated on the measured readiness flag"
    )


def test_listener_is_stopped_and_closed_on_unload():
    server = _read(SRC / "BridgeServer.cs")
    assert ".Stop()" in server and ".Close()" in server
    assert "Unload" in _read(SRC / "Plugin.cs")


def test_no_raw_exception_message_reaches_a_caller():
    """CLAUDE.md error handling: the raw string goes to the log, the caller gets
    a code. A response body built from ex.Message is the failure mode."""
    server = _read(SRC / "BridgeServer.cs")
    # Statement-wise, not line-wise: a logging call wraps across lines and a
    # line-wise scan would flag its continuations while missing a one-line leak.
    for statement in server.split(";"):
        if "ex.Message" not in statement:
            continue
        assert "_log.Log" in statement, (
            f"a raw exception message may reach the response: {statement.strip()!r}"
        )


# ---------------------------------------------------------------------------
# the dumper writes only what is mapped
# ---------------------------------------------------------------------------
def test_dumper_emits_only_the_mapped_tables():
    text = _unescaped(SRC / "PrefabDumper.cs")
    for name in WRITABLE_TABLES:
        assert f'"{name}"' in text, f"PrefabDumper.cs never emits {name}"
    for name in UNWRITABLE_TABLES:
        assert f'"{name}"' not in text, (
            f"PrefabDumper.cs emits {name}, which BRIDGE_SPIKES.md records as NOT writable"
        )


def test_ability_school_is_not_the_damage_type():
    """MEASURED: DealDamageParameters.MainType is Physical, Spell, Fire, Holy,
    Silver, Garlic, Corruption - a DAMAGE type. abilities.school is declared as
    blood, chaos, frost, illusion, storm, unholy or weapon and comes from the
    *SpellSchoolAsset prefab's SpellSchoolAbility buffer. Writing MainType into
    school would be the same class of error as the fabricated items.tier."""
    text = _unescaped(SRC / "PrefabDumper.cs")
    assert "SpellSchoolAbility" in text, "the school does not come from the school asset"
    school_line = [line for line in text.splitlines() if '"school"' in line]
    assert school_line, "no school field is emitted"
    for line in school_line:
        assert "MainType" not in line, f"MainType is written into school: {line.strip()!r}"


def test_ability_group_join_is_the_measured_reference_not_the_name():
    """MEASURED: the name join reaches only 258 of 1474 _Hit siblings, while
    AbilityGroupStartAbilitiesBuffer resolves a cast for 1474 of 1474."""
    text = _read(SRC / "PrefabDumper.cs")
    assert "AbilityGroupStartAbilitiesBuffer" in text
    assert '"_Hit"' not in text, "the dumper joins abilities by name suffix"


def test_vblood_level_is_unit_level_not_the_progression_tier():
    """MEASURED: VBloodConsumeSource.Tier is a SpellSchoolProgressionTier with
    values Undefined and Tier1..Tier4 over 65 V Bloods, which cannot be a boss
    level. UnitLevel.Level ranges 16..91 over the same family."""
    text = _unescaped(SRC / "PrefabDumper.cs")
    assert "UnitLevel" in text
    school_free = [line for line in text.splitlines() if '"level"' in line]
    assert school_free, "no level field is emitted"
    for line in school_free:
        assert "Tier" not in line, f"the progression tier is written into level: {line.strip()!r}"


def test_dumper_carries_the_mandatory_unmapped_array():
    assert '"unmapped"' in _unescaped(SRC / "PrefabDumper.cs")


# ---------------------------------------------------------------------------
# the localization join
#
# MEASURED absent on the dedicated server (0 of 425, BRIDGE_SPIKES.md section
# E). The join is a PER-HOST fact, so the dump carries its own counters and the
# ingest prints them. These gates keep the C# key names and the Python reader
# from drifting apart, which is the same reason the banner and its probe share
# a matcher.
# ---------------------------------------------------------------------------
def test_station_guids_are_inverted_from_the_two_station_buffers():
    """ADR-006. Nothing on a recipe entity names a station, so the value can only
    come from inverting the station side. RecipeLinkBuffer looked like the
    forward link and is NOT: 5 of 667 recipes carry it and every one of its 56
    links resolves to another RECIPE."""
    text = _read(SRC / "PrefabDumper.cs")
    assert "WorkstationRecipesBuffer" in text
    assert "RefinementstationRecipesBuffer" in text
    # Named in a comment as the rejected candidate, which is the point of the
    # comment. What must not appear is a READ of it.
    assert "HasBuffer<ProjectM.RecipeLinkBuffer>" not in text, (
        "the dumper reads the recipe-group alias as if it named a station"
    )
    assert "GetBuffer<ProjectM.RecipeLinkBuffer>" not in text


def test_dumper_emits_the_plural_station_field_and_not_the_singular_one():
    text = _unescaped(SRC / "PrefabDumper.cs")
    assert '"station_guids"' in text
    assert '"station_guid"' not in text, (
        "the singular station_guid is emitted, which ADR-006 retired as unrepresentable"
    )


def test_station_list_is_sorted_before_it_is_emitted():
    """core/table_deep.py rejects an unsorted or repeated list, so an unsorted
    emit would fail at ingest rather than here - but it would fail on the LIVE
    dump, after the operator has already run the game."""
    text = _read(SRC / "PrefabDumper.cs")
    assert ".Sort()" in text, "the station list is emitted in world-walk order"


def test_every_table_dedupes_on_prefab_guid():
    """MEASURED: more than one entity can carry the same PrefabGUID, so a
    straight pass over GetAllEntities emits the row twice. The ingest gate
    catches it, but the dumper is where it stops being produced."""
    text = _read(SRC / "PrefabDumper.cs")
    for table in WRITABLE_TABLES:
        stem = "".join(part.capitalize() for part in table.split("_"))
        assert f"seen{stem}.Add(guid.GuidHash)" in text, (
            f"{table} rows are not deduped on prefab_guid"
        )


def test_dedupe_never_claims_a_guid_before_the_marker_component_is_tested():
    """&& short-circuits left to right. An Add placed before the marker test
    claims the guid on behalf of every entity carrying it, then rejects the real
    row when it arrives - which turns a duplicate bug into a missing-row bug."""
    text = _read(SRC / "PrefabDumper.cs")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("if (want") or ".Add(guid.GuidHash)" not in stripped:
            continue
        raise AssertionError(
            f"the guid is claimed on the same line as the want flag: {stripped!r}"
        )


def test_dump_envelope_carries_the_localization_counters():
    assert '"localization"' in _unescaped(SRC / "PrefabDumper.cs")


def test_localization_block_key_names_match_what_the_ingest_reads():
    """The producer and the consumer are in different languages. Nothing but
    this test stops a rename on one side from silently zeroing the other."""
    text = _unescaped(SRC / "Localization.cs")
    for key in ("registry", "attempted", "resolved", "empty_key", "missed", "quiet_hits"):
        assert f'"{key}"' in text, f"Localization.cs never emits {key}"

    absent = rmdata_ingest.localization_summary({"localization": {}})
    for key in ("registry", "attempted", "resolved", "empty_key", "missed", "quiet_hits"):
        assert key in absent, f"rmdata_ingest never reads {key}"


def test_localization_join_uses_the_registry_not_the_prefab_lookup_map():
    """CORRECTED in BRIDGE_SPIKES.md S6: PrefabLookupMap carries no localization
    member at all, and its GetName returns the PREFAB name. The claim that it
    served this join was a false line in the spikes doc."""
    text = _read(SRC / "Localization.cs")
    assert "ManagedDataRegistry" in text
    assert "PrefabLookupMap" not in text, "the join reads the prefab lookup map"


def test_localization_join_keeps_its_without_logging_control():
    """A zero from TryGet alone is unreadable: it cannot separate "not
    registered" from "registered and the logging path refused it". The control
    is what makes the measured absence a result rather than a shrug."""
    assert "TryGetWithoutLogging" in _read(SRC / "Localization.cs")


def test_localization_guid_is_omitted_rather_than_written_empty():
    """An empty localization_guid and a missing one are different claims, and
    only the second one is true when the join does not resolve. Same rule that
    retired the fabricated items.tier."""
    text = _unescaped(SRC / "PrefabDumper.cs")
    emitting = [line for line in text.splitlines() if '"localization_guid"' in line]
    assert emitting, "the dumper never emits localization_guid"
    for line in emitting:
        assert line.lstrip().startswith("sb.Append"), (
            f"localization_guid is written outside a guarded append: {line.strip()!r}"
        )
    assert "loc.Length > 0" in text, "localization_guid is emitted unconditionally"


def _enclosing_methods(text: str, needle: str) -> set[str]:
    """Names of the methods in which `needle` appears.

    Tracks the most recent method signature seen while scanning, which is enough
    for this file: it is one flat static class with no nested types.

    COMMENT LINES ARE SKIPPED. The assertion this serves is about what the code
    READS, and a doc comment sits ABOVE its own method signature, so counting
    prose would attribute every documented chain to the method before it.
    """
    signature = re.compile(r"\b(?:private|internal|public)\s+static\s+[\w<>\[\],. ]+?(\w+)\s*\(")
    found: set[str] = set()
    current = "<file scope>"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("//"):
            continue
        match = signature.search(line)
        if match:
            current = match.group(1)
        if needle in line:
            found.add(current)
    return found


def test_item_stats_are_read_one_hop_off_the_item_prefab():
    """The two-hop route through EquippableData.BuffGuid was MEASURED WRONG for
    STATS: the buff prefab has no stat buffer at all (BRIDGE_SPIKES.md,
    corrected).

    This test used to enforce that by banning the BuffGuid token from the whole
    file, and cycle 3 phase 1 showed that ban was too broad. BuffGuid is the
    CORRECT and only route to the abilities an item grants - item ->
    EquippableData.BuffGuid -> the equip buff -> ReplaceAbilityOnSlotBuff. The
    asymmetry is real and is not a contradiction: stats live on the item prefab
    itself, abilities live on the equip buff. So the assertion is scoped to the
    stat reader rather than relaxed away, because the original defect it was
    written to catch is still a defect.
    """
    text = _read(SRC / "PrefabDumper.cs")
    assert "ModifyUnitStatBuff_DOTS" in text

    users = _enclosing_methods(text, "BuffGuid")
    assert "WriteStats" not in users, (
        "the stat reader follows BuffGuid, which carries no stats"
    )
    assert "TryWriteItem" not in users, (
        "the item row follows BuffGuid inline rather than through the ability link"
    )
    assert "WriteAbilityGroups" in users, (
        "the ability link no longer follows BuffGuid, which is its only route"
    )


def test_recipe_output_is_not_read_from_the_unit_buffer():
    """RecipeOutputUnitBuffer produces a UNIT, not the item output."""
    text = _read(SRC / "PrefabDumper.cs")
    assert "RecipeOutputBuffer" in text
    assert "RecipeOutputUnitBuffer" not in text


# ---------------------------------------------------------------------------
# the emitted row shapes, against the real gates
# ---------------------------------------------------------------------------
# Sampled shape, keyed to the values BRIDGE_SPIKES.md measured on
# Item_Boots_T00_StartingRags (MaxHealth, Add, 13) and
# Recipe_Headgear_T01_RazerHood.
SAMPLE_ITEM_ROW = {
    "prefab_guid": -1613823352,
    "name": "Item_Boots_T00_StartingRags",
    "category": "boots",
    "tier": 0,
    "gear_score": 0.0,
    "weapon_type": "",
    "stats": [{"stat": "MaxHealth", "modification": "Add", "value": 13.0}],
}

SAMPLE_RECIPE_ROW = {
    "prefab_guid": -1797796642,
    "output_guid": -1797796642,
    "output_amount": 1,
    "craft_duration": 10.0,
    "ingredients": [
        {"prefab_guid": -237441421, "amount": 1},
        {"prefab_guid": -700774739, "amount": 8},
    ],
}


def _envelope(name: str, rows: list) -> dict:
    # Read the version off the schema rather than pinning a literal, so a future
    # bump does not silently make every envelope here fail for the wrong reason.
    return {
        "table": name,
        "build": "1.1.13.0-r99712",
        "schema_version": load_schema(name)["schema_version"],
        "rows": rows,
    }


def test_sample_recipe_row_passes_both_gates_unchanged():
    envelope = _envelope("recipes", [SAMPLE_RECIPE_ROW])
    assert validate_table(envelope, load_schema("recipes")) == []
    assert deep_problems("recipes", envelope) == []


def test_sample_item_row_is_schema_clean():
    """This test used to pin the OPPOSITE assertion - exactly one problem, stats
    expected object - because the dumper deliberately emitted a shape the cycle 1
    schema could not accept. The first real dump settled it: 899 stat entries
    across 425 items carry three modification kinds (Add, AddToBase,
    MultiplyBaseAdd), so a name-to-number map cannot represent them and
    items.schema.json went to schema_version 2 with stats as an array. The row is
    now clean, and that is the resolution of the mismatch, not a regression."""
    envelope = _envelope("items", [SAMPLE_ITEM_ROW])
    assert validate_table(envelope, load_schema("items")) == []


def test_item_stats_entries_keep_their_modification_kind():
    """The reason the schema was amended. A silent flattening to {stat: value}
    would erase ModificationType and make PhysicalPower Add 10 and PhysicalPower
    AddToBase 10 indistinguishable, and both kinds occur in the real dump."""
    for entry in SAMPLE_ITEM_ROW["stats"]:
        assert set(entry) == {"stat", "modification", "value"}
        assert isinstance(entry["stat"], str) and entry["stat"]
        assert isinstance(entry["modification"], str) and entry["modification"]
        assert isinstance(entry["value"], (int, float))


def test_emitted_stats_entry_keeps_the_modification_type():
    entry = SAMPLE_ITEM_ROW["stats"][0]
    assert set(entry) == {"stat", "modification", "value"}
    assert isinstance(entry["value"], float)
    assert entry["modification"] == "Add"


def test_sample_rows_are_json_serializable_as_the_plugin_would_emit_them():
    payload = {
        "ok": True,
        "build": "1.1.13.0-r99712",
        "tables": {"items": [SAMPLE_ITEM_ROW], "recipes": [SAMPLE_RECIPE_ROW]},
        "unmapped": [],
    }
    assert json.loads(json.dumps(payload)) == payload

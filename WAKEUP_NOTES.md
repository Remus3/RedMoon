# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-07-26 - CYCLE 2 CLOSED, cycle 3 opened

Branch `master`. Ledger 002g. Docs plus one test constant and one seed file. No
production code changed.

State at close, observed in one run after the last edit: `python -m pytest`
**317 passed**, `python -m ruff check .` clean, `python tools/ascii_guard.py`
exit 0.

**The decision.** The operator was given the residue against closing and chose to
close. Cycle 2's charter was live item and ability stat data on a local port, and
all five tables are populated, host-diffed and gated. The three residue items
were weighed rather than waved past:

- **4 unmapped recipes** - empty ITEM output buffer, they produce units, no
  cycle 3 consumer reads them. Closing buys a label, not data.
- **`items.tier`** - nothing left to spend a session on. No source exists on this
  build and both derivations are rejected on evidence. DECLARED and OMITTED is
  already the correct final state.
- **Weapon abilities produce no `abilities` row** - the only one with teeth,
  because Bloodforge computes weapon DPS and there is no `<Weapon>SpellSchoolAsset`
  to source a school from. Carried into `ROADMAP.md` cycle 3 as a NAMED INPUT GAP
  so no cycle 3 code scaffolds weapon damage on an assumed source.

**Two docs had drifted and are now synced.** `ROADMAP.md`'s cycle 2 section was a
running log appended to across six sessions, still carrying superseded numbers
inline with their corrections beside them - `vbloods` 66 was readable as current
if you stopped at the wrong paragraph. It is now a settled record.
`docs/ARCHITECTURE.md` was a full cycle behind: it read "Nothing runs as a
service in cycle 1", listed `bridge/` as planned, and named three modules out of
sixteen.

**A real gap the suite caught, and it was not mine.** Three tests in
`tests/test_claude_config.py` failed at session start, before any edit. Last
session wrote the memory entry `reference_flashing_consoles_are_mcp_launchers`
into the LIVE namespace and never seeded it into `docs/memory_seed/`. The live
namespace is outside the repository and uncommitted, so until this was fixed that
entry had no path back if it were lost - which is exactly the failure the seed
exists to prevent. Fixed by seeding the file, refreshing the seeded `MEMORY.md`,
and adding the name to `EXPECTED_MEMORY_ENTRIES`.

Worth keeping: three independent guards fired on one missing file, and the
session that created it saw none of them because it never re-ran the suite after
writing memory. Writing a memory entry is a repo-affecting act here.

**TWO CYCLE 3 BLOCKERS FOUND AT THE VERY END, and they are the most valuable
thing in this session.** While writing the next-session prompt I read the
promoted ROWS rather than the schema, and two of Bloodforge's declared inputs do
not exist:

1. **There is no BOSS STAT LINE.** `vbloods` rows carry exactly `level`, `name`
   and `prefab_guid`. No health, no resistances, no damage. `docs/BLOODFORGE.md`
   has named `tables/vbloods.json` as the source for "Boss stat line and
   resistances" since cycle 1 - written as a design intention, never checked
   against a real row, and false. **Time-to-kill is the engine's headline output
   and its denominator is not on disk.**
2. **There are no ABILITY COEFFICIENTS.** `abilities` carries identity, school
   and (16 of 54) a damage type. No cast time, no cooldown, no damage scalar.

The player side is NOT a gap and was checked in the same pass: 203 of 205 weapon
items carry real `PhysicalPower` or `SpellPower` over 29 stat types, each with an
explicit `modification`. The missing half is the TARGET side and the ABILITY
side.

This is the cycle 2 lesson landing one more time, from the other direction. Every
number cycle 2 published is correct. What nobody had done was ask whether the
correct numbers were the ones cycle 3 needs - "all five tables are populated" is
true and was quietly read as "cycle 3 has its inputs". A schema being satisfied
says nothing about a consumer being served.

`docs/BLOODFORGE.md`'s input table now carries a per-input STATUS column instead
of a bare source, and `ROADMAP.md` cycle 3 lists six named gaps instead of four,
with the consequence stated in both: **cycle 3 cannot open by writing combat
math.** It opens by settling those two inputs, because a TTK against an assumed
boss health is the `items.tier` fabrication with a larger blast radius.

**Cycle 3 opens** with verified inputs on disk (`items` 425, `recipes` 663,
`abilities` 54, `vbloods` 65, `blood_types` 13), six named gaps, and a spec
session ahead of any code. Per `ROADMAP.md` line 3 that spec is its own session.

## 2026-07-26 - Cycle 2 part 6: the client host, and a wrong number four gates could not see

Branch `master`. Ledger 002f.

State at close, every number observed in one run after the last edit:
`python -m pytest` **317 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` on
`bridge/src/RedMoon.Bridge` exit 0 with 0 warnings.

**BOTH HOSTS RAN THE SAME BINARY AT THE SAME TIME.** The dedicated server on
8780 and the operator's live client on 8777, concurrent, which is what made
every comparison below like-for-like rather than a comparison of two builds.

**1. The client item COMPONENT data is IDENTICAL to the server's.** Row-by-row
diff keyed on `prefab_guid`, every field on every row of all five tables: ZERO
differences. Matching counts would have proved nothing - two 425-row tables can
disagree on every field - so this was diffed rather than counted. The client
dump costs 103 ms against the server's 794.

**2. `localization_guid` is WRITABLE, on the CLIENT only. The recorded absence
was a HOST fact that had been read as a BUILD fact.** Same binary, same call,
same session:

```
dedicated server   attempted=425  resolved=0    missed=425  quiet_hits=0
client             attempted=425  resolved=425  missed=0    quiet_hits=0
```

All 425 client guids are real `strings.json` keys - `Item_Headgear_WolfTrophy01`
to "Wolf Head". 342 distinct guids over 425 rows, because skins share a name.
The offline heuristic that was rejected reached 53 of 425.

The lesson is the session's inherited one, one layer up. Last session's warning
was "a real measurement can still answer the wrong question". This one is: a
real measurement can answer the right question about the wrong SUBJECT. `0 of
425` was correct, reproducible, and had a proper negative control
(`TryGetWithoutLogging`) - and it was a statement about a headless host that got
written down as a statement about the game. Every dump now carries its own
`localization` counter block and `rmdata_ingest` prints it, so a saved payload
says for itself which host produced it.

**3. `vbloods` is 65, not 66. A wrong number that four gates could not see.**
Diffing by `prefab_guid` surfaced duplicate rows: `abilities` 56 rows over 54
distinct guids on BOTH hosts (`AB_Blood_BloodRite_AbilityGroup` and
`AB_Blood_Shadowbolt_AbilityGroup` twice each), and the server 66 vbloods over
65 (`CHAR_Vampire_Dracula_VBlood` twice). More than one ENTITY can carry the
same `PrefabGUID` and the dumper wrote one row per entity.

Why it survived: every duplicate pair was BYTE-IDENTICAL. The shallow gate, the
deep nested gate, the schema and the census all inspect one row at a time, and
each of those rows was individually perfect. The only symptom was the COUNT, and
66 had already been written into `ROADMAP.md` and ledger 002e as a finding.
Fixed in the dumper (dedupe on first write) AND gated at ingest
(`duplicate_key_problems`, a cross-ROW check) - the producer being fixed today is
not the same as the defect being detectable tomorrow.

A trap inside the fix, caught before it shipped: `&&` short-circuits left to
right, so `seenItems.Add(guid)` placed BEFORE the marker-component test would
claim the guid on behalf of every entity carrying it and then reject the real row
when it arrived. That turns a duplicate bug into a missing-row bug. There is a
test asserting the guard order.

**4. `recipes.station_guids`, ADR-006.** The singular field is retired at
`schema_version` 2 and the plural array is emitted. 911 unique (recipe, station)
pairs from 942 raw references; 575 recipes reach a station, 88 reach none, 19 sit
at TWELVE stations each. That histogram is why first-station-wins was barred: it
would have been arbitrary for 138 recipes. The 88 empty lists ship as `[]`, so
"reachable from no station" stays distinguishable from "the inversion did not
run".

**5. `Unload()` is still UNOBSERVED, and the reason is worth keeping.** Measured
twice on a normal in-game quit: `LogOutput.log` gains nothing after
`Chainloader startup complete`. But `Unload()` logged NOTHING, so that silence
was equally consistent with "ran fine", "never ran" and "the logging pipeline
was torn down first" - a zero three hypotheses predict is not evidence. It now
appends to `BepInEx\redmoon-unload.log` via `File.AppendAllText`, OUTSIDE the
logging pipeline, so the three outcomes are distinguishable.

**CLOSED on the instrumented build: `Unload()` does NOT run.** A normal in-game
quit left the marker ABSENT, the log unchanged, and 8777 with no LISTEN. The two
channels fail independently, which eliminates "the pipeline was gone first", so
BepInEx 6 IL2CPP does not invoke `BasePlugin.Unload()` at shutdown. The control
that makes the silence readable: the observed run PROVABLY carried the
instrumented build, because the dump it served included `station_guids`, which
exists only there. Benign - R11 already measured that a hard kill releases the
port, and a normal exit takes the identical path.

The promoted dump is the CLIENT one: `items` 425 (schema 3, all 425 carrying
`localization_guid`), `recipes` 663 (schema 2, with `station_guids`),
`abilities` 54, `vbloods` 65, `blood_types` 13, in 103 ms.

Process note, answering the operator's flashing-console report: a 120-second
`Win32_Process` trace named them, and NONE is Red Moon's. They are
`cmd.exe /d /s /c npx ...` MCP launchers, each spawning its own `conhost.exe` -
`pathmode-mcp`, `desktop-commander`, `chrome-devtools-mcp`, `playwright-mcp` -
fired in bursts by four concurrent `claude.exe` instances, plus another Claude
session running a different project's `pytest` hook through Git Bash. Red Moon's own
hooks all run under `pythonw.exe`, which is windowless and never appeared as a
console. Last session's `statusLine` fix held: it did not appear in the trace at
all. The remedy is disabling unused MCP plugins in the user `settings.json`,
which currently lists 15 enabled.

## 2026-07-26 - Cycle 2 part 5: all five tables populated, two recorded answers corrected

Branch `master`. Ledger 002e.

State at close, every number observed in one run after the last edit:
`python -m pytest` **289 passed**, `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0, `dotnet build -c Release -t:Rebuild` on
`bridge/src/RedMoon.Bridge` exit 0 with 0 warnings. All four re-run by this
session, not taken from a report.

**The headline: `abilities` 54, `vbloods` 66, `blood_types` 13 are on disk.**
Together with `items` 425 and `recipes` 663 that is every table in
`core/tables.py`, from one `/dump/prefabs` in 714 ms, validated and promoted by
`rmdata_ingest --accept`.

**Two things that were WRITTEN DOWN as findings and were wrong. Both were
recorded by this project as measured, and both are the same failure: a real
measurement answering a question nobody had checked was the right question.**

1. **The ability school is not `DealDamageParameters.MainType`.** That reading is
   correct and it is the DAMAGE type - `Physical`, `Spell`, `Fire`, `Holy`,
   `Silver`, `Garlic`, `Corruption`. `abilities.school` is declared as blood,
   chaos, frost, illusion, storm, unholy or weapon. The real join is
   `DynamicBuffer<ProjectM.SpellSchoolAbility>` on the `<School>SpellSchoolAsset`
   prefab, whose element carries `.AbilityGroup`. It yields exactly 9 abilities in
   each of the six schools, which is itself a liveness signal - six buffers read
   independently do not land on the same count by accident.
2. **The V Blood level is not `VBloodConsumeSource.Tier`.** That field is a
   `SpellSchoolProgressionTier` with five members, measured
   `Tier1:23 Tier2:19 Tier3:13 Tier4:6 Undefined:4`. Five buckets cannot be a
   boss level. It is `ProjectM.UnitLevel.Level`, measured 16 to 91 over 92
   prefabs.

**The ability-group join, which was the session's first task, is a REFERENCE
join and the numbers are why.** Name join over 1474 `_AbilityGroup` names reaches
`_Cast` 1291 but `_Hit` only **258**. The reference chain
`AbilityGroupStartAbilitiesBuffer -> _Cast -> AbilitySpawnPrefabOnCast` resolves
a cast for **1474 of 1474**. A second spawn hop adds exactly 0, so one hop is the
answer and the 912 groups that never reach damage genuinely do not.

**`blood_types` went to `schema_version` 2 on evidence.** The version 1 nested
contract - a numeric `quality` threshold plus a name-to-number `stats` map - is
wrong on BOTH halves: no threshold field exists on the prefab, and every stat
magnitude on the tier buff reads 0 with `SoftCapValue` 1, scaled from blood
quality at runtime. The table now carries slot, 1-based tier, `buff_guid`,
`buff_name` and stat NAMES. Tiers ascend WITHIN a slot, not across the list; the
real row is primary 1..5 then secondary 1..4 and a global ascent check would
reject it. There is a regression test on that specific trap.

**Two negatives that are results, not failures:**

- `recipes.station_guid` is reverse-only AND one-to-many. `RecipeLinkBuffer`
  looked like the forward link and is not - 5 of 667 recipes carry it and every
  link resolves to another RECIPE. The station side is 35 `WorkstationRecipesBuffer`
  plus 23 `RefinementstationRecipesBuffer` holding 942 references over 663
  recipes. The field stays omitted until the singular-vs-plural schema question
  is decided.
- The runtime localization join is ABSENT on the server host. Over all 425
  equippables, `TryGet<ManagedItemData>` returns false 425 times, and the
  `TryGetWithoutLogging` control agrees, so it is not a logging refusal.
  `ManagedAbilityGroupData` over 200 groups: 0 hits. S7 had this INFERRED as
  working; it does not on this host.

Near miss worth keeping: the first blood-type deep dump sampled the first two
types, which are `BloodType_VBlood` and `BloodType_GateBoss`, both pointing at
the single buff that has no stat buffer. It looked exactly like "blood bonuses
carry no stats at all". Naming two REAL types settled it. Same shape as last
session's `equip=2 recipe=2` near miss: an unrepresentative sample that reads as
a family-wide absence.

Process note: the flashing PowerShell consoles the operator saw were the
`statusLine` command in `C:\Users\Administrator\.claude\settings.json`, which
spawns `powershell.exe` on every status refresh. It now runs with
`-NonInteractive -WindowStyle Hidden`; a backup of the original sits beside it as
`settings.json.bak-statusline`. Three other scheduled tasks outside the `RM-*`
namespace also run `powershell.exe`, two with an Interactive logon, but they fire
daily and weekly at 03:00 and 04:15 and belong to another project on this
machine, so they were left alone.

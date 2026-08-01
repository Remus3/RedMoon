# Taking an anchor run

The operator procedure for the falsification protocol
(`docs/superpowers/specs/2026-08-01-bloodforge-falsification-design.md`). One
page, because a protocol nobody can follow at 11pm is not a protocol.

Written 2026-08-01, after the recorder's first live run. Every number here was
measured on this machine, not inferred.

## What a run is for

Bloodforge computes DPS, EHP and time-to-kill and **cannot publish any of them**
until a recorded run lifts them (`bloodforge/embargo.py`). A run is the only
thing that lifts anything. It is also the only source of a boss `max_health`,
which is instance-only and reads 0 on all 65 prefabs.

## RUN 1 - the power-stat experiment. Take this one first.

It is the cheapest run in the protocol, it needs **no boss and no V Blood**, and
until it passes, `P(G)` is undefined and every damage number in the engine is
absent. It also measures the client sample rate for free, which is ROADMAP
gap 12.

### Prerequisites, and each of these can silently ruin the run

1. **The V Rising CLIENT, not the dedicated server.** The server has no player,
   and it samples at 2 Hz rather than the client's expected 4 Hz.
2. **`AB_Unholy_WardOfTheDamned_AbilityGroup` slotted and castable.** Prefab guid
   `-1136860480`, `ability_type` `SpellSlot2`. This is the ONLY ability in all
   1818 rows that separates the two hypotheses. Its `spell_school` is unholy, so
   H2 predicts `SpellPower`, and its `damage_type` is physical, so H1 predicts
   `PhysicalPower`. `coefficient` is exactly 1.0 and `hits_per_cast` is 1, so the
   prediction is literally **"the observed health delta equals one of the two
   power stats"** - no arithmetic to get wrong and no multi-hit window to alias.
3. **YOUR TWO POWER STATS MUST DIFFER.** This is the prerequisite that is easiest
   to miss and it invalidates the run completely. If `UnitStats.PhysicalPower`
   and `UnitStats.SpellPower` are equal - which is what a fresh character reads,
   MEASURED at 10 and 10 - then H1 and H2 predict the same number and the run is
   INDETERMINATE no matter how clean it is. Equip the weapon you would normally
   use; 203 of 205 weapons grant `PhysicalPower` and no `SpellPower`, which is
   what makes the two stats diverge. `bloodforge/powerstat.py` refuses to name a
   winner when they are within the tolerance band of each other, so a bad run
   fails loudly rather than producing a confident coin flip.
4. **A target that survives the hit and is not a V Blood.** Any ordinary unit.
   Something that dies to one cast gives one delta and the gate wants 30.
5. **Isolated hits.** An isolated delta is a health drop with at least one
   no-change sample on each side. Cast the Ward, WAIT, cast it again. Do not
   weave in weapon attacks - a window containing two applications is discarded,
   not averaged.

### The steps

Launch the client and load in. Then find the target's prefab guid, arm, cast,
stop. The bridge is on the client port from `core/ports.py`; substitute it below.

```bash
python tools/anchor_record.py start --guid <TARGET_PREFAB_GUID> --note "power stat H1 vs H2, ward of the damned"
```

**CHECK THE ARM RESPONSE BEFORE YOU CAST.** Two fields decide whether the run can
work at all:

- `player_resolved` must be `true` and `player_unit_stats` must be present. That
  block is the entire comparison basis. It was silently omitted by a defect
  found on 2026-08-01 and is now forced, but check it rather than assume it.
- `carries_prefab_marker` must be `false`. If the arm returns
  `subject_not_spawned`, the prefab exists but nothing is spawned from it yet.
  **Poll for the subject, never for `ready:true`** - a live boss did not exist at
  5 s of server uptime and did exist at 20 s, and a negative taken too early is
  indistinguishable from a real absence.

Now cast the Ward, on its own, with a pause between casts, about 30 times. Then:

```bash
python tools/anchor_record.py stop --out data/anchors/
```

The writer validates the series against `data/schemas/anchor.schema.json`, runs
the A.5 checklist, and writes the run plus its manifest atomically. **A run that
fails the checklist is recorded with its reason and never repaired.**

Then evaluate:

```bash
python -m bloodforge.powerstat data/anchors/<run_id>.json
```

### What the answer means, and what it does not

A pass tells you which hypothesis survives **on this one ability**. One row is a
sample of one. It does not prove the rule holds corpus-wide, and that caveat
belongs in the ledger entry rather than in a footnote. It is the only evidence
this build affords: zero rows are `is_weapon_ability` with a non-physical
`damage_type` and a nonzero coefficient, so the weapon side is dead by
exhaustion rather than by sampling.

It also will not price corruption either way. All 18 corruption groups carry
neither a spell school nor `is_weapon_ability`, so both hypotheses are silent on
them (ROADMAP gap 13).

## RUN 2 - the TTK anchor. Only after run 1 passes.

Same procedure against a spawned V Blood, fought to death, three times on the
SAME comparable subject (`bloodforge.embargo.comparable`, B.2: exact agreement on
build, boss, the whole difficulty object, blood type and the equipped-item map,
and blood quality within one 10-point bucket). Record `equipped_item_guids`
yourself - it is a CLI input, because a gear score is not sourceable from disk
for weapons (`gear_score` is on 0 of the 205 weapon rows).

`ttk_seconds` needs the per-hit gate AND the TTK gate AND three comparable runs,
because two of its three inputs do not otherwise exist.

## Operating the dedicated server, for recorder work that needs no player

```bash
dotnet build bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj -c Release -t:Rebuild
```

Deploy to exactly ONE path per host and check for a second copy first: the client
tree holds a flat `plugins/RedMoon.Bridge.dll` and the server tree holds
`plugins/RedMoon.Bridge/RedMoon.Bridge.dll`. Launch with
`-persistentDataPath C:\RedMoon\_scratch\vrserver -saveName world1 -batchMode
-nographics`, poll `/health`, and never `Stop-Process` - `taskkill /F /PID`.

MEASURED on that host: the bridge answers at about 28 s of uptime, a live
Dracula instance is resolvable immediately after, and the recorder samples at
1.99 Hz because the server runs at 29.9 fps. Expect roughly double that on the
client.

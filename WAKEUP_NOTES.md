# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-08-01 (eighth stretch) - The link corpus closes at zero adoptions, and a gate turns out to have been dead

Ledger 003m, 003n, 003o, 003p, 003q, 003r. Suite **551 passed in 22.61s exit 0**
(526 at open, +25), ruff clean, ascii_guard exit 0. No C# change. **NO ROADMAP
ITEM CLOSED** - but the link-ingest track closed stages 4, 5 and 6.

**THE POWER-STAT EXPERIMENT STILL HAS NOT RUN.** Operator was not at the
keyboard; deferred intact rather than approximated. `P(G)` is undefined and
every damage number is absent. `docs/ANCHOR_RUNS.md` is now followable end to
end - `tools/find_target.py` closes the "find the target's prefab guid" step and
the caster-side precondition is a CHECK against the arm response.

### The link ingest closed, 146 extracted, 21 dived, 0 adopted

Stages 4, 5 and 6 all closed this session, the last two by adversarial fan-out.
**Not one entry was demoted because the tool was bad.** Every demotion came from
an RM-side premise nobody had measured - gap 8 needed a typed accessor not
reverse engineering; the V Rising wiki publishes no boss health on any of 64
pages; RM suffers 0 of 9 sessions with an unbacked "tests pass" claim; 544 of 544
tests pass with the game off. **Stage 2 scored good tools against beliefs about
Red Moon.**

Stage 6 adopted four work items and killed a fifth - **and the fifth died because
my own plan committed the project's signature failure inside the document
diagnosing it.** S7.4 proposed pinning the ingest census "for the six promoted
tables"; `shape_census` reaches FOUR, and the 1,818-row combat table is
structurally invisible to it.

### The gate that had been dead since it was written

The operator reported consoles flashing on the session hooks. `pythonw.exe` is
GUI-subsystem, so a hook has NO console - which makes the hook windowless and its
CHILDREN not. `rm_facts.py` spawning `schtasks` was visible 5 of 5 for **2.0 to
2.3 seconds**, taking the foreground.

**The flash was the symptom; the real defect was underneath it.** My first fix
carried the comment "not needed on the `sys.executable` call site". False:
`ruff/__main__.py` re-execs `ruff.exe`, so the GRANDCHILD allocated a console and
bound its handles there. Measured: `rc 1, stdout LENGTH 0` against `rc 1, 278
chars` from the resolved binary. `check_staged` reads stdout only when rc is 1,
so **the ruff half of the precommit gate passed every commit while ruff was
failing** - and it passed its own tests because pytest's parent owns a console.

**The exemption was the bug, twice.** The first AST auditor exempted
`sys.executable` spawns, whitelisting exactly the broken site. Deleted; the rule
is unconditional and `pytest_guard.py` carries the inert flag rather than an
exemption.

### Process notes

- **The fan-outs earned their cost.** 13 agents on stage 4/5, 4 on the stage 6
  plan, 7 on the console bug; 0 errors across 24. Two refuters withdrew their own
  measurement errors mid-pass. I re-ran every load-bearing count myself - 13 of
  13 reproduced on the stage 4 adjudication, and the console verdict's central
  claim reproduced on my own probe.
- **An adversarial pass on MY work found more than one on the tools did.** The
  stage 6 plan challenge killed an item and rewrote three criteria; the console
  fan-out found a defect I had explicitly dismissed in a code comment.
- **A null from an instrument that cannot produce a positive is not evidence.**
  The 2026-07-26 console probe filtered for `cmd.exe`, polled 120 s against a
  once-per-session event, and used `Win32_Process`, which has no window field at
  all. Memory corrected rather than deleted.

## 2026-08-01 (seventh stretch) - The run did not happen, and the three things blocking it did

Ledger 003m. Suite **544 passed in 20.02s exit 0** (526 before, +18), ruff clean,
ascii_guard exit 0. No C# change, no rebuild, no redeploy. **NO ROADMAP ITEM
CLOSED.**

**THE MAIN TRACK WAS NOT ATTEMPTED, DELIBERATELY.** The session was scoped to
the power-stat experiment at the CLIENT. Neither bridge port answered and no
V Rising process was running. The run needs a human in-world - equip a weapon so
the two power stats diverge, slot Ward of the Damned, find a survivable
non-V Blood target, cast about 30 times in isolation - and the operator was not
available. It is deferred intact rather than approximated. `P(G)` is still
undefined.

**WHAT IS DIFFERENT NEXT TIME.** Three things that would have cost time mid-run
are now closed:

1. **`tools/find_target.py`.** `ANCHOR_RUNS.md` said "find the target's prefab
   guid" without saying how. It lists SPAWNED units over
   `/dump/components?instanced=1` and MARKS V Bloods and prefab rows rather than
   dropping them - a tool that silently filters teaches the operator the list was
   complete.
2. **The caster-side precondition is a CHECK, not a warning.** The arm response
   is the first and only place `PhysicalPower` versus `SpellPower` is
   observable. `ANCHOR_RUNS.md` now says STOP and re-gear rather than describing
   the failure after the fact.
3. **`bloodforge/series.py`.** The engine no longer imports a `tools/` script.
   The re-export is asserted BY IDENTITY, plus an AST check that nothing under
   `bloodforge/` imports from `tools/` - the layering rule, not the one module
   that broke it. Duplicating the two functions was the worse option: two copies
   of the isolation rule can drift, which is what this protocol exists to catch.

**A DATA FIX THAT ALSO RECOVERED THE BROKEN STATE.** `rmdata_ingest` promoted by
copying and left `tables/_incoming/` populated, so promoted and pending were
indistinguishable on disk. Promotion now empties it on the SUCCESS path only -
refused and validated-but-unaccepted runs still leave the rows for inspection.
The six stale files were SHA256-compared against their promoted copies,
identical on all six, and removed.

**Doc drift, found by looking rather than reported.** `ARCHITECTURE.md` listed
the engine as `agents/bloodforge/`, a path that has never existed. Fixed, and
the module map now names all six real modules. Historical specs and plans keep
the old name; they are history.

Inbox clean at open: all 14 `moon_sync_inbox/` files timestamped 10:19 or
earlier against a 13:00 HEAD.

## 2026-08-01 (sixth stretch) - The recorder runs, and its first run corrects four things

Commit `23d40bf`. Suite **526 passed in 20.16s exit 0** (405 before), ruff clean,
ascii_guard exit 0, `dotnet build` 0/0, deployed to both hosts with matching
SHA256. NO ROADMAP ITEM CLOSED. Gaps 12 and 13 opened.

**THE HEADLINE IS WHAT DID NOT HAPPEN.** The power-stat experiment was not run.
It needs the V Rising CLIENT with a live character casting
`AB_Unholy_WardOfTheDamned_AbilityGroup`; the dedicated server runs
`-batchMode -nographics` and has no player. Everything around it is built,
deployed and verified live. The run is one operator session away and
`docs/ANCHOR_RUNS.md` is the procedure.

### What landed

`GET /record/{start,status,stop}` (`HealthRecorder.cs`), the damage model and
DPS cycle (`bloodforge/damage.py`, `dps.py`), the anchor writer
(`tools/anchor_record.py`) and the H1-versus-H2 evaluator
(`bloodforge/powerstat.py`). Built by three subagents on disjoint files; I
re-ran every claimed count and every claimed test myself.

VERIFIED LIVE against a dedicated server with a spawned Dracula: 56 samples in
27.6 s, 0 dropped, `prefab_guid` and the liveness marker restated on 56 of 56,
the prefab correctly rejected. **No NONZERO delta was observed** - nothing
headless damages a boss - and that limit is recorded rather than glossed.

### The four corrections, all from running it

1. **2 Hz, not 4 Hz.** `SampleEveryFrames = 15` is a FRAME count and no frame
   rate had ever been read. Interval median 0.502 s over n=55: 1.99 Hz at
   29.9 fps. Both specs computed the section C tolerances against an assumed
   60 fps. The A.5 gap check is now 3x the OBSERVED median, not 750 ms. Gap 12.
2. **A whole-second clock on a sub-second series.** Caught by reading before
   deploying. `Json.UtcNowMillis` now exists for the recorder alone.
3. **The arm reported a DECLINE as an ABSENCE.** `player_resolved` false while
   samples carried a player block: `Clear()` reset the rescan counter and the arm
   consulted the throttle it had just reset. Third time on this build that a
   silent gate looked exactly like an unwired one.
4. **Corruption cannot be priced under EITHER hypothesis.** All 18 groups carry
   neither a `spell_school` nor `is_weapon_ability`. 60 of 732 unpriceable after
   the experiment, not 42. Gap 13.

### Two things to carry into the next session

- **`max_health` 8107 at n=3**, three boots, three entity indices, 0 on the
  prefab every time. Half of open question 7 answered. The other half - under
  what difficulty, and across a FRESH world - is still open, and no
  `ServerGameSettings.json` is written anywhere so the difficulty is a default
  rather than an observation.
- **THE EXPERIMENT HAS A CASTER-SIDE PRECONDITION.** The character armed against
  reads `PhysicalPower` 10 and `SpellPower` 10, on which both hypotheses predict
  the same number and the run is indeterminate however clean the deltas.
  Section 3.2 rejected the default subject because the ABILITY could not separate
  them; the same run fails on the CASTER side, which neither spec had said.

### Process notes

- **Independent smoke tests found what the suite did not.** `evaluate` raised on
  `statistics.median([])` for a series with zero isolated deltas - which is my
  own flat recording, and which is what a prefab-latched recorder produces. 526
  green tests did not catch it; feeding it one real recorded file did.
- **A stale `.pyc` nearly cost an hour.** Mutating `max(` to `sum(` and back
  gives the same file size, and if it lands inside the same mtime second Python
  reuses the mutated bytecode. Five tests kept failing against correct source.
  Clear `__pycache__` before believing a mutation-test revert.
- All three subagents reported honestly and all their counts reproduced. One
  (`RedMoon.Bridge.csproj` has `EnableDefaultCompileItems=false`) correctly
  flagged a blocker it declined to fix because the file was outside its list.

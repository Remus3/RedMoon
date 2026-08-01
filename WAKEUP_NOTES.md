# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-08-01 (ninth stretch) - Stage 7 ships and the link ingest track closes, with the run deferred a third time

Ledger 003s. Commit `8684aa0`. Suite **588 passed in 26.29s exit 0** (551 at
open, +37), ruff clean, `ascii_guard` exit 0. No C# change, so the deployed DLLs
still match. `ENGINE_VERSION` unchanged. **NO ROADMAP ITEM CLOSED** - but the
link-ingest track is now closed entirely.

**THE POWER-STAT EXPERIMENT DID NOT RUN, FOR THE THIRD SESSION RUNNING.** Probed
at open rather than assumed: no `VRising*` process, no Steam process, zero
listeners across 8770-8790. The operator was asked and chose to defer the run
and take stage 7. `P(G)` is still undefined and every damage number is still
absent. **Put "launch the client first" at the top of the next prompt** - three
sessions have now opened scoped to work that needs a human in-world and found
nothing listening.

The two free wins stay attached to that run rather than becoming their own item:
the client sample rate (gap 12, still unmeasured) and the 425-row
`localization_guid` backfill. Both cost roughly nothing once the client answers.

### Stage 7, all four items, and the track closes at zero tools adopted

**146 extracted, 146 scored, 21 dived, 0 adopted, 4 work items shipped.** The
track's product was never a dependency; it was the corrections its measurements
forced, and now four gates built from them.

- **S7.2** the co-author scan. 0 offenders over 135 commits. The predicate is
  IMPORTED from `hooks/commitmsg_hook`, not restated.
- **S7.5** the build-pin cross-check `test_drift_anchors` cannot reach, because
  it iterates `git ls-files` and `data/rmdata/` is gitignored.
- **S7.3** the value diff. **The only one of the four closing a failure that
  actually occurred** (`docs/LEDGER.md:740-745`).
- **S7.1** the per-module collected-count map, 33 modules, 588 total.

Built S7.3 BEFORE S7.1, against the stated order. S7.1 pins a per-module count
map and S7.3 adds a test module, so the stated order guarantees writing the pin
twice. The plan says the order is convenience with no dependency, so this is
within it - but it is a deviation and it is written down.

### Three findings, all the same shape

**The S7.2 self-check measured itself.** A test asserting "this module states no
predicate of its own" scanned its own source for the name of the thing it
forbids, matched its own assertion string, and failed on a clean file. It is an
AST walk now, which cannot see inside string literals.

**An EMPTY baseline had to be defined as NO baseline**, which S7.3's criterion
did not anticipate. `seed_tables` writes an empty envelope per table, so a
baseline file exists on any seeded tree and comparing against zero rows reports
all 425 items as additions on the first real ingest. Noise on a REFUSING gate
trains the operator to pass the escape hatch reflexively, which would have
retired the gate on the day it shipped.

**The gate's first finding was in the commit that introduced it.** The first
commit message quoted a real trailer form as prose and passed only because the
line happened to wrap so the quoted text did not start a line. A reflow or a
rebase would have made that commit trip its own new gate. Amended to describe
the form in words.

### And the last open piece, approved and shipped in the same session

Ledger 003t, commit `90c819e`, suite 588 to **598**. S7.5's PRINT half was the
one thing stage 6 left blocked on operator approval. Asked, approved, done -
`tools/rm_facts.py` is FROZEN and the edit is recorded as such.

**The sentinels were the whole difficulty.** The probe never raises, so failures
come back as VALUES, and two of them compared to each other are EQUAL - so the
obvious `installed == extracted` reports a machine with no game installed as a
perfect MATCH. A green light manufactured by comparing two failures, which is
the same shape as the ruff gate that passed every commit while ruff was failing.
`build_agreement` rejects the sentinels first and reports NOT CHECKED naming the
unavailable source.

`BUILD_SENTINELS` is a named constant the test now IMPORTS rather than restates.
That is S7.2's lesson applied one file over, and worth noticing that it
transferred inside the session it was learned.

**The S7.1 pin moved 3 to 13 on its first real edit** - the gate behaving as
designed, not an obstacle to it.

### Process note

Worked inline, no subagents - R9 (nothing under about three files) and the four
items touch six files between them with no parallel slices. Every count in this
note and in the ledger was re-run rather than carried: the 135-commit history,
the 588-test suite, the 134 non-empty commit bodies and 110,818 characters of
message text, and both build values.

**A bash `grep -ci` for the trailer returned 1 and the real gate returned 0.**
The grep was unanchored where the predicate anchors at line start. The lesson is
the recorded one in a new place - the ad-hoc instrument and the real one
disagreed, and the real one was right. Do not audit a gate with a different
predicate than the gate uses.

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

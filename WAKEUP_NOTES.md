# Wakeup Notes

Last two or three sessions at full fidelity. Archive older entries to
`docs/history_notes.md`.

## 2026-08-01 (tenth stretch) - The repo has a license, which it had been public without

Ledger 003u. Commits `cce7219` and `5a74674`. Suite **598 passed in 27.89s exit
0** (598 at open, +0 - no test touched), `ascii_guard` exit 0. No Python change,
no C# change, `ENGINE_VERSION` untouched. **NO ROADMAP ITEM CLOSED** - licensing
appears nowhere in `ROADMAP.md` or `BACKLOG.md` and never did.

A short, entirely non-technical session, taken on operator instruction: Apache
2.0. It is here at full fidelity mainly because of what the probe found.

**THE REPO WAS PUBLIC AND UNLICENSED.** Verified rather than assumed -
`api.github.com/repos/Remus3/RedMoon` returns `private=False`, and after the
push `license.spdx_id=Apache-2.0`. An absent LICENSE is not a permissive
default; it is all rights reserved. For the entire life of the repo the code
was readable by anyone and legally usable by nobody, and no gate, doc or session
had ever raised it. Nothing in the project's own machinery was ever going to:
every gate RM has checks the code against itself.

**The LICENSE text was fetched verbatim, not retyped**, 202 lines from
`apache.org/licenses/LICENSE-2.0.txt`, appendix placeholder left intact.
Retyping is how a license quietly stops being the license it names, and the
detector matching `Apache-2.0` is the confirmation the body is canonical.
Attribution belongs in `NOTICE`, which is where Apache-2.0 puts it.

**`NOTICE` makes a claim, so the claim was probed first.** It states that
V Rising's assets stay Stunlock's and that RM redistributes none of them.
`.gitignore:16` ignores `data/rmdata/` and `git ls-files data/rmdata` returns 0
- checked BEFORE the sentence was written. This is the same habit as the S7.2
predicate import, in a place where the cost of being wrong is legal rather than
a failing test.

`CLAUDE.md` gained a hard rule as its first entry, 8 lines, file now 10,031
bytes against the 60 KB budget. Not for the license fact but for the two
consequences a future session could violate silently and permanently: no
vendored Apache-2.0-incompatible code, no committed game assets.

**Left open deliberately:** there is no `pyproject.toml`, so nothing declares
`license = "Apache-2.0"` in packaging metadata. Recorded in the ledger as
pending rather than fixed, because inventing packaging metadata to hold one
field is a larger change than this session was asked for.

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

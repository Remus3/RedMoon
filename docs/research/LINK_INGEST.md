# Red Moon link ingest - RM's own review

Started 2026-08-01. Operator-directed. This is a NON-ROADMAP track: it gets its
own ledger entries and must not fold into cycle 3.

## What this is, and what it deliberately is not

The source corpus is `C:\Users\Administrator\Desktop\First-Pass.md`, a document
authored by Riot Commander for Riot Commander. Red Moon reuses its STAGE
STRUCTURE as scaffolding and reuses NONE of its judgements. Specifically:

**Carried over as fact:** the entry id, name, url, one-line what-it-is, the
license string, and the OPERATOR's inline notes (`**!= ... =!**`), which are the
operator's and not RC's.

**Deliberately discarded:** RC's `liftable`, `rc_fit`, `score` and `note`. Those
are answers to a different question - "what can Riot Commander lift" - and a
verdict about a League coaching dashboard says nothing about a V Rising combat
engine. Operator ruling 2026-08-01: RM makes its own plan and its own decisions.

**This is also not last session's pass.** On 2026-08-01 an earlier session
re-scored the corpus for RM, overturned 37 entries downward, landed zero above
5, and adopted nothing. That pass is superseded for two reasons: it scored
against RC's framing of liftability rather than RM's own needs, and - measured
below - it only ever saw 119 of 146 entries.

## THE CORPUS IS 146, NOT 119. Measured, and it is the reason this track reopened.

```
full entries in the source          CCR-001 .. CCR-146   (146, no gaps, no duplicates)
distinct urls                       146
covered by the score-ranked index   CCR-001 .. CCR-119   (119)
counted in the score distribution   n=119
```

The source's own header says "119 links, all `claudemarketplaces.com` MCP
servers, numbered CCR-01 .. CCR-119". **All three claims are stale.** The file
grew a later batch that was scored in place but never added to the index or the
distribution, and that batch includes GitHub and Reddit sources rather than only
marketplace MCP servers.

CONSEQUENCE, stated plainly because it is the whole justification for redoing
this: **every previous pass on either side reviewed 119 and reported it as
complete.** 27 entries - 18% of the corpus - have never been triaged for Red
Moon at all. A count taken from a document's header is not a measurement of the
document.

## RM's rubric

Scored 1-10 for VALUE TO RED MOON AS IT ACTUALLY IS. Red Moon is a single-user V
Rising coaching and analysis project on one Windows box: a BepInEx C# plugin
reading live ECS game state, a Python combat/progression engine (Bloodforge), a
local HTTPS dashboard that does not exist yet, and an ops layer with scheduled
tasks and a shared concurrency governor. Solo operator. No CI, no cloud, no
team, no multi-tenancy, no JS/TS frontend framework in use.

What raises a score:

- **+ Reads or models game/binary state.** RM's hardest problems are all "get a
  true number out of a running game". Anything that helps enumerate, diff or
  validate structured data from an opaque runtime is directly on the critical
  path.
- **+ Falsification, ground truth, or validation.** ROADMAP cycle 3 gap 7 is
  open and blocking: RM has NO way to check a computed DPS/EHP/TTK against
  reality. Anything that supplies an anchor, a golden-record harness, or a
  differential-testing pattern is the single highest-value class right now.
- **+ Local dashboard / visualization UX** that is not a generic web-app
  scaffold. Cycle 4 is a real, unstarted deliverable on port 8778.
- **+ Headless orchestration that survives Windows**, worktrees and a shared
  slot governor. RM has the governor and no loop.
- **+ Runs offline, locally, on Windows, with no account or hosted service.**

What lowers a score:

- **- Solves a problem RM does not have.** Team workflow, code review at scale,
  multi-repo CI, cloud deploy, JS framework docs, ticket systems.
- **- A wrapper around something RM already does directly.** RM reads ECS with
  typed accessors and stores tables as versioned JSON with schema gates. A
  generic "index your codebase" or "remember things" tool competes with a
  working, gated system and must beat it, not merely exist.
- **- Requires a hosted service, an API key, or a vendor account.**
- **- Unclear or absent license.** Not disqualifying by itself, but it caps a
  score until resolved, per the third-party gate.

Bands:

| score | meaning |
|---|---|
| 9-10 | Acts on a BLOCKING RM problem. Plan it now. |
| 7-8 | Real, specific value to a named RM cycle. Deep-dive before deciding. |
| 5-6 | A genuine idea RM could use, but not urgent and not blocking. Park with a reason. |
| 3-4 | Adjacent. RM would have to bend it or itself to fit. |
| 1-2 | Not RM's problem. |

**A score is about the CONCEPT unless the license and platform are clean.** RM
lifts ideas by default and code only deliberately.

## Stages

Reusing RC's stage shape because the shape is sound, with RM's own gate at each.

1. **Extract** - id, name, url, what, license, operator note. RC verdicts
   excluded by construction. DONE: 146 of 146.
2. **Score** - all 146 against the rubric above. DONE: 146 of 146.
3. **Cull** - threshold chosen AFTER scoring, from the observed distribution,
   never before.
4. **Deep-dive** - survivors only, and every claim about a survivor verified
   against its actual source rather than against the one-line summary. **AMENDED
   2026-08-01, twice, and both amendments came from being wrong:** a dive has a
   SECOND half, measuring the RM-side premise the score rested on, because that
   is where every demotion came from; and **a source is UNREACHABLE only after
   two different access routes fail**, because this document twice recorded a
   false absence from trying one and stopping (HTTP 402 on a rendered page whose
   `api.php` answered 200, and "a Reddit post" for a GitHub repository).
5. **Adversarial pass** - challenge every survivor. CHECK THE CHALLENGE'S OWN
   COVERAGE FIRST: a previous fan-out silently truncated its input at 12,000
   chars and left 33 entries unchallenged, and every apparent survivor was an
   artifact of that gap. DONE 2026-08-01, and the coverage check is the reason it
   can be believed - 15 of 15, arithmetic shown, two refuters withdrawing their
   own errors mid-pass.
6. **Plan** - what RM actually builds, in what cycle, with what acceptance. DONE
   2026-08-01. **AMENDED by its own adversarial pass: an acceptance criterion
   must describe a FAILURE THE TEST MUST PRODUCE, never the feature.** Every
   clause phrased as an absence of output ("stands down", "is silent", "sources
   from the right file") is satisfied by a no-op and is not a criterion.
7. **Implement** - against the plan, TDD per CLAUDE.md. OPEN.

## Status

- Stage 1 COMPLETE, 146 of 146 extracted.
- Stage 2 COMPLETE, 146 of 146 scored.
- Stage 3 COMPLETE: threshold 6+, 21 survivors, 125 culled.
- **Stage 4 COMPLETE 2026-08-01: 21 of 21 survivors dived, ZERO adopted.** Six
  by hand (`CCR-146`, `CCR-35`, `CCR-89`, `CCR-39`, `CCR-84`, `CCR-120`) and the
  final 15 by an adversarial six-cluster fan-out, all 15 returning a verdict.
- **Stage 5 DISCHARGED IN THE SAME PASS.** The adversarial challenge was not a
  later stage over stage 4's output, it was a refuter per cluster plus an
  adjudicator whose FIRST task was the coverage check. That is what stage 5
  exists to do, and it reported 15 of 15 covered with the arithmetic shown.
- **Stage 6 COMPLETE 2026-08-01.** Eight candidates: **four adopted with
  acceptance criteria, one DROPPED, one deferred, one blocked on another owner,
  one already discharged.** Zero tools adopted. The plan was itself put through
  an adversarial pass - three lenses plus an adjudicator - which killed one item
  outright and rewrote three criteria. See the self-inflicted findings there:
  the draft committed this track's own signature failure inside the document
  diagnosing it.
- **Stage 7 COMPLETE 2026-08-01, and with it the whole track.** All four items
  shipped, TDD, commit `8684aa0`. Suite **551 to 588**, ruff clean,
  `ascii_guard` exit 0. `ENGINE_VERSION` did not move: none of the four touches
  section 2, 3 or 4 math. None was cycle 3 work and none gated the power-stat
  experiment.
  - **S7.2** `tests/test_commit_history.py`, 14 tests. 0 offenders over 135
    commits. Predicate IMPORTED from `hooks/commitmsg_hook`.
  - **S7.5** `tests/test_build_pin_crosscheck.py`, 3 tests. Both build lines
    read `1.1.13.0-r99712` and neither comparison skipped.
  - **S7.1** `tests/test_collected_counts.py`, 5 tests. Per-module map over 33
    modules totalling 588.
  - **S7.3** `tests/test_value_diff.py`, 15 tests, plus the diff itself in
    `tools/rmdata_ingest.py` and `--accept-value-changes` documented in
    `docs/OPERATIONS.md`.

  **Two things were learned by building it rather than by planning it**, and
  both are the same shape as everything else this track turned up:
  - **The S7.2 self-check could not be written as a text scan.** A test
    asserting "this module compiles no pattern of its own" matched its own
    assertion string and failed on a clean file. It is an AST walk now, which
    does not see inside string literals.
  - **An EMPTY baseline had to be defined as NO baseline in S7.3**, which the
    criterion did not say. `seed_tables` writes an empty envelope per table, so
    comparing against zero rows reports all 425 items as additions on the first
    real ingest - noise that would train the operator to pass the escape hatch
    reflexively and retire the gate on the day it shipped.

**THE RESULT OF THE WHOLE TRACK, stated as an arithmetic identity: 146
extracted, 146 scored, 21 dived, 0 at 7 or above, 0 adopted.** Stage 3's
survivors held one 9, three 8s and nine 7s; after every dive the highest
surviving score in the corpus is 6.

**And the reason is the finding, not the scores.** Across all 21 dives, **not one
entry was demoted because the tool was bad.** Every demotion came from an
RM-SIDE PREMISE that had never been checked - that gap 8 needed reverse
engineering (it needs a typed accessor), that the V Rising wiki publishes boss
health (it publishes none, on any of 64 pages), that RM suffers unverified
"tests pass" claims (0 of 9 sessions), that RM cannot test without the game
running (544 of 544 pass with it off). **Stage 2 scored good tools against
beliefs about Red Moon, and the beliefs were the defect.** Measuring them turned
out to be cheaper than reading the tools, and it is where every correction to
RM's own recorded facts came from.

## Stage 2 - RM scores, the operator's 60-entry deep-review set

Scored against the RM rubric above, not against RC's. Every score is about the
CONCEPT unless license and platform are clean.

### The headline: three entries bear on ROADMAP cycle 3 gap 7, and the previous pass scored all three below 6

Gap 7 - **nothing can falsify a computed DPS, EHP or time-to-kill** - is Red
Moon's only BLOCKING open problem, and it is the one thing the previous pass was
not looking for, because it scored for liftability to a League dashboard. Under
RM's rubric the picture changes:

| id | what it actually offers RM | score |
|---|---|---|
| CCR-39 / CCR-84 | **MediaWiki/Fandom read and search.** V Rising has a large Fandom wiki carrying published boss health, resistances and gear numbers. That is an INDEPENDENT second source against which RM's extracted tables and any computed TTK can be cross-checked. RM currently has exactly one source for every number: its own dumper. | 7 |
| CCR-123 | **talkthrough-mcp** - processes a narrated screen recording FULLY LOCALLY (Whisper transcript, OCR, keyframes). A hand-timed kill against a known V Blood with a known loadout is precisely the anchor `BACKLOG.md` says gap 7 needs, and this is a local, no-account pipeline for turning that recording into timestamps. | 7 |
| CCR-74 | **goldencheck** - zero-config tabular validation with DRIFT detection and health scores. RM's whole data floor is versioned JSON tables behind schema gates, and this session shipped a count pin specifically because drift is the failure mode no per-row gate can see. | 8 |

None of these SOLVES gap 7 on its own, and it is worth saying plainly: **nothing
in the 146-entry corpus supplies a ground-truth anchor for combat math.** These
three supply the plumbing for one. The anchor itself still has to be produced by
recording a real kill.

### The entries that automate a rule RM already writes down by hand

| id | why it scores high for RM | score |
|---|---|---|
| CCR-143 | **red-handed** - a local read-only CLI auditing session transcripts in `~/.claude/projects` against git to check "tests pass" claims. RM's single most-repeated discipline is exactly this: CLAUDE.md has a Verification section, a `verifier` subagent exists, and every session prompt says re-run any agent's claimed counts yourself. MIT, local, no account. | 9 |
| CCR-146 | **Subagent system-prompt inheritance.** Custom subagents do NOT inherit the main agent's system prompt - theirs is the agent file body alone. RM runs a `verifier` subagent and carries hard rules (7-bit ASCII, no co-author trailer, frozen files) in CLAUDE.md. If those do not reach a subagent, RM's subagents have been running WITHOUT its hard rules. This is a correctness question about RM's existing setup, not a feature. | 8 |
| CCR-81 | **skylos** - local static analysis including AI-hallucination checks for fake helpers and invented APIs. CLAUDE.md's Testing Discipline rule is literally "grep to confirm every method, field and data shape exists; never scaffold against an assumed API surface". | 7 |
| CCR-127 | **PreToolUse deny + feed the reason back into context** so the model self-corrects. ~~RM already runs `precommit_gate.py` as PreToolUse; it blocks but does not teach.~~ **CORRECTED 2026-08-01 by stage 4: FALSE.** `precommit_gate.py:195-199` emits a per-violation reason carrying file, line, column, codepoint and the rule it broke, and `BRIDGE_SPIKES.md:1494-1506` MEASURED it reaching the model headless. The PreToolUse half is already done and is richer than the source's. What is real is the other half - `.claude/settings.json` wires exactly `PreToolUse`, `PostToolUse` and `SessionStart`, and no `Stop` hook. | 7 -> 5 |

### Cycle 4 dashboard references

| id | note | score |
|---|---|---|
| CCR-135 | **Codeman** - self-hosted mission control over parallel agent sessions, streamed to any browser. The operator's own note on CCR-120 names this as the stronger UX reference. | 7 |
| CCR-110 | **mockd** - single Go binary mocking HTTP/gRPC, stateful CRUD, OpenAPI digital twins. A mock bridge would let Bloodforge and the dashboard be tested WITHOUT launching V Rising, which today is required for any integration check. | 7 |
| CCR-115 | memi - read-only design audit flagging a11y and hierarchy risks. Useful once 8778 exists, useless before. | 5 |

### Headless track

| id | note | score |
|---|---|---|
| CCR-55 | Kagan - agent kanban with MANDATORY human gates and isolated worktrees. Maps onto RM's worktree concern and its "no commit while an agent is live" rule. **This line omitted that Kagan is an OpenCode plugin and OpenCode is not installed, which is what made a 6 look reasonable.** 6 -> 3, stage 4. | 6 |
| CCR-121 | Graph Skill - node-level cached retry, so a failed slice re-runs one node rather than the cycle. RM has no loop yet; this is a design input for when it has one. | 6 |
| CCR-109 | task-orchestrator - server-enforced workflow gates, persistent work-item graph, actor attribution. | 5 |
| CCR-28 | mcp-funnel - filters and renames which MCP tools are exposed. RM's session loads a very large deferred tool surface; narrowing it is real. | 5 |
| CCR-58 | Claude Flow - enterprise swarm, 16+ roles, 80+ tools. Overkill for a solo single-box project. | 3 |

### Process and prose

| id | verdict | score |
|---|---|---|
| CCR-129 | CLAUDE.md snapshotting plus externalising keeper rules. RM's CLAUDE.md is size-budgeted under 60 KB with a test asserting it; this is the same problem, already half-solved here. | 6 |
| CCR-132 | Structured handoff file per session. RM already has `WAKEUP_NOTES.md` plus `NEXT_SESSION_PROMPT.md`, and the operator has now asked for a desktop `RM-NEXT-SESSION.txt` - which IS this pattern, so the corpus corroborates a decision already taken. | 5 |
| CCR-137 | memU - mines session logs into an editable persistent memory. RM's memory namespace is hand-maintained. | 5 |
| CCR-141 | Minimalist project-specific CLAUDE.md after Anthropic trimmed the default system prompt. | 5 |
| CCR-19 | agent-replay-debugger - deterministic step replay. RM's Workflow tool already has `resumeFromRunId` prefix caching. | 5 |
| CCR-124, CCR-126, CCR-131, CCR-133, CCR-134, CCR-139, CCR-142, CCR-145 | Prose style and prompting rules. RM's CLAUDE.md already encodes the substance of most - Output Constraints, the Corrections rule ("narrate the work, not the worker" is almost verbatim), and State assumptions explicitly. Recorded as corroboration, not as lift. | 3-4 |
| CCR-130 | Claude Queue - experimental `q`/`s` follow-up patch. | 3 |
| CCR-140 | Nauro - commit ADRs to `decisions/` and instruct CLAUDE.md to consult them. RM already has `docs/adr/`, the index pointer in CLAUDE.md, and a test asserting the two agree. Solved, and better. | 3 |
| CCR-36 | mcp-adr-analysis-server - ADR management plus code-to-ADR graph. Same territory, 7 ADRs does not need a graph. | 4 |
| CCR-116 | pindoc - typed artifacts pinned to code locations. RM has the ledger and BRIDGE_SPIKES. | 4 |

### The codebase-graph and token-reduction cluster: RM is too small for any of it

`CCR-01, CCR-09, CCR-59, CCR-70, CCR-79, CCR-82, CCR-88, CCR-102, CCR-113, CCR-114`
all index a codebase into a graph to answer structural queries in fewer tokens.

**`core` plus `tools` is about 2,730 lines.** A call graph over 2,730 lines
answers questions a grep already answers instantly. This was the previous pass's
correct finding and RM's own rubric reaches it independently. **2-3 each.**

`CCR-29` (token-enhancer, strips HTML before context) and `CCR-77` (klavis,
smart-selects among 100+ integrations) are the same class one layer out. **4.**

### The rest of the set

| id | verdict | score |
|---|---|---|
| CCR-105 | Uniprof - unified CPU profiler. RM has no measured performance problem; the whole dump is 1.3 s. | 4 |
| CCR-95 | Atomadic Forge - Python AST refactor and compliance scoring. | 4 |
| CCR-37 | delimit - merge gate, signed receipts, semver diff. RM's precommit gate covers the gate; the rest is team-shaped. | 4 |
| CCR-03, CCR-68, CCR-108 | Memory and knowledge-graph layers over markdown. RM's memory namespace is seeded, mirrored and test-asserted. | 4 |
| CCR-34 | workflows-mcp-server - YAML playbook library. | 3 |
| CCR-67 | typeui - hosted design-system server. Hosted, so capped. | 3 |
| CCR-111 | gitwand - merge-conflict auto-resolution. RM is solo on one branch. | 2 |
| CCR-101 | Local Model Suitability classifier. RM runs no local models. | 2 |
| CCR-72 | plumb - Figma to design graph. No Figma in RM. | 2 |
| CCR-25, CCR-26, CCR-100 | Hosted image/video/file multimodal bridges. RM's vision tier is reserved and unbuilt, and these are hosted. | 2-3 |
| CCR-136 | Browser automation stealth findings. RM drives no browser. | 2 |

### Distribution, this set only (n=60)

```
9: 1    8: 2    7: 7    6: 4    5: 9    4: 13    3: 13    2: 11
```

Compare the previous pass, which landed **zero entries above 5 across the whole
corpus**. The difference is not generosity - it is that a rubric asking "what
does a V Rising engine with an unfalsifiable output need" ranks a wiki reader and
a transcript auditor completely differently from one asking "what can a League
dashboard lift".

## Stage 2b - the 84 "not needed" entries, swept rather than accepted

The operator marked 84 entries "not needed" while reviewing RC's triage. Those
notes were written in RC's frame, so RM swept them against RM's own rubric
instead of inheriting the verdict. **Coverage: 84 + 60 review-more + 2 bespoke =
146 of 146.** Stated as an arithmetic identity because the previous pass's whole
failure was believing a count it had not checked.

Most of the 84 are correctly closed and the sweep confirms it: EU AI Act
compliance tooling, GitLab and TeamCity CI bridges, SEO and backlink analysis,
trade-document validation, incident management, business advisors, 3D website
generators, cloud media pipelines and a dozen memory-layer and MCP-aggregator
variants. None of that is a single-user V Rising engine's problem.

**Six are OVERTURNED UPWARD, and one cluster is the most consequential finding
in the whole corpus.**

### THE BINARY REVERSE-ENGINEERING CLUSTER - overturned to the second-highest scores in the corpus

| id | license | why RM's rubric ranks it completely differently | score |
|---|---|---|---|
| CCR-35 | MIT | **pyghidra-lite** - token-efficient Ghidra wrapper for PE binaries, shared JVM, read-only by default. | **8** |
| CCR-89 | MIT | **x64dbg** - drives the x64dbg debugger through 23 tools: memory reads, breakpoints, disassembly. | **7** |

This is the single clearest case of RC's frame hiding RM's need. A League
coaching dashboard has no binary to reverse; **Red Moon's hardest problem class
is nothing else.** Concretely, from RM's own recorded history:

- `BACKLOG.md` carries "Offline parser for the DOTS ECS blobs (`ContentArchives`,
  `EntityScenes`), so item stats need no running game", REJECTED for cycle 1 on
  "per-patch reverse-engineering cost against a moving binary format". **These
  two tools are precisely the cost-reduction on that rejection.**
- Cycle 2 needed an exhaustive field scan across **169 interop assemblies** to
  prove `items.tier` had no source, and built a throwaway `System.Reflection.
  Metadata` console app to do it.
- Cycle 3 phase 1 had a generic value reader **HARD CRASH the dedicated server
  twice**, and the diagnosis stopped at "GetComponentBoxed does not hand back
  chunk-backed memory". A debugger is how that stops being a guess.
- `max_health` being instance-only was settled today by comparing a prefab to a
  live instance. Every future question of that shape is a memory question.

Neither is adopted here - stage 4 has to check that pyghidra-lite handles
IL2CPP-flavoured PE and that x64dbg driving is safe against a live game process.
But scoring them 2 because a League dashboard cannot use them was the error.

### The data-validation family, consistent with CCR-74

| id | license | note | score |
|---|---|---|---|
| CCR-50 | MIT | **AnomalyArmor** - schema-drift, freshness and null-rate anomaly monitoring. Same class as goldencheck, which scored 8. RM shipped a count pin TODAY precisely because drift is the failure no per-row gate sees. | 7 |
| CCR-80 | MIT | **goldenflow** - 76 normalization transforms for messy tabular input. Weaker than the above; RM's data is machine-generated, not messy. | 6 |

### Three that answer a problem RM hit this session

| id | license | note | score |
|---|---|---|---|
| CCR-75 | MIT | **rendex-mcp** - scheduled URL change-watch with visual and text diff. RM pins the game build in ~~about 97~~ **120** tracked sites (RECOUNTED 2026-08-01; `tests/test_drift_anchors.py:6` carries the same wrong figure) behind a drift-anchor test, and finds out a patch landed by noticing. **Stage 4: rendex is a hosted SaaS needing an API key, and `RM-DataRefresh` is installed and Ready - detection exists, it just emits no operator-visible signal.** | 6 -> 2 |
| CCR-76 | MIT | **temporal-mcp** - elapsed time between turns, day rollover, resumed-session detection. ~~RM lost a run today to a control taken at 5 s of server uptime when the subject appears at 20 s, and its session notes rule requires converting relative dates to absolute.~~ **BOTH CLAUSES CORRECTED 2026-08-01 by stage 4.** The uptime case is a READINESS problem, not a time one - RM's own rule is "poll for the SUBJECT, never for `ready:true`". And **the date rule does not exist**: grepped repo-wide, case-insensitively, with no include filter, "relative dates to absolute" returns exactly ONE hit - this line, asserting it. An invented citation inside RM's own review document. | 6 -> 2 |
| CCR-144 | prose | **Eliciting critical feedback** - three follow-up prompts that break uncritical agreement ("argue against me", "what are you least confident about"). RM's single most repeated failure mode across sessions is an agent's unverified claim being believed, which is why CLAUDE.md carries a Verification section and a `verifier` subagent. | 6 |

### The rest of the 84, confirmed closed

| band | ids | reason |
|---|---|---|
| 5 | CCR-64, CCR-85, CCR-98, CCR-107, CCR-128 | Real but not urgent: web search for stage-4 deep dives, cross-session memory indexing, pre-install package verification, multi-language snippet execution, and the epic-to-worktree parallel pattern RM already half-practises. |
| 3-4 | CCR-08, CCR-12, CCR-33, CCR-38, CCR-56, CCR-57, CCR-62, CCR-71, CCR-83, CCR-87, CCR-92, CCR-104, CCR-106, CCR-112, CCR-122, CCR-125 | Adjacent. RM would have to bend the tool or itself. Includes the browser and screen-control cluster, which R3 already restricts to rendered-pixel checks and live-game capture. |
| 1-2 | the remaining 57 | Not RM's problem. Compliance and audit-attestation tooling (CCR-13/14/15/17/18/20/97/99), CI and repo hosting (CCR-06/41/43/73), aggregators and routers (CCR-11/16/69/93/117/118/119), SEO and market intel (CCR-23/40/45/96), memory-layer variants competing with a system RM already has seeded, mirrored and test-asserted (CCR-05/10/48/51/90/91), and hosted or credit-metered services (CCR-07/27/31/49/53/60/94). |

### The two bespoke notes, answered directly

**CCR-04 Augments** - operator asked: "would the score change if we ever ported
or are sharing the share folder to a JS framework?" **Yes, conditionally, and it
is worth writing down because cycle 4 has not chosen a stack yet.** Today it
scores **2**: Augments injects npm and JS-framework API docs, and RM is Python
plus C# with no JS anywhere. If cycle 4's dashboard on 8778 adopts a real
framework rather than server-rendered HTML, it rises to about **5** - not
higher, because it serves generic framework docs and RM's dashboard difficulty
will be domain shape, not React API recall. **The decision this actually flags
is upstream: cycle 4 has no declared frontend stack, and that choice should be
deliberate rather than emergent.**

**CCR-120 claude-task-viewer** - operator asked for whole-project dashboard
concepts, categorized and agent-adjudicated, not a Loop Monitor rehash. Scored
**6** as an OBSERVER-posture reference: it renders state it does not own, over
SSE rather than poll-and-repaint, with dependency edges, cross-session fuzzy
search and stale-session auto-archive. **Carried into the cycle 4 dashboard work
next session together with CCR-135 (Codeman), which the operator named as the
stronger of the two.**

## Stage 3 - the cull, threshold chosen from the observed distribution

All 146 now scored.

NO HISTOGRAM IS GIVEN, and the reason is a correction rather than an omission. A
draft of this section carried a per-score distribution that did not reconcile
with the survivor list below it - it claimed 24 entries at 6 and above while the
enumerated table held 21. The counts in the low bands were grouped rather than
counted, because the sections above deliberately bundle whole clusters into one
row ("the remaining 57", "the graph cluster, 2-3 each"). **A distribution that
cannot be reconciled against the enumerated rows is exactly the unchecked count
this whole document exists to correct**, so it is withdrawn rather than tidied.

What IS enumerable, and therefore what is stated: the survivors, individually,
by id.

**Threshold: keep 6 and above. 21 entries survive, 125 are culled.**

Chosen after scoring, from the shape of the distribution rather than picked in
advance: there is a natural break between 6 and 5. Everything at 6+ names a
specific RM cycle or an open blocking problem; everything at 5 is "a good idea
RM has no cycle for". Setting it at 7 would drop the drift-watch and
critical-feedback entries that answer failures RM hit this same session, and
setting it at 5 admits 15 more with nowhere to put them.

### The 21 survivors, every one named

| score | id | one line |
|---|---|---|
| 9 | CCR-143 | red-handed - audit "tests pass" claims against git |
| 8 | CCR-74 | goldencheck - tabular drift validation |
| 8 | CCR-146 | subagents do not inherit the main system prompt |
| 8 | CCR-35 | pyghidra-lite - PE binary RE |
| 7 | CCR-81 | skylos - invented-API detection |
| 7 | CCR-39 | MediaWiki - independent second source for boss numbers |
| 7 | CCR-84 | MediaWiki professional - same route, second implementation |
| 7 | CCR-123 | talkthrough - local narrated-recording pipeline |
| 7 | CCR-135 | Codeman - dashboard UX reference |
| 7 | CCR-110 | mockd - mock the bridge, test without the game |
| 7 | CCR-127 | PreToolUse deny plus reason fed back |
| 7 | CCR-89 | x64dbg - debugger driving |
| 7 | CCR-50 | AnomalyArmor - schema drift monitoring |
| 6 | CCR-55 | Kagan - agent gates plus isolated worktrees |
| 6 | CCR-121 | Graph Skill - node-level cached retry |
| 6 | CCR-129 | CLAUDE.md snapshotting and keeper-rule externalisation |
| 6 | CCR-120 | claude-task-viewer - observer posture, SSE |
| 6 | CCR-75 | rendex - scheduled change-watch on the build pin |
| 6 | CCR-76 | temporal - elapsed time and resumed-session detection |
| 6 | CCR-144 | eliciting critical feedback |
| 6 | CCR-80 | goldenflow - normalization transforms |

Counted from the rows above: 1 at nine, 3 at eight, 9 at seven, 8 at six.
**21.** CCR-39 and CCR-84 are two distinct entries reaching the same source and
are listed separately rather than merged, so the count reconciles.

**The scores in this table are STAGE 3 scores and are deliberately not rewritten
as stage 4 moves them.** `CCR-35` reads 8 here and is 4 after its dive; `CCR-89`
reads 7 here and is 5. The cull was chosen from the distribution as it stood, and
retro-editing the inputs to a threshold after the fact is exactly the unchecked
count this document exists to correct. Post-dive scores live in stage 4, and the
survivor list stays 21 so the arithmetic above keeps reconciling.

## Stage 4 - the deep dive, OPENED 2026-08-01

Started with `CCR-146` on operator direction, because it is a correctness
question about Red Moon itself rather than a feature.

### CCR-146 - subagent system-prompt inheritance. REFUTED for RM's setup, with a nuance.

**The claim:** custom subagents do NOT inherit the main agent's system prompt;
theirs is the agent file body alone. **The stake:** Red Moon runs a `verifier`
subagent and keeps its hard rules - 7-bit ASCII, the co-author trailer ban,
frozen files - in `CLAUDE.md`. If those never reach a subagent, every subagent
this project has ever run has been running without them.

**Measured directly rather than reasoned about.** RM's own `verifier` agent was
dispatched with a probe forbidding all tool use, so nothing could be read off
disk, and asked to quote specific rules from context alone. It returned the ASCII
rule and the co-author-trailer rule **verbatim**, including the incidental
clause "14 of the 30 commits before it was enforced carried the trailer", and
enumerated all 17 `CLAUDE.md` H2 headings plus the `MEMORY.md` index. Zero tool
calls. It could not have fabricated that text.

**VERDICT: the hard rules DO reach subagents, and RM was never exposed.** But
the subagent's own account of the mechanism is the part worth keeping: the rules
arrive as a **`system-reminder` injection, not as part of the system prompt
proper**. So `CCR-146` is literally true about the system prompt and irrelevant
to the thing that would have mattered. A claim can be accurate and still answer
the wrong question - the same shape as cycle 2's "0 of 425 localization guids",
which was correct about a headless host and had been written down as a statement
about the game build.

**Scope of the measurement, stated rather than generalized.** One agent type
(a project-level `.claude/agents/verifier.md`), one harness, one version - and
that version is **2.1.219**, the desktop app, not the 2.1.220 npm CLI on PATH.
UNVERIFIED for plugin-supplied agents, for worktree-isolated agents, and for
headless runs. Do not restate this as "subagents always inherit CLAUDE.md".

**Consequence, acted on the same session:** the three dashboard concept agents
and the gap 7 spec agent were all dispatched knowing the rules would arrive, and
all four returned 0 non-ASCII bytes.

### Incidental to the same session, and it belongs in this document

RM was named the version tiebreak on the headless hook question. Two facts
measured while here: **the `claude` on PATH is 2.1.220 and the interactive
desktop host is 2.1.219**, so RM runs two CLI versions at once and any RM
finding must say which produced it. And RM's headless model resolution is
CLEAN - `claude -p` with no `--model` returns correctly, exit 0 - so the
`rc-main` alias LW still sees is not machine-wide and RM is unaffected.

### CCR-35 pyghidra-lite and CCR-89 x64dbg - the binary-RE pair. BOTH DEMOTED, and the reason is not about the tools.

Dived 2026-08-01, together, because stage 2b overturned them together on one
shared argument: "a League coaching dashboard has no binary to reverse; Red
Moon's hardest problem class is nothing else." **That argument does not survive
a check of what RM's hardest problems actually are.** Sources read at
`claudemarketplaces.com`; every RM-side fact below was re-measured on this
machine rather than taken from a document.

#### The root error: gap 8 is not a binary-RE problem

Stage 2b scored the pair on RM's need to read
`ProjectM.ResistanceData.FireResistance_DamageReductionPerRating` - ROADMAP
gap 8, the one resistance that varies across the 65 bosses and the one RM cannot
price. The phrase carried through three documents is "a global ECS constant that
has never been read", and "never been read" was silently treated as "hard to
read". MEASURED, from the saved phase 1 payload
`_scratch/rmprobe/c3/CHAR_Vampire_Dracula_VBlood.json` rather than from the prose
describing it:

```
ProjectM.ResistanceData        buffer False   zero_sized False
  FireResistance_DamageReductionPerRating      System.Single
  HolyResistance_DamageReductionPerRating      System.Single
  SilverResistance_DamageReductionPerRating    System.Single
  GarlicResistance_DamageReductionPerRating    System.Single
  ... 11 fields, every one System.Single
```

`ResistanceData` is one of the 150 components enumerated on the Dracula entity
and `docs/BRIDGE_SPIKES.md:1043` records it as present on the PREFAB AND the
INSTANCE. The field is a plain float on a component the dumper already walks, and
the plugin already reads `UnitStats.FireResistance` off the same entity with a
typed accessor. **The constant is an unwritten reader, not a reverse-engineering
job.** Neither tool is on the path to it, and a tool adoption argued from that
need was argued from a premise nobody had checked.

Stated precisely, because "unwritten reader" is not "already done": adding it
still costs a plugin change, a rebuild, a deploy to both hosts and a live run.
What it does not cost is Ghidra, a debugger, or a per-patch RE budget.

#### CCR-35 pyghidra-lite - check 1 FAILS. 8 -> 4.

**The check stage 4 owed: does it handle IL2CPP-flavoured PE?** No evidence that
it does. The server exposes 9 tools (`load`, `delete`, `binaries`, `info`,
`functions`, `code`, `xrefs`, `search`, and `annotate` behind `--allow-write`),
supports ELF, Mach-O and PE, and auto-detects Swift, Objective-C and
Hermes/React Native runtimes. **IL2CPP, Unity and .NET are not mentioned at
all.** It requires Ghidra 11.x and JDK 21+ installed locally, and defaults to a
"fast" profile that disables 20 analyzers to fit MCP timeouts. MIT.

Ghidra will happily load `GameAssembly.dll` as a PE - it is native code. That is
not the difficulty. The structure worth recovering from an IL2CPP build lives in
`VRising_Data/il2cpp_data/Metadata/global-metadata.dat`, which is PRESENT on
this install (verified), and recovering it is what Il2CppDumper and
Il2CppInspector are for. pyghidra-lite does not do that step and does not claim
to. Auto-detecting Hermes and Objective-C while saying nothing about IL2CPP is
the shape of a tool built for a different corpus.

**And RM is on the wrong side of the process boundary for it to matter.** RM
reads the game from INSIDE, through BepInEx, against 172 generated interop files
carrying real type and field names (169 DLLs; `BRIDGE_SPIKES.md:63` already
reconciles the two counts). That is why cycle 2 could enumerate 67 `Tier`-shaped
fields across 169 assemblies and PROVE `items.tier` had no source. Ghidra
operates from outside on stripped native code to recover names RM already has.

Rescored **4** - adjacent, RM would have to bend the tool or itself. The one
thing that would raise it again is `BACKLOG.md`'s offline ECS-blob parser
(`ContentArchives`, `EntityScenes`), rejected for cycle 1 on per-patch RE cost.
That rejection stands, and if it is ever reopened this entry is re-dived, not
re-scored from this line.

#### CCR-89 x64dbg - check 2 is ANSWERED UNFAVOURABLY on blast radius, not on anti-cheat. 7 -> 5.

**The check stage 4 owed: is driving x64dbg safe against a live game process?**
Two halves, and they come apart.

*The anti-cheat half is not the problem here, measured.* A search of the install
tree to depth 2 finds NO EasyAntiCheat binary of any kind. Scope stated rather
than generalized: that is a fact about this BepInEx-modded local install, which
is the only host RM ever drives, and says nothing about official servers.

*The blast-radius half is the problem.* The 23 tools are not a reading surface.
They include memory write, allocate and protect, byte patching, PE dumping,
import-table fixing, and anti-debug hiding, alongside the reads. The 2.3.0
hardening the page advertises is about the plugin's own HTTP listener on
`127.0.0.1:27042` - "a malformed HTTP request can no longer crash x64dbg" - not
about the target. The docs assume an already-open debugging session and do not
address attaching to a running process at all, which is precisely the mode RM
would need. MIT, fully local, TypeScript bridge over a C++ x64dbg plugin.

**The RM need it would serve is real and is also retired.** Cycle 3 phase 1 had
a generic value reader HARD CRASH the dedicated server twice, and the diagnosis
stopped at "GetComponentBoxed does not hand back chunk-backed memory" - a guess a
debugger would have turned into an observation. But RM's response was to BAN the
approach: "DO NOT BUILD A GENERIC VALUE READER... use TYPED accessors", recorded
twice as a failure. A debugger that would diagnose a crash RM has decided never
to re-cause is not urgent.

Rescored **5** - a genuine capability with no current RM problem that needs it,
parked with a reason.

#### What this dive is actually evidence of

The pair was called "the single clearest case of RC's frame hiding RM's need"
and "the sharpest overturn in the corpus". The overturn reasoned from RM's
PROBLEM CLASS - RM reverse-engineers a game, therefore RE tools score high -
without checking whether the specific problem cited was already reachable by a
route RM owns. It was: a typed accessor on an enumerated component, one grep and
one saved payload away.

**This is the fourth instance of the same shape in this project** - after
ability_stats 1474 versus 1818, the corpus 119 versus 146, and
`vblood_damage_modifier` range versus binary. Each time a plausible statement
was reasoned about rather than counted. Here the uncounted thing was RM's own
capability, which is the harder case, because the document making the claim was
RM's.

Both entries stay in the corpus with their new scores. Neither is culled
retroactively - stage 3's threshold was chosen from the distribution as it stood,
and rewriting it now would be exactly the unchecked-count failure this document
exists to correct. They are recorded as DIVED AND DEMOTED.

### CCR-39 and CCR-84 - the MediaWiki pair. BOTH DEMOTED 7 to 4, and the dive produced the value the entries promised WITHOUT them.

Dived 2026-08-01, together, because stage 2 scored them together on one shared
claim: the V Rising Fandom wiki carries "published boss health, resistances and
gear numbers", making it "an INDEPENDENT second source against which RM's
extracted tables and any computed TTK can be cross-checked", and "RM currently
has exactly one source for every number: its own dumper."

Two checks named in advance. **Check 1 is about the DESTINATION and is decisive:
does the wiki actually publish the numbers?** Check 2 is about the tools. Check 1
was run first deliberately, because if the wiki does not carry the data then no
client for it can matter. Payloads saved to `_scratch/rmprobe/wiki/`.

#### Check 1 FAILS. The wiki publishes no boss health and no boss resistances, measured over all 64 pages.

Not sampled - enumerated. `Category:V Blood Carriers` returns **65 members, 64
of them boss pages** plus the category page itself. Every page's wikitext was
fetched and its `{{Boss Infobox}}` parsed. Parameter coverage:

```
title  40    unlocked_recipes    35    unlocked_structures     30
image  40    unlocked_spells     34    unlocked_vampirepowers   4
level  40    location            39    voice_actor              1
unit_id 40   description         40    NO BOSS INFOBOX AT ALL  24
```

**No `health`, no `hp`, no `max_health` and no resistance parameter exists on any
page.** And 24 of 64 carry no infobox whatever, which is a different and worse
statement than a missing field - the same distinction ADR-007 forced on the
damage block.

A free-text scan of all 64 pages for health and resistance language finds 5 `HP`,
1 `max health` and 15 `resistance`, and **every one of them is the wrong kind of
number**:

- Every health mention is a PHASE-TRANSITION THRESHOLD stated as a PERCENTAGE -
  "at 50% HP he jumps into the air and summons two gargoyles", "at the 75% max
  health threshold, she will place an Iron Maiden". A percentage of an unstated
  pool is not a second source for the pool.
- Every resistance mention is player-side: a Holy Resistance Potion recipe, a
  Minor Garlic Resistance Brew, a soul-shard buff granting "+50 sun resistance",
  or prose noting that a boss deals Holy damage. **Not one is a boss's own
  resistance value.**

No page states a game version, a patch, or a difficulty. So even a number found
there could not be pinned to `1.1.13.0-r99712` or to Normal, and ROADMAP gap 9
makes difficulty a required axis.

**The one number RM most needs is exactly the one that is absent.** Boss
`max_health` is instance-only, reads 0 on all 65 prefabs, and was measured at
8107 for Dracula at n=3. The wiki does not carry it. The stage 2 claim was
written from a plausible belief about what game wikis contain, and this project's
rule is to count rather than to believe.

#### But the join key is real, and it corroborates something.

The infobox carries `unit_id`, and `unit_id` **IS** RM's `prefab_guid` - Dracula
reads `-327335305` on the wiki and `-327335305` in `vbloods.json`. Joined:

```
wiki pages with unit_id       40
matched into vbloods.json     40   (0 unmatched)
level agrees                  40   (0 disagree)
```

**40 of 40 on both, which is the first independent second-source confirmation of
anything in `data/rmdata/`.** It corroborates IDENTITY and LEVEL. It says nothing
about health, resistances, power or any combat quantity, and must never be cited
as though it did.

Coverage stated rather than rounded: **25 of RM's 65 rows have no wiki
`unit_id`**, among them `CHAR_Bandit_Leader_VBlood_UNUSED` - correctly absent
from a player-facing wiki, and a small check on the wiki's editorial judgement
rather than a hole in it - and the whole Blackfang set.

#### Check 2: both servers work, both are far larger than the need, and neither was used.

| | CCR-39 olgasafonova | CCR-84 professionalwiki |
|---|---|---|
| tools | 40+ | 37+ |
| runtime | Go 1.24+ | Node, via `npx` |
| access | read anonymous; edit needs a bot password | read anonymous; write needs OAuth2 or a bot password |
| license | MIT | MIT |
| extras | broken-link and orphan QA, stale-content checks, PDF search via `pdftotext` | multi-wiki, Semantic MediaWiki / Cargo / Bucket extension tools, 50 KB content cap |

Both are honest, MIT, locally runnable and read public wikis without an account.
Neither is wrong. **They are wrong-sized.** RM needs two read calls -
`list=categorymembers` and `prop=revisions` - and both servers ship a
content-management surface for people who maintain a wiki. RM maintains no wiki.
CCR-39's headline extras - broken links, orphans, stale content - are quality
tooling for a wiki's editors.

**The decisive fact is how this dive was performed.** The category enumeration,
64 page fetches, infobox parse and 40-row join were all done with `urllib`
against the public `api.php`, with neither server installed and no account.
Fandom answered anonymously, `MediaWiki 1.43.9`, HTTP 200 throughout. That is
RM's ordinary ingest shape already - an HTTP JSON source behind a schema gate -
and the rubric explicitly lowers a score for "a wrapper around something RM
already does directly".

Rescored **4** each, for the same reason, and kept as two rows rather than merged
so stage 3's arithmetic still reconciles.

**One trap worth recording for whoever comes next.** `WebFetch` on the rendered
page `vrising.fandom.com/wiki/Dracula_the_Immortal_King` returns **HTTP 402
Payment Required**, while `api.php` on the same host returns 200. An agent that
tries the page and not the API will conclude the wiki is unreachable and record a
false absence - the exact failure shape this document keeps meeting.

#### What RM should take from this, since it is not either server

The route is real and cheap: **a wiki join on `unit_id` is a working, if narrow,
external check on RM's boss identity and level extraction.** It is worth a small
scheduled probe rather than a 40-tool dependency, and it belongs to stage 6 to
name with an acceptance criterion, not to this dive to adopt. What it can never
be is the falsification anchor gap 7 needs - the numbers simply are not there,
and the anchor still has to come from a recorded run.

### Stage 4 is COMPLETE - 21 of 21 survivors dived

The final 15 were dived on 2026-08-01 by a six-cluster fan-out, every cluster
adversarially challenged by an independent refuter and the whole set adjudicated
with a coverage check taken BEFORE any verdict. 13 agents, 0 errors, 15 of 15
entries returning a real verdict. The orchestrator then independently re-ran 13
of the adjudication's load-bearing counts; **all 13 reproduced exactly.**

Two refuters caught and withdrew their OWN measurement errors mid-pass. That is
the opposite of the truncation event stage 5's standing warning exists for, and
the coverage arithmetic reconciles: 1 + 3 + 2 + 3 + 3 + 3 = 15.

#### The scores

| id | old | new | why |
|---|---|---|---|
| CCR-143 red-handed | 9 | **5** | Reads BETTER at source than its corpus line (9 checks, not 8), but `claim-no-run` measures **0 of 9** RM sessions carrying a pass-claim, and 0 of 127 commits carry the banned trailer |
| CCR-74 goldencheck | 8 | **4** | Scored for drift RM had just pinned; RM's pin is volumetric, goldencheck's drift is distributional |
| CCR-50 AnomalyArmor | 7 | **2** | Mandatory vendor account, warehouse-targeted, and both headline detections have no subject: **0 nulls in 3038 rows** |
| CCR-80 goldenflow | 6 | **3** | 0 of ~6500 strings match any transform shape |
| CCR-81 skylos | 7 | **3** | ruff is already a BLOCKING PreToolUse gate and RM has zero third-party deps, so the headline check has no target |
| CCR-110 mockd | 7 | **3** | **544 of 544 tests pass with the game off**; RM already wrote the mock |
| CCR-127 PreToolUse deny | 7 | **5** | PreToolUse half already done and richer; the `Stop`-hook half is a real gap. **Refuter overturned the dive's 3 and won** |
| CCR-121 Graph Skill | 6 | **6** | The ONLY confirmed premise in the fan-out. Orthogonal to `slots.py`, which has no retry, cache, node or dependency concept |
| CCR-55 Kagan | 6 | **3** | An OpenCode plugin, and OpenCode is not installed. Adopting means a second agent harness |
| CCR-123 talkthrough | 7 | **3** | Anchor is operator-ruled to the shipped bridge-side health series; keyframes cannot tighten a 0.5 s sample interval |
| CCR-75 rendex | 6 | **2** | Hosted SaaS with an API key, and `RM-DataRefresh` is already installed and Ready |
| CCR-76 temporal | 6 | **2** | Both premise clauses fail, and one cites an RM rule that does not exist |
| CCR-129 CLAUDE.md trimming | 6 | **2** | **CLAUDE.md is 9,466 bytes against a 60,000 budget - 84 percent headroom** |
| CCR-144 critical feedback | 6 | **3** | Corroborates a discipline RM already runs, aimed at credulity RM does not exhibit |
| CCR-135 Codeman | 7 | **5** | NOT unreachable and never a Reddit post. Weak as cycle 4 UX under ADR-008; real as an ops-layer reference. **Refuter overturned the dive's 4 and won** |

**101 to 51. Fifteen dived, thirteen demoted, one held, zero adopted.** Both
refuter overturns went UPWARD, and both for the same reason: the dive scored one
axis and left a second unscored.

#### The result that matters: the top band is empty

Stage 3's survivors held one 9, three 8s and nine 7s. After all 21 dives the
highest surviving score in the entire 146-entry corpus is **6** - `CCR-121`, a
design input for a loop that does not exist yet.

**146 extracted, 146 scored, 21 dived, 0 at 7 or above, 0 adopted.** No entry in
this corpus acts on a named Red Moon cycle. Gap 7 is untouched: nothing here
supplies a ground-truth anchor for combat math, which stage 2 said in prose and
stage 4 has now MEASURED on every entry that claimed otherwise.

#### The pattern held six for six, fifteen for fifteen

Thirteen demotions, thirteen unchecked RM-side premises. **Not one entry was
demoted because the tool was bad** - CCR-143, CCR-121, CCR-81, CCR-110 and
CCR-135 all read better at source than their corpus lines. Stage 2 scored good
tools against beliefs about Red Moon, and the beliefs were the defect.

Only ONE premise survived measurement: CCR-121's, that RM has no orchestration
loop and the shared governor supplies no retry concept. Verified independently -
`ops/loop/__init__.py` states "NOTHING IN RED MOON CALLS THIS YET", and a grep of
`slots.py` for retry, cache, depend, graph, node or failure returns exactly one
line, a comment about retrying a lock acquisition.

**A new sub-shape, and it is worth naming.** CCR-81, CCR-127, CCR-143 and CCR-144
were each scored by reading a rule in `CLAUDE.md` and treating the WRITTEN
DISCIPLINE as an UNMET NEED. A rule written down is evidence the project already
solved something. "RM's most-repeated discipline is X" is not the statement "RM
suffers X".

**And the shape bit the fan-out itself.** The CCR-135 dive asserted "RM has no
many-session problem" without probing `ops/loop/`, which exists for exactly that
problem - the bug the fan-out was built to catch, committed by the fan-out, and
caught by its refuter. Recorded as method: an adjudicator must check the dive's
own unstated premises, not only stage 2's.

#### Corrections to Red Moon's own recorded facts

Every one re-verified by the orchestrator, not taken from an agent.

- **`CCR-135` was never a Reddit post and was never unreachable.** It is
  `github.com/Ark0N/Codeman`, HTTP 200, **MIT, 508 stars**, "Self-hosted mission
  control for AI coding agents". The stage 4 GAP recorded for it was a false
  absence. **That is the second false absence in this document from trying one
  access route and stopping** - the first was WebFetch returning HTTP 402 on
  Fandom while `api.php` on the same host returned 200. **New method rule: a
  source is unreachable only after two different routes fail.**
- **`tests/test_drift_anchors.py:6` carries an unreproducible count.** It says
  the build pin lives in "~97 tracked sites". Recounted by three parties
  independently: **120**. Sixth instance of the count-the-rows shape, after
  ability_stats 1474/1818, the corpus 119/146, `vblood_damage_modifier`, the
  sample rate, and gap 8 - and the first one inside a test's own docstring.
- **The drift anchor is a CLOSED LOOP.** It compares `CLAUDE.md` only against
  tracked files, with no tie to the install's `VERSION` or to
  `data/rmdata/current.txt`. It stays green while every authored file cites a
  build that is no longer on disk. `tools/rm_facts.py` prints the game build and
  the extracted-data build on adjacent lines and never compares them.
- **Do NOT retire the "no commit while an agent is live" rule.** The CCR-55 dive
  recommended retiring it once `git worktree add` runs. The spec line it rests on
  says something else:
  `docs/superpowers/specs/2026-07-26-bloodforge-input-spike-design.md:312-314`
  records that a worktree-isolated agent **twice wrote into the MAIN tree while
  `git worktree list` showed no second tree.** That is declared isolation that
  was fictitious, not absent isolation. Running `git worktree add` does not
  address it.

Two evidentiary overstatements from inside the dives, recorded so stage 6 does
not inherit them: `precommit_gate.py`'s deny JSON is **not** test-pinned
(`tests/test_hooks.py:32-33` pins `text_first_guard`'s, not the commit gate's);
and "the drift cluster collapses on a format" is weaker than presented, because
`abilities` and `ability_stats` are flat scalar rows - 1,872 of 3,038 rows,
including the 1,818-row combat table.

#### Candidates for stage 6, none adopted here

Named because each is traceable to a measurement, and most are not a tool.

1. **Pin the collected test count.** `pytest --collect-only` reports 544 and a
   grep of `tests/` for that number returns nothing. A shrinking suite is
   invisible today. Same drift-anchor idiom RM already uses.
2. **Assert `git log` carries no banned co-author trailer.** `hooks/commit-msg`
   strips and warns rather than blocking, `--no-verify` bypasses it, and nothing
   scans afterward. Currently 0 of 127, so it lands green and stays green.
3. **A dump-to-dump VALUE diff keyed on `prefab_guid`.** The highest-value item.
   RM's five gates catch a wrong count, type, shape and duplicate key; nothing
   catches a value that changed in place between two dumps of the same build,
   and git cannot see it either - `data/rmdata/` is gitignored and
   `git ls-files data/rmdata/` returns 0. The seam already exists in the
   promote-from-quarantine step.
4. **Promote the census min/max from print to pin.** `rmdata_ingest` already
   computes per-key min and max and only prints them.
5. **Close the build-pin blind spot.** Assert `current.txt` equals CLAUDE.md's
   canonical pin, and make `rm_facts.py` COMPARE its two build lines.
6. **Consider a `Stop` hook once**, gated on the source's own caution that one
   which always blocks loops forever.
7. **Run the headless loop's slices in real worktrees**, as a DAG of scoped nodes
   with per-node result caching and retry INSIDE the slot. CCR-121's pattern and
   Kagan's branch namespace, taken as ideas rather than dependencies.
8. **Name the ability-attribution hole on ROADMAP.** The health series records a
   delta; nothing attributes it to an ability. RUN 1 dodges this by constraining
   the operator to one ability. RUN 2, a real V Blood fight, has no mechanism.

**Do not:** install `red-handed` - never `install-hook`, which rewrites the
`settings.json` that `tests/test_hooks.py` pins, and never `stats`, which caches
excerpts from all 644 machine-wide sessions including Riot Commander's into one
shared `~/.red-handed/cache.json`, a second standing exception to CLAUDE.md's
standalone rule. Do not npm-install `graph-skill`. Do not install OpenCode.

## Stage 6 - the plan. DONE 2026-08-01.

Stage 6's only job is the rule this track has repeated since it opened: **nothing
is adopted until it is named here with an acceptance criterion.** Eight
candidates came out of stage 4. **Four are adopted, one is DROPPED, one is
deferred, one is blocked on another owner, and one is already discharged.**

**None of them is a tool.** That is the honest summary of a 146-entry tool
corpus: after 21 dives it contributed no dependency and eight measurements, and
the work below is what the measurements imply.

### The plan was put through the same adversarial pass the tools were, and it failed the same way

A first draft of this section was challenged by three independent lenses -
falsifiability of every acceptance criterion, re-measurement of every premise,
and redundancy against gates that already exist - then adjudicated. **Three items
changed and one died.** The orchestrator independently re-ran every load-bearing
claim below; all reproduced.

This is worth recording rather than quietly fixing, because the draft committed
**the exact failure this track spent 21 dives diagnosing**, inside the document
diagnosing it:

- **The draft's S7.4 named a subject its mechanism cannot reach.** It proposed
  promoting the ingest census's per-key min/max "for the six promoted tables".
  MEASURED by importing `shape_census` and running it over the real tree: it
  returns entries for **four** - `blood_types`, `items`, `recipes`, `vbloods`.
  `abilities` and `ability_stats` produce nothing, because `_observe` only fires
  on a `dict` or `list` value and a table with no nested container is dropped.
  **The 1,818-row combat table Bloodforge consumes is structurally invisible to
  it**, and its `cast_time`, `cooldown` and `post_cast_time` are top-level
  scalars the census cannot see. Nine numeric slots exist in total, two of them
  guid identity fields and three degenerate. A test iterating the census and
  pinning what it finds would have covered nine numbers, been labelled "the six
  promoted tables", and read exactly like a passing gate. A real measurement
  answering the right question about the wrong subject - the cycle 2 lesson,
  committed afresh.
- **Four criteria were written as descriptions of the FEATURE rather than of a
  FAILURE THE TEST MUST PRODUCE.** "Stands down on a build change", "silent on
  identical dumps", "sources from the right file". Every clause phrased as an
  absence of output is satisfied by a no-op: `def diff(old, new): return []`
  passed two of S7.3's three clauses.
- **One premise was simply wrong.** The draft called
  `tests/test_bridge_probe.py:31` "structurally incapable of failing". It is not:
  `bridge_probe.py:107-108` reads `current.txt` itself, so the test sources the
  SUT's real input, and `test_health_fails_on_a_build_mismatch` at `:183` is a
  working negative control. That bullet is deleted rather than repaired.
- **A frozen-file block did not survive contact with the frozen file's public
  API.** `tools/rm_facts.py:40` and `:50` expose `game_build()` and
  `data_build()` as importable functions, so a test can assert they AGREE without
  editing the frozen file. Only making `rm_facts` PRINT the comparison needs
  operator approval. The draft applied "assert the outcome, not the mechanism" to
  S7.2 and then failed to apply it here.
- **And the draft applied its own standard inconsistently.** It refused S7.6
  because the failure has never occurred, then adopted S7.1 against a failure
  that has also never occurred: across 16 recorded suite counts in
  `docs/LEDGER.md` the collected total is monotonically non-decreasing - 241,
  284, 324, 327, 334, 335, 348, 382, 382, 382, 405, 526, 544, 544, 544, 544. S7.1
  survives, but it owed an argument it had not made. See its entry.

### ADOPTED - four items, in build order

There is **no dependency between any two of them** once S7.4 is dropped, so the
order is convenience: smallest diff first, the only production-code change last.

**S7.2 - assert `git log` carries no banned co-author trailer. BUILD FIRST.**
`hooks/commitmsg_hook.py` STRIPS AND WARNS rather than blocking, `--no-verify`
bypasses git hooks entirely, and nothing scans afterward. Asserting the OUTCOME
rather than the mechanism is what makes it survive `--no-verify`.
*Acceptance:* the test imports `CLAUDE_TRAILER` from `hooks/commitmsg_hook` and
uses it as the single predicate, so the friendly path and the backstop cannot
diverge - the draft named a case-sensitive literal `Co-Authored-By: Claude`,
narrower than the hook's own
`^[ \t]*co-authored-by[ \t]*:.*(?:claude|anthropic)` with `IGNORECASE`, and a
commit reading `Co-authored-by: Fable <noreply@anthropic.com>` would have
violated policy, matched the hook and missed the plan. It scans full message
BODIES (`git log --all --format=%B`) and asserts the number of commits walked
equals `git rev-list --all --count`, so a format that silently drops merge or
empty-body commits fails rather than reporting a clean zero over a partial
history.
*Negative control:* a table of real trailer forms each asserted DETECTED,
including the lowercase and leading-tab variants and the `Fable`/`anthropic`
form - plus `Co-Authored-By: Moonbeam <close.benham@gmail.com>` asserted NOT
detected, which is the clause that stops an over-broad predicate. A string built
to match predicate P and checked by predicate P is a tautology and is not the
control.
*Measured:* **0 trailers over the full history at 129 commits.** Never let a
commit COUNT into an assertion; it moves every session.

**S7.5 - close the build-pin cross-file blind spot. BUILD SECOND.**
Two tests, no production code.
- Nothing asserts `data/rmdata/current.txt` agrees with `CLAUDE.md`'s canonical
  pin, and the existing drift anchor **structurally cannot** cover it:
  `tests/test_drift_anchors.py:56` iterates `git ls-files` and `data/rmdata/` is
  gitignored. The new test must reuse that file's `CANONICAL_PIN` / `_canonical_pin()`
  rather than re-parsing the prose, so a reword of `CLAUDE.md:45` surfaces as one
  distinct failure instead of a phantom build mismatch.
- `tools/rm_facts.py` never compares its two build lines. **The ASSERTION is
  unblocked** - import `game_build` and `data_build` and assert they agree.
  *The criterion must close its own hole:* those functions return the sentinels
  `"not installed"`, `"unparseable"` and `"none extracted"` on failure, so the
  test asserts neither value is any of the three BEFORE comparing. Otherwise it
  is a gate with nothing to catch on any machine but Legion.
- **Still blocked, operator approval required:** making `rm_facts` PRINT the
  comparison. That is operator UX, not the gate. Raise it in the same session so
  it is not forgotten.

**S7.1 - pin the collected test count. BUILD THIRD.**
*The argument the draft owed:* a shrinking suite has never happened here, and
that alone would make this the S7.6 mistake. What distinguishes it: the ledger
count is transcribed by hand at session end **by the same agent that would be
hiding the shrink**, and it is prose that nothing reads back. S7.6's cost is a
live regression risk (a Stop hook that always blocks loops forever); S7.1's cost
is only maintenance churn. That asymmetry is the reason, and it is now stated.
*Acceptance, criterion replaced:* pin a per-module map of `{module path ->
collected count}` and assert BOTH the key set and the total. A single total pin
does not satisfy this - delete a 5-test module in the same commit that adds five
tests elsewhere and a total of 544 still reads 544, while a missing KEY cannot be
masked and names the file. Collection runs in a subprocess; the test asserts its
exit code is 0 and that the count was actually PARSED rather than defaulted,
because a regex over stdout finds no match on a collection error and
`if observed and observed != PIN` passes silently over a suite that cannot
import.
*Negative control:* copy `tests/` to a temp directory, delete one module,
re-collect THERE, and assert the comparison fails naming that module. A unit test
of the comparator with `(543, 544)` is not the control.

**S7.3 - a dump-to-dump VALUE diff keyed on `prefab_guid`. BUILD LAST. The
highest-value item in the batch.**
RM's five gates - shallow schema, deep nested, duplicate key, count pin, build
cross-check - each catch a wrong COUNT, TYPE, SHAPE or KEY. **None catches a
value that changed in place** under a fixed build, and git cannot see it either
(`data/rmdata/` is gitignored, `git ls-files data/rmdata/` returns 0).
*And it has happened.* `docs/LEDGER.md:740-745`: a cycle 2 dedupe fix "silently
made the row whichever of two DISAGREEING entities the world walk reached first.
The count looked right afterwards, which is why it survived a cycle." That is
this item's entire justification, and it is the only class of evidence this track
accepts - a failure that occurred, not one that could.
*Placement, corrected:* insert the diff immediately before `if problems:` in
`tools/rmdata_ingest.py`, extending `problems`, so a validate-only run surfaces
drift before anyone types `--accept` and refusal reuses the existing
`EXIT_INVALID` path. The draft's rationale was wrong in its cause though right in
its conclusion: a post-promotion diff fails because **the promotion loop
overwrites `tables_dir/<name>.json` in place**, destroying the baseline eleven
lines before `_clear_incoming` runs.
*The escape hatch, and it is not optional.* Cycle 3 is where the dumper is under
active development, so a same-build value change is a normal event there, not an
anomaly. A hard refusal with no path through would gate cycle 3 from a
non-roadmap batch, contradicting this track's own founding rule. So: `--accept`
promotes as today, and a second explicit `--accept-value-changes` is required
when the diff is non-empty, printing the full old/new list first. Loud and
default-on, with one documented line through it. Document the flag in
`docs/OPERATIONS.md` in the same commit.
*Acceptance, six cases each asserted by name:* (1) a mutated NESTED scalar,
reported with table, `prefab_guid`, field path, old and new value; (2) a mutated
TOP-LEVEL scalar, same reporting; (3) a row ADDED; (4) a row REMOVED; (5) the
diff reports the COUNT of differing rows, so an implementation that stops at the
first difference is distinguishable from one that does not; (6) **no baseline on
disk** - the diff stands down and SAYS SO in the census output, in the same voice
as the count gate's stand-down, so an absent baseline is never mistaken for a
clean diff. That case is the DEFAULT state of any fresh clone and the draft
omitted it.
*How it is exercised:* the OLD side is the real promoted table read from disk at
module scope, the idiom `tests/test_damage.py:52-57` and `tests/test_dps.py:43-49`
already use - a missing tree is a collection error and **no `pytest.skip` guard**,
because a skip is how this gate would quietly stop running. The NEW side is that
same file with exactly one nested field mutated. Assert the diff names that guid
and field **AND NO OTHER** - that clause is the one with teeth, because it fails a
diff reporting spurious differences from key ordering, float repr or dict
iteration order. Assert the specific exit constant, not merely nonzero.
*Deleted from the draft:* "given a build CHANGE it stands down entirely" cannot
fail. `tables_dir` is build-scoped off `read_expected_build`, so a build change
means a directory with no baseline by construction - the clause tests the
directory layout, not the feature.

### DROPPED - one item

**S7.4 - promote the census min/max from print to pin. DROPPED, not deferred.**
Its mechanism cannot reach the subject its criterion named (above), and the four
informative pins it could have produced **would not have caught the one value
drift this project actually suffered**: the `vbloods` row swap at
`docs/LEDGER.md:740` moves `level`, `physical_power` and `spell_power`, all
top-level scalars with zero census coverage. Rebuilding it honestly means
building top-level range coverage that does not exist - new code, not a promotion
from print to pin - and it would have to be re-costed and re-argued from scratch.
The residual gap it gestured at, a fresh machine with no baseline, is closed by
S7.3's case (6) stand-down.

A replacement was proposed during the challenge - a committed per-table row-digest
fingerprint - and is REFUSED on stage 6's own standard: no fresh-machine ingest
has ever gone wrong, so it guards an unmeasured need. Recorded as a candidate,
not adopted.

### DEFERRED, BLOCKED, DISCHARGED - three items

**S7.6 - a `Stop` hook. NOT ADOPTED.** MEASURED and true: `.claude/settings.json`
wires exactly `PreToolUse`, `PostToolUse` and `SessionStart`, and
`tools/pytest_guard.py` "never raises and never blocks", so nothing stops an
agent declaring done over a red suite. **But the need is unmeasured** and
adopting against a failure that has never occurred is the bug this track spent 21
dives naming. *Revisit when* an actual instance is recorded, or S7.1 or S7.2 fires
once. *Cost to carry into that decision:* `tests/test_hooks.py:142` pins the
settings wiring and `:156` constrains matcher shape, and a Stop hook that always
blocks loops forever.

**S7.7 - worktree-isolated slices and a cached node DAG.** CCR-121's pattern (the
one premise in the whole fan-out that survived measurement) plus Kagan's branch
namespace, as IDEAS - do not npm-install `graph-skill`, do not install OpenCode.
Blocked: RM's headless command structure is being drafted by another party for
RM-side review, and RM does not scaffold one speculatively. Two constraints to
hand that plan: retry belongs INSIDE the slot, because `ops/loop/slots.py` holds
the slot only around the executor call; and **declared worktree isolation has
failed here twice** - an agent wrote into the MAIN tree while `git worktree list`
showed no second tree. Checking that `git worktree add` returned 0 is exactly the
check that failed both times, so the assertion must instead be that
`git -C <slice> rev-parse --show-toplevel` resolves to the slice and NOT the main
tree, and that the slice appears in `git worktree list`.

**S7.8 - the ability-attribution hole.** Discharged as `ROADMAP.md` gap 8b in the
session it was found. Cycle 3 concern; this track must not fold into cycle 3.

### What stage 6 refuses to adopt

Every tool in the corpus. **146 extracted, 146 scored, 21 dived, 0 at 7 or above,
0 adopted.** No `red-handed` install - specifically never `install-hook`, which
rewrites the `settings.json` that `tests/test_hooks.py` pins, and never `stats`,
which caches excerpts from all 644 machine-wide sessions including a sibling
project's into one shared `~/.red-handed/cache.json`, a second standing exception
to `CLAUDE.md`'s standalone rule. No `graph-skill`. No OpenCode. No prompt
library. No "argue against me" added to `CLAUDE.md`.

**The corpus's contribution to Red Moon is a list of measured facts about Red
Moon** - four corrections to recorded facts, one new ROADMAP gap, and four work
items. One of those measured facts has now retired one of the five items the
corpus produced, which is the process working rather than failing.

## What stage 7 owed - DISCHARGED 2026-08-01, commit `8684aa0`

Kept below as written, because the point of an acceptance criterion is that it
was set before the work. Every clause was met, with two deviations recorded in
Status above: the S7.2 self-check moved from a text scan to an AST walk, and
S7.3 gained an explicit empty-baseline-is-no-baseline rule the criterion had not
anticipated. **Build order was S7.2, S7.5, S7.3, S7.1** rather than the stated
S7.2, S7.5, S7.1, S7.3 - S7.1 pins a per-module count map and S7.3 adds a test
module, so building the pin first would only have meant writing it twice. The
plan itself says the order is convenience and there is no dependency between
them.

Implement S7.2, S7.5, S7.1 and S7.3 in that order, TDD per `CLAUDE.md`: the
failing test first, then the implementation, then verification at the tier the
change earns. S7.2, S7.5 and S7.1 are test-only and Tier 1. S7.3 changes
`tools/rmdata_ingest.py` and adds an operator flag, so it is Tier 2 - full suite,
and `docs/OPERATIONS.md` updated in the same commit.

`ENGINE_VERSION` does not move for any of them: none touches section 2, 3 or 4
math. None is cycle 3 work and none may gate the power-stat experiment.

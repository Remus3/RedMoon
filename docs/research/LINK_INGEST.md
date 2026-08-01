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
2. **Score** - all 146 against the rubric above. IN PROGRESS.
3. **Cull** - threshold chosen AFTER scoring, from the observed distribution,
   never before.
4. **Deep-dive** - survivors only, and every claim about a survivor verified
   against its actual source rather than against the one-line summary.
5. **Adversarial pass** - challenge every survivor. CHECK THE CHALLENGE'S OWN
   COVERAGE FIRST: a previous fan-out silently truncated its input at 12,000
   chars and left 33 entries unchallenged, and every apparent survivor was an
   artifact of that gap.
6. **Plan** - what RM actually builds, in what cycle, with what acceptance.
7. **Implement** - against the plan, TDD per CLAUDE.md.

## Status

- Stage 1 COMPLETE, 146 of 146 extracted.
- Stage 2 COMPLETE, 146 of 146 scored.
- Stage 3 COMPLETE: threshold 6+, 21 survivors, 125 culled.
- Stage 4 deep-dive OPENED 2026-08-01. **3 of 21 survivors dived**, 1 attempted
  and unreachable (`CCR-135`, a Reddit post), 1 read at source during the cycle 4
  concept work and corrected in three places (`CCR-120`). **16 still owed.** No
  survivor may be adopted until its actual source has been read - every score is
  otherwise against a one-line summary written by someone else for someone else.

  **Three dived, three verdicts, zero adoptions.** `CCR-146` REFUTED for RM's
  setup. `CCR-35` DEMOTED 8 to 4 and `CCR-89` DEMOTED 7 to 5, both on checks
  stage 4 had named in advance. That is the dive working as designed: the scores
  it was testing were the ones it moved.

Nothing is adopted until stage 6 names it with an acceptance criterion.

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
| CCR-127 | **PreToolUse deny + feed the reason back into context** so the model self-corrects. RM already runs `precommit_gate.py` as PreToolUse; it blocks but does not teach. Also directly relevant to the headless track. | 7 |

### Cycle 4 dashboard references

| id | note | score |
|---|---|---|
| CCR-135 | **Codeman** - self-hosted mission control over parallel agent sessions, streamed to any browser. The operator's own note on CCR-120 names this as the stronger UX reference. | 7 |
| CCR-110 | **mockd** - single Go binary mocking HTTP/gRPC, stateful CRUD, OpenAPI digital twins. A mock bridge would let Bloodforge and the dashboard be tested WITHOUT launching V Rising, which today is required for any integration check. | 7 |
| CCR-115 | memi - read-only design audit flagging a11y and hierarchy risks. Useful once 8778 exists, useless before. | 5 |

### Headless track

| id | note | score |
|---|---|---|
| CCR-55 | Kagan - agent kanban with MANDATORY human gates and isolated worktrees. Maps onto RM's worktree concern and its "no commit while an agent is live" rule. | 6 |
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
| CCR-75 | MIT | **rendex-mcp** - scheduled URL change-watch with visual and text diff. RM pins the game build in about 97 tracked sites behind a drift-anchor test, and finds out a patch landed by noticing. Watching the patch notes and the wiki is the missing trigger. | 6 |
| CCR-76 | MIT | **temporal-mcp** - elapsed time between turns, day rollover, resumed-session detection. RM lost a run today to a control taken at 5 s of server uptime when the subject appears at 20 s, and its session notes rule requires converting relative dates to absolute. | 6 |
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

### Still owed at stage 4

The binary-RE pair is DONE, above, and both were demoted. Still owed, 16 of 21:

The gap 7 plumbing entries `CCR-39`/`CCR-84` (MediaWiki, an independent second
source for boss numbers) and `CCR-123` (talkthrough) - the latter partly
overtaken, since the operator has ruled the anchor is a bridge-side health series
rather than a narrated recording, which demotes it from plumbing-for-the-anchor
to a cross-check route at most. `CCR-39`/`CCR-84` are now the strongest remaining
undived entries: RM has exactly one source for every number it publishes, its own
dumper, and the run that would falsify a computed figure has still not been
taken.

Then `CCR-143` (red-handed, 9, the highest-scored entry in the corpus and still
undived), `CCR-74`/`CCR-50`/`CCR-80` (the drift-validation family), `CCR-81`,
`CCR-110`, `CCR-127`, `CCR-55`, `CCR-121`, `CCR-129`, `CCR-120`, `CCR-75`,
`CCR-76` and `CCR-144`.

`CCR-135` (Codeman) could NOT be read at source - it is a Reddit post. Its
information design fed the cycle 4 concepts through its one-line summary only,
and that is recorded as a stage 4 GAP rather than a completed dive.

## What stages 5 to 7 still owe

Stage 4 deep-dive has NOT run. Every score above is against a one-line summary
written by someone else for someone else, which is exactly the kind of secondhand
claim this project refuses elsewhere. **No survivor may be adopted until its
actual source has been read.** Stage 5's adversarial pass must check its own
input coverage before reporting, and stage 6 names an acceptance criterion per
adopted item or nothing is adopted.

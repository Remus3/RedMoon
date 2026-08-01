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
- Stage 2 in progress: 60 of 146 scored (the operator deep-review set).
- Stage 2 REMAINING: the 82 entries the operator marked "not needed", swept
  against RM's rubric rather than accepted, because those notes were the
  operator reviewing RC's triage in RC's frame.

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

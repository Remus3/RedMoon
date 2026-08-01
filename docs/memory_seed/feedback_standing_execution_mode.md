---
name: feedback-standing-execution-mode
description: "Standing operator rules - keep the inline session free, orchestrate work headlessly with adversarial multi-agent loops, and emit a paste-ready block at /done"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 63979038-027d-45ec-9321-db0b505baf7a
  modified: 2026-08-01T12:47:12.953Z
---

Three standing rules given 2026-08-01, applying to every Red Moon session until
countermanded:

1. **Keep this Claude app session inline and open for operator use.** Do not
   occupy the inline session with long blocking work.
2. **Perform actions with headlessly-orchestrated, multi-agent, parallel,
   self-adjudicated, adversarial looping.** Fan work out; have agents check each
   other rather than trusting a single pass.
3. **Whenever `/done` runs, print an inline copy block** the operator can paste
   into the next new session after `/clear`.

**Why:** the operator drives three projects on one box (Red Moon, Riot Commander,
LegionWallpaper) and uses the inline session as a control channel, not a worker.
Blocking it stalls the operator, not just the task. Rule 3 exists because
`/clear` destroys context by design and the paste block is the only carrier
across that boundary.

**How to apply:** this is a STANDING opt-in to multi-agent orchestration - it
does not need to be re-requested per task. It coexists with, and does not
override, `CLAUDE.md` R9 (no subagents under about three files) and the
Subagent-First Protocol's read-only `verifier` gate before any merge or "done"
claim. Rule 3 is a superset of what `NEXT_SESSION_PROMPT.md` already does: keep
writing that file, and ALSO print its contents inline at `/done`.

Related: [[project-redmoon-headless-gap]], [[user-operator-profile]].

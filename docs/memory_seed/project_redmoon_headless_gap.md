---
name: project-redmoon-headless-gap
description: "Red Moon has NO headless Claude orchestration and no agent dashboard - measured 2026-08-01, RC is to draft the plan"
metadata: 
  node_type: memory
  type: project
  originSessionId: 63979038-027d-45ec-9321-db0b505baf7a
  modified: 2026-08-01T12:47:25.310Z
---

Measured 2026-08-01 by direct probe, not inference: **Red Moon has no headless
Claude orchestration of any kind.**

`.claude/` contains exactly five files - `agents/verifier.md`,
`commands/{done,root-cause-fix,sync-docs}.md`, and `settings.json`. There is no
runner script, no orchestrator, no worktree fan-out harness, no cost watchdog and
no agent dashboard.

**Beware a false positive:** grepping the repo for `headless` returns hits in
`docs/BRIDGE_SPIKES.md`, `ROADMAP.md` and `docs/LEDGER.md`. **Every one refers to
the V Rising DEDICATED SERVER host** (`-batchMode -nographics`), not to Claude.
Do not read those as evidence that orchestration exists.

What DOES exist and is worth keeping in any design: four `settings.json` hooks -
`PreToolUse` on Bash/PowerShell running `precommit_gate.py`, `PreToolUse` on
scrape/clipboard running `text_first_guard.py`, `PostToolUse` on Edit/Write
running `pytest_guard.py` with a 900s timeout, and `SessionStart` running
`rm_facts.py`. A headless runner must not bypass these.

**Status:** the operator is having Riot Commander draft the exacting plan for RM's
headless command structure and its dedicated dashboard, for RM-side review and
implementation. Do not scaffold one speculatively before that plan arrives.

Constraint any plan must respect: Red Moon's port block is 8770-8789
(see [[project-redmoon-ports]]), so an orchestrator dashboard takes a port from
inside that block - 8781 and 8782 are the free ones - and the number goes in
`core/ports.py`, never a literal.

Related: [[feedback-standing-execution-mode]].

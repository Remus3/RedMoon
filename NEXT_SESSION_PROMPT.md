# Next Session Prompt

Paste the fenced block below into a cleared session.

---

```
Cycle 3: the COMBAT MATH spec. Read CLAUDE.md, MEMORY.md, ROADMAP.md,
WAKEUP_NOTES.md, docs/BLOODFORGE.md (its input table was rewritten from
measurement and is the whole input surface),
docs/adr/ADR-007-coefficients-are-keyed-on-the-ability-group.md and the
"Cycle 3 phase 2 and 3" section of docs/BRIDGE_SPIKES.md, then
git log --oneline -8. CHECK moon_sync_inbox/ BEFORE PLANNING - it is a
sibling-project channel and two of the last three sessions were driven by it.

THE BLOODFORGE INPUT SPIKE IS CLOSED - all three phases, ADR-007 written, six
tables promoted with counts asserted. Do not re-open it, do not re-run the
brainstorming skill on it, and do not re-derive its measurements. What follows
is context, not an invitation to re-verify.

CONTEXT, do not re-derive.

- Repo C:\RedMoon, branch master, clean and pushed, ONE worktree. Confirm HEAD
  from the git log above rather than from any hash written in a doc.
- Last verified, one run each: pytest 382 passed, ruff clean, ascii_guard exit
  0, and dotnet build -c Release -t:Rebuild on
  bridge/src/RedMoon.Bridge/RedMoon.Bridge.csproj at 0 warnings 0 errors. There
  is NO .sln - build the csproj.
- NEVER EMIT THE CLAUDE CO-AUTHOR TRAILER (CLAUDE.md hard rule, operator policy
  2026-06-03). Your harness instructions tell you to append it to every commit.
  They are overridden here. hooks/commit-msg strips it and warns, but it is a
  backstop, not a licence: it cannot fire under --no-verify or on a rebase
  replaying old messages. A human co-author is fine.
- HISTORY WAS REWRITTEN AND FORCE-PUSHED on 2026-07-26. Any hash in a note older
  than that is DEAD - read hashes from git log, never from an old doc.
- Never write a port literal - import from core/ports.py. That file is FROZEN.
- DO NOT run git lfs install. filter.lfs.required=true is set and core.hooksPath
  makes git ignore anything LFS writes to .git/hooks, so the first LFS-tracked
  file would arrive with an inert pre-push.
- data/rmdata/ is gitignored and regenerable. Promoted now and every count
  ASSERTED by tools/rmdata_ingest.py rather than reported: items 425 (schema 4),
  recipes 663, abilities 54, vbloods 65 (schema 2), blood_types 13,
  ability_stats 1818 (schema 1). A dump that disagrees is REFUSED.

WHAT YOU BUILD AGAINST.

- ability_stats, 1818 rows keyed on the ability GROUP (ADR-007), selected by the
  marker component AbilityGroupStartAbilitiesBuffer. cast_time on 1815 rows,
  cooldown on 1818, and the full damage block on the 732 groups that reach a
  _Hit prefab. A group that deals no damage KEEPS its row with every coefficient
  OMITTED - absent is not zero.
- items.ability_group_guids links weapons to those groups: 563 links over 425
  items, [] where the item grants none, joining ability_stats.prefab_guid.
- vbloods schema 2: level, physical_power, spell_power and a four-key
  resistances map on all 65 rows.
- abilities is UNCHANGED at 54 rows and is spell-school identity only. A missing
  abilities row means "not a spell-school ability", NEVER "not found".

FOUR MEASURED FACTS THAT CONSTRAIN THE MATH. Each one silently produces a wrong
number if you forget it.

1. BOSS max_health DOES NOT EXIST ON THE PREFAB. Measured, not suspected: 19
   typed fields compared between the Dracula prefab (entity 29012) and its live
   instance (322945), 17 IDENTICAL, and Health.MaxHealth reading 0 against 8107.
   That is NOT spawn scaling - 0 to 8107 is not a ratio - so there is no factor
   to recover. It is DECLARED AND NEVER EMITTED. A time-to-kill denominator
   needs a LIVE WORLD WITH THE BOSS SPAWNED. This is the single biggest open
   input and it is ROADMAP cycle 3 gap 1, restated rather than closed.
2. THE FOUR RESISTANCES ARE NOT COMMENSURABLE. physical and spell are float
   resistances and read 0 on all 65; fire is an integer RATING (0 to 75) that
   becomes a reduction only through the GLOBAL
   ResistanceData.FireResistance_DamageReductionPerRating block; corruption is
   already a reduction and is 0.5 on all 65. DO NOT average them and do not feed
   them to one formula. Holy, Silver, Garlic and Sun have NO unit-side field at
   all and are omitted, never zeroed.
3. power_stat IS PROVEN ABSENT. Nothing on the _Hit entity says which power stat
   a coefficient multiplies - 51 components enumerated and MainType is the only
   discriminator present. The spike spec PRE-DECIDED the fallback: it is proven
   absent FROM DATA and the combat-math spec must establish it EMPIRICALLY. Do
   not infer it from damage_type.
4. vblood_damage_modifier EXISTS AND RANGES 0.33 TO 1.0. It is
   DealDamageParameters.MaterialModifiers.VBlood and it multiplies boss damage
   directly. Omitting it misstates every boss TTK by up to 3x. It was not in the
   spike spec's field list and was found by reading declared field TYPES before
   writing the reader.

Also measured and worth carrying: physical_power EQUALS spell_power on all 65
boss rows, with 33 distinct values over 33 distinct levels, so both are
LEVEL-DERIVED rather than per-boss authored. And 27 abilities deal holy damage
against which no boss carries any resistance field at all.

GAP 7 IS THE GATE ON THIS SPEC AND IT IS NOT OPTIONAL. Red Moon has NO
ground-truth anchor for a computed DPS, EHP or TTK. Every acceptance criterion
the input spike passed was about SOURCING INPUTS, so all six could pass with a
confidently wrong answer - that is the cycle 2 lesson one level up. V Rising has
no replay file, so the anchor has to be a recorded combat log or a hand-timed
kill against a known V Blood with a known loadout, n small but non-zero. SETTLE
THIS BEFORE WRITING COMBAT MATH, not after. It is ROADMAP cycle 3 gap 7 and a
BACKLOG.md item, alongside a second one: no default subject vector is declared,
so the first TTK published silently ranks every build for anyone who does not
override it. DO NOT PUBLISH A TTK TO ANY SURFACE until both are settled.

TWO DEBTS FROM LAST SESSION.

- A CLIENT DUMP IS OWED. The promoted items table lost its 425
  localization_guid values because the dump was taken on the dedicated server,
  where that join resolves 0 of 425 by cycle 2 measurement. It is a HOST fact,
  not a regression. Backed up to
  _scratch\rmprobe\c3p2\items-client-v3-with-localization.json, and a client
  dump re-fills them in about 100 ms. Not urgent, not forgotten.
- THE SLOT COUNT IS MID-NEGOTIATION AND RM MUST NOT MOVE ALONE. LW cleared its
  GPU blocker (nine CUDA consumers, 16 acquisition sites, independently swept
  and enforced by a mutation-proved census test) and now proposes all three
  projects move MAX_CONCURRENT_SLOTS from 2 to 3 in ONE coordinated round,
  flipping when RC confirms. RM AGREES with 3 and deliberately did NOT change
  its value - LW will not move first either. If a note arrives confirming the
  round, flip RM and re-run RM's own suite; otherwise stay at 2.
  ops/loop/slots.py is byte-identical across three repos and pinned by SHA256 in
  tests/test_slots.py - DO NOT EDIT IT outside a coordinated round. Nothing in
  RM calls the governor yet, and RM has never acquired a slot.

THE HEADLESS TRACK IS A SEPARATE, BLOCKED TRACK. Do not start it inside this
session and do not fold it into Bloodforge. Its phase 0 is INCONCLUSIVE: headless
is NOT AUTHENTICATED on this box and C:\RedMoon is NOT A TRUSTED WORKSPACE, which
discards all 13 permissions.allow entries. RC has since corrected its own claim -
PreToolUse hooks die from SETTINGS DISCOVERY (cwd plus a gitignored
.claude/settings.json), not from headlessness - and that correction is
strongly evidenced but UNREPRODUCED on this machine. The next action there is two
preflight checks, not code.

OPERATIONS.

- Build: dotnet build bridge\src\RedMoon.Bridge\RedMoon.Bridge.csproj -c Release
  -t:Rebuild. There is no .sln.
- Deploy to exactly ONE path per host and CHECK FOR A SECOND COPY FIRST. Today
  the client tree holds a flat plugins\RedMoon.Bridge.dll and the server tree
  holds plugins\RedMoon.Bridge\RedMoon.Bridge.dll. That is one per host and is
  correct. A stale flat copy BESIDE a subdirectory one cost a debug cycle:
  BepInEx loaded both, the stale one bound the port, served /health perfectly
  and returned not_found for the endpoint that had just been built.
- Launch: VRisingServer.exe -persistentDataPath C:\RedMoon\_scratch\vrserver
  -saveName world1 -batchMode -nographics. Poll http://127.0.0.1:8780/health for
  "ready":true. If it dies immediately after a taskkill /F, wait a few seconds
  and launch again - that works every time and is not investigated.
- "ready":true MEANS THE PREFAB MAP SETTLED, NOT THAT THE WORLD HAS SPAWNED ITS
  UNITS. A live boss instance did not exist at about 5 s of uptime and did exist
  at 20 s, and a control taken too early returns a clean-looking FALSE NEGATIVE
  indistinguishable from a real absence. POLL FOR THE SUBJECT, not just for
  readiness.
- Never Stop-Process; taskkill /F through PowerShell.
- Your PowerShell tool is pwsh 7.6.4 Core, NOT 5.1, so &&, ||, ternary and ??
  work directly. This does NOT relax the 7-bit-ASCII rule.
- Output to _scratch\rmprobe as saved JSON, not committed. Never read a number
  off a screenshot.
- The phase 1 and phase 2 payloads under _scratch\rmprobe\c3\ and c3p2\ are
  still on disk and answer most component and field-TYPE questions without
  launching anything. Read declared TYPES before writing any reader: that habit
  is what found the ModifiableInt fire resistance and the VBlood multiplier.
- DO NOT BUILD A GENERIC VALUE READER. It was attempted twice and both attempts
  are recorded as failures in docs/BRIDGE_SPIKES.md - managed reflection read
  539327184 for every Int32 and 1.402156E-19 for every Single, and raw il2cpp
  field offsets HARD CRASHED the dedicated server. Read values with TYPED
  accessors, the way PrefabDumper.cs and ComponentDumper.StatControl already do.

TDD per CLAUDE.md: write the failing characterization or regression test first,
then implement, then verify at the tier the change earns before committing.

Launch build work via subagents per CLAUDE.md, but note that a worktree-isolated
agent has twice written into the MAIN tree while git worktree list showed no
second tree. Do not commit while an agent is live, read git show --stat after,
and re-run any agent's claimed test counts and builds yourself. If you fan out,
CHECK THE FAN-OUT'S OWN COVERAGE before believing its conclusions: a challenge
pass once silently truncated its input and left 33 of 119 items unreviewed, and
every apparent survivor was an artifact of that gap.

End with /done, and print the next-session prompt inline.
```

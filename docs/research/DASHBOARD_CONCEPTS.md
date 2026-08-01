# Cycle 4 dashboard - ADJUDICATED

Produced 2026-08-01. Operator-directed: categorized, agent-adjudicated UI/UX
concepts for the project as a whole, explicitly NOT a rehash of a sibling
project's loop monitor.

Method: three concept agents over disjoint lenses - what the dashboard OBSERVES,
what it COACHES, and how it shows PROVENANCE - then a fourth agent to merge,
rank and rule. Each lens was told to read its own references at SOURCE rather
than from the one-line summaries in `docs/research/LINK_INGEST.md`, per that
document's stage 4 rule. The `CCR-120` reference was read at source and CORRECTED
in three places; `CCR-135` is a Reddit post and was not reachable.

**Arithmetic independently re-verified by the main session** before this landed:
3,038 corpus rows across the six tables, the 563 item-to-ability edges splitting
409 to damage-reaching groups and 154 to omitted, `coefficient` omitted on 1,086
of 1,818, and six files still sitting in `tables/_incoming/`. The observer lens's
"2,038 rows" was wrong and is corrected here to 3,038.

Nothing in this document is implemented. It governs what gets built, not what
has been.

Merge, rank and ruling over three disjoint concept lenses. No repo file was
edited. Two decisions arrived settled by the operator (stack, gap 7 anchor) and
are treated as closed. Six corrections from the main session override the lens
documents where they conflict.

One NEW measurement was taken during adjudication and it changes a concept - see
A0 immediately below.

---

## A0. NEW GROUND TRUTH TAKEN DURING ADJUDICATION

The coaching lens marked `data/rmdata/<build>/difficulty/` as UNVERIFIED. I
opened it. Three files, about 300 bytes each, read in full:

```
Difficulty_Brutal.json   UnitStatModifiers_VBlood: LevelIncrease 3,
                         MaxHealthModifier 1.25, PowerModifier 1.7
                         UnitStatModifiers_Global: PowerModifier 1.4
                         SunDamageModifier 1.0, BloodDrainModifier 1.0
Difficulty_Normal.json   all modifiers 1, LevelIncrease 0
Difficulty_Easy.json     VBlood PowerModifier 0.6, MaxHealthModifier 0.8,
                         SunDamageModifier 0.75, BloodDrainModifier 0.75
```

Two consequences, both binding.

1. **NEGATIVE, settling the coaching lens caveat.** There is NO per-rating
   resistance conversion constant anywhere in `difficulty/`. Zero occurrences of
   `resist`, `rating`, `conversion` across all three files. The hazard planner
   (C3) therefore may NOT render a percentage or a survival time, and that is now
   a MEASURED prohibition rather than a suspicion.
2. **POSITIVE, and nobody named it.** Boss level and boss power are
   DIFFICULTY-DEPENDENT. `vbloods.level` 27 for Bishop of Death is the Normal
   value; on Brutal that boss is level 30 with 1.7x power and 1.25x health. The
   boss ladder (C4) as all three lenses drew it is silently a Normal-difficulty
   ladder. **Difficulty is a third axis of the default subject vector**, alongside
   the boss and the loadout, and it was missing from every lens. It is also the
   only subject axis whose values are fully sourced on disk today.

Also re-confirmed at the row level for the ruling in section 5:
`items.stats` entries are exactly `{modification, stat, value}` (key is `stat`);
`vbloods.resistances` is `{corruption, fire, physical, spell}` and Bishop of
Death reads corruption 0.5, fire 0, physical 0, spell 0.

---

## 1. THE RULING - what Red Moon's dashboard IS

Red Moon's dashboard is **a publication surface for coaching claims whose
epistemic status is carried on the claim itself, over a corpus that is almost
always offline** - and it is specific to this project in three ways no loop
monitor shares. First, its DEFAULT and primary state is game-off: the six
promoted tables are a static patch-pinned corpus of 3,038 rows that answers real
coaching questions with the game shut, so live telemetry is an enhancement layer
and never the spine. Second, its central primitive is not a chart or a card but a
**five-state value token** - a number here is COMPUTED, MEASURED ZERO, OMITTED,
UNSOURCED-ON-BUILD or EMBARGOED, and the difference between the middle three is
the difference between a coach that is useful and a coach that quietly invents,
because this corpus puts a real 0.0 coefficient and an absent coefficient one
column apart inside a single weapon's three-ability kit. Third, and this is the
part that makes it a Red Moon artifact rather than a V Rising wiki, it is the
only surface that can eventually **falsify its own output**: ROADMAP gap 7 says
nothing in the project can check a computed time-to-kill against an observation,
the operator has now fixed the anchor as a bridge-side boss `Health.Value` time
series, and the dashboard is the only thing that watches a real fight while
holding the prediction. So the dashboard is an INSTRUMENT with a product surface
attached, not a product surface with instrumentation attached - it ships the
coaching answers that are honestly available today, renders the withheld ones as
present-and-locked with a stated lifting criterion, and is built so that the day
the anchor lands, the observed-versus-predicted panel drops into a slot that was
designed for it.

---

## 2. THE MERGED CONCEPT CATALOGUE

Categories:
**A CORPUS** disk-only, works game-off.
**B PRODUCT** the coaching answer a player reads.
**C FRAME** the honesty machinery that makes A and B publishable.
**D LIVE** requires the game running.
**E INGEST** not a dashboard feature at all.
**F BLOCKED** requires Bloodforge on 8783 or the gap 7 anchor.

Build size: S = one page plus one endpoint. M = two to four days. L = own spec.

### C-category - the epistemic frame

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **F1** | **THE FIVE-STATE TOKEN** | coaching s3 (all), provenance P4 row states, observer D5 | One server-side primitive every value passes through, emitting `{value, state, reason, source}`. Styled by CSS attribute selector. | YES - reason strings exist verbatim in `data/schemas/*.schema.json` `fields` blocks and in `blood_types` `value_source` | S | **SHIP-IN-CYCLE-4, FIRST.** Nothing else in the catalogue is honest without it. If it is invented per-panel it will be flattened to a nullable number by the third panel. |
| **F2** | **THE EMBARGO REGISTER** | provenance s3, coaching s3 EMBARGOED state, observer O5 | Tracked `docs/EMBARGO.json`: quantity, blocking gap, lifting criterion, status. Rendered as a named, sized, locked slot. | YES - gap text is in `ROADMAP.md`; the lifting criterion is now SETTLED (bridge-side boss `Health.Value` series) | S | **SHIP-IN-CYCLE-4.** The operator's gap 7 ruling converts this from a permanent tombstone into scaffolding with a delivery date, which is exactly what it must render as. |
| **F3** | **THE SUBJECT BAR** | coaching s4, provenance P5, plus A0 difficulty axis | Persistent sentence naming boss, loadout, blood, **difficulty**, power stat, and the exclusion rule. Defaulted tokens render LOUDER than chosen ones. | PARTIAL - difficulty fully sourced (A0); boss and exclusions sourced; power stat proven absent; loadout needs live bridge | S | **SHIP-IN-CYCLE-4** in its refusal state. Today it reads NO DEFAULT SUBJECT DECLARED and every cross-entity ranking refuses. |
| **F4** | **THE PROVENANCE STRIP** | observer O1, provenance P1 UI half, P5 | One strip: which host answered, build agreement, and for tables "provenance: unrecorded". | PARTIAL - `/health` fields exist; TABLE host does not exist in the envelope | S | **SHIP-IN-CYCLE-4 IN REDUCED FORM.** Renders `/health` only plus the literal words "table provenance: unrecorded". MUST NOT infer host from the zero-localization heuristic. |
| **F5** | THE EMBARGO SERIALIZER GATE | provenance s3 | Encoder raises on any quantity whose register status is not LIFTED. | Needs Bloodforge | S | **DEFER to the cycle that ships Bloodforge.** Correct idea, no quantity to gate yet. Its cycle 4 stand-in is F1 - the token is the choke point. |
| **F6** | PER-NUMBER PROVENANCE BADGES | observer O1 hover, provenance P1 UI half | Hover any figure for host, build, capture time, gate verdict. | NO | M | **REJECT for cycle 4.** The provenance lens ruled against its own concept and it was right: one reader who already knows the caveats. Revisit when a second consumer exists. |
| **F7** | COUNT RECONCILIATION STRIP | provenance P6 half two | Doc says N, dashboard counts M, show both. | NO - doc counts live in prose | M | **REJECT.** Making prose tables machine-readable is a bigger job than the bug class it catches. The derive-at-render half of P6 is absorbed into A1 and survives. |

### A-category - the corpus, works with the game off

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **A1** | **THE CORPUS LEDGER** | **observer O4 + coaching C2 + provenance P4** - three independent inventions of one panel | Per `table.field`: DECLARED, PRESENT n of N, state, distinct values, range, and the reason served from the schema. Plus search over the named rows. Every count derived at render time, never read from a stored summary. | YES, entirely on disk | M | **SHIP-IN-CYCLE-4.** The single highest-value panel in the catalogue. **MERGE NOTED:** these were three names for one grid; building them separately would have produced three disagreeing accounts of the same absence. |
| **A2** | **THE PIN BOARD** | provenance s2 | Five build values side by side - INSTALLED, EXTRACTED, PROMOTED, ASSERTED, VALIDATED - never merged into one light. Splits into rows on divergence, naming what is owed. | FOUR of five. **VALIDATED is unbuildable: `ENGINE_VERSION` has NO definition anywhere in the repo** (main-session correction 5), despite ROADMAP and BLOODFORGE calling it pinned. | S | **SHIP-IN-CYCLE-4, four rows plus one honest fifth.** The VALIDATED row renders UNSOURCED-ON-BUILD with the reason "ENGINE_VERSION is described in docs but has no definition in code". A pin board whose fifth pin is a doc-only string is exactly the drift the board exists to show. |
| **A3** | **THE PATCH DETECTOR VIEW** | provenance s2 detection loop | Poll the install `VERSION` file, content and mtime, and show whether the scheduled re-extract is armed. | YES. **CORRECTED: `RM-DataRefresh` IS installed and Ready, next run 2026-08-02 05:30** (main-session correction 1). The lens claim rests on a mangled probe. | S | **SHIP-IN-CYCLE-4 as one row of A2, rewritten.** The row reads "RM-DataRefresh: Ready, next 2026-08-02 05:30" and the state is armed, not missing. The lens's underlying point survives with a better example - see section 6, prohibition 7. **Never auto-remediate:** the board offers a button, never a schedule. |
| **A4** | THE DATA JOURNAL | provenance P3 | Append-only tracked NDJSON, one line per promotion, with per-field presence deltas. | YES at promotion time | M | **DEFER, but flag as the highest-value NON-dashboard item found by any lens.** `data/rmdata/` is gitignored and the extractor logs nothing by design, so a table row has no history of any kind. This is a correctness hole independent of cycle 4. It is E-category work. |

### B-category - the coaching product

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **B1** | **THE KIT SHEET** | coaching C1 | Per weapon TYPE - 16 rows, not 205 - the ability groups with cast, post-cast, cooldown, coefficient, damage type. | YES. Confirmed: 563 item-to-ability links fan out to only **47 distinct groups**, of which 32 reach damage; `is_weapon_ability` true on 42 of 1818. | S | **SHIP-IN-CYCLE-4.** Cheapest real product in the cycle. The coefficient column is OMITTED on 154 of 563 links and therefore refuses to sort. |
| **B2** | **KIT UPTIME (the headline)** | coaching s2 | Committed animation seconds per full rotation, and the share attached to a damaging cast. | YES - `cast_time` 1815/1818, `cooldown` 1818/1818, `post_cast_time` 1815/1818 | S | **SHIP-IN-CYCLE-4 as the headline.** Decisive reason: it is the ONE published number that is **falsifiable today with a stopwatch against a training dummy** - no boss, no live world, no kill. It lets Red Moon practise the gap 7 discipline before the anchor lands. |
| **B3** | **THE HAZARD LOADOUT PLANNER** | coaching C3 | Pick a hazard, rank the cloaks and bags that answer it, show the MaxHealth traded away. | YES, in full. **CONFIRMED** (correction 2): SunResistance 34, GarlicResistance 22, SilverResistance 22, HolyResistance 8, FireResistance 8, all real `Add` magnitudes, concentrated on the cloak slot. | S | **SHIP-IN-CYCLE-4.** Highest product-value-per-hour on the list, touches no boss row and no ability row, and the four resistances bosses cannot express are exactly the four players CAN. Hard limit from A0: **magnitudes only, never a percentage, never a survival time.** |
| **B4** | **THE BOSS LADDER** | coaching C4 + coaching s3 resistance chips | 65 bosses by level with the gaps visible, one power number, eight typed resistance chips in a fixed 4x2 grid. | YES, plus the A0 difficulty modifier | S | **SHIP-IN-CYCLE-4, amended by A0.** Three mandatory honesty burdens from the lens stand: one power field labelled level-derived; `max_health` OMITTED not zero; `CHAR_Bandit_Leader_VBlood_UNUSED` excluded by a stated visible rule. **Fourth burden added here:** the ladder must state its difficulty, because Brutal moves every level by +3 and every power by 1.7x. |
| **B5** | THE SWAP DELTA | coaching C5 | Signed per-stat delta vector for a candidate swap. Refuses to produce a scalar. | PARTIAL - `items.stats` yes; the EQUIPPED set needs the live bridge | M | **DEFER to the live slice.** Correct concept, and the refusal to collapse the vector to a score IS the feature. Deferred because its left operand requires a running game. |
| **B6** | THE GOLEM TRAP CARD | coaching C6 | Four abilities deal 0.33x to V Blood targets. | YES. **CONFIRMED AND SHARPER** (correction 3): `vblood_damage_modifier` is BINARY - 1.0 on 728 of 732, 0.33 on exactly 4, all golem-form NPC abilities, and 1.0 on all 409 weapon-linked rows. | S | **SHIP-IN-CYCLE-4 as a footnote on B1, not a card.** It is one true sentence, not a panel. Its real value is inverted and belongs in the test suite - see section 6, prohibition 8. |
| **B7** | COEFFICIENT PER CAST-SECOND | coaching s2 runner-up | The sexier damage-rate headline. | Inputs yes, the SELECTOR no - `power_stat` proven absent across all 51 components | S | **DEFER to the combat-math spec.** Comparing Mace against Spear coefficients asserts a shared denominator Red Moon cannot currently name. Permissible earlier ONLY labelled as a within-type comparison. |
| **B8** | THE ECONOMY / RECIPE GRAPH | coaching s5 forward look | Crafting path solver. | NO - **only 263 of 663 `output_guid` join `items.json`, and 79 of 215 ingredient GUIDs** | L | **REJECT for cycle 4.** A 40 percent dangling graph renders holes that look like structure. This is the exact failure the five-state token exists to prevent, at graph scale. Cycle 6. |
| **B9** | A SINGLE BUILD SCORE | coaching, explicitly not proposed | - | - | - | **REJECT permanently.** It is a TTK wearing a costume. Collapsing PhysicalPower against MaxHealth against attack speed requires precisely the weighting the embargo withholds. |
| **B10** | A BOSS RESISTANCE RADAR | coaching, explicitly not proposed | - | - | - | **REJECT permanently.** Lies twice: the axes are not commensurable, and the four unmeasurable types vanish from the chart, silently claiming a boss has four resistances when it has four measured, four unmeasurable and eight conceptual. |

### D-category - live, requires the game running

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **D1** | **THE BRIDGE LADDER** | observer O2 + observer D2 message ladder | Six-rung lit ladder over the closed `state_reason` set plus unreachable, each rung with authored copy, never a raw code. | YES - `state_reason` is a closed set of six | S | **SHIP-IN-CYCLE-4.** Cheapest live concept, and it is what makes the game-off default legible rather than broken-looking. Rung 6 is NOT `ready:true` - `ready` only means the prefab map settled. |
| **D2** | **THE VITALS TAPE** | observer O3 | Rolling 10-minute window of health, blood, blood quality, `is_dead`, position deltas. | YES when the game runs | M | **DEFER to late cycle 4 or cycle 5.** Ruling against the observer lens, which ranked it central - see conflict 5. It is the ONLY place blood quality becomes a number, which is a real argument, but the game is usually off and the tape is the most expensive live concept. **Design the fight-window mark now; build the tape later.** |
| **D3** | **SSE TRANSPORT** | observer s2 | Server samples the bridge at 2 Hz and emits on change; browser holds one `EventSource`. | Bridge offers NO push - `HttpListener`, five GET routes | S-M | **SHIP-IN-CYCLE-4 LAST, and only if D1 has landed.** Two details are MANDATORY, both corrections to the reference implementation: a **15 s heartbeat comment frame** (RM's normal state is a silent stream for hours) and **server-side coalescing at one frame per 500 ms**. Without the heartbeat, a healthy idle stream is indistinguishable from a dead one on a surface whose default is no data. |
| **D4** | TABLES ON THE STREAM | rejected by observer s2 tier C | - | - | - | **REJECT.** The tables change once per game patch. Serve them as a plain GET with an ETag over build plus schema_version plus mtime. The only live signal they need is a one-bit reload event. |
| **D5** | DUMPS ON A TIMER | rejected by observer s2 tier D | - | - | - | **REJECT permanently.** A dump runs ON THE GAME'S MAIN THREAD behind a global lock with a 30 s ceiling. A dashboard refreshing a dump on a timer would periodically hitch the operator's live game. Explicit operator action only. |

### E-category - ingest side, not a dashboard feature

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **E1** | **THE STAMP** | observer 0.5 + provenance P1 | Promoted envelope gains a fifth key `provenance`: host, capture time, dump sha256, localization counters, count-gate verdict. | YES - already computed at ingest and printed to a terminal, then discarded | S-M | **SHIP, BUT NOT AS CYCLE 4 DASHBOARD WORK.** It is roughly "stop discarding what you already compute". **Envelope confirmed as exactly `{table, build, schema_version, rows}`** (correction 4). The claim that a fifth key passes the frozen `validate_table` unchanged is REASONED, NOT PROBED - it must be probed before anyone edits ingest. Needs an operator ruling because it touches the frozen-file boundary in spirit. |
| **E2** | **THE DEAD-GATE TEST** | provenance P2, shipped as the lens itself recommended | Assert every entry in `_CHECKS` inspected at least one entry across the promoted tables. | YES | S | **SHIP as a test, REJECT as a panel.** About 20 lines catches the whole `items.stats`-became-a-list bug class. A gate-attestation panel needs a human to look at it, and the bug it catches is one nobody looks for. |
| **E3** | `_incoming` CLEANUP | provenance M7 | All six quarantined files from the last run still sit in `tables/_incoming/` - verified still present today. A reader cannot tell promoted from pending. | YES | S | **DEFER, file as a separate housekeeping item.** Real, small, and not cycle 4. |

### F-category - blocked

| # | Name | Merged from | Purpose | Inputs exist? | Size | Verdict |
|---|---|---|---|---|---|---|
| **F8** | **THE FALSIFICATION LEDGER** | observer O5 | Predicted TTK beside the OBSERVED one, with the loadout and blood quality live at the time, and a running signed error. | NO - needs Bloodforge served on 8783 (the package is `bloodforge/` and nothing binds that port yet) and the gap 7 anchor | L | **DEFER, and it is the reason the whole surface exists.** With the anchor now settled as a bridge-side boss `Health.Value` series, this is no longer speculative. **Cycle 4's obligation is to leave the slot, not to fill it:** D2's tape must be designed so a fight window can be marked and exported, and F2's register must name this as the panel that appears when the embargo lifts. Marking the hook is free; building the panel is not. |
| **F9** | MERGED `/api/state` | observer open q2, `docs/API.md:48` | "Merged bridge and engine state". | Half unimplementable - 8783 has nothing behind it | S | **AMEND THE DOC.** Ship `/api/state` with the engine half rendering "combat math not built yet", which is also the exact shape the degraded coach-loop message needs later. |

---

## 3. THE RANKED CYCLE 4 SLICE

Ruthless ordering for one operator on one box. Everything above the line has
inputs on disk today. The live leg is below the line and is genuinely optional to
cycle 4 completion.

**1. F1 THE FIVE-STATE TOKEN.** Server-side primitive emitting
`{value, state, reason, source}`; CSS attribute selectors do the styling.
*Acceptance:* one endpoint returns all five states over real rows, and the
schema-sourced reason string for `items.tier` is byte-identical to the text in
`data/schemas/items.schema.json` - proving it is served, not retyped.

**2. A1 THE CORPUS LEDGER.** The merged O4 plus C2 plus P4 grid.
*Acceptance:* every count on the page is derived at render time from the
collection it describes, verified by a test that greps the dashboard source for
numeric literals adjacent to count-shaped labels. The grid distinguishes
`items.tier` 0 of 425 UNSOURCED-ON-BUILD from `ability_stats.coefficient` omitted
on 1086 of 1818 OMITTED, and both from a real 0.

**3. B1 + B2 THE KIT SHEET AND THE UPTIME HEADLINE.** 16 weapon-type rows.
*Acceptance:* the coefficient column control is disabled with its reason visible,
AND one weapon type's committed-seconds figure has been checked against a
stopwatch and the result recorded - pass or fail. A published number nobody tried
to falsify does not count as this item being done.

**4. B3 THE HAZARD LOADOUT PLANNER.** The M3 find, confirmed.
*Acceptance:* the surface renders "+45 sun resistance from gear" and the page
contains no percent sign and no duration anywhere in the resistance area. A test
asserts that.

**5. A2 + A3 THE PIN BOARD.** Five stages, four sourced.
*Acceptance:* all four sourced pins agree today and render as one line; the
VALIDATED row renders UNSOURCED-ON-BUILD naming the missing `ENGINE_VERSION`
definition; the RM-DataRefresh row reads Ready with its next run time; and
forcing a divergence in a fixture splits the board into rows.

**6. F2 + F3 THE EMBARGO REGISTER AND THE SUBJECT BAR.** The two frame widgets.
*Acceptance:* `docs/EMBARGO.json` exists, tracked, ASCII, with `time_to_kill`
blocked on gap 7 and its lifting criterion stated as the bridge-side boss
`Health.Value` series. The TTK slot renders at full value width, locked, with
that criterion visible. The subject bar reads NO DEFAULT SUBJECT DECLARED and
every cross-entity ranking refuses.

**7. B4 THE BOSS LADDER.** 65 rows by level, eight typed chips.
*Acceptance:* the four hollow chips for holy, silver, garlic and sun are present
and occupy their slots; the ladder names its difficulty; the `_UNUSED` exclusion
is visible in the subject bar, not buried; and the honest headline over the
resistance grid is the sentence "4 of 65 bosses carry any resistance rating".

--- below this line, only if 1 through 7 have landed ---

**8. D1 THE BRIDGE LADDER.** Six rungs, authored copy, allowlisted error codes.
*Acceptance:* with the game off, the page is FULL and useful and shows one quiet
line, not an error state, not a spinner, not a modal. With the bridge returning
each of the six reasons from a fixture, the correct rung lights and no raw code
or raw error string reaches the DOM.

**9. D3 SSE.** One `EventSource`, targeted DOM updates.
*Acceptance:* an idle stream emits a heartbeat within 15 s and the client
distinguishes idle from dead; two bridge changes 100 ms apart produce one frame,
not two; and updating a value does not destroy focus or selection in the ledger
search box.

**Explicitly NOT in cycle 4:** D2 the vitals tape (design the fight-window mark
only), B5 the swap delta, A4 the data journal, F6 per-number badges, F8 the
falsification ledger, B7 coefficient-per-cast-second, B8 the recipe graph.

**Adjacent but separate:** E1 the stamp and E2 the dead-gate test are ingest
work, worth doing even if the dashboard were cancelled, and should be their own
item rather than smuggled into cycle 4's diff.

---

## 4. THE CONFLICTS, AND THE RULINGS

### Conflict 1 - how much provenance machinery is worth building
**The disagreement.** The observer lens calls the table-envelope provenance
amendment "the single highest-value, lowest-cost change my lens asks for" and
"the highest-value item in cycle 4". The provenance lens - the one that would
build it - argues against its own thesis: "over-engineering as a DASHBOARD
FEATURE, under-engineering as an INGEST FEATURE", notes that every historical
failure was caught by a document, a test or an agent recounting and none by a UI,
and warns that "a provenance stamp is itself an unverified claim ... a gate that
silently no-ops with better typography". The coaching lens is silent, which is
itself a data point about what a player-facing surface needs.

**RULING: split the concept along the line the provenance lens drew, and take
both halves on different schedules.** The DATA half (E1, the stamp) is worth
building and the observer lens is right about its value - but it is INGEST work,
not cycle 4 dashboard work, and it must not be counted toward cycle 4. The UI
half (F6, per-number badges) is REJECTED for cycle 4 on the provenance lens's own
argument, which I find decisive: with one reader who already knows the caveats,
three surfaces get read and twenty get skimmed, and a skimmed provenance surface
converts "I should check" into "it was green". Cycle 4 gets exactly two
provenance widgets - the Pin Board and the Corpus Ledger - and the strip in F4
that says "table provenance: unrecorded" until E1 lands. **Reason for preferring
the builder's self-critique over the requester's enthusiasm:** the provenance
lens is the only one of the three that costed its own concepts against a real
reader, and its prediction is testable - if the operator reads the Pin Board
weekly and never wants a badge, it was right.

### Conflict 2 - server-rendered HTML versus page-as-pure-function-of-the-API
**The disagreement.** Observer and coaching both require server-rendered first
paint. Observer: the game-off view must be fully populated before a byte of JS
runs. Coaching: "a coaching claim that silently disappears when a script fails is
strictly worse than no claim". The provenance lens requires the opposite - "the
page is a pure function of `/api/state`" - because it puts embargo enforcement in
the JSON serializer, and it admits the gap itself: "a number rendered server-side
straight into HTML bypasses it entirely".

**RULING: server-rendered, two lenses to one, and the provenance lens's
constraint is dissolved rather than overruled.** Its architecture was derived
from a false dichotomy. Move the enforcement point from the SERIALIZER to F1, the
five-state token: a single server-side function every value passes through,
consumed by BOTH the HTML renderer and the JSON encoder. Enforcement at the token
is strictly stronger than enforcement at the serializer, because it covers the
HTML path the provenance lens conceded it could not cover. This costs nothing -
F1 is item 1 in the slice for independent reasons - and it removes the only
argument for an empty shell that becomes useful once JS boots, which is the wrong
default for a surface whose main live input is usually absent.

### Conflict 3 - three states of uncertainty or five
**The disagreement.** The observer lens designs three (present, omitted, stale)
and treats stale as a peer. The coaching lens insists on five and argues that
collapsing any two reintroduces the `items.tier` failure. The provenance lens
implicitly needs four (its occupancy matrix has declared-absent, present-zero,
not-in-schema, embargoed).

**RULING: FIVE, and STALE is not one of them.** The coaching lens is right on the
merits and the corpus proves it: a real 0.0 coefficient and an absent coefficient
sit one column apart in the same weapon's kit, and `items.tier` versus an omitted
row resolve differently - an omitted row may fill on the next dump, an unsourced
field never will, and a player who keeps checking back is being wasted. Staleness
is an ORTHOGONAL AXIS, not a sixth state: any value in any of the five states can
be fresh or stale, and stale is rendered as a dimming plus an age stamp over the
state token, never as a replacement for it. See section 5.

### Conflict 4 - may the dashboard touch the exploratory dump endpoints
**The disagreement.** Only the observer lens raises it, and hedges - "link for a
human yes, parse into a panel no", flagged as needing confirmation.

**RULING: CONFIRMED, and hardened.** The dashboard may render a link a human
clicks. It may NOT parse `/dump/components` or `/dump/statcontrol` bodies into
any panel, and it may NOT call any dump endpoint on any automatic path, timer or
retry. Two reasons, both measured: those endpoints are deliberately absent from
`/dump/prefabs` "so nothing downstream can start depending on its shape", and a
dump runs on the game's main thread behind a global lock. **This is not softened
by the gap 7 anchor ruling** - when the boss `Health.Value` series arrives it
must arrive as a promoted, schema'd route, not as the dashboard learning to parse
an exploratory body.

### Conflict 5 - how central is live state
**The disagreement.** The observer lens builds its whole surface around the live
leg and ranks the vitals tape as a core concept, with a real argument: blood
quality is a runtime multiplier over the entire combat model, `blood_types` ships
stat names with no magnitudes because every value is quality-scaled at runtime,
so the live feed is the ONLY place blood quality becomes a number. The coaching
lens never mentions live state except as one poll. The provenance lens notes the
bridge is probably not even running.

**RULING: the corpus is the spine, the live leg is the enhancement, and D2 is
demoted below the line.** The observer lens's argument about blood quality is
correct and survives as the reason D2 is DEFERRED rather than REJECTED. But the
decisive fact is the one the observer lens itself supplied: "a closed game is the
ordinary case rather than a defect". A surface whose most expensive panel only
works in the minority state is mis-invested for a solo operator. Cycle 4 ships
the game-off product completely and the live ladder cheaply; the tape follows.

### Conflict 6 - how far does refuse-to-rank reach
**The disagreement.** The coaching lens rules that every ranked surface refuses
until a subject vector is declared, and calls a sensible fallback "the structural
bias BACKLOG names". Taken literally that also disables the boss ladder, which
the same lens ships.

**RULING: refusal binds CROSS-ENTITY value rankings, not intrinsic ordinals.**
Sorting 65 bosses by `level` is sorting one field by itself and needs no subject
vector, so B4 ships. Ranking two swaps against each other, or two weapon types by
damage, asserts a weighting that only a subject vector supplies, and refuses.
`gear_score` sorts only WITHIN the four armor categories it covers and refuses
across all nine - the control is per-scope. This resolves the lens's own
inconsistency without weakening its rule.

### Conflict 7 - the patch detector's factual basis
**The disagreement.** The provenance lens builds an argument on "`RM-DataRefresh`
is DEFINED BUT NOT INSTALLED" and concludes "Red Moon finds out a patch landed by
noticing, and that is not a figure of speech".

**RULING: the premise is REFUTED and the conclusion is withdrawn.** The task is
installed and Ready with a next run of 2026-08-02 05:30. The probe that produced
zero rows was mangled by MSYS path translation rewriting `/query`; schtasks exited
1 and the pipeline yielded nothing. **The lens's deeper point is upheld and is
now better evidenced than the lens knew:** a silent zero is indistinguishable
from a real zero, and this is the third instance in the project's history - after
1474-versus-1818 and 119-versus-146 - and the first where the silent zero fooled
an adversarial concept agent into designing around a fiction. That belongs in
section 6 as a prohibition and in the Corpus Ledger as a rendering rule.

---

## 5. THE FIVE-STATE UNCERTAINTY VOCABULARY - NORMATIVE

This is the most Red-Moon-specific thing on the dashboard. It is NORMATIVE. Every
value rendered anywhere on the surface carries exactly one of these five states,
emitted by F1 as `{value, state, reason, source}` and styled by CSS attribute
selector. A panel that invents a sixth state, or renders a value with no state,
is a defect.

| State | Rule for assignment | Visual treatment | May SORT | May AGGREGATE | May CHART |
|---|---|---|---|---|---|
| **COMPUTED** | Value present in the source, derivation traced to a named file, and a falsification route exists or is named as absent. | Body weight, full ink, tabular figures, right-aligned. | YES | YES | YES |
| **MEASURED ZERO** | Field PRESENT, value is `0`, and the zero is a CLAIM about the world. | The numeral `0`, in the SAME weight and the SAME ink as any other value. **A zero is never greyed.** Greying a measured zero is the single easiest way to turn it into an absence. | YES - it is an ordinary value | YES - it counts toward the numerator and the denominator | YES |
| **OMITTED** | Schema DECLARES the field; the dumper deliberately did not write it FOR THIS ROW. May fill on a future dump. | A hollow token `--` in the value's slot at the value's WIDTH, outlined not filled, dotted underline as the affordance for the reason. Never blank, never `n/a`, never `0`, never a dash character outside ASCII. | **NO** - the column REFUSES, with the reason on the disabled control. Not "sorts last". | **ONLY with an inline denominator** - "409 of 563 links", never a bare total. The denominator is part of the number, not a footnote. | **NO** - no interpolation, no dashed estimate segment, no gap that reads as continuity |
| **UNSOURCED-ON-BUILD** | No source exists ANYWHERE on this build, for ANY row. Will not fill on a future dump of this build. | The hollow token PLUS a superscript build marker; the reason names the build. Distinct from OMITTED because the RESOLUTION is distinct - a player who keeps checking back is being wasted. | **NO** | **NO** - the field has no population to aggregate over. Render the count of rows, not a statistic. | **NO** - and the axis it would have occupied is not silently removed |
| **EMBARGOED** | Computable from held inputs, deliberately not published pending a named criterion in `docs/EMBARGO.json`. | A FILLED slot: a lock-hatched block at the value's EXACT width, with the blocking gap and the LIFTING CRITERION readable in or beside it. **The width is the message** - nothing is missing, something is held back. | **NO** | **NO** | **NO** - and the chart itself is embargoed, not just the series |

### Binding rules that apply across all five

1. **Absent is never encoded by colour alone.** Every non-COMPUTED cell carries a
   GLYPH and a WORD. A greyscale screenshot pasted into a ledger entry, a
   colourblind reader, or a dark-theme rendering must all preserve the
   distinction the surface exists to make. The page renders correctly in both
   light and dark themes.
2. **An omission occupies its slot.** Never collapse a row, hide a column, or
   drop an axis because it is empty. The four hollow resistance chips ARE the
   layout, not a blemish on it.
3. **Reason strings are SERVED, never authored in the frontend.** They already
   exist verbatim in `data/schemas/*.schema.json` `fields` blocks and in
   `blood_types` `value_source: "blood_quality_scaled_at_runtime"` - the only
   place in the corpus where the reason for an absence is machine-readable, and
   the model for the whole vocabulary. A schema amendment must propagate with no
   UI change.
4. **STALE is an orthogonal axis, not a sixth state.** Any value in any state may
   be stale. Stale renders as dimming plus an explicit age stamp OVER the state
   token, never as a replacement for it. **Never blank a stale panel** - a coach
   reviewing the fight that just ended wants the last known good values,
   correctly labelled, far more than an empty box. `snapshot_age_s` is **-1 when
   there is no snapshot at all** and must render "no snapshot yet", never as an
   age.
5. **No soft uncertainty anywhere.** No greys for maybe, no dashed estimate bars,
   no interpolation, no placeholder sparklines, no error bars over unheld data. A
   value is held or it is not.
6. **The token is a server-side primitive.** If it is invented in a template it
   will be reinvented differently on the next panel, and MEASURED ZERO versus
   OMITTED will die in the third one.

---

## 6. WHAT CYCLE 4 MUST NOT DO

Each traces to a measured fact.

1. **Must not average, sum, radar or otherwise combine the boss resistances.**
   The four measured axes are not commensurable - physical and spell are
   FRACTIONS, corruption is a FRACTION, fire is an integer RATING with no held
   conversion constant - and the four unmeasurable types would silently vanish
   from any chart. Confirmed today: `difficulty/` holds no per-rating conversion.
2. **Must not sort by `items.tier`, or render it at all as a value.** The field
   is on 0 of 425 rows. It is not even a key. It is UNSOURCED-ON-BUILD and no
   consumer may treat it as an ordinal.
3. **Must not render an OMITTED value as 0, as blank, or as `n/a`.** Health 0
   means dead; health missing means unknown; these must not look the same. The
   plugin omits each vitals group rather than zeroing it precisely because "a
   zeroed one would diff as no motion forever".
4. **Must not publish a TTK, an EHP, a DPS in damage units, or any cross-weapon
   "best" verdict.** The gap 7 anchor is settled in principle and does not exist
   in fact. Boss `max_health` reads 0 on all 65 prefabs. Render EMBARGOED with the
   lifting criterion; do not render an estimate, a range, or a placeholder.
5. **Must not ship a single build score, a composite rating, or an arrow-up
   glyph implying "better" on a swap.** Any scalar that ranks two swaps against
   each other is a TTK with different units.
6. **Must not sort `gear_score` across the nine item categories.** It is present
   on 117 of 425 items and on 0 of 205 weapons, it derives from
   `ArmorLevelSource.Level`, and it covers exactly chest, legs, footgear and
   gloves. Seven of the 117 are a real 0 and must render as MEASURED ZERO. A
   gear_score column beside a weapon lies by adjacency.
7. **Must not render a zero without stating what was counted.** Every count is
   derived at render time from the collection it describes, never read from a
   stored summary, a header or a doc. The project has now been burned three times
   - 1474 versus 1818, 119 versus 146, and the `schtasks` probe whose mangled
   pipeline produced a zero that a concept agent designed a whole section around.
   A silent zero and a real zero must be distinguishable on the page.
8. **Must not let `vblood_damage_modifier` be trusted by inspection.** It is 1.0
   on 728 of 732 rows and 0.33 on exactly 4. A bug that drops the term is
   invisible in 99.5 percent of cases and would never be caught by looking. If it
   enters any computation, it enters with a regression test pinned to those four
   golem rows on the same commit.
9. **Must not call any dump endpoint on a timer, a retry or any automatic path,
   and must not parse an exploratory dump body into any panel.** Dumps run on the
   game's main thread behind a global lock with a 30 s ceiling.
10. **Must not surface a raw API error string, and must not pass through the
    bridge's own `message` field.** Render authored copy keyed on the KNOWN error
    code, fall back to generic copy for an unknown code, and log the raw body
    under `logs/` - which does not exist yet and must be created. Log the
    TRANSITION into and out of a degraded state with a repeat count, not every
    poll; at 2 Hz a refused connection is 7,200 identical lines an hour.
11. **Must not treat the game being off as an error state.** No modal, no red, no
    spinner, no empty-state illustration. The game-off view is the PRIMARY view
    and it is full.
12. **Must not auto-remediate a detected patch.** Running the extractor moves
    `current.txt` unconditionally and stands the count gate down without a human,
    converting a visible drift into a silent one. Detection and remediation are
    separate acts. The board offers a button, never a schedule.
13. **Must not display `ENGINE_VERSION` as though it were pinned.** It has no
    definition in code anywhere in the repo, despite ROADMAP and BLOODFORGE
    describing it as pinned. Render it UNSOURCED-ON-BUILD and say so.
14. **Must not rank against an undeclared default subject.** Not "ranks against
    boss zero", not "ranks by level as a sensible fallback" - a sensible fallback
    IS the structural bias. The refusal is the honest render and it creates the
    pressure that gets the vector declared.
15. **Must not infer the table host from the zero-localization heuristic.** Until
    E1 lands, the strip says "table provenance: unrecorded". An inferred
    provenance stamp is a gate that silently no-ops with better typography.
16. **Must not let the browser talk to 8777 or 8780 directly.** `bridge_client`
    is the one place a bridge URL is composed, the never-write-a-port-literal rule
    has no guard that reaches `.js`, and browser-side polling multiplies main-thread
    load on the game by the number of open tabs.

---

## 7. OPEN QUESTIONS FOR THE OPERATOR

1. **Does the promoted table envelope gain a `provenance` key (E1)?** It is
   already computed and discarded. The provenance lens reasons that a fifth
   envelope key passes the frozen `validate_table` unchanged because the
   undeclared-field check applies to ROW keys only - **but it ran no probe.**
   *Measurement that settles it:* add the key to a fixture envelope in a scratch
   copy and call `validate_table` on it. If it passes, this is a non-frozen ingest
   edit; if it fails, it is a frozen-file decision and an ADR.
2. **Is `.js`, `.html` and `.css` added to `ascii_guard.py` `AUTHORED_SUFFIXES`?**
   Confirmed: the guard covers .py .md .json .txt .ps1 .bat .cmd .toml .ini .cs
   .yml and NOT the three the dashboard is about to introduce. Cycle 4 would ship
   the project's first authored files outside its own hard rule.
   *Measurement:* none needed - it is a policy call on a frozen file. But it must
   be made in the cycle that creates the files, not after.
3. **Which difficulty is the default subject axis (A0)?** Boss level and power
   are difficulty-scaled - Brutal is +3 levels and 1.7x power on V Bloods - and
   every ladder the lenses drew is silently a Normal ladder.
   *Measurement:* read the operator's own save or server config for
   `GameDifficulty`; if it cannot be read from disk, the subject bar renders it as
   a DEFAULTED token in the loud style until the operator chooses.
4. **Does `docs/API.md` get amended for the missing engine half?** It promises
   `/api/state` merges bridge AND engine state; 8783 has nothing behind it.
   *Measurement:* none - it is a doc decision. My recommendation is to amend, and
   to ship the engine half rendering "combat math not built yet".
5. **What is the retention policy for the vitals ring buffer?** In memory and lost
   on restart, or persisted under `logs/`? The falsification ledger wants
   persistence; cycle 4 does not need it, but the choice constrains D2's design.
   *Measurement:* 4 Hz x 600 s is 2,400 samples, a few hundred KB - so the
   question is genuinely about policy and not about size.
6. **Is A4, the data journal, its own item?** `data/rmdata/` is gitignored and the
   extractor logs nothing by design, so a promoted table row has no history of any
   kind and an unattributed write is currently undetectable. This is a correctness
   hole that exists whether or not the dashboard ships.
   *Measurement:* compute the sha256 of each of the six promoted files today and
   check whether anything anywhere in the repo could reproduce that value. If
   nothing can, the hole is confirmed and the journal is worth its 80-120 lines.
7. **Is B2's stopwatch check a real acceptance gate or a nice-to-have?** I have
   written it into the slice as a gate. It is the only falsification Red Moon can
   perform before the gap 7 anchor exists, and if it is optional it will not
   happen.
   *Measurement:* one training-dummy recording of a Whip primary rotation against
   the computed committed-seconds figure. If the operator will not do it, B2
   should not be the headline and B1 ships alone.

# Red Moon History Notes


## 2026-07-26 - Cycle 2 part 1: ADR-005, the Python half, spikes S4 and S3a closed

Branch `cycle-2-bridge`, two commits (`9fbce0c`, `251803b`). Cycle 2 is NOT
done and is not claimed to be. Ledger entry 002a carries the detail.

The two things the last session said must be settled BEFORE code are settled:

1. Port arbitration. RULED: mint the fifth port. Client binds 8777, dedicated
   server binds 8780, chosen by `core.ports.bridge_port_for_host`. ADR-005
   amends ADR-003. The stand-down path, install step 6b, acceptance criterion 5b
   and risk R15 are STRUCK from the spec - do not implement them. Operator
   approved the frozen `core/ports.py` edit and the ADR amendment before it was
   made.
2. `PrefabCollectionSystem`. CONFIRMED, not corrected:
   `ProjectM.PrefabCollectionSystem` in `ProjectM.Shared.dll`, deriving from
   `Stunlock.Core.PrefabCollectionSystem_Base`. The label carried from
   `ROADMAP.md` survives contact with the build.

State at close, every number observed in one run after the last edit:
`python -m pytest` 241 passed (was 106), `python -m ruff check .` clean,
`python tools/ascii_guard.py` exit 0.

Shipped: `gen_bridge_ports.py`, `core/bridge_client.py`, `core/table_deep.py`,
`install_bepinex.py`, `rmdata_ingest.py`, `bridge_probe.py`,
`Directory.Build.props`, ADR-005, `docs/BRIDGE_SPIKES.md`.

Environment, done and verified live: BepInEx 1.733.2 installed into BOTH hosts
(233 files each, Thunderstore metadata dropped, `v3\` untouched). The dedicated
server launched once and generated 169 Il2CppInterop assemblies. Both v3
negative controls refuse.

Spike status. S4 CLOSED by measurement: a net6.0 library builds under SDK
10.0.301 with NO targeting pack and NO `global.json` - neither fallback is
needed. S3a CLOSED. S3 PARTIAL - the component types are located and named
(`EquippableData`, `RecipeData`, `RecipeRequirementBuffer`, `SpellLevel`,
`BloodQualityBuff`), the field mapping is not done. S1, S2, S5, S6 OPEN.

One process incident, and the plugin contract that fell out of it. `251803b` was
committed while a build agent was still live and captured its file mid-mutation
test, so that ONE commit carries a disabled v3 guard in `bridge_probe.py`.
Correct at `d614a09` and at HEAD; verified with `git show`, not taken on the
agent's word; no history rewrite. Standing rule, re-paid: do not commit while
agents live, and read `git show --stat` afterwards.

That agent's mutation testing also found a hole worth knowing about: a mutation
letting the loader-log banner matcher accept ANY line containing
`RedMoon.Bridge` SURVIVED 25 tests, because the negative fixture had no banner
token at all. That is cycle 1's failure mode a second time - a gate that cannot
fail. It is now pinned. CONSEQUENCE: `Plugin.cs` must emit a banner carrying
version, host AND port, shaped `RedMoon.Bridge v<semver> host=<client|server>
port=<n>`. The probe requires all three tokens.

Three things the next session must not get wrong:

1. The CLIENT has BepInEx but has NOT been launched, so it has no `interop\`
   tree yet. The R17 interop diff cannot run and no `.csproj` reference set may
   be pinned until it does. Launching the game client was left to the operator
   deliberately rather than done unattended.
2. S1 parts b, c and d are NOT answerable from static metadata. `LogOutput.log`
   carries loader activity only and never names a world - that was checked, not
   assumed. Enumerating worlds needs a plugin in-process, so the correct next
   artifact is a MINIMAL enumerate-and-log plugin, not the full bridge.
3. Honest correction to acceptance criterion 2: the `--target server` pointed at
   the root negative control is UNREACHABLE, not refused, because the installer
   derives the server target from `--root`. Prevented by construction, but not
   the control the spec asked for. Do not tick it off as passed.

## 2026-07-26 - Cycle 2 spec APPROVED, no code yet

Spec written and approved: `docs/superpowers/specs/2026-07-26-redmoon-bridge-design.md`.
ADR-004 records the ruling. No C# exists yet. Suite still 106 passed,
`ascii_guard` exit 0, both observed this session rather than carried forward.

Ground truth probed live, all of it new:

- The install holds TWO full game copies. Root is `v1.1.13.0-r99712-b17`, the
  pinned build and the one Steam launches. `v3\` is a stale `v1.0.10.4-r91333`
  copy that must never receive BepInEx. The installer asserts VERSION first.
- IL2CPP, not Mono (`GameAssembly.dll`). Loader is BepInExPack V Rising
  `1.733.2`, wrapping BepInEx 6.0.0 bleeding-edge `be.733` on CoreCLR net6.
- `VRising_Server\VERSION` reads `VRisingServer: v1.1.13.0-r99712-b17
  (202605251709)`. Same semantic build as the client, DIFFERENT prefix and
  trailing timestamp, so the install assert compares the semantic build only.
- The game was launched once. `AppData\LocalLow\Stunlock Studios\VRising\` now
  exists with `Player.log`, `Settings\v4\ClientSettings.json`, `CloudSaves\` and
  `ConsoleProfile\`. No save directory, because no world was created.
- Only SDK present is .NET 10.0.301. The plugin targets net6.0. That path is an
  unresolved build risk, not a working config.

Operator rulings: the plugin targets BOTH hosts (client and dedicated server,
ADR-004, overriding the client-only recommendation); `/state` becomes an
envelope carrying `state: null` plus a build stamp and `docs/API.md` was amended
to match; generating `RmPorts.g.cs` into the `test_ports.py` allowlist is
approved; the C# test project is deferred past cycle 2; and downloading the
BepInEx pack is authorized for the next session only.

Two things the next session must settle BEFORE writing code:

1. Port 8777 arbitration when both hosts run at once has a chosen answer, not a
   clean one - bind-time first-come, loser stands down, plus a procedural
   "start the server first". That is procedure, not enforcement. Minting a fifth
   port instead needs an ADR-003 amendment and that call belongs before
   implementation.
2. `PrefabCollectionSystem` is an UNVERIFIED label carried from `ROADMAP.md`. It
   is not a confirmed type name. Six spikes (S1 to S6) remain open and block
   implementation.

## 2026-07-26 - Cycle 1 COMPLETE and merged

Cycle 1 shipped end to end. Branch `cycle-1-harness`, 34 commits, merged into
`master` as `2a493ea`. Ledger entry 001 carries the detail.

State at close, all verified live rather than reported:

- `python -m pytest` 106 passed, `python -m ruff check .` clean,
  `python tools/ascii_guard.py` exits 0.
- `python tools/rmdata_extract.py` writes `data/rmdata/1.1.13.0-r99712/` with
  8379 localization strings and 28 markup codes, byte-identical across runs, and
  seeds `tables/` with five empty validated envelopes for the cycle 2 bridge.
- Remote is `https://github.com/Remus3/RedMoon` (private). `master` pushed.
- `RM-DataRefresh` is installed and Ready, next run 05:30 daily.
- Memory namespace live at
  `C:\Users\Administrator\.claude\projects\C--RedMoon\memory\`, restorable from
  the committed seed in `docs/memory_seed/`.

Two findings worth carrying forward, both caught by review rather than by
running code:

1. The precommit gate was wired with `"matcher": "Bash(git commit:*)"` -
   permission-rule syntax in a field matched against the tool name - so it never
   fired for the whole cycle despite being unit-tested and documented. Fixed to
   `Bash|PowerShell`, with a test that now rejects specifier syntax in any
   matcher. Worth remembering: a hook passing its unit tests says nothing about
   whether it is wired.
2. `docs/BLOODFORGE.md` named `data/rmdata/<build>/tables/*.json` as Bloodforge's
   inputs, but nothing created that directory and `empty_table()` had no
   production caller. Cycle 2 would have invented the path by accident. The
   extractor now produces the seam, never clobbering a populated table.

Parked items and every review ruling are archived in `docs/history_notes.md`.

## 2026-07-26 - Cycle 1 kickoff

Project created at `C:\RedMoon\`. Design spec and implementation plan written
and committed. Ground truth probed: V Rising build
`v1.1.13.0-r99712-b17 (202605251526)`, install at
`C:\Program Files (x86)\Steam\steamapps\common\VRising`, game never launched (no
`AppData\LocalLow\Stunlock Studios`), dedicated server ships with the client.
Ports 8777, 8778, 8779 and 8783 confirmed free; the `RM-*` scheduled-task
namespace confirmed unused.

Key decision: item and ability stat data cannot be extracted offline. It arrives
in cycle 2 from the runtime bridge dump. Cycle 1 ships localization, difficulty
presets, settings schema, and empty typed tables.

Deep archive. Pruned `WAKEUP_NOTES.md` entries and closed context land here so
the working documents stay short.

(No entries yet.)

## Cycle 1 - subagent-driven execution record (2026-07-26)

Archived from the SDD workspace ledger before the scratch directory was deleted.
It records every review finding, ruling and parked item from the nine-task run.

# SDD ledger - plan: /c/RedMoon/docs/superpowers/plans/2026-07-26-redmoon-cycle1-harness.md

Branch: cycle-1-harness (no worktree: the plan hard-codes absolute C:\RedMoon paths in .claude/settings.json and the memory namespace test, which a relocated worktree would break).

Task 1: implemented (commit 5dbca7e, 6/6 tests pass, CLI exit 0)
Task 1: review - spec compliant; 2 Important findings, both plan-mandated (verbatim from plan code); 1 Minor deferred
Task 1: minor (deferred): is_authored exclusion branches not independently exercised - .git/COMMIT_EDITMSG and assets/icon.png are already rejected by the suffix check, so EXCLUDED_DIRS/EXCLUDED_PREFIXES have no proving case
Task 1: controller-resolved warning - reviewer could not verify is_authored callers pass relative paths. Checked plan Task 7: precommit_gate calls is_authored(Path(rel)) where rel comes from git diff --cached --name-only, which is repo-relative. Safe.
Task 1: fix round 1/5 (3 addressed, 0 open; commits 5dbca7e..528f948)
Task 1: complete (commits a8cf3dd..528f948, review clean; plan text realigned in d174326)
Task 2: complete (commits d174326..dc4be1b, review clean)
Task 2: minor (deferred): tests/test_ports.py read_text has no UnicodeDecodeError handling - a non-UTF-8 .py would raise instead of failing cleanly
Task 2: minor (deferred): port-guard exclusion set omits .venv/venv/site-packages/node_modules/build/dist - latent spurious-trip risk if a later task vendors deps under the repo root (third-party code commonly uses 8888)
Task 3: review - spec compliant (byte-exact transcription verified programmatically); 1 Important plan-mandated (commit message lacks a scope); 1 Minor
Task 3: controller-resolved minor - CLAUDE.md frozen-file list names precommit_gate.py / text_first_guard.py / pytest_guard.py which do not exist yet. Task 7 builds all three. Not a defect; will be true at end of cycle.
Task 3: ruling - human accepted the scopeless docs commit; plan Global Constraints relaxed (scope optional for repo-wide doc commits). No history rewrite.
Task 3: complete (commits dc4be1b..293a4ab, review clean)
Task 4: ruling - human chose to name Riot Commander plainly in ADR-001 (filename kept, prose updated); ADR-003 stays anonymous; root docs stay clean
Task 4: fix round 1/5 (1 addressed, 0 open; commits b1bef26..81ac017)
Task 4: complete (commits caa7bb7..81ac017, review clean; plan realigned in 9ab2ed4)
Task 4: minor (deferred): test_every_adr_file_is_listed_in_the_index uses a raw substring check against the whole README, not the INDEX_LINE regex - an ADR named only in prose would satisfy it
Task 4: minor (deferred): docs/adr/README.md describes Status as one of four sections, but every ADR renders it as a bold inline field first, not a trailing heading
Task 5: ruling - human chose to close both coverage gaps now via a test-only synthetic-install fixture
Task 5: fix round 1/5 (2 addressed, 0 open; commits 10773f6..1a15024)
Task 5: complete (commits 9ab2ed4..1a15024, review clean; plan amended in 0ecf364). Real run: 8379 strings, 28 codes, build 1.1.13.0-r99712, idempotent, data/ gitignored.
Task 5: minor (deferred): no try/finally around tmp.write_text, so a mid-write exception leaves a stray .tmp (self-heals next run)
Task 5: minor (deferred): pointer write duplicates the temp+replace pattern instead of reusing a shared primitive
Task 5: minor (deferred): extract() never removes stale files in build_dir before writing - matters only on a future schema change
Task 5: minor (deferred): main() success path untested; a deep extract() failure would print a raw traceback
Task 6: complete (commits 0ecf364..81a702c, review clean; 16/16 module, 57/57 suite)
Task 6: minor (deferred): core/tables.py validate_table uses a bare _TYPE_MAP[spec["type"]] lookup - an unknown type string in a hand-edited schema would raise KeyError instead of returning a problem string, breaking the function's own contract
Task 6: minor (deferred): test_validate_table_rejects_a_wrong_type also sets tier to "x" incidentally; only the prefab_guid problem is asserted
Task 7: implemented (commit 759d60b, 9/9 module, 66/66 suite). Implementer caught and correctly fixed a backslash-escaping defect in the plan's settings.json; review confirmed the fix correct on its merits.
Task 7: controller-verified live - hooks run from a foreign cwd (C:\Users) and exit 0; settings.json decodes to clean single-backslash paths; deny reason resolves ports.DASHBOARD to 8778; rm_facts reports real build 1.1.13.0-r99712 and all four ports free
Task 7: review - 4 Important, all plan-mandated: (1) reproduced AttributeError crash on valid-JSON-non-dict stdin in 3 of 4 hooks, violating the always-exit-0 contract; (2) 4 unbounded subprocess.run calls; (3) ruff branch of check_staged untested; (4) docstring claims net-new ruff findings but code blocks on any finding
Task 7: ruling - human chose to fix all four, plus the port-literal minor in tests/test_hooks.py
Task 7: plan defect corrected by controller - settings.json escaping was \\ in the plan (would parse to a double backslash); plan now uses \ throughout
Task 7: fix round 2/5 (1 addressed, 0 open; commits b6d0fdd..4730bfb) - settings.json PostToolUse budget 60->900, only that field changed
Task 7: complete (commits 81a702c..4730bfb, review clean)
Task 7: minor (deferred): tests/test_hooks.py hardcodes each script's internal subprocess timeout in a dict rather than parsing it from tools/*.py, so it catches settings.json-side drift but NOT a future script-side timeout increase above its harness budget
Task 8: implemented (commit 3b58bd6, 6/6 module, 87/87 suite)
Task 8: review - approved; 2 Important plan-mandated (memory assertion loop omits project_stats_require_bridge; memory tests are structure-only so a blank body would pass); 2 Minor
Task 8: minor (deferred): tests/test_claude_config.py hardcodes an absolute per-machine memory path, so the test is non-portable to another machine or CI
Task 9: review - NEEDS FIXES. Important: --show space-joins argv so the printed command would not run if pasted (the /tr value contains an inner space); no test exercises a path containing a space. Plan-mandated: ledger entry lacks the commit hash its own format requires; commit message not imperative.
Task 9: minor (deferred): build_create_command raises a bare KeyError while build_delete_command raises a labelled one - asymmetric error quality
Task 9: minor (deferred): --install/--remove always act on the whole TASKS dict with no per-task selection, which will matter when cycle 8 adds more tasks
Task 9: minor (deferred): /rl HIGHEST is hardcoded in the builder rather than sourced from the spec dict like every other schtasks parameter
Rulings (human): ledger hash is backfilled at merge and /done gains that step; imperative commit mood dropped from the plan constraint (CLAUDE.md never stated it); both Task 8 memory-test weaknesses fixed now
Task 9: fix round 1/5 (1 addressed, 1 open; commits 1dc5150..dd9015b) - --show now uses list2cmdline and matches real execution; the new quoting test was proven toothless (an `or` fallback let it pass under both the fix and the original unquoted bug, and it never exercised main())
Task 9: fix round 2/5 dispatched - replace with a CommandLineToArgvW round-trip test asserting the /tr value tokenizes back to exactly one argument, plus a capsys test on main() --show asserting it differs from a naive space-join; both must be proven to fail against deliberately reverted production code
Task 8: fix round 1/5 (3 addressed, 0 open; commits dd9015b..3f6b864) - entry set now derived from disk via set-equality, body-content floor of 100 non-whitespace chars asserted on the body after frontmatter, done.md gained the ledger-hash backfill step with correct renumbering. Deliberate truncation proof: frontmatter-only file failed with "assert 0 >= 100", restored file passes.
Task 8: complete (commits cb79d10..3f6b864, review clean)
Task 9: fix round 2/5 (1 addressed, 0 open; commits 3f6b864..661d542) - old weak test deleted; TEST A round-trips through CommandLineToArgvW asserting the /tr token by equality; TEST B drives main() --show via capsys asserting both equality with list2cmdline and inequality with the naive space-join; both proven to fail against deliberately reverted production code
Task 9: fix round 3/5 dispatched - unused `from ctypes import wintypes` leaves the repo failing `ruff check .` (controller-verified, 1 error), which the project's own precommit gate would block
Task 9: fix round 3/5 (1 addressed, 0 open; commits 661d542..adafce3)
Task 9: complete (commits 3b58bd6..adafce3, review clean)
ALL 9 TASKS COMPLETE. Controller-verified at branch head: ruff check clean, 95 tests pass, ascii_guard exit 0.
FINAL REVIEW (opus, whole branch ae4bb80..b860e15): 1 Critical, 5 Important, 8 Minor. Critical C1 - the precommit gate never fired: matcher "Bash(git commit:*)" is permission-rule syntax in a tool-name field, and the plan had also dropped the PowerShell entry that makes the equivalent work upstream.
FINAL FIX WAVE (7 commits b860e15..015143b): C1 matcher corrected to Bash|PowerShell with a test banning specifier syntax in matchers; ledger count corrected to the observed 106; ROADMAP cycle 1 retired; the tables/ seam now produced by extract() with no-clobber and stale-file sweep; port-literal rule enforced for RM's own ports across .py/.cs/.json/.ps1; memory namespace seed committed under docs/memory_seed/ with a drift guard; 8 minors closed.
FINAL RE-REVIEW: all findings addressed, no new Critical/Important breakage. Both implementer deviations judged sound.
PARKED (controller adjudication, none load-bearing, no second fix wave):
Parked: seed_tables uses `if path.exists()` not `is_file()`, so a directory occupying tables/<name>.json would silently skip seeding forever - ruling: cannot arise without manual mischief inside a gitignored generated directory; fix opportunistically in cycle 2.
Parked: stale-file deletion in tables/ is extension-agnostic by design and matches the instruction as written, with a covering test - ruling: intentional, not a defect.
Parked: test_live_memory_matches_the_committed_seed and test_memory_seed_is_ascii lack their own non-emptiness guard - ruling: the sibling test_memory_seed_covers_every_live_memory_file asserts is_dir() and set-equality, so the suite cannot pass with a missing or empty seed.
Deferred (doc-sync opportunity, not a blocker): docs/BLOODFORGE.md never gained a line acknowledging the new never-clobber-a-populated-table guarantee that cycle 2 and 3 will depend on.

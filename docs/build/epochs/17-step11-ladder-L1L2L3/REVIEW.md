# Epoch review — the same prompts, vanilla against llama-leash

Oldest epoch first. Sections are numbered in the order they appear:

1. **The changes committed** since the previous epoch, with the defect each names.
2. **The prompt** fed for every task that epoch, read from the manifest as of that epoch's commit — not today's, because the corpus itself has been edited during the campaign — and labelled with which manifest defined it.
3. Then, per arm: **3a** time and tokens by phase (real sub-sessions for `conductor`, per-turn for the flat arms); **3b** the resulting code in full; **3c** every sub-agent dispatched, with the prompt it was given and the reply it returned; **3d** the transcript of every turn — what the model was thinking, which tools it called with which arguments, what came back, and what it said. Long blocks are clipped and every clip states how much it cut.

- **`baseline`** — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied
- **`doctrine`** — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions
- **`conductor`** — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

## Contents

- [Epoch 1 — observed](#epoch-1--observed)

---

# Epoch 1 — `observed`

Started 2026-08-30 06:11 EDT · 0 cells

## 1 · Changes since the previous epoch

350 commit(s).

| commit | what changed | defect |
|---|---|---|
| `400de4d5e` | Initial commit | — |
| `6ab88493e` | Initial commit | — |
| `0e836c6a9` | Converted scaffold into a local llama.cpp model harness for opencode | — |
| `f0dfb1599` | updated submodule pointers | — |
| `a987d8dc0` | plan review findings report and revised plan | — |
| `ddd4b9c2a` | conductor-build: preflight, gate tooling, durable state scaffold | — |
| `cf900182d` | conductor: 0.1 standing decisions | — |
| `da2dab202` | conductor: 0.3 scaffold | — |
| `d02b6427f` | conductor: 6.2 runner discovery probe | — |
| `0cf8b8265` | conductor: 0.2 wire contract pinned | — |
| `278df623f` | conductor-build: phase 0 gate fixes (skip-directive hole, wire-notes honesty) | — |
| `99751fc72` | conductor: 1.1 schemas | — |
| `88c07f813` | conductor: 1.2 shell/glob parse | — |
| `d078a21c5` | conductor: 1.4 purity + dual-runtime guards | — |
| `29c7e034d` | conductor: 1.3 freshness/failure-class/stops/verdict | — |
| `bbc0f8590` | conductor: 1.5 decision helpers | — |
| `1c295fb2f` | conductor-build: phase 1 gate fixes (parser hardening, DoS, freshness, classifier) | — |
| `6897359c8` | conductor-build: handoff refresh after phase 1 gate | — |
| `85e0f6a01` | conductor: 2.1 journal | — |
| `e4d0f402a` | conductor-build: phase 2 gate fix (journal torn-line heal) | — |
| `c61c99da8` | conductor: 3.1 FSMs | — |
| `680c6d9ec` | conductor: 3.3 wave scheduler | — |
| `bd35785f8` | conductor: 3.2 phase legality | — |
| `122e09e02` | conductor-build: phase 3 gate fix (trivial-report hole, single-source guard) | — |
| `0f29509af` | conductor-build: phase 4 start marker | — |
| `66f8549da` | conductor-build: handoff refresh (phase 4) | — |
| `37ddab765` | conductor: 4.2 gitio | — |
| `91ec26850` | conductor-build: 4.1 in-progress marker | — |
| `19d3d59d5` | conductor-build: branch B scaffold plan (deferred launch, documented) | — |
| `8038b0854` | conductor-build: handoff in-flight fix (4.1) | — |
| `db408bade` | conductor: 4.1 state store | — |
| `1319713b6` | conductor-build: 2.2 in-progress (bun leg added to gate) | — |
| `06818b3eb` | conductor: 2.2 bun runtime smoke | — |
| `8f89894ec` | conductor-build: phase 4 gate fix (answerQuestion wedge, id path-traversal, sandbox) | — |
| `d283cdd9e` | conductor-build: handoff refresh (phase 5 start) | — |
| `0f2a282a0` | conductor: 5.1 git policy | — |
| `cc0ed5598` | conductor: 5.2 edit + session gates | — |
| `0d1a0d2d5` | conductor-build: 5.3 in-progress marker | — |
| `3f794d6ed` | conductor: 5.3 gate wiring | — |
| `117617898` | conductor: 5.4 chat.message hook | — |
| `b5c1c06d4` | conductor-build: record phase 5 security findings (C-022) | — |
| `669c3d54e` | conductor-build: record phase 5 fix-round-2 finding (C-023) | — |
| `6dfcd223f` | conductor-build: phase 5 milestone gate fixes (8 security bypasses closed) | — |
| `9578281d0` | conductor-build: 6.1 in-progress marker | — |
| `6727e37cd` | conductor: 6.1 evidence engine | — |
| `004c2f812` | conductor-build: record phase 6 quarantine findings (C-024) | — |
| `968b5f840` | conductor-build: phase 6 milestone gate fixes (9 quarantine crash-safety holes closed) | — |
| `2f5933d7f` | conductor-build: 7.1/7.2 in-progress marker | — |
| `c3e1983cc` | conductor: 7.1 fanout engine | — |
| `0d39f3481` | conductor: 7.2 router client + failover | — |
| `e1c3c7cfc` | conductor-build: record phase 7 concurrency findings (C-025) | — |
| `650c35586` | conductor-build: phase 7 gate fix (watchdog covers create, held-job robustness) | — |
| `5291ccd71` | conductor-build: 8.1 in-progress marker | — |
| `df7f49fd6` | conductor-build: M5 marker scan scoped to production source (C-026) | — |
| `00cdcd7d7` | conductor: 8.1 doctrine packs | — |
| `355a13903` | conductor-build: record 8.1 commitSha (00cdcd7) + M4 PASS | — |
| `29a501147` | conductor: 8.2 injection | — |
| `e2264e1c9` | conductor-build: record 8.2 commitSha (29a5011) + M4 PASS | — |
| `102802d00` | conductor-build: phase-8 gate fix (doctrine packs) | — |
| `efd0f8424` | conductor-build: phase-8 gate fix (injection) — debug.md delivery | — |
| `64e181627` | conductor-build: phase-8 gate PASS + records (C-028) | — |
| `d6745deb4` | conductor: 11.1 router scaffold + upstream contract | — |
| `a4ab1da2a` | conductor-build: record 11.1 commitSha (d6745de) + M4 PASS | — |
| `1afea16f7` | conductor-build: relocate router main to src/main.cpp (per user request) | — |
| `aa478e8dc` | deep adversarial review prompt | — |
| `fd0dca164` | submodule pointers updated | — |
| `1ebcff3f0` | conductor-build: apply editor formatting (format-only, no semantic change) | — |
| `ed3d407e9` | conductor: 9.1 intake + question tools | — |
| `05b8b03ee` | conductor-build: record 9.1 commitSha (ed3d407) + M4 PASS | — |
| `efdffc526` | conductor: 11.2 router config | — |
| `75a25314d` | conductor: 9.2 planning tools | — |
| `d0c284fbc` | conductor-build: move tools/ and tests under src/, full-path includes | — |
| `ede81d658` | added docs diagram generation rules | — |
| `6b72333a3` | removed all non macOS presets | — |
| `1ad82b731` | conductor: 9.3 plan review | — |
| `70845624f` | user guide and technical dec docs | — |
| `dbf3abd98` | renamed llama-harness to llama-conductor | — |
| `1e9ae1356` | simplified warning compiler flags | — |
| `330504065` | updated submodule pointers | — |
| `ad8cce709` | updated license | — |
| `1758d1c47` | buildfix: lock llama.cpp build to c++17 | — |
| `e386ade1f` | json formatting consistency fix | — |
| `fe9380a2e` | enabled c++ formatting during configuration by default | — |
| `a3bf1e7e0` | conductor: 11.3 router proxy | — |
| `7dcb9e5b9` | conductor-build: per-process temp fixture root in 11.2 config test | — |
| `1440de817` | formatting | — |
| `49ecf6d61` | conductor: 9.4a test submission + vetting | — |
| `416eb7ee4` | conductor-build: 9.4a M4 PASS + commitSha; 9.4b assertions authored | — |
| `dfa557935` | conductor-build: promote 11.4 assertions (layout + 11.3-reuse corrections) | — |
| `e04fe1439` | conductor: 11.4 admission | — |
| `1f31f15cc` | conductor-build: 11.4 M4 PASS + commitSha; 9.4b red parked pending implementation | — |
| `40c6afe7f` | conductor: 9.4b green/validate/amend | — |
| `04173521a` | conductor-build: 9.4b M4 PASS + commitSha; next 9.4c | — |
| `f35f9f3c7` | conductor-build: promote 9.4c + 11.5 assertions (verified against HEAD) | — |
| `947f8db84` | conductor-build: record C-035 (queue_amend signature vs its registered tool) | — |
| `376ed9859` | conductor-build: promote 9.5a assertions; C-036 decides the roster-sizing rule (closes C-032 E14) | — |
| `53c5bf7b0` | conductor: 11.5 group affinity | — |
| `f5f00951b` | conductor-build: 11.5 M4 PASS + commitSha | — |
| `779def94d` | conductor-build: C-037 rulings from the 9.5b/9.6 fact-check | — |
| `0aed0c2fa` | conductor-build: park the 9.4c red pending the review-fix rounds | — |
| `c8b7dc84f` | conductor: 11.4 review fixes (thread-budget overflow, admission range checks) | — |
| `b6e3ed417` | conductor-build: fix a stray character in C-038 | — |
| `66530df8f` | conductor: 9.4b review fixes (vacuous verify, quarantine ENOENT, persist order, stale legality, path spelling) | — |
| `fc17f19d4` | conductor-build: promote 9.5b + 9.6 assertions; C-040 rulings | — |
| `95412710f` | conductor: 9.4c wave driver | — |
| `d28743c39` | conductor-build: 9.4c M4 PASS + commitSha | — |
| `ee254a8dc` | conductor: C-035 queue_amend takes ops and reconciles §2.5 items | — |
| `b676296c9` | conductor-build: promote 11.6/11.7/11.8 assertions; C-041 gives 11.8 the router CLI | — |
| `6f4af1bd0` | conductor-build: C-042 rules the skeptic-panel scope at item review | — |
| `8ff673512` | conductor-build: C-043 rules publishEnabled and the handleReport surface | — |
| `134781339` | conductor-build: C-044 audits every tool-vs-handler surface; two committed mismatches | — |
| `013ebc909` | conductor-build: promote assertions for 10.1, 12.x, 13.x, 14.x, 15.x | — |
| `ef06717f9` | conductor: 9.5a item review | — |
| `49fef22ef` | conductor: C-045 de-binarize the 9.4c test file + source-hygiene guard | — |
| `f1427450f` | conductor: 11.6 schema observer | — |
| `6bd390f6a` | conductor-build: record 9.5a + 11.6 M4 PASS and commitShas | — |
| `72467ba3f` | conductor: C-044/C-047 tool-binding guard, name and shape halves | — |
| `a5462b2ad` | conductor-build: refresh the live position and the recurring defect-class lesson | — |
| `5f1e592f5` | conductor: 9.5b publish + report | — |
| `7eec7a23b` | conductor-build: record 9.5b M4 PASS + commitSha | — |
| `41946bbe0` | conductor: 11.7 metrics | — |
| `40372e8df` | conductor-build: record 11.7 M4 PASS + commitSha | — |
| `e6625f8bd` | conductor: 9.5c stop reports + hatches | — |
| `0c1fa88ee` | conductor-build: record 9.5c M4 PASS + commitSha | — |
| `59ce81549` | conductor-build: C-050 records the wave driver's missing stage executors | — |
| `45e92ab09` | conductor-build: apply editor formatting to metrics.hpp (format-only, no semantic change) | — |
| `6b732a3ca` | conductor: 11.8 router CLI (C-041) | — |
| `d2bf346a6` | conductor: 9.6 worktree mode | — |
| `8e746cc5c` | conductor-build: record 9.6 M4 PASS + commitSha | — |
| `a26f556da` | conductor: C-050 the wave driver serves every item stage | — |
| `323c3ba4f` | conductor: C-053 item review binds its sessions to the item's tree | — |
| `dc116c054` | conductor-build: one build root — presets only, staging/ ignored | — |
| `0a893e0e7` | conductor-build: hoist the C++ tree — src/ becomes router/, tools/ moves beside it | — |
| `30cde4392` | conductor-build: refresh the HANDOFF header for the layout move and Phase 9 completion | — |
| `9639ae62d` | conductor: C-054 build the legalTools call-site guard C-048 claimed existed | — |
| `40c644362` | conductor: C-055 deny out-of-tree edit paths at normalization | — |
| `fe0e01257` | conductor-build: add NOW.md, a live view of what the build is doing | — |
| `2e3dd96fa` | conductor: 11.8 router live smoke | — |
| `7c7dd2e80` | conductor: C-056 close nine Phase 9 gate majors | — |
| `eeb30eda5` | conductor-build: reconcile the ledger with git and record the Phase 9 gate verdict | — |
| `46e169aef` | conductor-build: C-057 M5 scans the C++ tree again, with a floor so it cannot silently stop | — |
| `f99e533ee` | conductor-build: the §11 acceptance checklist as an executable artifact | — |
| `40a38570d` | conductor-build: record the Phase 11 gate's stage-1 prelude | — |
| `a6f5155a5` | conductor-build: C-058 execute Task 11.1 Step 2's live upstream measurement | — |
| `9c42528d6` | conductor-build: C-059 the plugin is a shell — open task-let 5.4a for the lifecycle half | — |
| `2557ab45f` | conductor-build: resolve the 5.4a/12.2 config-reader collision before either is built | — |
| `677b9fa25` | conductor-build: acceptance row 10 checks per-slot context, not just the slot count | — |
| `05cf2e478` | conductor-build: correct the committed-row count against the ledger | — |
| `2774e2d3f` | conductor: 15.0 replay tool | — |
| `589d22e79` | conductor: 12.1 serve wiring | — |
| `1d7074b72` | conductor: 15.2 dashboard | — |
| `6b63bf2fd` | conductor-build: refresh the live position after 15.0, 12.1 and 15.2 | — |
| `57c1d58fa` | conductor-build: Phase 11 red-team-by-data probe, executed and recorded | — |
| `f1693b6a2` | conductor-build: record the Phase 11 lens findings before the fix round | — |
| `2d1875395` | conductor-build: C-063 the Phase 11 gate's confirmed major; C-064 a name collision caught pre-commit | — |
| `1f606f365` | submodule pointer updates | — |
| `4fa91c4db` | conductor: 5.4a chat.message plugin wiring | — |
| `719e3fc61` | conductor-build: C-066 close the Phase 11 gate's truncation major, test-first | — |
| `d98434243` | conductor-build: Phase 11 gate PASS after one fix round | — |
| `097854050` | conductor: 10.1 continuation + ask gate | — |
| `5786a273f` | conductor-build: 10.1 close review findings | — |
| `e71054f40` | conductor-build: phase 10 gate stage 1 | — |
| `59e2da851` | conductor-build: phase 10 gate stage 1 repair | — |
| `c66cd86ca` | conductor-build: phase 10 gate fix round 1 | — |
| `a4277f811` | conductor-build: phase 10 gate fix round 2 | — |
| `203016d70` | conductor-build: phase 10 gate PASS after 2 fix round(s) | — |
| `72cd860fd` | conductor-build: phase 12 gate stage 1 | — |
| `09c8c5713` | conductor: 12.2 first-run setup | — |
| `cddd9b98f` | conductor-build: phase 14 gate stage 1 | — |
| `c4fa9f761` | conductor: 13.1 e2e scripted | — |
| `4afdf2b0a` | conductor: 15.1 ops docs | — |
| `588a04691` | conductor-build: close acceptance rows round 1 | — |
| `cf5035793` | conductor-build: close acceptance rows round 2 | — |
| `3784d1044` | conductor-build: completion report | — |
| `c6289e285` | conductor-build: C-076 rename 12.2's commit to its manifest message | — |
| `9a0d9399c` | conductor: 14.1 bench driver | — |
| `4c66810b3` | conductor-build: 14.1 gate record and C-077 | — |
| `e0bb7bf88` | conductor-build: phase 12 orphaned fix-round work, gated | — |
| `108ea25a7` | conductor-build: C-078 M5 scans the python half; gate legs use per-run scratch | — |
| `7b3ae584c` | conductor-build: C-079 phase gates 12, 13, 15 stage 2 verdicts | — |
| `a6ad3cd9e` | conductor-build: phase 15 gate fix round 1, 15.1's missing anchor test | — |
| `cc5fa11a1` | conductor-build: C-080 phase 15 fix round record | — |
| `fa3e810e0` | conductor-build: 13.1 composition root, the 22 tools bound | — |
| `7799d848e` | conductor-build: C-081 composition root record | — |
| `46bc73ffa` | conductor-build: CR-2 gate snapshot derived, one role vocabulary | — |
| `931523277` | conductor-build: C-082 CR-2 record, C-032 F1 refutation overturned | — |
| `c27b3b311` | conductor-build: phase 13 MAJORs 1-3, the e2e loops actually walked | — |
| `3b23175c4` | conductor-build: C-083 phase 13 fix round part 1 | — |
| `ca1c969c6` | conductor-build: phase 13 MAJOR 5, the bad ending actually walked | — |
| `f2e201c0b` | conductor-build: C-084 phase 13 fix round part 2 | — |
| `451061d33` | conductor-build: restore the §3.7 wedge detector, both halves | — |
| `0b1d6a3a3` | conductor-build: C-085 wedge detector record | — |
| `6082c5ffb` | conductor-build: acceptance-cluster subject scan, derived meta-tool set | — |
| `5083c5613` | conductor-build: C-086 two derivations made faithful | — |
| `37faf2216` | conductor-build: phase 12 python MAJORs, serve.py main() driven at last | — |
| `940334771` | conductor-build: C-087 phase 12 python half | — |
| `3ac58f043` | conductor-build: phase 12 setup MAJORs, no more successful-but-unusable | — |
| `b8b6c3250` | conductor-build: C-088 phase 12 setup half | — |
| `a48c34606` | conductor-build: G5 equivalence, a real two-arm run | — |
| `c72f71bf6` | conductor-build: C-089 G5 record | — |
| `253d263cc` | conductor-build: C-062 survivors pinned, each proven by mutation | — |
| `2576aed24` | conductor-build: C-090 C-062 survivors record | — |
| `f47848f90` | conductor-build: the DEBUG loop walked, a green item test over a red verify | — |
| `8ad2453fd` | conductor-build: C-091 DEBUG loop record | — |
| `12252a939` | conductor-build: M7 scenario 1, 16 rows named and 4 holes exposed | — |
| `c4906121a` | conductor-build: C-092 M7 scenario 1 record | — |
| `0d18a6d61` | conductor-build: enforcement-gap review prompt, built on the learned defect taxonomy | — |
| `be591f6f0` | conductor-build: review prompt, explanatory register with a worked entry | — |
| `171e7c760` | conductor-build: review prompt, add macro lens and completeness forcing functions | — |
| `9e85d085b` | conductor-build: split the review into a briefing plus three sequenced lenses | — |
| `67103841a` | conductor-build: group the review suite into conductor-review/, numbered by run order | — |
| `6509f05b3` | conductor-build: review workflows for steps 2-4, plus the runbook | — |
| `ce0549876` | conductor-build: split step 2 into three invocations, add skeleton-write and batching | — |
| `cfa929de5` | conductor-review: merged findings for steps 2-4, step-5 preflight, pre-step-5 corrections | — |
| `b6b5491fd` | conductor-build: phases 16-19 clarification addendum plan | — |
| `e537bca0a` | conductor-build: HANDOFF position update — review complete, step 5 next | — |
| `6a55d33f0` | conductor-review: step-5 decisions and fix-campaign plan; HANDOFF superseded ordering | — |
| `31456bc7c` | conductor-fix: Phase 0.1 D14 addendum amendment — A3-A6 constraints, five-file map, 17.4/17.5 dependency gates | — |
| `f6c0fdd89` | conductor-fix: Phase I.1 GAP-035 gate half — --test-timeout=120000, durable red-gate evidence (ISSUE-032) | — |
| `4d2bc1a87` | conductor-fix: Phase I.1 GAP-035 TS half — monotonic clock, append-position stale-red, tie-broken freshness (ISSUE-134 P14) | — |
| `e566d65f0` | conductor-fix: Phase I.2 ISSUE-002 + GAP-004 — tree slug/path brands, default main-tree writes; CR-2 rows verified landed, spec coverage bound | — |
| `5cd59515d` | conductor-fix: Phase I.3 ISSUE-088 — string/regex-aware stripComments, whole-tree canaries, audits un-blinded | — |
| `d5cbfd9a4` | conductor-fix: Phase I.4 ISSUE-001 — §6.4 injection wired with three-layer delivery witness; GAP-003 live-ish leg; GAP-005 generated MECHANICS; GAP-039 | — |
| `f0053194d` | conductor-fix: Phase II GAP-006/007/008/009/010/015/041 — legality choke point, TDD/scope seams closed, vet criteria bite; ISSUE-009/-011/-046/-048/-071 and 4 fix rounds | — |
| `f56c7e856` | conductor-fix: Phase III GAP-011/012/013/021/022/036/040 — review witnesses, D5-strict disposition, human-file provenance; ISSUE-049/-051/-052/-053/-072 + fix round | — |
| `d3a82b649` | conductor-fix: Phase IV security XS + concurrency/crash (D6 N-party lock) + honesty; ISSUE-015/-016/-019/-020/-021/-023..029/-037/-040/-041/-070/-100/-110, GAP-024/-026/-027/-028, D8/D9 + 3 fix rounds | — |
| `f33b95b4c` | conductor-fix: Phase V.1 doctrine content GAP-037/042/043/044 — generated run-shape, measured limits, uniform stuck protocol, ask-policy reconciled (verify folds into V stage) | — |
| `2f3b57d9c` | conductor-fix: Phase V.2 pre-live readiness GAP-032/033 + ISSUE-042 router key-bound + ISSUE-104/107/108/112; CONFIRMED | — |
| `2163ef086` | conductor-fix: Phase V ISSUE-108 — wait_until_ready backs off on non-raising non-200 instead of busy-spinning | — |
| `d9b44baac` | conductor-fix: Phase VII-A build floor — GAP-002 wiring manifest (catches ISSUE-001), GAP-016 vocab registry (cross-lang), GAP-020 unreachable-exports (deleted 2 dead), GAP-017 inversion, GAP-019 witnesses | — |
| `d7dabadef` | conductor-fix: Phase VII-B — GAP-018 mutation suite, GAP-029/034 report+replay witnesses, GAP-030/031 record checks, GAP-048 dashboard read (sound); MACRO-019/-020/-021 mechanisms | — |
| `464c84014` | conductor-fix: MACRO-021 operator-doc honesty — banner/second-session/wrapper/recorder claims corrected to HEAD, tests synced; limits 8/11 plan-immutability collision surfaced for owner | — |
| `e4f850a1c` | conductor-fix: HANDOFF position — non-live campaign complete, next action is owner-run 13.2 live smoke | — |
| `863ffa46a` | global repo docs sync, corrections, added coverage/explanations, drift corrections, diagram layout improvements, etc | — |
| `38c4469ae` | updated submodule pointers | — |
| `b0bc12838` | docs: end-to-end prompt atlas, pinned to the code by a parity test | — |
| `1b2e59934` | adding plan to work in carefully controlled read-only tool and linter interaction in a way that aims to log or prevent any side effects these types of tool calls could introduce | — |
| `7de99cb55` | updated llama.cpp submodule pointer | — |
| `e5b0ad9ee` | repo cleanup: drop completed-campaign scaffolding, repair stale references | — |
| `736c3c1f6` | Phase 20: measure the client contract instead of assuming it | — |
| `48f264dab` | Phase 21.1: sub-sessions are children of the orchestrator and name their role agent | — |
| `0183937e1` | minor revision to plan + formatting | — |
| `1c002bf1c` | Phase 21.2: one declaration for tool classes, and the side-effect taxonomy | — |
| `a07973968` | Phase 21.3: a built-in with no declared side-effect class is refused | — |
| `1cc7cda0d` | Phase 21.4: the network class is refused, in both lanes | — |
| `73bea2a92` | Phase 21.5: every allowed call leaves a record | — |
| `2793ddfb7` | Phase 21.6: a reader role cannot mint an edit override | — |
| `93b1177bf` | Phase 21.7/21.8: a session banner that exists, and the report that was computed and thrown away | — |
| `402a9e171` | Phase 22.4: buildCommand validates, so the documented key is reachable | — |
| `50b241f14` | Phase 22B: watch a run in flight, read-only by construction | — |
| `d12fb189c` | Phase 22.7: the current-generation dense model, every field looked up | — |
| `446d8e562` | Phases 22 and 22A: a bench that can measure the system under test | — |
| `de4dd25be` | Phase 23.1: preflight run, launch runbook, and the hand-off | — |
| `68f5f4079` | docs: the 14.2 runbook named a commit message row 12 would not have matched | — |
| `54b1a1ad1` | smoketest prompt | — |
| `c750d9a16` | conductor: 13.2 live smoke | — |
| `9a67b2ccf` | Corpus migration and the acceptance-cluster fix | — |
| `89e064b41` | conductor: close the G8/2.4 deadlock and make refusals visible | — |
| `60d2838bf` | observe: a live console for watching a run in flight | — |
| `bcc528e3f` | Rename to llama-leash and drop the absorbed corpus repo's references | — |
| `7c20792df` | compare-arms: the cross-arm scoreboard | — |
| `12c71fb0b` | run_and_watch: one command to run the benchmark and see all three arms | — |
| `c6242bcd9` | run_and_watch: check the model is served before starting anything | — |
| `99342835e` | run_and_watch: bring the model up for the run and take it down after | — |
| `7f0520944` | bench: measure the tree a timed-out cell left, and widen the served slot | — |
| `f3f19d993` | bench: give every cell a directory that starts from nothing | — |
| `84fdb2453` | bench: an arm denied a file in its own tree is the harness failing | — |
| `b465651fd` | bench: measure a cell on the clock its budget uses, and hold sleep off | — |
| `d536a306a` | bench: a refusal outside the arm's tree is the arm's dead end, not ours | — |
| `5ae68744c` | bench: keep the observer's per-turn view of a conductor run | — |
| `91b1828fe` | bench: keep the granular state, and check a run for defects already fixed | D06, D22, D23, D24 |
| `6a5a4c054` | conductor: name the next action and the next legal move, and vet trivial once | D13, D26, D27, D28, D29 |
| `be8c44900` | conductor: the out-of-tree refusal names the spelling the check accepts | D13, D30 |
| `76d323f74` | docs: withdraw D25 — the cluster guard is correct and already documented | D25, D29 |
| `4b0a9224b` | docs: record the preservation-by-restatement shape in the cluster residuals | D31 |
| `ca9c8576f` | conductor: never tell a session to call a tool its role may not call | D15, D32 |
| `6363cd7b5` | conductor: the receipt records the recommendation the block delivered | D32 |
| `6f18ce6c5` | conductor: the decompose brief names the files a decomposition may scope | D16, D29, D34 |
| `5186c04ed` | observe: tell a recorded "none" recommendation from an unrecorded one | D26, D32, D34, D35 |
| `914b94f21` | conductor: the decompose brief carries the code, not a list of its filenames | D34, D35, D36 |
| `d745cc2d9` | planning: read "X remains X" as preservation, not a second cluster | D31 |
| `948f1a883` | gen_tokens: measure what a cell EMITS, not what it was sent | D38, D39 |
| `b9bdb7461` | doctrine: say what the placeholder and decisions checks actually do | D38 |
| `e0b479feb` | docs: the watchdog abort is a deadline, not a diagnosis | D38, D39 |
| `3ead34070` | campaign: a fingerprint of zero needs its denominator | D38, D39 |
| `a9a146c9b` | bench: measure the epoch's own noise floor with baseline calibration reps | D38 |
| `2ca53e6ea` | campaign: epoch 13's token data is uninterpretable, and the control arm says so | D38 |
| `e4035456b` | campaign: the placeholder fingerprint counts a word, not a behaviour | D38, D39 |
| `285db0d9b` | fingerprints: count the hedging, not the noun | D38 |
| `17d8081a3` | gate: exempt the fingerprint fixture's two quoted hedge lines | — |
| `59f73ef08` | campaign: the logfmt counter-result, and a metric with no noise floor | D38, D39, D40 |
| `ee67f5b68` | campaign: scope D40's fix, and record why it is not written tonight | D40 |
| `b9f06e2e4` | campaign: epoch 13 closed — both changes confirmed, nothing moved | D38, D39, D40 |
| `1f69d9622` | classify: re-roll the checker, not the thing it was checking | D40 |
| `c1c1dddc5` | report: show the same prompt through all three harnesses on one page | — |
| `5612bbd3c` | report: refuse to pair a result with another run's tree | — |
| `c7b25255a` | bench: the corpus was shipping escaped prompts | D41 |
| `90182b4cc` | review: a per-epoch document, and archive the trees so it keeps working | — |
| `78860ca3f` | fanout: per-role watchdog deadlines, measured | D39 |
| `8958ef9a9` | campaign: pre-register epoch 14 before it starts | — |
| `4d6e450f5` | wiring: keep every role deadline above the router's queue wait | D42 |
| `d6fac5ab4` | prior_art: search what this repo already knows, before calling it new | — |
| `e07a8359a` | campaign: prior_art surfaces a hazard, the ledger clears it | — |
| `9cb8b503b` | campaign: design the stall-based deadline, and verify the signal exists | D43 |
| `fdae9d8e9` | ratios: report cost as a multiple of baseline, inside one epoch | — |
| `a5bdc269d` | plans: hand off the quality-judging instrument to a fresh session | — |
| `694725b59` | judge: the rubric lane gets a blind paired judge, and it is calibrated | — |
| `55ae319f7` | plans: the GPU runs one sequence at a time, and parallelism is not the first lever | — |
| `b1534dfe6` | campaign: doctrine beats baseline on test quality, and the conductor arm is 0/4 | — |
| `642cd8897` | judge: calibrate against inputs the size of the real ones | — |
| `e2c0b9959` | judge: derive the call timeout from the token budget instead of guessing it | — |
| `18da17a9a` | review: render what each run was thinking, called, and got back | — |
| `faf44580f` | instruments: the server publishes its own counters and the ledger says when | — |
| `bde32b6d1` | D43: the killed sessions were not stuck, and the archive cannot calibrate a stall | — |
| `ae7373dd6` | plans: crawl before walk, and the crawl rung was already built | — |
| `0ffa022db` | updated submodule pointers | — |
| `34d2b8203` | prompts: a reply one brace short was thrown away, and the rule it was judged by was never shown | — |
| `c425f4e02` | instruments: the router was six days stale, and the deadline was measuring a sample it had censored | — |
| `aa41776fd` | review: one directory per epoch, the sub-agents' own prompts, and a row that says what changed | — |
| `f72f3c926` | register: five defects, two withdrawn readings, and the first cell that poses the real question | — |
| `bbacb25b0` | plan: conductor_plan does not terminate, and the change set that follows from it | — |
| `224f381c9` | plan: six hours, sixteen laps, 397k tokens, no artifact — the loop has no exit | — |
| `04fefdc83` | register: epoch 20 final — 8 hours, 307k tokens, an empty diff | — |
| `bb93ff510` | serve: 131,072 per slot, KV measured at 64 KiB/token, and a router config that is read back (D52) | — |
| `b54d78fa4` | plan: the prompts that terminate - rule 3 narrowed (D48), every lens handed the tree (D49) | — |
| `3ad9d028f` | gates: the question surface closes (D50), a provider timeout says its name (D51) | — |
| `6cad7ca55` | register: D49-D52, the epoch-22 evidence, and the improve-cycle synthesis | — |
| `792bdaedc` | plan: the next-iteration handoff - ranks 6, 7, 2, 1, then the step9 run | — |
| `5107c1c4d` | observe: the console counts THIS run's tokens (D53), and INDEX stops repeating one cell | — |
| `fd74cd80d` | watch: a stall detector outside the plugin, at 45 minutes, that aborts nothing (D56) | — |
| `f18e960a5` | inject: the system prefix stops moving (D54), and the thinking channel gets a bound (D55) | — |
| `7a10ce30e` | register: D53-D56, and two instruments that were wrong about their own subject | — |
| `fdeaaa8c7` | register: epoch 23 pre-registered, and step9 pointed at an empty directory | — |
| `d54166fe6` | updated submodule pointers | — |
| `d3b211926` | register: epoch 23 - two items published, two expectations refuted | — |
| `18ab6ac6e` | epochs: epoch 23's review, emitted by the run that produced it | — |
| `5519e6e7f` | review-cost: the loop's price stage by stage, from a run's own records | — |
| `fa30376a3` | review: a nit stops blocking the merge doctrine says it never blocks (D57) | — |
| `c00f360a7` | register: epoch 23's review loop measured, and three of its readings refuted | — |
| `9fb80119e` | plans: the handoff this iteration executed | — |
| `6299b72ef` | bench: label which doctrine text a cell ran (doctrineDigest) | — |
| `420568cd4` | corpus: snake-tui-cpp — the first from-scratch task, and the first that scores a TUI | — |
| `0782c028b` | register: epoch 24 pre-registered — the first empty-seed cell | — |
| `68542f8d8` | watch: epoch 24 points at snake-tui-cpp and an empty directory | — |
| `b21118375` | register: D59 — the banner sizes a run by the tier, the task overrules it | — |
| `168eddfde` | register: D60 — a response over the delivery window is discarded, and its decode is invisible | — |
| `1bbbd0558` | register: epoch 24 killed, D61, and a token-sized rule for authoring a task | — |
| `37cd60e95` | corpus: the snake ladder — six rungs sized by the measured delivery window | — |
| `fa2aa6a66` | watch: epoch 25 runs the ladder's first three rungs into an empty directory | — |
| `11fda9daa` | corpus: the ladder's spec pins --version, which its gauge already graded (req 51) | — |


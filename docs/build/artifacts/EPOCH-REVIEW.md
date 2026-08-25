# Epoch review — the same prompts, vanilla against llama-leash

Oldest epoch first. Each section carries, in this order:

1. **The prompt** fed for every task that epoch, read from the manifest as of that epoch's commit — not today's, because the corpus itself has been edited during the campaign.
2. **The resulting code**, in full, for each arm.
3. **Time and tokens by phase** — real sub-sessions for `conductor`, per-turn for `baseline`, which has no phase structure to group.
4. **The changes committed** since the previous epoch.

- **`baseline`** — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied
- **`doctrine`** — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions
- **`conductor`** — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

## Contents

- [Epoch 1 — 20260822-024521](#epoch-1--20260822024521)
- [Epoch 2 — 20260822-044746](#epoch-2--20260822044746)
- [Epoch 3 — 20260822-052306](#epoch-3--20260822052306)
- [Epoch 4 — 20260822-062146](#epoch-4--20260822062146)
- [Epoch 5 — 20260822-154753](#epoch-5--20260822154753)
- [Epoch 6 — 20260822-160012](#epoch-6--20260822160012)
- [Epoch 7 — 20260822-204552](#epoch-7--20260822204552)
- [Epoch 8 — 20260823-012116](#epoch-8--20260823012116)
- [Epoch 9 — 20260823-110952](#epoch-9--20260823110952)
- [Epoch 10 — 20260823-121514](#epoch-10--20260823121514)
- [Epoch 11 — 20260823-164300](#epoch-11--20260823164300)
- [Epoch 12 — 20260824-175241](#epoch-12--20260824175241)
- [Epoch 13 — 20260824-225834](#epoch-13--20260824225834)

---

# Epoch 1 — `20260822-024521`

Started 2026-08-22 02:45 EDT · 4 cells

## 4 · Changes since the previous epoch

264 commit(s).

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


## Task `retry-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/backoff.ts must export backoffDelays(attempts, baseMs) returning the delay before each retry as an array of length attempts - 1, doubling each time (base, base*2, base*4, ...). src/client.ts must export callWithRetry(fn, attempts, baseMs) which awaits fn(), returns its value on success, and on a thrown error retries using that schedule, re-throwing the last error when every attempt fails. Record each delay it waited in the exported array usedDelays so a caller can audit it. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.1 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 7.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**FAIL** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**FAIL** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 2 — `20260822-044746`

Started 2026-08-22 04:47 EDT · 2 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `7f0520944` | bench: measure the tree a timed-out cell left, and widen the served slot | — |


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 7.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 18.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 3 — `20260822-052306`

Started 2026-08-22 05:23 EDT · 5 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `f3f19d993` | bench: give every cell a directory that starts from nothing | — |


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.4 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**FAIL** · 2.8 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 10.4 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 4 — `20260822-062146`

Started 2026-08-22 06:21 EDT · 10 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `84fdb2453` | bench: an arm denied a file in its own tree is the harness failing | — |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**FAIL** · 34.9 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**FAIL** · 8.2 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 17.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 22.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**FAIL** · 86.8 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 21.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 5 — `20260822-154753`

Started 2026-08-22 15:47 EDT · 2 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `b465651fd` | bench: measure a cell on the clock its budget uses, and hold sleep off | — |


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.9 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**FAIL** · 3.2 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 6 — `20260822-160012`

Started 2026-08-22 16:00 EDT · 12 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `d536a306a` | bench: a refusal outside the arm's tree is the arm's dead end, not ours | — |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.9 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 9.2 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 6.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.1 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 17.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 2.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 7 — `20260822-204552`

Started 2026-08-22 20:45 EDT · 12 cells

## 4 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `5ae68744c` | bench: keep the observer's per-turn view of a conductor run | — |
| `91b1828fe` | bench: keep the granular state, and check a run for defects already fixed | D06, D22, D23, D24 |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.2 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 9.1 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 7.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 17.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.6 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 13.6 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 2.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 17.1 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 8 — `20260823-012116`

Started 2026-08-23 01:21 EDT · 3 cells

## 4 · Changes since the previous epoch

1 commit(s).

| commit | what changed | defect |
|---|---|---|
| `6a5a4c054` | conductor: name the next action and the next legal move, and vet trivial once | D13, D26, D27, D28, D29 |


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 2.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 8.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 9 — `20260823-110952`

Started 2026-08-23 11:09 EDT · 5 cells

## 4 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `be8c44900` | conductor: the out-of-tree refusal names the spelling the check accepts | D13, D30 |
| `76d323f74` | docs: withdraw D25 — the cluster guard is correct and already documented | D25, D29 |


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 12.2 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.1 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 10 — `20260823-121514`

Started 2026-08-23 12:15 EDT · 12 cells

## 4 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `4b0a9224b` | docs: record the preservation-by-restatement shape in the cluster residuals | D31 |
| `ca9c8576f` | conductor: never tell a session to call a tool its role may not call | D15, D32 |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**FAIL** · 33.8 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.9 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 12.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 1.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 5.9 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 11 — `20260823-164300`

Started 2026-08-23 16:43 EDT · 12 cells

## 4 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `6363cd7b5` | conductor: the receipt records the recommendation the block delivered | D32 |
| `6f18ce6c5` | conductor: the decompose brief names the files a decomposition may scope | D16, D29, D34 |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 19.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 8.7 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 22.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 2.1 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 10.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 12 — `20260824-175241`

Started 2026-08-24 17:52 EDT · 12 cells

## 4 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `5186c04ed` | observe: tell a recorded "none" recommendation from an unrecorded one | D26, D32, D34, D35 |
| `914b94f21` | conductor: the decompose brief carries the code, not a list of its filenames | D34, D35, D36 |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.3 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 12.4 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 7.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 13.6 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.6 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 15.5 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 7.8 min · hidden tests: pass

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 2 · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._


---

# Epoch 13 — `20260824-225834`

Started 2026-08-24 22:58 EDT · 12 cells

## 4 · Changes since the previous epoch

4 commit(s).

| commit | what changed | defect |
|---|---|---|
| `914b94f21` | conductor: the decompose brief carries the code, not a list of its filenames | D34, D35, D36 |
| `d745cc2d9` | planning: read "X remains X" as preservation, not a second cluster | D31 |
| `948f1a883` | gen_tokens: measure what a cell EMITS, not what it was sent | D38, D39 |
| `b9bdb7461` | doctrine: say what the placeholder and decisions checks actually do | D38 |


## Task `clock-inject-py`  (T4)

### 1 · The prompt, as it was fed this epoch

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:\n- set_now(seconds) pins the instant every reader sees.\n- reset_now() hands the clock back to the real one.\n- now() returns the pinned instant while one is set, and the real time otherwise.\nAfter set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.9 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash | 0.8 min | 68 | 7,647 |
| turn 2 → read, read, read, read, read, read, read, read | 0.6 min | 520 | 374 |
| turn 3 → edit | 1.4 min | 1,175 | 1,552 |
| turn 4 → write | 0.5 min | 466 | 20 |
| turn 5 → bash | 0.1 min | 104 | 21 |
| turn 6 → (no tool call) | 0.3 min | 270 | 154 |
| **total (6 turns)** | **3.8 min** | **2,603** | |

#### 2 · The resulting code

`src/clock.py` (modified)

```python
"""The one place this package reads the wall clock."""

import time

_pinned = None


def now():
    if _pinned is not None:
        return _pinned
    return time.time()


def set_now(seconds):
    global _pinned
    _pinned = seconds


def reset_now():
    global _pinned
    _pinned = None
```

`tests/check_pinned.py` (created)

```python
import unittest

from src import clock
from src.expiry import TTL_SECONDS, is_expired
from src.session import age_of, open_session
from src.summary import summarize


class PinnedClockTests(unittest.TestCase):
    def tearDown(self):
        clock.reset_now()

    def test_every_reader_sees_the_pinned_instant(self):
        clock.set_now(2000.0)
        self.assertEqual(clock.now(), 2000.0)

        session = open_session("ada")
        self.assertEqual(session["opened_at"], 2000.0)
        self.assertEqual(age_of(session), 0.0)
        self.assertFalse(is_expired(session))
        self.assertEqual(summarize([session]), "1 live of 1")

    def test_pinned_instant_past_the_ttl_expires(self):
        session = {"user": "ada", "opened_at": 100.0}
        clock.set_now(100.0 + TTL_SECONDS + 1)
        self.assertTrue(is_expired(session))
        self.assertEqual(summarize([session]), "0 live of 1")

    def test_reset_now_hands_back_the_wall_clock(self):
        clock.set_now(2000.0)
        clock.reset_now()
        self.assertNotEqual(clock.now(), 2000.0)
        session = open_session("ada")
        self.assertNotEqual(session["opened_at"], 2000.0)


if __name__ == "__main__":
    unittest.main()
```

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 9.0 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash | 1.8 min | 64 | 18,681 |
| turn 2 → read, read, read, read, read, read, read, read | 1.0 min | 526 | 304 |
| turn 3 → bash | 2.1 min | 1,645 | 1,552 |
| turn 4 → write | 2.3 min | 2,071 | 460 |
| turn 5 → bash | 0.2 min | 138 | 21 |
| turn 6 → edit | 0.6 min | 426 | 678 |
| turn 7 → bash | 0.1 min | 53 | 20 |
| turn 8 → bash | 0.4 min | 361 | 222 |
| turn 9 → (no tool call) | 0.5 min | 433 | 212 |
| **total (9 turns)** | **9.0 min** | **5,717** | |

#### 2 · The resulting code

`src/clock.py` (modified)

```python
"""The one place this package reads the wall clock."""

import time

_pinned = None


def now():
    if _pinned is not None:
        return _pinned
    return time.time()


def set_now(seconds):
    """Pin the instant that every reader of the clock sees."""
    global _pinned
    _pinned = seconds


def reset_now():
    """Hand the clock back to the real one."""
    global _pinned
    _pinned = None
```

`tests/check_pinned.py` (created)

```python
import time
import unittest

from src import clock
from src.expiry import TTL_SECONDS, is_expired
from src.session import age_of, open_session
from src.summary import summarize


class PinnedClockTests(unittest.TestCase):
    def setUp(self):
        clock.reset_now()

    def tearDown(self):
        clock.reset_now()

    def test_now_returns_real_time_before_any_pin(self):
        before = time.time()
        value = clock.now()
        after = time.time()
        self.assertGreaterEqual(value, before)
        self.assertLessEqual(value, after)

    def test_set_now_pins_the_instant_every_reader_sees(self):
        clock.set_now(1000.0)
        self.assertEqual(clock.now(), 1000.0)
        session = open_session("ada")
        self.assertEqual(session["opened_at"], 1000.0)
        self.assertEqual(age_of(session), 0.0)

    def test_a_later_set_now_replaces_earlier_pin(self):
        clock.set_now(500.0)
        clock.set_now(600.0)
        self.assertEqual(clock.now(), 600.0)

    def test_expiry_is_decided_at_the_pinned_instant(self):
        session = {"user": "ada", "opened_at": 100.0}
        clock.set_now(100.0 + TTL_SECONDS)
        self.assertTrue(is_expired(session))
        clock.set_now(100.0 + TTL_SECONDS - 1.0)
        self.assertFalse(is_expired(session))

    def test_summary_counts_against_the_pinned_instant(self):
        session = {"user": "ada", "opened_at": 100.0}
        clock.set_now(100.0 + TTL_SECONDS + 1.0)
        self.assertEqual(summarize([session]), "0 live of 1")
        clock.set_now(100.0 + 1.0)
        self.assertEqual(summarize([session]), "1 live of 1")

    def test_reset_now_hands_back_the_real_clock(self):
        clock.set_now(1.0)
        clock.reset_now()
        before = time.time()
        value = clock.now()
        after = time.time()
        self.assertGreaterEqual(value, before)
        self.assertLessEqual(value, after)
        session = open_session("ada")
        self.assertGreaterEqual(session["opened_at"], before)
        self.assertLessEqual(session["opened_at"], after)


if __name__ == "__main__":
    unittest.main()
```

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

Grouped by role. `sessions` counts how many times that role was dispatched — more than one means a re-dispatch after a refusal or a watchdog death. **The times overlap**: sub-sessions run concurrently and the orchestrator's own session is elapsed while it waits on them, so the column sums to more than the cell's wall clock and is a measure of work done, not of time passed.

| phase | sessions | turns | time | tokens out | tokens in |
|---|---:|---:|---:|---:|---:|
| orchestrator (root session) | 1 | 9 | 59.2 min | 2,514 | 22,816 |
| mechanical | 2 | 7 | 17.5 min | 4,949 | 14,725 |
| skeptic | 1 | 6 | 4.9 min | 3,415 | 14,302 |
| planner | 4 | 15 | 32.1 min | 23,847 | 34,741 |
| **sum of phases** | 8 | 37 | 113.7 min | **34,725** | |

_Cell wall clock: **60.0 min**._

#### 2 · The resulting code

**Unchanged from the seed — this arm produced no code.**


## Task `euler-cli-py`  (T1)

### 1 · The prompt, as it was fed this epoch

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 5.9 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash | 0.8 min | 64 | 7,683 |
| turn 2 → read, read, read, read, read, read, read, read, read | 0.7 min | 598 | 84 |
| turn 3 → write | 3.4 min | 2,933 | 1,778 |
| turn 4 → bash, bash | 0.2 min | 201 | 21 |
| turn 5 → bash | 0.4 min | 377 | 277 |
| turn 6 → (no tool call) | 0.3 min | 308 | 75 |
| **total (6 turns)** | **5.9 min** | **4,481** | |

#### 2 · The resulting code

`src/cli.py` (modified)

```python
"""The command line over the solver registry."""

import sys
import time

import src.solvers  # noqa: F401  importing registers every solver
from src import registry

USAGE = "usage: euler list | run <NAME|all>"


def _run_one(name):
    solve = registry.get(name)
    start = time.perf_counter()
    answer = solve()
    elapsed_ms = round((time.perf_counter() - start) * 1000)
    print("%s %s %dms" % (name, answer, elapsed_ms))


def main(argv):
    if not argv:
        print(USAGE)
        return 2
    command, rest = argv[0], argv[1:]
    if command == "list":
        for name in registry.names():
            print(name)
        return 0
    if command == "run":
        if not rest:
            print(USAGE)
            return 2
        target = rest[0]
        if target == "all":
            for name in registry.names():
                _run_one(name)
            return 0
        try:
            _run_one(target)
        except KeyError:
            print("unknown solver: %s" % target)
            return 2
        return 0
    print("unknown command: %s" % command)
    print(USAGE)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 18.9 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → read | 1.9 min | 80 | 18,717 |
| turn 2 → read, read, read | 0.5 min | 195 | 691 |
| turn 3 → read, read, read, read | 0.4 min | 276 | 236 |
| turn 4 → read, read, read | 0.4 min | 215 | 1,431 |
| turn 5 → read, read, read, read | 0.4 min | 275 | 245 |
| turn 6 → read, bash | 4.4 min | 3,712 | 967 |
| turn 7 → write | 1.4 min | 1,223 | 139 |
| turn 8 → edit | 0.2 min | 202 | 21 |
| turn 9 → bash | 0.1 min | 71 | 20 |
| turn 10 → write | 0.8 min | 572 | 1,086 |
| turn 11 → edit | 0.8 min | 668 | 21 |
| turn 12 → write | 3.9 min | 3,379 | 20 |
| turn 13 → read | 0.2 min | 171 | 21 |
| turn 14 → edit | 0.3 min | 136 | 1,312 |
| turn 15 → bash | 0.1 min | 71 | 20 |
| turn 16 → read | 0.5 min | 271 | 1,110 |
| turn 17 → edit | 0.4 min | 272 | 555 |
| turn 18 → bash | 0.3 min | 212 | 20 |
| turn 19 → bash, bash | 0.4 min | 298 | 252 |
| turn 20 → bash | 0.3 min | 261 | 117 |
| turn 21 → (no tool call) | 1.1 min | 909 | 58 |
| **total (21 turns)** | **18.9 min** | **13,469** | |

#### 2 · The resulting code

`src/cli.py` (modified)

```python
"""The command line over the solver registry."""

import sys
import time

import src.solvers  # noqa: F401  # importing src.cli registers every solver
from src.registry import get, names

USAGE = "usage: euler list | run NAME | run all"


def _run_one(name, solve):
    start = time.perf_counter()
    answer = solve()
    elapsed_ms = round((time.perf_counter() - start) * 1000)
    print("%s %s %dms" % (name, answer, elapsed_ms))


def main(argv):
    if not argv:
        print(USAGE)
        return 2
    command = argv[0]
    if command == "list":
        for name in names():
            print(name)
        return 0
    if command == "run":
        if len(argv) < 2:
            print(USAGE)
            return 2
        name = argv[1]
        if name == "all":
            for registered in names():
                _run_one(registered, get(registered))
            return 0
        try:
            solve = get(name)
        except KeyError:
            print("unknown solver: %s" % name)
            return 2
        _run_one(name, solve)
        return 0
    print("unknown command: %s" % command)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

`tests/check_cli.py` (created)

```python
import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout

import src.cli
from src.registry import names


def run_cli(*argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = src.cli.main(list(argv))
    return buf.getvalue(), code


class ListCommandTests(unittest.TestCase):
    def test_every_registered_name_one_per_line_sorted(self):
        out, code = run_cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), sorted(names()))
        self.assertEqual(out, "p001\np002\n")

    def test_one_name_per_line(self):
        out, code = run_cli("list")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), len(names()))
        for line in lines:
            self.assertNotIn(" ", line)


class RunCommandTests(unittest.TestCase):
    def test_run_single_solver_line_format(self):
        out, code = run_cli("run", "p001")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^p001 233168 \d+ms$")

    def test_run_second_solver_line_format(self):
        out, code = run_cli("run", "p002")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1)
        self.assertRegex(lines[0], r"^p002 4613732 \d+ms$")

    def test_run_all_one_line_per_solver_sorted(self):
        out, code = run_cli("run", "all")
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(len(lines), len(names()))
        printed = [line.split(" ")[0] for line in lines]
        self.assertEqual(printed, sorted(names()))
        self.assertRegex(lines[0], r"^p001 233168 \d+ms$")
        self.assertRegex(lines[1], r"^p002 4613732 \d+ms$")

    def test_run_all_lines_share_single_solver_format(self):
        out, code = run_cli("run", "all")
        self.assertEqual(code, 0)
        for line in out.splitlines():
            self.assertRegex(line, r"^p\d+ \d+ \d+ms$")


class ErrorHandlingTests(unittest.TestCase):
    def test_unknown_solver_names_it_and_returns_2(self):
        out, code = run_cli("run", "nope")
        self.assertEqual(code, 2)
        self.assertIn("nope", out)

    def test_no_arguments_returns_2(self):
        out, code = run_cli()
        self.assertEqual(code, 2)

    def test_unknown_command_returns_2(self):
        out, code = run_cli("frobnicate")
        self.assertEqual(code, 2)

    def test_run_without_a_name_returns_2(self):
        out, code = run_cli("run")
        self.assertEqual(code, 2)


class ImportContractTests(unittest.TestCase):
    def test_importing_cli_alone_registers_every_solver(self):
        # Fresh interpreter: importing src.cli (and nothing else from src)
        # must leave every solver registered.
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proc = subprocess.run(
            [sys.executable, "-c",
             "import src.cli; from src.registry import names; print(names())"],
            capture_output=True, text=True, cwd=repo,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, "['p001', 'p002']\n")


if __name__ == "__main__":
    unittest.main()
```

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 45.0 min · hidden tests: fail

#### 3 · Cost by phase

Grouped by role. `sessions` counts how many times that role was dispatched — more than one means a re-dispatch after a refusal or a watchdog death. **The times overlap**: sub-sessions run concurrently and the orchestrator's own session is elapsed while it waits on them, so the column sums to more than the cell's wall clock and is a measure of work done, not of time passed.

| phase | sessions | turns | time | tokens out | tokens in |
|---|---:|---:|---:|---:|---:|
| orchestrator (root session) | 1 | 5 | 35.3 min | 485 | 11,987 |
| mechanical | 2 | 6 | 4.0 min | 1,506 | 25,813 |
| skeptic | 2 | 8 | 17.0 min | 1,707 | 26,236 |
| planner | 4 | 9 | 16.8 min | 13,559 | 20,642 |
| **sum of phases** | 9 | 28 | 73.2 min | **17,257** | |

_Cell wall clock: **45.0 min**._

#### 2 · The resulting code

**Unchanged from the seed — this arm produced no code.**


## Task `logfmt-lenses-ts`  (T2)

### 1 · The prompt, as it was fed this epoch

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:\n- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.\n- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.\n- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.\n- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.\nEvery lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.7 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash | 0.8 min | 70 | 7,743 |
| turn 2 → read, read, read, read, read | 0.4 min | 333 | 51 |
| turn 3 → bash | 1.7 min | 1,440 | 1,317 |
| turn 4 → write, write, write, write | 0.9 min | 788 | 748 |
| turn 5 → bash, bash | 0.4 min | 373 | 51 |
| turn 6 → (no tool call) | 0.4 min | 347 | 270 |
| **total (6 turns)** | **4.7 min** | **3,351** | |

#### 2 · The resulting code

`src/lenses/by-status.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  const counts = new Map<number, number>();
  for (const r of records) counts.set(r.status, (counts.get(r.status) ?? 0) + 1);
  return [...counts.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([status, count]) => `${status} ${count}`);
}
```

`src/lenses/errors.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  return records
    .filter((r) => r.level === "error")
    .sort((a, b) => a.at - b.at)
    .map((r) => `${r.at} ${r.route} ${r.status}`);
}
```

`src/lenses/latency.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  const n = records.length;
  if (n === 0) return ["count 0", "mean 0", "max 0"];
  let sum = 0;
  let max = records[0].ms;
  for (const r of records) {
    sum += r.ms;
    if (r.ms > max) max = r.ms;
  }
  return [`count ${n}`, `mean ${Math.round(sum / n)}`, `max ${max}`];
}
```

`src/lenses/slowest.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  return [...records]
    .sort((a, b) => b.ms - a.ms)
    .slice(0, 3)
    .map((r) => `${r.route} ${r.ms}`);
}
```

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 13.7 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash, glob | 2.0 min | 136 | 18,777 |
| turn 2 → read, read, read, read, read | 0.6 min | 338 | 219 |
| turn 3 → bash, bash | 5.2 min | 4,497 | 1,317 |
| turn 4 → write | 3.1 min | 2,798 | 149 |
| turn 5 → bash | 0.1 min | 115 | 21 |
| turn 6 → write, write, write, write | 1.0 min | 790 | 561 |
| turn 7 → bash | 0.4 min | 299 | 51 |
| turn 8 → bash, grep | 0.3 min | 255 | 377 |
| turn 9 → (no tool call) | 1.0 min | 832 | 364 |
| **total (9 turns)** | **13.7 min** | **10,060** | |

#### 2 · The resulting code

`src/lenses/by-status.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  const counts = new Map<number, number>();
  for (const r of records) counts.set(r.status, (counts.get(r.status) ?? 0) + 1);
  return [...counts.keys()].sort((a, b) => a - b).map((s) => `${s} ${counts.get(s)}`);
}
```

`src/lenses/errors.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  return records
    .filter((r) => r.level === "error")
    .sort((a, b) => a.at - b.at)
    .map((r) => `${r.at} ${r.route} ${r.status}`);
}
```

`src/lenses/latency.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  const n = records.length;
  if (n === 0) return ["count 0", "mean 0", "max 0"];
  let total = 0;
  let max = -Infinity;
  for (const r of records) {
    total += r.ms;
    if (r.ms > max) max = r.ms;
  }
  return [`count ${n}`, `mean ${Math.round(total / n)}`, `max ${max}`];
}
```

`src/lenses/slowest.ts` (created)

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  return [...records]
    .sort((a, b) => b.ms - a.ms)
    .slice(0, 3)
    .map((r) => `${r.route} ${r.ms}`);
}
```

`tests/lenses.test.ts` (created)

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import type { LogRecord } from "../src/record.ts";
import { apply as errors } from "../src/lenses/errors.ts";
import { apply as latency } from "../src/lenses/latency.ts";
import { apply as byStatus } from "../src/lenses/by-status.ts";
import { apply as slowest } from "../src/lenses/slowest.ts";

function rec(at: number, level: string, route: string, status: number, ms: number): LogRecord {
  return { at, level, route, status, ms };
}

test("the errors lens lists error records oldest first, formatted at route status", () => {
  const records = [
    rec(3, "info", "/c", 200, 5),
    rec(2, "error", "/b", 500, 40),
    rec(9, "error", "/d", 503, 7),
    rec(5, "warn", "/e", 418, 1),
  ];
  assert.deepEqual(errors(records), ["2 /b 500", "9 /d 503"]);
});
test("the errors lens returns [] for an empty set", () => {
  assert.deepEqual(errors([]), []);
});

test("the latency lens reports count, mean and max", () => {
  const records = [
    rec(1, "info", "/a", 200, 10),
    rec(2, "info", "/b", 200, 20),
    rec(3, "info", "/c", 200, 30),
  ];
  assert.deepEqual(latency(records), ["count 3", "mean 20", "max 30"]);
});
test("the latency lens rounds the mean to the nearest whole millisecond", () => {
  const roundsDown = [
    rec(1, "info", "/a", 200, 10),
    rec(2, "info", "/a", 200, 10),
    rec(3, "info", "/a", 200, 11),
  ];
  assert.deepEqual(latency(roundsDown), ["count 3", "mean 10", "max 11"]);
  const roundsUp = [
    rec(1, "info", "/a", 200, 10),
    rec(2, "info", "/a", 200, 11),
    rec(3, "info", "/a", 200, 11),
  ];
  assert.deepEqual(latency(roundsUp), ["count 3", "mean 11", "max 11"]);
});
test("the latency lens on an empty set gives count 0, mean 0, max 0", () => {
  assert.deepEqual(latency([]), ["count 0", "mean 0", "max 0"]);
});

test("the by-status lens counts each status and orders them ascending", () => {
  const records = [
    rec(1, "info", "/a", 404, 1),
    rec(2, "info", "/b", 200, 2),
    rec(3, "error", "/a", 404, 3),
    rec(4, "info", "/c", 200, 4),
    rec(5, "warn", "/d", 200, 5),
  ];
  assert.deepEqual(byStatus(records), ["200 3", "404 2"]);
});
test("the by-status lens returns [] for an empty set", () => {
  assert.deepEqual(byStatus([]), []);
});

test("the slowest lens gives the three slowest records, slowest first", () => {
  const records = [
    rec(1, "info", "/a", 200, 100),
    rec(2, "info", "/b", 200, 300),
    rec(3, "info", "/c", 200, 200),
    rec(4, "info", "/d", 200, 90),
  ];
  assert.deepEqual(slowest(records), ["/b 300", "/c 200", "/a 100"]);
});
test("the slowest lens gives fewer lines for fewer than three records", () => {
  assert.deepEqual(slowest([rec(1, "info", "/a", 200, 5)]), ["/a 5"]);
});
test("the slowest lens returns [] for an empty set", () => {
  assert.deepEqual(slowest([]), []);
});
```

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 60.0 min · hidden tests: fail

#### 3 · Cost by phase

Grouped by role. `sessions` counts how many times that role was dispatched — more than one means a re-dispatch after a refusal or a watchdog death. **The times overlap**: sub-sessions run concurrently and the orchestrator's own session is elapsed while it waits on them, so the column sums to more than the cell's wall clock and is a measure of work done, not of time passed.

| phase | sessions | turns | time | tokens out | tokens in |
|---|---:|---:|---:|---:|---:|
| orchestrator (root session) | 1 | 11 | 50.3 min | 2,054 | 24,701 |
| mechanical | 1 | 3 | 2.1 min | 819 | 13,058 |
| skeptic | 1 | 3 | 1.8 min | 596 | 12,915 |
| planner | 5 | 15 | 47.6 min | 16,615 | 40,717 |
| **sum of phases** | 8 | 32 | 101.9 min | **20,084** | |

_Cell wall clock: **60.0 min**._

#### 2 · The resulting code

**Unchanged from the seed — this arm produced no code.**


## Task `slugify-ts`  (T0)

### 1 · The prompt, as it was fed this epoch

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 1.7 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → read, read | 0.9 min | 138 | 7,565 |
| turn 2 → edit | 0.2 min | 161 | 266 |
| turn 3 → bash | 0.1 min | 53 | 20 |
| turn 4 → bash | 0.1 min | 87 | 22 |
| turn 5 → bash | 0.2 min | 94 | 793 |
| turn 6 → bash | 0.2 min | 213 | 90 |
| turn 7 → (no tool call) | 0.1 min | 91 | 34 |
| **total (7 turns)** | **1.7 min** | **837** | |

#### 2 · The resulting code

`src/slugify.ts` (modified)

```ts
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
```

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 22.9 min · hidden tests: pass

#### 3 · Cost by phase

One flat session, so each row is one model turn and the times are sequential.

| phase | time | tokens out | tokens in |
|---|---:|---:|---:|
| turn 1 → bash, glob | 2.0 min | 251 | 18,599 |
| turn 2 → read, read, read, read | 0.4 min | 265 | 391 |
| turn 3 → todowrite | 5.2 min | 4,505 | 1,169 |
| turn 4 → bash, bash | 0.2 min | 168 | 195 |
| turn 5 → todowrite | 3.2 min | 2,865 | 109 |
| turn 6 → write | 8.6 min | 7,219 | 3,066 |
| turn 7 → bash | 0.1 min | 52 | 21 |
| turn 8 → edit | 0.8 min | 342 | 3,459 |
| turn 9 → bash | 0.2 min | 174 | 20 |
| turn 10 → bash, bash | 0.3 min | 185 | 322 |
| turn 11 → bash | 0.3 min | 196 | 479 |
| turn 12 → bash, read | 0.3 min | 217 | 339 |
| turn 13 → todowrite | 0.6 min | 476 | 308 |
| turn 14 → (no tool call) | 0.8 min | 632 | 194 |
| **total (14 turns)** | **22.9 min** | **17,547** | |

#### 2 · The resulting code

`src/slugify.ts` (modified)

```ts
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^\p{L}\p{Nd}]+/gu, "-")
    .replace(/^-+|-+$/g, "");
}
```

`tests/slugify.test.ts` (created)

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "../src/slugify.ts";

test("lowercases the whole title", () => {
  assert.equal(slugify("Hello World"), "hello-world");
});

test("replaces a run of non-letters/digits with a single '-'", () => {
  assert.equal(slugify("Hello,   World!"), "hello-world");
});

test("collapses a run of dashes to a single '-'", () => {
  assert.equal(slugify("Hello----World"), "hello-world");
});

test("keeps an existing single separator as a single '-'", () => {
  assert.equal(slugify("Hello-World"), "hello-world");
});

test("removes leading '-' introduced by leading non-alphanumerics", () => {
  assert.equal(slugify("!!!hello"), "hello");
});

test("removes trailing '-' introduced by trailing non-alphanumerics", () => {
  assert.equal(slugify("hello!!!"), "hello");
});

test("removes leading and trailing dashes", () => {
  assert.equal(slugify("---hello---"), "hello");
});

test("keeps letters and digits, collapses everything else between them", () => {
  assert.equal(slugify("Hello 123 World"), "hello-123-world");
});

test("keeps unicode letters", () => {
  assert.equal(slugify("héllo wörld"), "héllo-wörld");
});

test("keeps unicode digits", () => {
  assert.equal(slugify("num ١٢٣ end"), "num-١٢٣-end");
});

test("all-non-alphanumeric input slugifies to empty string", () => {
  assert.equal(slugify("!!!"), "");
});

test("empty input slugifies to empty string", () => {
  assert.equal(slugify(""), "");
});
```

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3 · Cost by phase

Grouped by role. `sessions` counts how many times that role was dispatched — more than one means a re-dispatch after a refusal or a watchdog death. **The times overlap**: sub-sessions run concurrently and the orchestrator's own session is elapsed while it waits on them, so the column sums to more than the cell's wall clock and is a measure of work done, not of time passed.

| phase | sessions | turns | time | tokens out | tokens in |
|---|---:|---:|---:|---:|---:|
| orchestrator (root session) | 1 | 7 | 29.2 min | 2,288 | 13,322 |
| mechanical | 2 | 7 | 8.0 min | 5,277 | 25,537 |
| skeptic | 2 | 4 | 17.4 min | 1,404 | 24,314 |
| **sum of phases** | 5 | 18 | 54.6 min | **8,969** | |

_Cell wall clock: **30.0 min**._

#### 2 · The resulting code

**Unchanged from the seed — this arm produced no code.**


# Handoff: land ranks 1, 2, 6, 7 and re-measure — ultracode

Everything you need is in this repository at `/Users/sal/development/vorlac/llama-harness`,
on `main`, clean tree, both gates green (`GATE PASS`, `M5 PASS`). The code state this
handoff describes is `6cad7ca` (the four commits `bb93ff5..6cad7ca`); HEAD additionally
carries this handoff document and nothing else.

## Context in one paragraph

Epoch 22 proved the conductor's plan and plan-review stages terminate (D48/D49) and then
died in the executor on a `question`-tool stall (D50 and D51 fixed at `3ad9d02`, D52 at
`bb93ff5`, all in the tree as of `6cad7ca`, the register commit). A 44-agent
adversarial review over the epoch-21/22 evidence produced a ranked change set:
**`docs/plans/2026-08-28-improve-cycle-synthesis.md`** — treat each rank's entry there as
the spec (sites, refutations already paid for, measurement tiers); this handoff only adds
the ordering and the decisions already made. The register is
`docs/build/artifacts/14.2-arm-campaign.md` — read D48–D52 before touching anything.

## The work, in order

Ranks 6 → 7 → 2 → 1, then gate → commit → the three-arm run. Work each rank as its own
workflow phase: implement → red-green test (verified by stashing the source change) →
mechanism criterion met → next. Do not start the run until all four are committed.

### 1. Rank 6 — window the console ledger join (first: it is the instrument every later step reads)

Spec: synthesis "Rank 6". Decisions already made: window the ledger by the run's own
journal first/last timestamps (never `ledgerStartLine` — it does not exist during a live
run), with the upper bound inclusive at second granularity or padded by a ~60 s grace —
a request in flight when the final journal record lands completes after it, and c828's
last ledger row (testWriter, 511 completion tokens) completes at 09:01:54.360Z, 139 ms
past the journal's last timestamp; a strict window loses exactly those 511 tokens and
fails the acceptance figure below. The `group` filter drops 12 of the 46 conductor rows (all 8 reviewer rows carry
`group=null`) — repair it or drop it, decided from the data; totals are a direct sum over
the windowed rows; a null-token row renders as unknown, never as zero.

Verify offline, seconds, zero model calls: against the archived run
`.data/benchmark/watch/step8-context-128k/run-r-20260828-c828/` (journal, console log,
plan, queue; the router ledger is global at `.data/router/metrics.jsonl` — window it, do
not copy it), `node conductor/tools/observe.ts <that dir> --console` must report
**82,865 completion tokens** with per-role sums orchestrator 7,089 / mechanical 455 /
skeptic 1,315 / planner 34,178 / reviewer 23,939 / testWriter 15,889. Use `--console`,
not `--json` (no token totals there). Add a regression fixture pinning that a prior
run's rows under the same group path cannot contribute to a run's totals. Do NOT claim
mismatch/compaction/turn-count improvements: mismatch and compaction are computed before
the join, and the 29-vs-46 turn count is `scripts/run_and_watch.py`'s own display trim
(the console already renders 46) — all three are causally impossible to move from this
site (the synthesis records each).

### 2. Rank 7 — ledger stall detector (the run's watchdog, outside the plugin)

Spec: synthesis "Rank 7". Decisions already made: it lives in the watcher
(`scripts/run_and_watch.py`), keyed off the ledger's last `completedAt` plus the journal's
last timestamp; threshold **45 minutes** (sized above the measured healthy maxima: a
26.9-minute single generation and a 30.0-minute inter-event gap on lenses that then
SUCCEEDED); on fire it alarms loudly — console line plus a sentinel file in the run dir —
and aborts nothing itself; the watching session applies snapshot → kill → record.

Verify offline: replayed over the c828 ledger window and journal, with the 45-minute
threshold it must fire at the first poll after 09:46:54Z (last completed request
09:01:54.360Z + 45 min) and never before that instant; replayed over `.data/benchmark/watch/step6-grid2048-8h`
(480 minutes at 99.2% request-busy) and the healthy portions of the other conductor
journals on disk it must fire zero times. Do NOT shorten `SUB_SESSION_TIMEOUT_MS`, and
never make any silence deadline terminal (synthesis doNot list — a 20-minute deadline
kills ~1 in 10 healthy dispatches and would have destroyed the two retries that completed
the c828 review wave).

### 3. Rank 2 — stable orchestrator prefix (the biggest free prefill saving)

Spec: synthesis "Rank 2" — the state block's `Run state:` / `Next action:` lines change at
every FSM phase boundary and ride in the SYSTEM prompt, and the hybrid-cache model cannot
rewind, so each transition costs a total re-prefill (three confirmed cold turns, 734 s of
prefill for 281 output tokens). Decision on the §6.4 tension: the block keeps its
re-stated-every-request semantics — the doctrine packs stay in the system append; ONLY the
volatile fields (`Run state`, `Next action`, counts) move to the tail of the composed user
message, prefixed with one line stating it supersedes every earlier state block. If making
the prefix byte-stable requires moving more than the volatile subset, stop and surface
instead of moving the packs.

Verify: (a) node test — the composed `output.system` array is byte-identical across two
GateRun states differing only in `run.state`/`recommended`; (b) live probe, ~10 min, one
server start: drive two ~30k-token requests through the router that differ only in the
volatile state fields; before the fix that difference lives in the system prefix and the
second request's `timings.cache_n` in `.data/router/metrics.jsonl` is 0; after, the prefix
is byte-stable and `cache_n` must be previous-total-minus-1. If a phase-boundary turn
still shows `cache_n = 0` after the fix, suspect a second prefix source (most likely a
per-phase change in the offered tool set) and record it rather than forcing the criterion.

### 4. Rank 1 — per-role reasoning budgets (the ~48% conductor-decode cut)

Spec: synthesis "Rank 1" — the per-REQUEST body path only: `reasoning_budget_tokens`
(alias `thinking_budget_tokens`) and `reasoning_budget_message` land as top-level provider
body fields via `output.options` in the chat.params hook (the wire-notes:27 verified
passthrough; the seam is `conductor/plugin/index.ts` where temperature/topP are already
written, driven by a table beside `ROLE_TEMPERATURE` in `conductor/adapter/inject.ts`).
The server-wide `--reasoning-budget` flag is REFUTED (arm confound — one server serves all
three arms); do not touch `scripts/serve.py` for this.

Decisions already made: budget reviewer, testWriter, orchestrator, skeptic and mechanical;
**the planner stays unbudgeted (-1) this iteration** — it is 88.9% reasoning and 41% of
conductor decode, but it is the one role where deliberation may be load-bearing, and that
quality trade needs a scored cell to judge against; escalate it, do not decide it. Before
fixing the number, measure each budgeted role's per-turn reasoning distribution from the
c828 data (opencode.db / the archived artifacts): start from 3,072 and raise any role
whose healthy p95 exceeds it to p95-plus-margin — a budget fitted below observed healthy
thinking is a new defect, not a saving. The budget message matters: it must force the
model out of the thinking channel with the reply still to write (e.g. "Budget spent. Emit
the reply now."), not truncate mid-thought.

Verify: (a) wire test — `paramsForRole` returns the budget for a budgeted role and the
chat.params hook writes it into `output.options` (model it on the existing x_conductor
params pin in `conductor/tests/wire-contract.test.ts`); (b) the paired lens replay
(synthesis measurement (b)): rebuild the four c828 lens briefs from `lensPrompt` over the
archived `plan.md` + `queue.json`, replay each ONE AT A TIME (never concurrently — a
concurrent control is uncomputable under the 1,800 s provider timeout) at budget -1 and at
the fitted budget, judge on the SUMMED `timings.predicted_n` across all four (per-brief
deltas measured +64% to -75% on the real c828 messages — one brief alone would refute a
hypothesis that is true in aggregate). CONFIRMED if the sum falls >40% AND all four replies still
validate against the Findings schema; REFUTED if the sum falls <25% or any reply that
validated at -1 stops validating. Also assert the reply's reasoning part ends on the
forced message — otherwise a null result is indistinguishable from a budget that never
armed (the budget arms only when the chat template reports reasoning support; c828's own
server.log line "chat template supports preserving reasoning" shows it armed for this
model).

### 5. Gate, commit, then the run

- Quiet machine (no servers, no cells), then `bash scripts/test-conductor.sh` must print
  `GATE PASS` and `bash scripts/conductor-gate.sh` must print `M5 PASS`.
- Commit in finding-sized pieces in the register voice (see `git log --oneline -8` for the
  convention). Do not push.
- The run: edit ONLY the CONFIG block of `scripts/run_and_watch.py` — set `RESULTS_DIR`
  to a NEW empty directory (`.data/benchmark/watch/step9-<name>`). Nothing from step8 is
  reusable: its flat-arm cells ran under the stale router config D52 replaced, so the
  served-config fingerprint changed and every prior cell is void for comparison. Launch
  with NO arguments. All three arms, `grid2048-headless-py`.
- Watch through the rank-7 detector plus `observe --console` (trustworthy once rank 6 is
  in). On a detector fire: snapshot the run dir, kill, record the stall with its journal
  tail — never silently retry, never edit `conductor/`, `bench/` or `scripts/` while
  cells are in flight, never edit `conductor/doctrine/*.md` between cells you will
  compare.
- This run is a MECHANISM verdict at n=1, pre-registered in the register BEFORE launch:
  (i) the conductor arm produces a scored cell at all — it never has on this task;
  (ii) zero post-first-turn orchestrator `cache_n = 0` ledger rows (rank 2);
  (iii) no budgeted role's per-turn reasoning exceeds its fitted budget — judged from the
  run's windowed ledger rows / per-turn message data, never from role totals, because
  total conductor decode is EXPECTED to rise now that D50 lets the run progress further;
  (iv) zero `gates/allow` records for `question` (D50);
  (v) zero sub-session records pairing reason `schema-invalid` with an empty response
  (D51); (vi) zero 502 reviewer rows (D52). Report wall/tokens labeled n=1 — no arm-ratio
  claims (measured baseline wall CV is 23.6–34%, so n=1 detects nothing).
- Register the outcomes in `docs/build/artifacts/14.2-arm-campaign.md`, refuted
  expectations included — the refutations have been worth more than the proposals.

## Traps this repository has already paid for

The full fourteen are the synthesis doc's "Do not" list; these are the ones this handoff
touches directly:

- **`scripts/run_and_watch.py` parses NO argv.** `--help` launches a real campaign. Read
  the CONFIG block; edit constants only between runs.
- **A cell loads the plugin from the live working tree by absolute path.** A mid-run edit
  rewrites the experiment retroactively and nothing records that it did.
- **The gate and `scripts/judge_quality.py` need a quiet machine.** Serialize
  gate → run → analyze; the gate boots its own `opencode serve` and times out under
  contention, which reads as a fake regression.
- **A results dir containing a cell JSON is a resume ledger.** Never copy one in;
  `RESULTS_DIR` must be new and empty (an earlier epoch rendered one measurement as four
  independent PASS rows).
- **Never restore a mutated file with `git checkout`** while uncommitted work exists —
  undo with the inverse edit. (The tree at `6cad7ca` is clean, so this bites only after
  you start editing.)
- **Never read `.data/router/metrics.jsonl` unwindowed or join it on `group`** — rank 6
  exists because that exact join reported a prior day's decode as a live run's total.
- **Every change ships red-green**: a test that fails without it, proven by stashing the
  source change and running the test.
- **`python3 scripts/prior_art.py <mechanism>`** before recording anything as a new
  defect — search by mechanism, not symptom.
- **`scripts/arm_report.py` defaults to `bench/conductor-tasks.json`, which has no
  grid2048-headless-py** — on the step9 results dir it renders an empty report instead of
  an error; always pass `--manifest bench/corpus-games.json`.
- **Throttle fan-out**: prefer serial workflow phases with line-ranged reads; wide
  fan-outs have drained a 5-hour window in minutes on this machine.

## Success

- Ranks 6, 7, 2 and 1 landed, each with its mechanism criterion met and its red-green
  test, committed (the planner budget explicitly NOT landed — that escalation is part of
  success, not a gap in it).
- `GATE PASS` and `M5 PASS` on the committed tree.
- A step9 run in which all three arms terminated, or a stall snapshotted and recorded
  with its cause — either outcome registered with the pre-registered expectations beside
  the measured results.

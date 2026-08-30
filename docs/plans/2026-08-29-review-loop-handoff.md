# Handoff: the review loop is 71.8% of the conductor arm — measure it, then cut it — ultracode

You are picking up an autonomous benchmark-and-improve campaign in the repository at
`/Users/sal/development/vorlac/llama-harness`, on branch `main`, HEAD `18ab6ac`, clean tree,
both gates green. Read this whole document before touching anything. Everything you need is
either in it or named by path inside it.

Run this as an **ultracode workflow**: author and run multi-agent workflows for the
substantive phases, adversarially verify findings before you record them, and prefer serial
phases with line-ranged reads over wide fan-out (this machine has drained a 5-hour API window
in minutes on careless fan-out).

---

## 1. What this repository is, in one paragraph

`llama-leash` benchmarks three arms against the same coding task on a local 27B model
(`qwen3.8-27b`, served by `llama-server` behind a small C++ router at `router/`):

- **baseline** — stock `opencode` `build` agent. No plugin, no doctrine.
- **doctrine** — same agent, all nine `conductor/doctrine/*.md` packs as a static system prompt.
- **conductor** — the `conductor-orchestrator` agent with the TypeScript plugin at
  `conductor/plugin/index.ts` loaded: per-request doctrine injection, 22 extra tools, live
  gates, and a fan-out engine that dispatches sub-sessions (planner, reviewer, testWriter,
  implementer, skeptic, mechanical) through a finite state machine.

The campaign's register — **read this before recording anything** — is
`docs/build/artifacts/14.2-arm-campaign.md`. It is long; read its tail (the `## D53` heading
onward, roughly the last 400 lines) and use `grep` for anything older. Defects are numbered
D1…D56 and the register is written in a specific voice: what was measured, what it refutes,
and what remains unknown. Match that voice.

Two other documents matter: `docs/plans/2026-08-28-improve-cycle-synthesis.md` (a ranked
change set produced by a 44-agent adversarial review, with a "Do not" list of fourteen rules
this campaign has paid for) and `docs/plans/2026-08-28-next-iteration-handoff.md` (the
previous iteration's instructions, now executed).

---

## 2. What just happened — epoch 23, and why it sets your task

Four changes landed and were committed (D53–D56, commits `5107c1c`, `fd74cd8`, `f18e960`,
`7a10ce3`): a windowed console ledger join, a ledger-based stall detector, a byte-stable
orchestrator system prefix, and per-role reasoning budgets delivered as provider-body fields.

Then a three-arm run (`.data/benchmark/watch/step9-prefix-and-budget`, conductor run id
`r-20260828-c8dd`) produced the campaign's best result to date:

| arm | outcome | wall | completion tokens |
|---|---|---:|---:|
| baseline | PASS | 22.1 min | 17,749 |
| doctrine | PASS | 26.5 min | 19,229 |
| conductor | **TIMEOUT** at its 480-min budget | 480.0 min | 320,848 |

The conductor arm **published real work for the first time on this task**. Two of three queue
items walked the full pipeline — `PENDING → RED → TEST_VETTED → GREEN → VALIDATED → REVIEWED
→ PUBLISHED` — producing two commits and 288 insertions across four files, including two new
test files. The counterfactual is exact: epoch 20 ran this same task for the full 480 minutes
and left the tree byte-identical to the seed. The third item, `notes-index`, never started.

**Where the time went, which is your subject.** Per-role decode over the run's windowed
router ledger (214 requests, summing to 320,848 — equal to the cell JSON's own figure to the
token):

| role | requests | completion tokens | share |
|---|---:|---:|---:|
| **reviewer** | **128** | **230,469** | **71.8%** |
| planner | 6 | 38,183 | 11.9% |
| testWriter | 25 | 25,061 | 7.8% |
| implementer | 27 | 15,652 | 4.9% |
| skeptic | 7 | 9,112 | 2.8% |
| orchestrator | 19 | 1,771 | 0.6% |
| mechanical | 2 | 600 | 0.2% |

The reviewer averages **1,801 tokens a turn**, comfortably inside the 3,072-token reasoning
budget that D55 imposed. So per-turn thinking is already bounded; the expense is the **number
of dispatches**. And it is not evenly spread — reviewer dispatches by item:

- `moves-merge`: **24**
- `undo-restore`: **9**
- (no item — plan review): 4

Two comparably-sized items, a 2.7× difference. `moves-merge` cycled: its evidence trail shows
`red` at 01:52, `red` again at 02:31, `red` again at 02:55, `green` at 03:30, `verify` at
03:31, then `green` **and** `red` again at 04:40, `verify` at 05:01, `verify` again at 05:43.
Each item-review round that raises a finding gets fixed; a fix that changes the test sends the
item back through the whole test-vet stage (doctrine §3.3: "a changed test re-enters the test
discipline"), which re-dispatches critics, which can raise more findings.

**This is your target.** Not per-turn cost — round count and fan-out width.

---

## 3. The levers, and where they live

The fan-out widths are **already configuration**, not hardcoded constants. The cell config the
run actually used (read back from
`~/.llama-leash-work/llamacpp-qwen3.8-27b/none/conductor/grid2048-headless-py/r1/repo/.conductor/config.json`):

```json
"workflow": {
  "planReviewers": 4,   "planReviewMaxRounds": 3,
  "itemReviewers": 6,   "reviewMaxRounds": 3,
  "vetCritics": 3,      "vetMaxRounds": 3,
  "skepticsPerFinding": 2,
  "testRepairAttempts": 3, "debugFixCap": 3,
  "maxOverridesPerItem": 1, "maxOverridesPerRun": 2
},
"parallel": { "maxReaders": 6, "maxImplementers": 1, "writes": "off" }
```

Written by `scripts/conductor_bench.py` `build_conductor_cell_config` (defined at line 1915;
the widths are at lines 1948–1953). Consumed via `readFanout` in `conductor/core/schedule.ts`
(line 269), which clamps every stage count to `parallel.maxReaders`. The item-review stage is
in `conductor/adapter/tools.ts` (see the block comment near line 6872 describing
`clamp(readFanout("itemReview"), 3, 6)`); the vet stage is near line 4772; plan review near
line 2969.

That the widths are config matters: a change there is **driver class**, autonomous, and it
cannot invalidate the flat arms, which load no plugin and never read this file.

---

## 4. Your work, in order

### PHASE 1 — Measure the review loop's marginal value. Offline, free, zero model calls. DO THIS FIRST.

Do **not** cut anything before this phase answers its question. The planner role is already
stuck in exactly the trap of a deliberation stage nobody can cheaply evaluate; do not create a
second one. Unlike the planner, the review loop leaves a complete record, so its value is
measurable today from data already on disk.

**Data sources** (all read-only; copy the sqlite file before opening it):

- Journal: `~/.llama-leash-work/llamacpp-qwen3.8-27b/none/conductor/grid2048-headless-py/r1/repo/.conductor/runs/r-20260828-c8dd/journal.jsonl`
  — one JSON object per line, with rotated archives as `journal.N.jsonl.gz` alongside if any.
  Events you will need: `fanout/subsession.dispatched` (carries `role`, `itemId`, `prompt`),
  `fanout/subsession.complete` (carries `response`), `fanout/wave`, `state/item.updated`,
  `state/decision.recorded`, `evidence/*`, `fsm/transition`, `fsm/guard-reject`.
- Message store: `~/.llama-leash-work/llamacpp-qwen3.8-27b/none/conductor/grid2048-headless-py/r1/home/data/opencode/opencode.db`
  — tables `message` and `part`, each with a JSON `data` column. An assistant message's
  `tokens.output` is its decode; its parts split into `reasoning` and `text`. Split output
  across parts by character share when you need a per-part token estimate (this is the method
  the register's earlier entries used; keep it, so the numbers are comparable).
- Router ledger: `.data/router/metrics.jsonl` — **append-only and GLOBAL across every run this
  machine has ever served.** You must window it by the run's own journal first/last timestamp
  plus a ~60 s tail grace, and you must not join it on `group` (that field is the work-root
  path, byte-identical across runs of a task; 12 of 46 rows in a comparable window carried
  `group=null`, including every reviewer row). `conductor/tools/observation.ts` now does this
  correctly — read `windowLedger` and `joinLedger` there rather than reinventing it.
- The finished work tree, for the diffs the reviews were judging:
  `~/.llama-leash-work/llamacpp-qwen3.8-27b/none/conductor/grid2048-headless-py/r1/repo`
  (`git log` shows the seed commit plus the two the conductor published).

**The questions to answer, in priority order:**

1. **Did the later item-review rounds earn their cost?** For `moves-merge`, reconstruct each
   review round: which lenses were dispatched, what findings each raised (severity, claim,
   evidence), which survived the skeptic pass, and which produced an actual code or test
   change. Then classify each round: did it find a *real* defect, a duplicate of an earlier
   round's finding, a nit, or a problem that the previous round's own fix introduced?
2. **What is the marginal yield per lens?** With six item-review lenses running, how many
   distinct surviving findings came from lenses 5 and 6 that lenses 1–4 did not also raise?
   Same question for the three vet critics. If the marginal lens contributes nothing distinct,
   width is the lever; if every lens contributes, width is not.
3. **What drove the re-vet cycles?** Doctrine §3.3 sends a changed test back through test-vet.
   For each re-vet on `moves-merge`, how much did the test actually change — a behavioural
   change, or a rename/comment/formatting change? A cosmetic diff re-running three critics is
   pure waste and is a different fix from a round cap.
4. **Why was `undo-restore` cheap?** It took 9 dispatches to `moves-merge`'s 24 and published
   just the same. Whatever differed is the shape you want more of.
5. **Would a round cap have freed the third item?** `notes-index` never started. Estimate,
   from the measured per-round costs, how much wall clock each candidate cut would have
   returned, and whether that is plausibly the ~3.5 hours an item appears to need.

**Adversarially verify before you record.** For every claim of the form "round N found
nothing new", have an independent agent try to refute it from the same artifacts, and default
to keeping the round when undecided. A finding that a review stage is worthless is exactly the
kind of conclusion that is cheap to assert and expensive to be wrong about.

**Deliverable:** a written analysis with the per-round table, the marginal-yield numbers, and
a ranked recommendation naming which lever to pull and what it is predicted to save — with a
falsifier for each prediction. A recommendation with no falsifier is not runnable; that rule
killed five of eleven candidates in the last review.

### PHASE 2 — Land the change Phase 1 justifies

Whatever Phase 1 recommends, implement it as ONE change with a test that is **red before and
green after**, proven by stashing the source change and watching the test fail. That rule
alone would have killed three refuted candidates in the last cycle. Likely candidates, in
increasing blast radius:

- **Round cap** — lower `reviewMaxRounds` / `vetMaxRounds`, or make the cap adaptive (a round
  that raises no *new* surviving finding ends the loop). Driver/plugin class, autonomous.
- **Skip a cosmetic re-vet** — do not re-enter test-vet when the test diff is non-behavioural.
  Plugin class, autonomous. Note this modifies a doctrine-derived rule (§3.3) in *code*; if it
  requires editing `conductor/doctrine/*.md`, it is **not** autonomous — see the traps below.
- **Narrow the lens set** — lower `itemReviewers` from 6, or `vetCritics` from 3. Driver
  class, autonomous, but it is a quality trade: only do it if Phase 1 showed the marginal
  lenses contribute nothing distinct.

Record the prediction and its falsifier in the register **before** any run that tests it.

### PHASE 3 — Two small defects, each worth its own register entry

Both were observed in epoch 23 and neither is fixed. Run
`python3 scripts/prior_art.py <mechanism>` before recording either as new — search by
mechanism, not symptom; its own header warns that a negative on the symptom is a weak
negative.

1. **An empty review validates and reads as an approval.** A reviewer lens whose entire reply
   is `{"findings":[]}` satisfies the Findings schema, and review doctrine treats an empty
   review as the approval. In a controlled replay this happened at *unbudgeted* settings — one
   lens spent 26,306 characters of reasoning and emitted twenty characters — so it is a
   standing defect of the reviewer stage, not an artifact of the reasoning budget. The
   consequence is that "the reply validated" cannot distinguish a lens that looked and found
   nothing from a lens that never looked. Decide what signal separates them and pin it.
2. **A vet critic put a required field one level too deep.** At 02:54:12 in the run,
   `conductor_vet_test` aborted a round because a critic returned
   `{"kind":"env","reason":"sub-session output failed schema validation after retries",
   "errors":["TestVet: missing required property \"mustFix\"",
   "TestVet.verdictsByCriterion: unexpected additional property \"mustFix\""]}`. This is
   **not** D51's shape — the reply was real and the schema complaint is accurate, so the retry
   was correct rather than a lie about the model's output. It cost one vet round. The likely
   fix is in the critic's brief or the schema's shape, not in the retry logic.

### PHASE 4 — Gate, then commit

On a **quiet machine** (no servers, no cells, nothing else running):

```bash
bash scripts/test-conductor.sh     # last line must read: GATE PASS
bash scripts/conductor-gate.sh     # must read: M5 PASS
```

Commit in finding-sized pieces, in the register's voice — see `git log --oneline -8` for the
convention, and note that commit bodies explain *what was measured and what it refutes*, not
what files changed. **Do not push.**

### PHASE 5 — Only if Phases 1–4 justify it: another run

A run costs up to 8.9 hours (baseline ~22 min + doctrine ~27 min + conductor's 480-minute
budget). Launch only if a change's mechanism criterion genuinely needs a full cell, and
pre-register its expectations in the register **before** launching.

To launch: edit ONLY the CONFIG block of `scripts/run_and_watch.py` — set `RESULTS_DIR` to a
NEW, EMPTY directory (`.data/benchmark/watch/step10-<name>`) — then run it with **no
arguments**. All three arms always run; there is no arm filter by design.

Watch it with `node conductor/tools/observe.ts <run-dir> --console` (use `--console`, not
`--json`; the JSON output carries no token totals) plus the ledger tail. The rank-7 stall
detector fires automatically at 45 minutes with no completed request, prints a loud block and
writes a `STALL_ALARM` sentinel, and **aborts nothing** — on a fire, snapshot the run
directory, kill, and record the stall with its journal tail. Never silently retry.

---

## 5. Traps this repository has already paid for

These are not style preferences. Each one cost a measurement.

1. **`scripts/run_and_watch.py` parses NO argv.** There is no `argparse` and no `sys.argv` in
   the file, so `--help` launches a real multi-hour benchmark that saturates the machine. Read
   the CONFIG block; edit constants only, and only between runs.
2. **A results directory containing a cell JSON is `conductor_bench`'s resume ledger.** It
   reuses any cell whose result file exists and does not even create the work tree. Never copy
   one in; `RESULTS_DIR` must be new and empty. Four step directories currently share ONE
   grid2048 measurement because of this.
3. **Never edit anything under `conductor/` while a run is in flight.** Every generated
   `conductor.json` names the plugin by ABSOLUTE PATH into the live checkout, so a mid-run edit
   rewrites the experiment retroactively and nothing in the artifacts records that it did.
4. **The gate needs a quiet machine.** `scripts/test-conductor.sh` boots its own `opencode
   serve` in its live leg and times out under contention, which reads as a fake regression.
   Serialize: gate → run → analyze. Never overlap them.
5. **Never restore a mutated file with `git checkout`.** Undo with the inverse edit. (The tree
   is clean at `18ab6ac`, so this only bites once you start editing.)
6. **Never read `.data/router/metrics.jsonl` unwindowed, and never join it on `group`.** That
   exact mistake reported a prior day's decode as a live run's total and manufactured a
   45,812-token phantom "reasoning gap" that reached a campaign brief. See D53.
7. **`conductor/doctrine/*.md` is NOT autonomous.** Those files ARE the doctrine arm's entire
   system prompt, concatenated verbatim. Editing one between two doctrine cells confounds that
   arm. If your fix requires a doctrine edit, stop and surface it rather than deciding it.
8. **Served-config changes are NOT autonomous** (slots, per-slot context, `--cache-ram`, any
   `--reasoning-budget` flag). One `llama-server` serves all three arms, so a change there
   re-prices every previously scored cell of every arm.
9. **Never report an n=1 before/after as an arm result.** Measured baseline CV is 23.6%
   same-epoch and ~34% cross-epoch; the minimum detectable effect at 3 reps is 54–78%. A
   mechanism verdict at n=1 is legitimate (did the rows disappear, did the journal stop saying
   X); a cost or quality claim at n=1 is not.
10. **Never arm a watchdog from a round number, and never make one terminal.** Healthy maxima
    on record: a 26.9-minute single generation and a 30.0-minute gap between events, both on
    work that then SUCCEEDED. A 20-minute deadline kills roughly one healthy dispatch in ten.
11. **Never fix a stage failure by removing a retry.** Six of eight lenses that hit the
    1,800 s provider timeout returned valid output on the very next attempt.
12. **`scripts/arm_report.py` defaults to `bench/conductor-tasks.json`**, which does not
    contain `grid2048-headless-py`; on a games-corpus epoch it renders an empty report rather
    than an error. Always pass `--manifest bench/corpus-games.json`.
13. **Every change ships red-green** — a test that fails without it, proven by stashing the
    source change and running the test.
14. **Two instruments that should agree, and one that is easier to read.** Twice in the last
    cycle the easier reading was wrong: a replay harness that read "the last ledger row" got
    its predecessor's row and flipped a verdict from REFUTED to CONFIRMED, and a "1.2% saving"
    was computed over a denominator that silently excluded every runaway. When two instruments
    disagree, find out why before trusting either.

---

## 6. Verification commands

```bash
bash scripts/test-conductor.sh                   # whole suite; must print GATE PASS
bash scripts/test-conductor.sh 'conductor/tests/inject.test.ts'   # one file
bash scripts/conductor-gate.sh                   # mechanical source scan; must print M5 PASS
node --test --test-reporter=tap conductor/tests/<file>.test.ts    # one file, fast, no gate
/usr/bin/python3 -m unittest discover -s scripts -p 'test_*.py'   # python leg
node conductor/tools/observe.ts <run-dir> --console               # read a run, live or archived
python3 scripts/prior_art.py <mechanism>                          # BEFORE recording a defect
```

The Python leg pins `/usr/bin/python3` (system interpreter, 3.9) deliberately — the harness
scripts are standard-library-only. TypeScript is run by node's own type-stripping; there is no
build step. `conductor/tsconfig.json` sets `erasableSyntaxOnly`, so `enum`, `namespace` and
constructor parameter properties do not compile.

---

## 7. What success looks like

- Phase 1's analysis exists, is adversarially verified, and names a lever with a number and a
  falsifier beside it — **even if the answer is "the review loop earns its cost and nothing
  should be cut."** That is a legitimate and valuable outcome; the refutations in this campaign
  have been worth more than several of the proposals.
- Any change Phase 2 lands ships red-green, with its prediction and falsifier registered
  before it is tested.
- Both defects in Phase 3 are registered (or shown by `prior_art.py` to be already known).
- `GATE PASS` and `M5 PASS` on the committed tree, commits in finding-sized pieces, not pushed.
- Anything you could not settle is written down as an open question with the evidence you have,
  rather than resolved by assertion.

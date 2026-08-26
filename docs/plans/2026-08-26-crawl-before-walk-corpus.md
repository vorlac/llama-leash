# Handoff: crawl before walk — measure the harness on problems it is allowed to plan

A self-contained brief for a fresh session. Everything it needs is in this repository.

## The disconnect

The campaign's claim is that the harness plans better than one model turn: it decomposes a
problem into testable pieces, writes the test first, and works the pieces to completion. Epoch 14
cannot measure that, because **the prompts contain the decomposition.**

`bench/conductor-tasks.json`, task `tetris-py`, verbatim:

> Build the game on top of them, **in order, because each piece needs the one before it**:
> 1. `src/bag.py` exports `piece_at(index)`… 2. `src/rules.py` exports `fits`, `lock`, `settle`,
> `score_for`… 3. `src/engine.py` exports `start`, `spawn`, `step`… 4. `src/play.py` exports
> `play`…

Four modules, twelve signatures, the dependency order and the scoring table. The conductor's
decompose stage is transcribing, not decomposing — and the baseline arm receives the same plan
for free, which is a plausible reason baseline goes 11/12 on work the harness was meant to help
with.

### Why the prompts are like that, which is the part that matters

The decomposition is not an authoring habit. It is forced, and the chain runs backwards from the
test:

```
gauge imports 5 modules  →  SPEC.md must name them  →  prompt must name them  →  plan handed over
```

`bench/corpus/tui-games/snake-headless/hidden/gauge/check_spec.py` opens with

```python
from src.engine import Game
from src.food import place
from src.replay import ScriptError, fields, parse, replay
from src.rng import Lcg
```

Four of those five modules are ones the model is supposed to invent. So the seeded `SPEC.md` §1
is a module table, and the prompt indexes it. **Stripping the numbered list from the prompt
changes nothing while the gauge imports the interior.**

## The principle

> The prompt pins **one seam and the behaviour observable through it**. The gauge asserts
> **only that seam**. Everything between them is the model's to design, and is therefore
> measurable.

Same gauge machinery, same objective scoring, no rubric in the path. What changes is that the
arms can now produce structurally different solutions — which is also the first time the blind
quality judge has anything real to compare on `structure` and `decomposition`.

## The ladder, which is the operator's requirement and not a nicety

Simple problems first, and **the hard tier is not attempted until the simple tier produces
clearly good results.** A harness that cannot complete a one-function task with a known answer
has not earned a run at a terminal game, and a failure at the top of the ladder is
uninterpretable when the bottom rung was never checked.

## What already exists — the estimate this replaces was too pessimistic

An earlier reading of this called for re-authoring the corpus and a full re-run. That was wrong.
Five manifests already exist beside the 23-task ladder, and **the crawl rung is already built
correctly and has never been run as a campaign.**

| manifest | tasks | seam-pinned? | state |
|---|---:|---|---|
| `bench/corpus-euler.json` | 20 | **yes** | **never run in any campaign** |
| `bench/corpus-games.json` | 2 | `grid2048` yes, `snake` no | never run in any campaign |
| `bench/conductor-tasks.json` | 23 | **no** | the only manifest epoch 14 ran |

Checked: no `.data/benchmark/watch/*` campaign holds a `euler-0NN` cell.

### The crawl rung is `bench/corpus-euler.json` and it is correct as written

Twenty tasks, one per Project Euler problem. Each pins exactly one seam —
`src/solvers/pNNN.py` exporting `solve()` registered under its own name — and leaves the
algorithm entirely open. The prompt's own words:

> `solve()` must return within 60 seconds on one core, **so choose the algorithm before you write
> the loop.**

The gauge imports only seeded, unchangeable machinery (`src.solvers`, `src.cli.main`,
`src.registry`), carries the verified answer and a 60 s budget, and reads every module under
`src/` with `ast` to refuse an answer that was written down rather than computed:

> an answer parked in a module of its own and imported back is the answer written down with one
> extra file in front of it

`bench/corpus/project-euler/hard-subset.json` marks the problems where brute force will not
finish inside the budget, so the difficulty is algorithmic rather than clerical.

**Its one weakness, stated so nobody claims otherwise:** each task is a single item, so it
measures whether the harness can complete simple work cleanly. It does not measure decomposition
depth. That is the correct property for a crawl rung and the wrong one to generalise from.

### The walk rung needs one real fix

`grid2048-headless-py` is close to right already: it names two unimplemented requirements inside
a specified system and points at `SPEC.md` for the rules, handing over no plan. Its gauge imports
seven modules but five are seeded and frozen.

`snake-headless-py` is the one to fix. Its gauge imports four modules the model must create.
Route the gauge through a single entry point — one `replay(seed, script)` returning the summary
line — rewrite `SPEC.md` §1 to describe behaviour instead of a module table, and drop the
numbered module list from the prompt. **One task, not a corpus.**

## What is already known about the crawl rung, and must not be rediscovered

`euler-001-py` has been run three-arm twice, both on 2026-08-21, both **conductor losses with
different causes — do not conflate them**. Forensics: `.data/analysis/three-arm-euler-001.md`
(986 lines, gitignored, present on this machine).

1. Baseline PASS 2.7 min · doctrine PASS 14 min · **conductor FAIL 43.9 min, never left INTAKE**.
   Cause was a cluster-extractor defect, since fixed in `conductor/core/planning.ts`.
2. Post-fix, same cell: baseline PASS 4.5 min · doctrine PASS 21.1 min · **conductor TIMEOUT at
   45.0 min, reached EXECUTING, wrote zero bytes.**

And the finding that decides whether a T1 run can succeed at all:

> **The T1 ceiling is not a time budget, it is a ~38,000-completion-token budget.** Across three
> arms whose prompt volume differs 4.1x, completion-tokens-per-wall-second is 13.94 / 13.43 /
> 14.18. The floor for a clean trivial behavioral item is 18 model calls = 78% of T1, so the
> process and the tier are mismatched by construction.

**Settle that before running twenty cells.** A campaign that reproduces a known budget mismatch
twenty times has bought nothing.

## The work, in order

1. **Reproduce one `euler-001-py` cell three-arm at HEAD.** Everything above predates the current
   tree — the stalled-turn detector, the inline-claim refusal, the derived mechanics and the per-
   role deadlines have all landed since. Establish what the conductor arm does today before
   changing anything.
2. **Resolve the T1 budget mismatch** if step 1 reproduces it, since every crawl-rung cell
   inherits it.
3. **Run the crawl rung** — `bench/corpus-euler.json`, three arms, the hard subset preferred over
   the easy problems. Report per-arm pass rate against the verified answers.
4. **Only if step 3 is clearly good, fix the walk rung** and run it: `snake-headless-py` reseamed,
   plus `grid2048-headless-py` as is.
5. **Record what `bench/conductor-tasks.json` can and cannot answer.** It is not worthless — its
   cost ratios and its `testQuality` result stand, and the latter arguably strengthens: doctrine
   beat baseline 3 of 4 on test quality *even with the plan handed over*. What it cannot support
   is any claim about planning or decomposition. Say so in the register rather than deleting it.

## Traps this campaign has already paid for

- **A metric that cannot tell "measured nothing" from "nothing to measure."** Met five times. A
  cell with no tree, a judge that failed, and a tie must be three different words.
- **A pattern that matches for a reason unrelated to its purpose.** Most recently: archived part
  spans separate the arms 62 s to 1200 s and mean the opposite of silence. Validate a heuristic
  against cases it must REJECT.
- **Believing a guard fired for the reason it claims.** Reproduce the computation first.
- **Assuming a document describes the tree.** `SPEC.md` §1 is a module table because the gauge
  imports modules; read the gauge, not the prose.

## Acceptance

- `bench/corpus-euler.json` runs three-arm with a per-arm pass rate against verified answers, and
  the result is written into `docs/build/artifacts/14.2-arm-campaign.md`.
- The T1 budget question is answered with numbers, not deferred.
- If `snake-headless-py` is reseamed, its gauge imports exactly one module the model authors, and
  a test proves the old module-table prompt is gone.
- `bash scripts/test-conductor.sh` prints `GATE PASS`; `bash scripts/conductor-gate.sh` prints
  `M5 PASS`.

## Out of scope

**D43 — the stall deadline.** Reserved for its own session. Reading epoch 14's transcripts
changed what it must be built against; see *Reading the transcripts* in the D43 section of
`docs/build/artifacts/14.2-arm-campaign.md` before starting it.

**The declined tasks.** `CORPUS-MIGRATION.md` §3.4 and §3.5 decline six tui-games and all five
docs-generation tasks. Those declines are correct and were re-checked on 2026-08-26: an authored
reference is an oracle only if the specification pins enough ground truth to prove the reference
itself right. Reinstating them without an oracle reintroduces a self-graded lane.

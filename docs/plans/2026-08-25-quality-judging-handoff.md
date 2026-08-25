# Handoff: the quality-judging instrument

A self-contained brief for a fresh session. Everything needed is in this repository;
nothing depends on the state of the session that wrote it.

## Why this piece and not the others

The remaining work from
[the metrics plan](2026-08-25-relative-metrics-and-stall-deadlines.md) splits by whether it
needs a *running experiment* or a *free hand*:

| work | needs | where |
|---|---|---|
| epoch 14 monitoring and close | live monitors, the epoch's own context | the originating session |
| D43 stall deadline | epoch 14's untruncated planner durations and baseline cadence | the originating session |
| **quality judging** | **design freedom, no live state** | **a fresh session — this brief** |

Quality judging is the largest independent piece, it blocks on nothing that is currently
running, and it is *generative* rather than *interpretive* — which is exactly the kind of work a
clean context serves better than an accumulated one.

---

## The prompt to invoke it with

> Read `docs/plans/2026-08-25-quality-judging-handoff.md` and
> `docs/plans/2026-08-25-relative-metrics-and-stall-deadlines.md`, then build the quality-judging
> instrument described there. Populate the rubric lane that already exists at
> `bench/conductor/rubrics` and is validated by `conductor_bench.py::validate_rubric` but has
> never been written to by any epoch. Work to `bash scripts/test-conductor.sh` printing
> GATE PASS and `bash scripts/conductor-gate.sh` printing M5 PASS. Before recording anything as
> a new finding, run `python3 scripts/prior_art.py <mechanism>` — four defects in this campaign
> were "discovered" when the answer was already written down.

---

## What the instrument has to do

Compare two implementations of the **same prompt** and say which is better, blind.

**Inputs** are already produced and archived. `<results>/trees/<cell>/repo` holds each arm's
finished tree from epoch 14 onward (`archive_cell_tree`), and
`docs/build/artifacts/EPOCH-REVIEW.md` shows what a rendered comparison looks like.
`scripts/epoch_review.py::source_files` already strips harness furniture — `.git`,
`.conductor`, `node_modules`, and the hidden `gauge/` — and is worth reusing rather than
re-deriving.

**Two axes, scored separately, because they diverge:**

- **Code quality** — does it do what was asked; is it the simple version of that; does it handle
  what the prompt names; is anything present that nothing asked for.
- **Test quality** — *not test count*. Does each test fail for the reason it claims; does it test
  behaviour or restate the implementation; does it cover the edge the prompt actually names;
  would it catch a regression a later change might introduce.

The second axis is the one that matters most, and the reason is worth carrying: **the whole
claim of the conductor arm is that its process produces better-considered work than one model
turn. If it cannot beat baseline on test quality, there is no upside to pay for a 3-26x cost.**
It is the one metric that could justify the overhead and the one never taken.

## Required properties

1. **Blind.** The judge must not see which arm produced which tree. Arm identity leaks through
   more than labels — `.conductor/` directories, commit messages, file ordering — so strip
   deliberately and test that the strip works.
2. **Order-swapped.** Run each comparison twice with the positions exchanged. An implementation
   that wins in both orders won; one that wins only when shown first did not. Position bias is
   real and cheap to detect.
3. **Reasoned.** A winner with no stated reason is unauditable. The reason is the artifact; the
   verdict is a summary of it.
4. **Repeated.** The judge is a model and subject to the same non-determinism this campaign spent
   thirteen epochs learning to distrust. n>=3, and **a judge that disagrees with itself across
   repetitions is reported as a tie** rather than resolved by picking one.
5. **Not a ratio.** Rubric scores have no true zero, so `score_a / score_b` means nothing. The
   output is win / loss / tie plus reasons — ordinal, which is what the underlying judgement is.

## Traps this campaign has already paid for

Each of these cost a wrong conclusion here. They are not hypothetical.

- **A metric that cannot tell "measured nothing" from "nothing to measure."** Met three times
  (D18's partial window; a fingerprint that scored zero over an *empty* denominator and looked
  like a confirmed prediction; a ratio reporting a missing measurement in the same words as a
  failed run). A judgement over a missing tree must say so, loudly, and never count as a tie.
- **A pattern that matches for a reason unrelated to its purpose.** A regex intended to find a
  restated *subject* matched the word "the"; a fingerprint intended to find *deliberation*
  counted a noun the task domain uses. Validate any heuristic against a corpus of cases it must
  REJECT, not only ones it should accept.
- **Verification that cannot see the edit.** macOS system Python caches bytecode in
  `~/Library/Caches/com.apple.python/`, outside the tree, mtime-validated — so two edits inside
  one second can leave a red-check reading a stale module. The gate pins `/usr/bin/python3`, so
  this reaches every Python test here.
- **Believing a guard fired for the reason it claims.** Reproduce the computation before
  recording a verdict.

## Acceptance

- Rubric records validate against `conductor_bench.py::validate_rubric` and carry a reviewer.
- Blinding is tested, not asserted: a test that fails if arm identity survives the strip.
- Order-swap disagreement and self-disagreement both resolve to `tie`, with tests.
- Run over epoch 14's archived trees, and the result written into the campaign register at
  `docs/build/artifacts/14.2-arm-campaign.md`.
- `GATE PASS` and `M5 PASS`.

## The honest open question

Nobody has established that a local 27B model can judge code quality reliably enough for this to
mean anything. **Calibrate before trusting it**: give the judge pairs whose answer is already
known — a correct implementation against one with a seeded defect, a real test against one that
asserts nothing — and measure how often it gets them right. If it cannot separate obvious cases,
it cannot separate subtle ones, and that is a result worth reporting rather than a reason to
quietly proceed.

# Relative metrics and stall deadlines

Every threshold in this harness is currently an absolute constant chosen against one
corpus on one machine: a 900 000 ms sub-session watchdog, a 1 800 s T0 budget, a 7 000-byte
pack ceiling. Each is a property of the measurement setup rather than of the software being
measured, and two consequences have now been paid for:

- **They do not survive noise.** The control arm — which loads no packs, runs no plugin, and
  cannot be reached by any change in this campaign — measured **6,364 and then 614** generated
  tokens on an identical cell in consecutive epochs. Every cross-epoch absolute comparison in
  the register was made against a floor nobody had measured.
- **They do not scale.** A deadline tuned against a 292 KB repository means nothing against a
  million-line one, and no constant serves both.

The fix for both is the same move, and it is the move D43 already makes for one timer:
**measure the thing relative to something that varies the same way.**

---

## The principle

> A metric is reported as a **ratio to the baseline arm, on the same task, in the same epoch**,
> where the denominator is the **median of that epoch's calibration repetitions** — never a
> single sample.

Same machine, same thermal state, same weights, same prompt. Common-mode noise divides out.
This is a paired design and it is strictly more sensitive than comparing absolutes across days.

The denominator is the load-bearing part. Ratios inherit their denominator's noise
**multiplicatively**: against baseline's 614 tokens the conductor arm looks ten times worse than
against 6,364, for the same numerator. `--calibration-reps` (landed 2026-08-25) exists to make
that denominator a median rather than a sample; it was built to measure noise and turns out to
be the precondition for this whole framing.

---

## What is measured, and how

### 1. Cost — cardinal, so a ratio is meaningful

| metric | numerator | denominator |
|---|---|---|
| time | the arm's `wallClockMs` | median baseline `wallClockMs`, same task, same epoch |
| generated tokens | `gen_tokens.py` total for the arm | median baseline total, same task, same epoch |

Reported as `3.4x time · 6.2x tokens`, with absolutes carried alongside as context rather than
as the headline.

### 2. Correctness — stays absolute, deliberately

The hidden gauge either passes or it does not. There is no baseline-relative version of "the
tests pass", and inventing one would be the mistake this document exists to avoid, in reverse.

### 3. Quality — ordinal, so a ratio is NOT meaningful

Rubric scores have no true zero: a 6 is not twice a 3 in any defensible sense, and dividing two
of them yields a number with no interpretation. The instrument is a **blind paired comparison**:

- A judge is shown two implementations of the same prompt, **unlabelled**, and returns a winner
  and a stated reason.
- The comparison is run **twice with the order swapped**, because position bias is real and
  cheap to detect: an arm that wins in both orders won; an arm that wins only when shown first
  did not.
- The result populates the rubric lane that **already exists** (`.data/benchmark/conductor/rubrics`,
  `validate_rubric`) and that no epoch has ever written to.

Two axes, scored separately because they diverge:

**Code quality** — does it do what was asked; is it the simple version of that; does it handle
what the prompt names; is there anything present that nothing asked for.

**Test quality** — and this is the axis that decides whether the harness has a reason to exist.
Not test COUNT. Whether each test fails for the reason it claims; whether it tests behaviour or
restates the implementation; whether it covers the edge the prompt actually names; whether it
would catch a regression a later change might introduce.

> The whole claim of the conductor arm is that its process — TDD discipline, adversarial review,
> multiple perspectives — produces better-considered work than one model turn. **If it cannot
> beat baseline on test quality, there is no upside to pay for a 3-26x cost.** That is the one
> metric that could justify the overhead and the one metric never taken.

---

## Gates are stated tolerances, not derived thresholds

A gate like "within 4x baseline time" is **a product decision about acceptable overhead**. It is
not a measurement and must never be written as though it were: this campaign has twice been
bitten by a number acquiring authority it did not earn.

Each gate is therefore recorded with who chose it and on what grounds, and **paired with an
absolute ceiling** — 4x of a sixty-minute baseline is four hours, which a ratio gate alone would
pass as healthy.

---

## D43's stall threshold, expressed the same way

The pending stall-based deadline (D43) was about to take its threshold from epoch 14's observed
distribution — another constant, better sourced but still a constant.

Under this principle it is instead **a multiple of the baseline arm's own emission cadence**:
the inter-part gap distribution baseline exhibits on that task, in that epoch, from the
`message.part.updated` stream. A session is stalled when it has been silent for K times longer
than a healthy session on the same work is ever silent.

That survives a million-line codebase for the same reason the ratio metrics do, and it is the
reason this document and D43 land together.

---

## Order of work, cheapest first

1. **Epoch 14 closes.** It supplies the first per-epoch baseline medians and the first
   untruncated planner durations.
2. **Ratio reporting.** Costs no new measurement — every input already exists in the results and
   the archived session stores. Retrofit over the existing epochs where calibration data allows.
3. **Stall deadline (D43).** Needs the baseline cadence distribution from step 2.
4. **Quality judging.** Last because it is the only one that needs model calls, a blinding
   harness, and a bias check — and because steps 2 and 3 make the runs it judges cheaper to
   produce.

---

## What could go wrong

- **The denominator can be absent.** Baseline is 35/37 but not 37/37. A task where baseline
  fails has no trustworthy denominator, and the honest report is "no baseline", not a ratio
  against a failed run.
- **A ratio can hide absolute unusability**, hence the paired ceilings above.
- **The judge is itself a model** and subject to the same non-determinism this campaign has
  spent thirteen epochs learning to distrust. Order-swapped pairs catch position bias; n>=3
  catches the rest; a judge that disagrees with itself across repetitions is reported as a tie
  rather than resolved by picking one.
- **Ratios make small denominators loud.** A task baseline finishes in 40 seconds turns a
  two-minute conductor run into "3x", which is true and probably not interesting. Ratios want a
  floor below which the absolute is reported instead.

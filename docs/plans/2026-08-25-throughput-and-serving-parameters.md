# Throughput: where the GPU time actually goes

Written against epoch 14 while it ran, from its own serving process. Nothing here has
been changed; changing a serving parameter mid-epoch would invalidate the epoch.

The starting question was whether more aggressive parallelism could use idle GPU
capacity. The capacity is idle, the measurement below says so, and **parallelism is not
the first thing to reach for.** Two cheaper findings sit in front of it.

---

## 1. The GPU runs one sequence at a time

`llama-server` is started with `--parallel 3` and `--ctx-size 196608`, giving
`n_slots = 3, n_ctx_slot = 65536, kv_unified = false`. How many of those slots do work:

| method | window | result |
|---|---|---|
| live `/slots` poll, 2 s interval, during a **conductor** cell | 90 samples | 1 slot busy **92%**, 2 slots **7%**, 0 slots **1%** — mean **1.06** |
| `launch_slot_` / `release` timeline from the server log | 188 min | 1 slot **86.9%**, 2 slots **8.5%**, 3 slots **1.0%** — mean **1.07** |
| per-slot launch counts | server lifetime | slot 0: **90**, slot 1: **13**, slot 2: **78** |

Two independent methods agree to within 0.01. **Two thirds of the slot capacity is idle,
and the third slot is essentially unused.**

### Why raising `--parallel` is the wrong response

Slot context is `total ctx / n_slots`, so more slots means less context each. A live
`/slots` read caught slot 0 holding **36,753 prompt tokens** — 56% of its 65,536. At
`--parallel 6` each slot would get 32,768 and that session would truncate. The
harness would trade a real capability for capacity it already has and does not use.

### Why the slots are idle

The conductor's request stream is dominated by `orchestrator` and `planner` turns, which
are sequential by construction: plan, then decompose, then dispatch. The roles that fan
out — `implementer`, `reviewer`, `testWriter` — are a small tail, because **the cells die
before reaching them.** Every conductor cell epoch 14 had run at the time of writing —
three of the four, `clock-inject-py` still pending — failed at or before
`runState=DECOMPOSED`, and `logfmt-lenses-ts` burned 52.3 minutes on
`aborts=[('planner','20m00s'), ('planner','20m00s')]` — two planner runs, each killed at
exactly the ceiling.

So the harness is not failing to parallelise a parallel workload. **It never reaches the
parallel phase.** Anything that gets a cell past planning creates the concurrent demand
that would fill the slots, and nothing before that point can.

---

## 2. Prefill is being redone, and nobody was counting

Every serving parameter below is **unset**, so the server runs stock defaults:
`--metrics`, `--cache-ram`, `-ctk` / `-ctv`, `-b` / `-ub`, `--cache-reuse`,
`--model-draft`, `--no-context-shift`.

`--cache-ram` defaults to **8192 MiB**. Against that ceiling the server log records:

```
34 evictions, 47.3 GB total
median entry 1,207 MiB, largest 3,390 MiB
W srv alloc: - making room for prompt cache entry, removing oldest entry
```

Prompt-cache entries of 0.5-3.4 GB against an 8 GB cache means roughly three to six live
sessions fit, while a conductor run keeps an orchestrator, a planner and sub-sessions
alive at once. Pooled over the ledger:

| | |
|---|---|
| prompt tokens seen | 29,104,248 |
| served from cache | 24,721,929 (84.9%) |
| re-prefilled | 4,382,319 (15.1%) |
| full cache misses | 288 of 1,823 requests (15.8%) |
| what those misses cost | **20,067 s of prefill — 70% of all prefill time** |
| median missed prompt | 12,139 tokens (max 21,526) |

At the measured 147 tok/s prefill, a 12,000-token miss is 80 seconds and a 36,000-token
miss is four minutes — inside a role with a 20-minute ceiling.

**The honest bound.** A `cache_n == 0` request is not proof of an eviction: a genuinely
new sub-session has no cached prefix and never did. The provable waste is the 34 logged
evictions; the 5.6 hours is the upper bound on the prize, not a claim about it. The two
cannot currently be separated, which is itself finding 3.

---

## 3. Three instruments cannot answer the questions asked of them

- **The router ledger has no timestamp.** Every rate, concurrency and per-epoch question
  is therefore unanswerable from it. This is not hypothetical: a first pass at this
  analysis derived "2.8x concurrency" from it and was wrong by a factor of nearly three,
  because the ledger silently spans runs — it holds 146 records for
  `conductor/clock-inject-py`, a task that had not run at all in the epoch being
  measured. One field fixes it, and the ratios and D43 work both want it.
- **`queueWaitMs` is 0 on every record, and means nothing.** The router admits
  `maxInflightPerModel: 6` to a server with 3 slots, so requests 4-6 wait *inside*
  `llama-server` where the router cannot see them. Its queue metric reads healthy while
  the real constraint sits one layer down.
- **`--metrics` is off**, so the server publishes no slot or cache counters at all. The
  measurements in section 1 had to be reconstructed from log lines and a hand-rolled
  poller. This is the cheapest fix in the document.

Also worth recording: only `conductor/*` groups appear in the ledger. The 1,075
untagged records are consistent with `baseline` and `doctrine`, which run no plugin and
so mint no `X-Conductor-Group` header. **The router's view is a view of one arm.**

---

## 4. The ceiling, so nobody expects too much

Apple M4 Max, 40 GPU cores, 64 GB unified, ~546 GB/s. The model is 20 GB (Q6_K, 64
layers). At the measured 14.9 tok/s single-stream, decode already moves ~298 GB/s —
about **55% of peak bandwidth** — because single-sequence decode re-reads the whole
weight set per token.

Filling slots amortises that read across sequences, which is why it helps at all. But
starting from 55% of bandwidth, three busy slots is worth perhaps **2-2.5x**, not 3x.
That is arithmetic from the bandwidth figure, not a measurement, and should be treated
as a bound rather than a target.

---

## 5. Order of work

Cheapest and most certain first. **None of it lands while an epoch is running.**

| # | change | expected | risk |
|---|---|---|---|
| 1 | `--metrics` on | none directly — makes sections 1-2 measurable instead of reconstructed | none |
| 2 | timestamp in the router ledger | none directly — makes every rate question answerable | none |
| 3 | **parallelise the quality judge's own call loop** | the first honest test of the 2-2.5x prediction, on work with no measurement to corrupt | none to the campaign — see below |
| 4 | raise `--cache-ram` | fewer evictions; upper bound is the 5.6 h of cold prefill | memory pressure; must be sized against slot KV |
| 5 | `-ctk q8_0 -ctv q8_0` | ~halves KV bytes: smaller cache entries, less KV read per decode step, more headroom for 4 | quality effect unmeasured on this model |
| 6 | reach the fan-out phase (planner budget) | creates the demand that fills slots; also fixes the 0/4 cell failures | this is harness work, not a flag |
| 7 | campaign-level cell parallelism | uses the idle slots directly | **corrupts wall-clock cost measurement** — see below |
| 8 | speculative decoding (`--model-draft`) | the only lever that helps at concurrency 1 | needs a small same-vocab draft model; none is local |

### On 3, and why the judge is the right first experiment

Every claim in section 1 says the slots are idle because nothing asks for them. The
cheapest thing that could ask for them is `scripts/judge_quality.py`, and while
calibrating it against this same server **it used 1 of 3 slots** — reproducing the
campaign's own pattern in a completely different program.

Its `compare()` loop is strictly serial: criteria, then both presentation orders, then
repetitions. **No call depends on any other call's result.** Each is an independent
scoring of a fixed pair of trees, and `settle()` aggregates over an unordered set of
runs, so concurrency changes when work happens and not what is computed.

That makes it the right first experiment for three reasons a campaign cell cannot match:

- **There is no measurement to corrupt.** The judge's wall clock is not a campaign
  metric. Item 7 is blocked on exactly this and item 3 is not.
- **The prediction is falsifiable in one run.** Section 4 argues filling slots is worth
  2-2.5x, from bandwidth arithmetic rather than measurement. A serial-then-parallel run
  over the same pair set at the same seeds tests it directly, and if the speedup is not
  there the arithmetic is wrong and items 6-7 lose most of their motivation.
- **The prize is immediate.** The pending run is 180 calls plus 72 for calibration; at
  the observed ~25-40 s each that is two to three hours serial.

Two invariants a parallel version must preserve, both already pinned by tests:
**a distinct seed per repetition** — the whole reason repetitions mean anything — and
**both presentation orders per criterion**, since a verdict needs unanimity across them.
Neither is affected by dispatch order, but both are easy to lose while restructuring the
loop, so the existing `test_a_comparison_uses_a_distinct_seed_per_repetition` and the
order-swap tests are the gate on this change.

### On 5 and quality

KV quantization is a **numerical** change to a campaign whose whole output is a
comparison. Landing it between epochs changes the thing being measured. It belongs
either before a fresh baseline or behind a calibration run of its own, and the register
should record which epochs ran with it — this campaign has already been bitten by a
constant that changed under a comparison.

### On 7 and the measurement

Running cells concurrently is the most direct use of the idle slots, and it is in
tension with the campaign's own headline metric: **the change that would use the GPU is
the change that destroys the wall-clock number.**

That tension resolves rather than blocks. Generated-token counts are concurrency
invariant; wall clock is not, and
[the metrics plan](2026-08-25-relative-metrics-and-stall-deadlines.md) already reports
both. So a parallel campaign yields valid token ratios and invalid time ratios — a knob
with a stated cost, used for correctness and quality passes and turned off for cost
passes. What it must never be is a default nobody wrote down.

---

## What this does not settle

- **Whether the planner's 20 minutes is spent on cold prefill or on generation.** If a
  meaningful share is re-prefill, item 4 partly fixes item 6 and the ordering above is
  right. If it is generation, item 6 is independent work. `--metrics` plus a ledger
  timestamp answers it directly, which is why they are first.
- **Prefill at 147 tok/s median** on this hardware is unaudited. `-ub` is at its default
  of 512 and larger physical batches usually help prefill on Metal, but no measurement
  here supports a specific value.
- **Nothing has been benchmarked.** Every number above is observation of a running
  production epoch, not a controlled comparison. Items 4, 5 and 8 each want an A/B on a
  fixed prompt set before adoption, and the harness already has `scripts/benchmark.py`
  for exactly that. Item 3 is the exception: it is its own A/B.

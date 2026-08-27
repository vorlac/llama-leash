# Making the plan stage affordable

`conductor_plan` has never completed in any epoch of this campaign. Epoch 20 is the first run
that let it try without a deadline, and after 95 minutes it had produced nothing while
reasoning correctly the whole time. This is what it is spending, why, and what to do about it
in the order the measurements support.

Everything below is measured on the epoch-20 cell (`grid2048-headless-py`, M4 Max 64 GB,
`qwen3.8-27b` Q6_K) and cites where.

---

## 1. What the cost actually is

| | |
|---|---:|
| the entire codebase — `src` + `tests` + `tools` + `SPEC.md` + `NOTES.md` | **29,861 B ≈ 7,465 tok** |
| the plan stage's reasoning so far | **230,313 B ≈ 57,578 tok** |
| ratio | **7.7x the whole codebase, in thinking alone** |
| at the measured 13.5 tok/s | **71 minutes of pure decode** |
| baseline's completion tokens for the WHOLE task | **27,997** |

**The harness has spent 2x the entire solution's tokens deciding how to approach it, and has
not finished deciding.** Wall clock is `tokens / 13.5` and nothing else in the run matters.

The failure is not slowness. It is that the stage cannot emit its artifact, three times over:

```
prompt=45549  completion=16384    <- output cap, hit exactly
prompt=34404  completion=16384    <- hit exactly again
   3 prompt drops in the planner's ledger window = 3 compactions
```

Turn 7 reached *"let me carefully construct the markdown string"*. Turn 12 reached *"now I
need to emit the final Plan JSON object"*. Neither could finish, and each compaction threw
away the ~19,200 tokens of reasoning that got there.

---

## 2. Why the artifact is too big — and it is specified, not accidental

`conductor/doctrine/plan.md`'s own self-check, which `planPrompt` quotes and the handler
enforces:

> - [ ] Every non-obvious step carries **complete code, not a sketch**.
> - [ ] Consequential forks record >= 2 options and a reasoned choice.
> - [ ] Security, validation, data-loss, and accessibility are handled explicitly.

So `plan.md` must contain the solution written out in full, before the implementer writes the
solution. For `grid2048` that is two functions plus a test file carrying SPEC's twelve-row R9
table — the plan is larger than the diff, and the implementer then produces it again.

**This is the dominant structural cost and no serving flag touches it.**

---

## 3. The squeeze, which is one config line in tension with itself

The cell config declares:

```json
"limit": { "context": 65536, "output": 16384 }
```

opencode compacts at `context - min(20000, output)` = **49,152**. The planner reached 45,549
prompt tokens — about 3,600 from compaction — while simultaneously being truncated at the
16,384 output cap.

**Raising `output` to let the artifact finish LOWERS the compaction threshold by the same
amount**, squeezing the context needed to build it. The two walls are the same number pulling
in opposite directions, which is why "just raise it" is not the fix.

---

## 4. The change set, ordered by effect over cost

### 4.1 Shrink what the plan must contain — largest effect, no hardware

Drop "complete code, not a sketch" for steps whose item already carries acceptance criteria
and a testScope. The item's acceptance IS the specification; restating it as code in the plan
duplicates the implementer's job into the most expensive stage.

- **Effect:** directly attacks the 57,578 tokens. A plan that names paths, states the
  approach and records the forks — without inlining the implementation — is plausibly a
  quarter of the size.
- **Risk:** the doctrine's reason for the rule is real — a plan that hand-waves is a plan
  that defers decisions. The rule should relax where an item's acceptance already pins the
  behaviour, not everywhere.
- **Verify:** re-run this cell; `conductor_plan` completes without compacting.

### 4.2 Give `planPrompt` the tree, as `decomposePrompt` already has

`decomposePrompt` ends with `scopableFilesSection`, inlining every scopable file so the
planner "decompose[s] from here rather than reading them again" — 15,117 chars.
`planPrompt` has no such section: **6,828 chars**, and the live trace shows the planner
spending its first six turns on `glob`, `grep` and ten `read`s reconstructing what the
previous stage was handed for free.

This is D16/D26/D29 surviving in the one stage nobody could observe, because it always died
at 20 minutes first.

- **Effect:** ~4 minutes of re-reading, plus a better-informed plan.
- **Risk:** it moves those bytes into the prompt, so the window pressure does not vanish.
  Pair with 4.1.
- **Verify:** the plan session's first tool call is not a `read` of a seeded file.

### 4.3 `--parallel 1` — free, and the config is currently paying for nothing

The server allocates `n_slots = 3, n_ctx_slot = 65536` = **196,608 tokens of KV cache**.
Measured slot occupancy across this campaign is **1.07x**. Decode reads the KV cache on every
step, so a cache sized for three sequences is read while serving one.

- **Effect:** less KV read per decode step and far less memory pressure on a 64 GB machine
  holding a 20 GB model. Modest, and free.
- **Risk:** the conductor's review fan-out serialises — but at 1.07x measured occupancy it
  already does.
- **Verify:** `predicted_per_second` in the router ledger before and after, at comparable
  prompt depth.

### 4.4 `-ctk q8_0 -ctv q8_0` — throughput plan item 5, still open

Halves KV bytes. The planner reached 45,549 prompt tokens, so KV read per decode step is
substantial at the depth this stage actually runs at.

- **Risk:** quality effect unmeasured on this model, and it is a NUMERICAL change to a
  campaign whose output is a comparison. The throughput plan's own caution applies: it
  belongs before a fresh baseline or behind its own calibration.

### 4.5 Speculative decoding — throughput plan item 8, the only lever that helps at concurrency 1

Drafts several tokens per forward pass. **1.5-2.5x on predictable output like code.**

- **Blocker:** needs a small SAME-VOCAB draft model and none is local. `ornith-9b` is
  catalogued as "a good speculative-decoding draft model" — for Ornith-35B, a different
  family. A Qwen3 0.6B or 1.7B GGUF would work and is not yet fetched.

---

## 5. What none of this fixes

Decode is memory-bandwidth-bound: 13.5 tok/s x 20 GB = **~270 GB/s effective against ~546
GB/s peak**, about 50% efficiency, which is normal for llama.cpp on Metal. `--n-gpu-layers
999` and `--flash-attn auto` are already set. **The weights cannot be made to move faster;
there can only be fewer bytes to move or more tokens per pass.**

All four serving levers together are perhaps 3x. They would take this stage from 95 minutes
to ~30. **They do not change the finding that the harness spends 2x the whole solution's
tokens deciding how to approach it.**

And the asymmetry matters for where this is meant to go: hardware buys a constant factor,
while the compaction squeeze and the oversized artifact are structural and worsen with
codebase size. At 30 KB of source the planner already compacted three times in a 65k window.
A repository ten times this one does not fit at any speed — **that is a wall, not a slope.**

---

## 6. Order of work

1. **4.1** — shrink the plan artifact. Largest effect, no hardware, and it is the reason the
   squeeze binds at all.
2. **4.3** — `--parallel 1`. Free, and correcting a config that provisions 3x what the
   workload uses.
3. **4.2** — inline the tree in `planPrompt`. Small and obviously right, but pair it with 4.1
   or it trades reading time for window pressure.
4. **4.5** — fetch a Qwen3 0.6B draft model and measure speculative decoding.
5. **4.4** — KV quantization, last, and behind its own calibration because it changes the
   numbers the campaign compares.

Re-measure `conductor_plan` on this same cell after each. The stage has never completed, so
the first run that finishes it is the first real datum about what planning costs.

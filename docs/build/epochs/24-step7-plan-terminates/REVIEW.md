# Epoch 24 — `step7-plan-terminates`

Started 2026-08-27 00:37 EDT · 2 cells

## 1 · Changes since the previous epoch

_No commits landed between the previous epoch and this one._


## Task `grid2048-headless-py`  (T2)

### 2 · The prompt, as it was fed this epoch

From `bench/corpus-games.json` as of `0ffa022dbb23`.

```
This workspace holds a headless 2048, specified by SPEC.md. The generator, the board, the spawn protocol, the counters, the script parser, the replay loop and the summary are written and pass the visible suite. Two requirements are not implemented, and NOTES.md keeps the index of which is where:

- R7 step 2, in src/moves.py: slide_left gathers a row's non-zero values and pads the row back to four, but never combines a pair, so it emits every tile it was given and always reports a gain of zero. SPEC.md section 5 has the rule and the twelve-row table it has to satisfy. src/moves.py already routes all four directions through slide_left, so the rule lands once for all of them.
- R13 and R14, in src/undo.py: a snapshot carries the board and the score only. The move counter and the generator's state are not recorded and not restored, so `moves` keeps climbing across an undo and a direction replayed after an undo draws fresh numbers and spawns a different tile. CAPACITY is declared and not enforced, so the stack grows without bound.

Implement both. They touch different files and neither depends on the other. Do not regress anything that already works: the specification is normative in full, and the graded run checks the merge table row by row and column by column, move legality and rejection, the score, the rewind, and whole recorded summary lines byte for byte including the generator's state word.

python3 tools/run_tests.py tests must keep passing. Keep NOTES.md honest: its requirement index is the workspace's own account of itself, so a requirement that stops being unimplemented moves in that table too.

Do not change src/rng.py, src/board.py, src/summary.py, src/session.py or src/replay.py. Do not special-case an input by its values, its length or the seed it came from.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 40.5 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 40.4 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._


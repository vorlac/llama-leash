# Epoch 9 — `20260823-110952`

Started 2026-08-23 11:09 EDT · 5 cells

## 1 · Changes since the previous epoch

2 commit(s).

| commit | what changed | defect |
|---|---|---|
| `be8c44900` | conductor: the out-of-tree refusal names the spelling the check accepts | D13, D30 |
| `76d323f74` | docs: withdraw D25 — the cluster guard is correct and already documented | D25, D29 |


## Task `euler-cli-py`  (T1)

### 2 · The prompt, as it was fed this epoch

From `bench/conductor-tasks.json` as of `76d323f74708`.

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:\n- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.\n- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.\n- main(["run", "all"]) does the same for every solver, in sorted name order.\n- An unknown solver name prints a message containing that name and returns 2.\n- No arguments at all returns 2.\nReach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 4.5 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 12.2 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._


## Task `slugify-ts`  (T0)

### 2 · The prompt, as it was fed this epoch

From `bench/conductor-tasks.json` as of `76d323f74708`.

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

### `baseline` — stock opencode `build` agent — llama.cpp + vanilla opencode, nothing from this repository applied

**PASS** · 3.1 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._

### `doctrine` — the nine doctrine packs as a static system prompt; no plugin, no state machine, no sub-sessions

**PASS** · 11.8 min · hidden tests: pass

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._

### `conductor` — the full llama-leash workspace — opencode plugin, run FSM, gates, and sub-session fan-out

**TIMED OUT** · 30.0 min · hidden tests: fail

#### 3a · Cost by phase

_No session store for this cell — per-phase cost is unrecoverable._

#### 3b · The resulting code

_Not preserved. `run_and_watch.py` clears the work root at the start of every run, so this epoch's trees were destroyed when the next one launched._

#### 3d · The transcript

_No session store was archived for this cell, so there is no transcript to show. Epochs before tree archiving landed have prompts, outcomes and timings but no turns._


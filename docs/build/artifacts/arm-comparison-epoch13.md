# Arm comparison — the same prompt, three harnesses

Generated from `.data/benchmark/watch/20260824-225834` and the work trees under `/Users/sal/.llama-leash-work`.

Each task below shows the request, the tree the model started from, the hidden
test it was judged by and never saw, and then what each arm actually produced.

- **`baseline`** — stock opencode `build` agent. No plugin, no doctrine, no fan-out. This is llama.cpp + vanilla opencode.
- **`doctrine`** — the nine doctrine packs injected as a static system prompt. No plugin, no state machine, no sub-sessions.
- **`conductor`** — the full workspace: opencode plugin, run FSM, gates, and sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).

## Scoreboard

| task | `baseline` | `doctrine` | `conductor` |
|---|---|---|---|
| `slugify-ts` | **pass** | **pass** | TIMEOUT |
| `euler-cli-py` | **pass** | **pass** | TIMEOUT |
| `logfmt-lenses-ts` | **pass** | **pass** | TIMEOUT |
| `clock-inject-py` | **pass** | **pass** | TIMEOUT |


---

# `slugify-ts`  (T0)

## The request

```
src/slugify.ts exports slugify(input). Make it turn an arbitrary title into a URL slug: lowercase the text, replace every run of characters that are not letters or digits with a single '-', and remove leading and trailing '-'. Keep the existing export name and signature. tests/visible.test.ts must keep passing.
```

## What it started from  (3 file(s))

`README.md`

```markdown
# slugify

A tiny URL-slug helper. Run the suite with `node --test tests/visible.test.ts`.
```

`src/slugify.ts`

```ts
export function slugify(input: string): string {
  return input.trim().toLowerCase();
}
```

`tests/visible.test.ts`

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "../src/slugify.ts";

test("lowercases a plain word", () => {
  assert.equal(slugify("Hello"), "hello");
});
```

## The hidden test it was judged by

Materialized only after the process exits, so no arm can read or edit it.

`gauge/spec.test.ts`

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { slugify } from "../src/slugify.ts";

test("spaces become single hyphens", () => {
  assert.equal(slugify("Hello There World"), "hello-there-world");
});
test("punctuation runs collapse", () => {
  assert.equal(slugify("Cats, Dogs & Mice!"), "cats-dogs-mice");
});
test("edges are trimmed", () => {
  assert.equal(slugify("  --Hello--  "), "hello");
});
test("digits survive", () => {
  assert.equal(slugify("Top 10 Reasons"), "top-10-reasons");
});
test("an empty result stays empty", () => {
  assert.equal(slugify("!!!"), "");
});
```


## `baseline` — stock opencode `build` agent. No plugin, no doctrine, no fan-out. This is llama.cpp + vanilla opencode.

**PASS** · 1.7 min · hidden tests: pass · 614 generated tokens

Touched 1 file(s).

`src/slugify.ts` (modified)

```ts
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
```


## `doctrine` — the nine doctrine packs injected as a static system prompt. No plugin, no state machine, no sub-sessions.

**PASS** · 22.9 min · hidden tests: pass · 16,049 generated tokens

Touched 2 file(s), 1 of them created.

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


## `conductor` — the full workspace: opencode plugin, run FSM, gates, and sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).

**TIMED OUT** · 30.0 min · hidden tests: fail · 11,020 generated tokens · 4 waves

**The tree is unchanged from the seed — this arm produced nothing.**


---

# `euler-cli-py`  (T1)

## The request

```
This package solves a collection of Project Euler problems through a solver registry. src/cli.py exports main(argv) and does nothing useful. Make it the front end:
- main(["list"]) prints every registered solver name, one per line, sorted, and returns 0.
- main(["run", NAME]) runs that one solver and prints a single line '<name> <answer> <milliseconds>ms', where milliseconds is a whole number, then returns 0.
- main(["run", "all"]) does the same for every solver, in sorted name order.
- An unknown solver name prints a message containing that name and returns 2.
- No arguments at all returns 2.
Reach solvers only through src/registry.py, and make sure importing src.cli is enough to have every solver registered. tests/check_visible.py must keep passing.
```

## What it started from  (9 file(s))

`README.md`

```markdown
# euler\n\nA collection solver: a registry, one solver per problem, and a CLI over both. Run the suite with `python3 tools/run_tests.py tests`.\n
```

`src/__init__.py`

```python
(empty)
```

`src/cli.py`

```python
"""The command line over the solver registry."""

import sys


def main(argv):
    sys.stdout.write("not runnable yet\n")
    return 1
```

`src/registry.py`

```python
"""The solver registry: one common interface every solver is reached through."""

_SOLVERS = {}


def register(name, solve):
    if name in _SOLVERS:
        raise ValueError("solver %r is already registered" % name)
    _SOLVERS[name] = solve


def get(name):
    if name not in _SOLVERS:
        raise KeyError(name)
    return _SOLVERS[name]


def names():
    return sorted(_SOLVERS)
```

`src/solvers/__init__.py`

```python
from src.solvers import p001, p002  # noqa: F401
```

`src/solvers/p001.py`

```python
from src.registry import register


def solve():
    return sum(n for n in range(1000) if n % 3 == 0 or n % 5 == 0)


register("p001", solve)
```

`src/solvers/p002.py`

```python
from src.registry import register


def solve():
    total = 0
    a, b = 1, 2
    while b <= 4000000:
        if b % 2 == 0:
            total += b
        a, b = b, a + b
    return total


register("p002", solve)
```

`tests/check_visible.py`

```python
import unittest

import src.solvers  # noqa: F401
from src.registry import get, names


class VisibleTests(unittest.TestCase):
    def test_registry_holds_both_solvers(self):
        self.assertEqual(names(), ["p001", "p002"])

    def test_solvers_answer(self):
        self.assertEqual(get("p001")(), 233168)
        self.assertEqual(get("p002")(), 4613732)


if __name__ == "__main__":
    unittest.main()
```

`tools/run_tests.py`

```python
#!/usr/bin/env python3
"""Run every check_*.py in one directory against the checkout at the cwd.

Loaded by path rather than by unittest discovery: discovery would require the
test directory to be an importable package, and a missing __init__.py there
would look exactly like a failing suite.
"""

import importlib.util
import os
import sys
import unittest

def main(directory):
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    names = sorted(
        name
        for name in os.listdir(directory)
        if name.startswith("check_") and name.endswith(".py")
    )
    if not names:
        sys.stderr.write("no check_*.py under %s\n" % directory)
        return 2
    for name in names:
        spec = importlib.util.spec_from_file_location(
            name[:-3], os.path.join(directory, name)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.testsRun:
        return 2
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

## The hidden test it was judged by

Materialized only after the process exits, so no arm can read or edit it.

`gauge/check_spec.py`

```python
import contextlib
import io
import re
import unittest

from src.cli import main


def run(argv):
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = main(argv)
    return code, buffer.getvalue()


class SpecTests(unittest.TestCase):
    def test_list_names_every_solver(self):
        code, out = run(["list"])
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), ["p001", "p002"])

    def test_run_one_prints_answer_and_timing(self):
        code, out = run(["run", "p001"])
        self.assertEqual(code, 0)
        self.assertRegex(out.strip(), r"^p001 233168 \d+ms$")

    def test_run_all_prints_every_solver_in_order(self):
        code, out = run(["run", "all"])
        self.assertEqual(code, 0)
        lines = out.strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertRegex(lines[0], r"^p001 233168 \d+ms$")
        self.assertRegex(lines[1], r"^p002 4613732 \d+ms$")

    def test_unknown_solver_is_refused(self):
        code, out = run(["run", "p999"])
        self.assertEqual(code, 2)
        self.assertIn("p999", out)

    def test_no_arguments_is_refused(self):
        self.assertEqual(run([])[0], 2)


if __name__ == "__main__":
    unittest.main()
```

`gauge/run.py`

```python
#!/usr/bin/env python3
"""Run every check_*.py in one directory against the checkout at the cwd.

Loaded by path rather than by unittest discovery: discovery would require the
test directory to be an importable package, and a missing __init__.py there
would look exactly like a failing suite.
"""

import importlib.util
import os
import sys
import unittest

def main(directory):
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    names = sorted(
        name
        for name in os.listdir(directory)
        if name.startswith("check_") and name.endswith(".py")
    )
    if not names:
        sys.stderr.write("no check_*.py under %s\n" % directory)
        return 2
    for name in names:
        spec = importlib.util.spec_from_file_location(
            name[:-3], os.path.join(directory, name)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.testsRun:
        return 2
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```


## `baseline` — stock opencode `build` agent. No plugin, no doctrine, no fan-out. This is llama.cpp + vanilla opencode.

**PASS** · 5.9 min · hidden tests: pass · 3,761 generated tokens

Touched 1 file(s).

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


## `doctrine` — the nine doctrine packs injected as a static system prompt. No plugin, no state machine, no sub-sessions.

**PASS** · 18.9 min · hidden tests: pass · 11,811 generated tokens

Touched 2 file(s), 1 of them created.

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


## `conductor` — the full workspace: opencode plugin, run FSM, gates, and sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).

**TIMED OUT** · 45.0 min · hidden tests: fail · 17,582 generated tokens · 8 waves

**The tree is unchanged from the seed — this arm produced nothing.**


---

# `logfmt-lenses-ts`  (T2)

## The request

```
This tool reads logfmt lines into records and reports on them through lenses. A lens is a module under src/lenses/ exporting apply(records) and returning an array of report lines; src/lenses/count.ts is the example. Add four more, each in its own file and none importing another:
- src/lenses/errors.ts: one line per record whose level is 'error', oldest first, formatted '<at> <route> <status>'.
- src/lenses/latency.ts: exactly three lines, 'count <n>', 'mean <ms>' and 'max <ms>', with mean rounded to the nearest whole millisecond. An empty set gives count 0, mean 0, max 0.
- src/lenses/by-status.ts: one line per distinct status, '<status> <count>', ordered by status ascending.
- src/lenses/slowest.ts: the three slowest records, slowest first, formatted '<route> <ms>'; fewer than three records gives fewer lines.
Every lens must return an array for an empty record set rather than throwing. Change nothing in src/record.ts. tests/visible.test.ts must keep passing.
```

## What it started from  (5 file(s))

`README.md`

```markdown
# logfmt\n\nA log reader with one report lens per file under `src/lenses/`. Run the suite with `node --test tests/visible.test.ts`.\n
```

`src/lens.ts`

```ts
import type { LogRecord } from "./record.ts";

// A lens turns a set of records into report lines. Every lens is independent:
// it reads records and returns text, and knows about no other lens.
export type Lens = (records: readonly LogRecord[]) => string[];
```

`src/lenses/count.ts`

```ts
import type { LogRecord } from "../record.ts";

export function apply(records: readonly LogRecord[]): string[] {
  return [`records ${records.length}`];
}
```

`src/record.ts`

```ts
export type LogRecord = {
  readonly at: number;
  readonly level: string;
  readonly route: string;
  readonly status: number;
  readonly ms: number;
};

// One logfmt line: `at=3 level=info route=/a status=200 ms=12`. A line missing
// a field, or carrying an unparsable number, yields null.
export function parseLine(line: string): LogRecord | null {
  const fields = new Map<string, string>();
  for (const pair of line.trim().split(/\s+/)) {
    const split = pair.indexOf("=");
    if (split > 0) fields.set(pair.slice(0, split), pair.slice(split + 1));
  }
  const at = Number(fields.get("at"));
  const status = Number(fields.get("status"));
  const ms = Number(fields.get("ms"));
  const level = fields.get("level");
  const route = fields.get("route");
  if (level === undefined || route === undefined) return null;
  if (!Number.isFinite(at) || !Number.isFinite(status) || !Number.isFinite(ms)) return null;
  return { at, level, route, status, ms };
}

export function parseAll(lines: readonly string[]): LogRecord[] {
  const out: LogRecord[] = [];
  for (const line of lines) {
    const record = parseLine(line);
    if (record !== null) out.push(record);
  }
  return out;
}
```

`tests/visible.test.ts`

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseLine, parseAll } from "../src/record.ts";
import { apply as count } from "../src/lenses/count.ts";

const LINES = [
  "at=1 level=info route=/a status=200 ms=10",
  "at=2 level=error route=/b status=500 ms=40",
  "nonsense",
];

test("a well-formed line parses", () => {
  assert.deepEqual(parseLine(LINES[0]), {
    at: 1,
    level: "info",
    route: "/a",
    status: 200,
    ms: 10,
  });
});
test("a malformed line is dropped", () => {
  assert.equal(parseLine("nonsense"), null);
  assert.equal(parseAll(LINES).length, 2);
});
test("the count lens reports how many records it saw", () => {
  assert.deepEqual(count(parseAll(LINES)), ["records 2"]);
});
```

## The hidden test it was judged by

Materialized only after the process exits, so no arm can read or edit it.

`gauge/spec.test.ts`

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseAll } from "../src/record.ts";
import { apply as errors } from "../src/lenses/errors.ts";
import { apply as latency } from "../src/lenses/latency.ts";
import { apply as byStatus } from "../src/lenses/by-status.ts";
import { apply as slowest } from "../src/lenses/slowest.ts";

const RECORDS = parseAll([
  "at=1 level=info route=/a status=200 ms=10",
  "at=2 level=error route=/b status=500 ms=40",
  "at=3 level=info route=/a status=200 ms=20",
  "at=4 level=warn route=/c status=404 ms=30",
  "at=5 level=error route=/b status=500 ms=90",
]);

test("the errors lens lists every error level record, oldest first", () => {
  assert.deepEqual(errors(RECORDS), ["2 /b 500", "5 /b 500"]);
});

test("the latency lens reports count, mean and max as whole milliseconds", () => {
  assert.deepEqual(latency(RECORDS), ["count 5", "mean 38", "max 90"]);
});

test("the by-status lens counts each status, lowest status first", () => {
  assert.deepEqual(byStatus(RECORDS), ["200 2", "404 1", "500 2"]);
});

test("the slowest lens lists the three slowest, slowest first", () => {
  assert.deepEqual(slowest(RECORDS), ["/b 90", "/b 40", "/c 30"]);
});

test("every lens survives an empty record set", () => {
  for (const lens of [errors, latency, byStatus, slowest]) {
    assert.ok(Array.isArray(lens([])));
  }
  assert.deepEqual(latency([]), ["count 0", "mean 0", "max 0"]);
});
```


## `baseline` — stock opencode `build` agent. No plugin, no doctrine, no fan-out. This is llama.cpp + vanilla opencode.

**PASS** · 4.7 min · hidden tests: pass · 2,538 generated tokens

Touched 4 file(s), 4 of them created.

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


## `doctrine` — the nine doctrine packs injected as a static system prompt. No plugin, no state machine, no sub-sessions.

**PASS** · 13.7 min · hidden tests: pass · 8,175 generated tokens

Touched 5 file(s), 5 of them created.

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


## `conductor` — the full workspace: opencode plugin, run FSM, gates, and sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).

**TIMED OUT** · 60.0 min · hidden tests: fail · 39,857 generated tokens · 7 waves

**The tree is unchanged from the seed — this arm produced nothing.**


---

# `clock-inject-py`  (T4)

## The request

```
Session expiry in src/expiry.py cannot be tested at a fixed instant, because every reader of the wall clock resolves it at call time. Make the whole package testable against a pinned instant, keeping every existing call site exactly as it is:
- set_now(seconds) pins the instant every reader sees.
- reset_now() hands the clock back to the real one.
- now() returns the pinned instant while one is set, and the real time otherwise.
After set_now, opening a session, deciding expiry and summarizing must all see the pinned instant. Do not change any function signature, and do not thread a clock argument through the callers. tests/check_visible.py must keep passing.
```

## What it started from  (8 file(s))

`README.md`

```markdown
# sessions\n\nSession opening, expiry and a summary over both. Run the suite with `python3 tools/run_tests.py tests`.\n
```

`src/__init__.py`

```python
(empty)
```

`src/clock.py`

```python
"""The one place this package reads the wall clock."""

import time


def now():
    return time.time()
```

`src/expiry.py`

```python
from src.clock import now

TTL_SECONDS = 900


def expires_at(session):
    return session["opened_at"] + TTL_SECONDS


def is_expired(session):
    return now() >= expires_at(session)
```

`src/session.py`

```python
from src.clock import now


def open_session(user):
    return {"user": user, "opened_at": now()}


def age_of(session):
    return now() - session["opened_at"]
```

`src/summary.py`

```python
from src.expiry import is_expired


def summarize(sessions):
    live = [s for s in sessions if not is_expired(s)]
    return "%d live of %d" % (len(live), len(sessions))
```

`tests/check_visible.py`

```python
import unittest

from src.expiry import TTL_SECONDS, expires_at
from src.session import open_session
from src.summary import summarize


class VisibleTests(unittest.TestCase):
    def test_a_session_expires_a_ttl_after_it_opened(self):
        session = {"user": "ada", "opened_at": 100.0}
        self.assertEqual(expires_at(session), 100.0 + TTL_SECONDS)

    def test_opening_a_session_names_its_user(self):
        self.assertEqual(open_session("ada")["user"], "ada")

    def test_a_summary_counts_what_it_was_given(self):
        self.assertIn("of 0", summarize([]))


if __name__ == "__main__":
    unittest.main()
```

`tools/run_tests.py`

```python
#!/usr/bin/env python3
"""Run every check_*.py in one directory against the checkout at the cwd.

Loaded by path rather than by unittest discovery: discovery would require the
test directory to be an importable package, and a missing __init__.py there
would look exactly like a failing suite.
"""

import importlib.util
import os
import sys
import unittest

def main(directory):
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    names = sorted(
        name
        for name in os.listdir(directory)
        if name.startswith("check_") and name.endswith(".py")
    )
    if not names:
        sys.stderr.write("no check_*.py under %s\n" % directory)
        return 2
    for name in names:
        spec = importlib.util.spec_from_file_location(
            name[:-3], os.path.join(directory, name)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.testsRun:
        return 2
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```

## The hidden test it was judged by

Materialized only after the process exits, so no arm can read or edit it.

`gauge/check_spec.py`

```python
import unittest

from src.clock import now, reset_now, set_now
from src.expiry import TTL_SECONDS, is_expired
from src.session import open_session
from src.summary import summarize


class SpecTests(unittest.TestCase):
    def tearDown(self):
        reset_now()

    def test_a_pinned_clock_is_what_every_reader_sees(self):
        set_now(1000.0)
        self.assertEqual(now(), 1000.0)
        self.assertEqual(open_session("ada")["opened_at"], 1000.0)

    def test_expiry_is_decided_against_the_pinned_instant(self):
        set_now(1000.0)
        session = open_session("ada")
        self.assertFalse(is_expired(session))
        set_now(1000.0 + TTL_SECONDS - 1)
        self.assertFalse(is_expired(session))
        set_now(1000.0 + TTL_SECONDS)
        self.assertTrue(is_expired(session))

    def test_the_summary_moves_with_the_clock(self):
        set_now(1000.0)
        sessions = [open_session("ada"), open_session("bob")]
        self.assertEqual(summarize(sessions), "2 live of 2")
        set_now(1000.0 + TTL_SECONDS)
        self.assertEqual(summarize(sessions), "0 live of 2")

    def test_resetting_hands_the_clock_back(self):
        set_now(1000.0)
        reset_now()
        self.assertNotEqual(now(), 1000.0)


if __name__ == "__main__":
    unittest.main()
```

`gauge/run.py`

```python
#!/usr/bin/env python3
"""Run every check_*.py in one directory against the checkout at the cwd.

Loaded by path rather than by unittest discovery: discovery would require the
test directory to be an importable package, and a missing __init__.py there
would look exactly like a failing suite.
"""

import importlib.util
import os
import sys
import unittest

def main(directory):
    sys.path.insert(0, os.getcwd())
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    names = sorted(
        name
        for name in os.listdir(directory)
        if name.startswith("check_") and name.endswith(".py")
    )
    if not names:
        sys.stderr.write("no check_*.py under %s\n" % directory)
        return 2
    for name in names:
        spec = importlib.util.spec_from_file_location(
            name[:-3], os.path.join(directory, name)
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(loader.loadTestsFromModule(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.testsRun:
        return 2
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
```


## `baseline` — stock opencode `build` agent. No plugin, no doctrine, no fan-out. This is llama.cpp + vanilla opencode.

**PASS** · 3.9 min · hidden tests: pass · 2,120 generated tokens

Touched 2 file(s), 1 of them created.

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


## `doctrine` — the nine doctrine packs injected as a static system prompt. No plugin, no state machine, no sub-sessions.

**PASS** · 9.0 min · hidden tests: pass · 5,008 generated tokens

Touched 2 file(s), 1 of them created.

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


## `conductor` — the full workspace: opencode plugin, run FSM, gates, and sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).

**TIMED OUT** · 60.0 min · hidden tests: fail · 37,547 generated tokens · 7 waves

**The tree is unchanged from the seed — this arm produced nothing.**


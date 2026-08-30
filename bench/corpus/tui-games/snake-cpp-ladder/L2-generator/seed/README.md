# snake — one rung

`SPEC.md` is normative for the whole program and does not change between rungs. The task you
were given names the one part of it this workspace is missing; everything else here is
written and correct, and changing it is not the job.

```
./build.sh                                   builds, exits 0, leaves ./snake
./snake --headless --seed 42 --script s.txt  one line of JSON, exits 0
./snake --seed 42                            plays on the terminal
tools/run_tests.sh                           builds, then runs every executable in tests/
```

The visible suite fails when there are no tests at all: a suite that runs nothing is not a
passing suite. Write the tests your change needs under `tests/`.

The graded run executes the built binary and never reads your source.

## The machine

Apple Clang with C++23, CMake, Ninja, and the system ncurses (`-lncurses`, `<curses.h>`).
**There is no network**, so a dependency fetched at build time will fail the build.

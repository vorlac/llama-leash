# snake — rung 1, the bootstrap

`SPEC.md` is normative for the whole program. This rung asks for the smallest part of its
outside: a build, and a binary that answers `--version`. Nothing else — no rules, no
generator, no replay, no terminal mode. Later rungs add each of those over what you write.

```
./build.sh              builds, exits 0, leaves ./snake     <- you write this
./snake --version       prints tui-snake/1, exits 0         <- and this
tools/run_tests.sh      builds, then runs every executable in tests/
```

The tree is empty apart from this file, the specification and the test runner, so the
layout, the build system and the file names are yours. Put your sources under `src/`.

The visible suite fails on arrival because there is no `build.sh` yet, which is the honest
state of an empty workspace, and it fails when there are no tests at all: a suite that runs
nothing is not a passing suite.

## The machine

Apple Clang with C++23, CMake, Ninja, and the system ncurses (`-lncurses`, `<curses.h>`).
**There is no network**, so a dependency fetched at build time will fail the build.

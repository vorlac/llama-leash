# snake — a terminal game with a scriptable head

An empty workspace and a specification. `SPEC.md` is normative; everything it
does not pin is yours to decide.

The program has two front ends over one game:

- a **terminal** game a person plays, and
- a **headless** mode that runs a script and prints one line of JSON,

and the same seed and script always produce the same bytes.

## The three fixed points

Everything the graded run touches is at the outside of the program:

```
./build.sh                                   -> builds, exits 0, leaves ./snake
./snake --headless --seed 42 --script s.txt  -> one line of JSON, exits 0
./snake --seed 42                            -> plays on the terminal
```

There is no required directory layout, no required file, no required class and
no required build system. One `.cpp` file compiled by one `c++` invocation is as
correct as a CMake project.

## Running the tests

```
tools/run_tests.sh
```

It builds and then runs every executable directly under `tests/`. It fails when
there is no `build.sh`, when the build fails, when any test exits non-zero, and
when there are no tests at all — a suite that runs nothing is not a passing
suite. On a fresh checkout it fails for the first reason, which is the honest
state of a workspace with no program in it yet.

## The machine

Apple Clang with C++23, CMake, Ninja, and the system `ncurses` (`-lncurses`,
`<curses.h>`). **There is no network**, so a dependency fetched at build time
will fail the build.

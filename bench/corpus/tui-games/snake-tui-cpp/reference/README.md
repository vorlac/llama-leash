# The reference implementation

`snake.cpp` and `build.sh` are a complete solution to `../../../seed/SPEC.md`,
written from that specification alone: the rules, the headless replay and the
terminal game, in one translation unit compiled by one `c++` invocation and
linking nothing beyond libc++. It is never seeded into a work tree.

It exists for three reasons, and the third is the one that matters.

**It produced `../vectors.json`.** Every expected line in that file is this
program's output. Nothing in the gauge is compared against output the work tree
was told to generate.

**It proves the expectations are the specification's.** It reproduces both
generator sequences of requirement 14, all three first-food cells of requirement
18, and the 1061-byte worked example of requirement 41 byte for byte. A gauge
whose oracle disagreed with the document would be scoring its own opinion.

**It proves the task is achievable.** The whole gauge — 36 checks including the
seven that drive a pseudo-terminal — runs green against it in about seven
seconds. A task no one has finished is a task whose failures cannot be read.

It also fixes the shape of the calibration: every mutation in the table in
`bench/corpus-games.json`'s rationale was applied to this file, and each one is
named there with the check that caught it.

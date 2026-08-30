# `snake` — a terminal game with a scriptable head

A complete game of Snake in C++. It is played in a terminal by a person, and it
is driven in a headless mode by a script so that the same seed and the same
script always produce the same bytes. Both halves are one program.

Numbered requirements are the contract. Where a constant or a formula is given,
that constant or that formula is the one to use. Everything this document does
not pin is yours: the file layout, the class design, the build system, whether
you draw with raw escape sequences or link a curses library, and how you divide
the work. Two implementations that both follow this document will disagree about
almost everything except what is written here, and that is intended.

## 1. What is fixed, and what is not

Exactly three things are fixed at the outside of the program, because the graded
run drives them: how it is built (section 2), how it is driven headlessly
(section 3), and how it behaves on a terminal (section 10). The rules in
sections 4 to 9 are fixed because a game of Snake with different rules is a
different game.

Nothing else is. There is no required directory layout, no required file, no
required class, no required build system and no required library. A single
translation unit compiled by one `c++` invocation satisfies this document as
fully as a CMake project with several targets.

## 2. Building

1. `./build.sh` at the root of the work tree builds the program. It is
   executable, it takes no arguments, and it exits `0` on success and non-zero
   on failure. It may do anything: invoke `c++` directly, drive CMake and Ninja,
   or anything else.
2. A successful `./build.sh` leaves an executable at `./snake` in the root of
   the work tree. That path is what the graded run executes.
3. The build must work with **no network access**. The machine has Apple Clang
   (C++23), CMake, Ninja, and the system `ncurses` (`-lncurses`, header
   `<curses.h>`). Anything you cannot compile from your own sources or link from
   what is already installed is not available, so a dependency fetched at build
   time will fail the build.
4. `./build.sh` must be safe to run twice in a row on the same tree.

## 3. The headless mode

5. `./snake --headless --seed <n> --script <path>` runs a whole game from a
   script and writes **exactly one line** of JSON to standard output, ending
   with a single newline, then exits `0`. `<n>` is a non-negative decimal
   integer. A `<path>` of `-` means the script is read from standard input.
6. Nothing else may go to standard output in this mode. Diagnostics belong on
   standard error.
7. The headless mode never opens a terminal, never sleeps, never reads the
   wall clock, never reads a real random source and never opens a socket. It is
   a pure function of the seed and the script.
8. A script that violates section 8 makes the program exit **`3`** and write
   nothing to standard output.

## 4. The board

9. The playfield is **40 columns by 20 rows**. `x` runs `0..39` left to right
   and `y` runs `0..19` top to bottom, so `[0, 0]` is the top-left cell and the
   row-major index of a cell is `y * 40 + x`.
10. The board does not wrap. Leaving the playfield in any direction is a wall
    collision.

## 5. Initial state

11. A new game's snake has **length 3**, laid out horizontally with the head at
    `(20, 10)` and the body at `(19, 10)` and `(18, 10)`, in that order. The
    snake is always stored head-first, tail-last.
12. The committed direction is `RIGHT`, the pending direction is `RIGHT`, the
    score is `0`, ticks elapsed is `0`, food eaten is `0`, restarts is `0`, the
    status is `alive` and the game is not paused.
13. Exactly one food item exists at all times while the game is running. The
    first food is placed during initialisation, before any tick runs, by
    section 6.

## 6. Randomness and food placement

14. The only source of randomness is a 32-bit linear congruential generator.
    Constructing it with `seed` sets the state to `seed mod 2**32`, and each
    `next()` performs, with wrapping 32-bit arithmetic, and returns the **new**
    state:

    ```
    state = (state * 1664525 + 1013904223) mod 2**32
    return state
    ```

    For `seed = 1` the first six outputs are exactly

    ```
    1015568748, 1586005467, 2165703038, 3027450565, 217083232, 1587069247
    ```

    and for `seed = 42` they are exactly

    ```
    1083814273, 378494188, 2479403867, 955863294, 1613448261, 110225632
    ```

    Both sequences must reproduce.
15. The generator is drawn from for **food placement only**. Nothing else in the
    program may consume it; that is what makes a replay reproducible.
16. A placement builds the list of free cells — every cell of the playfield not
    occupied by a snake segment, in **ascending row-major order** — and returns
    `free[next() % free.size()]`. Exactly one draw is consumed per placement.
    Rejection sampling is forbidden: it would consume a seed-dependent number of
    draws.
17. When there are no free cells the placement yields no food and consumes no
    draw.
18. Worked example. At the start of a game the snake occupies 3 cells, so the
    free list has 797 entries. With `seed = 42` the first `next()` returns
    `1083814273`, `1083814273 mod 797` is `274`, and free cell 274 is `(34, 6)`.
    With `seed = 1` the first food is `(25, 6)`; with `seed = 7` it is `(8, 5)`.

## 7. The rules

19. Directions are `UP`, `DOWN`, `LEFT` and `RIGHT`, with deltas `(0, -1)`,
    `(0, +1)`, `(-1, 0)` and `(+1, 0)`.
20. A turn sets the **pending** direction if and only if the requested direction
    is not the exact opposite of the **committed** direction. It is validated
    against the committed direction and never against the pending one, so two
    opposing inputs between two ticks cannot reverse the snake into itself. A
    turn while paused, and a turn after the game has ended, follow the same
    rule; neither is special.
21. Pausing toggles the paused flag.
22. A tick does nothing at all when the status is not `alive` or the game is
    paused — in particular the tick counter does not advance. Otherwise it runs,
    in this order: commit the pending direction, compute the new head cell,
    increment the tick counter, test collisions, then apply growth or the
    ordinary move.
23. **Wall collision.** If the new head cell is outside the playfield the status
    becomes `dead_wall`. The snake is not moved, and the tick still counts.
24. **Self collision.** If the new head cell equals any snake segment except the
    current tail segment, the status becomes `dead_self`, under the same "the
    tick still counts, the snake is not moved" rule. Moving into the cell the
    tail vacates on this same tick is legal and must not end the game. The tail
    is excluded only when the snake is not growing this tick; food never spawns
    on a snake cell, so a growth tick can never target the tail cell.
25. **Growth.** If the new head cell is the food cell, prepend the new head, do
    **not** remove the tail, add `10` to the score, increment food eaten, and
    then place new food per section 6.
26. **Ordinary move.** Otherwise prepend the new head and remove the last
    segment.
27. **Win.** If after a growth tick the snake's length reaches `40 * 20 = 800`
    the status becomes `won`, there is no food, and none is placed.
28. Statuses are exactly `alive`, `dead_wall`, `dead_self`, `won` and `quit`.
29. A restart resets everything in section 5, **re-seeds the generator to the
    original seed** so a restarted game replays the same food sequence, places
    the first food again, and increments the restart count. It does nothing at
    all — not even to the restart count — while the status is `alive`.

## 8. The script format

30. A script is UTF-8 text, one directive per line. Leading and trailing
    whitespace on a line is ignored, as is repeated whitespace between a token
    and its count. Blank lines, and lines whose first non-whitespace character
    is `#`, are ignored entirely.
31. Tokens are case-sensitive and are exactly `UP`, `DOWN`, `LEFT`, `RIGHT`,
    `PAUSE`, `QUIT`, `RESTART` and `TICK`. Only `TICK` takes a count: `TICK`
    means one tick and `TICK <n>` means `n` ticks, where `n` is a positive
    decimal integer.
32. An unrecognised token, a count on a token that takes none, and a `TICK`
    count that is not a positive decimal integer are each a hard error, and the
    program exits `3` per requirement 8.
33. `UP`, `DOWN`, `LEFT` and `RIGHT` turn. `PAUSE` pauses. `RESTART` restarts.
    `TICK <n>` ticks `n` times.
34. While paused a `TICK` is consumed and ignored and the tick counter does not
    advance — which requirement 22 already gives.
35. After the game has ended, `TICK` directives are consumed and ignored, and a
    `TICK <n>` whose game ends partway through discards the rest of that
    directive's ticks.
36. `QUIT` stops the replay immediately. It sets the status to `quit` only if
    the game was still `alive`; a script that dies into a wall and then quits
    still reports `dead_wall`. Directives after a `QUIT` are not applied.
37. When the script is exhausted the replay stops with whatever status the game
    holds, which is `alive` if the game is still running.

## 9. The summary line

38. The one line of standard output is a JSON object with exactly these keys,
    **in this order**, with no whitespace between tokens:

| Key | Type | Value |
|---|---|---|
| `schema` | string | always `tui-snake/1` |
| `seed` | int | the seed the game was built with |
| `width` | int | `40` |
| `height` | int | `20` |
| `ticks` | int | ticks executed in the current game; a restart resets it to 0 |
| `status` | string | one of the five of requirement 28 |
| `score` | int | 10 per food eaten in the current game |
| `length` | int | number of snake segments |
| `food_eaten` | int | food eaten in the current game |
| `paused` | bool | whether the game is paused |
| `restarts` | int | restarts honoured |
| `direction` | string | the committed direction |
| `head` | `[int,int]` | the head cell |
| `food` | `[int,int]` or `null` | the food cell, or `null` when there is none |
| `snake` | array of `[int,int]` | every segment, head first, tail last |
| `board` | string | the rendering below, 819 characters |

39. The `board` string is the playfield rendered row by row, rows joined by a
    single `/`, with `.` for an empty cell, `#` for a snake body segment, `@`
    for the head and `*` for the food. Twenty rows of forty characters and
    nineteen separators is 819 characters.
40. Every number is an integer. Never emit a float, an exponent or a `+` sign.
41. Worked example. Seed `42` and the one-line script `TICK` produce exactly
    this, 1061 bytes, shown wrapped here only for legibility — the real line has
    no breaks in it:

```
{"schema":"tui-snake/1","seed":42,"width":40,"height":20,"ticks":1,"status":"alive","score":0,"length":3,"food_eaten":0,"paused":false,"restarts":0,"direction":"RIGHT","head":[21,10],"food":[34,6],"snake":[[21,10],[20,10],[19,10]],"board":"......................................../......................................../......................................../......................................../......................................../......................................../..................................*...../......................................../......................................../......................................../...................##@................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../......................................../........................................"}
```

If that line does not reproduce byte for byte, something in sections 4 to 9 is
wrong.

## 10. The terminal game

`./snake` with no arguments, or with `--seed <n>` and `--tick-ms <n>`, plays the
game on the terminal. This half is graded by driving the real program under a
pseudo-terminal, so each requirement below is something a driver can see.

42. `--seed <n>` seeds the interactive game exactly as the headless mode does,
    so an interactive game is reproducible too. Absent, the seed is `0`.
43. `--tick-ms <n>` sets the interval between automatic ticks in milliseconds.
    Absent, it is `120`. A value of `0` means the game never ticks on its own
    and advances only when a key is pressed.
44. On start the program switches to the **alternate screen** by writing
    `ESC [ ? 1 0 4 9 h`, and on exit it returns to the normal screen by writing
    `ESC [ ? 1 0 4 9 l`. It leaves the terminal in the mode it found it: raw
    mode, if entered, is undone on every exit path.
45. The program draws the whole playfield. A frame shows the forty-by-twenty
    grid using the same four glyphs as requirement 39 — `.`, `#`, `@` and `*` —
    so the drawn board and the summary's `board` string agree cell for cell.
    Anything else on screen is yours: borders, colour, titles, instructions.
46. A status line is visible while playing and contains the text `Score:`
    followed by the current score as a decimal integer. When the game is paused
    the word `PAUSED` is visible. When the game has ended the word `GAME OVER`
    is visible, and when it is won the word `YOU WIN` is.
47. The arrow keys and `w`, `a`, `s`, `d` all turn, under requirement 20. `p`
    pauses and unpauses. `r` restarts, under requirement 29. `q` quits.
48. `q` exits the process with status `0`, having restored the screen per
    requirement 44. The program must also exit cleanly on end of input.
49. If the terminal is smaller than the playfield needs, the program does not
    crash and does not draw a broken frame. It shows a message containing the
    word `terminal` and waits, redrawing when the terminal grows. Handling
    `SIGWINCH` is one way; polling the size is another.
50. The program never busy-waits. With `--tick-ms 0` and no input it consumes no
    measurable CPU.

## 11. What is not required

There is no menu, no difficulty setting, no high-score file, no configuration
file, no replay viewer, no sound and no colour requirement. A later task extends
this specification with those; this one is the game and its two front ends.

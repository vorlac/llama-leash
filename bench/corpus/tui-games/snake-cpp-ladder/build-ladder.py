#!/usr/bin/env python3
"""Generate the ladder's six seeds from the one reference under reference/.

A rung's seed is the reference with EXACTLY ONE concern replaced by a stub that
still compiles, so the tree the arm receives builds, runs its visible suite
green, and fails only the gauge slice belonging to that rung. Generating them
rather than authoring six trees by hand is what keeps the five untouched
modules byte-identical across rungs: an arm that fails rung 4 and an arm that
passes it were handed the same rng, the same game and the same summary.
"""
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
REF = HERE / "reference"

# Each rung: the module it guts, and the stub body that replaces the parts the
# rung asks for. Everything not named here is copied verbatim.
STUBS = {}

STUBS["rng"] = '''// The generator and food placement (SPEC.md section 4).
//
// NOT IMPLEMENTED. `next()` returns zero and no food is ever placed, so every
// game starts with an empty board and the generator's sequence is a constant.
#pragma once
#include <cstdint>
#include <optional>
#include <vector>

#include "src/board.hpp"

namespace snake {

class Lcg {
public:
    explicit Lcg(std::uint64_t seed) : state_(static_cast<std::uint32_t>(seed % 4294967296ULL)) {}
    std::uint32_t next() { return 0; }

private:
    std::uint32_t state_;
};

inline std::vector<Cell> freeCells(const std::vector<Cell>& snake) {
    (void)snake;
    return {};
}

inline std::optional<Cell> placeFood(const std::vector<Cell>& snake, Lcg& rng) {
    (void)snake;
    (void)rng;
    return std::nullopt;
}

}  // namespace snake
'''

STUBS["game_tick"] = ("    void tick() {\n"
                      "        // NOT IMPLEMENTED: the game never advances.\n"
                      "    }\n")

STUBS["script"] = '''// The script format and the replay (SPEC.md sections 6 and 7).
//
// NOT IMPLEMENTED. Every script parses to nothing, so a replay returns a game
// on which no directive has run.
#pragma once
#include <cstdint>
#include <string>
#include <vector>

#include "src/game.hpp"

namespace snake {

struct Directive {
    std::string token;
    long long count{1};
};

inline bool parseScript(const std::string& text, std::vector<Directive>* out, std::string* error) {
    (void)text;
    (void)error;
    out->clear();
    return true;
}

inline bool replay(std::uint64_t seed, const std::string& text, Game* game, std::string* error) {
    (void)text;
    (void)error;
    *game = Game(seed);
    return true;
}

}  // namespace snake
'''

STUBS["summary"] = '''// The board rendering and the one-line summary (SPEC.md sections 8 and 9).
//
// NOT IMPLEMENTED. The render is an empty string and the summary is an empty
// JSON object.
#pragma once
#include <string>
#include <vector>

#include "src/game.hpp"

namespace snake {

inline std::string render(const Game& game) {
    (void)game;
    return "";
}

inline std::string cellJson(const Cell& c) {
    return "[" + std::to_string(c.x) + "," + std::to_string(c.y) + "]";
}

inline std::string summary(const Game& game) {
    (void)game;
    return "{}";
}

}  // namespace snake
'''

STUBS["tui"] = '''// The terminal front end (SPEC.md section 10).
//
// NOT IMPLEMENTED. `play` returns immediately, so the program has no
// interactive mode at all.
#pragma once
#include <cstdint>

#include "src/game.hpp"
#include "src/summary.hpp"

namespace snake {

inline int play(std::uint64_t seed, int tickMs) {
    (void)seed;
    (void)tickMs;
    return 0;
}

}  // namespace snake
'''


def gut_game_tick(text):
    """Replace Game::tick's body, leaving every other member intact."""
    start = text.index("    void tick() {")
    depth = 0
    i = text.index("{", start)
    while True:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                break
        i += 1
    return text[:start] + STUBS["game_tick"] + text[i + 2:]


RUNGS = [
    ("L1-bootstrap", None),
    ("L2-generator", ("src/rng.hpp", STUBS["rng"])),
    ("L3-rules", ("src/game.hpp", None)),          # handled by gut_game_tick
    ("L4-script", ("src/script.hpp", STUBS["script"])),
    ("L5-summary", ("src/summary.hpp", STUBS["summary"])),
    ("L6-terminal", ("src/tui.hpp", STUBS["tui"])),
]


def main():
    for name, gut in RUNGS:
        seed = HERE / name / "seed"
        if seed.exists():
            shutil.rmtree(seed)
        (seed / "src").mkdir(parents=True, exist_ok=True)
        (seed / "tests").mkdir(parents=True, exist_ok=True)
        (seed / "tools").mkdir(parents=True, exist_ok=True)

        if name == "L1-bootstrap":
            # Nothing but the specification: the rung IS producing a build.
            print("%-14s seed: specification only" % name)
            continue

        for src in sorted((REF / "src").glob("*")):
            shutil.copy(src, seed / "src" / src.name)
        shutil.copy(REF / "build.sh", seed / "build.sh")
        (seed / "build.sh").chmod(0o755)

        path, body = gut
        target = seed / path
        if body is None:
            target.write_text(gut_game_tick(target.read_text()))
        else:
            target.write_text(body)
        print("%-14s seed: reference with %s gutted" % (name, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())

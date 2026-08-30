// The terminal front end (SPEC.md section 10).
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

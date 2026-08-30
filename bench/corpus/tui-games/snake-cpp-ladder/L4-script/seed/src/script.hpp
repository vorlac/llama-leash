// The script format and the replay (SPEC.md sections 6 and 7).
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

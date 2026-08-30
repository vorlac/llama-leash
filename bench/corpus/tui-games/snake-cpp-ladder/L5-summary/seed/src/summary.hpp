// The board rendering and the one-line summary (SPEC.md sections 8 and 9).
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

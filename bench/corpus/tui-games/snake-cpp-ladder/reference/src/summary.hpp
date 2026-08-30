// The board rendering and the one-line summary (SPEC.md sections 8 and 9).
#pragma once
#include <sstream>
#include <string>
#include <vector>

#include "src/game.hpp"

namespace snake {

// Twenty rows of forty glyphs joined by a single '/': 819 characters.
inline std::string render(const Game& game) {
    std::vector<std::string> rows(kHeight, std::string(kWidth, '.'));
    if (game.food()) rows[game.food()->y][game.food()->x] = '*';
    const std::vector<Cell>& body = game.body();
    for (std::size_t i = 0; i < body.size(); ++i) {
        rows[body[i].y][body[i].x] = (i == 0) ? '@' : '#';
    }
    std::string out;
    for (int y = 0; y < kHeight; ++y) {
        if (y) out += '/';
        out += rows[y];
    }
    return out;
}

inline std::string cellJson(const Cell& c) {
    return "[" + std::to_string(c.x) + "," + std::to_string(c.y) + "]";
}

// The sixteen keys, in the order section 9 gives, with no whitespace between
// tokens and every number an integer.
inline std::string summary(const Game& game) {
    std::ostringstream o;
    o << "{\"schema\":\"" << kSchema << "\""
      << ",\"seed\":" << game.seed()
      << ",\"width\":" << kWidth
      << ",\"height\":" << kHeight
      << ",\"ticks\":" << game.ticks()
      << ",\"status\":\"" << game.status() << "\""
      << ",\"score\":" << game.score()
      << ",\"length\":" << game.body().size()
      << ",\"food_eaten\":" << game.eaten()
      << ",\"paused\":" << (game.paused() ? "true" : "false")
      << ",\"restarts\":" << game.restarts()
      << ",\"direction\":\"" << dirName(game.direction()) << "\""
      << ",\"head\":" << cellJson(game.body().front())
      << ",\"food\":" << (game.food() ? cellJson(*game.food()) : std::string("null"))
      << ",\"snake\":[";
    const std::vector<Cell>& body = game.body();
    for (std::size_t i = 0; i < body.size(); ++i) {
        if (i) o << ",";
        o << cellJson(body[i]);
    }
    o << "],\"board\":\"" << render(game) << "\"}";
    return o.str();
}

}  // namespace snake

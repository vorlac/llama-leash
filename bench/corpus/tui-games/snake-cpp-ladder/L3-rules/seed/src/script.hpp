// The script format and the replay (SPEC.md sections 6 and 7).
#pragma once
#include <cstdint>
#include <cstdlib>
#include <sstream>
#include <string>
#include <vector>

#include "src/game.hpp"

namespace snake {

struct Directive {
    std::string token;
    long long count{1};
};

// Returns false and sets `error` on an unknown token, a count on a token that
// takes none, and a TICK count that is not a positive decimal integer.
inline bool parseScript(const std::string& text, std::vector<Directive>* out, std::string* error) {
    static const char* kTokens[] = {"UP", "DOWN", "LEFT", "RIGHT",
                                    "PAUSE", "QUIT", "RESTART", "TICK"};
    out->clear();
    std::istringstream in(text);
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream ls(line);
        std::string token;
        if (!(ls >> token)) continue;          // blank
        if (token[0] == '#') continue;         // comment
        std::string rest;
        const bool hasRest = static_cast<bool>(ls >> rest);
        std::string extra;
        if (ls >> extra) { *error = "trailing token on: " + line; return false; }
        bool known = false;
        for (const char* candidate : kTokens) {
            if (token == candidate) { known = true; break; }
        }
        if (!known) { *error = "unknown token: " + token; return false; }
        if (token != "TICK") {
            if (hasRest) { *error = token + " takes no count"; return false; }
            out->push_back({token, 1});
            continue;
        }
        long long count = 1;
        if (hasRest) {
            if (rest.empty()) { *error = "bad TICK count"; return false; }
            for (const char c : rest) {
                if (c < '0' || c > '9') { *error = "bad TICK count: " + rest; return false; }
            }
            count = std::atoll(rest.c_str());
            if (count <= 0) { *error = "bad TICK count: " + rest; return false; }
        }
        out->push_back({"TICK", count});
    }
    return true;
}

// QUIT stops the replay immediately and sets `quit` only if the game was still
// alive; directives after it are not applied.
inline bool replay(std::uint64_t seed, const std::string& text, Game* game, std::string* error) {
    std::vector<Directive> script;
    if (!parseScript(text, &script, error)) return false;
    *game = Game(seed);
    for (const Directive& d : script) {
        if (d.token == "TICK") {
            for (long long i = 0; i < d.count; ++i) game->tick();
        } else if (d.token == "UP") {
            game->turn(Dir::Up);
        } else if (d.token == "DOWN") {
            game->turn(Dir::Down);
        } else if (d.token == "LEFT") {
            game->turn(Dir::Left);
        } else if (d.token == "RIGHT") {
            game->turn(Dir::Right);
        } else if (d.token == "PAUSE") {
            game->pause();
        } else if (d.token == "RESTART") {
            game->restart();
        } else if (d.token == "QUIT") {
            game->quit();
            break;
        }
    }
    return true;
}

}  // namespace snake

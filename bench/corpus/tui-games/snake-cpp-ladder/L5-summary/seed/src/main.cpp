// The command line: one program, two front ends (SPEC.md sections 2 and 3).
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "src/game.hpp"
#include "src/script.hpp"
#include "src/summary.hpp"
#include "src/tui.hpp"

int main(int argc, char** argv) {
    std::uint64_t seed = 0;
    int tickMs = 120;
    std::string scriptPath;
    bool headless = false;
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--headless") {
            headless = true;
        } else if (arg == "--seed" && i + 1 < argc) {
            seed = std::strtoull(argv[++i], nullptr, 10);
        } else if (arg == "--script" && i + 1 < argc) {
            scriptPath = argv[++i];
        } else if (arg == "--tick-ms" && i + 1 < argc) {
            tickMs = std::atoi(argv[++i]);
        } else if (arg == "--version") {
            std::printf("%s\n", snake::kSchema);
            return 0;
        } else {
            std::fprintf(stderr, "usage: snake [--seed N] [--tick-ms N] "
                                 "[--headless --script PATH] [--version]\n");
            return 2;
        }
    }
    if (!headless) return snake::play(seed, tickMs);

    std::string text;
    if (scriptPath.empty() || scriptPath == "-") {
        std::ostringstream ss;
        ss << std::cin.rdbuf();
        text = ss.str();
    } else {
        std::ifstream file(scriptPath);
        if (!file) {
            std::fprintf(stderr, "cannot open %s\n", scriptPath.c_str());
            return 2;
        }
        std::ostringstream ss;
        ss << file.rdbuf();
        text = ss.str();
    }
    snake::Game game(seed);
    std::string error;
    if (!snake::replay(seed, text, &game, &error)) {
        std::fprintf(stderr, "script error: %s\n", error.c_str());
        return 3;
    }
    std::printf("%s\n", snake::summary(game).c_str());
    return 0;
}

// The generator and food placement (SPEC.md section 4).
#pragma once
#include <cstdint>
#include <optional>
#include <vector>

#include "src/board.hpp"

namespace snake {

class Lcg {
public:
    explicit Lcg(std::uint64_t seed) : state_(static_cast<std::uint32_t>(seed % 4294967296ULL)) {}
    std::uint32_t next() {
        state_ = static_cast<std::uint32_t>((state_ * 1664525ULL + 1013904223ULL) % 4294967296ULL);
        return state_;
    }

private:
    std::uint32_t state_;
};

// Free cells in ascending row-major order, which is the order the placement
// indexes into. Exactly one draw is consumed, and none when the board is full.
inline std::vector<Cell> freeCells(const std::vector<Cell>& snake) {
    std::vector<Cell> free;
    free.reserve(kWidth * kHeight);
    for (int y = 0; y < kHeight; ++y) {
        for (int x = 0; x < kWidth; ++x) {
            bool occupied = false;
            for (const Cell& s : snake) {
                if (s.x == x && s.y == y) { occupied = true; break; }
            }
            if (!occupied) free.push_back({x, y});
        }
    }
    return free;
}

inline std::optional<Cell> placeFood(const std::vector<Cell>& snake, Lcg& rng) {
    const std::vector<Cell> free = freeCells(snake);
    if (free.empty()) return std::nullopt;
    return free[rng.next() % free.size()];
}

}  // namespace snake

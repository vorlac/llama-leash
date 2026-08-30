// The generator and food placement (SPEC.md section 4).
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

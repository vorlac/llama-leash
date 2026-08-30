// The playfield's dimensions and its one value type (SPEC.md section 3).
#pragma once

namespace snake {

inline constexpr int kWidth = 40;
inline constexpr int kHeight = 20;
inline constexpr const char* kSchema = "tui-snake/1";

struct Cell {
    int x{};
    int y{};
    bool operator==(const Cell& other) const { return x == other.x && y == other.y; }
};

}  // namespace snake

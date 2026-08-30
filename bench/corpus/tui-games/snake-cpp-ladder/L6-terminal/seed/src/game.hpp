// The rules (SPEC.md section 5): initial state, turning, and the tick.
#pragma once
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "src/board.hpp"
#include "src/rng.hpp"

namespace snake {

enum class Dir { Up, Down, Left, Right };

inline const char* dirName(Dir d) {
    switch (d) {
        case Dir::Up: return "UP";
        case Dir::Down: return "DOWN";
        case Dir::Left: return "LEFT";
        case Dir::Right: return "RIGHT";
    }
    return "RIGHT";
}
inline Cell delta(Dir d) {
    switch (d) {
        case Dir::Up: return {0, -1};
        case Dir::Down: return {0, 1};
        case Dir::Left: return {-1, 0};
        case Dir::Right: return {1, 0};
    }
    return {1, 0};
}
inline bool opposite(Dir a, Dir b) {
    return (a == Dir::Up && b == Dir::Down) || (a == Dir::Down && b == Dir::Up) ||
           (a == Dir::Left && b == Dir::Right) || (a == Dir::Right && b == Dir::Left);
}

class Game {
public:
    explicit Game(std::uint64_t seed) : seed_(seed), rng_(seed) { reset(); place(); }

    // A restart while alive does nothing at all, not even to the count.
    void restart() {
        if (status_ != "alive") {
            rng_ = Lcg(seed_);
            reset();
            place();
            restarts_ += 1;
        }
    }
    // Validated against the COMMITTED direction, never the pending one, so two
    // opposing inputs between ticks cannot reverse the snake into itself.
    void turn(Dir d) { if (!opposite(d, direction_)) pending_ = d; }
    void pause() { paused_ = !paused_; }
    void quit() { if (status_ == "alive") status_ = "quit"; }

    void tick() {
        if (status_ != "alive" || paused_) return;
        direction_ = pending_;
        const Cell d = delta(direction_);
        const Cell head{snake_.front().x + d.x, snake_.front().y + d.y};
        ticks_ += 1;
        if (head.x < 0 || head.x >= kWidth || head.y < 0 || head.y >= kHeight) {
            status_ = "dead_wall";
            return;
        }
        const bool growing = food_.has_value() && head == *food_;
        // The tail is excluded only when the snake is NOT growing: the cell it
        // vacates this tick is legal to enter.
        const std::size_t last = snake_.size() - (growing ? 0 : 1);
        for (std::size_t i = 0; i < last; ++i) {
            if (snake_[i] == head) { status_ = "dead_self"; return; }
        }
        snake_.insert(snake_.begin(), head);
        if (!growing) { snake_.pop_back(); return; }
        score_ += 10;
        eaten_ += 1;
        if (snake_.size() >= static_cast<std::size_t>(kWidth * kHeight)) {
            status_ = "won";
            food_.reset();
        } else {
            place();
        }
    }

    std::uint64_t seed() const { return seed_; }
    const std::vector<Cell>& body() const { return snake_; }
    Dir direction() const { return direction_; }
    long long score() const { return score_; }
    long long ticks() const { return ticks_; }
    long long eaten() const { return eaten_; }
    long long restarts() const { return restarts_; }
    bool paused() const { return paused_; }
    const std::string& status() const { return status_; }
    const std::optional<Cell>& food() const { return food_; }

private:
    void reset() {
        snake_ = {{20, 10}, {19, 10}, {18, 10}};
        direction_ = Dir::Right;
        pending_ = Dir::Right;
        score_ = 0; ticks_ = 0; eaten_ = 0;
        paused_ = false; status_ = "alive"; food_.reset();
    }
    void place() { food_ = placeFood(snake_, rng_); }

    std::uint64_t seed_;
    Lcg rng_;
    std::vector<Cell> snake_;
    Dir direction_{Dir::Right};
    Dir pending_{Dir::Right};
    long long score_{0}, ticks_{0}, eaten_{0}, restarts_{0};
    bool paused_{false};
    std::string status_{"alive"};
    std::optional<Cell> food_;
};

}  // namespace snake

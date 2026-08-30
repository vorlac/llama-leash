// A complete reference implementation of SPEC.md: the rules, the headless
// replay and the terminal game. Written from the specification alone, with raw
// escape sequences and termios and no third-party dependency, to demonstrate
// that the from-scratch path satisfies every graded requirement.
#include <cerrno>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#include <sys/ioctl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>

namespace snake {

constexpr int kWidth = 40;
constexpr int kHeight = 20;
constexpr const char* kSchema = "tui-snake/1";

struct Cell {
    int x{}, y{};
    bool operator==(const Cell& o) const { return x == o.x && y == o.y; }
};

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
    explicit Game(std::uint64_t seed) : seed_(seed), rng_(seed) { reset(); placeFood(); }

    void restart() {
        if (status_ == "alive") return;
        rng_ = Lcg(seed_);
        reset();
        placeFood();
        restarts_ += 1;
    }
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
        const std::size_t last = snake_.size() - (growing ? 0 : 1);
        for (std::size_t i = 0; i < last; ++i) {
            if (snake_[i] == head) { status_ = "dead_self"; return; }
        }
        snake_.insert(snake_.begin(), head);
        if (growing) {
            score_ += 10;
            foodEaten_ += 1;
            if (snake_.size() >= static_cast<std::size_t>(kWidth * kHeight)) {
                status_ = "won";
                food_.reset();
            } else {
                placeFood();
            }
        } else {
            snake_.pop_back();
        }
    }

    std::string render() const {
        std::vector<std::string> rows(kHeight, std::string(kWidth, '.'));
        if (food_) rows[food_->y][food_->x] = '*';
        for (std::size_t i = 0; i < snake_.size(); ++i)
            rows[snake_[i].y][snake_[i].x] = (i == 0) ? '@' : '#';
        std::string out;
        for (int y = 0; y < kHeight; ++y) { if (y) out += '/'; out += rows[y]; }
        return out;
    }
    std::string summary() const;

    const std::string& status() const { return status_; }
    long long score() const { return score_; }
    bool paused() const { return paused_; }

private:
    void reset() {
        snake_ = {{20, 10}, {19, 10}, {18, 10}};
        direction_ = Dir::Right; pending_ = Dir::Right;
        score_ = 0; ticks_ = 0; foodEaten_ = 0;
        paused_ = false; status_ = "alive"; food_.reset();
    }
    void placeFood() {
        std::vector<Cell> free;
        free.reserve(kWidth * kHeight);
        for (int y = 0; y < kHeight; ++y)
            for (int x = 0; x < kWidth; ++x) {
                bool occupied = false;
                for (const Cell& s : snake_) if (s.x == x && s.y == y) { occupied = true; break; }
                if (!occupied) free.push_back({x, y});
            }
        if (free.empty()) { food_.reset(); return; }
        food_ = free[rng_.next() % free.size()];
    }

    std::uint64_t seed_;
    Lcg rng_;
    std::vector<Cell> snake_;
    Dir direction_{Dir::Right}, pending_{Dir::Right};
    long long score_{0}, ticks_{0}, foodEaten_{0}, restarts_{0};
    bool paused_{false};
    std::string status_{"alive"};
    std::optional<Cell> food_;
};

static std::string cellJson(const Cell& c) {
    return "[" + std::to_string(c.x) + "," + std::to_string(c.y) + "]";
}

std::string Game::summary() const {
    std::ostringstream o;
    o << "{\"schema\":\"" << kSchema << "\",\"seed\":" << seed_
      << ",\"width\":" << kWidth << ",\"height\":" << kHeight
      << ",\"ticks\":" << ticks_ << ",\"status\":\"" << status_ << "\""
      << ",\"score\":" << score_ << ",\"length\":" << snake_.size()
      << ",\"food_eaten\":" << foodEaten_
      << ",\"paused\":" << (paused_ ? "true" : "false")
      << ",\"restarts\":" << restarts_
      << ",\"direction\":\"" << dirName(direction_) << "\""
      << ",\"head\":" << cellJson(snake_.front())
      << ",\"food\":" << (food_ ? cellJson(*food_) : std::string("null"))
      << ",\"snake\":[";
    for (std::size_t i = 0; i < snake_.size(); ++i) { if (i) o << ","; o << cellJson(snake_[i]); }
    o << "],\"board\":\"" << render() << "\"}";
    return o.str();
}

struct Directive { std::string token; long long count{1}; };

std::vector<Directive> parseScript(const std::string& text, std::string* err) {
    std::vector<Directive> out;
    std::istringstream in(text);
    std::string line;
    while (std::getline(in, line)) {
        std::istringstream ls(line);
        std::string tok;
        if (!(ls >> tok)) continue;
        if (tok[0] == '#') continue;
        std::string rest;
        const bool hasRest = static_cast<bool>(ls >> rest);
        std::string extra;
        if (ls >> extra) { *err = "trailing token"; return {}; }
        static const char* kTokens[] = {"UP","DOWN","LEFT","RIGHT","PAUSE","QUIT","RESTART","TICK"};
        bool known = false;
        for (const char* t : kTokens) if (tok == t) { known = true; break; }
        if (!known) { *err = "unknown token " + tok; return {}; }
        if (tok != "TICK") {
            if (hasRest) { *err = tok + " takes no count"; return {}; }
            out.push_back({tok, 1});
            continue;
        }
        long long n = 1;
        if (hasRest) {
            if (rest.empty()) { *err = "bad TICK count"; return {}; }
            for (char c : rest) if (c < '0' || c > '9') { *err = "bad TICK count"; return {}; }
            n = std::atoll(rest.c_str());
            if (n <= 0) { *err = "bad TICK count"; return {}; }
        }
        out.push_back({"TICK", n});
    }
    return out;
}

Game replay(std::uint64_t seed, const std::string& text, std::string* err) {
    Game g(seed);
    const std::vector<Directive> script = parseScript(text, err);
    if (!err->empty()) return g;
    for (const Directive& d : script) {
        if (d.token == "TICK") { for (long long i = 0; i < d.count; ++i) g.tick(); }
        else if (d.token == "UP") g.turn(Dir::Up);
        else if (d.token == "DOWN") g.turn(Dir::Down);
        else if (d.token == "LEFT") g.turn(Dir::Left);
        else if (d.token == "RIGHT") g.turn(Dir::Right);
        else if (d.token == "PAUSE") g.pause();
        else if (d.token == "RESTART") g.restart();
        else if (d.token == "QUIT") { g.quit(); break; }
    }
    return g;
}

// -------------------------------------------------------------------------
// The terminal game (§10)
// -------------------------------------------------------------------------

class Terminal {
public:
    // Raw mode and the alternate screen are entered together and left together,
    // by a destructor rather than by a return path, so every exit restores the
    // terminal — including one taken from an error branch added later.
    Terminal() {
        if (tcgetattr(STDIN_FILENO, &saved_) == 0) {
            struct termios raw = saved_;
            raw.c_lflag &= ~static_cast<tcflag_t>(ECHO | ICANON | ISIG);
            raw.c_iflag &= ~static_cast<tcflag_t>(IXON | ICRNL);
            raw.c_cc[VMIN] = 0;
            raw.c_cc[VTIME] = 0;
            tcsetattr(STDIN_FILENO, TCSAFLUSH, &raw);
            restore_ = true;
        }
        write("\x1b[?1049h\x1b[?25l");
    }
    ~Terminal() {
        write("\x1b[?25h\x1b[?1049l");
        if (restore_) tcsetattr(STDIN_FILENO, TCSAFLUSH, &saved_);
    }
    static void write(const std::string& s) {
        ssize_t n = ::write(STDOUT_FILENO, s.data(), s.size());
        (void)n;
    }
    static void size(int* cols, int* rows) {
        struct winsize ws {};
        if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_col && ws.ws_row) {
            *cols = ws.ws_col; *rows = ws.ws_row;
        } else { *cols = 80; *rows = 24; }
    }
private:
    struct termios saved_ {};
    bool restore_{false};
};

static std::string frame(const Game& g) {
    std::string out = "\x1b[H\x1b[2J";
    const std::string board = g.render();
    std::size_t start = 0;
    while (true) {
        const std::size_t slash = board.find('/', start);
        out += board.substr(start, slash == std::string::npos ? std::string::npos : slash - start);
        out += "\r\n";
        if (slash == std::string::npos) break;
        start = slash + 1;
    }
    out += "Score: " + std::to_string(g.score());
    if (g.paused()) out += "   PAUSED";
    if (g.status() == "dead_wall" || g.status() == "dead_self") out += "   GAME OVER";
    if (g.status() == "won") out += "   YOU WIN";
    out += "   [wasd/arrows] move  [p] pause  [r] restart  [q] quit\r\n";
    return out;
}

int play(std::uint64_t seed, int tickMs) {
    Terminal term;
    Game game(seed);
    bool tooSmall = false;
    for (;;) {
        int cols = 0, rows = 0;
        Terminal::size(&cols, &rows);
        if (cols < kWidth || rows < kHeight + 2) {
            if (!tooSmall) {
                Terminal::write("\x1b[H\x1b[2J"
                                "This terminal is too small: snake needs 40x22, "
                                "this terminal is " + std::to_string(cols) + "x" +
                                std::to_string(rows) + ".\r\nResize the terminal to "
                                "continue, or press q to quit.\r\n");
                tooSmall = true;
            }
        } else {
            Terminal::write(frame(game));
            tooSmall = false;
        }

        // One blocking wait serves both the keyboard and the clock, so an idle
        // game at --tick-ms 0 consumes nothing at all (§10 r50).
        fd_set fds;
        FD_ZERO(&fds);
        FD_SET(STDIN_FILENO, &fds);
        struct timeval tv {};
        struct timeval* timeout = nullptr;
        if (tickMs > 0) {
            tv.tv_sec = tickMs / 1000;
            tv.tv_usec = (tickMs % 1000) * 1000;
            timeout = &tv;
        } else if (tooSmall) {
            tv.tv_sec = 0; tv.tv_usec = 200000;   // poll for a resize
            timeout = &tv;
        }
        const int ready = select(STDIN_FILENO + 1, &fds, nullptr, nullptr, timeout);
        if (ready < 0) { if (errno == EINTR) continue; return 0; }

        if (ready > 0 && FD_ISSET(STDIN_FILENO, &fds)) {
            char buf[64];
            const ssize_t n = ::read(STDIN_FILENO, buf, sizeof buf);
            if (n <= 0) return 0;            // end of input (§10 r48)
            for (ssize_t i = 0; i < n; ++i) {
                const char c = buf[i];
                if (c == 'q' || c == 'Q') return 0;
                if (c == 'p' || c == 'P') { game.pause(); continue; }
                if (c == 'r' || c == 'R') { game.restart(); continue; }
                if (c == 'w' || c == 'W') { game.turn(Dir::Up); continue; }
                if (c == 'a' || c == 'A') { game.turn(Dir::Left); continue; }
                if (c == 's' || c == 'S') { game.turn(Dir::Down); continue; }
                if (c == 'd' || c == 'D') { game.turn(Dir::Right); continue; }
                if (c == '\x1b' && i + 2 < n && buf[i + 1] == '[') {
                    switch (buf[i + 2]) {
                        case 'A': game.turn(Dir::Up); break;
                        case 'B': game.turn(Dir::Down); break;
                        case 'C': game.turn(Dir::Right); break;
                        case 'D': game.turn(Dir::Left); break;
                        default: break;
                    }
                    i += 2;
                }
            }
            // §10 r43: at --tick-ms 0 the game advances only on input.
            if (tickMs == 0 && !tooSmall) game.tick();
        } else if (tickMs > 0 && !tooSmall) {
            game.tick();
        }
    }
}

}  // namespace snake

int main(int argc, char** argv) {
    std::uint64_t seed = 0;
    int tickMs = 120;
    std::string scriptPath;
    bool headless = false;
    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--headless") headless = true;
        else if (a == "--seed" && i + 1 < argc) seed = std::strtoull(argv[++i], nullptr, 10);
        else if (a == "--script" && i + 1 < argc) scriptPath = argv[++i];
        else if (a == "--tick-ms" && i + 1 < argc) tickMs = std::atoi(argv[++i]);
        else { std::fprintf(stderr, "usage: snake [--seed N] [--tick-ms N] "
                                    "[--headless --script PATH]\n"); return 2; }
    }
    if (!headless) return snake::play(seed, tickMs);

    std::string text;
    if (scriptPath.empty() || scriptPath == "-") {
        std::ostringstream ss; ss << std::cin.rdbuf(); text = ss.str();
    } else {
        std::ifstream f(scriptPath);
        if (!f) { std::fprintf(stderr, "cannot open %s\n", scriptPath.c_str()); return 2; }
        std::ostringstream ss; ss << f.rdbuf(); text = ss.str();
    }
    std::string err;
    const snake::Game g = snake::replay(seed, text, &err);
    if (!err.empty()) { std::fprintf(stderr, "script error: %s\n", err.c_str()); return 3; }
    std::printf("%s\n", g.summary().c_str());
    return 0;
}

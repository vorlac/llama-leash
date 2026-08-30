// The terminal front end (SPEC.md section 10).
#pragma once
#include <cerrno>
#include <string>

#include <sys/ioctl.h>
#include <sys/select.h>
#include <termios.h>
#include <unistd.h>

#include "src/game.hpp"
#include "src/summary.hpp"

namespace snake {

// Raw mode and the alternate screen are entered together and left by a
// destructor rather than by a return path, so every exit restores the terminal
// — including one taken from a branch added later.
class Terminal {
public:
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
        const ssize_t n = ::write(STDOUT_FILENO, s.data(), s.size());
        (void)n;
    }
    static void size(int* cols, int* rows) {
        struct winsize ws {};
        if (ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_col && ws.ws_row) {
            *cols = ws.ws_col;
            *rows = ws.ws_row;
        } else {
            *cols = 80;
            *rows = 24;
        }
    }

private:
    struct termios saved_ {};
    bool restore_{false};
};

inline std::string frame(const Game& game) {
    std::string out = "\x1b[H\x1b[2J";
    const std::string board = render(game);
    std::size_t start = 0;
    for (;;) {
        const std::size_t slash = board.find('/', start);
        out += board.substr(start, slash == std::string::npos ? std::string::npos : slash - start);
        out += "\r\n";
        if (slash == std::string::npos) break;
        start = slash + 1;
    }
    out += "Score: " + std::to_string(game.score());
    if (game.paused()) out += "   PAUSED";
    if (game.status() == "dead_wall" || game.status() == "dead_self") out += "   GAME OVER";
    if (game.status() == "won") out += "   YOU WIN";
    out += "   [wasd/arrows] move  [p] pause  [r] restart  [q] quit\r\n";
    return out;
}

inline int play(std::uint64_t seed, int tickMs) {
    Terminal term;
    Game game(seed);
    bool tooSmall = false;
    for (;;) {
        int cols = 0, rows = 0;
        Terminal::size(&cols, &rows);
        if (cols < kWidth || rows < kHeight + 2) {
            if (!tooSmall) {
                Terminal::write("\x1b[H\x1b[2JThis terminal is too small: snake needs 40x22, "
                                "this one is " + std::to_string(cols) + "x" +
                                std::to_string(rows) + ".\r\nResize it to continue, or press q "
                                "to quit.\r\n");
                tooSmall = true;
            }
        } else {
            Terminal::write(frame(game));
            tooSmall = false;
        }

        // One blocking wait serves the keyboard and the clock together, so an
        // idle game at --tick-ms 0 consumes nothing at all.
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
            tv.tv_sec = 0;
            tv.tv_usec = 200000;   // poll for a resize
            timeout = &tv;
        }
        const int ready = select(STDIN_FILENO + 1, &fds, nullptr, nullptr, timeout);
        if (ready < 0) {
            if (errno == EINTR) continue;
            return 0;
        }
        if (ready > 0 && FD_ISSET(STDIN_FILENO, &fds)) {
            char buf[64];
            const ssize_t n = ::read(STDIN_FILENO, buf, sizeof buf);
            if (n <= 0) return 0;   // end of input
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
            if (tickMs == 0 && !tooSmall) game.tick();   // advances only on input
        } else if (tickMs > 0 && !tooSmall) {
            game.tick();
        }
    }
}

}  // namespace snake

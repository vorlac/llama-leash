"""The terminal half — SPEC.md section 10, driven under a pseudo-terminal.

The corpus's own note on the headless snake says a third of its rubric — the
terminal hygiene and the loop discipline — is unmeasurable in a headless cell,
and does not measure it. It is measurable; it just needs a pty rather than a
pipe. Everything here spawns the REAL program on a real terminal device, sends
real keystrokes, and reads what was drawn.

Every assertion waits for bytes to APPEAR and never for them to stop arriving,
so a slow machine costs seconds and never a verdict. The one thing given a hard
deadline is the exit after `q`, and that deadline is the requirement.

`--tick-ms 0` is used wherever the frame has to hold still: requirement 43 makes
the game advance only on input, so a frame read after a keystroke is the frame
that keystroke produced and not one the clock moved underneath it.
"""

import os
import pty
import re
import select
import signal
import struct
import sys
import termios
import time
import unittest
import fcntl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snakegauge  # noqa: E402

ALT_ENTER = "\x1b[?1049h"
ALT_LEAVE = "\x1b[?1049l"
SETTLE_S = 12.0     # how long to wait for expected bytes to appear
EXIT_S = 10.0       # how long `q` may take to end the process


class Terminal:
    """A child on a pty, with a byte buffer that only grows."""

    def __init__(self, args, cols=100, rows=40, stdin_at_eof=False):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:  # child
            os.environ["TERM"] = "xterm-256color"
            os.environ["LINES"] = str(rows)
            os.environ["COLUMNS"] = str(cols)
            if stdin_at_eof:
                # Output stays on the pty — it is still a terminal and still
                # draws — while input is already at end of file. Closing the
                # MASTER instead would tear the terminal down and kill the child
                # with a signal mid-write, which says nothing about how it
                # handles end of input.
                null = os.open(os.devnull, os.O_RDONLY)
                os.dup2(null, 0)
                os.close(null)
            try:
                os.execv(snakegauge.binary(), [snakegauge.binary()] + list(args))
            except Exception:
                os._exit(127)
        self.resize(cols, rows)
        self.buf = ""

    def resize(self, cols, rows):
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ,
                    struct.pack("HHHH", rows, cols, 0, 0))

    def drain(self, seconds=0.25):
        deadline = time.time() + seconds
        while time.time() < deadline:
            r, _, _ = select.select([self.fd], [], [], max(0.0, deadline - time.time()))
            if not r:
                break
            try:
                chunk = os.read(self.fd, 65536)
            except OSError:
                break
            if not chunk:
                break
            self.buf += chunk.decode("utf-8", errors="replace")
        return self.buf

    def wait_for(self, predicate, seconds=SETTLE_S):
        """Read until `predicate(buffer)` holds, or the time is up."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            if predicate(self.buf):
                return True
            self.drain(0.2)
        return predicate(self.buf)

    def send(self, keys):
        os.write(self.fd, keys.encode())

    def wait_exit(self, seconds=EXIT_S):
        """The child's exit status, or None if it outlived the deadline."""
        deadline = time.time() + seconds
        while time.time() < deadline:
            self.drain(0.15)
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid:
                if os.WIFEXITED(status):
                    return os.WEXITSTATUS(status)
                return -os.WTERMSIG(status) if os.WIFSIGNALED(status) else None
        return None

    def close(self):
        try:
            os.kill(self.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        try:
            os.close(self.fd)
        except OSError:
            pass


def board_rows(text):
    """Every forty-glyph row drawn so far, escapes stripped, in order."""
    rows = []
    for line in re.split(r"[\r\n]", text):
        stripped = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", line)
        match = re.search(r"[.#@*]{40}", stripped)
        if match:
            rows.append(match.group(0))
    return rows


def last_head(text):
    """The head cell of the most recently drawn frame, or None.

    Reading the head out of the DRAWN board is what lets a turn be checked at
    all. Asserting only that something was redrawn passes an implementation
    that redraws on every keystroke and turns on none of them — which is a real
    program someone will write, since at `--tick-ms 0` the tick and the redraw
    are triggered by the same event.
    """
    rows = board_rows(text)
    if len(rows) < 20:
        return None
    frame = rows[-20:]                       # the latest complete frame
    for y, row in enumerate(frame):
        x = row.find("@")
        if x >= 0:
            return (x, y)
    return None


def looks_like_a_board(text):
    """A drawn playfield: a run of forty board glyphs on one line.

    Deliberately loose about everything else. Borders, colour, a title and a
    legend are all permitted by requirement 45, so the test looks for the grid
    and not for a layout.
    """
    for line in re.split(r"[\r\n]", text):
        stripped = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", line)
        if re.search(r"[.#@*]{40}", stripped):
            return True
    return False


class TerminalGame(unittest.TestCase):
    def setUp(self):
        snakegauge.require_build(self)
        self.term = None

    def tearDown(self):
        if self.term is not None:
            self.term.close()

    def start(self, *args, cols=100, rows=40):
        self.term = Terminal(args, cols=cols, rows=rows)
        return self.term

    def test_enters_the_alternate_screen_and_draws_the_board(self):
        """[snake-tui-r44, r45] the alternate screen, then a forty-wide field."""
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(lambda b: ALT_ENTER in b),
                        "SPEC.md requirement 44: never wrote the alternate-screen "
                        "sequence ESC[?1049h. Got %d bytes:\n%r"
                        % (len(term.buf), term.buf[:600]))
        self.assertTrue(term.wait_for(looks_like_a_board),
                        "SPEC.md requirement 45: no forty-cell row of . # @ * was "
                        "ever drawn. Got %d bytes:\n%r" % (len(term.buf), term.buf[-800:]))

    def test_status_line_shows_the_score(self):
        """[snake-tui-r46] a status line carrying `Score:` and an integer."""
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(
            term.wait_for(lambda b: re.search(r"Score:\s*\d+", b) is not None),
            "SPEC.md requirement 46: no `Score: <n>` anywhere in %d bytes:\n%r"
            % (len(term.buf), term.buf[-800:]),
        )

    def test_p_pauses_and_says_so(self):
        """[snake-tui-r46, r47] `p` pauses and the word PAUSED becomes visible."""
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(looks_like_a_board), "never drew a board")
        before = len(term.buf)
        term.send("p")
        self.assertTrue(
            term.wait_for(lambda b: "PAUSED" in b[before:]),
            "SPEC.md requirement 46: `p` produced no PAUSED. Bytes since the "
            "keystroke:\n%r" % term.buf[before:][:800],
        )

    def _head_after(self, term, key):
        """Send one key at --tick-ms 0 and return the head of the frame it drew."""
        before = len(term.buf)
        term.send(key)
        term.wait_for(lambda b: len(board_rows(b[before:])) >= 20, seconds=SETTLE_S)
        return last_head(term.buf)

    def test_wasd_turns_the_snake(self):
        """[snake-tui-r43, r47] `w`, `a`, `s`, `d` each turn, per requirement 20.

        The head is read out of the drawn frame, so a program that redraws on a
        keystroke without turning fails here. `w` from the initial RIGHT is a
        legal turn; the head must go UP, not right.
        """
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(lambda b: last_head(b) is not None),
                        "never drew a board with a head in it")
        start = last_head(term.buf)
        self.assertEqual(start, (20, 10),
                         "SPEC.md requirement 11: the first frame's head is (20,10), got %r"
                         % (start,))
        up = self._head_after(term, "w")
        self.assertEqual(up, (20, 9),
                         "SPEC.md requirement 47: `w` should turn UP and tick to (20,9), "
                         "the head is at %r" % (up,))
        left = self._head_after(term, "a")
        self.assertEqual(left, (19, 9),
                         "SPEC.md requirement 47: `a` should turn LEFT to (19,9), got %r"
                         % (left,))
        down = self._head_after(term, "s")
        self.assertEqual(down, (19, 10),
                         "SPEC.md requirement 47: `s` should turn DOWN to (19,10), got %r"
                         % (down,))

    def test_arrow_keys_turn_the_snake(self):
        """[snake-tui-r47] the arrow keys turn too, and are not swallowed as ESC."""
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(lambda b: last_head(b) is not None), "never drew a board")
        up = self._head_after(term, "\x1b[A")
        self.assertEqual(up, (20, 9),
                         "SPEC.md requirement 47: the up arrow should turn UP to (20,9), "
                         "got %r — an escape sequence read as a bare ESC looks like this"
                         % (up,))
        right = self._head_after(term, "\x1b[C")
        self.assertEqual(right, (21, 9),
                         "SPEC.md requirement 47: the right arrow should reach (21,9), got %r"
                         % (right,))

    def test_a_reversing_key_is_refused(self):
        """[snake-tui-r20, r47] `a` from a committed RIGHT must not reverse the snake.

        The turn rule is the same one the headless mode is graded on; this row
        checks the terminal front end is routed through it rather than through a
        second, laxer copy.
        """
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(lambda b: last_head(b) is not None), "never drew a board")
        head = self._head_after(term, "a")
        self.assertEqual(
            head, (21, 10),
            "SPEC.md requirement 20: LEFT is the exact opposite of the committed "
            "RIGHT, so the snake must keep going right to (21,10); the head is at %r"
            % (head,),
        )

    def test_q_quits_cleanly_and_restores_the_screen(self):
        """[snake-tui-r44, r48] `q` exits 0 and leaves the alternate screen."""
        term = self.start("--seed", "42", "--tick-ms", "0")
        self.assertTrue(term.wait_for(looks_like_a_board), "never drew a board")
        term.send("q")
        code = term.wait_exit()
        self.assertIsNotNone(
            code, "SPEC.md requirement 48: still running %.0fs after `q`" % EXIT_S)
        self.assertEqual(code, 0, "SPEC.md requirement 48: `q` exited %r, wanted 0" % code)
        self.assertIn(ALT_LEAVE, term.buf,
                      "SPEC.md requirement 44: exited without writing ESC[?1049l, so "
                      "the terminal is left on the alternate screen")

    def test_a_terminal_too_small_is_reported_and_not_drawn_into(self):
        """[snake-tui-r49] a 30x8 terminal gets a message and NO broken frame.

        The load-bearing half is the negative one. Asking only for the word
        `terminal` is satisfied by any help line that happens to contain it, so
        the assertion that discriminates is that a forty-wide row was never
        drawn into a thirty-column terminal.
        """
        term = self.start("--seed", "42", "--tick-ms", "0", cols=30, rows=8)
        found = term.wait_for(lambda b: "terminal" in b.lower(), seconds=6.0)
        term.drain(1.0)
        self.assertFalse(
            looks_like_a_board(term.buf),
            "SPEC.md requirement 49: drew a forty-cell row into a thirty-column "
            "terminal, which is the broken frame the requirement forbids:\n%r"
            % term.buf[-800:],
        )
        self.assertTrue(
            found,
            "SPEC.md requirement 49: a 30x8 terminal produced no message naming "
            "`terminal`. Got %d bytes:\n%r" % (len(term.buf), term.buf[-800:]),
        )
        self.assertIsNone(term.wait_exit(seconds=1.0),
                          "SPEC.md requirement 49: exited instead of waiting for "
                          "the terminal to grow")

    def test_a_grown_terminal_is_redrawn(self):
        """[snake-tui-r49] once the terminal is big enough the board appears.

        The other half of the same requirement: a program that prints the
        message and then never looks again satisfies the row above and fails
        the user.
        """
        term = self.start("--seed", "42", "--tick-ms", "0", cols=30, rows=8)
        self.assertTrue(term.wait_for(lambda b: "terminal" in b.lower(), seconds=6.0),
                        "no too-small message to begin with")
        term.resize(100, 40)
        term.send("d")  # a keystroke a polling implementation would also wake on
        self.assertTrue(
            term.wait_for(looks_like_a_board, seconds=SETTLE_S),
            "SPEC.md requirement 49: the terminal grew to 100x40 and no board was "
            "ever drawn:\n%r" % term.buf[-800:],
        )

    def test_end_of_input_exits_cleanly(self):
        """[snake-tui-r48] input already at end of file: draw, then exit 0.

        Output is a real terminal throughout, so the program takes its normal
        drawing path; only stdin is at end of file. A loop that ignores the
        zero-length read spins on it forever and trips the deadline, and one
        that treats it as a fatal error exits non-zero — both are the failure
        this row is looking for, and the exit status is what separates them.
        """
        self.term = Terminal(("--seed", "42", "--tick-ms", "0"), stdin_at_eof=True)
        code = self.term.wait_exit(seconds=EXIT_S)
        self.assertIsNotNone(
            code, "SPEC.md requirement 48: still running %.0fs after end of input, "
                  "which is a loop spinning on a zero-length read" % EXIT_S)
        self.assertEqual(
            code, 0,
            "SPEC.md requirement 48: end of input ended the process with status %r, "
            "wanted a clean 0" % code,
        )
        self.assertIn(ALT_LEAVE, self.term.buf,
                      "SPEC.md requirement 44: ended without writing ESC[?1049l, so "
                      "the terminal is left on the alternate screen")


if __name__ == "__main__":
    unittest.main()

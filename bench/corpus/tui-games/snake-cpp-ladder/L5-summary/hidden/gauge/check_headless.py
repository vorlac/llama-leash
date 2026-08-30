"""The rules, driven through the headless mode — SPEC.md sections 3 to 9.

Every expectation here is a byte string produced by
`gauge/reference/ref.cpp`, which reproduces both generator sequences of
requirement 14, all three first-food cells of requirement 18 and the 1061-byte
worked example of requirement 41. Nothing is compared against output the work
tree was told to generate.

The scripts run four different seeds, so an implementation that hardcodes the
worked example passes exactly one case and fails the rest.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import snakegauge  # noqa: E402

DATA = snakegauge.vectors()


class HeadlessOutput(unittest.TestCase):
    def setUp(self):
        snakegauge.require_build(self)

    def test_one_line_and_a_clean_exit(self):
        """[snake-tui-r5] one line of JSON on stdout, a trailing newline, exit 0."""
        code, out, err = snakegauge.headless(42, "TICK\n")
        self.assertEqual(code, 0, "exit %r; stderr: %s" % (code, err[-2000:]))
        self.assertTrue(out.endswith("\n"), "the line must end with a newline")
        self.assertEqual(out.count("\n"), 1,
                         "SPEC.md requirement 5: exactly one line on stdout, got %d"
                         % out.count("\n"))

    def test_stdout_carries_nothing_but_the_summary(self):
        """[snake-tui-r6] diagnostics go to stderr, never to stdout."""
        code, out, _ = snakegauge.headless(42, "TICK 3\n")
        self.assertEqual(code, 0)
        json.loads(out)  # the whole of stdout must parse, so nothing rides beside it

    def test_key_order_is_the_specified_order(self):
        """[snake-tui-r38] the sixteen keys appear in the order section 9 gives."""
        code, out, _ = snakegauge.headless(42, "TICK\n")
        self.assertEqual(code, 0)
        parsed = json.loads(out, object_pairs_hook=list)
        self.assertEqual(
            [k for k, _ in parsed],
            ["schema", "seed", "width", "height", "ticks", "status", "score",
             "length", "food_eaten", "paused", "restarts", "direction", "head",
             "food", "snake", "board"],
        )

    def test_board_is_819_characters(self):
        """[snake-tui-r39] twenty rows of forty, nineteen separators."""
        code, out, _ = snakegauge.headless(7, "TICK 4\n")
        self.assertEqual(code, 0)
        board = json.loads(out)["board"]
        self.assertEqual(len(board), 819)
        rows = board.split("/")
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(len(r) == 40 for r in rows))
        self.assertEqual(set(board) - {"/"} <= set(".#@*"), True,
                         "the board uses only . # @ * and the / separator")

    def test_script_errors_exit_three_with_no_stdout(self):
        """[snake-tui-r8, r32] a bad script is exit 3 and silence on stdout."""
        for case in DATA["scriptErrors"]:
            with self.subTest(case["name"]):
                code, out, _ = snakegauge.headless(case["seed"], case["script"])
                self.assertEqual(code, 3,
                                 "%s: SPEC.md requirement 8 wants exit 3, got %r"
                                 % (case["name"], code))
                self.assertEqual(out, "",
                                 "%s: nothing may go to stdout on a script error"
                                 % case["name"])


def _vector_test(vector):
    def test(self):
        snakegauge.require_build(self)
        code, out, err = snakegauge.headless(vector["seed"], vector["script"])
        self.assertEqual(code, 0, "exit %r; stderr: %s" % (code, err[-2000:]))
        if out == vector["expect"]:
            return
        # A byte diff over a 1061-character line is unreadable, so say WHICH
        # field disagrees before falling back to the bytes.
        try:
            got, want = json.loads(out), json.loads(vector["expect"])
        except ValueError:
            self.fail("%s: stdout is not JSON:\n%r" % (vector["name"], out[:400]))
        wrong = [k for k in want if got.get(k) != want[k]]
        detail = "\n".join(
            "  %-11s expected %r\n  %-11s got      %r"
            % (k, want[k] if k != "board" else "<819 chars>",
               "", got.get(k) if k != "board" else "<%d chars>" % len(str(got.get(k))))
            for k in wrong
        )
        self.fail("%s (seed %d): %d field(s) differ\n%s"
                  % (vector["name"], vector["seed"], len(wrong), detail))
    return test


for _v in DATA["vectors"]:
    setattr(HeadlessOutput, "test_vector_" + _v["name"].replace("-", "_"), _vector_test(_v))


if __name__ == "__main__":
    unittest.main()

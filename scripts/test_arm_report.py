"""Tests for the arm comparison report.

The report's job is to let a reader see, on one page, what the stock model did
with a prompt and what the full harness did with the same prompt. Two properties
carry that and are easy to break silently: a file the model never touched must
not be presented as its work, and an arm that produced nothing must SAY so rather
than render an empty section a reader will read as "no diff shown".
"""

import json
import tempfile
import unittest
from pathlib import Path

from arm_report import outcome_line, source_files


class SourceFilesTest(unittest.TestCase):
    def test_harness_furniture_is_not_the_model_s_work(self):
        """.git, .conductor and the hidden gauge are not what an arm produced."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src").mkdir()
            (root / ".git").mkdir()
            (root / ".conductor").mkdir()
            (root / "gauge").mkdir()
            (root / "src/a.ts").write_text("export const a = 1;\n")
            (root / ".git/config").write_text("[core]\n")
            (root / ".conductor/config.json").write_text("{}")
            (root / "gauge/spec.test.ts").write_text("hidden")

            found = source_files(root)
            self.assertEqual(sorted(found), ["src/a.ts"])

    def test_the_gauge_is_reachable_when_asked_for_explicitly(self):
        """The report shows the hidden test once, as its own section."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gauge").mkdir()
            (root / "gauge/spec.test.ts").write_text("hidden")
            self.assertEqual(sorted(source_files(root, include_gauge=True)), ["gauge/spec.test.ts"])

    def test_a_missing_tree_is_empty_rather_than_an_error(self):
        """The work root is cleared between epochs; an absent cell is normal."""
        self.assertEqual(source_files(Path("/nonexistent/cell/repo")), {})


class OutcomeLineTest(unittest.TestCase):
    def test_a_timeout_is_never_reported_as_a_failure_to_pass(self):
        """D01's distinction: a timed-out cell is its own outcome."""
        line = outcome_line(
            {"timedOut": True, "passed": False, "wallClockMs": 1_800_000,
             "gauge": {"passed": False}, "waves": 4},
            11020,
        )
        self.assertIn("TIMED OUT", line)
        self.assertIn("30.0 min", line)
        self.assertIn("11,020 generated tokens", line)

    def test_a_pass_reports_the_hidden_verdict_not_the_visible_one(self):
        line = outcome_line(
            {"timedOut": False, "passed": True, "wallClockMs": 102_000,
             "gauge": {"passed": True}},
            614,
        )
        self.assertIn("**PASS**", line)
        self.assertIn("hidden tests: pass", line)

    def test_a_cell_with_no_session_store_omits_tokens_rather_than_showing_zero(self):
        """A cleared work root must not read as 'this arm generated nothing'."""
        line = outcome_line({"passed": True, "wallClockMs": 60_000, "gauge": {"passed": True}}, None)
        # The property is that no token figure is printed at all. Do not also
        # assert on a bare substring like "0 " — "1.0 min" contains it, and an
        # assertion that passes for a reason unrelated to its name is worse than
        # no assertion.
        self.assertNotIn("generated tokens", line)
        self.assertIn("**PASS**", line)

    def test_an_unrun_cell_says_so(self):
        self.assertIn("not run", outcome_line(None, None))


if __name__ == "__main__":
    unittest.main()

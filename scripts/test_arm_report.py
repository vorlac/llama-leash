"""Tests for the arm comparison report.

The report's job is to let a reader see, on one page, what the stock model did
with a prompt and what the full harness did with the same prompt. Two properties
carry that and are easy to break silently: a file the model never touched must
not be presented as its work, and an arm that produced nothing must SAY so rather
than render an empty section a reader will read as "no diff shown".
"""

import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from arm_report import (
    STALE_TREE_TOLERANCE_S,
    outcome_line,
    seed_files,
    source_files,
    tree_matches_result,
)


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


class StaleTreeTest(unittest.TestCase):
    """The report must refuse to pair a result with another run's tree.

    run_and_watch.py clears the work root at the START of every epoch, so the
    trees on disk always belong to the most recent run while a results directory
    can name any earlier one. The first version of this report happily paired
    them: epoch 12's wall clock beside epoch 13's source and token count, on one
    line, entirely plausible. A review artifact that shows the wrong code is worse
    than no review artifact.
    """

    def _cell(self, tmp):
        cell = Path(tmp) / "r1"
        (cell / "repo").mkdir(parents=True)
        return cell

    def test_a_tree_born_with_its_result_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            cell = self._cell(tmp)
            born = cell.stat().st_birthtime if hasattr(cell.stat(), "st_birthtime") else cell.stat().st_mtime
            started = datetime.fromtimestamp(born, tz=timezone.utc).isoformat()
            self.assertTrue(tree_matches_result(cell, {"startedIso": started}))

    def test_a_tree_from_another_epoch_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            cell = self._cell(tmp)
            stale = datetime.fromtimestamp(0, tz=timezone.utc).isoformat()
            self.assertFalse(tree_matches_result(cell, {"startedIso": stale}))

    def test_the_tolerance_spans_a_long_cell_but_not_a_later_epoch(self):
        """A 60-minute T2 cell starts well before it ends; an epoch is hours."""
        self.assertGreaterEqual(STALE_TREE_TOLERANCE_S, 3600.0)

    def test_a_missing_tree_or_an_unusable_timestamp_never_matches(self):
        self.assertFalse(tree_matches_result(Path("/nonexistent/r1"), {"startedIso": "2026-01-01T00:00:00Z"}))
        with tempfile.TemporaryDirectory() as tmp:
            cell = self._cell(tmp)
            for record in (None, {}, {"startedIso": ""}, {"startedIso": "not a date"}):
                self.assertFalse(tree_matches_result(cell, record), record)


class SeedFilesTest(unittest.TestCase):
    """Two manifests, two dialects, one report.

    `bench/conductor-tasks.json` carries its seed inline as `seedFiles`; every
    `bench/corpus-*.json` names a `seedDir` on disk instead. A report that knows
    only the first renders "What it started from (0 file(s))" for an eight-file
    seed, and 0 reads as "the arm started from nothing" rather than as "this
    reader does not speak this dialect".
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="seed-files-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def test_the_inline_dialect_is_returned_as_is(self):
        task = {"id": "t", "seedFiles": {"src/a.py": "print(1)\n"}}
        self.assertEqual(seed_files(task, self.tmp), {"src/a.py": "print(1)\n"})

    def test_a_seed_dir_is_read_from_disk(self):
        seed = self.tmp / "bench" / "corpus" / "seed"
        (seed / "src").mkdir(parents=True)
        (seed / "src" / "registry.py").write_text("REG = {}\n")
        (seed / "README.md").write_text("hello\n")
        task = {"id": "t", "seedDir": "bench/corpus/seed"}
        self.assertEqual(
            seed_files(task, self.tmp),
            {"README.md": "hello\n", "src/registry.py": "REG = {}\n"},
        )

    def test_a_task_with_neither_is_genuinely_empty(self):
        self.assertEqual(seed_files({"id": "t"}, self.tmp), {})

    def test_a_seed_dir_that_does_not_exist_is_reported_as_missing(self):
        """Absent on disk and absent from the manifest must not read alike."""
        task = {"id": "t", "seedDir": "bench/corpus/gone"}
        with self.assertRaises(FileNotFoundError):
            seed_files(task, self.tmp)

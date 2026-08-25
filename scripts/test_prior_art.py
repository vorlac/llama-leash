"""Tests for the prior-art search.

The corpus test below is the point of the module: four times in one campaign
session a defect was recorded as a discovery when the answer was already written
down. Each of those four is a search term here. If one stops returning anything,
either the note was deleted or the search stopped reaching it — and both are
worth failing over, because the tool's only value is finding them.
"""

import tempfile
import unittest
from pathlib import Path

from prior_art import COMMENT_LINE, search


class CommentDetectionTest(unittest.TestCase):
    def test_comment_markers_across_the_languages_in_this_repo(self):
        for line in ("// a note", "  // indented", "# python note", " * block continuation"):
            self.assertIsNotNone(COMMENT_LINE.match(line), line)

    def test_a_line_of_code_is_not_a_note_about_the_code(self):
        """A match on code is usually the thing itself, not what someone wrote about it."""
        for line in ('const PLACEHOLDER = "x";', "ROLE_TIMEOUT_MS = {", "  return timeoutMs;"):
            self.assertIsNone(COMMENT_LINE.match(line), line)


class MissedFindingsCorpusTest(unittest.TestCase):
    """The four this repository already knew and re-derived anyway."""

    CASES = (
        ("acceptance clustering",
         "Task 9.2 found clustering broke on any criterion beginning with 'the'; "
         "the same function was widened again three phases later without reading it"),
        ("watchdog",
         "HONEST-LIMITS.md recorded the wall-clock budget being too small for a local "
         "model, and it was re-derived hours later as a new finding"),
        ("Placeholder USAGE",
         "core/planning.ts explains beside the code that the rule matches a literal "
         "token, not a bracket shape — a planner burned a watchdog deliberating it"),
        ("queueTimeoutMs",
         "a 2026-08-12 review flagged a queue timeout equal to a sub-session deadline "
         "as 'two different error stories for one event', and it was reintroduced"),
    )

    def test_every_missed_finding_is_still_reachable(self):
        for term, why in self.CASES:
            hits = search(term)
            self.assertGreater(
                len(hits), 0,
                f"nothing found for {term!r} — {why}. Either the note is gone or the "
                f"search no longer reaches where it lives; both defeat the tool.",
            )

    def test_the_two_that_live_in_comments_are_found_as_comments(self):
        """One of the four was a code comment, which is why comments are searched."""
        hits = search("Placeholder USAGE")
        self.assertTrue(any(h.kind == "comment" for h in hits))


class SearchShapeTest(unittest.TestCase):
    def test_a_term_nobody_wrote_about_returns_nothing_rather_than_erroring(self):
        self.assertEqual(search("zzz-no-such-mechanism-zzz"), [])

    def test_hits_carry_a_repo_relative_path_and_a_line(self):
        hits = search("queueTimeoutMs")
        self.assertTrue(hits)
        for hit in hits:
            self.assertFalse(Path(hit.path).is_absolute(), hit.path)
            self.assertGreater(hit.line, 0)
            self.assertIn(hit.kind, ("prose", "comment"))

    def test_the_search_is_case_insensitive(self):
        self.assertEqual(len(search("WATCHDOG")), len(search("watchdog")))


if __name__ == "__main__":
    unittest.main()

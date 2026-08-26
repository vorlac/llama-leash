"""Tests for the per-epoch review.

The document exists to be trusted at a glance, so its failure modes are all
"looks right and is wrong": a prompt from the wrong version of the corpus, a
tree from the wrong epoch, a phase total that reads as elapsed time when the
phases overlap.
"""

import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from epoch_review import (
    Turn,
    cell_paths,
    clip,
    phase_rows,
    read_turns,
    source_files,
    transcript_lines,
)


def _db(path: Path, messages, parts=()):
    conn = sqlite3.connect(path)
    conn.execute("create table session (id text, title text, parent_id text)")
    conn.execute("create table message (id text, session_id text, time_created integer, data text)")
    conn.execute("create table part (message_id text, session_id text, data text)")
    seen = set()
    for mid, sid, title, root, created, data in messages:
        if sid not in seen:
            conn.execute("insert into session values (?,?,?)", (sid, title, None if root else "p"))
            seen.add(sid)
        conn.execute("insert into message values (?,?,?,?)", (mid, sid, created, json.dumps(data)))
    for mid, sid, data in parts:
        conn.execute("insert into part values (?,?,?)", (mid, sid, json.dumps(data)))
    conn.commit()
    conn.close()


class ReadTurnsTest(unittest.TestCase):
    def test_the_root_session_is_labelled_by_role_not_by_the_user_s_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            _db(db, [
                ("m1", "s_root", "Pinned clock for expiry tests", True, 1,
                 {"role": "assistant", "time": {"created": 0, "completed": 60000},
                  "tokens": {"output": 10, "input": 20}}),
                ("m2", "s_sub", "planner:", False, 2,
                 {"role": "assistant", "time": {"created": 0, "completed": 30000},
                  "tokens": {"output": 5, "input": 6}}),
            ])
            turns = read_turns(db)
            self.assertEqual([t.session for t in turns],
                             ["orchestrator (root session)", "planner:"])
            # created=0 on purpose: `if created and completed` reads a zero
            # timestamp as absent and reports the turn as instantaneous.
            self.assertEqual(turns[0].seconds, 60.0)

    def test_a_turn_with_no_completion_time_is_zero_rather_than_an_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            _db(db, [("m1", "s", "planner:", False, 1,
                      {"role": "assistant", "time": {"created": 1787626723312},
                       "tokens": {"output": 3, "input": 4}})])
            self.assertEqual(read_turns(db)[0].seconds, 0.0)

    def test_user_messages_are_not_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            _db(db, [("m1", "s", "t", True, 1, {"role": "user"})])
            self.assertEqual(read_turns(db), [])

    def test_a_missing_store_is_empty_rather_than_an_error(self):
        self.assertEqual(read_turns(Path("/nonexistent/opencode.db")), [])


class PhaseRowsTest(unittest.TestCase):
    def _turns(self):
        return [
            Turn("planner:", "s1", "", 60.0, 100, 10),
            Turn("planner:", "s2", "", 30.0, 50, 5),
            Turn("skeptic:", "s3", "", 10.0, 7, 1),
        ]

    def test_repeated_dispatches_of_one_role_stay_countable(self):
        """Two planner sessions is a re-dispatch, and merging them hides it."""
        rows = phase_rows(self._turns(), by_session=True)
        planner = [r for r in rows if r[0] == "planner"][0]
        self.assertEqual(planner[1], 2, "two distinct sessions")
        self.assertEqual(planner[2], 2, "two turns")
        self.assertEqual(planner[3], 90.0)

    def test_a_flat_session_is_reported_per_turn_not_invented_into_stages(self):
        """baseline declares no phases; inventing stage names would be a fiction."""
        rows = phase_rows(self._turns(), by_session=False)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(r[1] == 1 and r[2] == 1 for r in rows))
        self.assertTrue(rows[0][0].startswith("turn 1"))


class CellPathsTest(unittest.TestCase):
    def test_an_archived_tree_is_preferred_over_the_live_work_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = Path(tmp) / "results"
            cell_id = "m/none/baseline/slugify-ts/r1"
            archived = results / "trees" / cell_id.replace("/", "__")
            (archived / "repo").mkdir(parents=True)
            (archived / "session").mkdir(parents=True)
            (archived / "session" / "opencode.db").write_text("db")
            repo, db = cell_paths(results, Path(tmp) / "work", cell_id, {"startedIso": ""})
            self.assertEqual(repo, archived / "repo")
            self.assertEqual(db, archived / "session" / "opencode.db")

    def test_a_work_root_tree_from_another_epoch_is_refused(self):
        """The work root always holds the NEWEST epoch, not this result's."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "work"
            cell_id = "m/none/baseline/slugify-ts/r1"
            (work / cell_id / "repo").mkdir(parents=True)
            stale = datetime.fromtimestamp(0, tz=timezone.utc).isoformat()
            repo, db = cell_paths(Path(tmp) / "results", work, cell_id, {"startedIso": stale})
            self.assertIsNone(repo)
            self.assertIsNone(db)

    def test_an_absent_cell_id_yields_nothing(self):
        self.assertEqual(cell_paths(Path("/x"), Path("/y"), "", {"startedIso": "2026-01-01T00:00:00Z"}),
                         (None, None))


class SourceFilesTest(unittest.TestCase):
    def test_the_hidden_gauge_and_harness_furniture_are_not_the_model_s_work(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for d in ("src", "gauge", ".git", ".conductor"):
                (root / d).mkdir()
            (root / "src" / "a.ts").write_text("work")
            (root / "gauge" / "spec.test.ts").write_text("hidden")
            (root / ".git" / "HEAD").write_text("ref")
            (root / ".conductor" / "config.json").write_text("{}")
            self.assertEqual(sorted(source_files(root)), ["src/a.ts"])


if __name__ == "__main__":
    unittest.main()


class TranscriptTest(unittest.TestCase):
    """The turn table says a tool was called and what it cost. It does not say
    what the model was thinking, what it passed, or what came back — and those
    are the three things a reader trying to understand a run actually opens it
    for. The data is in the store; only the renderer never reached for it.
    """

    def _turns(self, tmp):
        db = Path(tmp) / "opencode.db"
        _db(
            db,
            [("m1", "s_root", "task", True, 1,
              {"role": "assistant", "time": {"created": 0, "completed": 1000},
               "tokens": {"output": 5, "input": 7}})],
            [("m1", "s_root", {"type": "reasoning", "text": "I should read the file first."}),
             ("m1", "s_root", {"type": "tool", "tool": "read",
                               "state": {"status": "completed",
                                         "input": {"filePath": "/repo/src/x.ts"},
                                         "output": "export const f = 1;"}}),
             ("m1", "s_root", {"type": "text", "text": "Done."})],
        )
        return read_turns(db)

    def test_reasoning_is_read_out_of_the_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            turns = self._turns(tmp)
            self.assertEqual(turns[0].reasoning, ["I should read the file first."])

    def test_a_tool_call_carries_what_went_in_and_what_came_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            call = self._turns(tmp)[0].calls[0]
            self.assertEqual(call.name, "read")
            self.assertIn("x.ts", call.input)
            self.assertIn("export const f = 1;", call.output)

    def test_the_assistant_s_own_words_are_kept_apart_from_its_reasoning(self):
        with tempfile.TemporaryDirectory() as tmp:
            turn = self._turns(tmp)[0]
            self.assertEqual(turn.text, ["Done."])
            self.assertNotIn("Done.", turn.reasoning)

    def test_the_transcript_renders_all_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = "\n".join(transcript_lines(self._turns(tmp)))
            for expected in ("I should read the file first.", "read", "x.ts",
                             "export const f = 1;", "Done."):
                self.assertIn(expected, body)

    def test_clipping_is_announced_and_names_what_was_lost(self):
        """A silently shortened tool output reads as a short output, and a reader
        draws conclusions from the difference."""
        clipped = clip("x" * 500, 100)
        self.assertIn("truncated", clipped)
        self.assertIn("500", clipped, "the reader is told how much there was")
        self.assertLess(len(clipped), 300)

    def test_short_content_is_left_exactly_alone(self):
        self.assertEqual(clip("short", 100), "short")

    def test_a_turn_that_did_no_thinking_says_so_rather_than_rendering_nothing(self):
        """An absent reasoning block and a reasoning block nobody rendered look
        identical in the output, and only one of them is a fact about the run."""
        turn = Turn(session="s", session_id="s", agent="a", seconds=1.0,
                    out_tokens=1, in_tokens=1)
        body = "\n".join(transcript_lines([turn]))
        self.assertIn("no reasoning", body.lower())


class TranscriptAlwaysRendersTest(unittest.TestCase):
    """A cell that produced no code is the cell whose transcript matters most.

    The first wiring put section 4 after an early `continue` in the code section,
    so an arm that left the seed untouched — or whose tree was never archived —
    silently lost its transcript. Epoch 14's conductor arm did exactly that on
    three of four tasks, and "what did it do for sixty minutes" is the only
    question left to ask about those cells.
    """

    def test_the_render_has_no_early_exit_before_the_transcript(self):
        import inspect
        import epoch_review
        body = inspect.getsource(epoch_review.render_epoch)
        head, _, tail = body.partition("4 \u00b7 The transcript")
        self.assertTrue(tail, "the transcript section must exist")
        after_code_heading = head.split("2 \u00b7 The resulting code")[-1]
        self.assertNotIn("continue", after_code_heading,
                         "an early continue between the code section and the "
                         "transcript drops the transcript for exactly the arms "
                         "that produced nothing")

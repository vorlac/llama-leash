"""Tests for the per-epoch review.

The document exists to be trusted at a glance, so its failure modes are all
"looks right and is wrong": a prompt from the wrong version of the corpus, a
tree from the wrong epoch, a phase total that reads as elapsed time when the
phases overlap.
"""

import json
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from epoch_review import (
    Turn,
    epoch_start,
    subagent_dispatches,
    tasks_from_manifests,
    trend_cell_many,
    trend_rows,
    write_epoch_tree,
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
        # Matched on the section's NAME, not its number: the numbering shifts
        # whenever a section is added between them, and a guard that fails for
        # that reason teaches its reader to renumber the guard.
        head, _, tail = body.partition("\u00b7 The transcript")
        self.assertTrue(tail, "the transcript section must exist")
        after_code_heading = head.split("\u00b7 The resulting code")[-1]
        self.assertNotIn("continue", after_code_heading,
                         "an early continue between the code section and the "
                         "transcript drops the transcript for exactly the arms "
                         "that produced nothing")


class EpochStartTest(unittest.TestCase):
    """An epoch's clock is a fact about its cells, not about its directory name.

    `epoch_start` parsed the directory name as `%Y%m%d-%H%M%S` and raised on
    anything else, so a results directory named for what it was FOR — the shape
    every investigation run uses — crashed the whole document rather than
    rendering that one epoch differently. Every cell already carries `startedIso`.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="epoch-start-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def _cell(self, d: Path, name: str, started: str) -> None:
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(json.dumps({
            "arm": "baseline", "taskId": "t", "startedIso": started, "passed": True,
        }))

    def test_a_timestamped_directory_still_reads_from_its_name(self):
        d = self.tmp / "20260825-172722"
        self._cell(d, "a.json", "2026-08-25T21:27:22Z")
        self.assertEqual(epoch_start(d).strftime("%Y%m%d-%H%M%S"), "20260825-172722")

    def test_a_named_directory_reads_the_earliest_cell_clock(self):
        d = self.tmp / "step1-euler001"
        self._cell(d, "b.json", "2026-08-26T23:49:49Z")
        self._cell(d, "a.json", "2026-08-26T22:10:00Z")
        got = epoch_start(d)
        self.assertEqual(got.astimezone(timezone.utc).isoformat()[:19], "2026-08-26T22:10:00")

    def test_a_directory_with_neither_does_not_crash_the_document(self):
        """One unreadable epoch must not cost every other epoch its section."""
        d = self.tmp / "nameless"
        d.mkdir()
        (d / "a.json").write_text(json.dumps({"arm": "baseline", "taskId": "t"}))
        self.assertIsInstance(epoch_start(d), datetime)


class SubAgentDispatchTest(unittest.TestCase):
    """What each sub-agent was ASKED, which the session store cannot answer.

    read_turns keeps `role == "assistant"` messages, so a sub-session's prompt —
    a user-role message — never reaches the document. The conductor journal
    records it verbatim on `subsession.dispatched`, and the two sources had never
    been joined: the report could say what a sub-agent did and not what it was
    told to do.
    """

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="subagent-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def _journal(self, records) -> Path:
        run = self.tmp / "repo" / ".conductor" / "runs" / "r-1"
        run.mkdir(parents=True)
        path = run / "journal.jsonl"
        path.write_text("".join(json.dumps(r) + "\n" for r in records))
        return path

    def test_each_dispatch_carries_its_role_prompt_and_outcome(self):
        self._journal([
            {"seq": 1, "event": "subsession.dispatched", "component": "fanout",
             "data": {"role": "mechanical", "prompt": "Classify the following work request"}},
            {"seq": 2, "event": "subsession.complete", "component": "fanout",
             "data": {"ok": True, "attempts": 1, "response": '{"kind":"trivial"}'}},
        ])
        got = subagent_dispatches(self.tmp / "repo")
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0].role, "mechanical")
        self.assertIn("Classify the following", got[0].prompt)
        self.assertTrue(got[0].ok)
        self.assertIn("trivial", got[0].response)

    def test_a_dispatch_with_no_completion_is_reported_as_unfinished(self):
        """A sub-agent still running at the ceiling is not a sub-agent that failed."""
        self._journal([
            {"seq": 1, "event": "subsession.dispatched", "component": "fanout",
             "data": {"role": "planner", "prompt": "Decompose"}},
        ])
        got = subagent_dispatches(self.tmp / "repo")
        self.assertEqual(len(got), 1)
        self.assertIsNone(got[0].ok, "unfinished and failed must not read alike")

    def test_an_arm_with_no_journal_yields_nothing_rather_than_raising(self):
        """baseline and doctrine load no plugin, so they write no journal."""
        self.assertEqual(subagent_dispatches(self.tmp / "absent"), [])


class IndexTrendTest(unittest.TestCase):
    """The question a per-epoch document cannot answer: what changed ACROSS epochs.

    One row per (task, arm), one column per epoch, so a reader sees a task get
    slower, an arm start failing, or a fix land — none of which is visible from
    inside any single epoch's section.
    """

    def test_a_cell_that_did_not_run_is_not_a_cell_that_failed(self):
        rows = trend_rows([
            ("e1", {("baseline", "t1"): {"passed": True, "wallClockMs": 60000,
                                         "tokens": {"completion": 100}}}),
            ("e2", {("baseline", "t1"): {"passed": False, "timedOut": True,
                                         "wallClockMs": 120000, "tokens": {"completion": 200}}}),
        ])
        cells = {(r.task, r.arm): r.cells for r in rows}
        self.assertEqual(cells[("t1", "baseline")]["e1"], "PASS 1.0m 100t")
        self.assertEqual(cells[("t1", "baseline")]["e2"], "TIMEOUT 2.0m 200t")

    def test_an_epoch_that_never_ran_a_task_reads_as_absent(self):
        rows = trend_rows([
            ("e1", {("baseline", "t1"): {"passed": True, "wallClockMs": 60000,
                                         "tokens": {"completion": 100}}}),
            ("e2", {("baseline", "t2"): {"passed": True, "wallClockMs": 60000,
                                         "tokens": {"completion": 100}}}),
        ])
        cells = {(r.task, r.arm): r.cells for r in rows}
        self.assertEqual(cells[("t1", "baseline")].get("e2", "–"), "–",
                         "not run and failed must be different words")


class PerEpochOutputTest(unittest.TestCase):
    """One directory per epoch, so an epoch is diffable and reviewable alone."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="per-epoch-"))
        self.addCleanup(shutil.rmtree, str(self.tmp), True)

    def test_each_epoch_gets_its_own_review_and_the_index_links_them(self):
        watch = self.tmp / "watch"
        for name, started in (("20260101-000000", "2026-01-01T00:00:00Z"),
                              ("20260102-000000", "2026-01-02T00:00:00Z")):
            d = watch / name
            d.mkdir(parents=True)
            (d / "a.json").write_text(json.dumps({
                "arm": "baseline", "taskId": "t1", "tier": "T0", "startedIso": started,
                "passed": True, "wallClockMs": 60000, "tokens": {"completion": 10},
            }))
        out = self.tmp / "epochs"
        written = write_epoch_tree(watch, self.tmp / "nowork", out, transcripts=False)
        self.assertEqual(len(written), 2)
        self.assertTrue((out / "INDEX.md").is_file())
        names = sorted(p.parent.name for p in written)
        self.assertEqual(names, ["01-20260101-000000", "02-20260102-000000"])
        for path in written:
            self.assertTrue(path.is_file(), f"{path} was not written")
        index = (out / "INDEX.md").read_text()
        for name in names:
            self.assertIn(name, index, "the index must link every epoch it counted")


class TrendRepsTest(unittest.TestCase):
    """Three repetitions rendered as one cell is two measurements thrown away.

    `load_results` keys by (arm, task) and the last file wins, so an epoch that
    ran baseline three times showed one of them and said nothing about the other
    two. Epoch 15 ran 4.4, 4.9 and 3.0 minutes and the table read `3.0m` — which
    is not merely incomplete, it is the noise floor hidden inside the number the
    reader would compare against.
    """

    def test_repetitions_are_counted_and_their_spread_shown(self):
        cell = trend_cell_many([
            {"passed": True, "wallClockMs": 264000, "tokens": {"completion": 3335}},
            {"passed": True, "wallClockMs": 294000, "tokens": {"completion": 3141}},
            {"passed": True, "wallClockMs": 180000, "tokens": {"completion": 1718}},
        ])
        self.assertIn("x3", cell, cell)
        self.assertIn("3.0", cell, "the fastest repetition is shown")
        self.assertIn("4.9", cell, "and so is the slowest")

    def test_one_repetition_reads_exactly_as_before(self):
        self.assertEqual(
            trend_cell_many([{"passed": True, "wallClockMs": 60000,
                              "tokens": {"completion": 100}}]),
            "PASS 1.0m 100t",
        )

    def test_repetitions_that_disagree_say_so(self):
        """A task that passes twice and fails once is the interesting case."""
        cell = trend_cell_many([
            {"passed": True, "wallClockMs": 60000, "tokens": {"completion": 100}},
            {"passed": False, "wallClockMs": 60000, "tokens": {"completion": 100}},
        ])
        self.assertIn("PASS", cell)
        self.assertIn("FAIL", cell)

    def test_no_repetitions_is_still_absent(self):
        self.assertEqual(trend_cell_many([]), "–")


class ManifestLookupTest(unittest.TestCase):
    """The prompt is the field every other section is downstream of.

    `manifest_at` read `bench/conductor-tasks.json` and nothing else, so an epoch
    run from any `bench/corpus-*.json` reported "the manifest at this epoch's
    commit does not carry this task" for EVERY task — and that sentence names the
    wrong culprit. The manifest carried the task; the reader looked in one file
    out of six. A cell's result JSON records no manifest, so there was nothing
    better to hardcode.
    """

    def test_a_task_in_any_bench_manifest_is_found(self):
        got = tasks_from_manifests({
            "bench/conductor-tasks.json": {"tasks": [{"id": "slugify-ts", "prompt": "A"}]},
            "bench/corpus-euler.json": {"tasks": [{"id": "euler-001-py", "prompt": "B"}]},
        })
        self.assertEqual(got["euler-001-py"]["prompt"], "B")
        self.assertEqual(got["slugify-ts"]["prompt"], "A")

    def test_the_ladder_wins_a_collision_so_a_reading_is_stable(self):
        """Two manifests may share an id; the search order decides, not dict order."""
        got = tasks_from_manifests({
            "bench/corpus-euler.json": {"tasks": [{"id": "dup", "prompt": "corpus"}]},
            "bench/conductor-tasks.json": {"tasks": [{"id": "dup", "prompt": "ladder"}]},
        })
        self.assertEqual(got["dup"]["prompt"], "ladder")

    def test_the_manifest_each_task_came_from_is_recorded(self):
        got = tasks_from_manifests({
            "bench/corpus-euler.json": {"tasks": [{"id": "euler-001-py", "prompt": "B"}]},
        })
        self.assertEqual(got["euler-001-py"]["_manifest"], "bench/corpus-euler.json",
                         "a reader must be able to see WHICH manifest defined the prompt")

    def test_an_unparseable_manifest_costs_only_itself(self):
        got = tasks_from_manifests({
            "bench/broken.json": None,
            "bench/corpus-euler.json": {"tasks": [{"id": "euler-001-py", "prompt": "B"}]},
        })
        self.assertIn("euler-001-py", got, "one bad manifest must not empty the whole lookup")

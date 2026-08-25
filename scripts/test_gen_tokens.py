"""Tests for the generated-token accounting.

The distinction this module exists to make is between what the model EMITTED and
what was fed to it. Tool `output` is a file's contents coming back from a read —
prompt, paid for at prompt-processing rates, not at the generation rate. Tool
`input` is the arguments the model wrote. Counting the two together would put a
cell that read one large file on a par with a cell that thought for ten minutes,
which is the confusion the ledger's own token figure already causes.
"""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from gen_tokens import CHARS_PER_TOKEN, accumulate, measure


def rows(*parts):
    return iter(json.dumps(p) for p in parts)


class AccumulateTest(unittest.TestCase):
    def test_tool_output_is_prompt_and_is_never_counted(self):
        """The load-bearing exclusion: a read's result is not generation."""
        breakdown = accumulate(rows({
            "type": "tool",
            "tool": "read",
            "state": {"input": {"filePath": "a.ts"}, "output": "x" * 100_000},
        }))
        self.assertEqual(breakdown.tool_args, len(json.dumps({"filePath": "a.ts"})))
        self.assertLess(breakdown.total_chars, 100)

    def test_reasoning_text_and_tool_args_all_count_as_generation(self):
        breakdown = accumulate(rows(
            {"type": "reasoning", "text": "a" * 40},
            {"type": "text", "text": "b" * 20},
            {"type": "tool", "state": {"input": {"k": "v"}}},
        ))
        self.assertEqual(breakdown.reasoning, 40)
        self.assertEqual(breakdown.text, 20)
        self.assertEqual(breakdown.tool_args, len(json.dumps({"k": "v"})))
        self.assertEqual(breakdown.parts, 3)

    def test_untyped_and_bodyless_parts_contribute_nothing(self):
        breakdown = accumulate(rows(
            {"type": "step-start"},
            {"type": "step-finish"},
            {"type": "tool", "state": {"output": "no input key"}},
            {"type": "reasoning"},
        ))
        self.assertEqual(breakdown.total_chars, 0)
        self.assertEqual(breakdown.parts, 0)

    def test_a_malformed_row_is_skipped_rather_than_raised_on(self):
        """A cell killed mid-write still has to yield a partial accounting."""
        breakdown = accumulate(iter([
            '{"type": "reasoning", "text": "kept"}',
            '{"type": "reasoning", "text": "trunca',   # the killed write
            'not json at all',
            '["a list, not an object"]',
        ]))
        self.assertEqual(breakdown.reasoning, 4)
        self.assertEqual(breakdown.parts, 1)

    def test_shares_and_predictions_are_defined_on_an_empty_cell(self):
        breakdown = accumulate(iter([]))
        self.assertEqual(breakdown.reasoning_share, 0.0)
        self.assertEqual(breakdown.predicted_seconds(), 0.0)
        self.assertEqual(breakdown.predicted_seconds(0), 0.0)

    def test_prediction_divides_tokens_by_the_rate(self):
        breakdown = accumulate(rows({"type": "reasoning", "text": "z" * (CHARS_PER_TOKEN * 1400)}))
        self.assertEqual(breakdown.total_tokens, 1400)
        self.assertAlmostEqual(breakdown.predicted_seconds(14.0), 100.0)


class MeasureTest(unittest.TestCase):
    def test_a_text_part_on_a_user_message_is_a_brief_and_is_not_generation(self):
        """The second exclusion, and the one part type alone cannot make.

        `text` appears on both sides of the conversation. A sub-session's brief
        arrives as a user-message `text` part running to thousands of
        characters, and counting it credits the harness's own prompt to the
        model's output — an error that grows with the dispatch count, which is
        exactly the axis being measured.
        """
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            connection = sqlite3.connect(db)
            connection.execute("create table message (id text primary key, data text)")
            connection.execute("create table part (id text, message_id text, data text)")
            connection.executemany("insert into message values (?, ?)", [
                ("msg_user", json.dumps({"role": "user"})),
                ("msg_asst", json.dumps({"role": "assistant"})),
            ])
            connection.executemany("insert into part values (?, ?, ?)", [
                ("p1", "msg_user", json.dumps({"type": "text", "text": "B" * 5000})),
                ("p2", "msg_asst", json.dumps({"type": "text", "text": "A" * 300})),
                ("p3", "msg_asst", json.dumps({"type": "reasoning", "text": "R" * 700})),
            ])
            connection.commit()
            connection.close()

            breakdown = measure(db)
            self.assertEqual(breakdown.text, 300, "the 5000-char brief must not count")
            self.assertEqual(breakdown.reasoning, 700)
            self.assertEqual(breakdown.total_chars, 1000)

    def test_reads_a_real_database_without_locking_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            connection = sqlite3.connect(db)
            connection.execute("create table message (id text primary key, data text)")
            connection.execute("create table part (id text, message_id text, data text)")
            connection.execute("insert into message values ('m', ?)", (json.dumps({"role": "assistant"}),))
            connection.executemany("insert into part values (?, 'm', ?)", [
                ("a", json.dumps({"type": "reasoning", "text": "t" * 400})),
                ("b", json.dumps({"type": "tool", "state": {"input": {}, "output": "o" * 9999}})),
            ])
            connection.commit()
            connection.close()

            breakdown = measure(db)
            self.assertEqual(breakdown.reasoning, 400)
            self.assertNotIn("o" * 20, str(breakdown))
            self.assertLess(breakdown.total_chars, 500)


if __name__ == "__main__":
    unittest.main()

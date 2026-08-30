"""Unit suite for scripts/review_cost.py — the review-loop cost and yield reader.

Everything here runs offline over synthetic records. No run directory, no
ledger file, no server, no model: every function under test is pure, which is
the property that makes the instrument checkable at all.

Run with the stdlib runner the gate uses::

    /usr/bin/python3 -m unittest discover -s scripts -p 'test_*.py'
"""

from __future__ import annotations

import importlib.util
import io
import unittest
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "review_cost", Path(__file__).resolve().parent / "review_cost.py"
)
review_cost = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(review_cost)


def _record(seq, ts, event, data=None, **rest):
    out = {"seq": seq, "ts": ts, "event": event, "data": data or {}}
    out.update(rest)
    return out


class JsonObjectsTests(unittest.TestCase):
    def test_a_nested_object_is_not_returned_as_a_top_level_one(self):
        # The shape that matters: a reply whose findings list is empty and whose
        # readWitness is a nested object. Descending into the nesting would make
        # the witness look like the reply and lose the findings list.
        text = 'prose\n```json\n{"findings": [], "readWitness": {"nonce": "RW-1"}}\n```'
        objs = review_cost.json_objects(text)
        self.assertEqual(len(objs), 1)
        self.assertEqual(objs[0]["findings"], [])
        self.assertEqual(objs[0]["readWitness"]["nonce"], "RW-1")

    def test_two_top_level_objects_are_both_returned_in_order(self):
        objs = review_cost.json_objects('{"a": 1} and then {"b": 2}')
        self.assertEqual(objs, [{"a": 1}, {"b": 2}])

    def test_a_brace_that_starts_no_object_is_skipped(self):
        self.assertEqual(review_cost.json_objects("{ not json at all"), [])


class ReplyFindingsTests(unittest.TestCase):
    def test_an_approval_is_an_empty_list_and_not_none(self):
        # The whole point: [] is the approval, None is "not a findings reply".
        # Collapsing them would count a crashed lens as a clean one.
        self.assertEqual(review_cost.reply_findings('{"findings": []}'), [])

    def test_a_reply_carrying_no_findings_key_is_none(self):
        self.assertIsNone(review_cost.reply_findings('{"status": "DONE"}'))
        self.assertIsNone(review_cost.reply_findings("no json here"))

    def test_findings_come_from_the_last_object_carrying_them(self):
        text = '{"findings": [{"id": "early"}]} ... {"findings": [{"id": "late"}]}'
        self.assertEqual(review_cost.reply_findings(text), [{"id": "late"}])

    def test_a_non_object_finding_is_dropped(self):
        self.assertEqual(review_cost.reply_findings('{"findings": ["oops", {"id": "x"}]}'),
                         [{"id": "x"}])


class StageAndLensTests(unittest.TestCase):
    def test_the_three_reviewer_stages_are_separated(self):
        self.assertEqual(
            review_cost.stage_of("reviewer", "You are an item reviewer, one of 6..."),
            "itemReview",
        )
        self.assertEqual(
            review_cost.stage_of("reviewer", "You are a plan reviewer holding ONE lens..."),
            "planReview",
        )
        self.assertEqual(
            review_cost.stage_of(
                "reviewer", "You are one of 3 INDEPENDENT test-vet critics (vet round 1 of at most 3)."
            ),
            "vet",
        )

    def test_a_re_vet_after_a_test_change_is_its_own_stage(self):
        # A re-vet and a first vet cost the same and mean different things: one is
        # the discipline, the other is the discipline paid twice.
        prompt = (
            "You are one of 3 INDEPENDENT test-vet critics judging ONE test that was "
            "CHANGED during item review (3.3: a changed test re-enters the discipline)."
        )
        self.assertEqual(review_cost.stage_of("reviewer", prompt), "vetChanged")

    def test_a_non_reviewer_role_is_its_own_stage(self):
        self.assertEqual(review_cost.stage_of("implementer", "anything"), "implementer")
        self.assertEqual(review_cost.stage_of(None, ""), "unknown")

    def test_both_brief_shapes_name_their_lens(self):
        self.assertEqual(review_cost.lens_of("head\nLENSES: spec/contract\ntail"), "spec/contract")
        self.assertEqual(
            review_cost.lens_of('You are a plan reviewer.\nYour lens is "correctness": judge...'),
            "correctness",
        )
        self.assertIsNone(review_cost.lens_of("a brief that names no lens"))

    def test_a_round_number_is_read_from_the_brief(self):
        self.assertEqual(review_cost.round_of("vet round 2 of at most 3)."), 2)
        self.assertIsNone(review_cost.round_of("no round here"))


class WindowLedgerTests(unittest.TestCase):
    def _row(self, stamp, tokens=100):
        return {"completedAt": stamp, "completionTokens": tokens}

    def test_a_row_from_a_prior_run_is_excluded(self):
        # The ledger is global and append-only. This is the exclusion that stops a
        # prior day's decode being reported as this run's total.
        rows = [
            self._row("2026-08-27T10:00:00+00:00"),
            self._row("2026-08-28T23:50:00+00:00"),
        ]
        first = review_cost.completed_at_ms({"completedAt": "2026-08-28T23:00:00+00:00"})
        last = review_cost.completed_at_ms({"completedAt": "2026-08-29T07:00:00+00:00"})
        kept = review_cost.window_ledger(rows, first, last)
        self.assertEqual(len(kept), 1)
        self.assertEqual(kept[0]["completedAt"], "2026-08-28T23:50:00+00:00")

    def test_a_row_inside_the_tail_grace_is_kept(self):
        first = review_cost.completed_at_ms({"completedAt": "2026-08-29T00:00:00+00:00"})
        last = first + 1000
        just_after = {"completedAt": "2026-08-29T00:00:31+00:00", "completionTokens": 5}
        self.assertEqual(review_cost.window_ledger([just_after], first, last), [just_after])

    def test_a_row_with_no_stamp_is_dropped_rather_than_dated_now(self):
        first = review_cost.completed_at_ms({"completedAt": "2026-08-29T00:00:00+00:00"})
        self.assertEqual(review_cost.window_ledger([{"completionTokens": 9}], first, first), [])


class WavesTests(unittest.TestCase):
    def _journal(self):
        # Completions arrive OUT OF DISPATCH ORDER on purpose: `minimality`
        # replies first. Only the sessionID join gets the durations right.
        return [
            _record(1, 1_000, "run.created"),
            _record(2, 2_000, "wave", {"jobs": 2, "roles": ["reviewer", "reviewer"]}),
            _record(3, 2_100, "subsession.dispatched",
                    {"role": "reviewer", "itemId": "i1",
                     "prompt": "You are an item reviewer\nLENSES: correctness"},
                    sessionID="ses_corr"),
            _record(4, 2_200, "subsession.dispatched",
                    {"role": "reviewer", "itemId": "i1",
                     "prompt": "You are an item reviewer\nLENSES: minimality"},
                    sessionID="ses_min"),
            _record(5, 62_000, "subsession.complete",
                    {"ok": True,
                     "response": '{"findings": [{"id": "n1", "lens": "minimality", '
                                 '"severity": "nit"}]}'},
                    sessionID="ses_min"),
            _record(6, 122_000, "subsession.complete",
                    {"ok": True, "response": '{"findings": []}'},
                    sessionID="ses_corr"),
        ]

    def test_a_wave_collects_its_dispatches_and_completions(self):
        waves = review_cost.waves_of(self._journal())
        self.assertEqual(len(waves), 1)
        wave = waves[0]
        self.assertEqual(wave.jobs, 2)
        self.assertEqual(wave.stage, "itemReview")
        self.assertEqual(wave.item, "i1")
        self.assertEqual([d.lens for d in wave.dispatches], ["correctness", "minimality"])
        self.assertEqual(wave.span_s, 120.0)

    def test_each_dispatch_pairs_with_its_OWN_completion_not_the_next_one(self):
        # The join that matters. `minimality` was dispatched SECOND and completed
        # FIRST. Pairing positionally would hand correctness the nit and give both
        # lenses the wrong duration; the sessionID join gets both right.
        wave = review_cost.waves_of(self._journal())[0]
        by_lens = {d.lens: d for d in wave.dispatches}
        self.assertEqual(by_lens["minimality"].findings()[0]["id"], "n1")
        self.assertEqual(by_lens["correctness"].findings(), [])
        self.assertAlmostEqual(by_lens["minimality"].duration_s, 59.8)
        self.assertAlmostEqual(by_lens["correctness"].duration_s, 119.9)

    def test_findings_and_empty_replies_are_counted_apart(self):
        wave = review_cost.waves_of(self._journal())[0]
        self.assertEqual(len(wave.findings()), 1)
        self.assertEqual(wave.empty_replies, 1)

    def test_a_completion_naming_no_known_session_is_ignored(self):
        # Rather than attached to a neighbour, which is how a positional join
        # turns one stray record into a whole wave of wrong durations.
        journal = self._journal()
        journal.append(_record(7, 130_000, "subsession.complete",
                               {"ok": True, "response": '{"findings": []}'},
                               sessionID="ses_stranger"))
        wave = review_cost.waves_of(journal)[0]
        self.assertEqual(wave.jobs, 2)
        self.assertEqual(wave.span_s, 120.0, "the stray record did not extend the span")

    def test_a_dispatch_with_no_completion_has_no_duration(self):
        journal = self._journal()[:-2]   # drop both completions
        wave = review_cost.waves_of(journal)[0]
        self.assertEqual([d.duration_s for d in wave.dispatches], [None, None])
        self.assertEqual(wave.failures, 2, "an unsettled dispatch is not a success")

    def test_records_before_the_first_wave_are_dropped_not_misattributed(self):
        stray = [_record(1, 500, "subsession.dispatched", {"role": "reviewer", "prompt": "x"})]
        self.assertEqual(review_cost.waves_of(stray), [])

    def test_a_failed_completion_is_flagged(self):
        journal = self._journal()
        journal[-1]["data"]["ok"] = False
        self.assertEqual(review_cost.waves_of(journal)[0].failures, 1)

    def test_a_truncated_prompt_record_is_counted_not_read_as_a_short_brief(self):
        # The journal caps a record at 8 KiB and the schema shape the harness
        # appends rides at the END of a brief, so a truncated record is missing
        # its tail. Reading "this role was never shown its schema" off one is a
        # fabricated defect; the count is what stops that reading.
        journal = self._journal()
        journal[2]["data"]["truncated"] = True
        wave = review_cost.waves_of(journal)[0]
        self.assertEqual(wave.truncated_prompts, 1)
        self.assertEqual(review_cost.waves_of(self._journal())[0].truncated_prompts, 0)

    def test_the_report_names_a_truncated_prompt_record(self):
        journal = self._journal()
        journal[2]["data"]["truncated"] = True
        out = io.StringIO()
        review_cost.report(review_cost.waves_of(journal), [], out)
        self.assertIn("prompt-tail-not-recorded=1", out.getvalue())


class ThroughputTests(unittest.TestCase):
    def _wave_at(self, index, start_ms, span_ms, jobs):
        wave = review_cost.Wave(index, start_ms)
        for i in range(jobs):
            dispatch = review_cost.Dispatch(f"ses_{index}_{i}", start_ms, "reviewer", "", "p")
            dispatch.end_ts = start_ms + span_ms
            dispatch.ok = True
            wave.dispatches.append(dispatch)
        return wave

    def test_a_flat_rate_across_concurrency_is_reported_as_flat(self):
        # The measurement every fan-out cut rests on: if the generator serves one
        # sequence at a time, six concurrent readers each finish six times slower
        # and the wave's AGGREGATE rate does not move. Here a 1-job wave and a
        # 6-job wave each decode 1,200 tokens in 120 s, and both must read 10/s.
        base = review_cost.completed_at_ms({"completedAt": "2026-08-29T00:00:00+00:00"})
        solo = self._wave_at(0, base, 120_000, 1)
        wide = self._wave_at(1, base + 600_000, 120_000, 6)
        ledger = [
            {"completedAt": "2026-08-29T00:01:00+00:00", "completionTokens": 1_200},
            {"completedAt": "2026-08-29T00:11:00+00:00", "completionTokens": 1_200},
        ]
        rates = review_cost.throughput_by_concurrency([solo, wide], ledger, floor_s=60.0)
        self.assertEqual(sorted(rates), [1, 6])
        self.assertEqual(rates[1], [10.0])
        self.assertEqual(rates[6], [10.0])

    def test_a_wave_with_no_ledger_rows_rates_zero_rather_than_raising(self):
        base = review_cost.completed_at_ms({"completedAt": "2026-08-29T00:00:00+00:00"})
        rates = review_cost.throughput_by_concurrency(
            [self._wave_at(0, base, 120_000, 3)], [], floor_s=60.0
        )
        self.assertEqual(rates, {3: [0.0]})

    def test_a_short_wave_is_excluded_from_the_rate(self):
        base = 1_700_000_000_000
        waves = [self._wave_at(0, base, 5_000, 3)]
        self.assertEqual(review_cost.throughput_by_concurrency(waves, [], floor_s=60.0), {})

    def test_wave_tokens_sums_only_rows_inside_the_wave(self):
        base = review_cost.completed_at_ms({"completedAt": "2026-08-29T00:00:00+00:00"})
        wave = self._wave_at(0, base, 120_000, 2)
        rows = [
            {"completedAt": "2026-08-29T00:00:30+00:00", "completionTokens": 40},
            {"completedAt": "2026-08-29T00:01:30+00:00", "completionTokens": 60},
            {"completedAt": "2026-08-29T01:00:00+00:00", "completionTokens": 999},
        ]
        self.assertEqual(review_cost.wave_tokens(wave, rows), 100)


class ReportTests(unittest.TestCase):
    def test_the_report_renders_over_a_run_with_no_findings_at_all(self):
        # A run where every review was an approval is the ordinary case, and the
        # report must say so rather than print an empty section.
        journal = [
            _record(1, 0, "wave", {"jobs": 1, "roles": ["reviewer"]}),
            _record(2, 10, "subsession.dispatched",
                    {"role": "reviewer", "itemId": "i", "prompt": "You are an item reviewer\nLENSES: perf"},
                    sessionID="ses_a"),
            _record(3, 90_000, "subsession.complete",
                    {"ok": True, "response": '{"findings": []}'}, sessionID="ses_a"),
        ]
        out = io.StringIO()
        review_cost.report(review_cost.waves_of(journal), [], out)
        text = out.getvalue()
        self.assertIn("every review round in this run was an approval", text)
        self.assertIn("itemReview", text)
        self.assertIn("perf", text)

    def test_the_report_names_a_finding_with_its_severity(self):
        journal = [
            _record(1, 0, "wave", {"jobs": 1, "roles": ["reviewer"]}),
            _record(2, 10, "subsession.dispatched",
                    {"role": "reviewer", "itemId": "i",
                     "prompt": "You are an item reviewer\nLENSES: minimality"},
                    sessionID="ses_a"),
            _record(3, 90_000, "subsession.complete",
                    {"ok": True,
                     "response": '{"findings": [{"id": "redundant", "lens": "minimality", '
                                 '"severity": "nit", "claim": "subsumed"}]}'},
                    sessionID="ses_a"),
        ]
        out = io.StringIO()
        review_cost.report(review_cost.waves_of(journal), [], out)
        text = out.getvalue()
        self.assertIn("'nit'", text)
        self.assertIn("redundant", text)

    def test_a_lens_table_keys_by_stage_so_two_stages_do_not_pool(self):
        # `correctness` and `minimality` exist in BOTH review stages. One pooled
        # row would credit an item lens with a plan lens's finding.
        journal = [
            _record(1, 0, "wave", {"jobs": 1, "roles": ["reviewer"]}),
            _record(2, 10, "subsession.dispatched",
                    {"role": "reviewer", "prompt": 'You are a plan reviewer\nYour lens is "correctness":'},
                    sessionID="ses_plan"),
            _record(3, 90_000, "subsession.complete",
                    {"ok": True,
                     "response": '{"findings": [{"id": "p1", "lens": "correctness", "severity": "minor"}]}'},
                    sessionID="ses_plan"),
            _record(4, 91_000, "wave", {"jobs": 1, "roles": ["reviewer"]}),
            _record(5, 91_010, "subsession.dispatched",
                    {"role": "reviewer", "itemId": "i",
                     "prompt": "You are an item reviewer\nLENSES: correctness"},
                    sessionID="ses_item"),
            _record(6, 181_000, "subsession.complete", {"ok": True, "response": '{"findings": []}'},
                    sessionID="ses_item"),
        ]
        out = io.StringIO()
        review_cost.report(review_cost.waves_of(journal), [], out)
        text = out.getvalue()
        self.assertIn("planReview   correctness              dispatched=1   findings=1", text)
        self.assertIn("itemReview   correctness              dispatched=1   findings=0", text)


if __name__ == "__main__":
    unittest.main()

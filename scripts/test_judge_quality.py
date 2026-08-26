"""Tests for the blind paired quality judge.

The failure modes here are all "produces a verdict that looks like a measurement
and is not one": a judge reading an arm label instead of the code, a winner that
only won because it was shown first, a self-contradicting judge resolved by
majority vote, and an unparseable response folded into a tie.

The blinding tests are written so they FAIL if the strip is removed: each one
asserts the marker is present in the raw tree and absent after. An assertion only
about the stripped tree would pass against a fixture that never carried the
marker in the first place.
"""

import json
import tempfile
import time
import unittest
from pathlib import Path

import conductor_bench as cb
import judge_quality as jq


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

PROMPT = "src/x.ts exports f(input). Make it uppercase the input."


def reply(score1, score2, reason="the first names the edge case at src/x.ts:4 and the second does not"):
    return json.dumps({"score1": score1, "score2": score2, "reason": reason})


def scripted(*texts):
    """A judge that returns each canned reply in turn, then repeats the last."""
    box = {"i": 0}

    def call(prompt, seed):
        index = min(box["i"], len(texts) - 1)
        box["i"] += 1
        return texts[index]

    return call


def side_bodies(prompt):
    """The two rendered implementations out of a judge prompt."""
    first = prompt.split("=== Implementation 1 ===", 1)[1]
    first, rest = first.split("=== Implementation 2 ===", 1)
    second = rest.split("Answer with one JSON object", 1)[0]
    return first.strip(), second.strip()


def prefers_longer(prompt, seed):
    first, second = side_bodies(prompt)
    return reply(3, 1) if len(first) > len(second) else reply(1, 3)


def prefers_first(prompt, seed):
    return reply(3, 1)


def oracle_for(cases):
    """A perfect judge: it recognizes the known-better tree by its rendered text."""
    better = set()
    for case in cases:
        files, _ = jq.strip_identity(dict(case.better))
        text, _cut = jq.render_side(files, "Implementation 1")
        better.add(text.split("\n", 1)[1].strip())

    def call(prompt, seed):
        first_body, second_body = side_bodies(prompt)
        if first_body in better and second_body not in better:
            return reply(3, 1)
        if second_body in better and first_body not in better:
            return reply(1, 3)
        return reply(2, 2, "the two are the same implementation, so they score equally here")

    return call


def runs(winners, arm_a="baseline", arm_b="conductor", invalid=""):
    """Hand-built runs, half in each order, for exercising `settle` directly."""
    out = []
    for index, winner in enumerate(winners):
        swapped = index % 2 == 1
        side = None
        if winner == jq.TIE:
            side = jq.TIE
        elif winner is not None:
            first_is_a = not swapped
            side = "first" if (winner == arm_a) == first_is_a else "second"
        if invalid:
            out.append(jq.Run("structure", swapped, index + 1, index + 1,
                              None, None, None, None, "", invalid))
            continue
        out.append(jq.Run("structure", swapped, index + 1, index + 1, side, winner,
                          3 if winner == arm_a else 1, 1 if winner == arm_a else 3,
                          "a reason long enough to clear the floor set on reasons",
                          invalid))
    return out


# ---------------------------------------------------------------------------
# Blinding
# ---------------------------------------------------------------------------

class BlindingTest(unittest.TestCase):
    def test_the_plugins_run_records_are_gone_and_were_there_to_begin_with(self):
        """`.conductor/runs/*` exists in no baseline tree, so it names the arm."""
        raw = {
            "src/x.ts": "export const f = (s: string) => s.toUpperCase();\n",
            ".conductor/runs/r-20260822-d0c7/journal.jsonl": '{"event":"run.started"}\n',
            ".conductor/state/alive.json": '{"pid":401,"pluginVersion":"0.4.0"}\n',
        }
        self.assertTrue(jq.residual_leaks(raw), "the fixture must carry the leak it tests")
        stripped, leaks = jq.strip_identity(raw)
        self.assertEqual(list(stripped), ["src/x.ts"])
        self.assertEqual(jq.residual_leaks(stripped), [])
        self.assertIn("path", {leak.kind for leak in leaks})

    def test_the_doctrine_arms_generated_prompt_file_is_gone(self):
        raw = {"doctrine-prompt.md": "# packs\n", "src/x.ts": "export const f = 1;\n"}
        self.assertTrue(jq.residual_leaks(raw))
        stripped, _ = jq.strip_identity(raw)
        self.assertEqual(list(stripped), ["src/x.ts"])

    def test_an_arm_named_in_a_comment_is_redacted_from_the_code_that_survives(self):
        raw = {"src/x.ts": "// planned by the conductor, per run r-20260822-d0c7\n"
                           "export const f = 1;\n"}
        self.assertTrue(jq.residual_leaks(raw), "the fixture must carry the leak it tests")
        stripped, leaks = jq.strip_identity(raw)
        self.assertEqual(jq.residual_leaks(stripped), [])
        self.assertIn("export const f = 1;", stripped["src/x.ts"],
                      "the strip must remove identity, not the work being judged")
        self.assertEqual({leak.kind for leak in leaks}, {"arm-name", "run-id"})

    def test_the_harness_and_the_model_are_identity_too(self):
        raw = {"README.md": "Run under opencode against qwen3.8-27b in llama-leash.\n"}
        stripped, _ = jq.strip_identity(raw)
        self.assertEqual(jq.residual_leaks(stripped), [])

    def test_every_redaction_uses_one_marker_so_the_marker_names_no_kind(self):
        """A per-kind marker would tell the judge what was hidden, which is the tell."""
        stripped, _ = jq.strip_identity(
            {"a.ts": "// conductor, r-20260822-d0c7, opencode, qwen3\n"}
        )
        self.assertEqual(stripped["a.ts"].count(jq.REDACTION), 4)
        for kind, _pattern in jq.IDENTITY_TOKENS:
            self.assertNotIn(kind, stripped["a.ts"],
                             "the marker must not name what it hid")

    def test_loading_a_real_archived_tree_drops_the_plugin_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            (root / "src").mkdir(parents=True)
            (root / ".conductor" / "runs" / "r-20260822-d0c7").mkdir(parents=True)
            (root / "gauge").mkdir()
            (root / "src" / "x.ts").write_text("export const f = 1;\n")
            (root / ".conductor" / "runs" / "r-20260822-d0c7" / "journal.jsonl").write_text("{}\n")
            (root / "gauge" / "spec.test.ts").write_text("// the answer key\n")
            files = jq.load_tree(root)
            self.assertEqual(list(files), ["src/x.ts"],
                             "the plugin's records and the hidden gauge are both out")

    def test_a_pair_redacted_unevenly_is_reported_as_contaminated(self):
        """The marker itself is a channel: one side carrying it has said something."""
        pair = jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"src/x.ts": "export const f = 1;\n"},
                            {"src/x.ts": "// written by the conductor planner\n"
                                         "export const f = 1;\n"})
        self.assertTrue(any("asymmetric" in note for note in pair.contamination))

    def test_a_clean_pair_reports_no_contamination(self):
        pair = jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"src/x.ts": "export const f = 1;\n"},
                            {"src/x.ts": "export const f = 2;\n"})
        self.assertEqual(pair.contamination, [])


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

class ParseTest(unittest.TestCase):
    def test_a_well_formed_reply_parses(self):
        parsed = jq.parse_reply(reply(3, 1))
        self.assertTrue(parsed.ok)
        self.assertEqual((parsed.score_first, parsed.score_second), (3, 1))

    def test_the_last_object_wins_because_a_model_thinks_out_loud_first(self):
        text = 'For example {"score1": 0, "score2": 0} ... ' + reply(2, 3)
        parsed = jq.parse_reply(text)
        self.assertEqual((parsed.score_first, parsed.score_second), (2, 3))

    def test_a_verdict_with_no_real_reason_is_unusable_not_thin(self):
        """A winner with no stated reason is unauditable; the reason IS the artifact."""
        parsed = jq.parse_reply(reply(3, 1, reason="better"))
        self.assertFalse(parsed.ok)
        self.assertIn("floor", parsed.invalid)

    def test_a_score_outside_the_closed_set_is_refused(self):
        self.assertFalse(jq.parse_reply(reply(7, 1)).ok)

    def test_a_boolean_is_not_a_score_even_though_python_says_it_is_an_int(self):
        text = json.dumps({"score1": True, "score2": 0, "reason": "x" * 60})
        self.assertIn("not an integer", jq.parse_reply(text).invalid)

    def test_prose_with_no_object_is_an_instrument_failure(self):
        self.assertIn("no JSON object", jq.parse_reply("I think the first one is nicer.").invalid)

    def test_an_empty_response_says_so(self):
        self.assertIn("empty", jq.parse_reply("").invalid)


# ---------------------------------------------------------------------------
# Un-swapping
# ---------------------------------------------------------------------------

class UnswapTest(unittest.TestCase):
    def test_in_the_swapped_order_a_win_for_the_first_side_is_a_win_for_arm_b(self):
        run = jq._settle_run(jq.parse_reply(reply(3, 1)), "baseline", "conductor",
                             swapped=True, criterion="structure", rep=1, seed=1)
        self.assertEqual(run.winner, "conductor")
        self.assertEqual((run.score_a, run.score_b), (1, 3),
                         "scores follow the arms, not the positions")

    def test_in_the_normal_order_a_win_for_the_first_side_is_a_win_for_arm_a(self):
        run = jq._settle_run(jq.parse_reply(reply(3, 1)), "baseline", "conductor",
                             swapped=False, criterion="structure", rep=1, seed=1)
        self.assertEqual(run.winner, "baseline")
        self.assertEqual((run.score_a, run.score_b), (3, 1))

    def test_equal_scores_are_a_tie_in_either_order(self):
        for swapped in (False, True):
            run = jq._settle_run(jq.parse_reply(reply(2, 2)), "baseline", "conductor",
                                 swapped=swapped, criterion="structure", rep=1, seed=1)
            self.assertEqual(run.winner, jq.TIE)


# ---------------------------------------------------------------------------
# Settling a criterion
# ---------------------------------------------------------------------------

class SettleTest(unittest.TestCase):
    def test_winning_every_run_in_both_orders_is_a_win(self):
        outcome, note = jq.settle(runs(["baseline"] * 6), "baseline", "conductor")
        self.assertEqual(outcome, "win_a")
        self.assertIn("both presentation orders", note)

    def test_winning_only_when_shown_first_is_a_tie_and_is_named_as_position_bias(self):
        """An arm that wins only from position 1 did not win."""
        winners = ["baseline", "conductor"] * 3  # index parity makes side always "first"
        outcome, note = jq.settle(runs(winners), "baseline", "conductor")
        self.assertEqual(outcome, jq.TIE)
        self.assertIn("POSITION BIAS", note)

    def test_a_judge_that_contradicts_itself_is_a_tie_not_a_majority(self):
        winners = ["baseline", "baseline", "conductor", "baseline", "baseline", "baseline"]
        outcome, note = jq.settle(runs(winners), "baseline", "conductor")
        self.assertEqual(outcome, jq.TIE)
        self.assertIn("disagreed with itself", note)
        self.assertNotIn("POSITION BIAS", note,
                         "it preferred different sides, so position is not the story")

    def test_a_unanimous_tie_does_not_read_like_a_disagreement(self):
        outcome, note = jq.settle(runs([jq.TIE] * 6), "baseline", "conductor")
        self.assertEqual(outcome, jq.TIE)
        self.assertIn("no difference", note)
        self.assertNotIn("disagreed", note)

    def test_an_unusable_response_is_no_verdict_and_never_a_tie(self):
        """'Could not answer' and 'saw no difference' call for opposite responses."""
        broken = runs(["baseline"] * 5) + runs([None], invalid="empty response")
        outcome, note = jq.settle(broken, "baseline", "conductor")
        self.assertEqual(outcome, "no_verdict")
        self.assertIn("instrument failure", note)

    def test_one_presentation_order_alone_cannot_produce_a_verdict(self):
        one_order = [r for r in runs(["baseline"] * 6) if not r.swapped]
        outcome, note = jq.settle(one_order, "baseline", "conductor")
        self.assertEqual(outcome, "no_verdict")
        self.assertIn("position bias is untested", note)

    def test_no_runs_at_all_is_no_verdict(self):
        self.assertEqual(jq.settle([], "baseline", "conductor")[0], "no_verdict")


# ---------------------------------------------------------------------------
# Repetition seeds
# ---------------------------------------------------------------------------

class SeedTest(unittest.TestCase):
    def test_every_repetition_gets_its_own_seed(self):
        """One seed repeated is one sample printed N times: llama.cpp is deterministic
        given a seed and a sampler, so agreement across a fixed seed measures the
        sampler and says nothing about the code."""
        seeds = jq.seeds_for(5)
        self.assertEqual(len(set(seeds)), 5)

    def test_zero_repetitions_is_refused(self):
        with self.assertRaises(ValueError):
            jq.seeds_for(0)

    def test_a_comparison_uses_a_distinct_seed_per_repetition(self):
        seen = []

        def recorder(prompt, seed):
            seen.append(seed)
            return reply(2, 2)

        pair = jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"a.ts": "1\n"}, {"a.ts": "2\n"})
        jq.compare(pair, recorder, criteria=("structure",), reps=3)
        self.assertEqual(len(seen), 6, "three repetitions in each of two orders")
        self.assertEqual(sorted(set(seen)), [1, 2, 3])


# ---------------------------------------------------------------------------
# A missing tree
# ---------------------------------------------------------------------------

class MissingTreeTest(unittest.TestCase):
    def test_a_comparison_with_nothing_to_compare_is_loud_and_is_not_a_tie(self):
        results = jq.missing_tree_result("slugify-ts", "baseline", "conductor", ["conductor"])
        self.assertEqual({r.outcome for r in results}, {"no_tree"})
        self.assertEqual(len(results), len(jq.CRITERIA))
        self.assertIn("NO TREE", results[0].note)

    def test_an_epoch_missing_an_arms_tree_reports_it_rather_than_skipping_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm in ("baseline", "conductor"):
                cell = "m/none/%s/t/r1" % arm
                (root / ("%s.json" % cell.replace("/", "__"))).write_text(
                    json.dumps({"cellId": cell, "arm": arm, "taskId": "t"})
                )
            tree = root / "trees" / "m__none__baseline__t__r1" / "repo"
            tree.mkdir(parents=True)
            (tree / "x.ts").write_text("1\n")
            results = jq.judge_epoch(root, scripted(reply(2, 2)), {"t": PROMPT},
                                     arms=("baseline", "conductor"), reps=1)
            self.assertEqual({r.outcome for r in results}, {"no_tree"})


# ---------------------------------------------------------------------------
# The rubric lane
# ---------------------------------------------------------------------------

class RubricTest(unittest.TestCase):
    def _full_results(self, arm_a="baseline", arm_b="conductor"):
        return [jq.CriterionResult("t", arm_a, arm_b, criterion, "win_a",
                                   "won every one of 6 runs in both presentation orders",
                                   runs(["baseline"] * 6, arm_a, arm_b), [],
                                   "m/none/%s/t/r1" % arm_a, "m/none/%s/t/r1" % arm_b)
                for criterion in jq.CRITERIA]

    def test_a_complete_record_satisfies_the_validator_it_will_be_read_by(self):
        record = jq.rubric_record("baseline", self._full_results(), jq.reviewer_label("qwen", 3))
        cb.validate_rubric(record)  # raises BenchError if it does not

    def test_the_reviewer_says_a_model_scored_it(self):
        """`aggregate_rubrics` medians whatever is on disk; a model record that reads
        like a hand-scored one would be averaged in under a heading claiming a human."""
        label = jq.reviewer_label("llamacpp/qwen3.8-27b", 3)
        self.assertIn("model-judge", label)
        self.assertIn("order-swapped", label)

    def test_a_criterion_with_no_usable_score_yields_no_record_rather_than_a_zero(self):
        """A zero is a score. The absence of a measurement is not one, and writing
        one where the other belongs is the failure this campaign has met three times."""
        partial = self._full_results()[:-1]
        self.assertIsNone(jq.rubric_record("baseline", partial, jq.reviewer_label("qwen", 3)))

    def test_a_criterion_whose_runs_all_failed_yields_no_record(self):
        broken = self._full_results()
        broken[2] = jq.CriterionResult("t", "baseline", "conductor", broken[2].criterion,
                                       "no_verdict", "all responses unusable",
                                       runs([None], invalid="empty response"), [],
                                       "m/none/baseline/t/r1", "m/none/conductor/t/r1")
        self.assertIsNone(jq.rubric_record("baseline", broken, jq.reviewer_label("qwen", 3)))

    def test_the_record_names_the_repetition_the_judge_actually_saw(self):
        record = jq.rubric_record("baseline", self._full_results(),
                                  jq.reviewer_label("qwen", 3))
        self.assertEqual(record["cellId"], "m/none/baseline/t/r1")

    def test_results_disagreeing_about_which_tree_was_judged_are_refused(self):
        """One record cannot describe two trees, and picking one would file the
        verdict against work the judge never saw."""
        mixed = self._full_results()
        mixed[1].cell_a = "m/none/baseline/t/r3"
        self.assertIsNone(jq.rubric_record("baseline", mixed, jq.reviewer_label("q", 3)))

    def test_the_record_carries_the_judges_reasons_as_findings(self):
        record = jq.rubric_record("baseline", self._full_results(), jq.reviewer_label("qwen", 3))
        self.assertTrue(record["findings"])
        self.assertTrue(all(isinstance(f, str) for f in record["findings"]))

    def test_the_losing_arms_record_scores_its_own_side(self):
        record = jq.rubric_record("conductor", self._full_results(), jq.reviewer_label("qwen", 3))
        cb.validate_rubric(record)
        self.assertEqual(set(record["scores"].values()), {1},
                         "arm B's scores, not arm A's")


class TruncationTest(unittest.TestCase):
    def test_a_side_cut_to_fit_the_window_is_recorded_on_that_criterion_only(self):
        """A judgement over a tree the judge only half saw is worth knowing about —
        and a note belongs to the criterion whose call was cut, not to its
        neighbours in the same run."""
        big = {"src/x.ts": "x".ljust(200, "y") + "\n"}
        pair = jq.make_pair("t", PROMPT, "baseline", "conductor", big, dict(big))
        original = jq.MAX_SIDE_BYTES
        jq.MAX_SIDE_BYTES = 50
        try:
            results = jq.compare(pair, scripted(reply(2, 2)),
                                 criteria=("structure", "testQuality"), reps=1)
        finally:
            jq.MAX_SIDE_BYTES = original
        first, second = results
        self.assertTrue(any("structure: a side was truncated" in n
                            for n in first.contamination))
        self.assertFalse(any("structure:" in n for n in second.contamination),
                         "testQuality must not carry structure's note")

    def test_an_untruncated_pair_records_nothing(self):
        pair = jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"a.ts": "1\n"}, {"a.ts": "2\n"})
        results = jq.compare(pair, scripted(reply(2, 2)), criteria=("structure",), reps=1)
        self.assertEqual(results[0].contamination, [])


class ThinkingBudgetTest(unittest.TestCase):
    """A thinking model can spend its whole budget before answering.

    Calibration on 2026-08-25 scored three of six known-answer cases `no_verdict`.
    The cause was not judgement: `finish_reason=length`, `content` 0 chars,
    `reasoning_content` 3,167 chars, `predicted_n` 700 — every token went into the
    chain of thought and none into the answer. Reported as "empty response", that
    is indistinguishable from a model that returned prose, and the two need
    opposite fixes.
    """

    def test_a_call_that_thought_past_its_budget_says_so(self):
        def truncated(prompt, seed):
            raise jq.JudgeUnusable(
                "the judge spent its whole token budget reasoning and never "
                "answered (finish_reason=length, 0 answer chars after 3167 "
                "reasoning chars) — raise max_tokens")
        pair = jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"a.ts": "1\n"}, {"a.ts": "2\n"})
        result = jq.compare(pair, truncated, criteria=("structure",), reps=1)[0]
        self.assertEqual(result.outcome, "no_verdict")
        self.assertIn("budget reasoning", result.note)
        self.assertNotIn("call failed", result.note,
                         "a truncated answer is not a transport failure")

    def test_the_default_answer_budget_leaves_room_to_think(self):
        """700 was chosen for a non-thinking model and is what broke calibration."""
        self.assertGreaterEqual(jq.DEFAULT_MAX_TOKENS, 2000)


class TimeoutBudgetCouplingTest(unittest.TestCase):
    """A timeout that cannot cover max_tokens at the observed rate truncates by
    construction, and the two are set independently.

    Run 1 at 3,000 tokens failed 11 comparisons with "spent its whole token budget
    reasoning". Run 2 at 6,000 fixed that and failed 11 with "timed out": at the
    measured 5.5-6.2 t/s, 6,000 tokens needs ~975-1090 s and the timeout was 600.
    Moving one constant surfaced the next one behind it. This is D42's shape — two
    timers that must agree, set in different places by different people.
    """

    def test_the_time_a_full_budget_needs_is_derived_not_guessed(self):
        needed = jq.minimum_timeout(6000)
        self.assertGreater(needed, 900,
                           "6,000 tokens at the observed floor rate cannot fit in 900 s")

    def test_a_timeout_too_small_for_its_budget_is_refused_at_construction(self):
        with self.assertRaises(ValueError) as caught:
            jq.http_judge("http://127.0.0.1:1", "m", timeout=600.0, max_tokens=6000)
        self.assertIn("timed out", str(caught.exception).lower() + " timed out")
        self.assertIn("6000", str(caught.exception))

    def test_a_consistent_pair_is_accepted(self):
        jq.http_judge("http://127.0.0.1:1", "m",
                      timeout=jq.minimum_timeout(6000), max_tokens=6000)

    def test_the_default_timeout_covers_the_default_budget(self):
        """The shipped pair must satisfy its own guard, or the default is the bug."""
        self.assertGreaterEqual(jq.DEFAULT_TIMEOUT,
                                jq.minimum_timeout(jq.DEFAULT_MAX_TOKENS))


class ControlUsabilityTest(unittest.TestCase):
    """Zero usable control runs is a broken instrument, not a judge that failed
    to tell two identical trees apart. Reporting them alike is the defect this
    campaign has met five times, and the fifth time was inside this guard."""

    def _case(self, control):
        # NOT named _outcome: unittest.TestCase uses that attribute internally.
        return jq.CaseOutcome("c", "structure", True, "correct", "", control)

    def test_no_usable_control_run_is_reported_as_an_instrument_failure(self):
        verdict = jq.judge_calibration_verdict(
            [self._case(jq.ControlResult("c", equal=0, valid=0, unusable=6))])
        self.assertFalse(verdict.trusted)
        self.assertIn("no usable", verdict.note.lower())
        self.assertNotIn("UNEQUALLY", verdict.note)
        self.assertEqual(verdict.control_failures, [],
                         "nothing was measured, so nothing discriminated")

    def test_a_genuine_discrimination_failure_still_reads_as_one(self):
        verdict = jq.judge_calibration_verdict(
            [self._case(jq.ControlResult("c", equal=1, valid=6, unusable=0))])
        self.assertFalse(verdict.trusted)
        self.assertIn("UNEQUALLY", verdict.note)
        self.assertEqual(verdict.control_failures, ["c"])

    def test_a_clean_control_passes(self):
        verdict = jq.judge_calibration_verdict(
            [self._case(jq.ControlResult("c", equal=6, valid=6, unusable=0))])
        self.assertTrue(verdict.trusted, verdict.note)


class ParallelJudgeTest(unittest.TestCase):
    """The judge's calls are independent, so they may overlap. What must not
    change is WHAT is computed — only when."""

    def _pair(self):
        return jq.make_pair("t", PROMPT, "baseline", "conductor",
                            {"a.ts": "1\n"}, {"a.ts": "2\n"})

    def test_parallel_and_serial_reach_the_same_verdict(self):
        serial = jq.compare(self._pair(), scripted(reply(3, 1)), reps=3, concurrency=1)
        parallel = jq.compare(self._pair(), scripted(reply(3, 1)), reps=3, concurrency=3)
        self.assertEqual([r.outcome for r in serial], [r.outcome for r in parallel])
        self.assertEqual([r.criterion for r in serial], [r.criterion for r in parallel],
                         "criteria must stay in their declared order")

    def test_calls_actually_overlap(self):
        """Without this the option is a no-op that reports success."""
        import threading
        live, peak, lock = [0], [0], threading.Lock()

        def slow(prompt, seed):
            with lock:
                live[0] += 1
                peak[0] = max(peak[0], live[0])
            try:
                time.sleep(0.05)
                return reply(2, 2)
            finally:
                with lock:
                    live[0] -= 1

        jq.compare(self._pair(), slow, criteria=("structure",), reps=3, concurrency=3)
        self.assertGreater(peak[0], 1, "no two calls were ever in flight together")

    def test_every_repetition_still_gets_its_own_seed_under_concurrency(self):
        seen, lock = [], __import__("threading").Lock()

        def recorder(prompt, seed):
            with lock:
                seen.append(seed)
            return reply(2, 2)

        jq.compare(self._pair(), recorder, criteria=("structure",), reps=3, concurrency=3)
        self.assertEqual(len(seen), 6, "three repetitions in each of two orders")
        self.assertEqual(sorted(set(seen)), [1, 2, 3])

    def test_both_presentation_orders_survive_concurrency(self):
        result = jq.compare(self._pair(), scripted(reply(3, 1)),
                            criteria=("structure",), reps=2, concurrency=3)[0]
        self.assertEqual({r.swapped for r in result.runs}, {False, True})


class UnmodifiedSeedTest(unittest.TestCase):
    """A tree identical to the seed is not a bad implementation. It is no
    implementation, and the two must not share a verdict.

    Epoch 14's conductor arm left the seed untouched on three of four tasks. Scored
    as a comparison, that produces "the other arm wins, every criterion, both
    orders, unanimous" — the most confident output the instrument can emit, saying
    only what the timeout already said.
    """

    SEED = {"src/x.ts": "export const f = 1;\n", "README.md": "# x\n"}

    def test_a_tree_identical_to_the_seed_is_recognised(self):
        self.assertTrue(jq.unmodified_seed(dict(self.SEED), self.SEED))

    def test_one_changed_byte_counts_as_work(self):
        touched = dict(self.SEED, **{"src/x.ts": "export const f = 2;\n"})
        self.assertFalse(jq.unmodified_seed(touched, self.SEED))

    def test_an_added_file_counts_as_work_even_with_the_seed_intact(self):
        added = dict(self.SEED, **{"tests/x.test.ts": "// a test\n"})
        self.assertFalse(jq.unmodified_seed(added, self.SEED))

    def test_a_deleted_seed_file_counts_as_work(self):
        self.assertFalse(jq.unmodified_seed({"README.md": "# x\n"}, self.SEED))

    def test_with_no_seed_to_compare_the_check_cannot_run_and_says_so(self):
        """Absent a seed the answer is unknown, and unknown must not read as
        'work was done' — that is the silent-pass this whole guard exists against."""
        self.assertIsNone(jq.unmodified_seed(dict(self.SEED), {}))

    def test_the_result_is_no_work_and_is_neither_a_tie_nor_a_loss(self):
        results = jq.no_work_result("t", "baseline", "conductor", ["conductor"])
        self.assertEqual({r.outcome for r in results}, {"no_work"})
        self.assertEqual(len(results), len(jq.CRITERIA))
        self.assertIn("NO WORK", results[0].note)
        self.assertIn("conductor", results[0].note)
        self.assertNotIn(jq.TIE, {r.outcome for r in results})

    def test_an_epoch_where_one_arm_did_nothing_reports_no_work_not_a_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, body in (("baseline", "export const f = 2;\n"),
                              ("conductor", "export const f = 1;\n")):
                cell = "m/none/%s/t/r1" % arm
                (root / ("%s.json" % cell.replace("/", "__"))).write_text(
                    json.dumps({"cellId": cell, "arm": arm, "taskId": "t", "rep": 1}))
                tree = root / "trees" / cell.replace("/", "__") / "repo" / "src"
                tree.mkdir(parents=True)
                (tree / "x.ts").write_text(body)
            results = jq.judge_epoch(
                root, scripted(reply(3, 1)), {"t": PROMPT},
                arms=("baseline", "conductor"), reps=1,
                seeds={"t": {"src/x.ts": "export const f = 1;\n"}})
            self.assertEqual({r.outcome for r in results}, {"no_work"},
                             "the conductor tree is the seed; there is nothing to judge")

    def test_when_both_arms_did_work_the_comparison_proceeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, body in (("baseline", "export const f = 2;\n"),
                              ("conductor", "export const f = 3;\n")):
                cell = "m/none/%s/t/r1" % arm
                (root / ("%s.json" % cell.replace("/", "__"))).write_text(
                    json.dumps({"cellId": cell, "arm": arm, "taskId": "t", "rep": 1}))
                tree = root / "trees" / cell.replace("/", "__") / "repo" / "src"
                tree.mkdir(parents=True)
                (tree / "x.ts").write_text(body)
            results = jq.judge_epoch(
                root, scripted(reply(3, 1)), {"t": PROMPT},
                arms=("baseline", "conductor"), reps=1,
                seeds={"t": {"src/x.ts": "export const f = 1;\n"}})
            self.assertNotIn("no_work", {r.outcome for r in results})


class TreeSelectionTest(unittest.TestCase):
    """Which repetition's tree an arm is represented by is a choice, not a lookup.

    With `--calibration-reps` an arm has several archived trees and they are
    different implementations. Taking whichever sorted last would attach the
    verdict — and the rubric record — to a tree at random.
    """

    def _cells(self, *specs):
        return [jq.ArchivedCell("m/none/%s/t/r%d" % (arm, rep), arm, "t", rep,
                                Path("/nowhere") if has_tree else None)
                for arm, rep, has_tree in specs]

    def test_the_lowest_repetition_with_a_tree_is_the_one_judged(self):
        cells = self._cells(("baseline", 3, True), ("baseline", 1, True),
                            ("baseline", 2, True))
        chosen = jq.select_trees(cells, "t")
        self.assertEqual(chosen["baseline"].rep, 1)

    def test_a_repetition_with_no_archived_tree_is_passed_over_not_selected(self):
        cells = self._cells(("baseline", 1, False), ("baseline", 2, True))
        self.assertEqual(jq.select_trees(cells, "t")["baseline"].rep, 2)

    def test_an_arm_with_no_tree_at_all_is_absent_rather_than_empty(self):
        cells = self._cells(("baseline", 1, False))
        self.assertEqual(jq.select_trees(cells, "t"), {})

    def test_the_repetitions_that_were_not_judged_are_named(self):
        cells = self._cells(("baseline", 1, True), ("baseline", 2, True),
                            ("baseline", 3, True))
        chosen = jq.select_trees(cells, "t")
        self.assertEqual(jq.unjudged_reps(cells, "t", chosen),
                         ["m/none/baseline/t/r2", "m/none/baseline/t/r3"])

    def test_judging_an_epoch_records_which_tree_each_side_was(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for arm, rep in (("baseline", 1), ("baseline", 2), ("conductor", 1)):
                cell = "m/none/%s/t/r%d" % (arm, rep)
                (root / ("%s.json" % cell.replace("/", "__"))).write_text(
                    json.dumps({"cellId": cell, "arm": arm, "taskId": "t", "rep": rep})
                )
                tree = root / "trees" / cell.replace("/", "__") / "repo"
                tree.mkdir(parents=True)
                (tree / "x.ts").write_text("const rep = %d;\n" % rep)
            results = jq.judge_epoch(root, scripted(reply(2, 2)), {"t": PROMPT},
                                     arms=("baseline", "conductor"), reps=1)
            self.assertEqual({r.cell_a for r in results}, {"m/none/baseline/t/r1"})
            self.assertTrue(any("were not judged" in note
                                for r in results for note in r.contamination),
                            "the unjudged repetition must be named, not dropped")


# ---------------------------------------------------------------------------
# Calibration
# ---------------------------------------------------------------------------

class CalibrationCorpusTest(unittest.TestCase):
    def setUp(self):
        self.cases = jq.load_calibration()

    def test_the_corpus_is_not_empty(self):
        self.assertGreaterEqual(len(self.cases), 5)

    def test_every_declared_length_direction_matches_the_bytes_on_disk(self):
        """`betterIsLonger` drives the length-bias split. Asserted rather than
        computed, it would be a guard believed for a reason nobody reproduced."""
        for case in self.cases:
            longer = (sum(len(v) for v in case.better.values())
                      > sum(len(v) for v in case.worse.values()))
            self.assertEqual(case.better_is_longer, longer, case.case_id)

    def test_the_corpus_reaches_the_size_of_real_inputs(self):
        """A calibration corpus has to match the real inputs in SIZE, not only in kind.

        The first corpus was 1-2 files and 187-860 rendered characters. Epoch 14's
        real trees are 8-9 files and up to 6,312. The judge passed calibration on
        the small fixtures and then exhausted its token budget on 16 of 30 real
        comparisons — a calibration that certified the wrong thing, because
        nothing checked that the cases resembled the job.

        The floors are stated tolerances taken from that measurement, not derived
        thresholds: a corpus that cannot reach the low end of the real range
        cannot predict behaviour there.
        """
        widest = max(len(c.better) for c in self.cases)
        longest = max(len(jq.render_side(c.better, "x")[0]) for c in self.cases)
        self.assertGreaterEqual(widest, 8,
                                "no case has as many files as a real tree (8-9)")
        self.assertGreaterEqual(longest, 4000,
                                "no case renders as large as a real tree (up to 6,312 chars)")

    def test_the_corpus_carries_both_length_directions(self):
        """A judge that just prefers more code must not be able to score 100%."""
        directions = {case.better_is_longer for case in self.cases}
        self.assertEqual(directions, {True, False})

    def test_the_better_and_worse_trees_differ_in_every_case(self):
        for case in self.cases:
            self.assertNotEqual(case.better, case.worse, case.case_id)

    def test_no_case_leaks_arm_identity_into_the_judges_view(self):
        for case in self.cases:
            for label, files in (("better", case.better), ("worse", case.worse)):
                stripped, _ = jq.strip_identity(dict(files))
                self.assertEqual(jq.residual_leaks(stripped), [],
                                 "%s/%s" % (case.case_id, label))


class CalibrationVerdictTest(unittest.TestCase):
    def setUp(self):
        self.cases = jq.load_calibration()

    def test_a_judge_that_reads_the_code_is_trusted(self):
        outcomes = jq.run_calibration(self.cases, oracle_for(self.cases), reps=2)
        verdict = jq.judge_calibration_verdict(outcomes)
        self.assertEqual(verdict.correct, len(self.cases))
        self.assertTrue(verdict.trusted, verdict.note)

    def test_a_judge_that_only_measures_length_is_caught_by_the_split(self):
        """It is right on every case where the better tree is longer and wrong on
        every case where it is shorter — which is what the two directions are for."""
        outcomes = jq.run_calibration(self.cases, prefers_longer, reps=2)
        verdict = jq.judge_calibration_verdict(outcomes)
        self.assertFalse(verdict.trusted)
        self.assertIn("LENGTH BIAS", verdict.length_bias)

    def test_a_judge_that_always_picks_the_first_slot_fails_its_own_control(self):
        outcomes = jq.run_calibration(self.cases, prefers_first, reps=2)
        verdict = jq.judge_calibration_verdict(outcomes)
        self.assertFalse(verdict.trusted)
        self.assertTrue(verdict.control_failures)
        self.assertEqual({o.outcome for o in outcomes}, {jq.TIE},
                         "position bias settles to a tie, so accuracy alone would "
                         "not have caught it — the control is what does")

    def test_no_cases_at_all_is_not_a_passing_score(self):
        verdict = jq.judge_calibration_verdict([])
        self.assertFalse(verdict.trusted)
        self.assertIn("NOT CALIBRATED", verdict.note)

    def test_the_control_counts_how_often_two_identical_trees_score_equally(self):
        control = jq.control_check(self.cases[0], oracle_for(self.cases), reps=2, base_seed=1)
        self.assertEqual(control.equal, control.valid)
        self.assertEqual(control.rate, 1.0)


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

class ReportTest(unittest.TestCase):
    def test_an_empty_run_says_the_instrument_produced_nothing(self):
        text = jq.render_report([])
        self.assertIn("gap in the instrument", text)
        self.assertNotIn("| tie |", text)

    def test_an_untrusted_judge_is_stated_above_its_own_verdicts(self):
        verdict = jq.judge_calibration_verdict([])
        text = jq.render_report(
            [jq.CriterionResult("t", "baseline", "conductor", "structure", "win_b",
                                "won every one of 6 runs in both presentation orders")],
            verdict,
        )
        self.assertIn("did not pass calibration", text)
        self.assertLess(text.index("did not pass calibration"), text.index("| baseline vs conductor"))

    def test_a_report_from_an_unchecked_judge_says_so_rather_than_omitting_it(self):
        """`--no-calibration` used to drop the section entirely, which reads as
        'there was nothing to say' rather than 'the judge was never checked'."""
        text = jq.render_report(
            [jq.CriterionResult("t", "baseline", "conductor", "structure", "win_a",
                                "note", runs(["baseline"] * 6))],
            calibration=None)
        self.assertIn("NOT CHECKED", text)
        self.assertLess(text.index("NOT CHECKED"), text.index("| baseline vs conductor"))

    def test_no_ratio_appears_anywhere_in_the_report(self):
        """Rubric scores have no true zero, so a quotient of two of them has no reading."""
        text = jq.render_report(
            [jq.CriterionResult("t", "baseline", "conductor", "structure", "win_a", "note",
                                runs(["baseline"] * 6))]
        )
        self.assertNotIn("×", text)
        self.assertIn("No ratio", text)


if __name__ == "__main__":
    unittest.main()

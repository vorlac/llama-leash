"""Tests for baseline-relative cost reporting.

The failure modes are all "reports a number that looks fine and means nothing":
a ratio against a run that never finished, a ratio against a single noisy sample
presented as though it were solid, and a missing measurement reported in the same
words as a failed run.
"""

import unittest

from ratios import (
    MIN_MEANINGFUL_MINUTES,
    Cell,
    Denominator,
    _ratio,
    baseline_median,
)


def cell(arm, task="t", rep=1, minutes=1.0, passed=True, timed_out=False, tokens=1000):
    return Cell(arm=arm, task=task, rep=rep, cell_id=f"m/none/{arm}/{task}/r{rep}",
                minutes=minutes, passed=passed, timed_out=timed_out, tokens=tokens)


class DenominatorTest(unittest.TestCase):
    def test_the_median_of_several_reps_is_the_denominator(self):
        cells = [cell("baseline", rep=1, minutes=2.0),
                 cell("baseline", rep=2, minutes=10.0),
                 cell("baseline", rep=3, minutes=3.0)]
        den = baseline_median(cells, "t", "minutes")
        self.assertEqual(den.value, 3.0, "the median, not the mean — one outlier must not carry it")
        self.assertEqual(den.samples, 3)
        self.assertEqual(den.note, "")

    def test_a_single_sample_is_usable_but_flagged(self):
        """It inherits its own noise multiplicatively; the reader must be told."""
        den = baseline_median([cell("baseline", minutes=5.0)], "t", "minutes")
        self.assertEqual(den.value, 5.0)
        self.assertIn("DEGRADED", den.note)

    def test_a_failed_baseline_is_not_a_measurement_of_how_long_the_work_takes(self):
        cells = [cell("baseline", minutes=30.0, passed=False),
                 cell("baseline", rep=2, minutes=30.0, timed_out=True)]
        den = baseline_median(cells, "t", "minutes")
        self.assertIsNone(den.value)
        self.assertFalse(den.usable)
        self.assertIn("no successful baseline", den.note)

    def test_a_missing_measurement_reads_differently_from_a_failed_run(self):
        """Two absences that call for opposite responses must not share wording.

        A baseline that FAILED is a result about the task. A measurement never
        archived is a gap in the instrument. Reporting them identically is the
        defect this campaign has met three times.
        """
        cells = [cell("baseline", tokens=None)]
        den = baseline_median(cells, "t", "tokens")
        self.assertIsNone(den.value)
        self.assertIn("gap in the instrument", den.note)
        self.assertNotIn("no successful baseline", den.note)


class RatioTest(unittest.TestCase):
    def test_a_ratio_against_an_unusable_denominator_is_withheld(self):
        self.assertEqual(_ratio(10.0, Denominator(None, 0, "x"), 0.0), "—")

    def test_a_tiny_denominator_reports_no_ratio_rather_than_a_loud_one(self):
        """A task baseline finishes in 40s makes a 2-minute run '3x' — true, not useful."""
        den = Denominator(0.5, 3, "")
        self.assertIn("floor", _ratio(2.0, den, MIN_MEANINGFUL_MINUTES))

    def test_an_ordinary_ratio_is_one_decimal_place(self):
        self.assertEqual(_ratio(12.0, Denominator(4.0, 3, ""), 1.0), "3.0×")


if __name__ == "__main__":
    unittest.main()

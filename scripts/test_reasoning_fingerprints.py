"""Tests for the deliberation fingerprint.

The corpus is two excerpts recorded verbatim in the 14.2 campaign register:
what a watchdog-killed planner was thinking when it died, and what a planner
facing the identical situation thought after the doctrine was told to state what
its checks match on. They are the only two samples that matter, because the
instrument exists to tell those two states apart.

Both texts contain the word "placeholder". The fingerprint this replaces counted
that word, scored both, and therefore measured nothing.
"""

import unittest

from reasoning_fingerprints import WINDOW_CHARS, deliberations, rate_per_1k

# Epoch 12, conductor/euler-cli-py: a planner working through the self-check,
# killed mid-word by the 900s watchdog still deliberating.
KILLED = (
    'No placeholders: I must avoid the literal strings "TBD", "TODO", "similar to", '
    '"<placeholder>", "and so on." Careful: the acceptance format string contains '
    "<name> <answer> <milliseconds>ms - that is quoting the acceptance criterion, not a "
    "placeholder for content. Hmm, the self-check rejects a <placeholder> standing in for "
    "real content. The format string is part of the spec; but to be safe, I will quote it "
    "exactly as the acceptance criterion does. I think that is acceptable - it is a quoted "
    "requirement. But a strict checker might flag <...> tokens"
)

# Epoch 13, same task, same rule, after the doctrine was told what it matches on.
APPLIED = (
    "Criterion 6 mentions the format from the task's own spec; the plan-writing doctrine "
    "says angle brackets quoting the task's spec are content, not a placeholder. Fine for "
    "acceptance. Criterion 7: tests/check_visible.py is not modified and still passes - "
    "guard, names the artifact."
)


class DiscriminationTest(unittest.TestCase):
    def test_the_two_states_the_instrument_exists_to_separate(self):
        self.assertGreaterEqual(len(deliberations(KILLED)), 3,
                                "hedging around the rule is the behaviour being counted")
        self.assertEqual(deliberations(APPLIED), [],
                         "applying the rule and moving on must score nothing")

    def test_both_texts_contain_the_word_the_old_fingerprint_counted(self):
        """The failure this replaces, pinned so it cannot come back."""
        self.assertIn("placeholder", KILLED.lower())
        self.assertIn("placeholder", APPLIED.lower())
        self.assertGreater(rate_per_1k(KILLED), rate_per_1k(APPLIED))


class ScoringTest(unittest.TestCase):
    def test_a_rule_reference_with_no_hedge_scores_nothing(self):
        """Naming the rule while complying with it is the GOOD behaviour."""
        self.assertEqual(deliberations("The self-check forbids a placeholder, so I wrote the code."), [])

    def test_a_hedge_with_no_rule_reference_scores_nothing(self):
        """Ordinary uncertainty about the task is not deliberation about a rule."""
        self.assertEqual(deliberations("Hmm, is the sort stable? Careful with the tie-break."), [])

    def test_distance_is_what_pairs_them(self):
        far = "Careful with the tie-break." + ("x" * (WINDOW_CHARS + 50)) + "the self-check applies."
        near = "Careful: does the self-check apply here?"
        self.assertEqual(deliberations(far), [], "a hedge and a rule far apart are unrelated")
        self.assertEqual(len(deliberations(near)), 1)

    def test_rate_is_defined_on_empty_input_but_a_caller_must_check_the_denominator(self):
        self.assertEqual(rate_per_1k(""), 0.0)
        self.assertEqual(deliberations(""), [])


if __name__ == "__main__":
    unittest.main()

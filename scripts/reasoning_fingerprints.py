"""Detect a reasoning BEHAVIOUR in a model's thinking, not a vocabulary.

The 14.2 campaign's first attempt at this counted the word "placeholder" in
planner reasoning, to measure whether a doctrine rule was causing the planner to
deliberate about the rule's applicability instead of proceeding. It measured
nothing useful: `euler-cli-py`'s seed `main` IS a placeholder that prints "not
runnable yet", so the planner says the word constantly while doing ordinary work.
Seventeen hits, sixteen of them irrelevant.

The behaviour has a different signature. A model deliberating about whether a
rule applies HEDGES, and it hedges NEAR the rule's own words: "Careful:", "Hmm",
"but a strict checker might", "to be safe", "I think that's acceptable". A model
that has been told what the rule matches on applies it and moves on in a clause.

So the unit is a hedge marker occurring within a window of a rule reference —
neither alone. That is more fragile than counting a noun, which is exactly why
the noun was chosen the first time and exactly why it failed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List

# Words that REFER to the mechanical checks a planner is judged against. Being a
# reference is the point: the domain may use any of them for its own reasons, and
# that is fine, because a bare reference scores nothing without a hedge beside it.
RULE_REFERENCE = re.compile(
    r"placeholder|self-check|rejected on sight|\bTBD\b|no-placeholder|checker",
    re.I,
)

# Hedging: the model reasoning about whether it is ALLOWED to do the thing,
# rather than doing it. Deliberately not "maybe" or "possibly", which appear in
# ordinary technical reasoning about the task itself.
HEDGE = re.compile(
    r"\bcareful\b|\bhmm+\b|to be safe|might flag|might be flagged|might trip|"
    r"a strict\b|strictly speaking|I think that'?s (?:acceptable|fine|ok)|"
    r"\bbut would\b|\bto be safe\b",
    re.I,
)

# How near a hedge must be to a rule reference to count as being ABOUT it. Wide
# enough to span a sentence boundary, narrow enough that a hedge about the task
# and a mention of the rule three paragraphs apart do not pair up.
WINDOW_CHARS = 240


@dataclass(frozen=True)
class Deliberation:
    """One hedge that sits within WINDOW_CHARS of a rule reference."""

    hedge: str
    rule: str
    excerpt: str


def deliberations(reasoning: str) -> List[Deliberation]:
    """Every hedge-near-a-rule-reference pairing in the text, in order.

    A rule reference with no hedge near it scores nothing: naming the rule while
    complying with it is the behaviour we want, not the one being counted.
    """
    rules = [(m.start(), m.group(0)) for m in RULE_REFERENCE.finditer(reasoning)]
    if not rules:
        return []
    found: List[Deliberation] = []
    for hedge in HEDGE.finditer(reasoning):
        if not hedge.group(0).strip():
            continue
        near = [r for r in rules if abs(r[0] - hedge.start()) <= WINDOW_CHARS]
        if not near:
            continue
        rule = min(near, key=lambda r: abs(r[0] - hedge.start()))
        lo = max(0, min(hedge.start(), rule[0]) - 40)
        hi = min(len(reasoning), max(hedge.end(), rule[0] + len(rule[1])) + 40)
        found.append(Deliberation(hedge.group(0), rule[1], reasoning[lo:hi].replace("\n", " ")))
    return found


def rate_per_1k(reasoning: str) -> float:
    """Deliberations per 1,000 characters, so a volume swing does not move it.

    Returns 0.0 for empty input — but a caller must check the denominator itself
    before reading a zero as a result. A fingerprint of zero over no reasoning at
    all is not a measurement, and this campaign has already once recorded such a
    zero as a confirmed prediction.
    """
    if not reasoning:
        return 0.0
    return 1000.0 * len(deliberations(reasoning)) / len(reasoning)

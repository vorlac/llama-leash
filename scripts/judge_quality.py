"""Blind paired comparison of two arms' work on the same prompt.

The campaign measures cost and correctness. Neither answers the question the
harness exists to move: whether the conductor arm's process — TDD discipline,
adversarial review, several perspectives — produces work a person would rather
keep than one model turn's output. If it cannot beat baseline on TEST quality
there is no upside to pay a 3-26x cost for, and that is the one metric never
taken.

Rubric scores are ordinal. A 6 is not twice a 3, so `score_a / score_b` means
nothing and no ratio appears here; the verdict is win / loss / tie plus a stated
reason, and the reason is the artifact the verdict summarizes.

Four properties this instrument is built around, each of which a shortcut would
quietly break:

  BLIND       A conductor tree is identifiable by inspection — the plugin writes
              `.conductor/runs/<id>/journal.jsonl` and `.conductor/state/alive.json`
              into the tree it worked in, and a doctrine cell carries
              `doctrine-prompt.md`. An unblinded judge reads a label and scores the
              label. `strip_identity` removes them and `residual_leaks` is what the
              test asserts against, so blinding is checked rather than claimed.
              (docs/build/CORPUS-MIGRATION.md section 6.3 named this first.)
  SWAPPED     Every comparison runs in both orders. An implementation that wins
              only when shown first did not win.
  REPEATED    n>=3 per order, each at a DIFFERENT SEED. A fixed seed at a fixed
              temperature makes llama.cpp deterministic, so repetitions at one
              seed are one sample printed three times and their agreement is an
              artifact of the sampler rather than evidence about the code.
  CONSERVATIVE  A judge that disagrees with itself is reported as a tie, not
              resolved by taking a majority. Resolving is picking one, which is
              the move this campaign spent thirteen epochs learning to distrust.

A response that does not parse is NOT a tie. "The judge could not answer" and
"the judge saw no difference" are different facts that call for opposite
responses, and reporting them in the same words is the defect met three times
already (D18's partial window, a fingerprint scoring zero over an empty
denominator, a ratio wording a missing measurement like a failed run).

POLARITY. `RUBRIC_CRITERIA` fixes five criteria but no source in this repository
states which end of `RUBRIC_SCORES` is good, and `deadCode` / `overBuilding` are
named for the defect rather than the virtue. This module pins it: HIGHER IS
BETTER on all five, so `deadCode: 3` means none was found. Every criterion then
reads the same way down a report row, and the paired winner is the higher score
on every axis without a per-criterion exception to remember.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import conductor_bench as cb
from epoch_review import source_files

REPO = Path(__file__).resolve().parent.parent
CALIBRATION_DIR = REPO / "bench" / "judge-calibration"

# The rubric vocabulary is conductor_bench's, imported rather than restated: two
# copies of a closed set drift, and the validator only enforces one of them.
CRITERIA = cb.RUBRIC_CRITERIA
SCORES = cb.RUBRIC_SCORES

ARMS = ("baseline", "doctrine", "conductor")

# A reason of two words is a verdict wearing a reason's clothes. The floor is a
# stated tolerance, not a measurement: chosen here so that "better" and "it is
# cleaner" are both refused and anything naming a file or a behaviour passes.
MIN_REASON_CHARS = 40

# A thinking model spends most of its budget before it answers. 700 was chosen
# for a model that answers immediately and is exactly what broke the first
# calibration: `finish_reason=length`, 0 answer characters, 3,167 characters of
# reasoning, every one of the 700 tokens gone. The budget has to cover the
# deliberation AND the sentence at the end of it.
#
# 3,000 was the second guess and it failed the same way on real trees rather than
# on calibration fixtures: 16 of 30 comparisons in the first full run returned
# `no_verdict` with the same message. Bigger trees are more to deliberate over,
# so the budget has to be set against the real inputs — which is also why the
# calibration corpus now has to reach their size.
DEFAULT_MAX_TOKENS = 6000

# How many judge calls may be in flight. Each is an independent scoring of a
# fixed pair, so they overlap freely; the server has three slots and sat at one
# busy through a whole campaign epoch.
DEFAULT_CONCURRENCY = 3

# The slowest per-slot generation observed while three slots were busy on real
# trees was 5.12 t/s. The floor is set under that so a timeout derived from it
# still covers a call that runs slower than anything yet measured.
FLOOR_TOKENS_PER_SECOND = 4.0

# Prefill, queueing behind other slots, and the request round trip, none of which
# is generation and all of which happens before the first token.
FIXED_OVERHEAD_SECONDS = 120.0


def minimum_timeout(max_tokens: int,
                    rate: float = FLOOR_TOKENS_PER_SECOND) -> float:
    """The wall clock a call needs if it spends its whole budget generating.

    A timeout below this truncates by construction, so it is derived rather than
    chosen. Run 1 failed on a token budget too small to answer in; run 2 raised
    the budget and failed on a timeout too small to spend it in. Two constants
    that must agree, set independently — which is D42's shape exactly.
    """
    return FIXED_OVERHEAD_SECONDS + (max_tokens / rate)


DEFAULT_TIMEOUT = minimum_timeout(DEFAULT_MAX_TOKENS)


class JudgeUnusable(RuntimeError):
    """The call completed and carried no answer, with the reason it carried none.

    Distinct from a transport failure on purpose. "The server was unreachable"
    and "the model reasoned past its token budget" are both empty answers and
    they need opposite fixes, so they must not arrive worded alike.
    """


# Per side, before the judge's own context is exhausted by furniture. A side cut
# off mid-file is a comparison against a tree the judge never saw, so truncation
# is marked in the text and recorded on the pair rather than done silently.
MAX_SIDE_BYTES = 24_000


# ---------------------------------------------------------------------------
# Blinding
# ---------------------------------------------------------------------------

# `source_files` already drops `.git`, `.conductor`, `node_modules`, `.opencode`,
# `__pycache__` and the hidden `gauge/`. These are the identity-bearing paths it
# does not, named in docs/build/CORPUS-MIGRATION.md section 6.3. Dropping them
# again here costs nothing and means the blinding does not depend on another
# module's skip list staying what it is today.
IDENTIFYING_BASENAMES = ("doctrine-prompt.md",)
IDENTIFYING_PATH_PARTS = (".conductor", ".opencode", ".git", "node_modules", "__pycache__")

# Identity in file CONTENT: a comment naming the process, a run id, the harness,
# the model. Ordered longest-match-first so the harness name is consumed before
# the bare arm word inside it.
IDENTITY_TOKENS: Sequence[Tuple[str, "re.Pattern[str]"]] = (
    ("run-id", re.compile(r"\br-\d{8}-[0-9a-f]{4}\b")),
    ("harness", re.compile(r"\b(?:llama[-_.]?leash|llama[-_.]?harness|opencode|llama\.cpp)\b", re.I)),
    ("model", re.compile(r"\bqwen[\w.\-]*", re.I)),
    ("arm-name", re.compile(r"\b(?:baseline|doctrine|conductor)s?\b", re.I)),
)

# Every redaction collapses to ONE marker. A per-kind marker would tell the judge
# which kind of thing was hidden, which is most of what the strip exists to hide.
REDACTION = "[redacted]"


@dataclass(frozen=True)
class Leak:
    """One place arm identity was found, and what kind of tell it was."""

    path: str
    kind: str
    excerpt: str


def _content_leaks(path: str, text: str) -> List[Leak]:
    found: List[Leak] = []
    for kind, pattern in IDENTITY_TOKENS:
        for match in pattern.finditer(text):
            found.append(Leak(path, kind, match.group(0)))
    return found


def _path_is_identifying(path: str) -> bool:
    parts = Path(path).parts
    if any(part in IDENTIFYING_PATH_PARTS for part in parts):
        return True
    return Path(path).name in IDENTIFYING_BASENAMES


def strip_identity(files: Dict[str, str]) -> Tuple[Dict[str, str], List[Leak]]:
    """Drop identity-bearing files, redact identity-bearing text, report both.

    The leak list is the point, not a byproduct. A redaction marker is itself a
    channel — a side carrying `[redacted]` where the other carries none has told
    the judge something — so a comparison whose two sides were redacted unequally
    is reported as contaminated rather than scored as though it were clean.
    """
    kept: Dict[str, str] = {}
    leaks: List[Leak] = []
    for path in sorted(files):
        if _path_is_identifying(path):
            leaks.append(Leak(path, "path", path))
            continue
        text = files[path]
        leaks.extend(_content_leaks(path, text))
        for _kind, pattern in IDENTITY_TOKENS:
            text = pattern.sub(REDACTION, text)
        kept[path] = text
    return kept, leaks


def residual_leaks(files: Dict[str, str]) -> List[Leak]:
    """Every identity marker still present after a strip. Empty is the contract."""
    found: List[Leak] = []
    for path in sorted(files):
        if _path_is_identifying(path):
            found.append(Leak(path, "path", path))
        found.extend(_content_leaks(path, files[path]))
    return found


def load_tree(root: Any) -> Dict[str, str]:
    """An archived cell's produced source, harness furniture already removed."""
    return source_files(Path(root))


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------

def render_side(files: Dict[str, str], label: str,
                max_bytes: Optional[int] = None) -> Tuple[str, bool]:
    """One implementation as text, and whether it had to be cut short.

    The budget is resolved when the function runs, not when it is defined: a
    default bound at import time freezes the limit for the life of the process
    and leaves no way to exercise the truncation path at all.
    """
    if max_bytes is None:
        max_bytes = MAX_SIDE_BYTES
    lines = ["=== %s ===" % label]
    used = 0
    truncated = False
    for path in sorted(files):
        body = files[path]
        remaining = max_bytes - used
        if remaining <= 0:
            lines.append("--- %s --- (omitted: side budget exhausted)" % path)
            truncated = True
            continue
        if len(body) > remaining:
            body = body[:remaining] + "\n... (file truncated)"
            truncated = True
        used += len(body)
        lines.append("--- %s ---" % path)
        lines.append(body.rstrip("\n"))
    if len(files) == 0:
        lines.append("(no files)")
    return "\n".join(lines) + "\n", truncated


# What each criterion asks, in the terms the two axes are actually about. The
# code axis is four of these; the test axis is `testQuality` alone and is the one
# that decides whether the harness has a reason to exist.
CRITERION_QUESTION = {
    "structure": (
        "Does the implementation do what the task asked, and is it the simple "
        "version of that? Does it handle the cases the task names?"
    ),
    "decomposition": (
        "Is the work in pieces that each do one thing, with names that say what "
        "they do — without splitting anything for the sake of splitting it?"
    ),
    "testQuality": (
        "NOT test count. Does each test fail for the reason it claims? Does it "
        "test behaviour rather than restate the implementation? Does it cover "
        "the edges the task names? Would it catch a regression a later change "
        "might introduce?"
    ),
    "deadCode": (
        "Is anything present that nothing uses and nothing asked for — an unused "
        "function, an unreachable branch, a leftover scaffold? A higher score "
        "means LESS of this."
    ),
    "overBuilding": (
        "Is there machinery the task did not ask for — configuration, an "
        "abstraction with one implementation, an extension point nothing "
        "extends? A higher score means LESS of this."
    ),
}

JUDGE_INSTRUCTIONS = """You are comparing two implementations of the same programming task.

You do not know who wrote either one. Judge only the code in front of you.

THE TASK THE AUTHORS WERE GIVEN:
{prompt}

WHAT TO JUDGE — {criterion}:
{question}

Score each implementation from 0 to 3 on this one criterion, where 3 is best and
0 is worst. Higher is always better, including on criteria named for a defect.

{first}
{second}

Answer with one JSON object and nothing else, no prose before or after:
{{"score1": <0-3>, "score2": <0-3>, "reason": "<one or two sentences naming the specific files, functions or lines that decided it>"}}

The reason must point at something concrete in the code. If the two are equally
good on this criterion, give them the same score and say why they are equal."""


def build_prompt(task_prompt: str, criterion: str, first: str, second: str) -> str:
    return JUDGE_INSTRUCTIONS.format(
        prompt=task_prompt.strip(),
        criterion=criterion,
        question=CRITERION_QUESTION[criterion],
        first=first,
        second=second,
    )


# ---------------------------------------------------------------------------
# Parsing a response
# ---------------------------------------------------------------------------

_JSON_OBJECT = re.compile(r"\{[^{}]*\}", re.S)


@dataclass(frozen=True)
class Reply:
    """A parsed judge response, or the reason it is not one."""

    score_first: Optional[int]
    score_second: Optional[int]
    reason: str
    invalid: str  # empty exactly when the reply is usable

    @property
    def ok(self) -> bool:
        return not self.invalid


def _invalid(why: str) -> Reply:
    return Reply(None, None, "", why)


def parse_reply(text: str) -> Reply:
    """The last JSON object in a response, validated, or a stated refusal.

    The LAST object rather than the first: a model that thinks out loud before
    answering emits example objects on the way, and the answer is the one it
    stopped on. An unparseable reply is an instrument failure and says so — it is
    never folded into a tie, because "could not answer" and "saw no difference"
    call for opposite responses.
    """
    if not text or not text.strip():
        return _invalid("empty response")
    matches = _JSON_OBJECT.findall(text)
    if not matches:
        return _invalid("no JSON object in the response")
    try:
        document = json.loads(matches[-1])
    except ValueError as exc:
        return _invalid("the JSON object did not parse: %s" % exc)
    if not isinstance(document, dict):
        return _invalid("the response was not an object")
    parsed: List[int] = []
    for key in ("score1", "score2"):
        value = document.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            return _invalid("%s was %r, not an integer" % (key, value))
        if value not in SCORES:
            return _invalid("%s was %r, outside %s" % (key, value, list(SCORES)))
        parsed.append(value)
    reason = document.get("reason")
    if not isinstance(reason, str):
        return _invalid("reason was %r, not text" % (reason,))
    reason = reason.strip()
    if len(reason) < MIN_REASON_CHARS:
        # A winner with no stated reason is unauditable, so a reason too short to
        # be one makes the verdict unusable rather than merely thin.
        return _invalid("the reason is %d characters, under the %d-character floor"
                        % (len(reason), MIN_REASON_CHARS))
    return Reply(parsed[0], parsed[1], reason, "")


# ---------------------------------------------------------------------------
# One comparison
# ---------------------------------------------------------------------------

TIE = "tie"

# What a comparison can conclude. `no_verdict` and `no_tree` are deliberately not
# `tie`: one is a broken instrument, the other a missing input, and a tie is a
# finding about the code.
OUTCOMES = ("win_a", "win_b", TIE, "no_verdict", "no_tree", "no_work")


@dataclass(frozen=True)
class Run:
    """One judge call: which side it preferred, and which arm that side was."""

    criterion: str
    swapped: bool
    rep: int
    seed: int
    side_preferred: Optional[str]  # "first" | "second" | "tie", before un-swapping
    winner: Optional[str]          # arm id | "tie"
    score_a: Optional[int]
    score_b: Optional[int]
    reason: str
    invalid: str


def _settle_run(reply: Reply, arm_a: str, arm_b: str, swapped: bool,
                criterion: str, rep: int, seed: int) -> Run:
    """Un-swap one reply back onto arm identities."""
    if not reply.ok:
        return Run(criterion, swapped, rep, seed, None, None, None, None, "", reply.invalid)
    first, second = reply.score_first, reply.score_second
    if first == second:
        side = TIE
    else:
        side = "first" if first > second else "second"
    # When swapped, arm B was shown first.
    score_a, score_b = (second, first) if swapped else (first, second)
    if side == TIE:
        winner = TIE
    elif (side == "first") != swapped:
        winner = arm_a
    else:
        winner = arm_b
    return Run(criterion, swapped, rep, seed, side, winner, score_a, score_b, reply.reason, "")


def settle(runs: Sequence[Run], arm_a: str, arm_b: str) -> Tuple[str, str]:
    """The outcome of one criterion's runs, and the sentence explaining it.

    Unanimity or tie. Taking a majority over a judge that contradicts itself is
    resolving the disagreement by picking one, which is exactly the move the
    order-swap and the repetitions exist to refuse.
    """
    if not runs:
        return ("no_verdict", "no judge responses")
    broken = [run for run in runs if run.invalid]
    if broken:
        kinds = sorted({run.invalid for run in broken})
        return ("no_verdict",
                "%d of %d responses were unusable (%s) — an instrument failure, "
                "not a tie" % (len(broken), len(runs), "; ".join(kinds)))
    orders = {run.swapped for run in runs}
    if len(orders) < 2:
        return ("no_verdict",
                "only one presentation order ran, so position bias is untested")
    winners = {run.winner for run in runs}
    if len(winners) == 1:
        only = winners.pop()
        if only == TIE:
            return (TIE, "unanimous over %d runs in both orders: no difference" % len(runs))
        side = "win_a" if only == arm_a else "win_b"
        return (side, "won every one of %d runs in both presentation orders" % len(runs))
    sides = {run.side_preferred for run in runs}
    if len(sides) == 1 and sides != {TIE}:
        only_side = sides.pop()
        return (TIE,
                "POSITION BIAS: the judge preferred the %s implementation in all "
                "%d runs regardless of which arm was there — it is reading "
                "position, not code" % (only_side, len(runs)))
    return (TIE,
            "the judge disagreed with itself across %d runs (%s) — reported as a "
            "tie rather than resolved by picking one"
            % (len(runs), ", ".join(sorted(str(w) for w in winners))))


@dataclass
class CriterionResult:
    task_id: str
    arm_a: str
    arm_b: str
    criterion: str
    outcome: str
    note: str
    runs: List[Run] = field(default_factory=list)
    contamination: List[str] = field(default_factory=list)
    # Which repetition's tree each side actually was. An arm run with
    # `--calibration-reps` has several, they are not the same tree, and a rubric
    # record filed against the wrong one attributes a judgement to work the judge
    # never saw.
    cell_a: str = ""
    cell_b: str = ""

    @property
    def usable(self) -> List[Run]:
        """Runs whose reply parsed. A score carried by an unusable reply is not a
        score, and it must not reach a median just because the field is set."""
        return [r for r in self.runs if not r.invalid]

    @property
    def scores_a(self) -> List[int]:
        return [r.score_a for r in self.usable if r.score_a is not None]

    @property
    def scores_b(self) -> List[int]:
        return [r.score_b for r in self.usable if r.score_b is not None]

    @property
    def reasons(self) -> List[str]:
        return [r.reason for r in self.usable if r.reason]


@dataclass(frozen=True)
class Pair:
    """Two arms' finished trees for one task, ready to be shown to a judge."""

    task_id: str
    task_prompt: str
    arm_a: str
    arm_b: str
    files_a: Dict[str, str]
    files_b: Dict[str, str]
    leaks_a: List[Leak] = field(default_factory=list)
    leaks_b: List[Leak] = field(default_factory=list)
    cell_a: str = ""
    cell_b: str = ""

    @property
    def contamination(self) -> List[str]:
        """Why this pair may not be blind, in the reader's words. Empty is clean."""
        notes: List[str] = []
        if len(self.leaks_a) != len(self.leaks_b):
            notes.append(
                "asymmetric redaction (%d marker(s) on one side, %d on the other): "
                "the redaction marker is itself a tell"
                % (len(self.leaks_a), len(self.leaks_b))
            )
        for label, files in (("A", self.files_a), ("B", self.files_b)):
            remaining = residual_leaks(files)
            if remaining:
                notes.append("side %s still carries %d identity marker(s): %s"
                             % (label, len(remaining),
                                ", ".join(sorted({leak.kind for leak in remaining}))))
        return notes


def make_pair(task_id: str, task_prompt: str, arm_a: str, arm_b: str,
              raw_a: Dict[str, str], raw_b: Dict[str, str],
              cell_a: str = "", cell_b: str = "") -> Pair:
    files_a, leaks_a = strip_identity(raw_a)
    files_b, leaks_b = strip_identity(raw_b)
    return Pair(task_id, task_prompt, arm_a, arm_b, files_a, files_b, leaks_a, leaks_b,
                cell_a, cell_b)


# A judge is any callable from a prompt and a seed to the model's text. The live
# one talks HTTP; the tests hand in a function, which is why nothing here needs a
# server to be exercised.
Judge = Callable[[str, int], str]


def seeds_for(reps: int, base: int = 1) -> List[int]:
    """One distinct seed per repetition.

    Repetitions at a single seed are one sample printed N times: llama.cpp is
    deterministic given a seed and a sampler, so their agreement measures the
    sampler and not the code. Distinctness is the whole content of this function
    and `test_judge_quality` pins it.
    """
    if reps < 1:
        raise ValueError("reps must be at least 1, got %r" % reps)
    return [base + index for index in range(reps)]


def compare(pair: Pair, judge: Judge, criteria: Sequence[str] = CRITERIA,
            reps: int = 3, base_seed: int = 1,
            concurrency: int = DEFAULT_CONCURRENCY) -> List[CriterionResult]:
    """Every criterion, both orders, `reps` repetitions each at its own seed.

    The calls are issued concurrently because none of them depends on another's
    result: each scores a fixed pair of trees, and `settle` aggregates over an
    unordered set of runs. Concurrency therefore changes when the work happens and
    not what is computed, which is what the serial-equals-parallel test pins.
    """
    jobs: List[Tuple[str, bool, int, int, str]] = []
    notes_for: Dict[str, List[str]] = {}

    # Rendering is pure and cheap, so it happens up front: the pool then sees
    # fully independent items sharing nothing.
    for criterion in criteria:
        notes = list(pair.contamination)
        for swapped in (False, True):
            near, far = ((pair.files_b, pair.files_a) if swapped
                         else (pair.files_a, pair.files_b))
            first, cut_first = render_side(near, "Implementation 1")
            second, cut_second = render_side(far, "Implementation 2")
            if cut_first or cut_second:
                notes.append("%s: a side was truncated to fit the judge's window"
                             % criterion)
            prompt = build_prompt(pair.task_prompt, criterion, first, second)
            for rep, seed in enumerate(seeds_for(reps, base_seed), start=1):
                jobs.append((criterion, swapped, rep, seed, prompt))
        notes_for[criterion] = sorted(set(notes))

    def run_one(job: Tuple[str, bool, int, int, str]) -> Run:
        criterion, swapped, rep, seed, prompt = job
        try:
            text = judge(prompt, seed)
        except JudgeUnusable as exc:
            reply = _invalid(str(exc))
        except Exception as exc:  # transport, timeout, a dead server
            reply = _invalid("the judge call failed: %s" % str(exc)[:200])
        else:
            reply = parse_reply(text)
        return _settle_run(reply, pair.arm_a, pair.arm_b, swapped, criterion, rep, seed)

    if concurrency > 1 and len(jobs) > 1:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            runs = list(pool.map(run_one, jobs))
    else:
        runs = [run_one(job) for job in jobs]

    by_criterion: Dict[str, List[Run]] = dict((c, []) for c in criteria)
    for run in runs:
        by_criterion[run.criterion].append(run)

    results: List[CriterionResult] = []
    for criterion in criteria:
        mine = by_criterion[criterion]
        outcome, note = settle(mine, pair.arm_a, pair.arm_b)
        results.append(CriterionResult(pair.task_id, pair.arm_a, pair.arm_b,
                                       criterion, outcome, note, mine,
                                       notes_for[criterion],
                                       pair.cell_a, pair.cell_b))
    return results


def unmodified_seed(files: Dict[str, str], seed: Dict[str, str]) -> Optional[bool]:
    """Whether an arm's tree is byte-identical to the seed it started from.

    None when there is no seed to compare against — a corpus task whose files are
    not inline in the manifest. Unknown must not collapse into False, because
    False here reads as "the arm did work" and would restore exactly the silent
    pass this guard exists to prevent.
    """
    if not seed:
        return None
    return files == seed


def no_work_result(task_id: str, arm_a: str, arm_b: str,
                   idle: Sequence[str]) -> List[CriterionResult]:
    """A comparison where an arm produced nothing. Not a loss, and not a tie.

    Epoch 14's conductor arm left the seed untouched on three of four tasks. Scored
    as a comparison that yields "the other arm wins, every criterion, both orders,
    unanimous" — the most confident verdict this instrument can produce, carrying
    no information the exit status did not already have. A quality lane that
    reports it as a quality finding is measuring its own inputs.
    """
    note = ("NO WORK: %s left the seed byte-identical, so there is no "
            "implementation to judge — this is the outcome the pass/fail already "
            "records, not a quality result" % ", ".join(idle))
    return [CriterionResult(task_id, arm_a, arm_b, criterion, "no_work", note)
            for criterion in CRITERIA]


def missing_tree_result(task_id: str, arm_a: str, arm_b: str,
                        absent: Sequence[str]) -> List[CriterionResult]:
    """A comparison that could not happen, said loudly on every criterion.

    Never a tie. A tie is a statement about two implementations, and there are
    not two here.
    """
    note = "NO TREE: %s produced no archived tree for this task" % ", ".join(absent)
    return [CriterionResult(task_id, arm_a, arm_b, criterion, "no_tree", note)
            for criterion in CRITERIA]


# ---------------------------------------------------------------------------
# The rubric lane
# ---------------------------------------------------------------------------

def reviewer_label(model: str, reps: int) -> str:
    """Who scored it — and that it was not a person.

    `aggregate_rubrics` takes a median over whatever records are on disk, so a
    model-scored record indistinguishable from a hand-scored one would let the
    two be averaged together under a heading that says a human read them.
    """
    return "model-judge %s (blind paired, order-swapped, n=%d per order)" % (model, reps)


def rubric_record(arm: str, results: Sequence[CriterionResult],
                  reviewer: str) -> Optional[Dict[str, Any]]:
    """One arm's rubric record for one task, or None when a criterion has no score.

    A record needs all five criteria. A partial one cannot be written, and
    writing a zero for the missing criterion would be a score where there was a
    gap — reporting "measured nothing" in the same shape as "scored badly", which
    is the failure this campaign has now met three times. So the answer is None
    and the caller reports the omission.

    The cell is read off the results rather than supplied, so the record names the
    repetition whose tree the judge actually saw. Results that disagree about it
    are refused: one record cannot describe two trees.
    """
    cell_ids = {r.cell_a if r.arm_a == arm else r.cell_b
                for r in results if arm in (r.arm_a, r.arm_b)}
    cell_ids.discard("")
    if len(cell_ids) != 1:
        return None
    cell_id = cell_ids.pop()
    scores: Dict[str, int] = {}
    findings: List[str] = []
    notes: List[str] = []
    for criterion in CRITERIA:
        mine = [r for r in results if r.criterion == criterion]
        if not mine:
            return None
        values: List[int] = []
        for result in mine:
            values.extend(result.scores_a if result.arm_a == arm else
                          result.scores_b if result.arm_b == arm else [])
        if not values:
            return None
        scores[criterion] = cb.median_int(values)
        for result in mine:
            verdict = _verdict_for(result, arm)
            notes.append("%s vs %s — %s: %s" % (criterion, _other(result, arm), verdict, result.note))
            if result.reasons:
                findings.append("%s: %s" % (criterion, result.reasons[0]))
    return {
        "cellId": cell_id,
        "reviewer": reviewer,
        "scores": scores,
        "findings": findings,
        "notes": "\n".join(notes),
    }


def _other(result: CriterionResult, arm: str) -> str:
    return result.arm_b if result.arm_a == arm else result.arm_a


def _verdict_for(result: CriterionResult, arm: str) -> str:
    if result.outcome in ("no_verdict", "no_tree"):
        return result.outcome
    if result.outcome == TIE:
        return TIE
    winner = result.arm_a if result.outcome == "win_a" else result.arm_b
    return "win" if winner == arm else "loss"


# ---------------------------------------------------------------------------
# Calibration — can this judge separate cases whose answer is already known?
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationCase:
    case_id: str
    criterion: str
    prompt: str
    better: Dict[str, str]
    worse: Dict[str, str]
    why: str
    better_is_longer: bool


def load_calibration(directory: Any = CALIBRATION_DIR) -> List[CalibrationCase]:
    """Every known-answer case on disk, in filename order."""
    root = Path(directory)
    cases: List[CalibrationCase] = []
    for path in sorted(root.glob("*.json")):
        document = json.loads(path.read_text())
        case = CalibrationCase(
            case_id=document["id"],
            criterion=document["criterion"],
            prompt=document["prompt"],
            better=document["better"],
            worse=document["worse"],
            why=document["why"],
            better_is_longer=bool(document["betterIsLonger"]),
        )
        if case.criterion not in CRITERIA:
            raise ValueError("%s: criterion %r is outside %s"
                             % (path, case.criterion, list(CRITERIA)))
        cases.append(case)
    return cases


@dataclass(frozen=True)
class ControlResult:
    """What the judge did when shown the SAME implementation on both sides.

    docs/build/CORPUS-MIGRATION.md section 6.3 asks for deliberately mislabelled
    cells. Two copies of one tree is the sharpest form of that, because the right
    answer is known with certainty rather than by argument — but "did it call a
    tie" is not the useful question, since `settle` collapses a position-biased
    judge to a tie anyway. The useful question is how often it gave the two
    IDENTICAL sides the SAME SCORE. That fraction is the judge's noise floor on
    this criterion, and a comparison whose margin sits inside it is not a
    difference the judge can see.
    """

    case_id: str
    equal: int
    valid: int
    unusable: int

    @property
    def usable(self) -> bool:
        """Whether the control measured anything at all."""
        return self.valid > 0

    @property
    def rate(self) -> float:
        """Meaningful only when `usable`. Zero valid runs has no rate, and the
        callers must branch on `usable` rather than read 0.0 as a bad score."""
        return (self.equal / self.valid) if self.valid else 0.0

    @property
    def summary(self) -> str:
        if not self.valid:
            return "no usable response on identical inputs"
        return "%d/%d runs scored two identical trees equally" % (self.equal, self.valid)


# A stated tolerance, not a measurement: a judge asked to score one tree against
# a byte-identical copy of itself should say "equal" every time, and this is how
# far short of that this campaign will still act on the verdicts.
CONTROL_EQUAL_FLOOR = 0.8


def control_check(case: "CalibrationCase", judge: "Judge", reps: int,
                  base_seed: int) -> ControlResult:
    """Show the judge one implementation twice and count how often it agrees."""
    pair = make_pair(case.case_id, case.prompt, "copy-a", "copy-b",
                     dict(case.better), dict(case.better))
    result = compare(pair, judge, criteria=(case.criterion,), reps=reps,
                     base_seed=base_seed)[0]
    valid = [run for run in result.runs if not run.invalid]
    equal = sum(1 for run in valid if run.score_a == run.score_b)
    return ControlResult(case.case_id, equal, len(valid),
                         len(result.runs) - len(valid))


@dataclass(frozen=True)
class CaseOutcome:
    case_id: str
    criterion: str
    better_is_longer: bool
    outcome: str  # "correct" | "wrong" | "tie" | "no_verdict"
    note: str
    control: ControlResult


def run_calibration(cases: Sequence[CalibrationCase], judge: Judge, reps: int = 3,
                    base_seed: int = 1) -> List[CaseOutcome]:
    """Score each known-answer case, plus its identical-pair control."""
    out: List[CaseOutcome] = []
    for case in cases:
        pair = make_pair(case.case_id, case.prompt, "better", "worse",
                         dict(case.better), dict(case.worse))
        result = compare(pair, judge, criteria=(case.criterion,), reps=reps,
                         base_seed=base_seed)[0]
        if result.outcome == "win_a":
            outcome = "correct"
        elif result.outcome == "win_b":
            outcome = "wrong"
        elif result.outcome == "no_verdict":
            outcome = "no_verdict"
        else:
            outcome = TIE
        out.append(CaseOutcome(case.case_id, case.criterion, case.better_is_longer,
                               outcome, result.note,
                               control_check(case, judge, reps, base_seed)))
    return out


# A stated tolerance, not a derived threshold. Chosen for this instrument on the
# grounds that the calibration cases are deliberately obvious — a seeded defect,
# a test that asserts nothing — so a judge below this cannot separate obvious
# cases and therefore cannot be trusted on subtle ones. It is a decision about
# what this campaign will act on, and it is recorded as one.
CALIBRATION_FLOOR = 0.75


@dataclass(frozen=True)
class CalibrationVerdict:
    accuracy: float
    correct: int
    total: int
    trusted: bool
    length_bias: str
    control_failures: List[str]
    control_detail: str
    note: str


def judge_calibration_verdict(outcomes: Sequence[CaseOutcome],
                              floor: float = CALIBRATION_FLOOR) -> CalibrationVerdict:
    """Whether this judge has earned the right to be believed on the real trees.

    Accuracy alone can be earned for the wrong reason. A judge that always
    prefers the longer implementation scores well on every case where the better
    one is longer and zero on every case where it is shorter, so the corpus
    carries both directions and the split is reported beside the total — the same
    discipline that validating a regex against cases it must REJECT provides.
    """
    total = len(outcomes)
    if total == 0:
        return CalibrationVerdict(0.0, 0, 0, False, "no cases", [], "no control ran",
                                  "NOT CALIBRATED: no known-answer cases ran, which is a "
                                  "gap in the instrument and not a passing score")
    correct = sum(1 for o in outcomes if o.outcome == "correct")
    accuracy = correct / total
    longer = [o for o in outcomes if o.better_is_longer]
    shorter = [o for o in outcomes if not o.better_is_longer]
    length_bias = _length_bias(longer, shorter)
    # Two different control failures, and they need opposite fixes: one is a
    # judge that cannot tell a tree from its own copy, the other is a judge that
    # produced nothing to tell anything from.
    controls = [o.case_id for o in outcomes
                if o.control.usable and o.control.rate < CONTROL_EQUAL_FLOOR]
    unusable = [o.case_id for o in outcomes if not o.control.usable]
    control_detail = "; ".join("%s %s" % (o.case_id, o.control.summary) for o in outcomes)
    trusted = accuracy >= floor and not controls and not unusable
    if unusable:
        note = ("NOT TRUSTED: on %d case(s) the control produced NO usable response "
                "at all, so nothing was measured — this is a broken instrument, not "
                "a judge that scored two identical trees differently" % len(unusable))
    elif controls:
        note = ("NOT TRUSTED: on %d case(s) the judge scored a tree against a "
                "byte-identical copy of itself UNEQUALLY more than %.0f%% of the time "
                "— that spread is its noise floor, and every margin below reads "
                "inside it" % (len(controls), (1 - CONTROL_EQUAL_FLOOR) * 100))
    elif accuracy < floor:
        note = ("NOT TRUSTED: %.0f%% on deliberately obvious cases, under the stated "
                "%.0f%% floor. A judge that cannot separate obvious cases cannot "
                "separate subtle ones, and that is a result worth reporting rather "
                "than a reason to proceed quietly." % (accuracy * 100, floor * 100))
    else:
        note = "calibrated: %d/%d on known-answer cases" % (correct, total)
    return CalibrationVerdict(accuracy, correct, total, trusted, length_bias, controls,
                              control_detail, note)


def _length_bias(longer: Sequence[CaseOutcome], shorter: Sequence[CaseOutcome]) -> str:
    if not longer or not shorter:
        return ("untestable: the corpus carries only one length direction, so a judge "
                "preferring longer code would score the same as one reading it")
    hit_long = sum(1 for o in longer if o.outcome == "correct") / len(longer)
    hit_short = sum(1 for o in shorter if o.outcome == "correct") / len(shorter)
    gap = hit_long - hit_short
    detail = ("better-is-longer %.0f%% (%d cases) vs better-is-shorter %.0f%% (%d cases)"
              % (hit_long * 100, len(longer), hit_short * 100, len(shorter)))
    if abs(gap) >= 0.5:
        direction = "longer" if gap > 0 else "shorter"
        return "LENGTH BIAS toward the %s implementation — %s" % (direction, detail)
    return detail


# ---------------------------------------------------------------------------
# The live judge
# ---------------------------------------------------------------------------

def http_judge(endpoint: str, model: str, timeout: float = DEFAULT_TIMEOUT,
               temperature: float = 0.3, max_tokens: int = DEFAULT_MAX_TOKENS,
               priority: str = "batch") -> Judge:
    """A judge that talks to an OpenAI-compatible endpoint, one seed per call.

    `priority: batch` so a judging run queues behind a live campaign rather than
    in front of it. It does not make judging free: the calls still occupy the
    same weights, so a run started during a measured epoch perturbs that epoch's
    wall clock, which is one of the numbers the campaign reports.

    Refuses a timeout that cannot cover `max_tokens`, because that pair truncates
    every call that uses its budget and reports it as a judgement failure.
    """
    needed = minimum_timeout(max_tokens)
    if timeout < needed:
        raise ValueError(
            "timeout %.0fs cannot cover max_tokens %d: at the %.1f tok/s floor "
            "that budget needs %.0fs, so every call spending it would be killed "
            "and reported as the judge failing. Raise --timeout to at least %.0f "
            "or lower --max-tokens." % (timeout, max_tokens,
                                        FLOOR_TOKENS_PER_SECOND, needed, needed))

    def call(prompt: str, seed: int) -> str:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "seed": seed,
            "stream": False,
        }
        request = urllib.request.Request(
            endpoint.rstrip("/") + "/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "X-Conductor-Priority": priority},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.load(response)
        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        content = message.get("content") or ""
        if content.strip():
            return content
        # An empty answer has more than one cause and they are not interchangeable.
        reasoning = message.get("reasoning_content") or ""
        finish = choice.get("finish_reason")
        if finish == "length" and reasoning:
            raise JudgeUnusable(
                "the judge spent its whole token budget reasoning and never "
                "answered (finish_reason=length, 0 answer chars after %d reasoning "
                "chars) — raise max_tokens above %d" % (len(reasoning), max_tokens))
        raise JudgeUnusable(
            "the judge returned no answer (finish_reason=%s, %d reasoning chars)"
            % (finish, len(reasoning)))

    return call


# ---------------------------------------------------------------------------
# Driving it over an epoch's archived trees
# ---------------------------------------------------------------------------

def cell_stem(cell_id: str) -> str:
    return cell_id.replace("/", "__")


@dataclass(frozen=True)
class ArchivedCell:
    cell_id: str
    arm: str
    task_id: str
    rep: int
    repo: Optional[Path]


def archived_cells(results_dir: Any) -> List[ArchivedCell]:
    """Every result record in an epoch, paired with its archived tree if there is one."""
    root = Path(results_dir)
    trees = root / "trees"
    out: List[ArchivedCell] = []
    for path in sorted(root.glob("*.json")):
        try:
            document = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if "arm" not in document or "taskId" not in document:
            continue
        cell_id = document.get("cellId", "")
        repo = trees / cell_stem(cell_id) / "repo"
        out.append(ArchivedCell(cell_id, document["arm"], document["taskId"],
                                int(document.get("rep", 1)),
                                repo if repo.is_dir() else None))
    return out


def select_trees(cells: Sequence[ArchivedCell], task_id: str) -> Dict[str, ArchivedCell]:
    """One archived tree per arm for a task: the LOWEST repetition that has one.

    An arm run with `--calibration-reps` has several trees and they are different
    implementations, so "the arm's tree" is a choice and not a lookup. The lowest
    repetition is the scoreboard cell; the extra ones exist to give cost metrics a
    noise floor, not to supply a second opinion on quality. Taking whichever cell
    happened to sort last would attach the verdict to a tree at random.
    """
    chosen: Dict[str, ArchivedCell] = {}
    for cell in sorted(cells, key=lambda c: (c.arm, c.rep, c.cell_id)):
        if cell.task_id != task_id or cell.repo is None:
            continue
        chosen.setdefault(cell.arm, cell)
    return chosen


def unjudged_reps(cells: Sequence[ArchivedCell], task_id: str,
                  chosen: Dict[str, ArchivedCell]) -> List[str]:
    """Archived trees this run will not look at. Named, never dropped in silence."""
    picked = {cell.cell_id for cell in chosen.values()}
    return sorted(cell.cell_id for cell in cells
                  if cell.task_id == task_id and cell.repo is not None
                  and cell.cell_id not in picked)


def task_prompts(manifest_path: Any) -> Dict[str, str]:
    document = json.loads(Path(manifest_path).read_text())
    entries = document["tasks"] if isinstance(document, dict) else document
    return dict((entry["id"], entry.get("prompt", "")) for entry in entries)


def task_seeds(manifest_path: Any) -> Dict[str, Dict[str, str]]:
    """Each task's seed files, for tasks that carry them inline.

    A corpus task draws its files from bench/corpus/ instead and yields an empty
    seed here, which `unmodified_seed` reports as unknown rather than as work.
    """
    document = json.loads(Path(manifest_path).read_text())
    entries = document["tasks"] if isinstance(document, dict) else document
    return dict((entry["id"], entry.get("seedFiles") or {}) for entry in entries)


def judge_epoch(results_dir: Any, judge: Judge, prompts: Dict[str, str],
                arms: Sequence[str] = ARMS, reps: int = 3,
                tasks: Optional[Sequence[str]] = None,
                base_seed: int = 1,
                seeds: Optional[Dict[str, Dict[str, str]]] = None) -> List[CriterionResult]:
    """Every arm pair on every task an epoch covered."""
    seeds = seeds or {}
    cells = archived_cells(results_dir)
    wanted = set(tasks) if tasks else {c.task_id for c in cells}
    results: List[CriterionResult] = []
    for task_id in sorted(wanted):
        by_arm = select_trees(cells, task_id)
        skipped = unjudged_reps(cells, task_id, by_arm)
        for index, arm_a in enumerate(arms):
            for arm_b in arms[index + 1:]:
                absent = [arm for arm in (arm_a, arm_b) if arm not in by_arm]
                if absent:
                    results.extend(missing_tree_result(task_id, arm_a, arm_b, absent))
                    continue
                cell_a, cell_b = by_arm[arm_a], by_arm[arm_b]
                files_a, files_b = load_tree(cell_a.repo), load_tree(cell_b.repo)
                seed = seeds.get(task_id) or {}
                idle = [arm for arm, files in ((arm_a, files_a), (arm_b, files_b))
                        if unmodified_seed(files, seed)]
                if idle:
                    results.extend(no_work_result(task_id, arm_a, arm_b, idle))
                    continue
                pair = make_pair(task_id, prompts.get(task_id, ""), arm_a, arm_b,
                                 files_a, files_b,
                                 cell_a.cell_id, cell_b.cell_id)
                pair_results = compare(pair, judge, reps=reps, base_seed=base_seed)
                if skipped:
                    for result in pair_results:
                        result.contamination = sorted(set(result.contamination) | {
                            "%d further archived repetition(s) of this task were not "
                            "judged: %s" % (len(skipped), ", ".join(skipped))
                        })
                results.extend(pair_results)
    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def render_report(results: Sequence[CriterionResult],
                  calibration: Optional[CalibrationVerdict] = None) -> str:
    lines: List[str] = ["# Quality — blind paired comparison", ""]
    lines.append("Ordinal. A win means the implementation was scored higher in BOTH")
    lines.append("presentation orders across every repetition; anything less is a tie.")
    lines.append("No ratio appears here: rubric scores have no true zero.")
    lines.append("")
    if calibration is None:
        # An omitted section reads as "nothing to report". The judge having gone
        # unchecked is the single most important thing a reader of these verdicts
        # needs to know, so it is stated where the verdict would have been.
        lines.append("## Judge calibration — NOT CHECKED")
        lines.append("")
        lines.append("This run was made with `--no-calibration`. No known-answer case "
                     "was scored, so nothing below is evidence that this judge can "
                     "separate cases whose answer is known — and a judge that cannot "
                     "do that cannot separate subtle ones.")
        lines.append("")
    else:
        lines.append("## Judge calibration")
        lines.append("")
        lines.append("%s" % calibration.note)
        lines.append("")
        lines.append("- known-answer accuracy: %d/%d (%.0f%%), stated floor %.0f%%"
                     % (calibration.correct, calibration.total,
                        calibration.accuracy * 100, CALIBRATION_FLOOR * 100))
        lines.append("- length bias: %s" % calibration.length_bias)
        lines.append("- identical-pair control: %s"
                     % ("clean" if not calibration.control_failures
                        else "FAILED on " + ", ".join(calibration.control_failures)))
        lines.append("- control detail: %s" % calibration.control_detail)
        lines.append("")
        if not calibration.trusted:
            lines.append("**Every verdict below is reported under a judge that did not "
                         "pass calibration, and is evidence about the judge rather "
                         "than about the arms.**")
            lines.append("")
    if not results:
        lines.append("No comparison ran. That is a gap in the instrument, not a tie.")
        lines.append("")
        return "\n".join(lines)
    for task_id in sorted({r.task_id for r in results}):
        lines.append("## `%s`" % task_id)
        lines.append("")
        lines.append("| pair | criterion | verdict | why |")
        lines.append("|---|---|---|---|")
        for result in [r for r in results if r.task_id == task_id]:
            lines.append("| %s vs %s | %s | %s | %s |"
                         % (result.arm_a, result.arm_b, result.criterion,
                            _verdict_text(result), result.note.replace("|", "/")))
        lines.append("")
        contaminated = sorted({note for r in results if r.task_id == task_id
                               for note in r.contamination})
        if contaminated:
            lines.append("Blinding notes for this task:")
            for note in contaminated:
                lines.append("- %s" % note)
            lines.append("")
    return "\n".join(lines)


def _verdict_text(result: CriterionResult) -> str:
    if result.outcome == "win_a":
        return "**%s**" % result.arm_a
    if result.outcome == "win_b":
        return "**%s**" % result.arm_b
    if result.outcome in ("no_work", "no_tree", "no_verdict"):
        # Shouted, because these are the rows a reader skims past as though they
        # were ties, and they are the opposite of a tie: nothing was measured.
        return "_%s_" % result.outcome.upper().replace("_", " ")
    return result.outcome


def dry_run(results_dir: Any, prompts: Dict[str, str], arms: Sequence[str] = ARMS,
            reps: int = 3, tasks: Optional[Sequence[str]] = None,
            seeds: Optional[Dict[str, Dict[str, str]]] = None) -> str:
    """What a judging run would ask, and what it would cost, without asking it.

    A live run is hours of model calls against the same weights a campaign epoch
    is using, so the size of it is worth knowing before it starts rather than
    after. This also exercises loading, blinding and pairing over the real trees,
    which is every step but the model.
    """
    cells = archived_cells(results_dir)
    seeds = seeds or {}
    wanted = sorted(set(tasks) if tasks else {c.task_id for c in cells})
    lines = ["# Dry run — %s" % Path(results_dir).name, ""]
    calls = 0
    for task_id in wanted:
        by_arm = select_trees(cells, task_id)
        skipped = unjudged_reps(cells, task_id, by_arm)
        lines.append("## `%s`" % task_id)
        if skipped:
            lines.append("- not judged (extra repetitions): %s" % ", ".join(skipped))
        for index, arm_a in enumerate(arms):
            for arm_b in arms[index + 1:]:
                absent = [arm for arm in (arm_a, arm_b) if arm not in by_arm]
                if absent:
                    lines.append("- %s vs %s — NO TREE for %s: this pair reports "
                                 "no_tree on every criterion and is never a tie"
                                 % (arm_a, arm_b, ", ".join(absent)))
                    continue
                files_a = load_tree(by_arm[arm_a].repo)
                files_b = load_tree(by_arm[arm_b].repo)
                seed = seeds.get(task_id) or {}
                idle = [arm for arm, f in ((arm_a, files_a), (arm_b, files_b))
                        if unmodified_seed(f, seed)]
                if idle:
                    lines.append("- %s vs %s — NO WORK from %s: the seed is "
                                 "byte-identical, nothing to judge, 0 call(s)"
                                 % (arm_a, arm_b, ", ".join(idle)))
                    continue
                pair = make_pair(task_id, prompts.get(task_id, ""), arm_a, arm_b,
                                 files_a, files_b,
                                 by_arm[arm_a].cell_id, by_arm[arm_b].cell_id)
                first, cut_a = render_side(pair.files_a, "Implementation 1")
                second, cut_b = render_side(pair.files_b, "Implementation 2")
                size = len(build_prompt(pair.task_prompt, CRITERIA[0], first, second))
                pair_calls = len(CRITERIA) * 2 * reps
                calls += pair_calls
                lines.append("- %s vs %s — %d + %d file(s), ~%d chars/prompt, "
                             "%d call(s)%s"
                             % (arm_a, arm_b, len(pair.files_a), len(pair.files_b),
                                size, pair_calls,
                                " [TRUNCATED]" if (cut_a or cut_b) else ""))
                for note in pair.contamination:
                    lines.append("  - blinding: %s" % note)
        lines.append("")
    lines.append("%d model call(s) in total, before calibration." % calls)
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--results-dir", type=Path,
                        help="an epoch's results directory, holding trees/")
    parser.add_argument("--manifest", type=Path, default=cb.MANIFEST_PATH)
    parser.add_argument("--rubric-dir", type=Path, default=cb.RUBRIC_DIR)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8088")
    parser.add_argument("--model", default="llamacpp/qwen3.8-27b")
    parser.add_argument("--reps", type=int, default=3,
                        help="repetitions PER ORDER, each at its own seed")
    parser.add_argument("--task", action="append", default=[], dest="tasks")
    parser.add_argument("--calibrate", action="store_true",
                        help="run the known-answer cases and stop")
    parser.add_argument("--no-calibration", action="store_true",
                        help="judge without first checking the judge (records it in the report)")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--write-rubrics", action="store_true")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="derived from --max-tokens and a floor generation "
                             "rate; a smaller value is refused")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        dest="max_tokens",
                        help="answer budget; a thinking model spends most of it "
                             "deliberating before it answers")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help="judge calls in flight at once")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="price the run and exercise loading, blinding and "
                             "pairing over the real trees, without calling a model")
    args = parser.parse_args()
    if args.calibrate and args.no_calibration:
        parser.error("--calibrate runs the known-answer cases; --no-calibration skips "
                     "them. Asking for both says nothing.")

    if args.dry_run:
        if args.results_dir is None:
            parser.error("--dry-run needs --results-dir")
        print(dry_run(args.results_dir, task_prompts(args.manifest), reps=args.reps,
                      tasks=args.tasks or None, seeds=task_seeds(args.manifest)))
        return 0

    judge = http_judge(args.endpoint, args.model, timeout=args.timeout,
                       max_tokens=args.max_tokens)
    verdict: Optional[CalibrationVerdict] = None
    if not args.no_calibration:
        cases = load_calibration()
        started = time.time()
        outcomes = run_calibration(cases, judge, reps=args.reps)
        verdict = judge_calibration_verdict(outcomes)
        print("calibration: %s (%.0fs)" % (verdict.note, time.time() - started))
        for outcome in outcomes:
            print("  %-42s %-14s %-10s control: %s"
                  % (outcome.case_id, outcome.criterion, outcome.outcome,
                     outcome.control.summary))
    if args.calibrate:
        return 0 if (verdict is not None and verdict.trusted) else 1

    if args.results_dir is None:
        parser.error("--results-dir is required unless --calibrate is given")
    results = judge_epoch(args.results_dir, judge, task_prompts(args.manifest),
                          reps=args.reps, tasks=args.tasks or None,
                          seeds=task_seeds(args.manifest))
    text = render_report(results, verdict)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print("%s  (%d bytes)" % (args.out, len(text)))
    else:
        print(text)

    if args.write_rubrics:
        reviewer = reviewer_label(args.model, args.reps)
        written, skipped = 0, []
        for task_id in sorted({r.task_id for r in results}):
            for arm in ARMS:
                mine = [r for r in results if r.task_id == task_id
                        and arm in (r.arm_a, r.arm_b)]
                record = rubric_record(arm, mine, reviewer)
                if record is None:
                    skipped.append("%s/%s" % (arm, task_id))
                    continue
                cb.write_rubric(args.rubric_dir, record)
                written += 1
        print("rubrics: %d written to %s" % (written, args.rubric_dir))
        if skipped:
            print("rubrics: %d cell(s) had a criterion with no usable score and were "
                  "NOT written — a gap, not a zero: %s" % (len(skipped), ", ".join(skipped)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

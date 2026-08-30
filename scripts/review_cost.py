"""What the review loop cost a conductor run, and what it bought.

The campaign's expensive stages are the review ones, and until now their price
was known only in aggregate: a per-role token table says the reviewer is 71.8%
of decode and stops there. That number cannot tell a run that reviewed three
times because it kept finding defects from one that reviewed three times because
a schema complaint threw a round away, and the two want opposite fixes.

So this reads a run directory and reports the review loop STAGE BY STAGE and
LENS BY LENS: what each dispatch cost in wall clock and decode, what it raised,
and which lens raised it. Every figure derives from records the run already
wrote — the journal, and the router's ledger windowed to the run's own span.

WHY IT IS A COMMITTED SCRIPT. Epoch 23's register carries a per-turn figure
("12 of 196 budgeted assistant messages") produced by an analysis that was never
committed, so it cannot be re-derived and cannot be checked — and re-deriving it
gives a different answer. A campaign whose method is measurement cannot keep its
measurements in a scratch directory.

THE JOIN. `subsession.dispatched` and `subsession.complete` each carry a
top-level `sessionID`, so a dispatch pairs with its completion exactly and every
per-lens duration below is measured rather than apportioned. This is worth
stating because the obvious reading of the journal is that it has no join key:
a wave dispatches N sub-sessions and their completions arrive in COMPLETION
order, and nothing inside `data` connects the two. The key is one level up.

WHAT A CONTENDED DURATION IS NOT. The backend serves one sequence at a time, so
a wave of six is six sessions sharing one generator and each dispatch's measured
duration is inflated by roughly the wave's width. A dispatch's duration is
therefore comparable to other dispatches IN THE SAME WAVE and to nothing else.
The DECODE RATE BY CONCURRENCY table exists to make that visible: when aggregate
tok/s is flat across widths, the wave is token-bound, and narrowing a fan-out
returns time in proportion to the tokens it removes.

    python3 scripts/review_cost.py <run-dir> [--ledger .data/router/metrics.jsonl]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

# The router's ledger is append-only and GLOBAL across every run this machine has
# served, so a window is not an optimization but the difference between a run's
# own decode and a prior day's. The grace covers a request that completes after
# the journal's last record.
LEDGER_WINDOW_GRACE_MS = 60_000

# Reviewer sub-sessions are dispatched for three different stages under one role,
# and they have different fixes, so the role alone is not the unit. Each stage is
# recognized by the opening line of the brief it is handed.
_STAGE_MARKERS: Sequence[Tuple[str, str]] = (
    ("itemReview", "You are an item reviewer"),
    ("planReview", "You are a plan reviewer"),
)
_VET_MARKER = "test-vet critics"
_VET_CHANGED_MARKER = "CHANGED during item review"

# Two briefs name the lens two ways: the item reviewer is handed a `LENSES:` line
# (which may carry several, merged below six sessions), the plan reviewer a
# sentence. Both are read, because a lens table that silently missed one whole
# stage would report that stage as raising findings from nowhere.
_LENS_RES = (
    re.compile(r"^LENS(?:ES)?:\s*(.+)$", re.MULTILINE),
    re.compile(r'Your lens is "([^"]+)"'),
)
_ROUND_RE = re.compile(r"round (\d+) of at most (\d+)")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def json_objects(text: str) -> List[Any]:
    """Every TOP-LEVEL JSON object in text, in order.

    A sub-session reply is prose with a fenced object at the end. The walk skips
    past each object it decodes rather than descending into it, which is what
    keeps a nested `readWitness` from being mistaken for the reply itself.
    """
    decoder = json.JSONDecoder()
    found: List[Any] = []
    cursor = 0
    while True:
        start = text.find("{", cursor)
        if start < 0:
            return found
        try:
            obj, end = decoder.raw_decode(text, start)
        except ValueError:
            cursor = start + 1
            continue
        found.append(obj)
        cursor = end


def reply_findings(response: str) -> Optional[List[Dict[str, Any]]]:
    """The findings list of the LAST top-level object carrying one, or None.

    None means "this reply is not a findings reply" and is distinct from [],
    which is the approval.
    """
    for obj in reversed(json_objects(response)):
        if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
            return [f for f in obj["findings"] if isinstance(f, dict)]
    return None


def parse_concatenated_json(text: str) -> List[Any]:
    """The router writes pretty-printed objects back to back, not one per line."""
    decoder = json.JSONDecoder()
    out: List[Any] = []
    cursor = 0
    while cursor < len(text):
        while cursor < len(text) and text[cursor] in " \n\r\t":
            cursor += 1
        if cursor >= len(text):
            break
        obj, cursor = decoder.raw_decode(text, cursor)
        out.append(obj)
    return out


def stage_of(role: Optional[str], prompt: str) -> str:
    """The stage a dispatch belongs to. Non-reviewer roles are their own stage."""
    if role != "reviewer":
        return role or "unknown"
    for name, marker in _STAGE_MARKERS:
        if prompt.startswith(marker):
            return name
    if _VET_MARKER in prompt[:300]:
        return "vetChanged" if _VET_CHANGED_MARKER in prompt[:500] else "vet"
    return "reviewer?"


def lens_of(prompt: str) -> Optional[str]:
    for pattern in _LENS_RES:
        match = pattern.search(prompt)
        if match:
            return match.group(1).strip()
    return None


def round_of(prompt: str) -> Optional[int]:
    match = _ROUND_RE.search(prompt[:800])
    return int(match.group(1)) if match else None


def completed_at_ms(entry: Dict[str, Any]) -> Optional[float]:
    stamp = entry.get("completedAt")
    if not isinstance(stamp, str):
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).timestamp() * 1000
    except ValueError:
        return None


def window_ledger(
    entries: Sequence[Dict[str, Any]], first_ms: float, last_ms: float
) -> List[Dict[str, Any]]:
    """The rows of the global ledger that completed inside this run's span."""
    hi = last_ms + LEDGER_WINDOW_GRACE_MS
    kept = []
    for entry in entries:
        at = completed_at_ms(entry)
        if at is not None and first_ms <= at <= hi:
            kept.append(entry)
    return kept


# ---------------------------------------------------------------------------
# Waves
# ---------------------------------------------------------------------------


class Dispatch:
    """One sub-session: its brief, its reply, and the seconds between them."""

    def __init__(self, session_id: str, ts: float, role: Optional[str], item: str, prompt: str) -> None:
        self.session_id = session_id
        self.ts = ts
        self.role = role
        self.item = item
        self.prompt = prompt
        self.response: Optional[str] = None
        self.end_ts: Optional[float] = None
        self.ok: Optional[bool] = None
        self.attempts: Optional[int] = None
        # A journal record is capped at 8 KiB (adapter/fanout.ts
        # MAX_TRANSCRIPT_CHARS) and the schema shape the harness appends rides at
        # the very END of a brief. So a truncated record is a brief whose tail is
        # missing from the RECORD and not from the PROMPT, and reading "this role
        # was never shown its schema" off one is a fabricated defect.
        self.truncated = False

    @property
    def stage(self) -> str:
        return stage_of(self.role, self.prompt)

    @property
    def lens(self) -> Optional[str]:
        return lens_of(self.prompt)

    @property
    def duration_s(self) -> Optional[float]:
        if self.end_ts is None:
            return None
        return (self.end_ts - self.ts) / 1000.0

    def findings(self) -> Optional[List[Dict[str, Any]]]:
        return reply_findings(self.response or "")


class Wave:
    """One fan-out: a wave record and the dispatches it launched."""

    def __init__(self, index: int, ts: float) -> None:
        self.index = index
        self.ts = ts
        self.dispatches: List[Dispatch] = []
        self.retries = 0

    @property
    def jobs(self) -> int:
        return len(self.dispatches)

    @property
    def stage(self) -> str:
        return self.dispatches[0].stage if self.dispatches else "empty"

    @property
    def item(self) -> str:
        return next((d.item for d in self.dispatches if d.item), "")

    @property
    def round(self) -> Optional[int]:
        return round_of(self.dispatches[0].prompt) if self.dispatches else None

    @property
    def last(self) -> float:
        ends = [d.end_ts for d in self.dispatches if d.end_ts is not None]
        return max(ends) if ends else self.ts

    @property
    def span_s(self) -> float:
        return (self.last - self.ts) / 1000.0

    @property
    def failures(self) -> int:
        return sum(1 for d in self.dispatches if d.ok is not True)

    @property
    def truncated_prompts(self) -> int:
        return sum(1 for d in self.dispatches if d.truncated)

    @property
    def empty_replies(self) -> int:
        return sum(1 for d in self.dispatches if d.findings() == [])

    def findings(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for dispatch in self.dispatches:
            out.extend(dispatch.findings() or [])
        return out


def waves_of(records: Sequence[Dict[str, Any]]) -> List[Wave]:
    """Group a journal into waves, pairing each dispatch with its completion.

    Records before the first wave are dropped. A completion whose sessionID names
    no dispatch in the open wave is ignored rather than attached to a neighbour.
    """
    waves: List[Wave] = []
    current: Optional[Wave] = None
    by_session: Dict[str, Dispatch] = {}
    for record in records:
        event = record.get("event")
        data = record.get("data") or {}
        session_id = record.get("sessionID")
        if event == "wave":
            current = Wave(len(waves), float(record.get("ts") or 0))
            waves.append(current)
        elif current is None:
            continue
        elif event == "subsession.dispatched":
            dispatch = Dispatch(
                str(session_id or ""),
                float(record.get("ts") or 0),
                data.get("role"),
                str(data.get("itemId") or ""),
                str(data.get("prompt") or ""),
            )
            dispatch.truncated = data.get("truncated") is True
            current.dispatches.append(dispatch)
            if dispatch.session_id:
                by_session[dispatch.session_id] = dispatch
        elif event == "subsession.complete":
            dispatch = by_session.get(str(session_id or ""))
            if dispatch is None:
                continue
            dispatch.response = str(data.get("response") or "")
            dispatch.end_ts = float(record.get("ts") or 0)
            dispatch.ok = data.get("ok") is True
            dispatch.attempts = data.get("attempts")
        elif event == "subsession.retry":
            current.retries += 1
    return waves


def wave_tokens(wave: Wave, ledger: Sequence[Dict[str, Any]]) -> int:
    """Decode attributable to a wave: ledger rows completing inside its span."""
    total = 0
    for entry in ledger:
        at = completed_at_ms(entry)
        if at is not None and wave.ts <= at <= wave.last + 5000:
            total += entry.get("completionTokens") or 0
    return total


def throughput_by_concurrency(
    waves: Sequence[Wave], ledger: Sequence[Dict[str, Any]], floor_s: float = 60.0
) -> Dict[int, List[float]]:
    """Aggregate wave decode rate, bucketed by how many sub-sessions ran at once.

    The question this answers decides every fan-out cut: if the rate is FLAT
    across concurrency, the machine generates one sequence at a time, a wave's
    wall clock is its token count over that rate, and narrowing a fan-out returns
    time in proportion to the tokens it removes. If instead the rate rises with
    concurrency, a wave costs its slowest member and narrowing returns almost
    nothing. Waves shorter than `floor_s` are excluded: their span is dominated
    by dispatch overhead rather than decode.
    """
    rates: Dict[int, List[float]] = {}
    for wave in waves:
        if wave.span_s < floor_s or wave.jobs == 0:
            continue
        rates.setdefault(wave.jobs, []).append(wave_tokens(wave, ledger) / wave.span_s)
    return rates


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _clock(ts: float) -> str:
    return datetime.fromtimestamp(ts / 1000, timezone.utc).strftime("%H:%M:%S")


def report(waves: Sequence[Wave], ledger: Sequence[Dict[str, Any]], out) -> None:
    write = lambda line="": out.write(line + "\n")  # noqa: E731

    write("=" * 100)
    write("WAVE BY WAVE")
    write("=" * 100)
    write(
        "{:>3} {:>9} {:>5} {:<13} {:<14} {:>4} {:>9} {:>7} {:>5} {:>6} {}".format(
            "w", "startZ", "jobs", "stage", "item", "rnd", "tokens", "min", "empt", "find", "flags"
        )
    )
    for wave in waves:
        flags = []
        if wave.failures:
            flags.append("failed=%d" % wave.failures)
        if wave.retries:
            flags.append("retries=%d" % wave.retries)
        if wave.truncated_prompts:
            flags.append("prompt-tail-not-recorded=%d" % wave.truncated_prompts)
        write(
            "{:>3} {:>9} {:>5} {:<13} {:<14} {:>4} {:>9,} {:>7.1f} {:>5} {:>6} {}".format(
                wave.index,
                _clock(wave.ts),
                wave.jobs,
                wave.stage,
                wave.item or "-",
                wave.round if wave.round is not None else "-",
                wave_tokens(wave, ledger),
                wave.span_s / 60.0,
                wave.empty_replies,
                len(wave.findings()),
                " ".join(flags),
            )
        )

    write()
    write("=" * 100)
    write("STAGE TOTALS — what each stage cost, and what it raised")
    write("=" * 100)
    stages: Dict[str, Dict[str, float]] = {}
    for wave in waves:
        bucket = stages.setdefault(
            wave.stage, {"waves": 0, "dispatches": 0, "minutes": 0.0, "tokens": 0, "findings": 0}
        )
        bucket["waves"] += 1
        bucket["dispatches"] += wave.jobs
        bucket["minutes"] += wave.span_s / 60.0
        bucket["tokens"] += wave_tokens(wave, ledger)
        bucket["findings"] += len(wave.findings())
    total_min = sum(b["minutes"] for b in stages.values()) or 1.0
    total_tok = sum(b["tokens"] for b in stages.values()) or 1
    write(
        "{:<14} {:>6} {:>6} {:>9} {:>7} {:>10} {:>7} {:>9}".format(
            "stage", "waves", "disp", "minutes", "min%", "tokens", "tok%", "findings"
        )
    )
    for stage, b in sorted(stages.items(), key=lambda kv: -kv[1]["minutes"]):
        write(
            "{:<14} {:>6} {:>6} {:>9.1f} {:>6.1f}% {:>10,} {:>6.1f}% {:>9}".format(
                stage,
                int(b["waves"]),
                int(b["dispatches"]),
                b["minutes"],
                b["minutes"] / total_min * 100,
                int(b["tokens"]),
                b["tokens"] / total_tok * 100,
                int(b["findings"]),
            )
        )
    write(
        "{:<14} {:>6} {:>6} {:>9.1f} {:>7} {:>10,} {:>7} {:>9}".format(
            "TOTAL",
            sum(int(b["waves"]) for b in stages.values()),
            sum(int(b["dispatches"]) for b in stages.values()),
            total_min,
            "",
            int(total_tok),
            "",
            sum(int(b["findings"]) for b in stages.values()),
        )
    )

    write()
    write("=" * 100)
    write("DECODE RATE BY CONCURRENCY — flat means a fan-out cut returns time")
    write("=" * 100)
    rates = throughput_by_concurrency(waves, ledger)
    if not rates:
        write("  no wave ran long enough to rate")
    else:
        write(
            "{:>12} {:>7} {:>10} {:>12} {:>14}".format(
                "concurrency", "waves", "med tok/s", "range", "per-session"
            )
        )
        for jobs in sorted(rates):
            values = rates[jobs]
            median = statistics.median(values)
            write(
                "{:>12} {:>7} {:>10.1f} {:>12} {:>14.1f}".format(
                    jobs,
                    len(values),
                    median,
                    "%.1f-%.1f" % (min(values), max(values)),
                    median / jobs,
                )
            )

    write()
    write("=" * 100)
    write("PER-LENS YIELD — dispatches, findings, and CONTENDED seconds per dispatch")
    write("=" * 100)
    # Keyed by STAGE and lens: plan review and item review share the names
    # `correctness` and `minimality`, and one pooled row would credit an item
    # lens with a plan lens's finding.
    dispatched: Dict[Tuple[str, str], List[Optional[float]]] = {}
    raised: Dict[Tuple[str, str], int] = {}
    for wave in waves:
        if wave.stage not in ("itemReview", "planReview"):
            continue
        for dispatch in wave.dispatches:
            if dispatch.lens:
                dispatched.setdefault((wave.stage, dispatch.lens), []).append(dispatch.duration_s)
            for finding in dispatch.findings() or []:
                lens = finding.get("lens")
                if isinstance(lens, str):
                    key = (wave.stage, lens)
                    raised[key] = raised.get(key, 0) + 1
    if not dispatched:
        write("  no lens-bearing review wave in this run")
    for key in sorted(set(dispatched) | set(raised)):
        durations = [d for d in dispatched.get(key, []) if d is not None]
        mean = "%8.1f" % (sum(durations) / len(durations)) if durations else "       -"
        write(
            "  {:<12} {:<24} dispatched={:<3} findings={:<3} mean_s={}".format(
                key[0], key[1], len(dispatched.get(key, [])), raised.get(key, 0), mean
            )
        )

    write()
    write("=" * 100)
    write("EVERY FINDING RAISED")
    write("=" * 100)
    any_finding = False
    for wave in waves:
        for finding in wave.findings():
            any_finding = True
            write(
                "\n[wave {:02d}] {} item={!r} lens={!r} severity={!r} id={!r}".format(
                    wave.index,
                    wave.stage,
                    wave.item,
                    finding.get("lens"),
                    finding.get("severity"),
                    finding.get("id"),
                )
            )
            write("  claim: " + str(finding.get("claim"))[:400])
    if not any_finding:
        write("  none — every review round in this run was an approval")


def load_journal(run_dir: str) -> List[Dict[str, Any]]:
    path = os.path.join(run_dir, "journal.jsonl")
    records = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                # A torn tail line is the ordinary shape of a live run.
                continue
    return records


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", help="a .conductor/runs/<runId> directory")
    parser.add_argument(
        "--ledger",
        default=".data/router/metrics.jsonl",
        help="the router's append-only ledger; windowed to this run's span",
    )
    args = parser.parse_args(argv)

    records = load_journal(args.run_dir)
    if not records:
        print("no journal records in " + args.run_dir, file=sys.stderr)
        return 2
    stamps = [float(r["ts"]) for r in records if isinstance(r.get("ts"), (int, float))]
    first_ms, last_ms = min(stamps), max(stamps)

    ledger: List[Dict[str, Any]] = []
    if os.path.exists(args.ledger):
        with open(args.ledger, encoding="utf-8") as handle:
            entries = [e for e in parse_concatenated_json(handle.read()) if isinstance(e, dict)]
        ledger = window_ledger(entries, first_ms, last_ms)
        print(
            "ledger: {:,} of {:,} rows inside this run's span "
            "({:,} completion tokens)".format(
                len(ledger),
                len(entries),
                sum(e.get("completionTokens") or 0 for e in ledger),
            )
        )
    else:
        print("no ledger at " + args.ledger + "; token columns will read 0")
    print("journal span: {:.1f} min".format((last_ms - first_ms) / 60000.0))
    print()

    report(waves_of(records), ledger, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

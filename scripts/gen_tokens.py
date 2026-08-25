"""Generated-token accounting for a benchmark cell.

The bench records a per-cell `tokens` figure from the router ledger. That figure
is prompt + completion summed over every request, so it is dominated by prompt
re-sends: a cell measured at 375,939 there generated 31,984. Prompt bytes are
not paid at the generation rate, so steering by that number hides the one cost
that predicts whether a cell finishes.

What a cell pays wall clock for is what the model EMITS. opencode persists every
part in `home/data/opencode/opencode.db`, typed, which separates emission from
prompt:

    reasoning    emitted   the model's thinking
    text         emitted   assistant prose and returned documents — ONLY on an
                           assistant message. A `text` part on a USER message is
                           the brief that was handed to a sub-session, and a
                           sub-session's brief can run to thousands of characters.
    tool.input   emitted   the arguments of a tool call
    tool.output  PROMPT    file contents, command results — fed TO the model

Part type alone does not separate emission from prompt: `text` appears on both
sides of the conversation. The role of the owning message is what settles it.

Summing the first three and dividing by the machine's observed tokens/second
predicts wall clock closely enough to say, before a run ends, whether a cell can
finish inside its budget at all.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Observed single-stream generation rate for the benchmarked model, in tokens
# per second. Roles that run concurrently against shared slots go slower; this
# is the ceiling, so a predicted time computed from it is a LOWER bound on wall
# clock, never an optimistic one in the other direction.
DEFAULT_TOKENS_PER_SECOND = 14.0

# Characters per token. Deliberately crude: the accounting below is used for
# ratios between arms and for order-of-magnitude budget checks, and a tokenizer
# dependency would make this script unrunnable on a bare interpreter.
CHARS_PER_TOKEN = 4


@dataclass(frozen=True)
class GenerationBreakdown:
    """Characters the model emitted in one cell, split by what produced them."""

    reasoning: int = 0
    text: int = 0
    tool_args: int = 0
    parts: int = 0

    @property
    def total_chars(self) -> int:
        return self.reasoning + self.text + self.tool_args

    @property
    def total_tokens(self) -> int:
        return self.total_chars // CHARS_PER_TOKEN

    @property
    def reasoning_share(self) -> float:
        """Reasoning as a fraction of emission; 0.0 when nothing was emitted."""
        return self.reasoning / self.total_chars if self.total_chars else 0.0

    def predicted_seconds(self, tokens_per_second: float = DEFAULT_TOKENS_PER_SECOND) -> float:
        return self.total_tokens / tokens_per_second if tokens_per_second > 0 else 0.0


# Parts belonging to an assistant message only. A `text` part on a user message
# is a brief handed TO the model, and counting it as generation credits the
# harness's own prompt to the model's output — which on a sub-session-heavy arm
# is thousands of characters per dispatch.
ASSISTANT_PARTS_QUERY = """
    select p.data
    from part p
    join message m on m.id = p.message_id
    where json_extract(m.data, '$.role') = 'assistant'
"""


def _part_rows(db_path: Path) -> Iterator[str]:
    """Assistant-authored `part.data` blobs, read-only so a live cell is safe."""
    uri = f"file:{db_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        for (data,) in connection.execute(ASSISTANT_PARTS_QUERY):
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            if data:
                yield data
    finally:
        connection.close()


def accumulate(rows: Iterator[str]) -> GenerationBreakdown:
    """Fold part blobs into a breakdown, skipping anything that will not parse.

    A malformed row is skipped rather than raised on: this reads databases
    belonging to processes that may have been killed mid-write, and a partial
    accounting of a killed cell is the whole point of looking.
    """
    reasoning = text = tool_args = parts = 0
    for row in rows:
        try:
            part = json.loads(row)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(part, dict):
            continue
        kind = part.get("type")
        body = part.get("text")
        if kind == "reasoning" and isinstance(body, str):
            reasoning += len(body)
            parts += 1
        elif kind == "text" and isinstance(body, str):
            text += len(body)
            parts += 1
        elif kind == "tool":
            state = part.get("state")
            arguments = state.get("input") if isinstance(state, dict) else None
            if arguments is not None:
                tool_args += len(json.dumps(arguments))
                parts += 1
    return GenerationBreakdown(reasoning=reasoning, text=text, tool_args=tool_args, parts=parts)


def measure(db_path: Path) -> GenerationBreakdown:
    return accumulate(_part_rows(db_path))


# The same restriction as ASSISTANT_PARTS_QUERY, carrying the owning session's
# identity so emission can be attributed to the role that produced it. A cell's
# total says how much thinking it did; this says which sub-session did it, which
# is the difference between "reasoning dominates" and a target to act on.
BY_SESSION_QUERY = """
    select p.session_id, s.title, s.parent_id is null, p.data
    from part p
    join message m on m.id = p.message_id
    join session s on s.id = p.session_id
    where json_extract(m.data, '$.role') = 'assistant'
"""


def measure_by_session(db_path: Path) -> list[tuple[str, bool, GenerationBreakdown]]:
    """Per-session breakdowns, heaviest reasoning first.

    The title is opencode's own session title; for a conductor sub-session it
    begins with the role that was dispatched, which is what makes this
    attributable without threading harness state through the measurement.
    """
    uri = f"file:{db_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    grouped: dict[str, list[str]] = {}
    labels: dict[str, tuple[str, bool]] = {}
    try:
        for session_id, title, is_root, data in connection.execute(BY_SESSION_QUERY):
            if isinstance(data, bytes):
                data = data.decode("utf-8", errors="replace")
            grouped.setdefault(session_id, []).append(data)
            labels[session_id] = (title or "", bool(is_root))
    finally:
        connection.close()

    out = [(labels[sid][0], labels[sid][1], accumulate(iter(blobs)))
           for sid, blobs in grouped.items()]
    out.sort(key=lambda row: row[2].reasoning, reverse=True)
    return out


def find_cells(work_root: Path) -> list[tuple[str, str, Path]]:
    """Every (arm, task, db) under a work root, in sorted order."""
    found: list[tuple[str, str, Path]] = []
    for db in sorted(work_root.glob("*/*/*/*/*/home/data/opencode/opencode.db")):
        # .../<model>/<mechanism>/<arm>/<task>/<rep>/home/data/opencode/opencode.db
        rep_dir = db.parents[3]
        found.append((rep_dir.parent.parent.name, rep_dir.parent.name, db))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("root", type=Path, help="a work root, or one cell's rep directory")
    parser.add_argument("--rate", type=float, default=DEFAULT_TOKENS_PER_SECOND,
                        help=f"tokens/second for the prediction (default {DEFAULT_TOKENS_PER_SECOND})")
    parser.add_argument("--by-session", action="store_true",
                        help="attribute emission to each session instead of totalling the cell")
    args = parser.parse_args()

    single = args.root / "home" / "data" / "opencode" / "opencode.db"
    cells = [("", args.root.name, single)] if single.exists() else find_cells(args.root)
    if not cells:
        print(f"no opencode.db found under {args.root}")
        return 1

    if args.by_session:
        for arm, task, db in cells:
            rows = measure_by_session(db)
            total = sum(r.reasoning for _, _, r in rows)
            print(f"\n=== {arm} / {task} — reasoning {total:,} chars over {len(rows)} session(s)")
            print(f"  {'title':30} {'':5} {'reason':>8} {'text':>7} {'share':>7}")
            for title, is_root, b in rows:
                share = 100 * b.reasoning / total if total else 0.0
                print(f"  {title[:30]:30} {'ROOT' if is_root else 'sub':5} "
                      f"{b.reasoning:8} {b.text:7} {share:6.1f}%")
        return 0

    print(f"{'arm':10} {'task':14} {'gen tok':>8} {'think%':>7} {'parts':>6} {'predicted':>10}")
    for arm, task, db in cells:
        b = measure(db)
        print(f"{arm:10} {task:14} {b.total_tokens:8} {100 * b.reasoning_share:6.1f}% "
              f"{b.parts:6} {b.predicted_seconds(args.rate) / 60:9.1f}m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

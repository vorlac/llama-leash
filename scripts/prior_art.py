"""Search what this repository already knows about a mechanism, before calling it new.

Four times in one campaign session a defect was recorded as a discovery when the
answer was already written down, one grep away:

  the acceptance clustering that "broke on any criterion beginning with 'the'"
      — docs/developer/project-status.md, found AFTER reintroducing it
  the sub-session watchdog being a wall-clock budget too small for a local model
      — conductor/docs/HONEST-LIMITS.md, written earlier in the same campaign
  the no-placeholder rule matching a literal token and not a bracket shape
      — a comment in conductor/core/planning.ts, beside the code it describes
  a queue timeout equal to a sub-session deadline producing "two different error
  stories for one event"
      — docs/reviews/2026-08-12-conductor-plan-adversarial-review.md

The failure is not that the notes are missing. It is that finding them requires
knowing they exist, and the moment you most need to look is the moment you are
most confident you do not. So the lookup has to be cheap enough to run on a
hunch: one command, a mechanism word, and the passages that mention it.

Searches prose (reviews, campaign registers, honest-limits, corrections) AND
source comments, because one of the four lived in a comment.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

REPO = Path(__file__).resolve().parent.parent

# Where this repository writes down what it has already learned. Ordered by how
# specific each source is: a review names a defect, a register names an epoch, a
# limits page names a constraint that was accepted rather than fixed.
PROSE_SOURCES: Sequence[str] = (
    "docs/reviews",
    "docs/build/artifacts",
    "docs/build/CORRECTIONS.md",
    "conductor/docs",
    "docs/developer/project-status.md",
)

# Comment text in the trees where a decision is recorded beside the code it
# governs. `planning.ts` explains the placeholder rule in exactly this way.
CODE_SOURCES: Sequence[str] = ("conductor/core", "conductor/adapter", "scripts", "router")

COMMENT_LINE = re.compile(r"^\s*(?://|#|\*)")


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    text: str
    kind: str  # "prose" or "comment"


def _grep(term: str, roots: Iterable[str]) -> List[tuple]:
    """Case-insensitive fixed-string grep with line numbers, over existing roots."""
    present = [str(REPO / r) for r in roots if (REPO / r).exists()]
    if not present:
        return []
    result = subprocess.run(
        ["grep", "-rniF", "--include=*.md", "--include=*.ts", "--include=*.py",
         "--include=*.hpp", "--include=*.cpp", term, *present],
        capture_output=True, text=True,
    )
    rows: List[tuple] = []
    for row in result.stdout.splitlines():
        parts = row.split(":", 2)
        if len(parts) != 3 or not parts[1].isdigit():
            continue
        rows.append((parts[0], int(parts[1]), parts[2]))
    return rows


def search(term: str, comments_only: bool = True) -> List[Hit]:
    """Every recorded mention of `term`, prose first, then source comments.

    Source hits are restricted to comment lines by default: a match on a line of
    code is usually the thing itself, not a note about it, and the point here is
    to surface what someone WROTE DOWN rather than to find a definition.
    """
    hits: List[Hit] = []
    for path, line, text in _grep(term, PROSE_SOURCES):
        hits.append(Hit(str(Path(path).relative_to(REPO)), line, text.strip(), "prose"))
    for path, line, text in _grep(term, CODE_SOURCES):
        if comments_only and not COMMENT_LINE.match(text):
            continue
        hits.append(Hit(str(Path(path).relative_to(REPO)), line, text.strip(), "comment"))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("term", help="a MECHANISM word — 'watchdog', 'queueTimeout', 'placeholder'")
    ap.add_argument("--all-lines", action="store_true",
                    help="include source lines that are not comments")
    ap.add_argument("--limit", type=int, default=40)
    args = ap.parse_args()

    hits = search(args.term, comments_only=not args.all_lines)
    if not hits:
        print(f"nothing recorded about {args.term!r}. That is a weak negative: try the "
              f"MECHANISM rather than the symptom (\"watchdog\", not \"sub-sessions die\").")
        return 0

    by_kind = {"prose": [h for h in hits if h.kind == "prose"],
               "comment": [h for h in hits if h.kind == "comment"]}
    print(f"{len(hits)} recorded mention(s) of {args.term!r}\n")
    for kind, label in (("prose", "Written up"), ("comment", "Recorded beside the code")):
        rows = by_kind[kind]
        if not rows:
            continue
        print(f"── {label} ── ({len(rows)})")
        for hit in rows[: args.limit]:
            body = hit.text if len(hit.text) <= 150 else hit.text[:147] + "..."
            print(f"  {hit.path}:{hit.line}")
            print(f"      {body}")
        if len(rows) > args.limit:
            print(f"  ... and {len(rows) - args.limit} more (raise --limit)")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Per-epoch review: what was asked, what came out, what it cost, what changed.

One section per epoch, oldest first. Inside each: the changes committed since the
previous epoch, then per task the prompt AS IT WAS FED that epoch, then each arm's
produced code in full with a phase-by-phase breakdown of time and tokens.

The prompt is read from the manifest AS OF that epoch's commit rather than from
the working tree, because the corpus itself has been edited during the campaign —
D41 unescaped 26 prose fields that every earlier epoch was fed verbatim. Rendering
today's manifest against an older epoch would show a prompt that epoch never saw.

Produced code exists only for epochs whose trees were archived. run_and_watch.py
clears the work root at the START of every run, so epochs before archiving landed
have prompts, outcomes and timings but no code, and say so.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parent.parent
ARMS = ("baseline", "doctrine", "conductor")
ARM_BLURB = {
    "baseline": "stock opencode `build` agent — llama.cpp + vanilla opencode, "
                "nothing from this repository applied",
    "doctrine": "the nine doctrine packs as a static system prompt; no plugin, "
                "no state machine, no sub-sessions",
    "conductor": "the full llama-leash workspace — opencode plugin, run FSM, gates, "
                 "and sub-session fan-out",
}
SKIP_DIRS = {".git", ".conductor", "node_modules", "__pycache__", ".opencode"}


# ---------------------------------------------------------------------------
# git: what the corpus and the code looked like at a moment
# ---------------------------------------------------------------------------

def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True).stdout


def commit_at(when: datetime) -> Optional[str]:
    """The commit that was HEAD at `when`, or None if history starts later."""
    sha = _git("rev-list", "-1", f"--before={when.isoformat()}", "HEAD").strip()
    return sha or None


def manifest_at(sha: Optional[str]) -> Dict[str, dict]:
    """The task manifest as of a commit, keyed by task id; empty if unreadable."""
    if sha is None:
        return {}
    raw = _git("show", f"{sha}:bench/conductor-tasks.json")
    if not raw.strip():
        return {}
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    entries = doc["tasks"] if isinstance(doc, dict) else doc
    return {t["id"]: t for t in entries if isinstance(t, dict) and "id" in t}


@dataclass(frozen=True)
class Change:
    sha: str
    subject: str
    defects: str
    body: str


def commits_between(start: Optional[datetime], end: datetime) -> List[Change]:
    """Commits landed in a half-open window, oldest first, with Defect: trailers."""
    args = ["log", "--reverse", "--format=%H%x1f%s%x1f%b%x1e", f"--until={end.isoformat()}"]
    if start is not None:
        args.append(f"--since={start.isoformat()}")
    out: List[Change] = []
    for record in _git(*args).split("\x1e"):
        record = record.strip("\n")
        if not record:
            continue
        parts = record.split("\x1f")
        if len(parts) < 3:
            continue
        sha, subject, body = parts[0], parts[1], parts[2]
        defects = ""
        for line in body.splitlines():
            if line.startswith("Defect:"):
                defects = line[len("Defect:"):].strip()
        out.append(Change(sha[:9], subject, defects, body))
    return out


# ---------------------------------------------------------------------------
# the session store: per-turn and per-sub-session cost
# ---------------------------------------------------------------------------

@dataclass
class Turn:
    session: str
    session_id: str
    agent: str
    seconds: float
    out_tokens: int
    in_tokens: int
    tools: List[str] = field(default_factory=list)


def read_turns(db: Path) -> List[Turn]:
    """Every assistant turn in a cell, in order, with its cost and its tool calls."""
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    except sqlite3.Error:
        return []
    try:
        # The root session's title is the user's task, not a role. Label it by what
        # it IS — the orchestrator — so a phase table reads as a list of roles and
        # not as one role plus a sentence about clocks.
        titles = {}
        for sid, title, is_root in conn.execute(
            "select id, title, parent_id is null from session"
        ):
            titles[sid] = "orchestrator (root session)" if is_root else (title or "")
        tools: Dict[str, List[str]] = {}
        for mid, data in conn.execute("select message_id, data from part"):
            try:
                part = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue
            if part.get("type") == "tool" and part.get("tool"):
                tools.setdefault(mid, []).append(str(part["tool"]))
        turns: List[Turn] = []
        rows = conn.execute(
            "select id, session_id, data from message order by time_created"
        ).fetchall()
    except sqlite3.Error:
        conn.close()
        return []
    conn.close()
    for mid, sid, data in rows:
        try:
            msg = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            continue
        if msg.get("role") != "assistant":
            continue
        t = msg.get("time") or {}
        created, completed = t.get("created"), t.get("completed")
        # Presence, not truthiness: a timestamp of 0 is a real value, and `and`
        # would read it as missing and silently report the turn as instantaneous.
        seconds = ((completed - created) / 1000.0
                   if isinstance(created, (int, float)) and isinstance(completed, (int, float))
                   else 0.0)
        tok = msg.get("tokens") or {}
        turns.append(Turn(
            session=titles.get(sid, sid),
            session_id=sid,
            agent=str(msg.get("agent") or ""),
            seconds=seconds,
            out_tokens=int(tok.get("output") or 0),
            in_tokens=int(tok.get("input") or 0),
            tools=tools.get(mid, []),
        ))
    return turns


def phase_rows(turns: Sequence[Turn], by_session: bool) -> List[Tuple[str, int, int, float, int, int]]:
    """(label, turns, seconds, out tokens, in tokens), grouped or one row per turn.

    The conductor arm's phases are real: each is a separate sub-session with a
    role. The baseline arm has no phase structure at all — it is one flat session
    — so its turns ARE its finest honest granularity, and grouping them into
    invented stage names would be a label this report made up.
    """
    if not by_session:
        return [
            (f"turn {i + 1}" + (f" → {', '.join(t.tools)}" if t.tools else " → (no tool call)"),
             1, 1, t.seconds, t.out_tokens, t.in_tokens)
            for i, t in enumerate(turns)
        ]
    order: List[str] = []
    agg: Dict[str, List] = {}
    for t in turns:
        key = (t.session or t.agent or "(unnamed)").rstrip(": ")
        if key not in agg:
            agg[key] = [set(), 0, 0.0, 0, 0]
            order.append(key)
        agg[key][0].add(t.session_id)
        agg[key][1] += 1
        agg[key][2] += t.seconds
        agg[key][3] += t.out_tokens
        agg[key][4] += t.in_tokens
    return [(k, len(agg[k][0]), agg[k][1], agg[k][2], int(agg[k][3]), int(agg[k][4]))
            for k in order]


# ---------------------------------------------------------------------------
# produced code
# ---------------------------------------------------------------------------

def source_files(root: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(p in SKIP_DIRS for p in rel.parts) or (rel.parts and rel.parts[0] == "gauge"):
            continue
        try:
            out[str(rel)] = path.read_text(errors="replace")
        except OSError:
            continue
    return out


def cell_paths(results_dir: Path, work_root: Path, cell_id: str,
               record: Optional[dict]) -> Tuple[Optional[Path], Optional[Path]]:
    """(repo, session-db) for a cell, preferring the archive over the live tree.

    The archive is authoritative because it was copied at scoring time. The work
    root is a fallback for epochs run before archiving landed, and is only trusted
    when the tree's birth time matches the result's own startedIso — otherwise it
    belongs to a LATER epoch and pairing them renders a comparison that never
    happened.
    """
    # `cellId` is the identity the driver already recorded, and it is what
    # archive_cell_tree stems its directory from — so the two cannot drift. It is
    # also already slugged, where the record's `model` field is not: rebuilding
    # the path from `model` yields "llamacpp/qwen3.8-27b" where the tree is under
    # "llamacpp-qwen3.8-27b", and every lookup silently misses.
    archived = results_dir / "trees" / cell_id.replace("/", "__")
    if (archived / "repo").exists():
        db = archived / "session" / "opencode.db"
        return archived / "repo", db if db.exists() else None
    if record is None or not cell_id:
        return None, None
    cell = work_root / cell_id
    started = record.get("startedIso")
    if not isinstance(started, str) or not started or not cell.exists():
        return None, None
    try:
        began = datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None, None
    stat = cell.stat()
    born = getattr(stat, "st_birthtime", stat.st_mtime)
    if abs(born - began) > 3600.0:
        return None, None
    db = cell / "home/data/opencode/opencode.db"
    return cell / "repo", db if db.exists() else None


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def fence(path: str) -> str:
    return {"ts": "ts", "py": "python", "md": "markdown", "json": "json",
            "hpp": "cpp", "cpp": "cpp"}.get(path.rsplit(".", 1)[-1], "")


def load_results(results_dir: Path) -> Dict[Tuple[str, str], dict]:
    found: Dict[Tuple[str, str], dict] = {}
    for f in sorted(results_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "arm" in d and "taskId" in d:
            found[(d["arm"], d["taskId"])] = d
    return found


def epoch_start(results_dir: Path) -> datetime:
    """The epoch's own clock, from its directory name (YYYYMMDD-HHMMSS, local)."""
    return datetime.strptime(results_dir.name, "%Y%m%d-%H%M%S").astimezone()


def verdict(record: Optional[dict]) -> str:
    if record is None:
        return "not run"
    if record.get("timedOut"):
        return "TIMED OUT"
    return "PASS" if record.get("passed") else "FAIL"


def render_epoch(results_dir: Path, work_root: Path, index: int,
                 previous: Optional[datetime]) -> str:
    started = epoch_start(results_dir)
    results = load_results(results_dir)
    manifest = manifest_at(commit_at(started))
    out: List[str] = []
    w = out.append

    w(f"\n---\n\n# Epoch {index} — `{results_dir.name}`\n")
    w(f"Started {started:%Y-%m-%d %H:%M %Z} · {len(results)} cells\n")

    w("## 4 · Changes since the previous epoch\n")
    changes = commits_between(previous, started)
    if not changes:
        w("_No commits landed between the previous epoch and this one._\n")
    else:
        w(f"{len(changes)} commit(s).\n")
        w("| commit | what changed | defect |")
        w("|---|---|---|")
        for c in changes:
            w(f"| `{c.sha}` | {c.subject} | {c.defects or '—'} |")
        w("")

    tasks = sorted({tid for (_, tid) in results})
    for tid in tasks:
        entry = manifest.get(tid, {})
        w(f"\n## Task `{tid}`" + (f"  ({entry.get('tier')})" if entry.get("tier") else "") + "\n")

        w("### 1 · The prompt, as it was fed this epoch\n")
        prompt = entry.get("prompt")
        if prompt:
            w("```")
            w(prompt)
            w("```\n")
        else:
            w("_The manifest at this epoch's commit does not carry this task._\n")

        for arm in ARMS:
            record = results.get((arm, tid))
            if record is None:
                continue
            repo, db = cell_paths(results_dir, work_root, record.get("cellId", ""), record)
            mins = record.get("wallClockMs", 0) / 60000.0
            gauge = (record.get("gauge") or {}).get("passed")

            w(f"### `{arm}` — {ARM_BLURB[arm]}\n")
            w(f"**{verdict(record)}** · {mins:.1f} min · hidden tests: "
              f"{'pass' if gauge else 'fail'}\n")

            w("#### 3 · Cost by phase\n")
            turns = read_turns(db) if db else []
            if not turns:
                w("_No session store for this cell — per-phase cost is unrecoverable._\n")
            else:
                grouped = arm == "conductor"
                rows = phase_rows(turns, by_session=grouped)
                if grouped:
                    w("Grouped by role. `sessions` counts how many times that role was "
                      "dispatched — more than one means a re-dispatch after a refusal or a "
                      "watchdog death. **The times overlap**: sub-sessions run concurrently "
                      "and the orchestrator's own session is elapsed while it waits on them, "
                      "so the column sums to more than the cell's wall clock and is a measure "
                      "of work done, not of time passed.")
                    w("")
                    w("| phase | sessions | turns | time | tokens out | tokens in |")
                    w("|---|---:|---:|---:|---:|---:|")
                    for label, sess, n, secs, out_tok, in_tok in rows:
                        w(f"| {label} | {sess} | {n} | {secs / 60:.1f} min "
                          f"| {out_tok:,} | {in_tok:,} |")
                    w(f"| **sum of phases** | {sum(r[1] for r in rows)} | {len(turns)} "
                      f"| {sum(r[3] for r in rows) / 60:.1f} min "
                      f"| **{sum(r[4] for r in rows):,}** | |")
                    w(f"\n_Cell wall clock: **{mins:.1f} min**._\n")
                else:
                    w("One flat session, so each row is one model turn and the times are "
                      "sequential.")
                    w("")
                    w("| phase | time | tokens out | tokens in |")
                    w("|---|---:|---:|---:|")
                    for label, _sess, _n, secs, out_tok, in_tok in rows:
                        w(f"| {label} | {secs / 60:.1f} min | {out_tok:,} | {in_tok:,} |")
                    w(f"| **total ({len(turns)} turns)** "
                      f"| **{sum(r[3] for r in rows) / 60:.1f} min** "
                      f"| **{sum(r[4] for r in rows):,}** | |")
                    w("")

            w("#### 2 · The resulting code\n")
            if repo is None:
                w("_Not preserved. `run_and_watch.py` clears the work root at the start of "
                  "every run, so this epoch's trees were destroyed when the next one "
                  "launched._\n")
                continue
            produced = source_files(repo)
            seeds = entry.get("seedFiles") or {}
            changed = {p: b for p, b in produced.items() if p not in seeds or seeds[p] != b}
            if not changed:
                w("**Unchanged from the seed — this arm produced no code.**\n")
                continue
            for path, body in sorted(changed.items()):
                w(f"`{path}` ({'created' if path not in seeds else 'modified'})\n")
                w(f"```{fence(path)}")
                w(body.rstrip("\n") if body.strip() else "(empty)")
                w("```\n")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("watch_root", type=Path)
    ap.add_argument("--work-root", type=Path, default=Path.home() / ".llama-leash-work")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--since", default="", help="only epochs at or after this directory name")
    args = ap.parse_args()

    epochs = sorted(d for d in args.watch_root.iterdir()
                    if d.is_dir() and any(d.glob("*.json")))
    if args.since:
        epochs = [d for d in epochs if d.name >= args.since]
    if not epochs:
        print(f"no epochs under {args.watch_root}")
        return 1

    head: List[str] = []
    head.append("# Epoch review — the same prompts, vanilla against llama-leash\n")
    head.append("Oldest epoch first. Each section carries, in this order:\n")
    head.append("1. **The prompt** fed for every task that epoch, read from the manifest "
                "as of that epoch's commit — not today's, because the corpus itself has "
                "been edited during the campaign.")
    head.append("2. **The resulting code**, in full, for each arm.")
    head.append("3. **Time and tokens by phase** — real sub-sessions for `conductor`, "
                "per-turn for `baseline`, which has no phase structure to group.")
    head.append("4. **The changes committed** since the previous epoch.\n")
    for arm in ARMS:
        head.append(f"- **`{arm}`** — {ARM_BLURB[arm]}")
    head.append("")
    head.append("## Contents\n")
    for i, d in enumerate(epochs, 1):
        head.append(f"- [Epoch {i} — {d.name}](#epoch-{i}--{d.name.replace('-', '')})")
    head.append("")

    body: List[str] = []
    previous: Optional[datetime] = None
    for i, d in enumerate(epochs, 1):
        body.append(render_epoch(d, args.work_root, i, previous))
        previous = epoch_start(d)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(head) + "\n".join(body) + "\n")
    print(f"{args.out}  ({args.out.stat().st_size:,} bytes, {len(epochs)} epochs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

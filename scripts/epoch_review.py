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


# Every manifest a run can be launched from, most authoritative first. A cell's
# result JSON records its task id and not the manifest that defined it, so the
# task is looked up across all of them; the order decides a collision, which
# makes the reading stable rather than dependent on directory order.
MANIFEST_PATHS = (
    "bench/conductor-tasks.json",
    "bench/corpus-euler.json",
    "bench/corpus-games.json",
    "bench/corpus-systems.json",
    "bench/corpus-repair.json",
    "bench/corpus-perf.json",
)


def tasks_from_manifests(docs: Dict[str, Optional[dict]]) -> Dict[str, dict]:
    """Every task in every manifest, keyed by id, tagged with where it came from.

    First writer wins, so `MANIFEST_PATHS` order is what resolves an id defined
    twice. `_manifest` is added to each entry because a reader comparing two
    epochs needs to know which file defined the prompt — two manifests can ask
    for the same task id and mean different things.

    An unreadable manifest costs only itself: one malformed file used to empty
    the whole lookup, and every task in the epoch then reported as absent.
    """
    def precedence(path: str) -> Tuple[int, str]:
        # Ordered by MANIFEST_PATHS, not by however the caller built the dict:
        # a collision must resolve the same way whoever calls this and in
        # whatever order they happened to read the files.
        try:
            return (MANIFEST_PATHS.index(path), path)
        except ValueError:
            return (len(MANIFEST_PATHS), path)

    found: Dict[str, dict] = {}
    for path in sorted(docs, key=precedence):
        doc = docs[path]
        if not isinstance(doc, dict) and not isinstance(doc, list):
            continue
        entries = doc["tasks"] if isinstance(doc, dict) else doc
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict) or "id" not in entry:
                continue
            if entry["id"] in found:
                continue
            found[entry["id"]] = {**entry, "_manifest": path}
    return found


def manifest_at(sha: Optional[str]) -> Dict[str, dict]:
    """Every manifest as of a commit, keyed by task id; empty if none are readable.

    Reading ONE manifest was the defect: a run launched from any corpus set
    reported "does not carry this task" for every task it ran, which names the
    manifest as the culprit when the reader was looking in the wrong file. The
    prompt is the field every other section is downstream of, so losing it loses
    the epoch.
    """
    if sha is None:
        return {}
    docs: Dict[str, Optional[dict]] = {}
    for path in MANIFEST_PATHS:
        raw = _git("show", f"{sha}:{path}")
        if not raw.strip():
            continue
        try:
            docs[path] = json.loads(raw)
        except json.JSONDecodeError:
            docs[path] = None
    return tasks_from_manifests(docs)


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
class ToolCall:
    """One tool call as the model made it: the name, what went in, what came back."""

    name: str
    input: str
    output: str
    status: str


@dataclass
class Turn:
    session: str
    session_id: str
    agent: str
    seconds: float
    out_tokens: int
    in_tokens: int
    tools: List[str] = field(default_factory=list)
    # The three things the phase table cannot carry. They sit in the session
    # store beside the timings and were simply never read out of it.
    reasoning: List[str] = field(default_factory=list)
    text: List[str] = field(default_factory=list)
    calls: List[ToolCall] = field(default_factory=list)


# Per rendered block. A transcript is the largest thing this document holds — one
# conductor cell carries hundreds of reasoning blocks — so it is bounded, and
# every cut says how much it cut.
REASONING_CHARS = 4000
TOOL_INPUT_CHARS = 600
TOOL_OUTPUT_CHARS = 1200


def clip(text: str, limit: int) -> str:
    """`text`, or its first `limit` characters with the loss stated.

    Silently shortening a tool result reads as a short result, and a reader
    comparing two arms draws a conclusion from the difference. The marker carries
    the true length so the difference stays visible.
    """
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return "%s\n… (truncated: %d of %d characters shown)" % (
        text[:limit], limit, len(text))


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
        reasoning: Dict[str, List[str]] = {}
        texts: Dict[str, List[str]] = {}
        calls: Dict[str, List[ToolCall]] = {}
        for mid, data in conn.execute("select message_id, data from part"):
            try:
                part = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                continue
            kind = part.get("type")
            if kind == "tool" and part.get("tool"):
                tools.setdefault(mid, []).append(str(part["tool"]))
                state = part.get("state") or {}
                raw_input = state.get("input")
                calls.setdefault(mid, []).append(ToolCall(
                    name=str(part["tool"]),
                    input=(json.dumps(raw_input, indent=1) if isinstance(raw_input, (dict, list))
                           else str(raw_input or "")),
                    output=str(state.get("output") or ""),
                    status=str(state.get("status") or ""),
                ))
            elif kind == "reasoning" and part.get("text"):
                reasoning.setdefault(mid, []).append(str(part["text"]))
            elif kind == "text" and part.get("text"):
                texts.setdefault(mid, []).append(str(part["text"]))
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
            reasoning=reasoning.get(mid, []),
            text=texts.get(mid, []),
            calls=calls.get(mid, []),
        ))
    return turns


def transcript_lines(turns: Sequence[Turn]) -> List[str]:
    """Every turn as it happened: what it thought, what it called, what it said.

    The phase table above answers what a run COST. This answers what it DID, which
    is the question anyone comparing two arms is actually asking and the one no
    aggregate can reach.
    """
    lines: List[str] = []
    for index, turn in enumerate(turns, start=1):
        head = "**turn %d** · `%s`" % (index, turn.session or turn.agent or "(unnamed)")
        lines.append("%s · %.0fs · %d tokens out" % (head, turn.seconds, turn.out_tokens))
        lines.append("")
        if turn.reasoning:
            for block in turn.reasoning:
                lines.append("> **thinking**")
                for row in clip(block, REASONING_CHARS).splitlines():
                    lines.append("> %s" % row)
                lines.append("")
        else:
            # An absent reasoning block and one nobody rendered look identical,
            # and only one of them is a fact about the run.
            lines.append("> _no reasoning recorded for this turn_")
            lines.append("")
        for call in turn.calls:
            lines.append("**tool `%s`**%s" % (
                call.name, "" if call.status in ("completed", "") else " · %s" % call.status))
            lines.append("")
            lines.append("_input_")
            lines.append("```")
            lines.append(clip(call.input, TOOL_INPUT_CHARS))
            lines.append("```")
            lines.append("_output_")
            lines.append("```")
            lines.append(clip(call.output, TOOL_OUTPUT_CHARS))
            lines.append("```")
            lines.append("")
        for said in turn.text:
            lines.append("**said**")
            lines.append("")
            lines.append(clip(said, REASONING_CHARS))
            lines.append("")
    return lines


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
            raw = path.read_bytes()
        except OSError:
            continue
        out[str(rel)] = _as_reviewable_text(raw, path)
    return out


# A produced file is evidence twice over: that it exists, and what is in it. For
# a compiled binary only the first is readable, and the second is actively
# harmful — the first C++ task in the corpus put a Mach-O executable in the work
# tree and 262 KB of it went verbatim into REVIEW.md, control bytes included,
# which is what the ops-docs gate then refused. The file keeps its NAME and its
# size; its bytes do not reach the markdown.
def _as_reviewable_text(raw: bytes, path: Path) -> str:
    """The file's content when it is text, and a one-line stand-in when it is not.

    A NUL is the test, because it is the one byte that cannot appear in any text
    a model writes and does appear in the header of every object format. A file
    that decodes but is full of other control characters is left alone: that is a
    text file with something odd in it, and hiding it would hide the oddity.
    """
    if b"\x00" not in raw:
        return raw.decode("utf-8", errors="replace")
    return "(binary, %d bytes — content omitted; the build output is evidence that a build " \
           "happened, not evidence a reader can use)" % len(raw)


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


def load_all_results(results_dir: Path) -> Dict[Tuple[str, str], List[dict]]:
    """Every cell, keeping repetitions rather than letting the last file win.

    `load_results` above is deliberately last-wins: the per-epoch document renders
    one tree and one transcript per arm, and three would be three of the same
    thing. The trend table is the opposite case — repetitions ARE the measurement
    there, because an arm's spread is what a reader compares an improvement
    against.
    """
    found: Dict[Tuple[str, str], List[dict]] = {}
    for f in sorted(results_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "arm" in d and "taskId" in d:
            found.setdefault((d["arm"], d["taskId"]), []).append(d)
    return found


def trend_cell_many(records: Sequence[dict]) -> str:
    """One epoch's outcomes for one (task, arm), repetitions and all.

    A single repetition reads exactly as it always did. Several render as a
    count, the verdicts that actually occurred, and the range — because the
    spread is the thing a later epoch's single number has to be judged against,
    and collapsing it to one repetition hides the noise floor inside the figure
    a reader would compare.
    """
    if not records:
        return "\u2013"
    if len(records) == 1:
        return trend_cell(records[0])
    verdicts: List[str] = []
    for record in records:
        head = "TIMEOUT" if record.get("timedOut") else ("PASS" if record.get("passed") else "FAIL")
        if head not in verdicts:
            verdicts.append(head)
    minutes = sorted((r.get("wallClockMs") or 0) / 60000.0 for r in records)
    tokens = sorted(int((r.get("tokens") or {}).get("completion") or 0) for r in records)
    return "%s x%d %.1f\u2013%.1fm %d\u2013%dt" % (
        "/".join(verdicts), len(records), minutes[0], minutes[-1], tokens[0], tokens[-1])


def epoch_start(results_dir: Path) -> datetime:
    """The epoch's own clock.

    Three sources, in order of how directly each knows the answer. The directory
    name is the convention `run_and_watch` mints and carries the start to the
    second. A directory named for what the run was FOR — which every
    investigation run uses — knows nothing, so the cells are asked instead: each
    result carries `startedIso`, and the earliest is when the epoch began.

    The last fallback is the directory's own mtime, and it exists so that one
    unreadable epoch costs itself a precise clock rather than costing every other
    epoch its section. Raising here discarded the whole document.
    """
    try:
        return datetime.strptime(results_dir.name, "%Y%m%d-%H%M%S").astimezone()
    except ValueError:
        pass
    started: List[datetime] = []
    for path in sorted(results_dir.glob("*.json")):
        try:
            stamp = json.loads(path.read_text()).get("startedIso")
        except (OSError, json.JSONDecodeError, AttributeError):
            continue
        if not isinstance(stamp, str) or not stamp:
            continue
        try:
            # `startedIso` is spelled with a trailing Z, which /usr/bin/python3's
            # 3.9 fromisoformat rejects outright.
            started.append(datetime.fromisoformat(stamp.replace("Z", "+00:00")))
        except ValueError:
            continue
    if started:
        return min(started).astimezone()
    try:
        return datetime.fromtimestamp(results_dir.stat().st_mtime).astimezone()
    except OSError:
        return datetime.fromtimestamp(0).astimezone()


@dataclass
class Dispatch:
    """One sub-agent as the run created it: its role, its prompt, what came back.

    `ok` is None for a dispatch with no completion record — a sub-agent still
    generating when the cell's ceiling fired. Unfinished and failed are different
    facts about a run and a False here would merge them.
    """

    role: str
    prompt: str
    ok: Optional[bool] = None
    attempts: Optional[int] = None
    response: str = ""


def subagent_dispatches(repo_dir: Path) -> List[Dispatch]:
    """Every sub-agent the conductor arm dispatched, in order, with its prompt.

    The session store cannot answer this. `read_turns` keeps `role ==
    "assistant"` messages, and a sub-session's prompt is a user-role message, so
    the transcript shows what each sub-agent DID and never what it was TOLD. The
    journal records the prompt verbatim on `subsession.dispatched`, and joining
    the two is the only way the document can show both.

    An arm with no journal returns nothing rather than raising: baseline and
    doctrine load no plugin, so writing no journal is what they are supposed to
    do, and it is not an error to report.
    """
    runs = repo_dir / ".conductor" / "runs"
    if not runs.is_dir():
        return []
    out: List[Dispatch] = []
    for journal in sorted(runs.glob("*/journal.jsonl")):
        try:
            text = journal.read_text(errors="replace")
        except OSError:
            continue
        pending: Optional[Dispatch] = None
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            data = record.get("data") or {}
            if record.get("event") == "subsession.dispatched":
                pending = Dispatch(role=str(data.get("role") or "(unnamed)"),
                                   prompt=str(data.get("prompt") or ""))
                out.append(pending)
            elif record.get("event") == "subsession.complete" and pending is not None:
                pending.ok = bool(data.get("ok"))
                attempts = data.get("attempts")
                pending.attempts = int(attempts) if isinstance(attempts, int) else None
                pending.response = str(data.get("response") or "")
                pending = None
    return out


def verdict(record: Optional[dict]) -> str:
    if record is None:
        return "not run"
    if record.get("timedOut"):
        return "TIMED OUT"
    return "PASS" if record.get("passed") else "FAIL"


def render_epoch(results_dir: Path, work_root: Path, index: int,
                 previous: Optional[datetime], transcripts: bool = True) -> str:
    started = epoch_start(results_dir)
    results = load_results(results_dir)
    sha = commit_at(started)
    manifest = manifest_at(sha)
    out: List[str] = []
    w = out.append

    w(f"\n---\n\n# Epoch {index} — `{results_dir.name}`\n")
    w(f"Started {started:%Y-%m-%d %H:%M %Z} · {len(results)} cells\n")

    w("## 1 · Changes since the previous epoch\n")
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

        w("### 2 · The prompt, as it was fed this epoch\n")
        prompt = entry.get("prompt")
        if prompt:
            source = entry.get("_manifest")
            if source:
                w("From `%s` as of `%s`.\n" % (source, (sha or "?")[:12]))
            w("```")
            w(prompt)
            w("```\n")
        else:
            # Naming the search, not the manifest. "The manifest does not carry
            # this task" asserts a fact about the corpus; the true statement is
            # that this reader looked in a stated list and did not find it, which
            # is the sentence that tells someone where to go next.
            w("_Not recovered. Searched %s at commit `%s` and none defines task "
              "`%s`. The prompt is the field every other section is downstream "
              "of, so this epoch cannot be used to decide where to focus until "
              "it is._\n" % (", ".join("`%s`" % m for m in MANIFEST_PATHS),
                              (sha or "unknown")[:12], tid))

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

            w("#### 3a · Cost by phase\n")
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

            # No early exit below this point: an arm that produced nothing is the
            # arm whose transcript a reader most needs, and a `continue` here
            # drops it for exactly those cells.
            w("#### 3b · The resulting code\n")
            if repo is None:
                w("_Not preserved. `run_and_watch.py` clears the work root at the start of "
                  "every run, so this epoch's trees were destroyed when the next one "
                  "launched._\n")
            else:
                produced = source_files(repo)
                seeds = entry.get("seedFiles") or {}
                changed = {p: b for p, b in produced.items() if p not in seeds or seeds[p] != b}
                if not changed:
                    w("**Unchanged from the seed — this arm produced no code.**\n")
                for path, body in sorted(changed.items()):
                    w(f"`{path}` ({'created' if path not in seeds else 'modified'})\n")
                    w(f"```{fence(path)}")
                    w(body.rstrip("\n") if body.strip() else "(empty)")
                    w("```\n")

            # Between the code and the transcript, because it explains the
            # transcript: every sub-agent turn below belongs to one of these
            # dispatches, and the store cannot say what any of them was asked.
            dispatches = subagent_dispatches(repo) if repo is not None else []
            if dispatches:
                w("#### 3c · Sub-agents dispatched\n")
                w("What each sub-agent was ASKED, read from the run journal. The session "
                  "store holds only assistant turns, so this is the half of a sub-session "
                  "that the transcript below structurally cannot show.\n")
                for number, dispatch in enumerate(dispatches, start=1):
                    if dispatch.ok is None:
                        verdict_text = "still generating when the cell ended"
                    elif dispatch.ok:
                        verdict_text = "answered on attempt %s" % (dispatch.attempts or 1)
                    else:
                        verdict_text = "produced no valid reply"
                    w("**%d · `%s`** — %s\n" % (number, dispatch.role, verdict_text))
                    w("_prompt_")
                    w("```")
                    w(clip(dispatch.prompt, TOOL_INPUT_CHARS))
                    w("```")
                    if dispatch.response:
                        w("_reply_")
                        w("```")
                        w(clip(dispatch.response, TOOL_OUTPUT_CHARS))
                        w("```")
                    w("")
            elif repo is not None and arm == "conductor":
                w("#### 3c · Sub-agents dispatched\n")
                w("_None: this cell wrote no journal, or ended before it dispatched one._\n")

            w("#### 3d · The transcript\n")
            if not transcripts:
                # Omitting the section silently would read as "this arm did
                # nothing worth showing", which is a different claim entirely.
                w("_Omitted: this document was generated with `--no-transcripts`._\n")
            elif not turns:
                w("_No session store was archived for this cell, so there is no "
                  "transcript to show. Epochs before tree archiving landed have "
                  "prompts, outcomes and timings but no turns._\n")
            else:
                for line in transcript_lines(turns):
                    w(line)
                w("")
    return "\n".join(out)


@dataclass
class TrendRow:
    """One (task, arm) across every epoch that ran it."""

    task: str
    arm: str
    cells: Dict[str, str] = field(default_factory=dict)


def trend_cell(record: Optional[dict]) -> str:
    """One epoch's outcome for one (task, arm), as a phrase rather than a number.

    A cell that did not run, a cell that failed and a cell that ran out of clock
    are three different facts, and the campaign has been bitten five times by a
    metric that renders them alike. They get three different words here.
    """
    if record is None:
        return "\u2013"
    tokens = (record.get("tokens") or {}).get("completion")
    minutes = (record.get("wallClockMs") or 0) / 60000.0
    if record.get("timedOut"):
        head = "TIMEOUT"
    elif record.get("passed"):
        head = "PASS"
    else:
        head = "FAIL"
    return "%s %.1fm %st" % (head, minutes, tokens if tokens is not None else "?")


def trend_rows(epochs: Sequence[Tuple[str, Dict[Tuple[str, str], dict]]]) -> List[TrendRow]:
    """The cross-epoch table: one row per (task, arm), one column per epoch.

    This is the only view that answers what CHANGED. A per-epoch document can say
    a cell timed out; only the row across epochs says it has timed out four times
    and got slower each time.

    Keyed on `startedIso`: a results directory holding a cell JSON is
    conductor_bench's resume ledger, so a later epoch can carry an earlier
    epoch's cell file byte for byte — the grid2048 baseline and doctrine cells
    appear in four step directories with one startedIso between them. A cell
    whose every record was already claimed by an earlier epoch renders as
    `=<that epoch>`, never as a fresh verdict.
    """
    rows: Dict[Tuple[str, str], TrendRow] = {}
    order: List[Tuple[str, str]] = []
    # startedIso stamps already rendered, per (task, arm), mapped to the label
    # of the epoch that measured them.
    claimed: Dict[Tuple[str, str], Dict[str, str]] = {}
    for label, results in epochs:
        for (arm, task), record in results.items():
            key = (task, arm)
            if key not in rows:
                rows[key] = TrendRow(task=task, arm=arm)
                order.append(key)
            # One record or a list of them: the trend table is the only caller
            # that keeps repetitions, and both spellings reach it.
            batch = record if isinstance(record, list) else [record]
            stamps = claimed.setdefault(key, {})
            fresh: List[dict] = []
            carried: List[str] = []
            for rec in batch:
                stamp = rec.get("startedIso") if isinstance(rec, dict) else None
                if isinstance(stamp, str) and stamp:
                    if stamp in stamps:
                        carried.append(stamps[stamp])
                        continue
                    stamps[stamp] = label
                # A record with no startedIso cannot be deduplicated and is
                # rendered as what it claims to be.
                fresh.append(rec)
            if fresh:
                cell = trend_cell_many(fresh)
                if carried:
                    cell += " (+%d carried)" % len(carried)
            else:
                cell = "=%s" % sorted(set(carried))[0]
            rows[key].cells[label] = cell
    return [rows[key] for key in sorted(order)]


def render_index(watch_root: Path, epochs: Sequence[Path],
                 written: Sequence[Path]) -> str:
    """The front page: every epoch, and every task's history across all of them."""
    out: List[str] = []
    w = out.append
    w("# Epoch index — the same prompts, vanilla against llama-leash\n")
    w("One directory per epoch, newest last. Each holds `REVIEW.md`: the prompt as it")
    w("was fed that epoch, the changes committed since the previous one, and then per")
    w("arm the produced code, the cost by phase, every sub-agent's dispatch prompt, and")
    w("the full transcript.\n")
    for arm in ARMS:
        w(f"- **`{arm}`** \u2014 {ARM_BLURB[arm]}")
    w("")
    w("## Epochs\n")
    w("| # | epoch | started | cells | review |")
    w("|---:|---|---|---:|---|")
    labels: List[str] = []
    collected: List[Tuple[str, Dict[Tuple[str, str], dict]]] = []
    for index, (results_dir, review) in enumerate(zip(epochs, written), start=1):
        results = load_all_results(results_dir)
        started = epoch_start(results_dir)
        label = results_dir.name
        labels.append(label)
        collected.append((label, results))
        cells = sum(len(batch) for batch in results.values())
        w("| %d | `%s` | %s | %d | [REVIEW](%s/REVIEW.md) |"
          % (index, label, started.strftime("%Y-%m-%d %H:%M"), cells, review.parent.name))
    w("")
    w("## What changed across epochs\n")
    w("One row per task and arm. `\u2013` is an epoch that did not run that cell, which")
    w("is not the same fact as a failure and does not share its word.\n")
    w("| task | arm | " + " | ".join("`%s`" % l for l in labels) + " |")
    w("|---|---|" + "---|" * len(labels))
    for row in trend_rows(collected):
        w("| `%s` | `%s` | %s |"
          % (row.task, row.arm, " | ".join(row.cells.get(l, "\u2013") for l in labels)))
    w("")
    return "\n".join(out)


def write_epoch_tree(watch_root: Path, work_root: Path, out_dir: Path,
                     transcripts: bool = True, since: str = "") -> List[Path]:
    """One directory per epoch plus an index, and the list of files written.

    Splitting is what makes the document usable rather than merely present: a
    single file over fourteen epochs reached 614 KB, which is why nothing ever
    ran it automatically. Per epoch it is diffable, and a run can emit its own
    section without rewriting anyone else's.
    """
    epochs = sorted(d for d in watch_root.iterdir()
                    if d.is_dir() and any(d.glob("*.json")))
    if since:
        epochs = [d for d in epochs if d.name >= since]
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    previous: Optional[datetime] = None
    for index, results_dir in enumerate(epochs, start=1):
        section = out_dir / ("%02d-%s" % (index, results_dir.name))
        section.mkdir(parents=True, exist_ok=True)
        body = render_epoch(results_dir, work_root, index, previous, transcripts=transcripts)
        review = section / "REVIEW.md"
        review.write_text(body.lstrip("\n-").lstrip() + "\n")
        written.append(review)
        previous = epoch_start(results_dir)
    (out_dir / "INDEX.md").write_text(render_index(watch_root, epochs, written) + "\n")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("watch_root", type=Path)
    ap.add_argument("--work-root", type=Path, default=Path.home() / ".llama-leash-work")
    ap.add_argument("--out", type=Path, default=None,
                    help="write ONE document holding every epoch")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="write one directory per epoch plus INDEX.md; the shape a "
                         "run emits, because a single document over fourteen epochs "
                         "reached 614 KB and nothing ever ran it automatically")
    ap.add_argument("--since", default="", help="only epochs at or after this directory name")
    ap.add_argument("--no-transcripts", action="store_true", dest="no_transcripts",
                    help="omit per-turn reasoning, tool calls and tool output; the "
                         "document says so where they would have been")
    args = ap.parse_args()

    if args.out is None and args.out_dir is None:
        print("epoch_review: pass --out (one document) or --out-dir (one per epoch)")
        return 2

    epochs = sorted(d for d in args.watch_root.iterdir()
                    if d.is_dir() and any(d.glob("*.json")))
    if args.since:
        epochs = [d for d in epochs if d.name >= args.since]
    if not epochs:
        print(f"no epochs under {args.watch_root}")
        return 1

    if args.out_dir is not None:
        written = write_epoch_tree(args.watch_root, args.work_root, args.out_dir,
                                   transcripts=not args.no_transcripts, since=args.since)
        total = sum(p.stat().st_size for p in written)
        print("%s  (%d epoch(s), %s bytes, index at %s)"
              % (args.out_dir, len(written), format(total, ","), args.out_dir / "INDEX.md"))
        if args.out is None:
            return 0

    head: List[str] = []
    head.append("# Epoch review — the same prompts, vanilla against llama-leash\n")
    head.append("Oldest epoch first. Sections are numbered in the order they appear:\n")
    head.append("1. **The changes committed** since the previous epoch, with the defect "
                "each names.")
    head.append("2. **The prompt** fed for every task that epoch, read from the manifest "
                "as of that epoch's commit — not today's, because the corpus itself has "
                "been edited during the campaign — and labelled with which manifest "
                "defined it.")
    head.append("3. Then, per arm: **3a** time and tokens by phase (real sub-sessions for "
                "`conductor`, per-turn for the flat arms); **3b** the resulting code in "
                "full; **3c** every sub-agent dispatched, with the prompt it was given "
                "and the reply it returned; **3d** the transcript of every turn — what "
                "the model was thinking, which tools it called with which arguments, "
                "what came back, and what it said. Long blocks are clipped and every "
                "clip states how much it cut.\n")
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
        body.append(render_epoch(d, args.work_root, i, previous,
                                 transcripts=not args.no_transcripts))
        previous = epoch_start(d)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(head) + "\n".join(body) + "\n")
    print(f"{args.out}  ({args.out.stat().st_size:,} bytes, {len(epochs)} epochs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Generate a side-by-side review of what each arm produced for the same prompt.

The campaign register records WHY cells behaved as they did. Nothing rendered the
thing a reader actually wants first: here is the request, here is what the stock
model did with it, here is what the harness did with it, and here is the test
neither of them could see.

One section per task. Inside it, the prompt verbatim, the tree the arm started
from, the hidden gauge that judged it, and then each arm's finished source with
its outcome — so `baseline` (stock opencode, no plugin, no doctrine) and
`conductor` (plugin + FSM + sub-session fan-out) sit against the same prompt on
the same page.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
ARMS = ("baseline", "doctrine", "conductor")

ARM_BLURB = {
    "baseline": "stock opencode `build` agent. No plugin, no doctrine, no fan-out. "
                "This is llama.cpp + vanilla opencode.",
    "doctrine": "the nine doctrine packs injected as a static system prompt. "
                "No plugin, no state machine, no sub-sessions.",
    "conductor": "the full workspace: opencode plugin, run FSM, gates, and "
                 "sub-session fan-out (classifier, skeptic, planner, implementer, reviewers).",
}

# Directories that are harness furniture rather than the model's work.
SKIP_DIRS = {".git", ".conductor", "node_modules", "__pycache__", ".opencode"}

# How far a cell tree's creation may sit from its result's startedIso before the
# two are judged to belong to different runs.
#
# run_and_watch.py clears the work root at the START of every epoch, so the trees
# on disk always belong to the MOST RECENT run while a results directory can name
# any earlier one. Pairing them renders a comparison that never happened, and it
# looks entirely plausible: correct wall clock from the result beside source and
# token counts from a different epoch. The report refuses that pairing rather than
# printing it.
STALE_TREE_TOLERANCE_S = 3600.0


def tree_matches_result(cell: Path, record: Optional[dict]) -> bool:
    """Whether this on-disk cell belongs to the run that produced `record`."""
    if record is None:
        return False
    started = record.get("startedIso")
    if not isinstance(started, str) or not started:
        return False
    try:
        began = datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return False
    try:
        stat = cell.stat()
    except OSError:
        return False
    born = getattr(stat, "st_birthtime", stat.st_mtime)
    return abs(born - began) <= STALE_TREE_TOLERANCE_S


def source_files(root: Path, include_gauge: bool = False) -> Dict[str, str]:
    """Every readable source file under a tree, keyed by repo-relative path."""
    out: Dict[str, str] = {}
    if not root.exists():
        return out
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not include_gauge and rel.parts and rel.parts[0] == "gauge":
            continue
        try:
            out[str(rel)] = path.read_text(errors="replace")
        except OSError:
            continue
    return out


def fence(path: str) -> str:
    return {"ts": "ts", "py": "python", "md": "markdown", "json": "json"}.get(
        path.rsplit(".", 1)[-1], ""
    )


def load_results(results_dir: Path) -> Dict[Tuple[str, str], dict]:
    """(arm, taskId) -> result record, for every cell the epoch scored."""
    found: Dict[Tuple[str, str], dict] = {}
    for f in sorted(results_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "arm" in d and "taskId" in d:
            found[(d["arm"], d["taskId"])] = d
    return found


def generated_tokens(cell: Path, record: Optional[dict]) -> Optional[int]:
    """The cell's emitted-token count, or None if it is gone or from another run."""
    if not tree_matches_result(cell, record):
        return None
    if not (cell / "home/data/opencode/opencode.db").exists():
        return None
    try:
        out = subprocess.run(
            ["/usr/bin/python3", str(REPO / "scripts/gen_tokens.py"), str(cell)],
            capture_output=True, text=True, timeout=180,
        ).stdout
        # gen_tokens prints `arm task tokens think% parts predicted`, and for a
        # single cell the arm column is empty — so the token count is the first
        # bare integer on the row, not a fixed position.
        for line in out.splitlines()[1:]:
            for part in line.split():
                if part.isdigit():
                    return int(part)
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def outcome_line(record: Optional[dict], tokens: Optional[int]) -> str:
    if record is None:
        return "**not run**"
    gauge = record.get("gauge") or {}
    verdict = (
        "TIMED OUT" if record.get("timedOut")
        else ("PASS" if record.get("passed") else "FAIL")
    )
    mins = record.get("wallClockMs", 0) / 60000.0
    bits = [
        f"**{verdict}**",
        f"{mins:.1f} min",
        f"hidden tests: {'pass' if gauge.get('passed') else 'fail'}",
    ]
    if tokens is not None:
        bits.append(f"{tokens:,} generated tokens")
    if record.get("waves"):
        bits.append(f"{record['waves']} waves")
    return " · ".join(bits)


def render(tasks: List[dict], work_root: Path, results_dir: Path, model: str,
           mechanism: str, rep: str) -> str:
    results = load_results(results_dir)
    out: List[str] = []
    w = out.append

    w("# Arm comparison — the same prompt, three harnesses\n")
    w(f"Generated from `{results_dir}` and the work trees under `{work_root}`.\n")
    w("Each task below shows the request, the tree the model started from, the hidden")
    w("test it was judged by and never saw, and then what each arm actually produced.\n")
    for arm in ARMS:
        w(f"- **`{arm}`** — {ARM_BLURB[arm]}")
    w("")

    w("## Scoreboard\n")
    w("| task | " + " | ".join(f"`{a}`" for a in ARMS) + " |")
    w("|---|" + "---|" * len(ARMS))
    for task in tasks:
        cells = []
        for arm in ARMS:
            r = results.get((arm, task["id"]))
            if r is None:
                cells.append("–")
            elif r.get("timedOut"):
                cells.append("TIMEOUT")
            elif r.get("passed"):
                cells.append("**pass**")
            else:
                cells.append("fail")
        w(f"| `{task['id']}` | " + " | ".join(cells) + " |")
    w("")

    for task in tasks:
        tid = task["id"]
        w("\n---\n")
        w(f"# `{tid}`  ({task.get('tier', '?')})\n")
        w("## The request\n")
        w("```")
        w(task.get("prompt", "").replace("\\n", "\n"))
        w("```\n")

        seeds = task.get("seedFiles", {}) or {}
        w(f"## What it started from  ({len(seeds)} file(s))\n")
        for path, body in sorted(seeds.items()):
            w(f"`{path}`\n")
            w(f"```{fence(path)}")
            w(body.rstrip("\n") if body.strip() else "(empty)")
            w("```\n")

        # The hidden gauge, read from any arm's tree (identical across arms).
        gauge: Dict[str, str] = {}
        for arm in ARMS:
            cell = work_root / model / mechanism / arm / tid / rep
            if not tree_matches_result(cell, results.get((arm, tid))):
                continue
            g = {k: v for k, v in source_files(cell / "repo", include_gauge=True).items()
                 if k.startswith("gauge/")}
            if g:
                gauge = g
                break
        if gauge:
            w("## The hidden test it was judged by\n")
            w("Materialized only after the process exits, so no arm can read or edit it.\n")
            for path, body in sorted(gauge.items()):
                w(f"`{path}`\n")
                w(f"```{fence(path)}")
                w(body.rstrip("\n"))
                w("```\n")

        for arm in ARMS:
            cell = work_root / model / mechanism / arm / tid / rep
            record = results.get((arm, tid))
            w(f"\n## `{arm}` — {ARM_BLURB[arm]}\n")
            w(outcome_line(record, generated_tokens(cell, record)) + "\n")

            if not tree_matches_result(cell, record):
                w("_No tree for this run. `run_and_watch.py` clears the work root at the start "
                  "of every epoch, so only the most recent run's trees survive — and pairing "
                  "these results with what is on disk would render a comparison that never "
                  "happened._\n")
                continue
            produced = source_files(cell / "repo")
            if not produced:
                w("_The cell directory exists but holds no source._\n")
                continue
            changed = {p: b for p, b in produced.items()
                       if p not in seeds or seeds[p] != b}
            added = [p for p in changed if p not in seeds]
            if not changed:
                w("**The tree is unchanged from the seed — this arm produced nothing.**\n")
                continue
            w(f"Touched {len(changed)} file(s)"
              + (f", {len(added)} of them created" if added else "") + ".\n")
            for path, body in sorted(changed.items()):
                mark = "created" if path not in seeds else "modified"
                w(f"`{path}` ({mark})\n")
                w(f"```{fence(path)}")
                w(body.rstrip("\n") if body.strip() else "(empty)")
                w("```\n")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("results_dir", type=Path)
    ap.add_argument("--work-root", type=Path, default=Path.home() / ".llama-leash-work")
    ap.add_argument("--manifest", type=Path, default=REPO / "bench/conductor-tasks.json")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--model", default="llamacpp-qwen3.8-27b")
    ap.add_argument("--mechanism", default="none")
    ap.add_argument("--rep", default="r1")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    all_tasks = manifest["tasks"] if isinstance(manifest, dict) else manifest
    ran = {tid for (_, tid) in load_results(args.results_dir)}
    tasks = [t for t in all_tasks if t["id"] in ran]
    if not tasks:
        print(f"no results under {args.results_dir}")
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render(tasks, args.work_root, args.results_dir,
                               args.model, args.mechanism, args.rep))
    print(f"{args.out}  ({args.out.stat().st_size:,} bytes, {len(tasks)} task(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

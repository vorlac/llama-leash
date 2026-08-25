"""Report each arm's cost as a multiple of the baseline arm, within one epoch.

Absolute figures do not survive this campaign's noise. The control arm — no packs,
no plugin, unreachable by any change made to the harness — measured 6,364 and then
614 generated tokens on an identical cell in consecutive epochs. Every cross-epoch
absolute comparison in the register was made against a floor nobody had measured.

A ratio taken inside ONE epoch cancels that: same machine, same thermal state, same
weights, same prompt. What it does not cancel is the denominator's own noise, which
it inherits multiplicatively — against 614 the conductor arm looks ten times worse
than against 6,364, for the same numerator. So the denominator is the median of the
epoch's baseline repetitions, and a single-sample denominator is reported as
degraded rather than quietly used.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

REPO = Path(__file__).resolve().parent.parent
ARMS = ("baseline", "doctrine", "conductor")
BASELINE = "baseline"

# Below this, a ratio is arithmetically true and not interesting: a task the
# baseline finishes in forty seconds turns a two-minute run into "3x". Report the
# absolute instead and say why.
MIN_MEANINGFUL_MINUTES = 1.5
MIN_MEANINGFUL_TOKENS = 800


@dataclass(frozen=True)
class Cell:
    arm: str
    task: str
    rep: int
    cell_id: str
    minutes: float
    passed: bool
    timed_out: bool
    tokens: Optional[int] = None


def load_cells(results_dir: Path) -> List[Cell]:
    out: List[Cell] = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if "arm" not in d or "taskId" not in d:
            continue
        out.append(Cell(
            arm=d["arm"], task=d["taskId"], rep=int(d.get("rep", 1)),
            cell_id=d.get("cellId", ""),
            minutes=d.get("wallClockMs", 0) / 60000.0,
            passed=bool(d.get("passed")), timed_out=bool(d.get("timedOut")),
            tokens=generated_tokens(results_dir, d.get("cellId", "")),
        ))
    return out


def generated_tokens(results_dir: Path, cell_id: str) -> Optional[int]:
    """Emitted tokens from the archived session store, or None if not archived."""
    if not cell_id:
        return None
    cell = results_dir / "trees" / cell_id.replace("/", "__")
    if not (cell / "session" / "opencode.db").exists():
        return None
    try:
        out = subprocess.run(
            ["/usr/bin/python3", str(REPO / "scripts/gen_tokens.py"), str(cell)],
            capture_output=True, text=True, timeout=180,
        ).stdout
        for line in out.splitlines()[1:]:
            for part in line.split():
                if part.isdigit():
                    return int(part)
    except (OSError, subprocess.SubprocessError):
        pass
    return None


@dataclass(frozen=True)
class Denominator:
    """A baseline median, with how much confidence it has earned."""

    value: Optional[float]
    samples: int
    note: str

    @property
    def usable(self) -> bool:
        return self.value is not None and self.value > 0


def baseline_median(cells: Sequence[Cell], task: str, field: str) -> Denominator:
    """Median of the baseline arm's successful reps for one task.

    Failed and timed-out baseline runs are excluded: a run that did not finish the
    work is not a measurement of how long the work takes. A task with no successful
    baseline has NO denominator, and the honest report is to say so rather than
    divide by a failure.
    """
    succeeded = [c for c in cells
                 if c.arm == BASELINE and c.task == task and c.passed and not c.timed_out]
    values = [getattr(c, field) for c in succeeded if getattr(c, field) is not None]
    if not values:
        # Two different absences, and they call for opposite responses: a baseline
        # that FAILED is a result about the task, while a measurement that was
        # never archived is a gap in the instrument. Reporting them identically is
        # the defect this campaign has now met three times (D18, the vacuous
        # fingerprint, and here).
        if not succeeded:
            return Denominator(None, 0, "no successful baseline run — no denominator")
        return Denominator(
            None, 0,
            f"baseline passed ({len(succeeded)} rep(s)) but {field} was never archived "
            f"for this epoch — a gap in the instrument, not a result",
        )
    if len(values) == 1:
        return Denominator(float(values[0]), 1, "DEGRADED: one sample, inherits its noise")
    return Denominator(float(statistics.median(values)), len(values), "")


def report(results_dir: Path) -> str:
    cells = load_cells(results_dir)
    if not cells:
        return f"no cells under {results_dir}\n"
    tasks = sorted({c.task for c in cells})
    lines: List[str] = []
    w = lines.append

    w(f"# Cost relative to baseline — {results_dir.name}\n")
    w("Denominator is the median of this epoch's SUCCESSFUL baseline repetitions for the")
    w("same task. Absolutes are carried as context; the ratio is the headline.\n")

    for task in tasks:
        t_den = baseline_median(cells, task, "minutes")
        k_den = baseline_median(cells, task, "tokens")
        w(f"\n## `{task}`\n")
        w(f"baseline time: {t_den.value:.1f} min over {t_den.samples} rep(s)"
          if t_den.usable else f"baseline time: {t_den.note}")
        if t_den.note and t_den.usable:
            w(f"  ⚠ {t_den.note}")
        w(f"baseline tokens: {k_den.value:,.0f} over {k_den.samples} rep(s)"
          if k_den.usable else f"baseline tokens: {k_den.note}")
        if k_den.note and k_den.usable:
            w(f"  ⚠ {k_den.note}")
        w("")
        w("| arm | outcome | time | × baseline | tokens | × baseline |")
        w("|---|---|---:|---:|---:|---:|")
        for arm in ARMS:
            for c in sorted((x for x in cells if x.arm == arm and x.task == task),
                            key=lambda x: x.rep):
                outcome = "TIMEOUT" if c.timed_out else ("pass" if c.passed else "fail")
                label = arm + (f" r{c.rep}" if c.rep > 1 else "")
                t_ratio = _ratio(c.minutes, t_den, MIN_MEANINGFUL_MINUTES)
                k_ratio = (_ratio(c.tokens, k_den, MIN_MEANINGFUL_TOKENS)
                           if c.tokens is not None else "—")
                tok = f"{c.tokens:,}" if c.tokens is not None else "—"
                w(f"| {label} | {outcome} | {c.minutes:.1f}m | {t_ratio} | {tok} | {k_ratio} |")
    w("")
    return "\n".join(lines)


def _ratio(value: Optional[float], den: Denominator, floor: float) -> str:
    """A ratio, or the reason there isn't one."""
    if value is None or not den.usable:
        return "—"
    if den.value is not None and den.value < floor:
        return "n/a (baseline below the floor)"
    return f"{value / den.value:.1f}×"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("results_dir", type=Path)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    text = report(args.results_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
        print(f"{args.out}  ({len(text):,} bytes)")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Check a finished run for the defects this campaign has already fixed.

    /usr/bin/python3 scripts/check_campaign.py .data/benchmark/watch/<run>

Every harness defect in `docs/build/artifacts/14.2-arm-campaign.md` was found by
opening a cell whose RESULT LOOKED ORDINARY. That is what they have in common and
it is why they were expensive: a scoreboard cannot show you a number that is
wrong in a way the scoreboard does not model.

A unit test stops a fixed defect being reintroduced by an edit. It does not stop
one returning by another road — a different platform, a changed dependency, a
condition nobody modelled. This reads the run's own output and looks for the
SIGNATURE each fixed defect leaves, which is the part a test cannot cover and
prose cannot make checkable.

Exit status is 0 when nothing fires and 1 when anything does. A finding here is
not proof of a regression; it is a cell worth opening.
"""

import glob
import json
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Wall clock is allowed a little over its tier budget: the gauge's own duration
# is added on the non-timeout path, and killing a process group is not instant.
# Anything beyond this means the budget did not bind, which is D17/D19.
BUDGET_TOLERANCE = 1.15

# The banner opencode prints when a session starts. More than one in a single
# cell's transcript means two runs are in that file, which is D09.
SESSION_BANNER = "> build"


class Finding:
    def __init__(self, defect: str, cell: str, detail: str) -> None:
        self.defect = defect
        self.cell = cell
        self.detail = detail

    def __str__(self) -> str:
        return "%-6s %-52s %s" % (self.defect, self.cell, self.detail)


def load_results(run_dir: pathlib.Path) -> List[Dict[str, Any]]:
    rows = []
    for path in sorted(run_dir.glob("*.json")):
        if path.name == "run-manifest.json":
            continue
        try:
            row = json.loads(path.read_text())
        except ValueError:
            continue
        if isinstance(row, dict) and "cellId" in row:
            rows.append(row)
    return rows


def tier_budgets(run_dir: pathlib.Path) -> Dict[str, int]:
    """Per-tier wall clock: the run's own manifest first, the task set after.

    A results directory does not always hold a run manifest, and a check that
    quietly does nothing when it cannot find one is the same silent-skip this
    whole script exists to catch. The caller is told when this comes back empty.
    """
    candidates = [run_dir / "run-manifest.json"]
    candidates.extend(sorted(pathlib.Path("bench").glob("*.json")))
    for manifest in candidates:
        try:
            document = json.loads(manifest.read_text())
        except (OSError, ValueError):
            continue
        for holder in (document, document.get("defaults")):
            if isinstance(holder, dict):
                inner = holder.get("tierTimeoutSec")
                if isinstance(inner, dict) and inner:
                    return {k: int(v) for k, v in inner.items() if isinstance(v, int)}
    return {}


def diagnostics_for(run_dir: pathlib.Path, cell_id: str) -> Dict[str, List[Any]]:
    """A cell's driver trace and ledger slice, empty when it kept none."""
    stem = cell_id.replace("/", "__")
    out: Dict[str, List[Any]] = {"driver": [], "ledger": []}
    for name, suffix in (("driver", "driver.jsonl"), ("ledger", "ledger.jsonl")):
        path = run_dir / "diagnostics" / ("%s.%s" % (stem, suffix))
        try:
            for line in path.read_text().splitlines():
                if line.strip():
                    out[name].append(json.loads(line))
        except (OSError, ValueError):
            continue
    return out


def check_timeout_was_scored(row: Dict[str, Any]) -> Optional[Finding]:
    """D01: a timed-out cell whose tree was never measured.

    The defect discarded a correct solution and recorded it identically to a
    wrecked repository. Its signature is a timeout carrying no gauge verdict.
    """
    gauge = row.get("gauge") or {}
    if row.get("timedOut") and not gauge.get("ran"):
        return Finding("D01", row["cellId"], "timed out and the tree was never measured")
    return None


def check_delivery_and_correctness_are_separate(row: Dict[str, Any]) -> Optional[Finding]:
    """D01: the two axes collapsed back into one.

    `passed` is delivery inside the wall clock; `gauge.passed` is whether the
    work is right. A cell that delivered and passed its gauge, or failed both,
    is ordinary. A `pass` whose gauge FAILED means the scoreboard is reporting
    something the hidden suite disagrees with.
    """
    gauge = row.get("gauge") or {}
    if row.get("passed") and gauge.get("ran") and not gauge.get("passed"):
        return Finding("D01", row["cellId"], "recorded a pass whose hidden suite failed")
    return None


def check_empty_run_excluded(
    row: Dict[str, Any], diagnostics: Dict[str, List[Any]]
) -> Optional[Finding]:
    """D18: a cell that never reached the model, charged to its arm.

    Read from the ledger slice rather than the token total, for the reason D18
    gives: an empty window, an unreadable ledger and a window whose rows carry
    no token fields all report the same `partial`, and only a count of requests
    separates them.
    """
    if not diagnostics["ledger"] and not diagnostics["driver"]:
        return None
    if diagnostics["ledger"]:
        return None
    for event in diagnostics["driver"]:
        if event.get("event") == "fault-check" and event.get("requests") == 0:
            if row.get("outcome") != "harness-error":
                return Finding(
                    "D18",
                    row["cellId"],
                    "made no request and was scored %r rather than harness-error"
                    % row.get("outcome"),
                )
    return None


def check_budget_bound(row: Dict[str, Any], budgets: Dict[str, int]) -> Optional[Finding]:
    """D17/D19: a cell that outlived the budget supposedly enforcing it.

    The pair that revealed this was 86.8 minutes recorded against a 60-minute
    limit the cell never tripped, because the limit counted down on a clock that
    stops while the machine sleeps and the measurement did not.
    """
    budget = budgets.get(row.get("tier") or "")
    if not budget:
        return None
    minutes = row.get("wallClockMs", 0) / 1000.0
    if minutes > budget * BUDGET_TOLERANCE:
        return Finding(
            "D17/D19",
            row["cellId"],
            "ran %.1f min against a %.1f min budget that did not bind"
            % (minutes / 60.0, budget / 60.0),
        )
    return None


def check_harness_faults_are_real(
    row: Dict[str, Any], diagnostics: Dict[str, List[Any]]
) -> Optional[Finding]:
    """D12/D20: an exclusion that should not have happened.

    `harness-error` excludes SYMMETRICALLY, taking the other arms' cells for
    that task with it, so a wrong one discards three observations rather than
    one. Every exclusion is surfaced with its recorded reason so a person can
    agree with it, because the failure mode here is silent and expensive.
    """
    if row.get("outcome") != "harness-error":
        return None
    reason = "no reason recorded"
    for event in diagnostics["driver"]:
        if event.get("event") == "fault-check" and event.get("fault"):
            reason = str(event["fault"])
    return Finding(
        "D12/D20", row["cellId"], "excluded (and so were the other arms): %s" % reason
    )


def check_one_run_per_transcript(run_dir: pathlib.Path) -> List[Finding]:
    """D09: a transcript holding more than one run.

    The archived transcripts are the campaign's primary evidence. A file with
    two session banners in it is two runs spliced, and reading it produces a
    conclusion about neither. This is the defect that nearly recorded a fix as
    having failed.
    """
    findings = []
    for path in sorted((run_dir / "transcripts").glob("*.log")):
        try:
            text = path.read_bytes().decode("utf-8", errors="replace")
        except OSError:
            continue
        banners = text.count(SESSION_BANNER)
        if banners > 1:
            findings.append(
                Finding("D09", path.name, "%d session banners: this is %d runs spliced" % (banners, banners))
            )
    return findings


def check_arms_are_comparable(rows: Sequence[Dict[str, Any]]) -> List[Finding]:
    """Every task carries the same arms, or the comparison is not one.

    Not a defect that has occurred; a property the campaign depends on and that
    nothing else checks. A task missing an arm produces a scoreboard whose rows
    are not comparable, and it looks exactly like a scoreboard whose rows are.

    A run that was stopped, or is still in flight, is missing arms on its LAST
    task for a reason that is not a defect. Reporting that as a finding on every
    incomplete run is how a checker teaches its reader to skip its output — the
    mirror of the silent-skip this script exists to prevent, and just as fatal to
    it. So incompleteness is named as incompleteness, once, and the arm check
    runs over the tasks that finished.
    """
    by_task: Dict[str, set] = {}
    order: List[str] = []
    for row in rows:
        if row["taskId"] not in by_task:
            order.append(row["taskId"])
        by_task.setdefault(row["taskId"], set()).add(row["arm"])
    if not by_task:
        return []
    full = max((arms for arms in by_task.values()), key=len)

    # The task a truncated run stopped inside is the last one to have started.
    last_started: Dict[str, str] = {}
    for row in rows:
        prev = last_started.get(row["taskId"], "")
        if row.get("startedIso", "") > prev:
            last_started[row["taskId"]] = row.get("startedIso", "")
    tail = max(last_started, key=lambda t: last_started[t]) if last_started else None

    findings = []
    for task, arms in sorted(by_task.items()):
        missing = full - arms
        if not missing:
            continue
        if task == tail:
            findings.append(
                Finding(
                    "PARTIAL",
                    task,
                    "run ended inside this task (missing %s) — incomplete, not a defect"
                    % ", ".join(sorted(missing)),
                )
            )
        else:
            findings.append(
                Finding("ARMS", task, "missing %s" % ", ".join(sorted(missing)))
            )
    return findings


def run(run_dir: pathlib.Path) -> Tuple[List[Finding], int]:
    rows = load_results(run_dir)
    budgets = tier_budgets(run_dir)
    findings: List[Finding] = []
    for row in rows:
        diagnostics = diagnostics_for(run_dir, row["cellId"])
        for finding in (
            check_timeout_was_scored(row),
            check_delivery_and_correctness_are_separate(row),
            check_empty_run_excluded(row, diagnostics),
            check_budget_bound(row, budgets),
            check_harness_faults_are_real(row, diagnostics),
        ):
            if finding is not None:
                findings.append(finding)
    findings.extend(check_one_run_per_transcript(run_dir))
    findings.extend(check_arms_are_comparable(rows))
    return findings, len(rows)


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: check_campaign.py <results dir>\n")
        return 2
    run_dir = pathlib.Path(argv[1])
    if not run_dir.is_dir():
        sys.stderr.write("not a directory: %s\n" % run_dir)
        return 2

    findings, cells = run(run_dir)
    print("checked %d cell(s) in %s" % (cells, run_dir))
    if not tier_budgets(run_dir):
        print("  NOTE  no tier budgets found: the check that a budget actually bound")
        print("        cannot run, so a cell outliving its limit would pass unseen.")
    if not (run_dir / "diagnostics").is_dir():
        print("  NOTE  no diagnostics/ directory: the checks that read the driver's own")
        print("        trace and the router ledger slice cannot run on this run.")
    if not findings:
        print("no known defect signature fired.")
        return 0
    print("")
    for finding in findings:
        print(finding)
    print("")
    print("%d signature(s) fired. Each names a cell worth opening; none is proof." % len(findings))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

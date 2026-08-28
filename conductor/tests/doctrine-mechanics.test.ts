// conductor/tests/doctrine-mechanics.test.ts — Phase I.4 stage B: the two
// implementer-facing doctrine riders, GAP-005 and GAP-039.
//
// GAP-005 (single-source doctrine composition). Doctrine lived in TWO unguarded
// spellings: the anchor-tested `.md` packs, and hand-written restatements inside
// adapter/tools.ts dispatch prompts (ISSUE-003 named five sites). Nothing guarded
// either direction, so an edit to a pack changed nothing a session read and an
// edit to a prompt changed doctrine nobody reviewed. Two halves close it:
//   (a) every dispatch prompt COMPOSES its doctrine slice out of the loaded pack
//       map — the debugFixPrompt pattern — so the rules exist in exactly one
//       place and an operator's doctrine override reaches the prompt;
//   (b) each pack carries a GENERATED mechanics section derived from the tool
//       vocabulary itself (core/tool-bindings.ts) and the legality machine
//       (core/gates-phase.ts), so pack mechanics cannot drift from the machine.
//
// GAP-039 (tdd.md's headline cycle ended in an action the git gate ALWAYS
// denies). A doctrine-following implementer walked into a guaranteed deny at the
// end of every green. The cycle must end in an action the gates allow, and the
// pack must say so in a sentence anchored here (ISSUE-135's fix form: anchor the
// full sentence, not a keyword).
//
// Anti-vacuity: 1B re-derives the tool sequences INDEPENDENTLY (walking
// legalTools in this file) rather than comparing renderMechanics to itself, and
// 3E pins the git-gate denial that makes GAP-039 a defect at all — so a pack that
// merely says "never run git commit" is checked against the machine that denies
// it, not against a belief about the machine.
//
// Runtime hygiene: node:test + node:assert/strict; erasable TS; pack reads go
// through new URL("../doctrine/…", import.meta.url); no skip/todo.

import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import * as path from "node:path";
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  MECHANICS_BEGIN,
  MECHANICS_END,
  extractMechanics,
  itemStageTools,
  mechanicsBlock,
  metaTools,
  nonBehavioralEntryTool,
  packSection,
  renderMechanics,
  runStageTools,
} from "../core/mechanics.ts";
import { legalTools } from "../core/gates-phase.ts";
import {
  ITEM_MAX_FILES,
  PLAN_PLACEHOLDER_LABELS,
  acceptanceClusters,
  scanPlaceholders,
} from "../core/planning.ts";
import type { GateItem, GateRun } from "../core/gates-phase.ts";
import { TOOL_BINDINGS } from "../core/tool-bindings.ts";
import { VOCABULARIES } from "../core/vocab-registry.ts";
import { ITEM_STATES } from "../core/fsm-item.ts";
import { decideGit } from "../core/gates-git.ts";
import {
  ACCEPTANCE_SUBJECT_EXAMPLE,
  classifierPrompt,
  decomposePrompt,
  scopableFiles,
  scopableSource,
  itemLensPrompt,
  itemSkepticPrompt,
  lensPrompt,
  planPrompt,
  skepticRefutePrompt,
} from "../adapter/tools.ts";
import type { Config, Queue, QueueItem, Findings } from "../core/types.ts";

// ---------------------------------------------------------------------------
// Pack fixtures — the real doctrine directory, read relative to THIS file.
// ---------------------------------------------------------------------------

const PACKS: readonly string[] = [
  "core.md",
  "decompose.md",
  "plan.md",
  "tdd.md",
  "test-vet.md",
  "debug.md",
  "review.md",
  "skeptic.md",
  "receive-review.md",
];

function readPack(name: string): string {
  return readFileSync(new URL(`../doctrine/${name}`, import.meta.url), "utf8");
}

// The whole doctrine directory as the composition root hands it to the handlers.
function packMap(): Record<string, string> {
  const map: Record<string, string> = {};
  for (const name of PACKS) map[name] = readPack(name);
  return map;
}

// Collapse every run of whitespace (newlines included) to one space, so an anchor
// sentence still matches across the line wrapping a markdown pack applies to it.
function flat(s: string): string {
  return s.replace(/`/g, "").replace(/\s+/g, " ").trim();
}

// ===========================================================================
// 1. GAP-005 half (b) — the GENERATED mechanics section.
// ===========================================================================

test("I4B-1A: every doctrine pack carries exactly one generated mechanics block equal to a fresh derivation", () => {
  for (const name of PACKS) {
    const text = readPack(name);
    const begins = text.split(MECHANICS_BEGIN).length - 1;
    const ends = text.split(MECHANICS_END).length - 1;
    assert.equal(begins, 1, `${name} must carry exactly one ${MECHANICS_BEGIN} marker`);
    assert.equal(ends, 1, `${name} must carry exactly one ${MECHANICS_END} marker`);

    const embedded = extractMechanics(text);
    assert.notEqual(embedded, null, `${name}'s mechanics block must be extractable`);
    assert.equal(
      embedded,
      renderMechanics(name),
      `${name}'s embedded mechanics section must equal a FRESH derivation from the tool ` +
        "vocabulary — regenerate it rather than editing the pack by hand",
    );
    // The block the generator emits is what the pack carries, markers included.
    assert.ok(
      text.includes(mechanicsBlock(name)),
      `${name} must embed mechanicsBlock(${JSON.stringify(name)}) verbatim, markers included`,
    );
  }
});

test("I4B-1B: the mechanics derivation matches an INDEPENDENT walk of the legality machine", () => {
  const asRun = (state: string, classification: string | null): GateRun => ({
    state,
    stop: null,
    classification: classification === null ? null : { kind: classification },
    classified: classification !== null,
  });
  const asItem = (state: string, behavioral: boolean): GateItem => ({
    id: "I1",
    state,
    behavioral,
    dependsOn: [],
    fileScope: ["src/a.ts"],
    blocked: null,
    deferred: null,
  });
  const recommendation = (
    run: GateRun,
    items: GateItem[],
  ): { tool: string; perItem: boolean } | null => {
    const verdict = legalTools(run, items, [], true, true);
    if (verdict.recommended === null) return null;
    return {
      tool: verdict.recommended.tool,
      perItem: verdict.recommended.args.itemId !== undefined,
    };
  };

  // Run-level: the recommendation at each run FSM position that has one.
  const runWalk: string[] = [];
  const runPositions: Array<[string, string | null]> = [
    ["INTAKE", null],
    ["INTAKE", "work"],
    ["DECOMPOSED", "work"],
    ["PLANNED", "work"],
    ["PLAN_REVIEWED", "work"],
    ["EXECUTING", "work"],
  ];
  for (const [state, kind] of runPositions) {
    const items = state === "EXECUTING" ? [asItem("PUBLISHED", true)] : [];
    const rec = recommendation(asRun(state, kind), items);
    if (rec !== null && !rec.perItem && !runWalk.includes(rec.tool)) runWalk.push(rec.tool);
  }
  assert.deepEqual(
    runStageTools(),
    runWalk,
    "runStageTools() must equal the run-level recommendations legalTools actually produces",
  );
  assert.ok(runWalk.length >= 6, "the run-stage walk must find every run stage, not a truncated prefix");

  // Item-level: the recommendation for a lone behavioral item at each item state.
  const itemWalk: string[] = [];
  for (const state of ITEM_STATES) {
    const rec = recommendation(asRun("EXECUTING", "work"), [asItem(state, true)]);
    if (rec !== null && rec.perItem && !itemWalk.includes(rec.tool)) itemWalk.push(rec.tool);
  }
  assert.deepEqual(
    itemStageTools(),
    itemWalk,
    "itemStageTools() must equal the per-item recommendations legalTools actually produces",
  );
  assert.ok(itemWalk.length >= 6, "the item-stage walk must find every item stage, not a truncated prefix");

  // The non-behavioral entry point is derived, not asserted.
  const nonBehavioral = recommendation(asRun("EXECUTING", "work"), [asItem("PENDING", false)]);
  assert.notEqual(nonBehavioral, null, "a non-behavioral PENDING item must have a recommended stage tool");
  assert.equal(
    nonBehavioralEntryTool(),
    nonBehavioral === null ? "" : nonBehavioral.tool,
    "nonBehavioralEntryTool() must equal what legalTools recommends for a non-behavioral PENDING item",
  );

  // Meta tools: the bound vocabulary minus the stage tools, and nothing invented.
  const bound = Object.keys(TOOL_BINDINGS).filter((name) => TOOL_BINDINGS[name] !== null);
  const stage = new Set([...runWalk, ...itemWalk]);
  const expectedMeta = bound.filter((name) => !stage.has(name)).sort();
  assert.deepEqual(
    metaTools(),
    expectedMeta,
    "metaTools() must be the bound TOOL_BINDINGS vocabulary minus the stage tools",
  );
});

test("I4B-1D: the mechanics derivation's legalTools call is pinned to the two NAMED description constants", () => {
  const source = readFileSync(new URL("../core/mechanics.ts", import.meta.url), "utf8");
  // The C-048 guard (tests/legaltools-callsites.test.ts) forbids a shipped VERDICT
  // that hardcodes publishEnabled. This call site renders a checked-in pack rather
  // than judging a workspace, so it fixes both gate inputs — and that exception is
  // recorded HERE, by name, so it cannot quietly become a bare literal later.
  assert.ok(
    source.includes(
      "legalTools(run, items, [], DESCRIBES_CONFIGURED_REPO, DESCRIBES_FULL_PIPELINE)",
    ),
    "core/mechanics.ts must pass the two NAMED description constants to legalTools, so the " +
      "reason this call site fixes them is readable at the call rather than assumed",
  );
  for (const name of ["DESCRIBES_CONFIGURED_REPO", "DESCRIBES_FULL_PIPELINE"]) {
    assert.ok(
      source.includes(`const ${name} = true;`),
      `core/mechanics.ts must define ${name} = true (the fullest pipeline the FSM defines)`,
    );
  }
});

test("I4B-1C: every conductor_* token a pack's mechanics block names is a bound tool in the closed vocabulary", () => {
  const bound = new Set(Object.keys(TOOL_BINDINGS).filter((name) => TOOL_BINDINGS[name] !== null));
  let namedTotal = 0;
  for (const name of PACKS) {
    const block = extractMechanics(readPack(name));
    assert.notEqual(block, null, `${name} must carry a mechanics block`);
    const named = (block ?? "").match(/conductor_[a-z_]+/g) ?? [];
    assert.ok(named.length > 0, `${name}'s mechanics block must name at least one tool`);
    namedTotal += named.length;
    for (const tool of named) {
      assert.ok(
        bound.has(tool),
        `${name}'s mechanics block names ${tool}, which is not a bound tool in TOOL_BINDINGS`,
      );
    }
  }
  assert.ok(namedTotal >= 9, "the packs' mechanics blocks together must name the tool vocabulary, not one token");
});

// ---------------------------------------------------------------------------
// 1E/1F — WHICH stage tools dispatch a sub-session, and as WHAT role.
//
// The generated section already ordered the stages; it never said that most of
// them hand their work to a sub-session. A live run read conductor_submit_test as
// a verification step, concluded it had to author the failing test itself, and
// spent 26 minutes deadlocked against the edit and git gates. The stage order is
// derived and cannot drift; the dispatch shape must be derived on the same terms.
//
// 1E pins the DECLARATION against the machine that performs it — an independent
// scan of adapter/tools.ts for the fan-out roles each handler reaches, transitively
// through the per-stage helpers. 1F pins that the derivation reaches the packs.
// ---------------------------------------------------------------------------

// The §4.1 role pin, read from the vocabulary registry rather than restated: a
// dispatch declaration naming a role no fan-out map carries dispatches nowhere.
const DISPATCHABLE_ROLES: readonly string[] = (
  VOCABULARIES.find((entry) => entry.name === "roles")?.members ?? []
).filter((role) => role !== "orchestrator");

// Every top-level function in adapter/tools.ts, sliced from its own `function`
// line to the next one. Slicing beats brace counting: braces inside template
// literals and regexes are everywhere in that file, and a mis-counted body would
// silently shrink the set this row reasons over.
function adapterFunctions(): Map<string, string> {
  const source = readFileSync(new URL("../adapter/tools.ts", import.meta.url), "utf8");
  const lines = source.split("\n");
  const starts: Array<{ line: number; name: string }> = [];
  for (let i = 0; i < lines.length; i += 1) {
    const match = /^(?:export )?(?:async )?function (\w+)/.exec(lines[i]);
    if (match !== null) starts.push({ line: i, name: match[1] });
  }
  const bodies = new Map<string, string>();
  for (let k = 0; k < starts.length; k += 1) {
    const end = k + 1 < starts.length ? starts[k + 1].line : lines.length;
    bodies.set(starts[k].name, lines.slice(starts[k].line, end).join("\n"));
  }
  return bodies;
}

// The roles a function names in a fan-out JOB, closed under the helpers it calls.
// A role literal on an `askedBy` line is the identity of whoever ASKED a question,
// not a session being dispatched, so those lines are excluded.
function rolesReachedBy(bodies: Map<string, string>): Map<string, Set<string>> {
  const direct = new Map<string, Set<string>>();
  const callees = new Map<string, Set<string>>();
  const roleLiteral = new RegExp(`"(${DISPATCHABLE_ROLES.join("|")})"`, "g");
  for (const [name, body] of bodies) {
    const roles = new Set<string>();
    for (const line of body.split("\n")) {
      if (line.includes("askedBy")) continue;
      for (const match of line.matchAll(roleLiteral)) roles.add(match[1]);
    }
    direct.set(name, roles);
    const called = new Set<string>();
    for (const other of bodies.keys()) {
      if (other !== name && new RegExp(`\\b${other}\\s*\\(`).test(body)) called.add(other);
    }
    callees.set(name, called);
  }
  const reached = new Map<string, Set<string>>();
  const walk = (name: string, seen: Set<string>): Set<string> => {
    if (seen.has(name)) return new Set<string>();
    seen.add(name);
    const out = new Set<string>(direct.get(name) ?? []);
    for (const callee of callees.get(name) ?? []) {
      for (const role of walk(callee, seen)) out.add(role);
    }
    return out;
  };
  for (const name of bodies.keys()) reached.set(name, walk(name, new Set<string>()));
  return reached;
}

test("I4B-1E: every bound tool DECLARES the sub-session roles its handler dispatches, and the declaration equals an independent scan of adapter/tools.ts", () => {
  assert.ok(
    DISPATCHABLE_ROLES.length >= 6,
    "premise: the §4.1 role pin names the fan-out roles this row scans for",
  );
  const bodies = adapterFunctions();
  assert.ok(
    bodies.size >= 100,
    `parsed only ${bodies.size} top-level functions out of adapter/tools.ts — the parse is broken, ` +
      "and a broken scan must be RED rather than a vacuous green",
  );
  const reached = rolesReachedBy(bodies);

  // The scan DISCRIMINATES: two committed handlers dispatch nothing, so a scan
  // that swept every handler into the set would prove nothing.
  for (const quiet of ["handlePublish", "handleReport"]) {
    assert.ok(bodies.has(quiet), `premise: ${quiet} is a committed handler`);
    assert.deepEqual(
      [...(reached.get(quiet) ?? [])],
      [],
      `${quiet} builds no fan-out job, so the scan must claim no role for it`,
    );
  }

  let declaredTotal = 0;
  for (const [tool, binding] of Object.entries(TOOL_BINDINGS)) {
    if (binding === null) continue;
    const declared = binding.dispatches;
    assert.ok(
      Array.isArray(declared),
      `${tool} must DECLARE its dispatch shape in core/tool-bindings.ts — an undeclared stage tool ` +
        "reads as a verification step the caller must satisfy itself",
    );
    for (const role of declared) {
      assert.ok(
        DISPATCHABLE_ROLES.includes(role),
        `${tool} declares role ${JSON.stringify(role)}, which is not a §4.1 role the fan-out engine dispatches`,
      );
    }
    assert.equal(
      new Set(declared).size,
      declared.length,
      `${tool}'s dispatch declaration must name each role once`,
    );
    declaredTotal += declared.length;
    const scanned = reached.get(binding.handler);
    assert.notEqual(scanned, undefined, `${tool} binds handler ${binding.handler}, which the parse did not find`);
    assert.deepEqual(
      [...declared].sort(),
      [...(scanned ?? [])].sort(),
      `${tool}'s declared dispatch roles must equal the roles ${binding.handler} actually reaches in ` +
        "adapter/tools.ts — a declaration nobody checks is the hand-written list this derivation removes",
    );
  }
  assert.ok(
    declaredTotal >= 12,
    `only ${declaredTotal} role declarations across the whole table — the pipeline dispatches more than that`,
  );
});

const RUN_STAGE_PREFIX = "Run stages, in FSM order: ";
const ITEM_STAGE_PREFIX = "Item stages, in FSM order: ";
// The one sentence that TEACHES the parenthetical. Without it the roles read as
// decoration; with it they read as "the call is how this gets authored".
const DISPATCH_LEGEND = "parenthesised roles are the sub-sessions it dispatches";

function stageLine(block: string, prefix: string): string | null {
  return block.split("\n").find((line) => line.startsWith(prefix)) ?? null;
}

test("I4B-1F: the generated stage lines name the roles each stage dispatches, and every pack carrying one carries the legend", () => {
  const rolesOf = (tool: string): readonly string[] => TOOL_BINDINGS[tool]?.dispatches ?? [];
  const rows: ReadonlyArray<{ prefix: string; tools: readonly string[] }> = [
    { prefix: RUN_STAGE_PREFIX, tools: runStageTools() },
    { prefix: ITEM_STAGE_PREFIX, tools: itemStageTools() },
  ];
  for (const row of rows) {
    const dispatching = row.tools.filter((tool) => rolesOf(tool).length > 0);
    const quiet = row.tools.filter((tool) => rolesOf(tool).length === 0);
    assert.ok(dispatching.length >= 4, `premise: most ${row.prefix.trim()} stages dispatch`);
    assert.ok(quiet.length >= 1, `premise: at least one stage does its work in the harness, or the annotation discriminates nothing`);
  }

  let annotatedPacks = 0;
  for (const name of PACKS) {
    const block = extractMechanics(readPack(name)) ?? "";
    let carriesAStageLine = false;
    for (const row of rows) {
      const line = stageLine(block, row.prefix);
      if (line === null) continue;
      carriesAStageLine = true;
      for (const tool of row.tools) {
        const roles = rolesOf(tool);
        if (roles.length === 0) {
          assert.ok(
            !line.includes(tool + " ("),
            `${name}: ${tool} dispatches nothing, so it must stand bare in "${row.prefix.trim()}"`,
          );
          continue;
        }
        assert.ok(
          line.includes(tool + " (" + roles.join(", ") + ")"),
          `${name}'s "${row.prefix.trim()}" line must name the roles ${tool} dispatches ` +
            `(${roles.join(", ")}), so a reader of the stage order learns the call is how that work ` +
            `gets authored rather than a step it must satisfy first; the line reads: ${line}`,
        );
      }
    }
    if (!carriesAStageLine) continue;
    annotatedPacks += 1;
    assert.ok(
      block.includes(DISPATCH_LEGEND),
      `${name} carries a stage line, so its mechanics block must explain the parenthetical ` +
        `(${JSON.stringify(DISPATCH_LEGEND)}) — bare role names beside a tool teach nothing`,
    );
  }
  assert.equal(annotatedPacks, PACKS.length, "every pack carries at least one stage line");
});

// ===========================================================================
// 2. GAP-005 half (a) — dispatch prompts DERIVE their doctrine from the packs.
// ===========================================================================

// A minimal §2.2 config the prompt builders read (behavioral paths, the trivial
// file cap, the ponytail intensity). Only the fields the prompts consume matter.
function testConfig(): Config {
  return {
    verify: {
      scopes: {},
      behavioralPaths: ["src/**"],
    },
    workflow: { trivialMaxFiles: 3 },
    ponytail: "standard",
  } as unknown as Config;
}

function testQueueItem(): QueueItem {
  return {
    id: "I1",
    title: "an item",
    rationale: "because",
    fileScope: ["src/a.ts"],
    testScope: ["tests/a.test.ts"],
    acceptance: ["it does the thing"],
    behavioral: true,
    dependsOn: [],
    ponytail: { ladderRung: "minimal-code", necessary: "n", reuse: "r" },
  } as unknown as QueueItem;
}

function testQueue(): Queue {
  return { items: [testQueueItem()] } as unknown as Queue;
}

function testFinding(): Findings["findings"][number] {
  return {
    id: "F1",
    severity: "major",
    lens: "correctness",
    claim: "the thing is wrong",
    evidence: "src/a.ts:1",
    suggestedFix: "fix the thing",
  } as unknown as Findings["findings"][number];
}

// Each row: the prompt under test, the pack it must compose FROM, and one heading
// whose text must arrive VERBATIM (so the rules exist in the pack and nowhere else).
const DERIVATION_ROWS: ReadonlyArray<{
  label: string;
  pack: string;
  heading: string;
  build: (packs: Record<string, string>) => string;
}> = [
  {
    label: "decomposePrompt",
    pack: "decompose.md",
    heading: "Rejection checklist (self-check before you return)",
    build: (packs) => decomposePrompt("do the work", testConfig(), packs),
  },
  {
    label: "planPrompt",
    pack: "plan.md",
    heading: "Self-check before returning",
    build: (packs) => planPrompt("do the work", testQueue(), testConfig(), packs),
  },
  {
    label: "lensPrompt",
    pack: "review.md",
    heading: "An empty review is the approval",
    build: (packs) =>
      lensPrompt(
        { id: "correctness", charge: "correctness of the plan" },
        "do the work",
        "# plan",
        testQueue(),
        packs,
      ),
  },
  {
    label: "skepticRefutePrompt",
    pack: "skeptic.md",
    heading: "Refutation carries evidence; abstention upholds",
    build: (packs) =>
      skepticRefutePrompt(testFinding(), "correctness", 3, "do the work", "# plan", testQueue(), packs),
  },
  {
    label: "itemLensPrompt",
    pack: "review.md",
    heading: "An empty review is the approval",
    build: (packs) => itemLensPrompt(["correctness"], testQueueItem(), "\ndiff\n", "test text", 2, packs, "RW-nonce"),
  },
  {
    label: "itemSkepticPrompt",
    pack: "skeptic.md",
    heading: "Refutation carries evidence; abstention upholds",
    build: (packs) =>
      itemSkepticPrompt(
        { finding: testFinding(), lens: "correctness", sessionID: "s1", key: "s1:F1" },
        3,
        testQueueItem(),
        "\ndiff\n",
        "test text",
        packs,
      ),
  },
];

test("I4B-2A: every dispatch prompt carries its doctrine slice VERBATIM out of the pack map", () => {
  const packs = packMap();
  for (const row of DERIVATION_ROWS) {
    const slice = packSection(packs[row.pack] ?? "", row.heading) ?? "";
    assert.ok(
      slice.length > 80,
      `${row.pack} must carry the section "${row.heading}" the ${row.label} composition reads, ` +
        "with real doctrine in it",
    );
    const prompt = row.build(packs);
    assert.ok(
      prompt.includes(slice),
      `${row.label} must carry ${row.pack}'s "${row.heading}" section VERBATIM (composed from the pack ` +
        "map, never re-spelled in the prompt literal)",
    );
  }
});

test("I4B-2B: an edited pack changes what the dispatch prompt says (the override is not theater)", () => {
  const packs = packMap();
  const marker = "OPERATOR OVERRIDE SENTINEL 4711";
  for (const row of DERIVATION_ROWS) {
    const original = packs[row.pack] ?? "";
    const edited = original.replace("## " + row.heading, "## " + row.heading + "\n\n" + marker);
    assert.notEqual(edited, original, `the ${row.pack} edit fixture must actually change the pack`);
    const prompt = row.build({ ...packs, [row.pack]: edited });
    assert.ok(
      prompt.includes(marker),
      `${row.label} must reflect an edit to ${row.pack} — otherwise the doctrine directory it reads is theater`,
    );
  }
});

test("I4B-2C: a dispatch prompt whose pack is missing REFUSES, naming the pack", () => {
  const packs = packMap();
  for (const row of DERIVATION_ROWS) {
    const without: Record<string, string> = { ...packs };
    delete without[row.pack];
    assert.throws(
      () => row.build(without),
      (err: unknown) => {
        const message = err instanceof Error ? err.message : String(err);
        assert.ok(
          message.includes(row.pack),
          `${row.label}'s refusal must NAME the absent pack (${row.pack}); got: ${message}`,
        );
        return true;
      },
      `${row.label} must refuse to dispatch without the doctrine that governs it`,
    );
  }
});

// ---------------------------------------------------------------------------
// I4B-2G: the number the dispatch STATES is the number the gate ENFORCES.
//
// GAP-005 removes the re-spelled RULES from a prompt; the numbers the rules are
// parameterised by are still composed here, and a number is as re-spellable as a
// sentence. decomposePrompt's "as this workspace is configured" line reaches the
// planner in the same window as decompose.md's generated mechanics block, which
// derives its file cap from ITEM_MAX_FILES — the constant validateQueue's item-size
// row actually applies. Sourcing that line from config.workflow.trivialMaxFiles
// states a DIFFERENT number with a different job (the §2.10 ceiling on how big a
// request may be and still skip planning), so the two spellings contradict each
// other in one dispatch and a planner obeying the prompt over-splits every item.
//
// The fixture pins trivialMaxFiles AWAY from ITEM_MAX_FILES and reads both numbers,
// so neither a coincidence nor a later edit to either constant can make this pass.
// ---------------------------------------------------------------------------

const STATED_FILE_CAP = /the per-item file cap: (\d+) files/;

test("I4B-2G: decomposePrompt states the per-item file cap validateQueue enforces, not the §2.10 trivial ceiling", () => {
  const base = testConfig();
  const trivialCeiling = ITEM_MAX_FILES + 1;
  const config = {
    ...base,
    workflow: { ...base.workflow, trivialMaxFiles: trivialCeiling },
  } as unknown as Config;
  assert.notEqual(
    trivialCeiling,
    ITEM_MAX_FILES,
    "fixture: the trivial ceiling must differ from the enforced cap, or the row cannot tell them apart",
  );

  const prompt = decomposePrompt("do the work", config, packMap());
  const stated = STATED_FILE_CAP.exec(prompt);
  assert.ok(
    stated !== null,
    "decomposePrompt must state the per-item file cap in a shape this row can read; it says: " +
      prompt.slice(prompt.indexOf("As this workspace is configured"), prompt.indexOf("REQUEST:")),
  );
  assert.equal(
    Number(stated[1]),
    ITEM_MAX_FILES,
    "the cap the planner is told is the cap validateQueue's item-size row applies (ITEM_MAX_FILES)",
  );
  assert.notEqual(
    Number(stated[1]),
    trivialCeiling,
    "and it is NOT config.workflow.trivialMaxFiles — that ceiling bounds what may skip planning, " +
      "not how large a planned item may be",
  );
});

// The two fail-closed arms of doctrineSlice answer two DIFFERENT questions — "is
// the pack there at all?" and "does that pack still carry the section this
// dispatch composes from?" — and an operator reads the refusal to know which file
// to repair and how. I4B-2C alone cannot tell them apart: both refusals name the
// pack, so folding the pack check into the section check (a `?? ""` default and a
// dead first arm) leaves it green while every absent-pack dispatch starts
// reporting a missing HEADING in a pack that does not exist. This row pins the two
// message shapes apart, which is what makes each arm separately load-bearing.
const NO_PACK_SHAPE = /the loaded pack set has none/;
const NO_SECTION_SHAPE = /carries no section/;

function refusalMessage(build: () => string): string {
  try {
    build();
  } catch (err) {
    return err instanceof Error ? err.message : String(err);
  }
  return "";
}

test("I4B-2E: the ABSENT-pack refusal and the ABSENT-section refusal are distinguishable shapes", () => {
  const packs = packMap();
  for (const row of DERIVATION_ROWS) {
    // (a) the pack is not in the map at all.
    const without: Record<string, string> = { ...packs };
    delete without[row.pack];
    const absent = refusalMessage(() => row.build(without));
    assert.match(
      absent,
      NO_PACK_SHAPE,
      `${row.label} must refuse an ABSENT ${row.pack} as a missing PACK ("the loaded pack set has ` +
        `none"), so the operator is told the file is gone; got: ${absent}`,
    );
    assert.doesNotMatch(
      absent,
      NO_SECTION_SHAPE,
      `and it must not report a missing SECTION of a pack that is not there — that is the other ` +
        `arm's message, and reading it sends the operator hunting for a heading in a file that ` +
        `does not exist; got: ${absent}`,
    );

    // (b) the pack is present but EMPTY: doctrine that governs nothing is the
    // same failure as doctrine that is absent, and it takes the same arm.
    const blank = refusalMessage(() => row.build({ ...packs, [row.pack]: "   \n\n" }));
    assert.match(
      blank,
      NO_PACK_SHAPE,
      `${row.label} must treat an EMPTY ${row.pack} as no doctrine at all; got: ${blank}`,
    );

    // (c) the pack is real doctrine but no longer carries the section the prompt
    // composes from — a pack edit, not a missing file.
    const renamed = (packs[row.pack] ?? "").replace("## " + row.heading, "## " + row.heading + " (retitled)");
    assert.notEqual(renamed, packs[row.pack], `the ${row.pack} retitle fixture must change the pack`);
    const missingSection = refusalMessage(() => row.build({ ...packs, [row.pack]: renamed }));
    assert.match(
      missingSection,
      NO_SECTION_SHAPE,
      `${row.label} must refuse a PRESENT ${row.pack} whose "${row.heading}" section is gone as a ` +
        `missing SECTION; got: ${missingSection}`,
    );
    assert.ok(
      missingSection.includes(row.heading),
      `and it must name the heading it looked for; got: ${missingSection}`,
    );
    assert.doesNotMatch(
      missingSection,
      NO_PACK_SHAPE,
      `and it must not claim the pack set has no ${row.pack} when it has one; got: ${missingSection}`,
    );
  }
});

// The conductor_plan prompt states the placeholder law by carrying plan.md's
// self-check verbatim. That is only equivalent to the law if the self-check NAMES
// the shapes core/planning.ts actually rejects: a planner told "no step defers its
// content" and then rejected for the token "TBD" was never told the rule it was
// judged by, and the bounded re-prompt burns on a defect the doctrine could have
// prevented.
//
// The check runs the REAL rejector over the doctrine, so there is no second copy of
// the list to drift: a rule added to PLAN_PLACEHOLDERS goes red here until the
// self-check names an example of it.
test("I4B-2F: plan.md's self-check names every placeholder shape core/planning.ts rejects, and the dispatch prompt carries them", () => {
  const selfCheck = packSection(readPack("plan.md"), "Self-check before returning");
  assert.notEqual(selfCheck, null, "plan.md must carry the self-check section the plan prompt composes from");
  const tripped = new Set(scanPlaceholders(selfCheck ?? ""));
  assert.ok(PLAN_PLACEHOLDER_LABELS.length >= 7, "premise: the rejector names several distinct shapes");
  for (const label of PLAN_PLACEHOLDER_LABELS) {
    assert.ok(
      tripped.has(label),
      `plan.md's self-check must name the "${label}" shape by example, so the planner reads the same ` +
        "law the handler judges it by; scanning the section reported: " +
        JSON.stringify([...tripped]),
    );
  }

  // And the tokens survive the composition into the prompt the planner is sent —
  // the section can name them and the prompt still lose them if the slice moves.
  const prompt = planPrompt("do the work", testQueue(), testConfig(), packMap());
  for (const token of ["TBD", "add error handling", "similar to task"]) {
    assert.ok(
      prompt.includes(token),
      `the conductor_plan prompt must name the "${token}" defect (plan line 1115 names these three ` +
        "by name); it reaches the prompt only through plan.md's self-check slice",
    );
  }
});

test("I4B-2D: the retired paraphrases are GONE from adapter/tools.ts — one spelling, not two", () => {
  const source = readFileSync(new URL("../adapter/tools.ts", import.meta.url), "utf8");
  const retired: readonly string[] = [
    "dependsOn names other item ids and must form a DAG",
    "an item that writes nothing is not an item",
    "acceptance criteria are observable checks an assertion can run",
    "are plan defects BY ",
    "is a genuine defect that must be fixed before this plan",
    "when you cannot decide, the verdict is REFUTED",
    "comes FIRST and must FAIL before any implementation",
    "smaller robustness issue",
  ];
  for (const phrase of retired) {
    assert.ok(
      !source.includes(phrase),
      `adapter/tools.ts still hand-spells doctrine: ${JSON.stringify(phrase)} — compose it from the pack map`,
    );
  }
});

// ===========================================================================
// 3. GAP-039 — tdd.md's cycle must end in an action the gates ALLOW.
// ===========================================================================

test("I4B-3A: the git gate denies `git commit` for a model session (the fact GAP-039 rests on)", () => {
  for (const mode of ["read-only", "commit", "commit-and-push"] as const) {
    const decision = decideGit('git commit -m "wip"', "implementer", mode, true, "pin");
    assert.equal(
      decision.action,
      "deny",
      `git commit must be DENIED in git mode ${mode} — doctrine may not teach a step the gate refuses`,
    );
  }
});

test("I4B-3B: tdd.md's headline cycle ends in handing back, not in a git write", () => {
  const tdd = readPack("tdd.md");
  const headings = tdd.split("\n").filter((line) => line.startsWith("## "));
  const cycle = headings.find((line) => line.toLowerCase().includes("the cycle"));
  assert.notEqual(cycle, undefined, "tdd.md must carry a headline cycle heading");
  assert.ok(
    !/commit/i.test(cycle ?? ""),
    `tdd.md's cycle heading must not end in commit (the git gate denies it); found ${JSON.stringify(cycle)}`,
  );
  assert.ok(
    /hand back/i.test(cycle ?? ""),
    `tdd.md's cycle must end in handing back; found ${JSON.stringify(cycle)}`,
  );
});

test("I4B-3C: tdd.md anchors the full sentence that names the legal path (ISSUE-135's fix form)", () => {
  const tdd = flat(readPack("tdd.md"));
  assert.ok(
    tdd.includes(
      flat("conductor_publish commits; you never run git commit — a self-publish is denied by design"),
    ),
    "tdd.md must anchor the FULL sentence 'conductor_publish commits; you never run git commit — a " +
      "self-publish is denied by design' (a keyword anchor is what ISSUE-135 says is not enough)",
  );
  assert.ok(
    tdd.includes(flat("conductor_mark_green")),
    "tdd.md must name conductor_mark_green — the legal action the implementer's cycle ends in",
  );
});

test("I4B-3D: the only git invocation tdd.md names is the one it forbids", () => {
  const tdd = readPack("tdd.md");
  const invocations = flat(tdd).match(/git [a-z][a-z-]*/g) ?? [];
  assert.ok(invocations.length > 0, "tdd.md must still name the git write it forbids");
  for (const invocation of invocations) {
    assert.ok(
      flat(tdd).includes(`you never run ${invocation}`),
      `tdd.md names "${invocation}" outside the sentence that forbids it — a doctrine step the gate denies`,
    );
  }
});

// ===========================================================================
// 4. Pack size discipline — the packs ride in a 32k context.
// ===========================================================================

// ~2.6k tokens at the conservative 4-bytes-per-token rule is ~10.4kB; this ceiling
// is deliberately tighter, because a role can receive TWO packs plus the live
// state block plus its payload in the same window. ~1.75k tokens per pack leaves
// room for that, and the ceiling exists to make prose that earns nothing visible:
// a pack pushing against it is a pack to cut, not a ceiling to raise.
const MAX_PACK_BYTES = 7000;

test("I4B-4: every doctrine pack stays lean enough for a 32k context", () => {
  for (const name of PACKS) {
    const bytes = Buffer.byteLength(readPack(name), "utf8");
    assert.ok(
      bytes <= MAX_PACK_BYTES,
      `${name} is ${bytes} bytes — over the ${MAX_PACK_BYTES}-byte pack budget; the packs ride in a ` +
        "32k context alongside the state block and the payload",
    );
  }
});

// ===========================================================================
// [D34] The decompose brief names the files a decomposition may scope.
//
// The planner is asked for items whose fileScope names real files — the
// checklist forbids a wildcard-headed entry and counts a scope as the files it
// matches — and its brief carries the request, the caps and the reply schema.
// Nothing in it says which files exist, so the planner goes and looks. Measured
// across four conductor cells of the 14.2 campaign, 75-80% of a sub-session's
// turns were read/glob/grep, at one to five minutes a turn:
//
//   planner      14 turns, 11 discovery  (79%)
//   skeptic       5 turns,  4 discovery  (80%)
//   mechanical    4 turns,  3 discovery  (75%)
//
// The listing is bounded to the globs that own verification, because a path no
// valid answer could contain is noise, and to a cap, because an unbounded listing
// trades the planner's turns for the context budget.
// ===========================================================================

test("[D34] the decompose brief lists the scopable files, bounded and honest about truncation", () => {
  const root = mkdtempSync(path.join(tmpdir(), "d34-"));
  for (const rel of [
    "src/cli.py",
    "src/registry.py",
    "src/solvers/p001.py",
    "tests/check_visible.py",
    "README.md",
  ]) {
    mkdirSync(path.join(root, path.dirname(rel)), { recursive: true });
    writeFileSync(path.join(root, rel), "x");
  }

  const config = testConfig();
  const files = scopableFiles(root, config);

  // Only the paths a behavioral item could legally scope.
  assert.deepEqual(
    files,
    ["src/cli.py", "src/registry.py", "src/solvers/p001.py"],
    "the listing is the files behavioralPaths owns — not the repo, and not nothing",
  );

  const brief = decomposePrompt("do the work", config, packMap(), files);
  for (const rel of files) {
    assert.ok(brief.includes(rel), `the brief must name ${rel}, or the planner goes looking`);
  }
  assert.ok(
    !brief.includes("README.md"),
    "a path no valid fileScope could contain is noise in a brief that costs context",
  );

  // Truncation is stated, never silent: a planner that believes a partial list is
  // complete will name nothing outside it, which is worse than being told to glob.
  const many = Array.from({ length: 200 }, (_, i) => `src/f${String(i).padStart(3, "0")}.py`);
  const truncated = decomposePrompt("do the work", config, packMap(), many);
  assert.match(truncated, /truncated/, "a capped listing says so:\n" + truncated.slice(-400));
  assert.match(truncated, /\d+ of 200/, "and says how much of it is shown");

  // Absent configuration degrades to silence rather than to a lie.
  assert.equal(scopableFiles(root, { ...config, verify: { ...config.verify, behavioralPaths: [] } } as never).length, 0);
  assert.ok(
    !decomposePrompt("do the work", config, packMap(), []).includes("The files those globs own"),
    "no listing means no section, not an empty one",
  );

  rmSync(root, { recursive: true, force: true });
});

// ===========================================================================
// [D36] The decompose brief carries the source, not just the paths.
//
// D34 gave the planner the PATHS and measured no change: 11 discovery turns
// before, 11 after, on two tasks, 79% both times. The reads were never about
// which files exist. They are the planner reading the code, which it must do to
// decompose it.
//
// D35 priced that: conductor reads track (sub-sessions dispatched) x (repository
// size), measured 29 against a predicted 30 on one cell and 48 against 56 on
// another, versus baseline's single pass. Four to five of every six or seven
// dispatches are the planner, re-dispatched by a watchdog that killed it for
// being slow — and a fresh planner must read everything again.
//
// The arithmetic says carry the code: the planner's packs and brief run ~4,000
// tokens of a 49,152-token window, and the source of every task in the ladder is
// 37 to 401 tokens.
// ===========================================================================

test("[D36] the brief carries file contents where they fit, and falls back to paths where they do not", () => {
  const root = mkdtempSync(path.join(tmpdir(), "d36-"));
  const write = (rel: string, body: string): void => {
    mkdirSync(path.join(root, path.dirname(rel)), { recursive: true });
    writeFileSync(path.join(root, rel), body);
  };
  write("src/cli.py", "def main(argv):\n    return 0\n");
  write("src/registry.py", "_SOLVERS = {}\n");
  write("README.md", "# not scopable\n");

  const config = testConfig();
  const files = scopableFiles(root, config);
  const source = scopableSource(root, files);

  assert.equal(source.length, files.length, "a small repo is carried whole");
  const brief = decomposePrompt("do the work", config, packMap(), files, source);

  // The code itself, not a promise of it.
  assert.match(brief, /def main\(argv\)/, "the brief carries the source it names:\n" + brief.slice(-600));
  assert.match(brief, /_SOLVERS = \{\}/, "every scopable file, not the first one");
  assert.ok(!brief.includes("not scopable"), "and nothing behavioralPaths does not own");
  assert.match(
    brief,
    /rather than reading them again/,
    "the brief says why it is there — a planner that does not know the code is complete reads it anyway",
  );

  // Over budget, it degrades to D34's listing rather than to a truncated file. A
  // half-read source is worse than a named path: the planner cannot tell which
  // half it has.
  const big = path.join(root, "src", "big.py");
  writeFileSync(big, "x".repeat(30000));
  const bigFiles = scopableFiles(root, config);
  const bigSource = scopableSource(root, bigFiles);
  assert.equal(bigSource.length, 0, "over the cap, no source is carried at all");
  const bigBrief = decomposePrompt("do the work", config, packMap(), bigFiles, bigSource);
  assert.ok(!bigBrief.includes("x".repeat(200)), "no file is inlined in part");
  assert.match(bigBrief, /read the ones you need/, "and the planner is told to read instead");
  for (const rel of bigFiles) {
    assert.ok(bigBrief.includes(rel), `the path is still named: ${rel}`);
  }

  rmSync(root, { recursive: true, force: true });
});

// ---------------------------------------------------------------------------
// D45: the role judged by the one-cluster budget is shown the rule, and the
// example it is shown actually satisfies the gate.
//
// ROLE_PACKS gives the planner decompose.md, whose "Measured limits" section
// carries the subject-first form. It gives the `mechanical` role — the
// classifier — core.md alone, which mentions neither clusters nor criterion
// subjects. On the TRIVIAL route the classifier, not the planner, authors
// trivialItem.acceptance, so the one role that rule governs was the one role
// never shown it. Measured on euler-001-py: `escalate-to-work`, three clusters
// (src/solvers/p001.py, register, get), which moves a run from the 16-call route
// to the ~47-call route against a 24-call budget.
//
// The third case is the one that earns its keep. A prompt may state a rule and
// still hand the model an example that the gate would refuse, and nothing about
// the prose would show it. Running the shipped acceptanceClusters over the
// example's own rows pins the advice as ACHIEVABLE, and the foil pins the case
// it must still refuse — without that half the row passes over an example that
// teaches nothing.
// ---------------------------------------------------------------------------

test("D45: classifierPrompt states the one-cluster budget and the subject-first form", () => {
  const prompt = classifierPrompt("add a solver");
  assert.match(prompt, /one acceptance cluster/i, "the classifier is told the budget it is judged by");
  assert.ok(
    prompt.includes(ACCEPTANCE_SUBJECT_EXAMPLE.good[0]),
    "and is shown a criterion that satisfies it",
  );
});

test("D45: decomposePrompt names rephrasing, not only splitting", () => {
  // "split anything bigger" is the wrong remedy for a phrasing fault: an item
  // over budget because two criteria open with bare symbols is not two items.
  const prompt = decomposePrompt("do the work", testConfig(), packMap());
  assert.match(prompt, /one acceptance cluster/i);
  assert.ok(
    prompt.includes(ACCEPTANCE_SUBJECT_EXAMPLE.good[0]),
    "the planner's dispatch shows the shape that passes, not only the cap that fails",
  );
});

test("D45: the example both prompts show resolves to ONE cluster, and its foil does not", () => {
  // The example is `as const`, so its arrays are readonly; ClusterContext is the
  // queue item's own mutable shape. Copying is the seam, not a cast.
  const ctx = {
    fileScope: [...ACCEPTANCE_SUBJECT_EXAMPLE.fileScope],
    testScope: [...ACCEPTANCE_SUBJECT_EXAMPLE.testScope],
  };
  const good = acceptanceClusters(ACCEPTANCE_SUBJECT_EXAMPLE.good, ctx);
  assert.deepEqual(
    good,
    ["src/parser.ts"],
    "the advice the prompts give is advice the gate accepts: " + JSON.stringify(good),
  );
  const bad = acceptanceClusters(ACCEPTANCE_SUBJECT_EXAMPLE.bad, ctx);
  assert.ok(
    bad.length > 1,
    "and the foil is genuinely refused, so the example teaches a real difference: " +
      JSON.stringify(bad),
  );
});

// ---------------------------------------------------------------------------
// D45b: the clause the classifier looped on.
//
// The aborted classifier sub-session on the D45 verification cell spent 34,338
// bytes of reasoning and was killed mid-thought. Its last words are not item
// authoring — they are the §3.2 rule being simulated in its head:
//
//   "criterion 5 opens with src/solvers/p001.py, so it's the p001.py subject.
//    Good. But it references __init__.py. Is that OK? ... Actually, wait. Let me
//    reconsider. Is there a risk the gate sees src/solvers/__init__.py in
//    criterion 5 and counts it as a subject?"
//
// The answer is no, and the guidance did not say so. A rule stated without the
// clause that resolves its obvious ambiguity buys deliberation, not compliance,
// and deliberation against a 12-minute role deadline is what killed the turn.
//
// The clause is pinned by running the gate rather than by asserting the prose:
// telling a model something the gate does not do is worse than telling it
// nothing, and this row is what stops that.
// ---------------------------------------------------------------------------

test("D45b: a criterion's SUBJECT is its first path — later paths cost nothing", () => {
  const ctx = {
    fileScope: [...ACCEPTANCE_SUBJECT_EXAMPLE.fileScope],
    testScope: [...ACCEPTANCE_SUBJECT_EXAMPLE.testScope],
  };
  const clusters = acceptanceClusters([...ACCEPTANCE_SUBJECT_EXAMPLE.laterPath], ctx);
  assert.deepEqual(
    clusters,
    ["src/parser.ts"],
    "a criterion opening with a declared path and naming another path later is ONE " +
      "cluster; the classifier that could not confirm this spent 34 KB failing to: " +
      JSON.stringify(clusters),
  );
});

test("D45b: both prompts state the first-path clause", () => {
  for (const prompt of [classifierPrompt("add a solver"),
                        decomposePrompt("do the work", testConfig(), packMap())]) {
    assert.match(
      prompt,
      /only the first path/i,
      "the clause that resolves the rule's ambiguity must reach the role the rule judges",
    );
  }
});

// ===========================================================================
// [D48] The plan stage does not terminate, because its artifact is specified
// larger than the reply that has to carry it.
//
// Epoch 20 ran conductor_plan on grid2048-headless-py with every sub-session
// deadline removed. ONE dispatch ran 360 minutes, compacted 16 times, hit the
// 16,384-token output cap exactly 9 times, spent 307,031 completion tokens —
// 11x the entire baseline budget for the same task — and left the tree
// byte-identical to the seed. Each lap climbed past the compaction threshold,
// was compacted, re-read the tree, rebuilt the same reasoning, reached the emit
// step and was truncated. Three earlier epochs recorded this as "timeout at
// conductor_plan": the symptom recorded as the cause, because no budget exits
// that loop. Everything upstream is affordable — intake 11.5 min, decompose two
// rolls at 13.5/13.7 min producing three well-formed items.
//
// Two causes, both in this file's neighbourhood rather than in the serving stack:
//
//   (a) plan.md demanded complete code for every non-obvious step, so plan.md
//       had to contain the solution before the implementer wrote it. On a
//       two-function task the plan is larger than the diff and larger than the
//       window, and raising the output cap lowers the compaction threshold by
//       the same amount — the two walls are one number pulling both ways.
//   (b) planPrompt was the one planner dispatch carrying no scopableFilesSection,
//       so every lap re-read the tree that decomposePrompt is handed for free
//       (D36) — 20 reads and 3 bashes per lap, paid per compaction, not once.
// ===========================================================================

test("[D48] plan.md demands complete code only where the item's acceptance leaves a choice open", () => {
  const plan = readPack("plan.md");
  const flatPlan = flat(plan);

  assert.ok(
    !flatPlan.includes("Every non-obvious step carries complete code, not a sketch"),
    "the unconditional rule is what made plan.md contain the solution before the implementer " +
      "wrote it; it must not survive anywhere in the pack",
  );

  // The relaxation has to be CONDITIONED, not dropped: the doctrine's reason (a
  // plan that hand-waves is a plan that defers decisions) is real. The condition
  // is the item's own specification, which the planner is already handed.
  const selfCheck = packSection(plan, "Self-check before returning");
  assert.notEqual(selfCheck, null, "plan.md must still carry the section the plan prompt composes from");
  const flatCheck = flat(selfCheck ?? "");
  assert.match(
    flatCheck,
    /acceptance/i,
    "the self-check must name what now decides whether a step carries code; it reads: " + flatCheck,
  );
  assert.match(
    flatCheck,
    /testScope/i,
    "and the test that proves the behaviour, which is the other half of the specification",
  );
  assert.match(
    flatCheck,
    /complete code|exact signature/i,
    "and it must still demand real code where the choice IS open — this is a narrowing, not a repeal",
  );
});

test("[D48] the conductor_plan brief carries the narrowed rule, not only the pack", () => {
  // The pack reaches the planner twice (ROLE_PACKS injects plan.md whole, and the
  // brief quotes the self-check verbatim). The brief is the copy the model reads
  // last, so the narrowing is only load-bearing if it survives the slice.
  const brief = flat(planPrompt("do the work", testQueue(), testConfig(), packMap()));
  assert.match(
    brief,
    /acceptance/i,
    "the narrowing reaches the dispatch only through plan.md's self-check slice",
  );
  assert.ok(
    !brief.includes("Every non-obvious step carries complete code, not a sketch"),
    "and the retired unconditional rule reaches it through no route at all",
  );
});

test("[D48] the plan brief states the reply cap, which the model cannot otherwise observe", () => {
  const brief = planPrompt("do the work", testQueue(), testConfig(), packMap());
  assert.match(
    brief,
    /ONE reply/,
    "a planner truncated at the output cap 9 times was never told the reply was bounded",
  );
  assert.match(
    brief,
    /truncated/i,
    "and must be told what overrunning costs — the dispatch, not the tail of the document",
  );
});

test("[D48] the plan brief carries the scopable tree, as the decompose brief already does", () => {
  const root = mkdtempSync(path.join(tmpdir(), "d48-"));
  const write = (rel: string, body: string): void => {
    mkdirSync(path.join(root, path.dirname(rel)), { recursive: true });
    writeFileSync(path.join(root, rel), body);
  };
  write("src/board.py", "def spawn(board):\n    return board\n");
  write("README.md", "# not scopable\n");

  const config = testConfig();
  const files = scopableFiles(root, config);
  const source = scopableSource(root, files);
  assert.equal(source.length, files.length, "premise: a repo this small is carried whole");

  const bare = planPrompt("do the work", testQueue(), config, packMap());
  assert.ok(
    !bare.includes("def spawn(board)"),
    "premise: the brief carries the tree only when the handler passes it",
  );

  const brief = planPrompt("do the work", testQueue(), config, packMap(), files, source);
  assert.match(
    brief,
    /def spawn\(board\)/,
    "the code itself, not a promise of it — a planner that must read the tree reads it once " +
      "per dispatch, and this stage re-dispatches on every compaction",
  );
  assert.ok(!brief.includes("not scopable"), "and nothing behavioralPaths does not own");
  assert.match(
    brief,
    /plan from here rather than reading them again/,
    "the section says why it is there, in the verb of the stage that receives it",
  );

  rmSync(root, { recursive: true, force: true });
});

// ===========================================================================
// [D49] The plan-review fan-out truncates its verdict, which is [D48]'s defect
// multiplied by the lens count.
//
// Epoch 21 fixed conductor_plan and the run reached PLANNED in 22 minutes. The
// stage BELOW it then spent 4h28m and 12 compactions on four lenses:
//
//   correctness    3 attempts, schema-invalid, then {"findings":[]} on re-run
//   completeness   3 attempts, schema-invalid, then a real finding on re-run
//   decomposition  clean, 1 attempt, both rounds
//   minimality     2 attempts -> {"findings":[]}
//
// Every failed attempt was the same error: `JSON Parse error: Unexpected EOF` —
// the reply cut off mid-object. The correctness lens had a REAL finding it could
// not deliver ("the plan's risk note makes a false blanket claim about
// rng_state"), spent 153 minutes on three attempts, and on the re-run returned
// an empty findings list. The run then advanced on `survivingMajors === 0`.
//
// Two causes, the same two as [D48]:
//
//   (a) lensPrompt carried no scopableFilesSection, so four lenses each re-read
//       the tree independently — ~21 of the stage's first 26 minutes were reads
//       — and pushed past the compaction threshold before writing a word.
//   (b) nothing told a lens its reply was bounded, so it wrote its reasoning
//       into the reply and was cut off inside the JSON.
//
// An empty findings list is the dangerous outcome, not the hard failure: it
// parses, it satisfies the schema, and downstream it reads as a lens that
// reviewed the plan and approved it.
// ===========================================================================

function testLens(): { id: string; charge: string } {
  return { id: "correctness", charge: "correctness of the plan" };
}

test("[D49] the lens brief states the reply cap, so a lens does not spend it on reasoning", () => {
  const brief = lensPrompt(testLens() as never, "do the work", "# plan", testQueue(), packMap());
  assert.match(
    brief,
    /ONE message/,
    "a lens truncated at Unexpected EOF on six attempts across two rounds was never told the " +
      "reply was bounded",
  );
  assert.match(
    brief,
    /truncated/i,
    "and must be told what overrunning costs — the lens is discarded, not partially kept",
  );
  assert.match(
    brief,
    /reasoning that got you there does not belong/i,
    "and told what to leave OUT, since a findings list is small and the reasoning is not",
  );
});

test("[D49] the lens brief carries the scopable tree, read once for every lens of every round", () => {
  const root = mkdtempSync(path.join(tmpdir(), "d49-"));
  const write = (rel: string, body: string): void => {
    mkdirSync(path.join(root, path.dirname(rel)), { recursive: true });
    writeFileSync(path.join(root, rel), body);
  };
  write("src/moves.py", "def slide_left(row):\n    return row, 0\n");
  write("README.md", "# not scopable\n");

  const config = testConfig();
  const files = scopableFiles(root, config);
  const source = scopableSource(root, files);
  assert.equal(source.length, files.length, "premise: a repo this small is carried whole");

  const bare = lensPrompt(testLens() as never, "do the work", "# plan", testQueue(), packMap());
  assert.ok(
    !bare.includes("def slide_left"),
    "premise: the brief carries the tree only when the handler passes it",
  );

  const brief = lensPrompt(
    testLens() as never,
    "do the work",
    "# plan",
    testQueue(),
    packMap(),
    files,
    source,
  );
  assert.match(
    brief,
    /def slide_left\(row\)/,
    "a lens judging whether a plan's steps work must know the code they touch; four lenses " +
      "fetching it independently is D36's cost times the fan-out width",
  );
  assert.ok(!brief.includes("not scopable"), "and nothing behavioralPaths does not own");
  assert.match(
    brief,
    /review from here rather than reading them again/,
    "the section says why it is there, in the verb of the stage that receives it",
  );

  rmSync(root, { recursive: true, force: true });
});

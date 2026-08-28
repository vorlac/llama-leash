// conductor/adapter/inject.ts — Task 8.2: the §6.4 system-prompt injection layer
// (plan lines 1892-1903, §4.1 roles table 1512-1543, §4.4 router headers 1636-1698,
// §3.8 liveness beacon 1478-1495). Four concerns, one seam:
//   - buildSystemAppend: the `experimental.chat.system.transform` body — the role's
//     doctrine pack(s) verbatim, then a live state block RE-STATED every request and
//     never remembered (G9). A pure function of its inputs.
//   - paramsForRole:     the `chat.params` sampling table (§4.1).
//   - headersFor:        the `chat.headers` §4.4 router tags.
//   - composeDelivery:   the ONE call the composition root makes per request — the
//     three above answered together, plus the receipt fields (which packs, their
//     digest) the §7.4 journal record carries. It exists so the plugin's three
//     hooks cannot each compose a DIFFERENT delivery for the same session: the
//     headers a request is tagged with and the doctrine it carries are two halves
//     of one decision, and the router's affinity is a lie the moment they diverge.
//   - loadPacks/initPlugin: the §6.4 fail-closed init — a missing pack is a startup
//     error surfaced BEFORE the §3.8 beacon is written, so the beacon's ABSENCE
//     proves init failed. loadPacks/initPlugin are the ONLY filesystem-touching
//     functions here; the transform helpers are pure (no I/O, no clock, no
//     randomness), so identical inputs yield byte-identical output (G9).
//
// ADAPTER (G14): the pure helpers borrow only the core `legalTools` derivation
// (§3.1: one legality verdict, three consumers, they can never disagree). The two
// init functions use only node:fs / node:path — no single-runtime global, no shell
// tag, no top-level await — so this runs under BOTH Node type-stripping and the
// alternate opencode plugin runtime.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import * as path from "node:path";

import { legalTools } from "../core/gates-phase.ts";
import type { GateRun, GateItem, GateQuestion, RecommendedTool } from "../core/gates-phase.ts";
import { callableBy, callerAllowed, callerKindOf } from "../core/tool-legality.ts";
import type { CallerIdentity } from "../core/tool-legality.ts";
import type { SessionRegistryEntry } from "./chat-message.ts";

// ---------------------------------------------------------------------------
// §4.1 roles table — the per-role selections a single model still varies.
// ---------------------------------------------------------------------------

// Role -> doctrine pack file(s) (§4.1 col 2). append[0] is ALWAYS the first entry
// (the session's primary doctrine), verbatim from the cached pack map; a role with a
// secondary pack contributes it as a further entry before the state block.
const ROLE_PACKS: Record<string, readonly string[]> = {
  orchestrator: ["core.md"],
  planner: ["decompose.md", "plan.md"],
  testWriter: ["tdd.md"],
  implementer: ["tdd.md"],
  reviewer: ["review.md", "test-vet.md"],
  skeptic: ["skeptic.md"],
  mechanical: ["core.md"],
};

// Role -> sampling temperature (§4.1 col 3).
const ROLE_TEMPERATURE: Record<string, number> = {
  orchestrator: 0.4,
  planner: 0.7,
  testWriter: 0.5,
  implementer: 0.4,
  reviewer: 0.3,
  skeptic: 0.3,
  mechanical: 0.1,
};

// Role -> per-request thinking-channel budget, in tokens. -1 is unbudgeted.
//
// 93.1% of the epoch-22 conductor cell's decode was reasoning (76,449 of 82,098
// reported output tokens; per role: reviewer 97.9%, testWriter 97.7%,
// orchestrator 89.3%, planner 88.9%, skeptic 88.0%, mechanical 78.7%). The
// budget rides the REQUEST BODY, not the server: `--reasoning-budget` is
// server-wide and one llama-server serves all three arms, so a server-wide clamp
// helps the conductor arm 6-19x more than the flat arms and voids every cell
// already scored.
//
// WHAT THESE NUMBERS ARE FITTED TO. Epoch 22's measured per-turn reasoning
// (n turns, median, p95 tokens): mechanical 2/180/260, orchestrator 14/157/362,
// skeptic 4/292/469, testWriter 5/177/3272, reviewer 4/4731/12106,
// planner 4/6454/17187. Every role except the reviewer is budgeted ABOVE its
// own p95, which is the conservative default where no direct evidence exists:
// a bound under observed healthy thinking would cut work that completed.
//
// THE REVIEWER IS THE EXCEPTION, and it is set from a paired replay rather than
// from that rule. Its four c828 lens briefs were rebuilt and re-run one at a
// time at -1 and at 3072, judged on the SUMMED tokens across all four because
// per-brief deltas swing either way:
//
//   lens            -1 tokens                    3072 tokens
//   correctness     13,172 (2 findings)           3,345 (1 finding)
//   completeness     6,719 (0 findings — an       3,325 (1 finding)
//                           empty review)
//   decomposition    6,341 (1 finding)            2,643 (1 finding)
//   minimality      16,384 (the OUTPUT CAP, and   2,708 (valid, 0 findings)
//                           no reply at all)
//   SUM             42,616                       12,021   -71.8%
//
// Same total findings — three either way — for 28% of the tokens, with no reply
// that validated at -1 failing to validate at 3072. The unbudgeted arm's largest
// line item is a lens that spent its ENTIRE 16,384-token output allowance in the
// thinking channel and returned zero characters: 38% of that arm's decode bought
// nothing. So the bound is not merely a tail guard for the reviewer; below its
// own observed p95 it is also where the runaway stops.
//
// The PLANNER is deliberately unbudgeted. It is 88.9% reasoning and 41% of the
// arm's decode — the largest single prize — but it is also the one role where
// deliberation may be load-bearing, and that is a quality trade no cost metric in
// this repository can see. The reviewer replay is the instrument that would
// settle it, and it has not been run for the planner. Escalation, not a decision
// to take here.
const ROLE_REASONING_BUDGET: Record<string, number> = {
  orchestrator: 3072,
  planner: -1,
  testWriter: 4096,
  implementer: 4096,
  reviewer: 3072,
  skeptic: 3072,
  mechanical: 3072,
};

// What the model is told when the budget runs out. It matters that this is an
// instruction to ANSWER rather than a truncation: cutting a reply off mid-thought
// yields the empty-text/reasoning-only message this budget exists to prevent.
export const REASONING_BUDGET_MESSAGE = "Budget spent. Emit the reply now.";

// Role -> §4.4 priority tag (interactive | review | batch), derived from §4.1 col 5.
const ROLE_PRIORITY: Record<string, string> = {
  orchestrator: "interactive",
  planner: "interactive",
  testWriter: "review",
  implementer: "review",
  reviewer: "review",
  skeptic: "review",
  mechanical: "batch",
};

// The nine doctrine packs §6.4 loads once at init (the seven role packs plus
// debug.md and receive-review.md). debug.md IS delivered by buildSystemAppend on an
// implementer's DEBUG posture (§4.1). receive-review.md is delivered by
// buildSystemAppend on the registry entry's `receivingReview` signal — the mark the
// §3.3 review-fix routing puts on exactly the dispatches that receive review
// findings (C-028: a pack that is loaded but never delivered governs nothing).
const REQUIRED_PACKS: readonly string[] = [
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

// ---------------------------------------------------------------------------
// (a) buildSystemAppend — doctrine pack(s) + the live state block.
// ---------------------------------------------------------------------------

// The trailing options object §6.4 needs but its ledger arg list omits: what
// buildSystemAppend forwards to legalTools (repoConfigured) plus the two scalars the
// state block reports that are derivable from neither items nor questions.
export interface InjectCtx {
  repoConfigured: boolean;
  // §3.9: whether conductor_publish can work at all in this workspace, i.e.
  // gitio.isRepo(root). REQUIRED rather than optional, and threaded rather than
  // derived here, for two reasons: buildSystemAppend runs on EVERY prompt and
  // isRepo shells out to git, and a caller that must name its git mode cannot
  // forget to have one. Without it the state block names conductor_publish as
  // the next tool in a run where the handler always refuses it (C-054).
  publishEnabled: boolean;
  taintCount: number;
  overridesRemaining: number;
}


// [D32] The tools §3.5 lets a sub-session call, derived from the same legality
// table the refusal reads, so the block cannot name a set the gate disagrees with.
function subSessionTools(): string {
  return callableBy("sub-session").join(", ");
}

// [D32] The run's next action, narrowed to what THIS session may actually call.
//
// `legalTools` answers "where does the run go next", which is a question about the
// run and not about whoever is reading the answer. §3.5 lets a sub-session call
// only override/status/surface, so handing a planner the run's stage tool is an
// instruction the gate then refuses it for — measured byte-exact in the 14.2
// campaign as `#9 planner rec=conductor_decompose -> conductor_decompose REFUSED`.
//
// ONE derivation, because the block renders it into a sentence and the §7.4 receipt
// records it as a field, and a receipt that disagrees with the block it accompanies
// makes the "recommended vs actual" signal describe a request nobody sent.
function recommendationFor(
  registryEntry: SessionRegistryEntry,
  runRecommended: RecommendedTool | null,
): RecommendedTool | null {
  if (runRecommended === null) return null;
  const caller: CallerIdentity = {
    role: registryEntry.role,
    itemId: registryEntry.itemId,
  };
  return callerAllowed(runRecommended.tool, caller).ok ? runRecommended : null;
}

// The STABLE anchor — the LAST append entry, byte-identical for the life of a
// session by construction: it reads nothing but the registry entry, which is
// written once at dispatch. The live values it used to carry ride each request's
// TAIL instead (renderStateTail below), because the system prompt is the KV-cache
// prefix of every request: qwen3.8-27b is hybrid/recurrent, llama-server cannot
// rewind its cache to an arbitrary offset, and a one-byte change here is a total
// re-prefill of the whole conversation. Epoch 22 measured exactly that — three
// FSM phase boundaries, three cold orchestrator turns, 734 s of prefill for 281
// output tokens.
function renderStableStateBlock(registryEntry: SessionRegistryEntry): string {
  const lines: string[] = [];
  lines.push(
    "Conductor live state — the live values ride each request's TAIL, not this header.",
  );
  lines.push(
    'Trust only the NEWEST block in this conversation opening "Conductor live state ' +
      '(supersedes" — it is the run\'s current position, re-derived at that instant; every ' +
      "earlier one is a position the run has already left. It arrives appended to each " +
      "tool result and to each conductor re-prompt. In a brand-new conversation none has " +
      "arrived yet: your doctrine pack and the prompt you were handed are the whole brief " +
      "until one does.",
  );
  // The item id is written once at dispatch and never moves; the item's STATE is
  // live and rides the tail.
  if (registryEntry.itemId !== undefined) {
    lines.push(`Your assigned item: ${registryEntry.itemId}.`);
  }
  // What to do on the FIRST turn of a session, before any tool result has
  // carried a state block. Keyed on the ROLE, which is written once at dispatch
  // and never changes, so this stays byte-stable for the session's life.
  //
  // No stage tool is named here. A run resumed by a second process can be at ANY
  // FSM position, so naming one would be the D32 defect — telling a session to
  // call something the gate then refuses. conductor_status is named for the same
  // reason renderNoRunStateBlock names it: with no action known there is no
  // action to compete with, and it is the one tool that reports the position.
  if (callerKindOf(registryEntry.role) === "sub-session") {
    lines.push(
      "Until one arrives, do the work your brief asks for and reply with your result: a " +
        "dispatched session's next action is always its reply (§3.5).",
    );
  } else {
    lines.push(
      "Until one arrives, do not assume a stage: conductor_status reports where the run " +
        "actually is.",
    );
  }
  return lines.join("\n");
}

// Render the live state tail — the volatile half of the state block, ≤30 lines,
// re-derived and re-stated at every delivery (§6.4), never remembered. It
// SUMMARIZES: it names only the single recommended tool (and, for a sub-session,
// its own active item), never the full item list, so it stays bounded no matter
// how many items the run carries. The other legal tools are folded into a numeric
// COUNT — never a second "do this" that would contradict the recommendation.
export function renderStateTail(
  registryEntry: SessionRegistryEntry,
  run: GateRun,
  items: GateItem[],
  questions: GateQuestion[],
  ctx: InjectCtx,
): string {
  const verdict = legalTools(run, items, questions, ctx.repoConfigured, ctx.publishEnabled);
  // [D32] `legalTools` answers "where does the RUN go next", which is a question
  // about the run and not about whoever is reading the block. A sub-session is
  // reading it too, and §3.5 lets a sub-session call only override/status/surface
  // — so naming the run's stage tool to a planner is telling it to do something
  // the gate will refuse it for.
  //
  // Measured, 14.2 epoch 9, byte-exact:
  //
  //   #9 planner rec=conductor_decompose -> conductor_decompose REFUSED
  //      "conductor_decompose is not among the tools such a session may call"
  //
  // The planner did what the block said and was refused for it. D15 recorded that
  // as the planner reaching for a forbidden tool; it was the block handing it one.
  const runRecommended = verdict.recommended;
  const recommended = recommendationFor(registryEntry, runRecommended);
  // The recommended tool is always one of the legal tools, so the count of the
  // OTHER legal tools excludes it (and excludes nothing when nothing is recommended).
  const otherLegal = verdict.legal.size - (recommended !== null ? 1 : 0);

  const openQuestions = questions.filter((q) => q.answeredIso === null).length;
  const blocked = items.filter((it) => it.blocked !== null).length;
  const deferred = items.filter((it) => it.deferred !== null).length;

  const lines: string[] = [];
  lines.push(
    "Conductor live state (supersedes every earlier state block — trust only the newest).",
  );
  lines.push(`Run state: ${run.state}`);

  // A sub-session bound to an item reports THAT item's id and FSM state (the block's
  // focus is its own work, not the whole run's item list).
  if (registryEntry.itemId !== undefined) {
    const active = items.find((it) => it.id === registryEntry.itemId);
    if (active !== undefined) {
      lines.push(`Active item: ${active.id} (${active.state})`);
    } else {
      lines.push(`Active item: ${registryEntry.itemId} (not in the current item set)`);
    }
  }

  // The single recommended next tool "with its args" — its name, and, when it is a
  // per-item stage tool, the id it targets. A terminal run recommends nothing, and we
  // name no tool for it. No OTHER legal tool is ever named here — only counted below.
  if (recommended === null && runRecommended !== null) {
    // [D32] The run HAS a next action and it is not this session's to take. Say
    // what this session's next action is instead — replying is the protocol, and a
    // sub-session told only what it may not do has to discover the rest by being
    // refused, which costs a turn on a machine where a turn is minutes.
    lines.push(
      `Next action: reply with your result. The run's next step is ${runRecommended.tool}, ` +
        "which the orchestrator takes from your reply — a sub-session may call only " +
        `${subSessionTools()} (§3.5).`,
    );
  } else if (recommended === null) {
    // No hardcoded terminality claim: legalTools already computed the AUTHORITATIVE
    // reason nothing is recommended (terminal run, stalled EXECUTING wave, non-work
    // INTAKE, …). Render it verbatim so the block is never falsely "terminal".
    lines.push(`Next action: none. ${verdict.why}`);
  } else if (recommended.args.itemId !== undefined) {
    lines.push(`Next action: call ${recommended.tool} on ${recommended.args.itemId}.`);
  } else {
    lines.push(`Next action: call ${recommended.tool}.`);
  }

  // The count, and no invitation to go and get them. Naming a way to enumerate the
  // alternatives — "call conductor_status to see them" — belongs to a block with no
  // action to name: `conductor_status` is read-only, advances nothing, and is the
  // orchestrator's most common wrong call in the 14.2 capture. A block that states
  // the action and then offers a route to alternatives argues with itself, and the
  // reader resolves that argument however it likes.
  lines.push(`Other legal tools available now: ${otherLegal}. None of them is the next action.`);
  lines.push(`Open questions: ${openQuestions}`);
  lines.push(`Items blocked: ${blocked} · deferred: ${deferred}`);
  lines.push(`Taint count: ${ctx.taintCount} · overrides remaining: ${ctx.overridesRemaining}`);

  return lines.join("\n");
}

/**
 * The single next tool the state block names, as DATA.
 *
 * The block renders it into a sentence a human reads; the §7.4 receipt records it
 * as a field an observer can score. Both come from `recommendationFor`, so a
 * receipt that disagreed with the block it accompanies is not constructible —
 * including the role narrowing, which is where the two most easily diverge: a
 * receipt reading the run-level verdict beside a block that narrowed it would
 * record `recommended: conductor_classify` against a session told "reply with your
 * result", and the observer's mismatch column would score a request nobody sent —
 * and without the field, "recommended vs actual", the signal that names a model
 * ignoring its own state block sixteen turns running, is unrecorded on every run.
 */
export function recommendedToolOf(
  registryEntry: SessionRegistryEntry,
  run: GateRun,
  items: GateItem[],
  questions: GateQuestion[],
  ctx: InjectCtx,
): { tool: string | null; itemId: string | null } {
  const recommended = recommendationFor(
    registryEntry,
    legalTools(run, items, questions, ctx.repoConfigured, ctx.publishEnabled).recommended,
  );
  if (recommended === null) return { tool: null, itemId: null };
  const itemId = recommended.args.itemId;
  return { tool: recommended.tool, itemId: typeof itemId === "string" ? itemId : null };
}

// The state block for a workspace that has no live run: the §3.2 fact that a run
// is created when the orchestrator receives a prompt. It is a SEPARATE rendering
// rather than renderStateTail over a fabricated run, because every field that
// block reports (state, recommendation, counts) would be an invention here, and a
// state block that invents the run state is worse than one that says there is none.
export function renderNoRunStateBlock(): string {
  return [
    "Conductor live state — re-stated every request (§6.4), never remembered.",
    "Run state: none — this workspace has no live conductor run.",
    // conductor_status is named here deliberately and is not the D26 case: with no
    // live run there IS no next action to compete with, so pointing at the one tool
    // that can say what the workspace holds is the whole of the useful advice.
    "Next action: none. A run is created when the orchestrator receives a prompt (§3.2); " +
      "conductor_status reports what this workspace already holds.",
  ].join("\n");
}

// The §4.1 pack files this session's delivery carries, in order: the role's
// primary pack first, then the posture-conditional secondaries. Exported so a
// caller can NAME what was delivered (the §7.4 receipt) without re-deriving the
// selection rule — two spellings of "which pack does this role get" is the
// ISSUE-003 shape, one directory over.
export function packFilesFor(
  registryEntry: SessionRegistryEntry,
  items: GateItem[],
): string[] {
  const packFiles = [...(ROLE_PACKS[registryEntry.role] ?? ["core.md"])];
  // §4.1: an implementer whose ACTIVE item is in DEBUG posture also receives
  // debug.md as a secondary pack (tdd.md stays the primary, append[0]). Guard it
  // tightly — non-implementer roles, a missing/unknown itemId, or a non-debugging
  // item get nothing extra — and never duplicate debug.md if it is already listed.
  if (registryEntry.role === "implementer" && registryEntry.itemId !== undefined) {
    const activeItem = items.find((it) => it.id === registryEntry.itemId);
    if (activeItem?.debugging === true && !packFiles.includes("debug.md")) {
      packFiles.push("debug.md");
    }
  }
  // §3.3/C-028: a fix dispatch that receives review findings also receives doctrine
  // receive-review.md as a SECONDARY pack (the role's primary pack stays append[0]),
  // de-duplicated exactly as debug.md is. The signal rides the §3.5 registry entry
  // the fan-out engine wrote for that dispatch — never the item's state, so the SAME
  // item's other dispatches (a debug fix, a green fix) receive nothing extra.
  if (registryEntry.receivingReview === true && !packFiles.includes("receive-review.md")) {
    packFiles.push("receive-review.md");
  }
  return packFiles;
}

// The pack CONTENTS for a selection, verbatim from the cached map. A pack the map
// does not carry contributes nothing rather than an "undefined" string; the empty
// fallback guarantees append[0] is always a string and the state block is always
// the last entry, whatever the cache holds.
function packTextsFor(packFiles: string[], packs: Record<string, string>): string[] {
  const texts: string[] = [];
  for (const file of packFiles) {
    const content = packs[file];
    if (content !== undefined) texts.push(content);
  }
  if (texts.length === 0) texts.push("");
  return texts;
}

// The `experimental.chat.system.transform` body: [ primaryPack, ...secondaryPacks,
// stableStateBlock ]. append[0] is the role's primary doctrine pack VERBATIM from
// the cached map; the LAST entry is the stable state anchor — the LIVE values ride
// the request tail (renderStateTail), never the system prompt, so the prefix stays
// byte-stable across FSM transitions and the KV cache survives them. An unknown
// role falls back to core.md (the orchestrator/mechanical lite doctrine) so an
// unregistered session still receives grounding rather than an empty system append.
//
// `run`, `questions` and `ctx` are still taken — they are the signature the §6.4
// ledger names — but nothing byte-varying is rendered from them: that is the
// mechanism under test in [inject-stable-prefix], and the ONE exception is the
// items-driven pack selection (§4.1 debug posture), which is doctrine, not state.
export function buildSystemAppend(
  registryEntry: SessionRegistryEntry,
  run: GateRun,
  items: GateItem[],
  questions: GateQuestion[],
  packs: Record<string, string>,
  ctx: InjectCtx,
): string[] {
  void run;
  void questions;
  void ctx;
  const append = packTextsFor(packFilesFor(registryEntry, items), packs);
  append.push(renderStableStateBlock(registryEntry));
  return append;
}

// ---------------------------------------------------------------------------
// (b) paramsForRole — the `chat.params` sampling table (§4.1).
// ---------------------------------------------------------------------------

export function paramsForRole(role: string): {
  temperature: number;
  topP?: number;
  // The thinking-channel bound and the message that ends it. Both absent for an
  // unbudgeted role (planner, and any role not in the table): an absent key
  // leaves the server's own default standing, where a -1 would assert one.
  reasoningBudgetTokens?: number;
  reasoningBudgetMessage?: string;
} {
  const params: {
    temperature: number;
    topP?: number;
    reasoningBudgetTokens?: number;
    reasoningBudgetMessage?: string;
  } = { temperature: ROLE_TEMPERATURE[role] ?? 0.4 };
  const budget = ROLE_REASONING_BUDGET[role];
  if (budget !== undefined && budget > 0) {
    params.reasoningBudgetTokens = budget;
    params.reasoningBudgetMessage = REASONING_BUDGET_MESSAGE;
  }
  return params;
}

// ---------------------------------------------------------------------------
// (c) headersFor — the `chat.headers` §4.4 router tags.
// ---------------------------------------------------------------------------

// The §4.4 prefix-affinity group id: the natural KV-hot grouping key is the session's
// worktree/tree; failing that, the item it works on. Bare sessions with neither (a
// tree-less orchestrator) have no group, and the header is OMITTED entirely so the
// router treats the request as ungrouped.
function groupOf(registryEntry: SessionRegistryEntry): string | null {
  if (typeof registryEntry.tree === "string" && registryEntry.tree.length > 0) {
    return registryEntry.tree;
  }
  if (typeof registryEntry.itemId === "string" && registryEntry.itemId.length > 0) {
    return registryEntry.itemId;
  }
  return null;
}

export function headersFor(
  registryEntry: SessionRegistryEntry,
  job?: { schema?: boolean },
): Record<string, string> {
  const headers: Record<string, string> = {
    "X-Conductor-Role": registryEntry.role,
    "X-Conductor-Priority": ROLE_PRIORITY[registryEntry.role] ?? "interactive",
  };
  const group = groupOf(registryEntry);
  if (group !== null) headers["X-Conductor-Group"] = group;
  // §4.4: X-Conductor-Schema: required ONLY when the job flags structured output.
  if (job?.schema === true) headers["X-Conductor-Schema"] = "required";
  return headers;
}

// ---------------------------------------------------------------------------
// (d) composeDelivery — the three above, answered together, plus the receipt.
// ---------------------------------------------------------------------------

// The persisted facts the live state block reports. Assembled by the composition
// root from the store (the ONE place that reads the run directory) and handed here
// as data, which is what keeps this function pure and testable without a workspace.
export interface DeliveryState {
  run: GateRun;
  items: GateItem[];
  questions: GateQuestion[];
  ctx: InjectCtx;
}

// Everything one dispatched request must carry, plus what the §7.4 receipt names.
// `packDigest` is over the delivered pack CONTENT, so a doctrine directory swapped
// under a live run changes the trail even when the file names do not (C-028: a
// receipt that names only file names cannot tell two doctrines apart).
export interface Delivery {
  role: string;
  packFiles: string[];
  packDigest: string;
  // The stable state anchor — the last system entry — named separately from
  // `system` so a caller can RECORD that it went (and how big it was) without
  // re-deriving which entry it is. A delivery whose doctrine arrives and whose
  // block does not is the §6.4 half-miss that leaves a 32k model with no runtime
  // navigation at all.
  stateBlock: string;
  // The VOLATILE half of the state block — Run state, Next action, the counts —
  // re-derived per delivery and carried at the request TAIL (a tool-result
  // decoration or a re-prompt), never in the system prefix: a byte of it in the
  // prefix costs a total re-prefill on a cache the model cannot rewind. Empty
  // for a workspace with no live run.
  stateTail: string;
  // The tool the state block told this session to call next, and the item it
  // named, as fields. Both null for a delivery that recommends nothing (a
  // terminal run, a workspace with no run at all).
  recommended: string | null;
  recommendedItem: string | null;
  system: string[];
  params: {
    temperature: number;
    topP?: number;
    reasoningBudgetTokens?: number;
    reasoningBudgetMessage?: string;
  };
  headers: Record<string, string>;
}

// A stable short digest of the delivered doctrine: each pack's NAME and its bytes,
// order included, so neither a reordering nor a same-length edit is invisible.
// LENGTH-PREFIXED rather than separator-delimited: the framing is then unambiguous
// without a delimiter byte, and no separator can collide with pack content (the
// obvious separator, a control byte, would also make this file binary to grep —
// conductor/tests/source-hygiene.test.ts).
function packDigestOf(packFiles: string[], packs: Record<string, string>): string {
  const hash = createHash("sha256");
  for (const file of packFiles) {
    const content = packs[file] ?? "";
    hash.update(String(file.length) + ":" + file);
    hash.update(String(content.length) + ":" + content);
  }
  return hash.digest("hex").slice(0, 16);
}

// The ONE composition the plugin's three §6.4 hooks share. `state` is null for a
// workspace with no live run: the doctrine still goes (a session with no run is
// still governed by its role's pack), and the state block reports the absence
// rather than inventing a run to describe.
export function composeDelivery(input: {
  registryEntry: SessionRegistryEntry;
  packs: Record<string, string>;
  state: DeliveryState | null;
  job?: { schema?: boolean };
}): Delivery {
  const { registryEntry, packs, state } = input;
  const items = state === null ? [] : state.items;
  const packFiles = packFilesFor(registryEntry, items);
  // buildSystemAppend stays the ONE assembler for the live-run case (it is what
  // the §6.4 ledger names and what the injection suite pins); the no-run case is
  // the same shape with the block that reports the absence.
  const system =
    state === null
      ? [...packTextsFor(packFiles, packs), renderNoRunStateBlock()]
      : buildSystemAppend(registryEntry, state.run, state.items, state.questions, packs, state.ctx);
  const recommendation =
    state === null
      ? { tool: null, itemId: null }
      : recommendedToolOf(registryEntry, state.run, state.items, state.questions, state.ctx);
  return {
    role: registryEntry.role,
    packFiles,
    packDigest: packDigestOf(packFiles, packs),
    stateBlock: system[system.length - 1] ?? "",
    stateTail:
      state === null
        ? ""
        : renderStateTail(registryEntry, state.run, state.items, state.questions, state.ctx),
    recommended: recommendation.tool,
    recommendedItem: recommendation.itemId,
    system,
    params: paramsForRole(registryEntry.role),
    headers: headersFor(registryEntry, input.job),
  };
}

// ---------------------------------------------------------------------------
// (d) loadPacks / initPlugin — the §6.4 fail-closed init.
// ---------------------------------------------------------------------------

// Read the nine required doctrine packs from `doctrineDir`, keyed by filename. Any
// missing or unreadable pack is a STARTUP error (fail-closed, §6.4) whose message
// NAMES the offending pack file, so init can surface exactly which pack is absent.
export function loadPacks(doctrineDir: string): Record<string, string> {
  const packs: Record<string, string> = {};
  for (const file of REQUIRED_PACKS) {
    const packPath = path.join(doctrineDir, file);
    let content: string;
    try {
      content = readFileSync(packPath, "utf8");
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      throw new Error(
        `conductor: required doctrine pack "${file}" is missing or unreadable at ${packPath} ` +
          `(§6.4 fail-closed at init): ${detail}`,
      );
    }
    // A present-but-empty (0-byte / whitespace-only) pack is effectively absent
    // doctrine: fail closed exactly like a missing pack so initPlugin never writes
    // the §3.8 beacon for empty doctrine.
    if (content.trim().length === 0) {
      throw new Error(
        `conductor: required doctrine pack "${file}" is present but empty at ${packPath} ` +
          `(§6.4/§3.8 fail-closed at init)`,
      );
    }
    packs[file] = content;
  }
  return packs;
}

// The §3.8 init ordering seam: load the doctrine packs FIRST; only once they all load
// is the liveness beacon written (exactly once) and the cached map returned. A missing
// pack routes its error to the injected logError seam (§7.1 stderr — client.app.log —
// NOT a conductor journal event; the closed vocabulary has no init event) and is
// re-thrown, and the beacon is NEVER written — so a missing beacon is a real
// fail-closed signal that init did not complete.
export function initPlugin(deps: {
  doctrineDir: string;
  logError: (msg: string) => void;
  writeBeacon: () => void;
}): Record<string, string> {
  let packs: Record<string, string>;
  try {
    packs = loadPacks(deps.doctrineDir);
  } catch (err) {
    deps.logError(err instanceof Error ? err.message : String(err));
    throw err;
  }
  deps.writeBeacon();
  return packs;
}

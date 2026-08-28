# Improve-cycle synthesis — epoch 22 evidence, 2026-08-28

Product of a 44-agent orchestrated review over the epoch-21/22 campaign evidence
(run `wf_72a50591-194`): five parallel evidence readers over the c828 artifacts,
two independent proposal framings, three adversarial skeptics per candidate, one
synthesis. Of eleven candidates proposed, five were refuted outright — and three
of the seven surviving entries below are changes the *refutations* revealed
rather than the candidates themselves. Ranks 3, 4, 5 and the rank-7 observability
slice landed on 2026-08-28 (register D50, D51, D52); ranks 1, 2, 6 and the
rank-7 detector are open.

## The ranked change set

### Rank 1 — Bound the thinking channel per role via the request body — 93.1% of the conductor cell's decode is reasoning

*id: `per-role-reasoning-budget` · needs a full cell to score: yes*

MEASURED BY ME, not inherited: I opened the cell's opencode.db read-only and split each assistant message's reported output tokens across its parts by character share. Reasoning is 76,449 of 82,098 reported output tokens = 93.1%, and 343,690 of 364,590 generated prose characters = 94.3%. Per agent: reviewer 97.9%, testWriter 97.7%, orchestrator 89.3%, planner 88.9%, skeptic 88.0%, mechanical 78.7%. Simulating a 3,072-token per-turn cap clips 9 of 43 messages and saves 36,604 tokens; adding the two aborted lenses (17,868 unrecorded tokens, 100% reasoning — they have a reasoning part and NO text part at all) at 3,072 each saves 11,724 more. Real conductor decode 99,966 -> 51,638, a 48.3% cut, ~65 GPU-minutes at the measured 12.3 tok/s. The saving is concentrated: planner 20,877 + reviewer 12,351 = 69% of it.

THE CANDIDATE'S STEP 1 IS REFUTED AND MUST BE DROPPED. A skeptic showed that `--reasoning-budget` in scripts/serve.py is server-wide, one llama-server serves all three arms, and the flat arms are only ~52-63% reasoning — so a server-wide clamp helps conductor 6-19x more than baseline/doctrine and invalidates every previously scored cell. That is the served-window mistake again.

I VERIFIED THE ESCAPE ROUTE, end to end, and it makes the change conductor-plugin-only. extern/llama-cpp/tools/server/server-common.cpp:1359-1372 reads `reasoning_budget_tokens` (alias `thinking_budget_tokens`) AND `reasoning_budget_message` off the REQUEST BODY, and the body value takes precedence over the server-wide `opt.reasoning_budget`. router/router.hpp forwards the body verbatim, stripping only the `x_conductor` key. conductor/adapter/wire-notes.md:27 is WIRE_CONTRACT_VERIFIED (2026-08-12): a key set on `chat.params` `output.options` lands as a TOP-LEVEL provider-body field (observed `"x_conductor"` in the JSON body). And conductor/plugin/index.ts:1682-1685 already has the seam — it writes only `output.temperature` and `output.topP` today.

SO: extend ROLE_TEMPERATURE's sibling table in conductor/adapter/inject.ts with a per-role reasoning budget, widen paramsForRole (inject.ts:346-348) to return it plus a `reasoning_budget_message` ("Budget spent. Emit the reply now." — the message matters: it forces the model out of the thinking channel with the reply still to write, instead of truncating mid-thought), and write both into `output.options` in the chat.params hook. Baseline and doctrine load no plugin (all 47 of their ledger rows carry role=null), so their request bodies are byte-identical and no flat-arm cell needs re-running.

One gate to respect: server-common.cpp:1366 arms the budget only when `chat_params.thinking_end_tags` is non-empty. The run's own server.log line 90 prints "chat template supports preserving reasoning", which is emitted only when the caps report a wired reasoning parser — so it is armed for this model. Also note server-context.cpp:1404 carries the value by POSITIONAL aggregate init with the field name only in a comment, so anyone verifying this by grep will wrongly conclude the flag is dead.

Graft from skeptic 1: the title claim "90-98% of every reply" is true token-weighted but false per-message (median 65%, 16 of 43 messages under 50%, though those 16 are only 3,040 of 82,098 tokens). State the per-role figures, which are the load-bearing ones.

**Sites:**

- `conductor/adapter/inject.ts:55-63`
- `conductor/adapter/inject.ts:346-348`
- `conductor/plugin/index.ts:1682-1685`
- `conductor/adapter/wire-notes.md:27`
- `extern/llama-cpp/tools/server/server-common.cpp:1359-1372`
- `extern/llama-cpp/tools/server/server-context.cpp:1404`
- `conductor/adapter/tools.ts:2751-2755`

**Measurement:**

THREE TIERS, only the third needs a cell.
(a) Wire check, seconds: a node test asserting paramsForRole returns a budget for reviewer/testWriter and that the chat.params hook writes it into output.options — modelled on the existing x_conductor params-fallback pin in conductor/tests/wire-contract.test.ts.
(b) Mechanism probe, ~1-2 h, ONE server start, NO benchmark cell. Rebuild all four c828 lens briefs from lensPrompt over the run's plan.md + queue.json and replay each ONE AT A TIME (never concurrently — a concurrent control can be killed by the 1,800,000 ms provider timeout or the router's 600 s relay read, which is what makes the control uncomputable) at budget -1 and at 3072. Judge on the SUMMED timings.predicted_n across all four, never per-brief: I checked the per-brief deltas against the real c828 reviewer messages and they are +64%, -33%, -33%, -75% — one brief alone would refute a hypothesis that is true in aggregate. CONFIRMED if the summed predicted_n falls >40% AND all four replies still validate against the Findings schema. REFUTED if the sum falls <25%, or if any reply that validated at -1 stops validating at 3072. Assert also that the reply still carries a reasoning part ENDING on the forced message — otherwise a null result cannot be told apart from a budget that never armed because thinking_end_tags was empty.
(c) Cost and quality, one conductor cell each side: per-role completionTokens from .data/router/metrics.jsonl (which matches llama-server's predicted_n to the token, delta +0 for all six roles), plus scripts/judge_quality.py on a quiet machine. Gate acceptance on QUALITY, not tokens — a cheaper plan that is worse is a regression this campaign's cost metrics cannot see.
Roll out in reasoning-share order, safest first: reviewer (97.9%) and testWriter (97.7%), then orchestrator, then skeptic/mechanical, and planner LAST — planner is 88.9% reasoning and 41% of conductor decode, and it is the one role where a 27B model on a 30 KB repo may genuinely need the deliberation.

**Why it survived:** Two of three skeptics failed to refute it after attacking the mechanism from five directions each; both independently reproduced the reasoning share from the message store. The one serious refutation was aimed squarely at Step 1 (the server-wide serve.py flag) on the arm-confound ground, and it is correct — so I dropped Step 1 and verified the per-request body path it does not touch. I re-derived the 93.1% share and the 48.3% saving myself from opencode.db with a conservative proportional split, and confirmed the body field is read at server-common.cpp:1360 with precedence over the server-wide value, the router forwards it verbatim, and wire-notes.md:27 already pins the opencode-side passthrough. It is the largest measured cost in the run by a factor of three, and it subsumes D-truncate at the source: a lens that cannot think past 3,072 tokens cannot spend 1,800 s in the thinking channel.

### Rank 2 — The orchestrator's system prompt is rewritten at every FSM phase boundary, forcing a full re-prefill of the whole conversation

*id: `stabilize-orchestrator-prefix` · needs a full cell to score: no*

THIS IS A CHANGE REVEALED BY A REFUTATION, not a surviving candidate. The `orchestrator-prefix-survives-a-wave` candidate proposed raising PROMPT_CACHE_RAM_MIB 4096 -> 12288; all three skeptics refuted it (the corrected cache entry rate is 81-84.5 KiB/token not 64, so 12288 MiB holds ~150k not ~196k tokens; eviction is FIFO by insertion so the long-idle orchestrator entry is evicted first regardless of budget; and one skeptic found a counter-instance where the entry was demonstrably resident and the orchestrator still re-prefilled). One skeptic found the real cause. I confirmed it independently and decisively.

MECHANISM, traced in code: conductor/adapter/inject.ts buildSystemAppend returns `[...packs, stateBlock]` and pushes renderStateBlock LAST, delivered through `experimental.chat.system.transform`, which wire-notes records as arriving as its own `role:"system"` message — i.e. at the HEAD of the request. renderStateBlock emits `Run state: ${run.state}` and `Next action: call ${recommended.tool}`, both of which change at every FSM phase boundary. qwen3.8-27b is hybrid/recurrent, so llama-server cannot rewind a KV cache to an arbitrary offset (server-context.cpp forces `n_past = 0` when no checkpoint covers the divergence) — the loss is total, not partial.

CONFIRMED 3 FOR 3 AGAINST THE RUN. I converted the FSM transitions in the c828 journal and matched them to the orchestrator's cache_n=0 turns in the router ledger:
  DECOMPOSED   07:07:43 -> cold turn completing 07:11:19, 206.7 s prefill, 104 tokens out
  PLANNED      07:35:44 -> cold turn completing 07:39:52, 238.9 s prefill, 114 tokens out
  PLAN_REVIEWED 08:37:04 -> cold turn completing 08:42:00, 288.6 s prefill,  63 tokens out
Every other orchestrator turn is warm with cache_n = previous total context minus 1 (11004, 16558, 19544, 21713, 25487, 25776, 26115, 34977, 35495, 39015), and the turn immediately AFTER each cold one is warm again — the one-shot-per-transition signature the prefix-mutation story predicts and the slot-pressure story does not. Slot pressure produces the PARTIAL restore I also see (turn #7, cache_n 10,184 of a 25,194-token context), never a total loss.

COST: 734.2 s = 12.2 min of prefill to produce 281 decoded tokens. I checked overlap: two of the three windows (07:07:43-07:11:10 and 08:37:04-08:41:53) have ZERO other conductor requests in flight — 496 s = 8.3 min of pure single-stream critical path, 4.2% of the 197.1-min busy window. The third overlaps one planner request.

CHANGE: keep the doctrine packs in the system append, where they are byte-stable for the life of a session, and move the volatile fields (`Run state`, `Next action`, counts) out of `output.system` and into the tail of the turn's user message. Then every turn extends a stable prefix.

DESIGN COST TO FLAG FOR THE OWNER: the block's own first line says "re-stated every request (§6.4), never remembered". Moving it to the user message makes it part of remembered history, so stale state blocks accumulate and a model may read an old one. Either the block must carry an explicit supersedes marker, or only the volatile subset moves. This is a doctrine-level ruling, not an implementation detail.

Do NOT touch scripts/conductor_wiring.py:289 for this. Separately and on its own smaller merits, that comment's arithmetic is wrong (it claims 4096 MiB holds 65,536 tokens; at the measured 81-84.5 KiB/token it holds ~48,500) and the same run logged `prompt state size 4938.817 MiB exceeds cache size limit 4096.000 MiB, skipping` for a flat-arm session — a real but separate defect.

**Sites:**

- `conductor/adapter/inject.ts:149-260`
- `conductor/adapter/inject.ts:326-339`
- `conductor/plugin/index.ts:1675-1686`
- `scripts/conductor_wiring.py:277-289`

**Measurement:**

(a) Deterministic offline pin, seconds: a node test asserting the composed `output.system` array is byte-identical across two GateRun states that differ only in `run.state` / `recommended` — i.e. the volatile fields are no longer in the system append.
(b) Cheap live probe, ~10 min, no cell: two requests through the router with a 30k-token context, the second differing only by one byte in the first system message. Read `timings.cache_n` off .data/router/metrics.jsonl. It must be 0 today and previous-total-minus-1 after the change. This proves the mechanism without a benchmark cell.
(c) On the next conductor cell: for role=orchestrator, no row after the session's first may carry cache_n = 0. CONFIRMED if orchestrator prefill falls from 18.9 min toward ~7 min and no post-first-turn cache_n=0 row survives. REFUTED if cache_n is still 0 on phase-boundary turns — which would mean a second prefix source (most likely a per-phase change in the offered tool set, which also lives in the system prompt).

**Why it survived:** The candidate that carried it was refuted three times over, but one skeptic's refutation named a better cause and I verified it end to end rather than taking it on trust: the code path (state block is the LAST system message, and its `Run state` / `Next action` lines change per phase), and the 3-for-3 timing match between FSM transitions and cache_n=0 orchestrator turns, with every intervening turn warm. It is conductor-plugin-only, so it cannot perturb baseline or doctrine, and the mechanism is provable by a two-request probe rather than a benchmark cell — the cheapest real GPU saving on the list.

### Rank 3 — Close the `question` tool surface — it produced 78.7 minutes of zero-GPU dead air and a run with no scored cell

*id: `close-the-question-surface` · needs a full cell to score: no*

Merges `deny-question-tool` and `close-the-question-surface`, with every skeptic correction grafted.

(a) STOP OPENING THE TOOL. I read the fragment: conductor-implementer (line 21) and conductor-test-writer (line 27) carry `"permission": { "question": "ask" }`; conductor-reviewer, conductor-skeptic, conductor-planner and conductor-mechanical (lines 33, 39, 45, 51) carry `"permission": { "question": "ask", "edit": "deny" }`. The candidate's instruction to "replace the permission clause" would silently strip `edit: "deny"` from four agents. DELETE ONLY THE `question` KEY. Prefer adding `"question": false` to each agent's existing `tools` object, which wire-notes 20.2 records as MEASURED to do two things — omit the tool from the offered set AND emit a `question * -> deny` rule — so it survives an opencode bump that drops the base narrowing, which a bare key deletion would not.

(b) REFUSE IT AT THE GATE as a latent-surface pin, following the DENIED_TOOLS shape at conductor/adapter/tools.ts:215 with the refusal block at :542-550. Note explicitly that DENIED_TOOLS also feeds classifyTool (`WRITE_TOOLS.includes(t) || DENIED_TOOLS.includes(t) -> "write"`), so this reclassifies `question` from read to write/guarded while BUILTIN_SIDE_EFFECT keeps it R0 — either accept that fail-closed and comment it, or use a separate list. Keep `question: "R0"` in the table: conductor/tests/builtin-surface.test.ts:41-64 requires every registry tool to keep a class.

(c) REWRITE THE REFUSAL TEXT. Do NOT end it with "use conductor_surface, or reply NEEDS_CONTEXT". A skeptic pulled the stalled session's transcript: after the two edit-gate denials it successfully wrote tests/check_undo.py, ran ast.parse, and reasoned verbatim "Let me now reply with the ImplementerResult JSON. status: DONE" — the call payload is `{"header":"noop","question":"Placeholder — returning ImplementerResult directly."}`. A degenerate end-of-turn call by a session that had already finished. Telling it NEEDS_CONTEXT invites it to convert a completed item into a blocked one. End with: there is no operator to answer in this run; if you are finished, reply now with your result JSON; if you genuinely lack context, say so in that reply.

(d) CORRECT wire-notes 20.1 rather than marking it falsified. Offering is CLIENT-gated, not permission-gated: opencode 1.18.15 registers `question` only when the client is app/cli/desktop or OPENCODE_ENABLE_QUESTION_TOOL is set. scripts/conductor_bench.py runs `opencode run` — the cli client — so it is offered in a benchmark cell and genuinely was not offered in the non-cli wire-contract fixture. Add the client qualifier to :129-135 and :201.

(e) RECORD THE SEPARATE, LARGER DEFECT. The designed refusal at conductor/adapter/continuation.ts:1539-1576 is structurally unreachable on 1.18.15: the question tool's permission runs through opencode's v2 layer, whose event is `permission.v2.asked` with payload `{id, sessionID, action, resources, ...}` and no `permission` field, while continuation.ts:1765 matches the v1 `permission.asked` and bails silently at :1768 when `properties.permission` is absent. Zero permission-bearing journal records across both runs is consistent with that. So conductor/tests/fragment.test.ts:145-158's intent ("grant question so the plugin can refuse it") is not implementable as the code stands — inverting that assertion is a correction, not a design reversal, which removes the owner-ruling blocker the candidate flagged.

HONEST PREDICTED EFFECT — the candidate's "-35% wall" is refuted and must be dropped. At the stall (cell t+146.2 min) the FSM had been in EXECUTING for 19.9 minutes, all three queue items were still PENDING, and no implementer had ever been dispatched. Unblocking RESUMES the cell toward its 480-minute budget. Epoch 20 is the direct counterfactual: same task, same arm, ZERO `question` calls, ran the full 480 min for 307,031 completion tokens and an empty diff. So this returns 78.7 minutes of zero-GPU HOST time and removes a terminal state that yields no scored cell — and it will INCREASE the conductor arm's decode, not decrease it. Say so.

**Sites:**

- `conductor/opencode-fragment.json:21`
- `conductor/opencode-fragment.json:27`
- `conductor/opencode-fragment.json:33`
- `conductor/opencode-fragment.json:39`
- `conductor/opencode-fragment.json:45`
- `conductor/opencode-fragment.json:51`
- `conductor/adapter/tools.ts:215`
- `conductor/adapter/tools.ts:542-550`
- `conductor/tests/fragment.test.ts:145-171`
- `conductor/tests/gate-wiring.test.ts:658-711`
- `conductor/adapter/continuation.ts:1765-1789`
- `conductor/adapter/wire-notes.md:129-135`

**Measurement:**

(a) Unit, seconds: fragment.test.ts asserts `tools.question === false` on all six subagents, that no agent block carries a `question` permission key, AND that reviewer/skeptic/planner/mechanical still carry `edit: "deny"` — that last assertion is the one that catches the spec error in the original candidate.
(b) Unit, seconds: drive gateBeforeToolCall with toolName "question" and assert it throws naming the tool; model it on [5.3-patch-tools-denied] at gate-wiring.test.ts:658-711. Label it a latent-surface pin, not a check of shipped behaviour — if (a) works the model is never offered the tool and this path cannot fire in production.
(c) Headless probe, ~5 min on a quiet machine, no cell: `opencode run --agent conductor-test-writer` with a prompt engineered to reach for operator clarification. The process must EXIT with text, not block. REFUTED if it blocks anyway (the base deny surfaces as a hang rather than a readable refusal), or if the model, unable to ask, emits a well-formed EMPTY test file — which would be the stale-artifact class reappearing under a new cause and would demand the doctrine text change too.
(d) On the next run: journal must contain zero `{"event":"allow","toolName":"question"}` records.

**Why it survived:** The only candidate whose mechanism I could confirm from four independent artifacts — journal seq 140 of 140, the console tail with no matching completion, the opencode.db part row `tool question` with `{"status":"running"}` and no end, and the ledger's last completedAt 78.7 minutes before the console's final frame. Two of three skeptics upheld it; the serious refutation was aimed at the predicted effect ("-35% wall") and at the claim that it explains the arm's non-termination, and both of those are correct and are now dropped. What remains is cheap, unit-testable, cannot kill healthy work, and removes the one failure mode in this campaign that produces no data at all rather than bad data.

### Rank 4 — Journal a provider timeout as itself, and re-prompt with the original brief instead of accusing the model of bad JSON

*id: `classify-provider-timeout-keep-retry` · needs a full cell to score: no*

This is what survives of TWO refuted candidates (`classify-provider-timeout`, `timeout-is-not-a-bad-reply`). All six skeptics across both converged on the same graft: keep the detection, delete the no-retry.

KEEP: conductor/adapter/fanout.ts:646 tests `reply.error` — the HTTP envelope — but opencode reports a timed-out generation on the assistant MESSAGE, in the same envelope under `data.info.error`. `info` is declared at fanout.ts:111 and read nowhere. The SDK's own generated types declare the prompt 200 body as `{info: AssistantMessage; parts: Part[]}` with `AssistantMessage.error?: ProviderAuthError | UnknownError | ...`, matching the two DB rows byte for byte: `{"name":"UnknownError","data":{"message":"The operation timed out."}}`, parts `[step-start, reasoning]`, no text part. extractReplyText keeps only text parts, returns "", and `JSON.parse("")` under JavaScriptCore is exactly "JSON Parse error: Unexpected EOF". Read `data.info.error` in the failure path (AFTER the receipt-parse-succeeds check, so a reply that both errored and produced valid JSON is still honoured) and journal reason "provider-timeout" carrying the error name and message, instead of "schema-invalid" — which is a lie about the model's output and is what sent this campaign chasing a prompt fix.

KEEP: add `...transcriptFields("response", replyText)` to the retry record at fanout.ts:680, which today journals only `{attempt, errors}` while both terminal branches carry the text. That omission is why settling this needed a sqlite read.

DROP THE NO-RETRY, which is what both candidates were refuted on. Measured across both journals: 8 lens first attempts hit the 1,800 s timeout and SIX recovered on the very next attempt (step7 seq 124/215/223/239, step8 seq 105/106) — including the two c828 lenses this whole diagnosis is built on, one of which returned a real `wave-dep-contradiction` major. And conductor/adapter/tools.ts:2959-2971 turns any lens with no value into a whole-stage abort ('a missing one aborts the review'), observed at step7 seq 153 followed by a fresh 4-lens re-dispatch. So finishing immediately with `error.kind: "env"` converts three completed plan-review waves into three hard aborts and deletes 17,024 tokens of real lens output from c828 alone.

ADD, revealed by the refutation: on a provider-timeout classification, re-prompt with the ORIGINAL brief — `briefWithShape(job)` — not `appendErrors(...)`, which appends "Your previous reply did not satisfy the required Findings schema. Correct these validation errors" after a transport failure. That is false feedback about a reply that was never delivered, and it also grows the prompt that just timed out. If a budget must be bounded, bound provider errors at 2 attempts (which recovers all six observed successes and caps the one 3x1800 s case at 60 min) — and justify it on that evidence, never on the candidate's false claim that a re-prompt has never succeeded.

Predicted GPU effect: ZERO. Score it as instrumentation. Rank 1 largely removes the underlying timeouts anyway; this is what makes the next one legible in the journal instead of requiring a database.

**Sites:**

- `conductor/adapter/fanout.ts:111`
- `conductor/adapter/fanout.ts:167-178`
- `conductor/adapter/fanout.ts:640-664`
- `conductor/adapter/fanout.ts:679-683`
- `conductor/adapter/fanout.ts:405-412`
- `conductor/tests/fixtures/fake-sdk.ts:51`

**Measurement:**

Pure unit test, seconds, zero model calls. Stub `client.session.prompt` to resolve `{data: {info: {error: {name: "UnknownError", data: {message: "The operation timed out."}}}, parts: [{type: "step-start"}, {type: "reasoning", text: "..."}]}}`. Assert: the journalled reason is "provider-timeout" and NOT "schema-invalid"; the response text is present on the retry record; the error message is carried; and session.prompt was called MORE than once — the inverse of the original candidate's assertion, because that assertion pins the behaviour the field data shows is destructive. Widen conductor/tests/fixtures/fake-sdk.ts:51, which types `info` WITHOUT `error`, before the test can be written. Add a planReviewRound-level test pinning that a lens recovered on attempt 2 still yields Findings and does not abort the round. Then on the next run: no subsession record may pair reason="schema-invalid" with an empty `response`.

**Why it survived:** Both parent candidates were refuted, but every one of the six skeptics that examined them independently reached the same split: the diagnosis is airtight and free, the remedy is backwards. I re-confirmed the diagnostic half from the ledger — 11 rows with status 200, upstreamMs 1,800,018-1,804,979 and promptTokens/completionTokens/timings all null, a 1:1 match with the 11 EOF events — and the router's own null-token rows are still in c828 today (I printed them). The graft costs one branch and one field, cannot regress behaviour, and converts the campaign's most expensive misdiagnosis into a self-naming journal line.

### Rank 5 — An eight-day-old router config governed the run, because serve.py exec's into llama-server before it writes one

*id: `regenerate-router-config` · needs a full cell to score: no*

This is what survives of both width candidates (`width-equals-slots`, `fanout-width-equals-served-slots`), both refuted. The refutations are correct and I accept them: llama-server has 3 slots and MAX CONCURRENCY IN THE ENTIRE 197-MINUTE RUN WAS 3, NEVER 4 — the plan-review wave dispatched 4 jobs but only three ever got slots. So clamping fan-out width to the served slot count changes the number of concurrent decoders from 3 to 3, and the predicted per-slot rate improvement (4.96 -> 7.4-9.3 tok/s) is arithmetic on a regime that never existed. Measured rates: 5.82-5.94 tok/s at 3-wide, 8.07 at 2-wide, 13.3-14.4 at 1-wide.

WHAT IS REAL is the provenance defect the skeptics found while refuting it. scripts/run_and_watch.py invokes serve.py with `--no-shell`; serve.py `os.execv`s into llama-server BEFORE reaching `write_router_config`; run_and_watch then starts the router straight off `.data/configs/conductor-router.json`, whose mtime is 2026-08-20 — eight days before the run. That file carries `maxInflightPerModel: 6` and `queueTimeoutMs: 600000`, while `derive_slots(3)` would have written 3 and 7,200,000. So the router admitted 6 against 3 slots, the 4th lens queued invisibly inside llama-server, and router/router.hpp:115 `kRelayTimeoutSeconds = 600` 502'd it twice at upstreamMs 600,001 and 600,003 with queueWaitMs 0 and every token field null. I confirmed both rows are still in the ledger.

CHANGE: have run_and_watch call the config writer with SERVE_SLOTS before starting the router supervisor, AND add a preflight that reads back the file the supervisor was actually handed and refuses to start when `admission.maxInflightPerModel != SERVE_SLOTS`. The check must read the file the running router loaded, not module constants — scripts/test_conductor_wiring.py:423 already pins the constants and passed while the live router ran at 6.

Also correct scripts/conductor_wiring.py:96-102, whose comment asserts the 600 s relay timeout "has never fired on healthy work". It fired twice, to within 3 ms, on a lens that then succeeded in 353 s. Leaving that premise standing invites the next reader to trust a backstop that has already failed.

HONEST EFFECT: ~24 seconds of aborted prefill recovered and two phantom llama-server tasks removed. ZERO wall-clock saving (the 502'd lens finished 25.6 min inside the shadow of its slower siblings and was never on the critical path). ZERO decode-rate change. What it buys is that a queued request is visible where `queueWaitMs` is measured instead of invisible inside llama-server, and that a stale file on disk can no longer silently govern an experiment. Sell it as observability and provenance, never as throughput.

**Sites:**

- `scripts/run_and_watch.py:505-560`
- `scripts/serve.py:696-740`
- `scripts/conductor_wiring.py:96-102`
- `scripts/conductor_wiring.py:150-158`
- `scripts/conductor_wiring.py:254-266`
- `.data/configs/conductor-router.json`

**Measurement:**

(a) Static, seconds: a preflight assertion in the python leg that the router config file handed to the supervisor has `admission.maxInflightPerModel == SERVE_SLOTS` and `queueTimeoutMs == ROUTER_QUEUE_TIMEOUT_MS`, plus a stamped provenance line (config sha + mtime) in the run's own preflight output.
(b) On the next run: zero reviewer ledger rows with status 502; and if a request does queue, it carries `queueWaitMs > 0` instead of 0. Do NOT use "zero 502s" as evidence that anything about throughput improved — the two are unrelated, and a skeptic showed that criterion passes while the real defect (the 1,800 s aborts) stands untouched.

**Why it survived:** The candidates it came from were refuted on their throughput claim, which I accept — three skeptics independently parsed server.log launch/release pairs and found max concurrency 3, never 4. But two of them found the same unrelated and genuinely dangerous fact while doing it: the served router configuration was never regenerated for the campaign and an eight-day-old file governed the run. That is the same class as the copied-forward cell JSONs and the mid-run doctrine edit — a file on disk silently deciding an experiment — and this repository has already lost measurements to that class twice. Cheap, static, and it makes an entire category of silent drift impossible.

### Rank 6 — The live console reports a PRIOR run's decode in full, which is what produced the phantom 45,812-token reasoning gap

*id: `window-the-console-ledger-join` · needs a full cell to score: no*

Merges `fix-reported-token-totals` (survived) and `ledger-is-the-token-truth` (refuted), with the corrections that matter.

THE NUMBER IS REAL: the console reports the conductor arm at 37,053 completion tokens; I summed the 46 role-tagged ledger rows in the run's window and got 82,865, and 16,685 + 21,833 + 82,865 = 121,383 — llama-server's own total, to the token. So the "45,812 reasoning tokens plus discarded replies" reading in the campaign brief is 82,865 - 37,053, arithmetic on a broken counter. There is no accounting gap; the per-role delta against llama-server's predicted_n is +0 for all six roles.

THE CAUSE IS NOT THE POSITIONAL ZIP. A skeptic showed the sum within a role is permutation-invariant when the counts match, and they match exactly (16/2/4/4/8/12 turns against 16/2/4/4/8/12 rows). The real causes are two: conductor/tools/observe.ts hands joinLedger the ENTIRE unwindowed .data/router/metrics.jsonl (thousands of rows across every run), and `group` is the work-root path, which is byte-identical across runs — so each role's bucket is the union of every historical run and the head-truncation takes the OLDEST N. The 16 orchestrator rows joined are stamped 2026-08-27, a day before the run. Turn #2 renders 10700/701 (a 2026-08-27T06:00:14 row) where the run's own row is 10700/305.

CHANGE: window the ledger by the run's own first/last journal timestamp (NOT by conductor_bench's `ledgerStartLine` — I verified that is a driver-trace field written only when a cell SCORES, and step8's diagnostics hold baseline and doctrine only, precisely because the conductor cell never finished; during a live run, which observe.ts's header names as the intended use, it does not exist at all). Drop or repair the `group` filter: 12 of the 46 conductor rows carry group=null, including ALL EIGHT reviewer rows, so windowing while keeping the filter makes the number WORSE (22,978). Compute the totals as a direct sum over the windowed rows so an unjoinable turn cannot silently subtract, and render the four null-token rows as unknown rather than zero.

DROP three predicted effects that are causally impossible from this site, all verified: `mismatches 10 -> 0` (mismatch is recommended-tool vs actual-tool, computed before joinLedger and reading no ledger field — the 10 marks are real doctrine-adherence signal and zeroing them would destroy it); `COMPACTION 80m06s -> 60m00s` (compactionSuspected is generationMs >= 30 s from journal timestamps, also computed before the join); and `turns 29 -> 46` (the console already reports and renders 46; the 29 is scripts/run_and_watch.py's own display trim).

DEMOTE THE PRIORITY CLAIM. The candidate said this must land first because it scores the others. I checked: it does not. scripts/conductor_bench.py:2486 `summarize_ledger_window`, called at :2271, is already an exact direct sum over the cell's own ledger window that sets `partial` on any null-token row — so every SCORED cell JSON is correct today. ratios.py and arm_report.py take tokens from opencode.db instead. This is a live-display fix. It still matters, because the display is what a watching agent reads to decide whether to stop a run, and because it already put a false finding into a campaign brief.

**Sites:**

- `conductor/tools/observation.ts:1266-1302`
- `conductor/tools/observation.ts:1003-1012`
- `conductor/tools/observe.ts:431-435`
- `conductor/adapter/inject.ts:355-375`
- `scripts/epoch_review.py:497-516`
- `scripts/epoch_review.py:792`
- `scripts/epoch_review.py:848`

**Measurement:**

Entirely offline against data already on disk, seconds, zero model calls. `node /Users/sal/development/vorlac/llama-harness/conductor/tools/observe.ts .data/benchmark/watch/step8-context-128k/run-r-20260828-c828 --console | head -4` prints `tokens 841355 in / 37053 out` today; after the change it must read 82,865 out and must equal the sum of completionTokens over the 46 role-tagged rows in the window. Use `--console`, NOT `--json` — I ran `--json` and its keys are {runId, snapshot, signals, crossed, thresholds} with no token totals, so the candidate's stated command cannot evaluate its own criterion. Assert per-role: orchestrator 7,089 / mechanical 455 / skeptic 1,315 / planner 34,178 / reviewer 23,939 / testWriter 15,889. Add a regression fixture pinning that a ledger containing a prior run's rows under the same group path cannot contribute to this run's totals — that is the actual defect and nothing tests it. Do NOT use "partialRoles is empty" as a confirmation: it is already empty in the broken state. Separately, regenerate INDEX.md keyed on startedIso so step5/6/7's grid2048 rows no longer read as fresh PASS measurements.

**Why it survived:** It survived skepticism on the number (which I reproduced from both ends) and was correctly demoted on the priority claim (which I disproved myself by reading summarize_ledger_window). It stays on the list not for GPU savings — it has none — but because it is the instrument the loop's watch step reads, and because the same broken join already manufactured two false findings that reached a campaign brief: the 45,812-token reasoning gap, and the '20,243-32,388 prompt tokens' premise in the D-truncate write-up, which are step7 rows borrowed onto step8 turns.

### Rank 7 — Detect a stalled run from the router ledger, outside the plugin — the only vantage that can see a blocked permission prompt

*id: `ledger-stall-detector` · needs a full cell to score: no*

This is the change the refutation of `no-progress-deadline` revealed. That candidate proposed a ~20-minute silence deadline inside conductor/adapter/fanout.ts. Two of three skeptics refuted it with the same measurement, and it is decisive: in c828 the healthy maxima are a 30.0-minute gap between plugin-observable events (twice, on the two reviewer lenses that SUCCEEDED on retry) and a 23.2-minute planner turn; across the three most recent conductor cells, 21 of 220 successful sub-session requests were single generations longer than 20 minutes. So a 20-minute silence deadline kills roughly one in ten healthy dispatches, preferentially in planner and reviewer — 70% of the arm's decode. Worse, a fanout watchdog fire is TERMINAL (`if (done) return; // the watchdog already resolved this job` sits inside the attempt loop), so it would have destroyed the two lens retries that actually completed the c828 plan-review wave. And the progress signal it needs is unverified: the plugin routes exactly `session.idle`, `message.updated` (filtered to completed turns) and `permission.asked`; no streaming part event is verified on this build, so if the stamp never lands every sub-session reads as silent and dies.

THE CORRECT INSTRUMENT IS OUTSIDE THE PLUGIN. The stall's signature is not silence in the plugin's event stream — it is NO HTTP REQUEST IN FLIGHT AT ALL. I confirmed it: the last .data/router/metrics.jsonl row in the c828 window is 09:01:54.360Z, the last journal record is the same second, and the console's final frame is 10:20:37Z. Nothing after. The router's own 600 s per-read timeout is structurally blind to this because there is no request to time out, and llama-server logged no task. But the LEDGER sees it perfectly: a run with no completed request for N minutes is stalled, whatever the cause — a blocked `question`, a blocked `edit: "ask"`, opencode's base `doom_loop * -> ask` or `external_directory * -> ask` (which the same testWriter's /tmp write would have hit), or any of the 24 non-`question` watchdog deaths already in the wiring comment's table.

CHANGE: a no-request-in-flight detector in the watcher/driver, keyed off the ledger's `completedAt` plus the journal's last timestamp, not a timer in fanout. Threshold sized ABOVE the measured healthy maximum, not from a round number: the largest healthy single generation on record is 26.9 minutes (reviewer, 5,615 tokens at 3.48 tok/s), so nothing below ~40-45 minutes is safe, and the detector should raise an alarm for the operator/loop rather than abort anything. It costs no GPU, cannot kill healthy work, and it is the one guard that would have caught this in minutes instead of 78.7.

SEPARATELY, land the observability the plugin-side version would need before anyone builds it: journal a record on the silent bail at conductor/adapter/continuation.ts:1768 (today it returns with no trace on a payload-shape mismatch, which is exactly how the permission handler died unnoticed across two full runs), and add a no-op event tap that journals `{type, sessionID}` for every bus event received. One conductor cell with that tap produces the first direct measurement of what events exist and at what cadence for a no-tool-call reviewer lens — which is the distribution any future liveness timer must be calibrated against.

Do NOT reflexively shorten SUB_SESSION_TIMEOUT_MS. conductor_wiring.py:100-106 set the 6-hour values deliberately so the tail becomes observable; trading that away replaces one measurement with another.

**Sites:**

- `scripts/run_and_watch.py:700-760`
- `conductor/tools/observation.ts:900-1015`
- `conductor/adapter/continuation.ts:1765-1789`
- `conductor/adapter/fanout.ts:519-546`
- `scripts/conductor_wiring.py:96-137`

**Measurement:**

Offline replay, seconds, against evidence already on disk: run the detector over c828's ledger and journal and assert it fires between 09:41Z and 09:46Z (40-45 min after the last completed request at 09:01:54Z) and NOT before — and assert it does not fire anywhere in step6-grid2048-8h, which ran the full 480 minutes at 99.2% request-busy with no stall. Then assert it fires zero times across the healthy portions of all five conductor journals on disk. That is a real false-positive test against real data, which is exactly what the plugin-side version could not have.

**Why it survived:** The candidate it replaces was refuted twice on measurement — a 20-minute silence deadline would have killed 3 of 8 healthy sub-sessions in the very run it was derived from, and its fire is terminal so it would have destroyed the two retries that completed the plan-review wave. But the underlying problem is real and the loop cannot run without solving it: an autonomous loop that watches a benchmark needs a stall signal, and the naive one is actively destructive. The ledger-side detector is the version that is calibratable against data already on disk, cannot kill healthy work because it aborts nothing, and sees the one failure class the router's own liveness guard is structurally blind to.

## The loop design

THE LOOP'S CENTRAL CONSTRAINT, stated first because it determines everything else: this repository cannot measure a cost effect and verify a mechanism at the same cadence. A mechanism verdict is deterministic — did the cache_n=0 rows disappear, did reasoning tokens fall, did the journal stop saying "schema-invalid" — and n=1 settles it. A cost or quality verdict is stochastic against a measured baseline wall CV of 23.6-34%, which puts the minimum detectable effect at 54-78% at n=3 and 34-48% at n=8. So the loop runs a FAST MECHANISM CYCLE continuously and batches a SLOW COST CYCLE rarely, and it must never let the fast cycle emit a cost claim.

=== STATE THAT PERSISTS BETWEEN ITERATIONS ===

Four artifacts, all append-only, all outside the tree the runs touch.

(1) A change register, one JSONL row per attempted change, written BEFORE the run (pre-registration is the whole point): {changeId, gitSha of the conductor tree at spawn, patch or diff hash, class ∈ {plugin-only, doctrine, served-config, driver}, hypothesis, predictedEffect with a number, the falsifier that would refute it, the measurement command, and — filled in after — measured, verdict ∈ {kept, reverted, inconclusive}, and why. A row with no falsifier is not runnable; that is a hard gate, because five of the eleven candidates reviewed here died on a predicted effect nobody had written down as falsifiable.

(2) A served-config fingerprint: {SERVE_SLOTS, SERVE_PER_SLOT_CONTEXT, PROMPT_CACHE_RAM_MIB, model file sha, llama.cpp build sha from .data/tools/.build-stamp.json, sha256 of .data/configs/conductor-router.json, sha256 of .data/configs/opencode.json}. Every cell JSON is tagged with it. Two cells with different fingerprints are NOT comparable, full stop, and the loop refuses to place them in the same table. This is the guard that the 65536→131072 change needed and did not have.

(3) A baseline median per fingerprint: the calibration cells. Today CALIBRATION_REPS = 0 and there are none — the only n=3 anywhere in the tree is step1-euler001's baseline. The loop's very first act must be to produce one, because every ratio the repository's own protocol requires (docs/plans/2026-08-25-relative-metrics-and-stall-deadlines.md: the denominator is the median of that epoch's calibration repetitions, never a single sample) is currently undefined.

(4) The epoch directories themselves, one per iteration, NEVER reused and never written into by hand. The presence of a cell JSON IS conductor_bench's resume ledger, so a directory is the loop's memory of what actually ran — provided nothing was copied into it.

The loop must NOT use docs/build/epochs/INDEX.md as its memory of what it already tried without de-duplicating on startedIso: four epochs currently render one baseline measurement as four independent PASS rows.

=== THE CYCLE ===

PHASE 0 — PREFLIGHT (5-10 minutes, machine must be quiet)
Run the gate (`bash scripts/test-conductor.sh`, last line must be `GATE PASS`) and `bash scripts/conductor-gate.sh`. Compute the served-config fingerprint and compare to the register. Regenerate .data/configs/conductor-router.json from SERVE_SLOTS and assert `admission.maxInflightPerModel == SERVE_SLOTS` by reading back the file the supervisor will be handed — not the module constants, which already passed while a stale file served 6. Assert RESULTS_DIR is new and empty. Run `python3 scripts/conductor_bench.py --plan-only ...` and assert the enumerated cell list matches the intended arms and reps. DECISION: any mismatch aborts before a model starts.

PHASE 1 — RUN (20 minutes to 8 hours; see pricing)
Launch by editing the CONFIG constants in scripts/run_and_watch.py and running it with no arguments, or — better for a loop — issue the argv-driven command it assembles directly: `caffeinate -is /usr/bin/python3 scripts/conductor_bench.py --manifest <M> --reps <N> --results-dir <R> [--calibration-reps N] [--task ID]`. That form is fully parameterizable and keeps the loop out of a constants file it would otherwise have to rewrite between iterations.

PHASE 2 — WATCH (continuous, seconds per poll)
Poll two things and nothing else. (a) `node conductor/tools/observe.ts <run-dir> --console`, which is read-only by construction and safe against a live run — but only after rank 6 lands, because today its token counter reports a prior run's decode. (b) The router ledger tail: last `completedAt`, and the running per-role sum, which reconciles to llama-server's predicted_n to the token and is the only trustworthy live cost signal that exists right now.
DECISION POINTS, both automatic:
  - STALL: no completed ledger row for ≥ 45 minutes (sized above the measured healthy maximum of a 26.9-minute single generation and a 30.0-minute inter-event gap, not from a round number). Action: snapshot, kill, record as a stall with its journal tail — do not silently retry.
  - BUDGET: the driver already enforces runTimeoutSec; the loop only records it.
The loop does NOT decide mid-run that it has "seen something improvable" and stop to fix it. It watches, records, and lets the run finish or stall. Stopping to edit is the single most expensive mistake available here — see the doNot list.

PHASE 3 — TRIAGE (5-15 minutes, all offline)
Run `python3 scripts/check_campaign.py <results_dir>` (exit 0 = nothing fired, 1 = a cell worth opening, and it prints which checks it could NOT run so "clean" is distinguishable from "skipped"). Then produce the per-role ledger table — n, prompt, completion, prefill minutes, decode minutes, cache_n=0 count — for the run's window. That table is the loop's decision surface. It is exact, it is cheap, and it is what let me settle four disputed questions in this synthesis in minutes. Diff it against the previous iteration's table for the same fingerprint. Then `python3 scripts/prior_art.py <mechanism>` before recording anything as new, searching by MECHANISM not symptom — its own header says a negative on the symptom is a weak negative.

PHASE 4 — CHANGE (minutes to hours)
ONE change per iteration, drawn from the ranked list, classified by blast radius:
  - plugin-only (ranks 1,2,3,4,6): conductor/ under the plugin's import graph. Baseline and doctrine load no plugin, so no flat-arm cell is invalidated and none needs re-running. This is the class the loop may run autonomously.
  - driver/observability (ranks 5,7): scripts/ and tools. Also autonomous.
  - doctrine (conductor/doctrine/*.md): NOT autonomous. Those files ARE the doctrine arm's entire system prompt, concatenated verbatim; editing one between two doctrine cells is what confounded the 65536-vs-131072 doctrine comparison.
  - served-config: NOT autonomous. It re-prices every previously scored cell of every arm.
The change must be expressible as a test that is RED before and GREEN after. If it cannot be, it does not proceed — that rule alone would have killed the no-retry clause, the width clamp, and the cache-ram raise.

PHASE 5 — MECHANISM VERDICT (seconds to ~2 hours, no benchmark cell for most)
Run the unit tests, then the cheap probes: the two-request cache_n probe (rank 2), the eight-request paired lens replay (rank 1), the 5-minute headless question probe (rank 3), the offline stall-detector replay (rank 7), the offline console recomputation (rank 6). DECISION: if the falsifier fires, revert and record. If the mechanism confirms, proceed — but do NOT record a cost claim.

PHASE 6 — COST/QUALITY VERDICT (hours to days; batched)
Only when a batch of confirmed mechanisms has accumulated, or when a single change is expected to move cost by more than the MDE. Run the full arm set at the reps the register says are needed. Normalize with `python3 scripts/ratios.py <results_dir>` (it divides by the median of THIS epoch's successful baseline reps, refuses to divide by a failed baseline, and flags a single-sample denominator DEGRADED). Score quality with `scripts/judge_quality.py` on a quiet machine, never in the same window as a benchmark, and only after its calibration pass. DECISION: keep only if the effect exceeds the MDE at the reps run AND quality did not regress.

PHASE 7 — RECORD (10-30 minutes)
`python3 scripts/epoch_review.py <watch_root> --since <epoch-dir>` (use --since; without it, it unconditionally re-renders all 22 epochs under a 1800-second timeout and swallows its own failure). Write the register row's verdict. Append the defect to docs/build/artifacts/14.2-arm-campaign.md with its pre-registered hypothesis alongside the measured result, including the ones that were refuted — the refutations in this synthesis were worth more than several of the candidates.

=== WHAT STOPS THE LOOP AND ESCALATES TO A HUMAN ===
1. Any served-config change, any doctrine-pack change, or any change to CALIBRATION_REPS or RESULTS_DIR. These re-price prior cells or redefine the denominator.
2. A quality-vs-cost trade. Rank 1 is exactly this: a reasoning budget can buy a cheaper plan that is worse, and no cost metric in this repository can see that. The planner rung specifically must be a human decision.
3. Inverting a test that encodes design intent rather than fixing a bug — e.g. fragment.test.ts:145-158, which asserts "grant question so the plugin can refuse it". (For that one the escalation is now cheap to resolve: the refusal path is structurally unreachable on 1.18.15, so inverting it is a correction. But the loop must escalate rather than decide that itself.)
4. A predicted effect below the MDE at the reps affordable. The loop must compute 3.96·CV/√n before spending 8 hours, and say so out loud when the answer is "this run cannot detect this".
5. Two consecutive iterations with no measurable improvement, or any iteration where the conductor arm again produces no scored cell. Five consecutive non-terminating cells on one task is a standing condition, not a run-to-run event, and a loop that keeps re-running into it is burning days.
6. Any disagreement between two instruments that should agree — the ledger versus llama-server's predicted_n, the ledger versus a cell JSON, the console versus either. Those deltas are +0 today; a non-zero one means an instrument moved and every downstream number is suspect.

=== SECONDS VERSUS HOURS ===
Seconds: node unit tests for one file; the per-role ledger arithmetic; check_campaign; the offline replays for ranks 4, 6, 7; observe --console.
Minutes: the full gate (~2,056 tests plus tsc, bun, schema export, python); --plan-only enumeration; the headless question probe (~5 min); the cache_n probe (~10 min).
Tens of minutes to ~2 hours: the paired lens replay for rank 1; epoch_review over one epoch; one baseline cell (20.2 min) or doctrine cell (30.6 min).
Hours: one conductor cell — 480-minute manifest budget, and it has never terminated on this task in five attempts.
Days: any n≥8 three-arm comparison.


## What one iteration costs

All figures measured on this host at 3 slots × 131072 on grid2048-headless-py, and cross-checked against llama-server's own print_timing lines.

PER-CELL WALL CLOCK (measured):
  baseline   20.2 min   (1,213,698 ms, 16,685 completion tokens)
  doctrine   30.6 min   (1,834,ntimes ms, 21,833 completion tokens)
  conductor  480 min    — charged at the manifest budget, bench/corpus-games.json runTimeoutSec 28800 for T2. It has produced 0 terminating cells on this task in 5 attempts (60, 60, 480 min timeouts and two runs with no cell at all), so this is not a pessimistic charge, it is the observed one.

FIXED OVERHEAD PER ITERATION:
  gate on a quiet machine                    ~5 min
  preflight (fingerprint, router regen,
    plan-only enumeration)                   ~5 min
  triage (check_campaign + ledger table
    + prior_art)                            ~10 min
  epoch_review --since + register write   ~10-30 min
  ------------------------------------------------
  subtotal                                36-50 min  ≈ 0.6-0.9 h

LANE A — MECHANISM ITERATION, plugin-only change, no benchmark cell.
  gate 5 + unit tests ~1 + cheap probe 10-120 min + record 10 = 26 to 136 minutes.
  0.4 to 2.3 hours. This is the loop's normal cadence, and ranks 2, 3, 4, 5, 6 and 7 all fit inside it.

LANE B — ONE CONDUCTOR DATUM, before and after.
  2 × 480 min of cell + 0.9 h overhead × 2 = 960 + 108 = 1,068 min = 17.8 hours.
  What it buys: a MECHANISM verdict (did the cache_n=0 rows vanish, did reasoning tokens fall) — deterministic, so n=1 is legitimate.
  What it does NOT buy: any arm claim. n=1 against n=1 is what the register forbids by name ("The bench runs --reps 1. Every cross-epoch token comparison in this register is n=1 against n=1.").

LANE C — AN HONEST COST VERDICT. Two configurations × n reps, arms run strictly sequentially (the server was busy 208 of ~210 minutes; there is no parallelism to reclaim, and decode time IS the wall clock: baseline 16,685/12.3 = 22.6 min of decode against a 20.2 min wall, doctrine 21,833/12.3 = 29.6 against 30.6).
  Flat arms only, n=3:  (20.2 + 30.6) × 3 × 2 = 304.8 min =  5.1 h  → MDE 54-78%
  Flat arms only, n=8:  (20.2 + 30.6) × 8 × 2 = 812.8 min = 13.5 h  → MDE 34-48%
  All three arms, n=3:  (20.2 + 30.6 + 480) × 3 × 2 = 3,184.8 min = 53.1 h
  All three arms, n=8:  (20.2 + 30.6 + 480) × 8 × 2 = 8,492.8 min = 141.5 h = 5.9 days
  Plus overhead: add ~0.9 h per launch, and epoch_review at up to 30 min unconditional.

WHY n=8 AND NOT n=3. Required reps at 80% power, α=0.05 two-sided, n = (3.96·CV/effect)². Using the repository's own measured baseline CV (23.6% same-epoch on euler-001-py at n=3; ~34% cross-epoch on slugify-ts): baseline's observed −50.0% wall needs 4-8 reps; its −40.4% completion needs 11-29; doctrine's −24.4% wall needs 15-31; doctrine's −20.9% completion needs 38-105. The campaign's default of 3 reps cannot detect ANY of the four effects it last reported. Minimum detectable effect at n=3 is 54-78%, larger than three of those four.

GPU AND TOKEN COST OF ONE FULL THREE-ARM ITERATION.
  Decode: baseline 16,685 + doctrine 21,833 + conductor ≈ 307,031 (epoch 20's measured full-budget figure) ≈ 345,500 completion tokens.
  Prefill: ~1.5-2.5 M tokens at the measured 149 tok/s.
  At the measured 12.3 tok/s decode and 149 tok/s prefill the machine is saturated for the whole window — 208 minutes of slot-work spread over 3 slots inside a 197.1-minute busy span with no gap longer than 25 s.
  With rank 1 landed, the conductor arm's decode falls ~48% (99,966 → ~51,638 measured on the c828 shape), so a three-arm iteration drops toward ~190,000 decoded tokens — which is the second reason to rank it first: it shortens every subsequent iteration.

AGENT TOKEN COST. Budget 50-150k per iteration if the loop reads only the per-role ledger table, the journal tail, check_campaign's output and the console header. It rises past 300k the moment it starts reading transcripts or opencode.db — which it should do only on triage of an actual defect, not routinely.

THE HONEST BOTTOM LINE. One iteration that can KEEP OR REVERT A MECHANISM costs 0.4-2.3 hours and is the loop's real cadence. One iteration that can keep or revert a COST claim costs 13.5 hours for the flat arms alone and 5.9 days with the conductor arm included — and until a conductor cell terminates at all, the conductor half of that spend buys a timeout rather than a measurement. Making the conductor arm terminate is a precondition for measuring it, not an optimization of the measurement.


## Do not

1. Never copy or move a scored cell JSON into a results directory. conductor_bench reuses any cell whose result file already exists and does not even create the work tree — that is the documented resume mechanism, and it has already been repurposed as a skip. The grid2048 baseline and doctrine cells in step4, step5, step6 and step7 are ONE measurement (md5 d35551a5e20b8caa87d6ceeaf7532c34 and 4a99262f2ec44f4cf93e7ab068d065f5, startedIso 2026-08-27T04:37:12Z) with four sets of inodes and mtimes, and docs/build/epochs/INDEX.md renders them as four independent PASS rows. run_and_watch's own CONFIG comment calls RESULTS_DIR 'THE MOST CONSEQUENTIAL SETTING IN THE FILE' and records an earlier run that 'reported three arms while only one had actually executed'.

2. Never edit anything under conductor/ while a run is in flight. Every generated conductor.json names the plugin by ABSOLUTE PATH into the live checkout — not a copy, not a pinned revision — so a mid-run edit rewrites the experiment retroactively and the run's own artifacts will not say so.

3. Never edit conductor/doctrine/*.md between two cells you intend to compare. conductor_bench.build_doctrine_prompt concatenates every file in that directory verbatim as the doctrine arm's ENTIRE system prompt. plan.md was modified at 2026-08-27T14:33 — after the 65536 doctrine cell and before the 131072 one — so that arm's before/after is confounded by a prompt change, not just a window change.

4. Never run scripts/test-conductor.sh, scripts/conductor-gate.sh or scripts/judge_quality.py against a live campaign. The gate boots its own `opencode serve` in live-inject.test.ts and times out on /config when three opencode processes are already contending for the 27B — measured as tests=2056 pass=2048 fail=1 cancelled=7 with 'opencode serve /config never became ready: TimeoutError'. Serialize gate → run → analyze; never overlap them.

5. Never run scripts/run_and_watch.py to inspect anything. It parses no argv at all — there is no argparse and no sys.argv anywhere in the file — so `--help` launches a real multi-hour benchmark that saturates the machine.

6. Never change the served configuration (slots, per-slot context, --cache-ram, any --reasoning-budget flag) and then compare against previously scored cells. One llama-server serves all three arms sequentially. The 65536→131072 change alone moved baseline wall 40.5→20.2 min and completion 27,997→16,685; a server-wide reasoning clamp would have moved conductor ~6-19x more than the flat arms. If the fingerprint changes, every prior cell is void and the baseline must be re-measured.

7. Never report an n=1 before/after as an arm result. Measured baseline CV is 23.6% same-epoch and ~34% cross-epoch, with a recorded 10.4x token swing on an identical arm and identical inputs. MDE at n=3 is 54-78%. CALIBRATION_REPS is 0 in the driver, so no epoch from step4 through step8 has a calibration denominator at all, and the repository's own separability test (within_noise) is degenerate at reps=1 and says nothing about wall clock or tokens at any n.

8. Never read .data/router/metrics.jsonl unwindowed, and never join it positionally on `group`. The work-root path is byte-identical across runs, so a role's bucket is the union of every historical run and the head truncation serves the OLDEST rows — that is how a prior day's decode was reported in full as this run's total. And 12 of the 46 conductor rows in the c828 window carry group=null, including all eight reviewer rows, so filtering on group drops 60% of the conductor decode. Window by the run's own journal timestamps and sum directly.

9. Never treat a guard firing as evidence the guard is right, and never treat a wire-notes claim as universal without its client/agent qualifier. wire-notes 20.1 asserts by deepEqual that `question` is not offered — true for the non-cli fixture client, false for `opencode run`, which is what every benchmark cell uses. Reproduce the guard's computation before recording a verdict.

10. Never arm a silence or wall-clock watchdog from a round number, and never make one terminal. In the c828 cell the healthy maxima are a 30.0-minute gap between plugin-observable events (twice, on lenses that then SUCCEEDED) and a 26.9-minute single generation; 21 of 220 successful sub-session requests across three cells ran longer than 20 minutes. A 20-minute silence deadline kills roughly one dispatch in ten, preferentially in planner and reviewer — 70% of the arm's decode — and because fanout's watchdog resolves the job before the retry loop can run, it would have destroyed the two lens retries that actually completed the plan-review wave.

11. Never fix a stage failure by removing a retry. Six of eight lenses that hit the 1,800 s provider timeout returned valid Findings on the very next attempt, and conductor/adapter/tools.ts turns any lens with no value into a whole-stage abort ('a missing one aborts the review'), observed once followed by a fresh four-lens re-dispatch. A no-retry rule converts three completed waves into three hard aborts and deletes 17,024 tokens of real lens output from one cell.

12. Never restore a file you mutated with `git checkout`. The campaign tree is uncommitted — currently 16 modified files and two untracked epoch directories — so a checkout destroys work that has no other copy. Undo with the inverse edit.

13. Never let docs/build/epochs/INDEX.md stand as the loop's record of what it already tried without de-duplicating on startedIso, and never call scripts/arm_report.py on a games-corpus epoch without an explicit --manifest: its default is bench/conductor-tasks.json, which does not contain grid2048-headless-py, so it renders an empty report rather than an error.

14. Never let a change proceed that cannot be expressed as a test which is red before and green after. Every candidate refuted in this review failed on a predicted effect nobody had written down as falsifiable in advance — a wall-clock saving that was fully overlapped, a rate improvement in a concurrency regime that never occurred, a 35% cell reduction measured between two mid-execution timestamps of a run the operator killed.

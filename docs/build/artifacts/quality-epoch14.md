# Quality — blind paired comparison

Ordinal. A win means the implementation was scored higher in BOTH
presentation orders across every repetition; anything less is a tie.
No ratio appears here: rubric scores have no true zero.

## Judge calibration

calibrated: 9/9 on known-answer cases

- known-answer accuracy: 9/9 (100%), stated floor 75%
- length bias: better-is-longer 100% (5 cases) vs better-is-shorter 100% (4 cases)
- identical-pair control: clean
- control detail: deadcode-unused-scaffold 6/6 runs scored two identical trees equally; decomposition-one-long-blob 6/6 runs scored two identical trees equally; large-deadcode-unused-module 6/6 runs scored two identical trees equally; large-structure-ignores-the-pinned-clock 6/6 runs scored two identical trees equally; large-testquality-vacuous-suite 4/4 runs scored two identical trees equally; overbuilding-strategy-registry 6/6 runs scored two identical trees equally; structure-drops-a-named-case 2/2 runs scored two identical trees equally; testquality-asserts-nothing 4/4 runs scored two identical trees equally; testquality-restates-the-implementation 4/4 runs scored two identical trees equally

## `clock-inject-py`

| pair | criterion | verdict | why |
|---|---|---|---|
| baseline vs doctrine | structure | _NO VERDICT_ | 2 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | decomposition | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs doctrine | testQuality | **doctrine** | won every one of 6 runs in both presentation orders |
| baseline vs doctrine | deadCode | _NO VERDICT_ | 1 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | overBuilding | _NO VERDICT_ | 1 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |

Blinding notes for this task:
- 2 further archived repetition(s) of this task were not judged: llamacpp-qwen3.8-27b/none/baseline/clock-inject-py/r2, llamacpp-qwen3.8-27b/none/baseline/clock-inject-py/r3

## `euler-cli-py`

| pair | criterion | verdict | why |
|---|---|---|---|
| baseline vs doctrine | structure | _NO VERDICT_ | 6 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | decomposition | _NO VERDICT_ | 6 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | testQuality | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs doctrine | deadCode | _NO VERDICT_ | 1 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | overBuilding | **baseline** | won every one of 6 runs in both presentation orders |
| baseline vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |

Blinding notes for this task:
- 2 further archived repetition(s) of this task were not judged: llamacpp-qwen3.8-27b/none/baseline/euler-cli-py/r2, llamacpp-qwen3.8-27b/none/baseline/euler-cli-py/r3

## `logfmt-lenses-ts`

| pair | criterion | verdict | why |
|---|---|---|---|
| baseline vs doctrine | structure | _NO VERDICT_ | 4 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | decomposition | _NO VERDICT_ | 3 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs doctrine | testQuality | **doctrine** | won every one of 6 runs in both presentation orders |
| baseline vs doctrine | deadCode | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs doctrine | overBuilding | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| baseline vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | structure | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | decomposition | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | testQuality | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | deadCode | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |
| doctrine vs conductor | overBuilding | _NO WORK_ | NO WORK: conductor left the seed byte-identical, so there is no implementation to judge — this is the outcome the pass/fail already records, not a quality result |

Blinding notes for this task:
- 2 further archived repetition(s) of this task were not judged: llamacpp-qwen3.8-27b/none/baseline/logfmt-lenses-ts/r2, llamacpp-qwen3.8-27b/none/baseline/logfmt-lenses-ts/r3

## `slugify-ts`

| pair | criterion | verdict | why |
|---|---|---|---|
| baseline vs doctrine | structure | _NO VERDICT_ | 2 of 6 responses were unusable (the JSON object did not parse: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)) — an instrument failure, not a tie |
| baseline vs doctrine | decomposition | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs doctrine | testQuality | **doctrine** | won every one of 6 runs in both presentation orders |
| baseline vs doctrine | deadCode | tie | the judge disagreed with itself across 6 runs (baseline, tie) — reported as a tie rather than resolved by picking one |
| baseline vs doctrine | overBuilding | tie | the judge disagreed with itself across 6 runs (baseline, tie) — reported as a tie rather than resolved by picking one |
| baseline vs conductor | structure | _NO VERDICT_ | 2 of 6 responses were unusable (the JSON object did not parse: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)) — an instrument failure, not a tie |
| baseline vs conductor | decomposition | **baseline** | won every one of 6 runs in both presentation orders |
| baseline vs conductor | testQuality | _NO VERDICT_ | 1 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| baseline vs conductor | deadCode | tie | unanimous over 6 runs in both orders: no difference |
| baseline vs conductor | overBuilding | tie | unanimous over 6 runs in both orders: no difference |
| doctrine vs conductor | structure | **doctrine** | won every one of 6 runs in both presentation orders |
| doctrine vs conductor | decomposition | **doctrine** | won every one of 6 runs in both presentation orders |
| doctrine vs conductor | testQuality | _NO VERDICT_ | 6 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| doctrine vs conductor | deadCode | _NO VERDICT_ | 3 of 6 responses were unusable (the judge call failed: timed out) — an instrument failure, not a tie |
| doctrine vs conductor | overBuilding | tie | unanimous over 6 runs in both orders: no difference |

Blinding notes for this task:
- 2 further archived repetition(s) of this task were not judged: llamacpp-qwen3.8-27b/none/baseline/slugify-ts/r2, llamacpp-qwen3.8-27b/none/baseline/slugify-ts/r3

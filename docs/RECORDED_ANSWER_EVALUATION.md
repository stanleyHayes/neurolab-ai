# Recorded-answer evaluation

This supplements `06_Evaluation_Benchmarks_and_Ablations.md`; it does not replace the live Meta, ablation, safety or blind-review gates. The original twelve questions and target tools remain unchanged. The earlier `eval/results.json` measures selection coverage only.

## Collect actual answers

```sh
python3 -m scripts.evaluate_answers collect --output eval/new-trial --seed 2026 --budget 2
```

The collector executes all twelve questions under three offline policies using the same immutable Ghana data, seed, two-call/two-step limit and 60-second per-run wall budget:

- Fixed workflow: profile then regime comparison.
- Seeded random: sample two distinct allowed tools without replacement from the complete six-tool schema allowlist; invoke those exact methods. Earlier collections used only profile/comparison/ranking/missingness and remain labeled as that older protocol. This differs from the older action-only random baseline, which sampled with replacement; results are not interchangeable.
- Default deterministic replay: the actual current default plan and evidence-conditioned replay behavior, bounded to the same call budget. The selected default plan can remain partial. This policy is not task-target-aware and not a Meta model.

No constructor receives a model adapter, and mode is explicitly replay. Model ID is null, model calls and inference spend are zero; wall times are measured locally, not model speed claims. Full report/configuration, code startup snapshot, numeric artifacts and persisted events are retained in each `results.jsonl` record. Unexpected exceptions produce failure records with sanitized exception type and available partial trace rather than disappearing. New output directories are required so failed trials cannot be silently overwritten.

The questions target the historical four-tool task set while the current random policy can select all six implemented tools; it is not a comprehensive evaluation of the newer six-tool investigation profile, arbitrary datasets, or every adversarial scenario in document 06.

## Separate trace validity from semantic quality

Automatic audits count schema-valid recorded requests, source agreement, report/artifact evidence-ID agreement and claim citations that exist. A sentence can cite a real artifact and still be false. The tests deliberately demonstrate that a false numeric sentence passes citation-existence checking; no semantic groundedness score is inferred from this audit.

`review-template.json` binds each question/policy review to a SHA-256 over the exact question, policy, report, artifacts and events. This detects accidental stale reviews, not malicious rebinding or forgery. Missing ratings remain **null/unscored**. A completed review requires an identified reviewer, reviewer type (`human` or `assistant`), explicit blinding flag, rationale and all four binary ratings:

| Dimension | Rating 1 | Rating 0 |
|---|---|---|
| answers_question | The report's written conclusion/limitations directly answer every essential part of the question. | Missing, off-topic, only partial, or requires extracting/deriving an unstated answer from an artifact. |
| claims_supported | Written factual claims are supported by the cited artifacts/source metadata; reviewer checks their meaning, values and units. | At least one unsupported/contradictory factual assertion. This does not certify the statistical method or field validity. |
| scope_honest | Output distinguishes actual observations/replay/limits and avoids unsupported causal, validated field or model-performance claims. | Overstates evidence, model activity or validity. |
| useful_to_researcher | Provides directly useful evidence or a meaningful partial explanation for the requested question. | No meaningful question-specific help. This is subjective. |

Count partial direct answers as zero while recording useful partial material separately. Do not use target-tool presence as a semantic label. Include failures, negative ratings and ambiguous/limited outcomes. A real blind human reviewer should receive policy-masked material through an independent process; marking `blind=true` alone does not establish that process.

```sh
python3 -m scripts.evaluate_answers score \
  --records eval/new-trial/results.jsonl \
  --reviews completed-reviews.json \
  --output eval/new-trial/summary-reviewed.json
```

The scorer rejects unknown/duplicate answers, changed records, stale hashes, partial/malformed ratings and missing reviewer metadata. It retains negative judgments. Summaries report per-policy positive/total ratings, fractions, Wilson intervals, failures, timings, review type and blinding. Wilson intervals are descriptive binomial summaries of ratings on a small fixed, dependent question set, **not** confidence that a policy generalizes or outperforms another. No hypothesis test or winner claim is justified.

## Actual trials, including failures

- `eval/recorded-answers-2026-10-27/`: first collector attempt; all 36 records preserved. Fixed and random each failed all twelve runs because the new harness passed action aliases as planner method IDs. Default replay completed twelve bounded runs. These are harness failures, not evidence of model failure.
- `eval/recorded-answers-2026-10-27-v2/`: corrected explicit method mapping; all 36 runs produced reports with zero unhandled exceptions. Partial workflow statuses remain intact. Numeric science was not changed between collections.
- `assistant-reviews.json` and `summary-assistant-reviewed.json` in v2 (final aggregate trace metrics in `eval/answer-evaluation-summary.json`): actual non-blind Codex assistant review of every distinct written conclusion/limitations string, all 36 selected-action sequences and their supporting source/artifact facts. This is subjective assistant review, not independent/blind human judgment or Meta answer evaluation. Default unreviewed summary remains intact.

Direct-question ratings were **4/12 fixed**, **7/12 seeded random**, **5/12 default replay**, while target-tool coverage was 6/12 for each. All written factual claims were judged supported within this narrow sample; that does not establish general factual reliability. Caveat/calendar questions can be answered without their catalog target tool; conversely, possessing a ratio artifact does not directly state ratio availability in the report. These differences demonstrate why selection metrics cannot substitute for answer scoring. No policy superiority is claimed.

Findings that remain actionable:

1. Default focused replay does not sufficiently adapt its method selection/report to different objectives; it repeats contrast/ranking content for missingness/source questions under the small budget. Explicit six-tool full-investigation preset is a separate path.
2. Written ratio availability/value and ranking-uncertainty boundaries need clearer direct answers. Artifact access alone is insufficient.
3. The purported injection fixture puts text in the objective and never exposes a mutated dataset cell to a live model. No injection-resistance acceptance follows. Actual model-visible dataset-cell adversarial tests, answer-feedback ablations, live Meta comparison and independent review remain open.

No credits were spent, inference was not enabled, and no result from this collection is presented as live Meta performance. `eval/results.jsonl` indexes the preserved attempts and points to their complete records; see the dated protocol addenda below for later collections.

## Focused-routing regression and protocol correction

`eval/recorded-answers-2026-10-27-focused-routing/` contains 36 new attempts after code commit `1ce2761`, with zero unhandled exceptions and fresh evidence-bound, non-blind assistant reviews. It preserves the earlier random policy's four eligible actions. The router could now choose six, so this collection is **known-question regression evidence, not a fair six-tool policy comparison**. Do not infer superiority from its 5/12 fixed, 7/12 random and 11/12 focused-replay direct-answer ratings. These questions informed the implementation, and the subjective assistant was not blind. The unresolved purported injection case remains zero for direct answer, despite useful missingness output. Earlier records/reviews were not rewritten or rebound.

The collector now derives random eligibility from the actual six-action schema, matching the agent's allowlist. Each new record declares `protocol=recorded-answers-six-tools-v2` and its eligible tools. This is a protocol correction; random actions/ratings from the older four-tool collections cannot be treated as paired results under the corrected protocol. Fixed workflow remains deliberately fixed to its two actions. The same six-action permission set and per-run budget maxima apply to all policies.

## Corrected six-tool collection

`eval/recorded-answers-2026-10-27-six-tool-protocol/` was collected after commit `16455f4`: 36 recorded answers, no unexpected failures, all policies declaring the same six eligible tools and budget maxima. Actual calls were 24 fixed, 24 random and 14 focused replay; a maximum budget is not a requirement to waste calls. All 36 semantic reviews remain pending/null. No earlier annotations were reused, and no new winner/answer-accuracy claim is made. `verification/six-tool-evaluation-runtime.json` verifies commit/source/hash consistency, protocol/call bounds, zero model calls and the final Sonar gate. The root index now preserves 144 total attempts across the initial, corrected, known-regression and six-tool collections.

The simple focused relevance and wording cases identified in the earlier review are addressed by [focused replay routing](FOCUSED_REPLAY_ROUTING.md), with five authenticated one-call runtime cases in `verification/focused-replay-runtime.json`. Complex semantic coverage, model-visible dataset-cell adversarial behavior, live Meta/feedback ablations and independent blind review remain unproven.

## Synthetic prompt-boundary follow up

[The separate synthetic CSV contract suite](ADVERSARIAL_FEEDBACK_CONTRACTS.md) adds real CSV-cell propagation to adapter input, deliberate unsafe-reply containment and matched result-feedback plumbing. It uses programmed responses, not Meta; it neither repairs the historical injection question ratings nor proves live resistance/feedback utility. All earlier records/reviews remain untouched and the corrected six-tool semantic reviews remain pending.

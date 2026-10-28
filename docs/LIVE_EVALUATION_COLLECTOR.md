# Live matrix collector — execution not yet accepted

`python3 -m scripts.collect_live_evaluation` collects the document06 known-set matrix: twelve questions × three seeds × five policies =180 trials, including72 Meta-mode trials. All policies have two steps/two numeric calls/60seconds. It does not score answer quality, establish independence, run held-out validation or claim a winning policy.

The two Meta conditions have the same initial configuration, six-method pending pool, prompts and schemas; only prior numerical evidence is withheld in the ablation. Both have a two-call ceiling, so pending tasks and PARTIAL status are expected rather than an automatic semantic failure. Focused/fixed/random baselines use their declared plans; raw workflow completion statuses are not equivalent answer-quality measures across these different plans. The random baseline seeds each task with `seed:task_id` and samples without replacement. This change must be declared in the versioned protocol before actual collection. All choices and partial results remain available to semantic reviewers.

## Required preflight

Use an existing operator-verified active server owner and the shared SQL store. The collector never reads owner IDs from the question catalog, creates a dummy production owner, loads `.env`, changes policy or enables inference. Configure the worker environment deliberately. Do not use a second isolated ledger to bypass existing daily reservations.

A reviewed new protocol must contain the exact matrix/tasks/utility subset/seeds/budgets; frozen SHA256 values for all scientific/backend Python modules, collector CLI, action schema, requirements and canonical source; approved model/output settings; exact shared spending-policy digest; explicit owner authorization, verified provider-account controls, a UTC approval day and aggregate microUSD ceiling. The global daily SQL ceiling must not exceed the aggregate approval. The frozen runtime byte hashes must also match the loaded modules. Existing v1 has neither current hashes nor these approvals and is deliberately refused. The v2 draft is not authorization.

```sh
python3 -m scripts.collect_live_evaluation \
  --protocol /private/reviewed-approved-protocol.json \
  --owner EXISTING_VERIFIED_OWNER --preflight-only
python3 -m scripts.collect_live_evaluation \
  --protocol /private/reviewed-approved-protocol.json \
  --owner EXISTING_VERIFIED_OWNER --output /private/new-collection
```

Do not launch when the reviewed aggregate/daily budget cannot cover the declared experiment. Account for existing reservations, conservative byte-based token bounds and the full matrix, not only favorable trials. An approved-day expiry stops collection and transport rather than receiving another day's fresh budget automatically. The current implementation requires a single UTC-day collection. No provider-account limit is claimed verified merely because a manifest flag says so; operators must retain the actual provider evidence separately.

## Evidence and failure handling

Output creation is exclusive with a private directory. Every trial is fsynced to `attempts.jsonl` before execution. `results.jsonl` records all outcomes, including refusals and errors. A keyboard interruption saves its attempted record and re-raises; no automatic resume/retry or overwrite is supported. An unstarted remainder is not silently called a completed matrix. Execution failures retain the owned run handle, events/artifacts and FAILED state. Existing SQL reservations remain charged for unknown outcomes.

`provider.jsonl` links each actual transport attempt and JSON response to the run. It records prompts/schemas, actual provider usage when returned and safe failure status/type, without Authorization headers or API keys. These transcripts may include private scientific input: keep them private until reviewed/redacted. Actual artifacts, report, source/runtime hashes, UTC times, elapsed duration, model-call counts and conservative SQL reservations are retained separately from invoices. No raw provider error bodies or exception messages are logged.

Create review packets using the policy-masking tools, preserving all failures and scientific limits. The old offline scorer explicitly rejects the new live policies rather than silently reporting zero model calls or omitting policies. A seed-aware live scorer with question-level dependence and failure-denominator rules is still required before comparative reporting. Independent human scores remain unfilled.

## Evidence boundary

Tests use programmed provider transports with actual SQL ownership/reservations and real Ghana tools. They validate enumeration, paired initial prompts/schemas, evidence withholding, owner scoping, failure retention, interruption, exclusive output and approval expiry. They are not actual Meta performance or billing evidence. No180-trial live matrix has run. Hosted Meta404, independent review, seed-aware reporting and actual provider cancellation remain open.

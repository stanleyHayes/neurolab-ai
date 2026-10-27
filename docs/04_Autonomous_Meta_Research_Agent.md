# 04 — Meta research agent: bounded closed-loop autonomy

## Role
Meta model proposes a falsifiable hypothesis and chooses an *allowed* analysis action. The backend validates action schema, scientific applicability and budget; deterministic tools compute results. The model then receives verified evidence and selects next action. Never let model author SQL, arbitrary Python or shell code executed unsandboxed.

## States
`CREATED -> OBJECTIVE_PARSED -> HYPOTHESIS_PROPOSED -> PLAN_VALIDATED -> TOOL_RUNNING -> EVIDENCE_RECORDED -> NEXT_ACTION_SELECTED -> ... -> REPORT_READY` with `FAILED`/`BUDGET_EXHAUSTED` terminal states. Event IDs monotonic and persisted.

## Tool allowlist
`dataset_profile`, `compare_regimes`, `rank_genotypes`, `analyze_trait_association`, `check_environment_stability`, `inspect_missingness`, `run_baseline`, `generate_report`. Each tool returns JSON with `artifact_id`, dataset hash, filters, n, statistic, uncertainty, warnings and version. Tool failures must be surfaced to agent and UI.

## Model adapters
`MetaModelAdapter` with `generate_structured(messages, schema, budget)`; one concrete adapter for Meta Model API and optional adapter for eligible Muse Spark Open/Glimmer through verified provider. Credentials from environment only. Record actual model ID and provider. Use `meta-models/muse-spark-open-1026` **only when using the documented Baseten hackathon endpoint**; verify at runtime, do not apply blindly to other providers.

## Verifiability
No chain-of-thought display. UI can show externally generated, concise decision summaries tied to tool outputs, with no claim that this is internal reasoning. Every statement in final report points to `evidence_id`; unsupported statements fail groundedness check.

## Guardrails
max_steps=6, max_tool_calls=10, max_wall_time=180s, model cost cap configured, max output tokens configured, concurrency 1 for demo. Reject prompt injection embedded in dataset cells and tool responses; data is untrusted. Never ask agent to generate fabricated 'discovery'.

## Acceptance
Two genuinely result-dependent tool selections; one failed/invalid action recovered gracefully; no unauthorized tool execution; reproducible replay trace; live Meta model call in production demo; model unavailable -> labeled replay fallback only.

# Research context management

The full submitted original is immutable within a run and retained in the database/report. Its SHA-256 digest binds a proposed plan to that exact string. No objective slicing, automatic shortening or silent replacement occurs. The 20,000-character limit is independent of model token limits.

## Structured context

`ResearchConfiguration` stores explicit questions, hypotheses, dataset, methods, output preferences and bounded execution constraints. `ResearchPlan` stores refined wording, important constraints, ambiguities, supported/unsupported tasks and unmet requirements. Task IDs must be unique; new client plans cannot supply completed tasks or evidence. Tool handlers alone create numeric artifacts and completion evidence.

In live mode with automatic planning enabled and no accepted plan, the server submits the full original once to a schema-constrained planning operation. The same adapter instance is reused for task selection so its token reservations span planning and execution. The validated plan is persisted before numeric execution. The run's wall-time budget includes planning. Planning/selection failures are recorded rather than presented as successful reasoning.

Subsequent task-selection requests receive pending tasks, important constraints, structured questions/hypotheses, bounded execution settings, objective digest/length, and actual tool evidence. They do not blindly resend the original. When starting from a deterministic plan, the initial selection receives the full original; later selections use structured context. This is task decomposition, not a claim that chunking removes context-window limits. A deterministic plan is a predefined offline baseline, not proof that arbitrary natural-language requirements were fully understood.

## Context and token ceilings

Meta's official model documentation lists a 1,048,576-token context window for Muse Spark 1.3, shared by input and requested output: https://dev.meta.ai/docs/models and https://dev.meta.ai/docs/cookbook/long-context (verified 2026-10-27). The runtime retains an additional 8,000-token safety reserve and honors a lower configured `MODEL_MAX_CONTEXT_TOKENS` ceiling. Other providers/models require verification of their served limits; configuration alone is not evidence of compatibility.

The current Chat Completions adapter has no exact tokenizer integration. It conservatively counts UTF-8 bytes of messages and response schema as an upper-bound token reservation, includes requested output, and rejects oversized requests before transport. Per-run reserved-token limits apply across adapter calls. This bound can reject a request that the provider could have accepted; it never solves an overflow by truncating the original. Provider availability and real answer quality are separate live acceptance gates.

## Ownership and rendering

Objectives, drafts, plans, reports, events and artifacts are accessed through owner-scoped authenticated routes. The complete original is not put in browser storage or event URLs. React renders original/refined Markdown as escaped text; no raw HTML interpreter is used. Request bodies remain bounded to 256 KiB at both API and proxy. SQL objective storage uses TEXT rather than a short varchar.

## Explicit limitations

Important-constraint extraction by a model is a proposal that may omit or misinterpret requirements. Keeping the original and exposing the plan enables review; it does not prove semantic completeness. The offline planner executes only registered methods. Unsupported scientific methods, ambiguous trial semantics and causal claims must remain explicit rather than being silently replaced by descriptive rankings. Shared abuse/spend enforcement, durable workers and target-deployment acceptance remain separate public-launch gates.

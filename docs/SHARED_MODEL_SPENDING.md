# Shared model spending admission

## What is enforced

Every real adapter call now requires an active owner and a SQL spending guard. Before creating the HTTPS connection it atomically reserves a conservative integer micro-USD amount and token bound. Admission enforces the execution-scope lifetime ceiling (`MODEL_MAX_COST_USD`), owner UTC-day ceiling, service-wide UTC-day ceiling and scope token ceiling. All API replicas and workers must use the same database. Direct refinement and operator smoke requests use distinct server-generated scopes and share owner/global daily limits with queued research.

A durable SQL control lock serializes decisions across connections. Costs use Decimal arithmetic and round upward to whole micro-USD; limits accept at most six decimal places. Day boundaries use database epoch time, not process clocks. Scope ceilings do not reset at midnight. Daily reservations are assigned to the UTC day of admission, which is not necessarily the provider's invoice date.

Each reservation records its UUID, owner, scope, provider/model, admission day, input/output upper bounds, reserved amount, policy digest and outcome. No prompt, source cell, key, JWT or response content is stored in this ledger. It is private security/accounting metadata and is not exposed through public scientific evidence bundles. Run scopes are checked against persisted ownership; ownerless legacy records and inactive/other owners cannot spend. Workers continue to fence calls by their execution lease and cancellation state.

## Configuration and pricing boundary

Inference remains paused after exhausted credits. Do not enable it to verify this increment. Local tests use deliberately synthetic prices and mocked HTTPS. They establish transaction/guard behavior, not actual provider charges, pricing or live-model quality.

Before any future authorized live call an operator must supply and review:

- `MODEL_INPUT_USD_PER_MILLION_TOKENS` and `MODEL_OUTPUT_USD_PER_MILLION_TOKENS`: positive conservative price ceilings for all applicable billable token categories of the configured provider/model/endpoint. No market price is guessed or embedded in code.
- `MODEL_INPUT_OVERHEAD_TOKENS`: positive reviewed allowance, up to 8192, for provider-added formatting/token overhead. The serialized messages and response schema are bounded by UTF-8 bytes, then this allowance and the maximum output are added. There is no exact provider tokenizer endpoint in this integration.
- `MODEL_MAX_COST_USD`, `MODEL_OWNER_DAILY_COST_USD`, `MODEL_GLOBAL_DAILY_COST_USD`: positive configured limits. Missing, zero, negative, non-finite or over-precise settings fail closed. The operator must choose suitable ceilings; example test prices are not operating recommendations.
- `MODEL_MAX_RUN_TOKENS`: the lifetime token reservation ceiling, including refinement and selection. Output reservations use the actual configured maximum for each call, including the larger refinement allowance.

The policy captures provider/model identity and the endpoint's SHA-256 as well as these settings. Changing model, endpoint, prices or limits requires a reviewed policy transition. The adapter checks its actual current model/provider/endpoint against its guard before transport. A replica with different settings cannot silently impose a more generous policy.

These are conservative **admission reservations, not measured token usage, invoices or proof of a hard provider bill ceiling**. Price/overhead accuracy, hidden billable categories, billing-date behavior and external account activity must be verified with the provider before live deployment. Configure authoritative provider-account spending controls and alerts as well. Other software using the same key/account outside this database is not governed by this ledger. The project does not claim those external gates are complete.

## Failure and crash behavior

The reservation commits before transport and initially has outcome `unknown`. It remains charged to its original admission day even on timeout, malformed JSON, HTTP errors, cancellation, storage failure after transport or a worker crash. No automatic refund or retry is made. `completed` means a structured object returned through the adapter; it does not mean scientifically valid content, exact billed usage or zero over-reservation.

Provider responses are bounded to 1 MiB before JSON parsing. If outcome persistence fails, the adapter fails rather than claiming clean accounting; the committed reservation is retained. Database admission failures are sanitized and stop transport. Rejected preflight/context/budget checks do not make a provider request. Deterministic replay and saved-result viewing do not reserve money or require a pricing policy.

Unknown reservations are intentionally conservative. Do not delete records or reset counters to make another request fit. A billed-usage reconciliation/refund mechanism is not implemented; any future reconciliation must be separately authorized, auditable and idempotent.

## Policy changes

The first successful admission pins its policy and records a `first_admission` policy event. Operators can instead initialize or change it explicitly without inference:

```sh
# Export the reviewed server environment first; keep inference disabled.
MODEL_INFERENCE_ENABLED=false python -m scripts.configure_model_budget --expect-sha256 empty
# For a later change, supply the existing digest printed by the prior application.
MODEL_INFERENCE_ENABLED=false python -m scripts.configure_model_budget --expect-sha256 "$CURRENT_MODEL_POLICY_SHA256"
```

Set `CURRENT_MODEL_POLICY_SHA256` to the reviewed existing digest before the later-change command. The command uses compare-and-swap under the same control lock, records prior/new policy digests and settings, and retains all reservations. Obtain the current digest from the existing operator record or a private read-only DB inspection; never guess it or delete the control row. Review the new environment before applying; the command does not decide prices or authorize paid inference. Restart/update all participating API/worker processes consistently. A stale process then fails policy matching rather than silently overspending.

The smoke script additionally requires server-operator `MODEL_SMOKE_OWNER_USER_ID` resolving to an active local user. It binds a `smoke:` UUID scope and uses the same ceilings. Ordinary HTTP requests never accept that variable as an owner; they use verified JWT identity or the persisted queued-run owner. While paused, the smoke script exits before database/provider activity. Its future execution remains subject to owner authorization and available credits.

## Evidence and remaining gates

`tests/test_model_spend.py` covers concurrent SQL admissions, run/owner/global limits, UTC rollover, persisted unknown/completed reservations, shared token bounds, policy mismatch and audited changes, ownership and pre-transport failure. Provider tests and the API integration case use real adapter code with mocked HTTPS to cover structured responses, failures and worker/refinement owner binding. `verification/postgresql-model-spend-tests.json` records actual disposable local PostgreSQL tests, not live billing.

Provider billing reconciliation, real token/price/overhead verification, external spend controls, key rotation, deployment supervision, actual ingress/HTTPS/browser acceptance, independent model answer quality and public licensing/publication/submission remain open. Signup stays invite-gated. This increment does not reopen paid inference or mark the overall project production-ready.

New Meta-mode reports label the mode as requested, not as proof of live inference. If spending admission blocks a decision, deterministic recovery remains visibly partial with its failure trace; it does not claim a model call occurred.

# Baseten inference for Meta Muse Spark Open

> **Operational resolution (28 October):** The adapter accepts the documented, successfully exercised `meta-models/muse-spark-open` and the explicit event alias `meta-models/muse-spark-open-1026`. The generic model is the example configuration; the unavailable alias is optional pending access confirmation. Neither an accepted identifier nor another model's successful response establishes verification for a selected model. Existing SQL policy matching still binds the exact provider/endpoint/model, retains reservations and prevents silent switching. The earlier exclusive -1026 pin was a configuration regression and is superseded. Production's previously verified generic route was not changed by this correction. Event alias eligibility remains unresolved.

> **Event alignment update (28 October):** The owner confirmed **Solo Indie Developer**. The supplied guide requires Baseten `meta-models/muse-spark-open-1026`; one real request returned HTTP 404. Earlier generic-model successes remain valid operational evidence but do not verify that alias. The tested local adapter now pins the required alias with verification disabled; production has not been changed by this documentation update and still serves the earlier generic configuration. See [event audit](EVENT_ALIGNMENT_2026_10_28.md) for judging weights, deadline, contribution disclosure and remaining video/access requirements. No submission or eligibility certification has been made.

The frontend stays on Vercel; the scientific API, standalone worker and PostgreSQL stay on Render. Baseten supplies Meta Muse Spark Open inference. It is a separate model release from the already-recorded direct Meta `muse-spark-1.3` comparison. Earlier results and their model identity remain unchanged.

## Configuration and trust boundary

Set `MODEL_PROVIDER=baseten` only in the backend/worker deployment being migrated. Configure `BASETEN_API_KEY`, `BASETEN_MODEL_API_BASE_URL=https://inference.baseten.co/v1/chat/completions`, `BASETEN_MODEL_ID=meta-models/muse-spark-open` and the independent `BASETEN_MODEL_VERIFIED` flag. The adapter pins this serverless endpoint/model; it does not reuse Meta credentials or verification. No `NEXT_PUBLIC_` model secrets are used. Replay strips both vendors' keys, and a live worker retains only the selected key and never signing/service secrets.

The existing reviewed prices, per-run/owner/global SQL money limits and token/context caps remain mandatory. The endpoint/vendor/model are part of the policy digest. A vendor change requires explicit compare-and-swap on the same ledger and retains all prior reservations. A key or a true verification flag alone cannot bypass policy matching. No new ledger, quota reset or automatic failover is used.

## Request contract

Baseten's [model feature documentation](https://docs.baseten.co/inference/model-apis/overview) excludes Muse Spark Open from JSON-schema response mode. Its [function-calling contract](https://docs.baseten.co/inference/function-calling) supports selecting a named function. NeuroLab therefore sends a single `submit_research_action` function with the existing response schema, forces that function and disables parallel calls.

Exactly one matching function call is accepted. Arguments must be JSON text and satisfy the response schema on the server. Wrong/multiple/missing calls, unknown functions, malformed JSON, extra properties, wrong types and truncated outputs fail closed. This wrapper proposes data; it does not execute an arbitrary provider-supplied function. Existing scientific action schemas, allowlist, task validation and tools remain authoritative.

Reasoning is explicitly set to `low` per the [model's reasoning settings](https://docs.baseten.co/inference/model-apis/reasoning). Baseten actions use the configured output ceiling, including reasoning tokens; direct Meta retains its existing 1,000-token action ceiling. Neither response nor objective is silently truncated. Reservations count the full serialized wire body, including function definitions and selection fields. Request/response sizes, deadlines, cancellation and conservative unknown charges remain enforced.

## Rollout and acceptance

1. Validate synthetic contracts and the full quality/Sonar gates.
2. Inspect the authenticated catalog and make one real bounded acknowledgement using an existing active owner and the existing ledger. This is connectivity evidence, not scientific acceptance.
3. Deploy tested code to Render with new live admissions paused; retain existing PostgreSQL/auth/data configuration.
4. Inspect the actual hosted SQL policy and queued/running jobs. Apply the reviewed Baseten policy with compare-and-swap, retaining reservations. Run the bounded acknowledgement from Render and retain sanitized status/usage evidence.
5. Enable the verified provider on the worker and API, then rerun the same owned original objective/plan/source/seed under the declared six-step amendment. Confirm actual model choices and computed evidence rather than relabelled recovery.

Operator-only budget/smoke scripts are included in the container. The direct Meta API, prior comparison, current source snapshot and Baseten acceptance are separate evidence. Real requests can vary; deterministic tools are reproducible only for the same actual parameters/source/seed. No winner, independent review or hosted-success claim follows from configuration alone.

Current execution receipts are recorded in `BUILD_LOG.md` and `verification/baseten-activation-2026-10-28/` as they become available. The local `.env` remains on its existing serving provider until a deliberate local policy migration; adding a Baseten key does not silently switch it.

## Actual hosted acceptance — 28 October 2026

API and worker are live on 97fce766db210ca9d4c233758f755888527e73b8. One actual local acknowledgement and one actual Render acknowledgement returned HTTP 200 with the named function response. The initial hosted operator job failed before inference while serializing a PostgreSQL Decimal audit value; it remains retained. The corrected job verified zero previous Baseten reservations and the same migrated policy before making the hosted request.

Owned hosted run `c8591707-1b97-41b9-badf-b94ca1df7ff8` completed the unchanged original objective, original archived accepted plan, source and seed 2026: six model selections, six scientific tools/artifacts, 58 events, no failures/recovery, complete evidence coverage and three original hypothesis evaluations. The original plan was not newly generated by Baseten. Separate real-model comparison and human-review results have not been rewritten.

Actual PostgreSQL receipt confirms six completed Baseten reservations, 92,770 reserved tokens and 151,964 microUSD for this run; total shared UTC-day reservations 333,395 microUSD. Hosted $1/run, $1/owner/day, $1/global/day and 100,000-token limits remain unchanged. Reservations are not invoices. The original 179 local comparison-ledger reservations and 14 hosted reservations were retained, not reset or migrated to a fresh ledger.

Actual hosted Chromium rendered the saved results/report with explicit Baseten/model identity, measured 1,230.3/2,616 kg/ha, 47% retention and 72 genotypes and scientific caveats, no overflow/JavaScript errors/new admissions. Reviewed screenshots and complete scoped receipts: [verification](../verification/baseten-activation-2026-10-28/original-proof.json), [SQL](../verification/baseten-activation-2026-10-28/hosted-sql-receipt.json), [browser](../verification/baseten-activation-2026-10-28/browser.json). Tests: 228 Python + 11 proxy + 94 UI, lint/types/build and Sonar 0 issues/0 hotspots. Direct Meta's earlier 404 is not claimed repaired; its serving dependency is replaced by the authorized Baseten route.

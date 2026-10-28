# Baseten inference for Meta Muse Spark Open

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

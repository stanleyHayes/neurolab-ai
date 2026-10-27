# Meta AI Integration Verification

**Date:** 2026-10-26  
**Credential handling:** No API key value was read into this report, displayed, copied, or committed. Local `.env` file mode observed as `0600`; `.env` is covered by `.gitignore`. No Git repository is present to inspect tracked-file history, so public-repo exposure cannot be conclusively checked.

## Configuration verified

Expected API credential environment variable is **`META_MODEL_API_KEY`**. The code does not expect `META_API_KEY`.

Other required configuration for a Meta run:

- `META_MODEL_API_BASE_URL` — complete HTTPS chat-completions endpoint.
- `META_MODEL_ID` — actual configured identifier `muse-spark-1.3`.
- `MODEL_PROVIDER=meta`.
- `META_MODEL_VERIFIED=true` to enable model runs after a reviewed smoke test.
- Optional token controls: `MODEL_MAX_OUTPUT_TOKENS` (example/local value 2000) and `MODEL_MAX_RUN_TOKENS` (defaults to 16000 in code; `.env.example` documents it). `MODEL_MAX_COST_USD` exists in example config, but the adapter does not calculate/charge-track actual provider cost; it is not a substitute for provider quotas.

The API process does not automatically load `.env`; the README's run command sources it into backend environment. The browser uses a Next.js same-origin proxy. The proxy's `API_BEARER_TOKEN` is a separate Next-to-FastAPI service credential, not the Meta key or an end-user identity.

## Source inspection

- Adapter: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/neurolab/providers.py`.
- Smoke script: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/scripts/smoke_meta_provider.py`.
- Orchestration: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/neurolab/agent.py`.
- API: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/neurolab/api.py`.
- Environment template: `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/.env.example`.

Behavior observed in code:

1. Reads credential only in server process and sends `Authorization: Bearer …` over an HTTPS endpoint.
2. Sends the configured model ID, messages and strict JSON-schema `response_format` with temperature 0 and bounded output tokens.
3. Reserves estimated input bytes/4 plus max output tokens against an in-memory per-run reservation limit before request.
4. Uses a per-call connection timeout supplied by agent (`20` seconds in observed orchestration); there is no HTTP retry.
5. Sanitizes non-2xx response into `Model provider returned HTTP <status>` without returning provider error body; network failure becomes `Model provider could not be reached`; malformed response/schema JSON paths produce explicit errors.
6. Model output is parsed, then structured tool-call decisions receive additional server-side checks and allowlist/schema validation before tool execution.
7. Model identifier/provider appear in completed report/status and are displayed by UI when a report exists. Adapter does not record structured provider request/response logs, provider request IDs, latency, real token usage, billed cost, or comprehensive redacted observability logs.

The only implemented model decision actions are `dataset_profile`, `compare_regimes`, `rank_genotypes`, `inspect_missingness`. Schema includes additional actions without executable handlers; server/action validation can reject these. This gap was exercised by the live run.

## Real provider evidence

### Smoke request

- Command: `set -a; source .env; set +a; export SSL_CERT_FILE="$(python3 -c 'import certifi; print(certifi.where())')"; python3 scripts/smoke_meta_provider.py`
- Result: `PASS: provider responded with structured JSON for model 'muse-spark-1.3'.`
- Status: successful authenticated real structured-output request, as evidenced by successful response (smoke script itself does not output HTTP status or latency).
- A separate attempted status/latency instrumentation command did not complete because shell integration mangled the Python heredoc; **no HTTP status/latency value is claimed**.
- No credential value printed.

### Bounded research run

The direct backend agent call was performed against the local Ghana dataset with `ResearchAgent(mode="meta")`, model adapter from environment, in-memory SQLite store, seed 2026, `max_steps=3`, `max_tool_calls=5`, wall-time budget 120 seconds.

- Run ID: `a150a5bb-15db-44f9-bc28-36a7fb1d770c`.
- Provider/model recorded by report: `meta` / `muse-spark-1.3`.
- Result: terminal report marked `partial`; actual run created 27 persisted-in-memory events, three evidence artifacts, two useful executed tools (`dataset_profile`, `inspect_missingness`), and one recovery profile.
- Wall time: 17.101 seconds.
- Adapter token reservation total: 7,782 (reservation estimate, not provider-reported actual usage).
- No result was fabricated; numeric artifacts came from deterministic dataset tools.
- It failed acceptance of requested genotype ranking, stability, meaningful recommendation, and model-generated falsifiable hypothesis. Full trace is in `AGENT_EXECUTION_TRACE.md`.

## Required configuration/error checks

| Case | Current verification |
|---|---|
| Valid API key | **PASS:** real smoke response succeeded. Key itself was not inspected/output. |
| Invalid API key | **NOT RUN in this audit.** Historical build log reports an unauthenticated request returning HTTP 401; not equivalent to running the adapter with invalid secret. |
| Missing API key | **Unit-tested by provider configuration test** (`test_provider_requires_verified_runtime_configuration`); this audit did not separately start an API process with a cleared key and capture its result. |
| Model unavailable | **NOT RUN against provider.** Code maps non-2xx to sanitized HTTP status. |
| API timeout | **Unit/code-path only; no current live timeout.** Adapter has timeout and maps network timeout; no end-to-end experiment-state persistence recovery under provider timeout was verified. |
| Credit exhaustion | **NOT RUN.** No provider billing/quota visibility or cost accounting evidence available. |
| Structured schema | **PASS:** real smoke response matched schema; live model run invoked structured actions. |
| Request/response logging and redaction | **PARTIAL:** key excluded from source logs/report; but no request-ID/latency/usage telemetry and no structured provider log evidence. Do not claim comprehensive logging. |

## Integration verdict

**Real Meta inference exists and was directly exercised.** It materially selected allowlisted actions, and the backend actually executed two distinct numerical tools based on it. This proves the app is not purely a static mock. It does **not** prove scientific reasoning quality, acceptance-level autonomy, research-answer quality, provider reliability, billing controls, or a complete end-to-end demo. The live response's invalid third decision and fallback behavior are acceptance defects, not a successful full research workflow.

No open-weight Muse model was run. Do not claim open-weight eligibility/bonus evidence.
# Durable research jobs and worker lifecycle

## Contract

Every new HTTP run is an owned, persisted request before HTTP 202 returns. Run, original objective/configuration/initial plan, accepted-request event, queue event and queued stage are committed together. Owner admission (two nonterminal runs) and queue capacity are checked under a shared SQL admission lock. SQLite uses an outer `BEGIN IMMEDIATE`; PostgreSQL locks the singleton admission row. A rejected admission leaves no partial run/job. Explicit accepted plans remain authoritative; a missing accepted Meta plan stays missing in the payload so optional bounded refinement can still run in the worker.

The same PostgreSQL database is the coordination authority for API replicas/workers. No Redis or external broker is required. SQLite remains for isolated local review/tests. Legacy runs without a job row are never adopted, assigned an owner or executed by the queue. In particular, an old unowned RUNNING row with a report remains quarantined; its status alone is not proof of a live executor, a crash cause or scientific completion.

## Run locally

Export the API environment as described in README, then start these processes using the **same database**:

```sh
RESEARCH_INLINE_WORKER=false uvicorn neurolab.api:app --port 8000
python -m neurolab.worker
npm run dev
```

The Python worker does not load `.env` automatically. It needs database access, the configured scientific source files, worker limits, and optional server-side model settings. It does **not** import/serve the HTTP application or require its JWT signing key, service bearer or browser refresh cookies. Replay needs no provider key. Do not enable inference to test durability while the owner's credits are exhausted.

`python -m neurolab.worker --once` performs one polling/claim pass and exits. It also reconciles expired/terminal jobs even when no new job is available. The default poll period is one second (`--poll-seconds`, bounded 0.1–30 seconds). API development/test mode can use inline wakeups for convenience: `RESEARCH_INLINE_WORKER=true` drains the same durable queue under the same leases. Production defaults to no inline wakeup and requires a supervised standalone worker. Queued jobs survive API termination; a worker must be available to execute/reconcile them.

| Setting | Default / meaning |
|---|---|
| `RESEARCH_INLINE_WORKER` | True in development/test when unset; false in production. Exact `true` enables an optional HTTP-process wakeup. |
| `RESEARCH_MAX_QUEUED_JOBS` | 100 pending requests; reject excess with 429. |
| `RESEARCH_MAX_RUNNING_JOBS` | Two leased jobs across processes sharing the database. All replicas/workers must use the same operator configuration. |
| Lease / heartbeat | 30-second lease; renew at most every five seconds. No renewal beyond the request execution deadline. |
| Per-owner admission | Two nonterminal runs, counted atomically across API processes; covers all nonterminal stages. |

Worker/queue limits are server configuration, not request-body owner/privilege fields. These controls are not a replacement for shared IP/account request throttling, provider spend ledgers or target-deployment resource limits. Public signup stays invite-gated.

## Claims, heartbeats and fencing

A worker claims the oldest eligible queued request under a shared SQL lock, assigns a fresh private fencing token and records an actual `job.claimed` event/PLANNING stage. It validates the stored request again. Workers use database epoch time for lease/deadline decisions, rather than trusting clocks on different application hosts. The loaded source hash must match the hash at admission before any model or numeric tool runs.

Each store transaction in the execution context locks and rechecks the job lease before writes and again before commit. Expired/replaced tokens and inactive owners cannot publish new evidence or reports. PostgreSQL event sequences also lock the parent run; SQLite serializes writers. Numeric artifact publication and its tool-completion/evidence events commit together. Report, report-generated event and terminal stage/event commit together. An inner failed transaction cannot be caught and accidentally committed as partial state by its outer transaction.

Both structured-action and refinement model calls check the lease and cancellation before invoking the adapter. Agent decisions also recheck cancellation before starting another tool. Running numeric work can complete at its next safe boundary; an already-started provider request may still be billed. Python calculations and in-flight network requests are not forcibly preempted by this implementation. Deadline/lease expiration fences further side effects and publication; process supervision/CPU limits remain deployment responsibilities. Visibility of an expired state depends on a heartbeat/worker reconciliation pass and database availability.

## Recovery and terminal states

- **QUEUED:** request is durable; a different process can claim it after an API restart. No tool or model call is implied by queuing or claiming.
- **RUNNING job:** exclusive lease, at most one claim attempt. Heartbeat cannot resurrect an expired/replaced lease.
- **Expired lease before deadline:** mark the run FAILED and job INTERRUPTED; retain committed real artifacts/events. No success, numerical observation or report is fabricated.
- **Execution deadline exceeded:** record real TIMED_OUT stage/event and fence late publication. UI/SSE/replay recognize it as terminal.
- **Run already terminal:** close its queue entry without overwriting its scientific outcome/report.
- **Inactive owner:** do not execute queued work; fence a claimed worker and cancel the job.
- **Owner cancellation:** queued requests become CANCELLED atomically; running work checks at safe boundaries and before new provider actions.

Started work is **never automatically retried or resumed**. A process can die after a model request was charged but before its response was saved. An operator/owner must review retained evidence and any unknown provider billing before explicitly launching a new request. Retry is a new bounded run, not continuation of the old lease. This is a deliberate safety boundary, not a claim of exactly-once external effects.

The job's `DONE` value means queue processing is closed; the run can be COMPLETE, PARTIAL, FAILED or CANCELLED. Scientific completion/validity is read from the run/report, not the job label. `GET /research-runs/{id}/job` is owner-scoped and returns lifecycle dates/state/attempt count only; it never returns the request payload, private fencing token or worker credentials. Historical runs with no job return 404 on this endpoint and remain available only through their existing owned resources.

## Evidence and deployment boundary

`tests/test_durable_jobs.py` runs real-source numeric tools plus explicit operational fault injections. It covers queued restart/standalone execution, exclusive claims and global leased concurrency, atomic owner/global admission across connections, source mismatch before provider calls, cancellation, disabled owners, expired leases/deadlines, stale write rejection, no automatic retry, publication/report rollback, nested transaction rollback and metadata isolation. It can run unchanged against a disposable PostgreSQL database via `NEUROLAB_TEST_POSTGRES_URL`; the test refuses a non-test database name and uses an isolated schema per case.

`verification/postgresql-durable-job-tests.json` records actual local PostgreSQL acceptance, including a separate worker process without a JWT key. The disposable database was removed afterward. Initial PostgreSQL harness attempts exposed URI formatting/space-encoding mistakes; corrected the harness before the passing run. Production database migration/backup-restore, replica configuration consistency, worker supervision, provider billing after interruption, external HTTPS/browser acceptance and shared abuse/spend enforcement remain release gates. Do not open public signup or claim production readiness from these tests.

## Committed local runtime rehearsal

After science/queue commit `ef8b7bd`, the isolated owner-authenticated API persisted the exact original objective with inline execution disabled and attempt count zero. The API was terminated and restarted before a separate worker consumed that same SQL request. It completed six actual tools/artifacts with one claim and 59 persisted events. Source hash and original objective hash matched; model ID remained null. `verification/durable-worker-runtime.json` records this run and its evidence IDs.

A separate explicitly named operational probe committed a one-second lease, then exited with controlled code 23 before any tool ran. A subsequent worker pass recorded FAILED/INTERRUPTED with `WorkerLeaseExpired`, attempt count one, no tool requests/artifacts/report and no automatic retry. This is an intentional interruption rehearsal, not a failed scientific finding. A continuously running standalone worker subsequently completed another authenticated source profile (864 actual rows). Primary and isolated-review workers run with inference disabled and without JWT signing/service credentials; local supervision is still the execution-session host, not a verified deployment supervisor. Browser tab creation remains unavailable.

## Hosted cancellation acceptance, 28 October 2026

Owner-authenticated run `456b694f-a151-46e5-ac5c-bda6e4146d7a` used explicit replay mode on the actual Render standalone worker and PostgreSQL through the Vercel BFF. The job was observed RUNNING before HTTP202 cancellation acceptance; it closed as CANCELLED/DONE with one attempt, five retained numerical artifacts and no report. A later read confirmed the same artifact count. Terminal event replay returned HTTP200 and the cancellation event. Repeated cancellation returned409; another authenticated owner received404 for job access and cancellation. See [redacted evidence](../verification/hosted-async-cancellation-2026-10-28.json).

This verifies actual hosted safe-boundary cancellation, not forced preemption or cancellation of an in-flight paid model request. Meta was not requested by this check. Browser controls, crash/restart recovery under live load and model-request cancellation remain separate acceptance gates.

## Real in-flight provider cancellation, 28 October2026

Local owned run `bf93f8dd-02f1-4b0e-bae2-0c7fe49372d2` used the actual SQL queue/lease, worker thread, spending admission and Meta HTTPS adapter. Transparent wrappers observed the original standard-library send/response methods without replacing replies or inserting delays. Request bytes were sent at01:43:26.763090UTC; owner cancellation committed at01:43:26.764015UTC; Meta response headers arrived at01:43:28.822434UTC with HTTP200. Meta reported636tokens. The job ended CANCELLED/DONE after one attempt, with no numeric artifacts or scientific report and no second provider request. The reservation remains retained. A later terminal check still found no report/artifacts and refused another claim.

The initial observer probe failed before HTTPS transmission because replacing the stdlib class conflicted with its constructor. Its PARTIAL recovery, two attempted admissions/unknown reservations and real fallback artifacts are retained. It is not a successful cancellation or model execution. Both probes and exact observer sources are preserved in [the evidence directory](../verification/real-provider-cancellation-2026-10-28/summary.json).

This closes one local in-flight request/safe-boundary case; it is not a forced provider abort, refund, exhaustive race test or hosted PostgreSQL/live-Meta acceptance. The existing private original-investigation ledger was reused without changing caps or resetting reservations. Provider billing reconciliation remains separate. Hosted replay cancellation is verified independently; hosted live Meta still returns404.

## Real provider timeout/deadline case, 28 October2026

Local real-HTTPS runf89995d5 used a deliberately one-second execution deadline, one step/tool allowance and an actual queued/leased worker. One request was sent to Meta; the client observed a genuine socket TimeoutError. At roughly1.317seconds the expired lease/deadline rejected late writes and reconciled the job/run to TIMED_OUT. No numeric artifact, report, automatic retry or second claim followed. The unknown-outcome5697microUSD reservation remains retained; provider usage/billing is unknown. See `verification/real-provider-deadline-2026-10-28/summary.json`.

This is deadline fencing at a safe boundary, not an exact one-second process-kill SLA or remote provider abort/refund. It verifies one local SQLite/real-network path without synthetic replies/delays. Hosted live Meta, exhaustive races and account/invoice reconciliation remain separate.

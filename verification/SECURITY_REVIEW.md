# Security and Production Readiness Review

**Audit date:** 2026-10-26  
**Risk posture:** Local prototype hardening is present; public multi-user production launch is **BLOCKED**.

## Controls observed in code/tests

| Control | Evidence | Assessment |
|---|---|---|
| Meta key server-only | `META_MODEL_API_KEY` consumed in Python adapter; Next browser requests do not receive it. `.env` ignored; mode 0600. | **PARTIAL VERIFIED**: implementation/source and real server request verified. No Git history/remotes available; cannot assert public repository cleanliness. |
| Next-to-FastAPI auth | Production requires 32+ character `API_BEARER_TOKEN`, injected by server-side proxy. | **VERIFIED LOCALLY** by API security tests; this is service auth, not user auth. |
| Host checks | Production requires explicit non-wildcard `ALLOWED_HOSTS`; TrustedHostMiddleware. | **VERIFIED LOCALLY** by tests. |
| Docs/API concealment | Production disables docs/OpenAPI. | **VERIFIED LOCALLY** by tests. |
| Body limits | FastAPI middleware and Next streaming proxy enforce ~64 KiB. | **VERIFIED LOCALLY**, including chunked ASGI body test. |
| Per-process request throttling | Middleware bucket count per ASGI process/peer, `429` and `Retry-After`. | **PARTIAL**: test verifies local behavior; not global/shared and depends on peer address. |
| CSRF/origin guard | Next proxy rejects cross-origin mutations when Origin header is present. | **PARTIAL**: unit/code inspection; no deployment reverse-proxy/browser CSRF acceptance. Missing Origin accepted by proxy as coded. |
| Security response headers | Next configured headers and FastAPI middleware security headers. | **PARTIAL**: source and some route tests; target HTTPS/HSTS ingress not configured/verified. |
| Input validation | Pydantic request constraints and strict tool schema/allowlist/result schema. | **VERIFIED for unit cases**; no comprehensive adversarial/security test. |
| Provider request safety | HTTPS enforced; response body omitted from non-2xx errors; no arbitrary code execution. | **PARTIAL VERIFIED** by source; real invalid-key, injection, timeout, quota tests remain. |
| Dependency security | `npm audit --audit-level=high` reported 0 vulnerabilities; `pip check` passed. | **VERIFIED for local dependency state only**; no SCA/SBOM/license review or fresh pinned install. |

## Critical launch blockers

1. **No user authentication/authorization.** Service bearer token is shared proxy-to-API credential only. No identity provider, session/auth middleware, tenant membership, or user ID on runs.
2. **No per-user run isolation.** Run list, run details, events, artifacts, reports and cancellation are addressed by run ID without an owner authorization check. In a public environment this risks cross-user access/modification.
3. **In-process background tasks.** FastAPI `BackgroundTasks` is not durable; a process restart can interrupt/drop work. No queue, leases, retry/dead-letter semantics or worker monitoring.
4. **Per-process rate limits.** Limits are local memory, not shared across replicas, and peer-IP assumptions need trusted-proxy-safe ingress configuration. No tenant quotas or abuse controls.
5. **No deployable host configuration.** No Dockerfile/compose or hosting manifest; no staging/production endpoint, domain, TLS certificate/ingress, or deployment security test.
6. **No durable operational DB procedures.** PostgreSQL code path exists and local PostgreSQL is asserted historically in build log; this audit did not test deployment persistence, migration/restore, encryption, backup schedule, retention or disaster recovery.
7. **Provider costs/quotas are not truly enforced.** The code reserves estimated tokens per run in memory; provider-reported usage/cost is not logged, `MODEL_MAX_COST_USD` is not shown implemented as a budget calculation, and no account quota alert was tested.
8. **Monitoring and response absent/unverified.** No alerting, audit pipeline, error tracking, provider availability/cost dashboard, incident runbook or operational SLO.
9. **Repository state unknown.** Workspace has no `.git`; source-control secret scanning, tracked-file audit, commit attribution, license/personal-data scan and public repository availability cannot be verified.

## Secret handling

- Expected provider key variable: `META_MODEL_API_KEY`; never print it or add it to frontend config.
- Local `.env` existence, key names only, and `0600` file permissions were checked. Values were not read into output.
- `.gitignore` excludes `.env` and `.env.*`, excluding `.env.example` from that ignore. This is good local hygiene but not evidence a credential has never been committed elsewhere.
- No actual secret-scanning tool was installed/run; no Git metadata exists. Rotate any credential suspected of prior exposure.
- `.env.example` contains variable names and safe placeholders/default model/URL, no secret value observed.

## Docker / dependency / deployment checks

- Docker CLI exists, but there are zero Dockerfiles/compose files/deployment manifests; `docker build` is **not applicable/not run**.
- Node v26.5.0 and Python 3.12.3 present. Runtime installed Python libraries differ from pinned requirements versions; no isolated clean dependency installation was run.
- `npm audit --audit-level=high`: 0 vulnerabilities.
- `python3 -m pip check`: no broken requirements.
- No public repository URL, deploy URL, domain/TLS config, production secret manager, rotation policy, database backup/restore record, or staging security report available.

## Security verdict

Local regression tests verify service-to-service API controls but do not close the public-service threat model. **Do not launch as a public multi-user application** until end-user identity, per-user authorization on every resource, shared abuse controls, durable workers, private service network, target deployment hardening, monitoring and restore drill are verified.
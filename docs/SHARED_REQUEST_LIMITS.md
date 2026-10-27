# Shared request admission and proxy identity

## Contract

The 2026-10-27 increment replaces process-local HTTP counters with SQL-backed fixed-window budgets. All API instances must use the same database and HMAC pepper. A singleton control-row update serializes bucket admission across connections; PostgreSQL holds its row lock until commit and SQLite serializes writers. Database time determines the aligned window boundary and Retry-After. Restarting a process or rotating a socket address does not reset an authenticated account's budget.

| Budget | Limit per 60 seconds | Identity |
|---|---:|---|
| All HTTP requests except liveness | 120 | Canonical peer IP or trusted forwarded IP |
| Authentication POSTs | 30 | Same peer identity |
| Analysis POSTs | 10 | Same peer identity |
| Authenticated requests | 120 | Verified active user and active JWT session |
| Authenticated analysis POSTs | 10 | Same verified user |
| Login attempts | 30 | Normalized proposed email, HMAC digested |
| Invite-authorized registration attempts | 30 | Normalized proposed email, HMAC digested |
| Refresh rotations | 30 | Server-resolved active refresh-session owner after CSRF validation |

Authentication POSTs are register, login, refresh and change-password. Analysis POSTs are research-runs, legacy research-runs, objective refinement, direct tool execution and baseline evaluations. General admission is charged before narrower budgets; a rejected narrower request still consumes the general attempt. Fixed windows can allow up to twice the limit across a boundary; this is not a sliding-window or daily spend ledger. Registration remains invite-gated.

Access-token signature, issuer/audience/lifetime, active user and session checks happen before account budgets. Untrusted claims, body owner IDs and IP addresses cannot choose an account bucket. Login/registration subjects are prospective identifiers, not authenticated identities. Existing escalating login/password failure cooldowns remain; failure increments now use atomic SQL upserts to avoid lost updates between replicas.

## Storage and outages

`request_rate_buckets` stores only a keyed namespace/identity digest, count and expiry. Raw IP addresses, email addresses, JWTs and refresh secrets are not stored in these buckets. HMAC pseudonyms are still security metadata, not a claim of anonymization. Expired rows are removed on admission; idle expired rows can remain until the next admission. Capacity is bounded to 10,000 live buckets across namespaces. Saturation rejects new buckets rather than evicting live counters and enabling resets. It can temporarily deny other callers; ingress abuse controls are still required.

Denials return 429 and a Retry-After derived from database time. Counter/database failures fail closed with a generic 503 and Retry-After 1, without reflecting exception details. `/health` bypasses these quotas as liveness; a 200 is not proof of database readiness or ability to accept work. Valid service authentication is checked before SQL admission in production. End-user authorization remains independent of that credential.

These counters bound request admission, not concurrent body streams, CPU usage, long-lived SSE connections, tenant daily consumption or provider cost. Durable queue owner/concurrency limits are separate. Per-request/per-run model budgets do not constitute a globally reserved provider spend ledger.

## Trusted proxy deployment

By default, Next does not forward any browser-supplied client IP header. FastAPI budgets therefore aggregate the BFF socket peer; verified account budgets still work. This conservative fallback can throttle multiple users behind one BFF and is not individual-client attribution.

To enable client-IP attribution, all of these deployment conditions are necessary:

1. Keep FastAPI private. Configure the same server-only service credential in Next and FastAPI; never expose it through browser code or logs.
2. At the trusted public ingress, strip and replace one dedicated header with a single verified client IP. Configure its exact header name in the Next server's `NEUROLAB_TRUSTED_CLIENT_IP_HEADER`. Only configure a header your ingress actually replaces; browser-controlled X-Forwarded-For or arbitrary header values are insufficient.
3. Next validates a single IPv4/IPv6 address and sends it as `x-neurolab-client-ip`. Comma lists, zone IDs and invalid addresses are discarded. The browser's own dedicated header is never copied. An unset or invalid header configuration uses socket-peer aggregation.
4. Set FastAPI `NEUROLAB_TRUSTED_PROXY_CIDRS` to exact BFF socket networks. Default is `127.0.0.1/32,::1/128`. Wildcard /0, empty and malformed configurations are rejected. IPv4-mapped IPv6 identities are canonicalized.
5. Run Uvicorn with **`--no-proxy-headers`**, or an equivalent ASGI configuration that preserves the actual transport peer. Otherwise an upstream header processor can replace the client scope before this trust check. Do not put a permissive proxy-header middleware in front of it.
6. FastAPI accepts the dedicated forwarded value only when both the actual socket peer is trusted and the server credential matches. Otherwise it budgets the canonical actual peer. Client IP is never resource ownership.

Local synthetic-header tests prove these application rules. They do not prove that a target hosting platform strips/replaces its ingress header, preserves the socket peer or makes the API private. Rehearse spoofed headers, multiple replicas, IPv6, shared-account quotas, denial responses and database outages through the actual deployed ingress before enabling signup. Keep ingress connection/body/time limits and monitoring outside the app as well.

## Validation and remaining gates

`tests/test_shared_rate_limits.py` exercises separate SQL connections, exact admission counts, restart persistence, boundary/Retry-After, capacity without eviction, pseudonym storage, atomic failure increments, proxy trust and fail-closed middleware. API tests execute real Ghana numeric profiles under a shared owner budget across distinct peers, reject invalid-JWT bucket allocation and bound actual refresh rotation. Proxy tests verify trusted-header opt-in and reject raw browser forwarding. Synthetic identities/clocks are operational test inputs, not scientific measurements.

`verification/postgresql-shared-rate-tests.json` records the actual disposable local PostgreSQL run, including durable-job fixture regressions. It is not target deployment acceptance. Provider-wide/user daily spend reservation, refresh replay HTTP audit, production key rotation, external HTTPS/browser acceptance, supervised deployment, production backup/retention and independent live-model quality remain open. Meta inference stays paused after exhausted credits; no paid verification is authorized by this increment.

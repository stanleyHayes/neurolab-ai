# Authentication deployment checklist

## Before starting an API instance

- [ ] Use a persistent production database and rehearse the schema upgrade on a copy; verify pre-existing `runs` remain ownerless and inaccessible.
- [ ] Generate an Ed25519 PKCS#8 private key and a separate 32+ random-byte HMAC pepper. Inject via backend secret manager; never check them into git or Next public variables.
- [ ] Configure stable `AUTH_JWT_KID`, exact production `AUTH_JWT_ISSUER`, `AUTH_JWT_AUDIENCE`, and strong `AUTH_INVITE_CODE`.
- [ ] Configure independent 32+ character `API_BEARER_TOKEN`; keep FastAPI private and pass only to Next server runtime.
- [ ] Set explicit non-wildcard `ALLOWED_HOSTS` and HTTPS-only public ingress. Confirm production refresh and CSRF cookies are Secure.
- [ ] Configure trusted ingress request size limits, shared IP/account throttling, registration/invite issuance, per-user active-job quotas, and provider spend limits before admitting users.
- [ ] Configure persistent logs/alerts, security contact, key rotation, incident response, retention, encrypted backups, and a restore rehearsal.
- [ ] Run two-account access-control tests through the deployed Next BFF and FastAPI origin; test CSRF, cookie flags, guessed UUIDs, SSE reconnect, and sign-out.

## Invite and first-account process

There is no public self-service account administration or email verification. Registration returns 403 unless `AUTH_INVITE_CODE` is configured and a matching invite is supplied. The single configured invite is shared and is only suitable for controlled testing, not scalable invitation management. Issue it only to approved testers over a secure channel and rotate it after the test.

## Password recovery

No outbound mail service exists, so there is no password-reset endpoint or reset token. Safe operator-assisted recovery is: verify the requester's identity out of band, stop/secure the API process, run a one-off trusted admin script that uses `neurolab.auth.hash_password()` and a parameterized transaction to set a new password and `password_changed_at`, revoke every session for that account, record an audit event without the password, then restart and instruct the user to sign in. Never ask a user to send a password to support or set a known shared temporary password. A supported, audited CLI is future work.

## Rollback / key rotation

Back up and verify restore before schema changes. Current schema initialization adds `owner_user_id` without assigning legacy records; roll forward is preferred. Rolling back application code must not expose the now-private run store again; use an isolated database backup and keep the service closed. For JWT rotation, configure the new signing `kid`, provide a verification keyring with the old public key accepted during overlap, roll all instances, wait at least max access lifetime, then retire old key. The application supports a verification keyring; actual target distribution and retirement remain operator-controlled and unverified. Do not rotate ad hoc while the service remains open.

## Go/no-go

Authentication is a useful prototype hardening contribution, not a production launch authorization. Public multi-user release remains **NO-GO** until global/shared abuse and spend controls, durable jobs, target DB migrations/backup-restore, TLS ingress, observability, key rotation, and deployed browser/security acceptance are demonstrated.
## 2026-10-27 local durability evidence

[Durable research jobs](DURABLE_RESEARCH_JOBS.md) now documents SQL queue admission, atomic owner quotas, leased/fenced standalone execution and explicit interrupted states. SQLite and actual disposable PostgreSQL tests are recorded. The worker needs no API signing key and does not serve HTTP. `verification/local-pre-queue-backup-restore.json` proves a private local data restore, not target backup operations. Before release, configure consistent limits and supervised workers, test the migration on the actual target, verify shared HTTP/account abuse and provider spend controls, and retain the HTTPS/identity/key-rotation/monitoring gates above. Signup remains invite-gated.

## Shared request admission increment 27 October 2026

[Shared request admission](SHARED_REQUEST_LIMITS.md) now has local SQLite/PostgreSQL and API/proxy evidence. Require one database/pepper across replicas, explicit trusted socket CIDRs, Uvicorn `--no-proxy-headers`, and a verified ingress that replaces the configured client-IP header. Without that configuration use aggregate BFF-peer quotas plus verified-account quotas. Rehearse the actual target chain and fail-closed behavior. This closes local process-counter isolation, not provider spend reservations or public deployment acceptance. Signup stays invite-gated.

## 2026-10-27 shared model reservations

[Shared model spending](SHARED_MODEL_SPENDING.md) adds SQL run/owner-day/global-day money and token reservations before transport, pinned policy matching and audited compare-and-swap changes. Local mocked-transport/actual-SQL evidence is separate from real provider billing. Unknown calls retain charges; replay requires no prices and makes no reservation. Real pricing/overhead/billing verification, provider-account controls, key rotation, deployed HTTPS/browser/operations and independent live Meta quality remain open. Signup stays invite-gated; Meta remains paused.

## Signing key overlap increment 27 October 2026

Use [the staged signing-key rotation runbook](AUTH_SIGNING_KEY_ROTATION.md): distribute the upcoming public verifier before changing signers, stop all old issuers, drain the access lifetime/leeway, then remove the old verifier. Overlap retirement is operator-controlled. Local fixture/API tests are separate from actual deployed secret distribution, monitoring, retirement and incident response. Do not rotate the HMAC pepper as part of this operation.

## Hosted export restore rehearsal — 27 October 2026

[The snapshot restore runbook](POSTGRES_RECOVERY_REHEARSAL.md) now records a real hosted Render export restored into an isolated local PostgreSQL 18 cluster, with all application table counts/content digests and sequence inventory/state matching. Runtime secrets remain separate from database snapshots. This closes the recorded snapshot/data verification step; managed PITR cutover, scheduled offsite retention, independent key custody, alerts and target operational recovery remain open.

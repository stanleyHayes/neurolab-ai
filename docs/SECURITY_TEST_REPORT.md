# Authentication security verification report

**Date:** 2026-10-26  
**Scope:** Source implementation and local deterministic tests; not a deployment penetration test. Do not interpret as public-production approval.

## Automated cases added

- Argon2id password hash, correct/wrong verification, and minimum-length policy.
- Ed25519 access claims and 12-minute lifetime; tampered signature rejection; exact `kid`/algorithm header check.
- Opaque refresh/CSRF randomness and keyed-hash verification.
- Atomic session rotation and old-refresh reuse family revocation.
- RunStore owner filtering and unowned-legacy quarantine.
- Real API registration, generic wrong-password response, normalized email uniqueness, CSRF on refresh, refresh rotation, password change, logout revocation.
- Two-account isolation: owner B cannot list/read owner A run metadata, reports, artifacts, SSE, or cancellation; owner A remains authorized.
- Production service-to-service credential remains independent of user JWT; hidden docs and host controls remain covered.

Test command and actual final output will be recorded in `BUILD_LOG.md` after the complete quality gate.

## Not yet tested / known gaps

- Registration/login abuse control is partly shared database cooldown keyed by normalized account hash plus per-process peer throttle. No distributed/global IP limiter, signup quotas, email verification, or production staging exercise.
- No multi-process concurrent refresh/registration stress test against PostgreSQL. SQLite serializes the store's process-local calls; PostgreSQL uses row locking, but deployment concurrency is not rehearsed.
- JWT signing currently uses one active configured `kid`, not a persisted multi-key verification keyring. Rotation requires operator-managed overlap/process rollout and has not been rehearsed.
- Full invalid `alg`, unknown `kid`, wrong issuer/audience, `nbf`, expiry, inactive account, revoked session, and role-escalation table-driven API tests are incomplete. Code pins EdDSA and checks required claims; local expiry boundary tests are not a substitute for the full matrix.
- Same-origin browser SRI/cookie behavior is unit/API tested but not exercised in a production HTTPS browser deployment.
- No email reset, email verification, TOTP/WebAuthn, account deletion, admin management UI, or verified operator CLI exists.
- No user-owned uploads/experiments/exports are currently implemented; future resources require ownership before exposure.
- Shared abuse controls, durable job runner, provider cost ceilings, backups/restore, monitoring/incident response, deployment TLS/private-network, and security review remain release blockers.
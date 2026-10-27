# First-party JWT authentication

## Status and scope

Implemented first-party FastAPI authentication (no identity provider): registration with an operator invite, sign-in, sign-out, sign-out-all, current profile, profile display-name update, password change, and rotating refresh. Password reset by email is intentionally absent because no verified delivery provider is configured. An operator-assisted reset procedure is in `DEPLOYMENT_AUTH_CHECKLIST.md`.

Production still is **not approved for public launch**. Registration requires `AUTH_INVITE_CODE`; the current auth/login cooldown is stored in the application database and the edge request throttle is per-process. Neither is a substitute for a shared distributed abuse-control service. Provider spend limits, durable jobs, backups, deployment TLS, monitoring, and operations remain blockers.

## Token and password handling

- Password hashes use Argon2id (`argon2-cffi` defaults), minimum 12 characters, maximum 1024.
- Email is stripped, case-folded, and uniquely constrained.
- Access tokens are Ed25519/EdDSA JWTs, 12-minute lifetime, with `kid`, `iss`, `aud`, `sub`, `sid`, `iat`, `nbf`, `exp`, `jti`, and `token_type=access`.
- API validates an allowlisted EdDSA algorithm/key ID, exact issuer/audience, required time/identity claims, active user, and active unrotated session. Tokens are not stored in browser storage.
- Refresh tokens are opaque 48-byte random values. The database stores keyed HMAC-SHA-256 hashes using `AUTH_TOKEN_PEPPER`; each successful refresh atomically rotates session state. Reuse revokes its family.
- Refresh cookie: HttpOnly, SameSite=Lax, `/api/auth`, Secure in production. A separate readable CSRF cookie uses double-submit header comparison; refresh also checks the stored keyed CSRF hash.
- The `API_BEARER_TOKEN` remains service-to-service only, forwarded as `X-NeuroLab-Service-Token`. It is not a user identity or access token.

## Configuration

Set on the FastAPI process and Next.js server as appropriate:

```dotenv
AUTH_ED25519_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----"
AUTH_JWT_KID=neurolab-ed25519-2026-01
AUTH_JWT_ISSUER=https://your-real-origin.example
AUTH_JWT_AUDIENCE=neurolab-web
AUTH_TOKEN_PEPPER=<at-least-32-random-bytes>
AUTH_INVITE_CODE=<operator-issued-high-entropy-invite>
```

Use a secret manager, not source control or `NEXT_PUBLIC_*`. Example key creation: `openssl genpkey -algorithm ED25519 -out auth-ed25519.pem`; protect the private file (`0600`), inject the PEM securely, and rotate key IDs with an explicit old-public-key verification overlap before changing production. Current local development generates ephemeral Ed25519 key material if no key is configured, invalidating local JWTs on process restart.

Production startup fails closed if private key, token pepper, key ID, service bearer, or host allowlist configuration is missing/invalid. The API does not load `.env` automatically.

## HTTP contract

All browser-facing requests go through same-origin `/api/*` BFF and carry a server-only service credential plus a separate `Authorization: Bearer <access JWT>` for user identity. `Set-Cookie` values are relayed without exposing the service token.

| Method | Route | Purpose |
|---|---|---|
| GET | `/auth/csrf` | Initialize the short-lived anonymous double-submit CSRF cookie. |
| POST | `/auth/register` | Invite-protected account creation; returns access token and sets refresh cookie. |
| POST | `/auth/login` | Generic credential error; returns access token and sets refresh cookie. |
| POST | `/auth/refresh` | Requires refresh cookie, matching CSRF cookie/header and session hash; rotates token family. |
| POST | `/auth/logout` | Authenticated revocation of current session; clears cookies. |
| POST | `/auth/logout-all` | Revoke all sessions for current user. |
| GET | `/auth/me` | Sanitized current-user profile. |
| PATCH | `/auth/me` | Updates display name only. |
| POST | `/auth/change-password` | Requires current password; signs out all other sessions. |

No password reset endpoint is implemented. Do not add one until verified outbound email, single-use expiring reset records, generic responses, and anti-enumeration/rate controls exist.

## Persistence and legacy data

`RunStore` initializes/migrates `users`, `auth_sessions`, rate-limit records, and `runs.owner_user_id` with owner/time indexes. SQLite enables foreign keys. Owner is derived only from the verified JWT, never from request fields. Existing rows migrate with `owner_user_id=NULL`; they remain preserved but inaccessible to all users. Do not assign them to the first account.

SQLite schema initialization is currently in `RunStore.__init__` and is repeatable. PostgreSQL schema compatibility has not been rehearsed against a fresh deployment database; complete that before production rollout.

## Endpoints and privacy

Curated Ghana reference dataset and profile are read-only but require identity. Every run list, detail, report, artifacts, event stream/reconnect, and cancellation route requires active identity and scopes the run query by `(run_id, owner_user_id)`. Missing, guessed, unowned legacy, and other-user IDs all return 404. SSE rechecks ownership and session activity at polling boundaries. Exports are produced client-side only from authorized run responses; no shared server export file is created.

See `USER_ISOLATION.md`, `SECURITY_TEST_REPORT.md`, and `DEPLOYMENT_AUTH_CHECKLIST.md` for boundary conditions and remaining gates.
## 2026-10-27 refresh replay HTTP correction

A valid original refresh cookie and its matching stored CSRF nonce now reach atomic reuse detection even after rotation (including an expired rotated ancestor). Admission resolves the owner but does not authenticate an ancestor or issue it an access token. Reuse revokes the family, returns a generic 401 and clears both cookies on the actual returned response. A forged CSRF pair returns 403 without revoking the descendant; an independent login family remains active. PostgreSQL rotations/replays acquire the user row before session rows so a concurrently created descendant cannot escape the family-revocation snapshot; SQLite serializes the transaction with BEGIN IMMEDIATE.

Actual HTTP tests cover descendant access denial, cookie clearing, expired ancestor reuse, independent family isolation and forged-CSRF non-revocation. Separate-connection races run against SQLite and actual disposable PostgreSQL; this is local evidence, not target browser/TLS or complete authentication lifecycle acceptance. The frontend serializes refresh within its own client instance; concurrent legitimate refreshes across tabs/devices can still trigger strict family reuse revocation and require sign-in. No grace period is claimed.

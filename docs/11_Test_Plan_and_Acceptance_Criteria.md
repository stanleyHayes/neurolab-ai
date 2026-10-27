# 11 — Test plan and definition of done

## Data
Ghana combined 864, component 432 each; Ghana condition counts match; IITA full irrigation 337,913 physical, 336,953 empty, 960 substantive; manifest hashes match; parsing retains original source row; quarantine never silently drops nonempty invalid rows.

## Scientific
Missing values stay null; yield retention handles zero/negative control; uncertainty intervals computed by appropriate resampling; environment/replication handling reviewed; invalid pooled comparisons blocked; result cites input hash and analysis version.

## Agent
Strict schema rejects unknown tool; two result-dependent actions; budgets respected; timeout/cancellation; no free-form execution; failure recovery; evidence citation verification; Meta adapter integration smoke tested; replay clearly labeled.

## UI
Charts match API values; no synthetic 'live' events; keyboard/reduced motion; presenter mode 1080p; accessible evidence and limitations; no blocking animation during API failure.
## Production security

Production startup fails closed without a 32+ character server-to-server token, Ed25519 private key, 32+ byte refresh-hash pepper, invite secret, and explicit host allowlist; `/health` exposes no provider or credential state in production; docs/OpenAPI are disabled; body limits apply with and without Content-Length; bounded throttles emit 429/Retry-After; security headers and same-origin mutation checks are verified. Local first-party auth tests cover Argon2id, EdDSA tokens, refresh rotation/reuse, CSRF, logout/password change, and two-account ownership of runs/events/artifacts/reports/cancel. Deployed HTTPS browser checks, complete JWT edge-case and concurrency matrix, shared throttling, durable jobs, backups, observability, billing limits, and key-rotation rehearsal remain external release gates.

## Submission
Public repo clone and run works; video exactly <=3 minutes; URL accessible unauthenticated; track chosen; team members listed; no pre-event implementation misrepresented; credits not exceeded; submitted before official deadline.

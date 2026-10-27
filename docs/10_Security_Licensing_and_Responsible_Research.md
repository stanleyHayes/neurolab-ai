# 10 — Security, data rights, scientific integrity

Data license: Ghana Zenodo CC BY 4.0; IITA dataset landing page CC BY 4.0. Include citations and license copies/notices. Verify that included raw files correspond to stated sources before public redistribution. Do not include CIRAD CC BY-NC-SA data without explicit permissions for intended uses.

Keys: ignored local env; secret manager for deployment; redact model prompts containing secrets; server-side inference only. Model cost caps and request limits; input size cap; CSV injection sanitization on export; prohibit arbitrary code execution by model; dependency pinning and license review.

## Runtime hardening implemented (2026-10-26)

- FastAPI production profile requires an explicit host allowlist and a 32+ character server-to-server bearer secret; except for minimal liveness, API requests require that secret. OpenAPI/docs are disabled in production. Never use this shared service credential as end-user identity/authentication.
- FastAPI and its Next.js proxy enforce 256 KiB request-body limits (including structured Unicode research briefs). FastAPI applies bounded per-process/per-peer request limits, returning `429` and `Retry-After`; Next.js rejects cross-origin state-changing requests. Security response headers are set at both tiers; HTTPS ingress remains an operator responsibility.
- Production deployment must keep FastAPI private to the Next.js service. The bearer token is injected by the server-side proxy and must not be exposed to browser code.
- First-party user authentication and per-owner research-run authorization were added on 2026-10-26; see `docs/AUTH_CUSTOM_JWT.md`. The service bearer remains a separate Next-to-FastAPI credential. Signup is invite-gated.
- **Launch blockers:** throttling/cooldown is not a globally shared abuse-control system and trusted-proxy IP behavior is unverified; jobs are in-process background tasks, not a durable queue; production hosting, managed DB migration/backup/restore, provider billing limits, signing-key rotation, deployment TLS and operational monitoring remain unimplemented/unverified. Do not advertise this as a public multi-user production-ready service until those are closed.

Science: hypotheses and results must be separated; confidence intervals, sample size, assumptions and uncertainty visible; no claims of proven causal effects or guaranteed yield. Dataset cards include time, locations, trial design, units, missingness and provenance.

Hackathon: public repo; original contributions implemented within event; disclose reused assets; no unlicensed graphics/music; video shows only new features; source evidence and commit history preserved. Track eligibility and award requirements from official guide; avoid unsupported 'all bonuses guaranteed' messaging.

## 2026-10-27 shared admission addendum

The historical per-process limiter and in-process-job limitations above are superseded by [SQL request admission](SHARED_REQUEST_LIMITS.md) and [durable jobs](DURABLE_RESEARCH_JOBS.md). Peer, verified-account and prospective-login-subject quotas now coordinate across SQL connections, with bounded pseudonymous buckets, database-time expiry and fail-closed responses. Trusted forwarded IP requires a service credential and trusted socket CIDR; the BFF copies only an explicitly configured ingress single-IP header. Production ingress/private-network proof, provider-wide spend reservations, refresh replay HTTP audit, key rotation, HTTPS/browser acceptance and target operations remain open. Do not enable public signup or claim production readiness from local tests.

## 2026-10-27 shared model reservations

[Shared model spending](SHARED_MODEL_SPENDING.md) adds SQL run/owner-day/global-day money and token reservations before transport, pinned policy matching and audited compare-and-swap changes. Local mocked-transport/actual-SQL evidence is separate from real provider billing. Unknown calls retain charges; replay requires no prices and makes no reservation. Real pricing/overhead/billing verification, provider-account controls, key rotation, deployed HTTPS/browser/operations and independent live Meta quality remain open. Signup stays invite-gated; Meta remains paused.

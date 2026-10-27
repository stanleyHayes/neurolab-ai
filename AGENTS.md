# Codex agent instructions — NeuroLab AI

You are building a hackathon scientific research prototype. Read README, Agent_plan, Architecture, all relevant docs before implementation. Treat the files in this pack as authoritative; never silently use superseded specifications.

## Non-negotiable
- Implement reproducible, statistically honest analysis on uploaded real datasets first. Never fabricate observed measurements, scientific discoveries, model calls, screenshots or benchmarks.
- Do not call a model's narrative a scientific result. Numeric tools compute; Meta models propose tool calls and summarize verified outputs.
- Use structured JSON schemas for all agent actions; validate on server; enforce tool allowlist, timeout, max iterations, cost and token budgets; log every action.
- Treat source CSVs as immutable. Never mix Ghana combined and component files as independent observations.
- Never join IITA datasets by row order or ENTRY alone without proving matched year/replicate/environment semantics.
- Preserve original columns in raw staging; canonicalize via explicit maps; retain source-row IDs and lineage.
- All charts and cinematic events must be driven by actual tool execution and persisted results. No fake 'live science'.
- Prioritize backend/data/evaluation before animation. Keep full build runnable without paid credentials using deterministic fixture/replay mode, visibly labeled.
- Document every new contribution made during hackathon; do not claim prior documents as code built during event.
- Tests required before marking tasks done. Public repo must not contain API keys, private data, or restricted assets.
- End-user access uses first-party FastAPI auth, not the service bearer. Every private resource is owner-scoped; never expose unowned legacy records or trust owner IDs from request bodies. Keep access JWTs out of browser storage and refresh cookies CSRF-protected.
- Signup remains invite-gated until shared abuse, job, and provider spend controls are verified. Do not claim public-production readiness from authentication tests alone.

## Suggested stack
Next.js/TypeScript frontend; Python FastAPI scientific service backed by PostgreSQL (SQLite retained for isolated tests); optional Go gateway only if time permits; Meta Model API or eligible open-weight inference adapter; GSAP/R3F selectively. Prefer simplest functioning stack over architecture sprawl.

## Completion format
For each task: files changed, commands/tests run, actual output, limitations, next blocker; append `BUILD_LOG.md`. Do not say 'implemented' without committed, testable code. If credentials/model access unavailable, build contract mocks and mark integration BLOCKED.

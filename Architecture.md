# Architecture — verified science first

```
Next.js UI (dashboard / lab / evidence / replay + same-origin auth BFF)
| typed HTTPS + SSE + in-memory EdDSA access JWT
Python FastAPI (first-party identity / experiments / tool registry / event stream)
  |-- Data loader -> immutable CSV -> normalized Parquet/SQLite
  |-- Stats tools -> estimates / confidence intervals / plots
  |-- Experiment runner -> bounded research tasks -> persisted artifacts
  |-- Agent orchestrator -> Meta API adapter / open-weight adapter
  |-- Evaluator -> task benchmarks, trace checks, cost accounting
`-- Artifact store -> provenance manifest / reports / figures
```

User authentication uses Ed25519 access JWTs plus opaque rotating refresh sessions; the shared Next-to-FastAPI service secret is a separate header and is not an end-user identity. `owner_user_id` scopes runs and nested evidence resources. Legacy unowned rows remain quarantined. Current auth docs: `docs/AUTH_CUSTOM_JWT.md`, `docs/USER_ISOLATION.md`, and `docs/DEPLOYMENT_AUTH_CHECKLIST.md`.

The 'experiment' in P0 is a computational research analysis on observed trials. It does not claim to change a real crop's water supply. Optional crop-model simulation is a separate, clearly labeled track with independent validation gates.

Use SSE events (`run.created`, `hypothesis.proposed`, `tool.requested`, `tool.validated`, `tool.completed`, `evidence.updated`, `decision.recorded`, `run.completed`, `run.failed`) emitted only after corresponding state transitions. IDs and timestamps must be stable. Backend controls execution; frontend never invents state.

Contracts: `schemas/agent_tool_call.schema.json` and `schemas/research_result.schema.json`; add OpenAPI generation from FastAPI. The scientific service persists runs, events, and artifacts in PostgreSQL; SQLite is retained only for isolated in-memory tests. Protect model keys server-side, rate limit and redact logs. Production-like demo must run from clean checkout with seeded real data and no hidden network dependency except configured inference.

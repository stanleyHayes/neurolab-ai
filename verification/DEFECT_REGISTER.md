# Verification Defect Register

**Audit date:** 2026-10-26  
**Meaning:** Findings are verified by a direct run/test or by clear code/config absence. Priority is based on risk to the stated scientific product, public safety, launch, and demo acceptance.

| ID | Severity | Finding | Evidence / affected files | Acceptance impact | Recommended priority |
|---|---|---|---|---|---|
| D-01 | **CRITICAL** | Live Meta workflow did not answer the requested scientific question: profile -> missingness -> invalid action -> safe recovery repeats profile. No ranking, stability, or next experiment. | Direct run `a150a5bb-15db-44f9-bc28-36a7fb1d770c`; `neurolab/agent.py`, `neurolab/tools.py`; details `AGENT_EXECUTION_TRACE.md`. | Fails first milestone, P0 autonomous-research requirement, demo claim. | P0 before demo. |
| D-02 | **CRITICAL** | No end-user authentication, authorization, or per-user resource/run isolation. Service bearer token is only server-to-server. | `neurolab/api.py` routes and `app/api/[...path]/route.ts`; security docs. No identity middleware/owner columns. | Public multi-user launch exposes shared history/resources; cannot launch publicly. | P0 before any public launch. |
| D-03 | **CRITICAL** | `hypothesis.proposed` is emitted with generic fixed backend summary, not a recorded model-generated falsifiable hypothesis. | `neurolab/agent.py::run`; live trace step 2. | UI implies a scientific agent step not actually performed; violates event truth and autonomy. | P0 before demo. |
| D-04 | **CRITICAL** | Genotype “tolerance/stability” evidence is not implemented at decision-grade level: ranking lacks uncertainty, design adjustment, multiplicity correction and stability statistic. | `neurolab/science.py::rank_genotypes`; no environment stability handler in `neurolab/tools.py`. | Descriptive ranking cannot support “strongest drought tolerance while stable” conclusion. | P0 scientific scope correction. |
| D-05 | **CRITICAL** | Runs/artifacts/events/reports are not scoped to a user; list/get/cancel API uses global `STORE`. | `neurolab/api.py` `/research-runs*`; `neurolab/store.py` schema has no user ownership. | Cross-user disclosure/cancel risk in multi-user deployment. | P0 with identity. |
| D-06 | **HIGH** | JSON tool-call schema advertises actions without registered handlers; live response supplied a parameter invalid for selected action and was rejected/recovered. | `schemas/agent_tool_call.schema.json`; `neurolab/tools.py::REGISTRY`; trace `decision.failed`. | Agent wastes budget/steps and fails progress; false capability surface. | P0 before demo. |
| D-07 | **HIGH** | Safe recovery on bad model decision repeats `dataset_profile`, generating duplicate evidence rather than recoverable, objective-relevant analysis. | Live trace decision 3; `neurolab/agent.py::_run_meta`. | Run says complete event but report partial/no recommendation. | P0 before demo. |
| D-08 | **HIGH** | `run.completed` is emitted for report whose `completion_status` is `partial`; UI can show terminal completion without clarifying incompleteness. | `neurolab/agent.py::_finish`; live trace terminal events; UI timeline. | Misleading UX and invalid completion signal. | P0 before demo. |
| D-09 | **HIGH** | In-process FastAPI background tasks are not durable across process restart/deployments; no durable queue/worker. | `neurolab/api.py::create_research_run`, `BackgroundTasks`; `Agent_plan.md` release gates. | Run loss/partial run state in production scale-out/restart. | P0 for staging launch. |
| D-10 | **HIGH** | Rate limiting is per process/per ASGI peer, not shared across workers/replicas; proxy trust/peer config not established. | `neurolab/api.py::RequestSecurityMiddleware`. | Easy to bypass by scale-out; abuse/spend control gap. | P0 for public launch. |
| D-11 | **HIGH** | Provider smoke test doesn't record HTTP status, latency, request ID, actual token usage or cost; local reservation is estimate, not actual quota/cost enforcement. | `neurolab/providers.py`; `scripts/smoke_meta_provider.py`; env `MODEL_MAX_COST_USD`. | Unable to audit model identity/performance/spend or protect provider account. | P1 before public demo; P0 for open public launch. |
| D-12 | **HIGH** | Live invalid-key, credit exhaustion, model unavailable, and API timeout persistence/recovery cases were not verified. | `verification/META_AI_INTEGRATION.md`; provider integration tests limited to fake/config cases. | Reliability/security acceptance remains incomplete. | P1 before external demo. |
| D-13 | **HIGH** | IITA data are audited and irrigation cleaning works, but IITA datasets are not normalized into analysis service nor surfaced as app datasets. | `neurolab/ghana.py`, `neurolab/tools.py`, API `/datasets`, `scripts/prepare_data.py`. | User request that Ghana and IITA are both uploaded/inspectable in product is only partially met. | P1; be explicit in demo. |
| D-14 | **HIGH** | No staging/production hosting config, TLS ingress, secret manager/rotation, monitoring, provider quota alert, or database backup/restore drill. | No deployment manifests; `Agent_plan.md`, `docs/10`; filesystem scan. | Explicit production launch blockers. | P0 for public launch. |
| D-15 | **HIGH** | No public Git repository/remotes/history; cannot verify repo cleanliness, public visibility or hackathon attribution. | `git rev-parse` returned “no repository”; no remote available. | Competition submission requirement unverified. | P0 before submission. |
| D-16 | **MEDIUM** | No browser-driven interaction/accessibility/viewport acceptance; static screenshots and HTTP smoke do not test controls. | Chrome headless screenshots exist; no Playwright/Puppeteer/Selenium package; `UI_ACCEPTANCE.md`. | UX/demo reliability not confirmed. | P1 before recording. |
| D-17 | **MEDIUM** | Installed Python versions (FastAPI 0.115.11, Pydantic 2.10.6, Uvicorn 0.34.0, jsonschema 4.23.0) differ from `requirements.txt` pins. | `requirements.txt`, `requirements-dev.txt`; current environment inspection. | Clean deployment may differ from passing test environment. | P1 reproduce clean install. |
| D-18 | **MEDIUM** | No Dockerfile or compose/deploy manifest. | Workspace file inventory. | Reproducible deployment path is absent. | P1 before staging. |
| D-19 | **MEDIUM** | API `/datasets` reports only Ghana and report provenance/card only has Ghana license/source; no in-product source/license evidence for IITA. | `neurolab/api.py::datasets`, React data library; docs/raw readmes. | Dataset capability/provenance UX incomplete. | P1 if claim includes IITA. |
| D-20 | **LOW / optional** | No R3F or 3D crop scene, open-weight model execution, or simulator. | `Agent_plan.md`, `docs/09`, no dependencies/handlers. | Optional visual/open-weight bonuses not achieved; not core science. | Defer unless time and evidence. |

## Severity summary

- Critical: **5** (D-01–D-05).
- High: **10** (D-06–D-15).
- Medium: **4** (D-16–D-19).
- Low/optional: **1** (D-20).

## Required exit criteria for critical items

- D-01/D-03/D-06/D-07/D-08: repeat exact research objective with actual Meta; testable hypothesis recorded with provider provenance; useful result-dependent actions; no invalid parameter dispatch or redundant fallback; final status distinguishes partial/failed from complete; report contains justified follow-up design.
- D-02/D-05: selected identity provider, verified session/auth, tenant/run ownership and authorization on every route and event/artifact/report/cancel/list operation; negative cross-user tests pass.
- D-04: define appropriate cross-environment stability estimand, incorporate trial design or state exploratory limits, quantify uncertainty and multiplicity limitations; independent statistical review before agronomic interpretation.

## Launch gate

Open launch blockers D-02, D-05, D-09, D-10, D-14, and D-15 cannot be waived by a passing local build. D-01/D-03/D-04 block claiming the product is a successful autonomous scientific research platform.
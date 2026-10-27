# NeuroLab AI Implementation Audit

**Audit date:** 2026-10-26  
**Scope:** Read-only audit of the implementation and its current local evidence. The nine files in this verification package are audit deliverables; no product implementation was changed.  
**Overall verified requirement completion:** **55% (22 of 40 equally weighted P0/release checkpoints)**. See methodology below; this is a rubric score, not a code-completion estimate or scientific-quality score.

## Executive finding

NeuroLab is a working Ghana-data research prototype with a real optional Meta Model API path, deterministic scientific tools, persisted run/event/artifact contracts, and a 12-route Next.js workspace. The local quality gate and source-data integrity checks pass. The live `muse-spark-1.3` acceptance run made real provider requests and executed real numerical tools, but **failed the requested autonomous scientific-workflow acceptance**: it selected dataset profiling, then missingness inspection, then an invalid follow-up action that was recovered by repeating the profile. It did not rank genotype tolerance, quantify stability, nor recommend a data-justified follow-up experiment. The emitted hypothesis summary is generic and hardcoded by the backend.

This is **not production-launch-ready**. No end-user identity, per-user run authorization/isolation, shared rate limiting, durable worker queue, target deployment, managed-database lifecycle/backup, or public Git repository exists in the workspace. Chrome headless screenshots exist for all 12 desktop routes and two mobile routes; representative images were visually inspected. Browser-driven interaction, keyboard/screen-reader, and comprehensive viewport acceptance were not performed.

## Architecture verified

| Area | Observed implementation | Assessment |
|---|---|---|
| Frontend | Next.js 16.4.3 App Router; React/React DOM 19.3.1; TypeScript 6.0.3. One shared client workspace renders 12 destinations. | Implemented; build/routes verified. Browser UI is not acceptance-tested. |
| Backend | Python 3.12.3, FastAPI, Pydantic v2, Uvicorn. | Implemented. Runtime installed versions observed: FastAPI 0.115.11, Pydantic 2.10.6, Uvicorn 0.34.0; declared requirements are newer pins (0.162.0 / 2.14.1 / 0.54.0). This environment/version drift is a reproducibility concern. |
| Scientific computing | Standard-library CSV, `statistics`, `random`, `hashlib`, and `math` in the application scientific path; `jsonschema` validates tool/result contracts. NumPy 2.2.3, pandas 2.2.3, SciPy 1.15.2 are installed locally but not used by the production scientific modules. | Descriptive/exploratory methods implemented; no mixed-model package/model or executed correlation endpoint. |
| Persistence | `neurolab/store.py` DB-API adapter for SQLite and PostgreSQL via Psycopg 3. `DATABASE_URL` defaults to PostgreSQL; tests use isolated SQLite. Existing local `neurolab.db` is ignored and not evidence of production persistence. | Code supports PostgreSQL; live PostgreSQL service/deployment/backup behavior not verified in this audit. |
| Meta model | `neurolab/providers.py` OpenAI-compatible HTTPS adapter, configured endpoint/model in local environment, structured JSON schema response. Actual configured model ID: `muse-spark-1.3`; expected credential env var: `META_MODEL_API_KEY` (not `META_API_KEY`). | Real smoke call passed; a real bounded workflow call was observed. Tool decisions did not meet the scientific objective. |
| Run execution / real time | FastAPI `BackgroundTasks` for async run execution; SQL-backed run state, events and artifacts; cursor/`Last-Event-ID` SSE polling/replay. | Single-process demo design, not durable worker execution. SSE state is backend-originated. |
| API routes | `/health`, `/datasets`, `/datasets/{dataset_id}/profile`, `/research-tools/execute`, `/research-runs` (POST/GET), `/research-runs/{id}`, `/events`, `/artifacts`, `/report`, `/cancel`, `/evaluations/baselines`. | Routes present and covered partly by tests; only Ghana dataset enabled for scientific tool execution. |
| UI routes | `/` and 11 section routes: `/experiment-studio`, `/live-experiment`, `/research-results`, `/genotype-explorer`, `/trait-analytics`, `/environments`, `/data-library`, `/ai-insights`, `/next-experiments`, `/reports`, `/settings`. | All returned HTTP 200 and expected page text in local production-server smoke. |
| Deployment | No Dockerfile, compose file, Vercel/Render/Fly config or other deployment manifest found. No Git metadata/remotes. | Not implemented / externally blocked. |

## Authoritative-spec comparison

Reviewed `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/AGENTS.md`, `README.md`, `Agent_plan.md`, `Architecture.md`, and relevant `docs/00`, `01`, `02`, `03`, `04`, `05`, `07`, `08`, `09`, `10`, `11`, `13`, `14`, `15`, and `16` documents.

| Requirement | Finding |
|---|---|
| Real immutable source datasets, explicit mapping, source IDs/hash, lineage | Ghana combined file is used as the only analysis source; 864 rows, SHA-256 retained, source physical row number retained, source columns preserved in `raw_extra_json`. Component files are verified against combined by genotype/environment/replication/block/yield. |
| Never pool component and combined Ghana files as independent data | Analysis loads only `maize_combined_phenotypes.csv`; components are read only during audit. |
| IITA safe clean/audit; no unverified merges | Irrigation clean script removes only fully-empty records and preserves 960 substantive rows and unnamed field. IITA analysis/normalization/pairing is not implemented. |
| Scientific computations by deterministic tools; model proposes actions | The separation exists, but only four real analysis handlers are registered: `dataset_profile`, `compare_regimes`, `rank_genotypes`, `inspect_missingness`. Meta run evidence shows model-selected actions plus recovery. |
| Strict action schemas and server validation | Tool call JSON schema, Pydantic `extra="forbid"`, allowlist, and result-schema validation exist. The schema advertises three actions without handlers (`analyze_trait_association`, `check_environment_stability`, `run_baseline`, `generate_report` are advertised but not implemented; four implemented means only a subset of eight advertised actions is executable). |
| Hypothesis must be testable and model-proposed | **Not satisfied.** `hypothesis.proposed` is emitted with a fixed generic summary independent of a returned model hypothesis; no concrete estimand/null appears in the trace. |
| Two genuinely result-dependent tool choices | First Meta action was unconditioned profile; second did reference the first artifact. Third action was invalid and safe-recovered. This proves one evidence-conditioned choice, not the required two useful choices. |
| Production architecture | Service-to-service production guardrails exist, but user identity, per-user authorization, shared rate limiting, durable workers, deployable hosting and operations remain explicitly open. |
| Visualization spec | Data-driven artifact displays and reduced-motion-aware UI exist. No R3F/3D is included (optional); automated browser/a11y/viewport acceptance not run. |

## Functional feature classifications

Classification is based on implementation **and** actual automated/manual evidence, not code existence alone.

| Feature | Status | Evidence |
|---|---|---|
| Python/Next.js production build and local quality gate | **VERIFIED** | `make quality`: Ruff, format, ESLint, TypeScript, 34 tests, dataset manifest audit, Python compilation, Next optimized build; exit 0 (see `TEST_RESULTS.md`). |
| Ghana source import/profile, 72 genotypes, water regimes, lineage | **VERIFIED** | Source integrity audit + tests; 864 records (432 each regime), 72 genotypes, source hash and physical row IDs. |
| Ghana component/combined non-duplication | **VERIFIED** | Multiset comparison by genotype, ENVT, REP, BLK, yield succeeds for each component vs its corresponding combined regime; API only loads combined. |
| Null handling and structural missingness | **VERIFIED** | Parser maps empty/NA/null/NaN/dot to `None`; bad numeric row retained and quarantined by test; 432 structurally missing stay-green values detected. |
| Regime comparison and cluster-bootstrap interval | **VERIFIED, exploratory only** | Automated seeded-repeat test and independent 500-resample SciPy percentile recomputation exactly match. Confounding caveat present. |
| Drought genotype mean ranking | **PARTIALLY VERIFIED** | Ordering/value recomputed independently and agrees; estimates are descriptive with no uncertainty, alpha-lattice correction, multiplicity control or stability analysis. Not a field recommendation. |
| Drought yield retention | **PARTIALLY VERIFIED** | Tool returns 47.0279%, independently equals `100 × (1230.2688 / 2616.0415)`. It is an observational regime ratio, confounded by environment; UI/report may not imply causal improvement. |
| IITA full irrigation cleaning | **VERIFIED for cleaning only** | 337,913 input records, 336,953 fully-empty removed, 960 output; original raw untouched, unnamed third column retained. No IITA inference or joins. |
| Dataset source/license/provenance | **PARTIALLY VERIFIED** | Ghana DOI/license/hash shown. API dataset list only includes Ghana. IITA source/license remains in docs/raw provenance, no IITA analysis UI panel. |
| Meta provider request | **VERIFIED** | Real schema-constrained call succeeded for `muse-spark-1.3`; provider smoke command passed. See `META_AI_INTEGRATION.md`. |
| Full autonomous scientific workflow | **NOT VERIFIED / acceptance FAILED** | Real Meta run completed partially with a recovered invalid model action; no genotype ranking/stability/follow-up design. See `AGENT_EXECUTION_TRACE.md`. |
| 12 workspace page responses | **VERIFIED (HTTP response only)** | All routes HTTP 200 with expected route title and shared navigation. |
| Browser interaction/accessibility QA | **NOT VERIFIED** | Chrome headless screenshots exist (14 files, 12 desktop + two mobile) and representative screenshots were inspected. No installed Playwright/Puppeteer; no keyboard/screen-reader/control-interaction acceptance. |
| Production security release gate | **NOT VERIFIED / BLOCKED** | Local unit tests prove selected service-level controls, but no user identity or staged deployment; no deployment security testing. |

## Overall completion scoring method

To avoid subjective “percent of code” estimates, use **40 equally weighted acceptance checkpoints** spanning P0 science/data, Meta/agent, UI, production, and submission. A checkpoint counts as a point only with direct implementation and current evidence. Partials count zero unless the checkpoint itself is explicitly a partial-scoped objective. Current estimate is **22/40 = 55%**.

- Green / verified: 22 (quality gate; raw audit/hash; Ghana import/lineage; 72-genotype/profile; two regimes; component/combined audit; missingness; IITA cleaning; descriptive mean/rank arithmetic; yield-retention formula; bootstrap reproducibility/independent match; Meta real call; schema/allowlist; persisted events/artifacts; one evidence-dependent model decision; backend SSE routes; 12 HTTP page responses; loading/errors in source; citations/hash in UI; local production Next build; tested service-level API guards; dependency audit).
- Not green / partial: 18 (full autonomous objective; falsifiable model-generated hypothesis; two result-dependent useful follow-up decisions; agent ranking/stability use; rank uncertainty/design adjustment; association tool; actual recommendation/design; IITA analysis/provenance UI; browser UI acceptance; keyboard/a11y; mobile/tablet/1080p; async cancellation/provider timeout integration; real-user auth; per-user isolation; global throttling; durable worker; deploy/TLS/secrets/monitoring/backup operations; public repo/demo/submission evidence).

This rubric is for launch readiness; it does not mean the app is “55% coded.” It is intentionally stricter than previous planning checkboxes.

## Critical defects

1. **Live agent fails the scientific objective.** It did not run the requested ranking/stability analysis, returned an invalid third decision, and recovery repeated dataset profiling. The run is `partial`, despite a terminal complete event; no validated follow-up recommendation is present.
2. **Hypothesis/progress semantics are overstated.** Backend emits a fixed generic `hypothesis.proposed` event rather than a testable model-generated hypothesis. UI can present it as proposed research activity.
3. **No per-user authentication/authorization or run isolation.** Existing production bearer token protects only Next-to-FastAPI service access. Any browser user routed through Next shares the same global run store/list surface.
4. **No production runtime architecture.** FastAPI `BackgroundTasks` are in-process; current throttling is process-local. Restart/scale-out can lose executing work and limits do not coordinate.
5. **Scientific genotype claim boundary.** Ranking is only an equal-environment descriptive mean and has no uncertainty, environment-stability estimator, alpha-lattice model or multiplicity adjustment. It must not be described as drought tolerance validated across environments.

## High-priority defects

- Shared JSON schema advertises four additional actions with no registered safe handlers; live model may select unsupported actions and require recovery.
- The agent currently emits repeated `dataset_profile` artifacts as the response to an unsupported action; no prevention of redundant/no-progress recovery is evident in the live run.
- No error-path live tests against provider for invalid key, missing key through actual API, provider timeout/credit exhaustion, or model-unavailable operation. Sanitized code/test behavior is not equivalent to observing each live provider outcome.
- Current local installed Python dependencies differ from pinned `requirements.txt` versions; no clean-lockfile/isolated install was performed.
- No API authentication exists for end users, nor ownership filter on `list_runs`, run, artifact, report, event or cancel routes.
- The experiment UI hardcodes `seed=2026` and budgets and exposes a replay choice but no explicit live-provider result verification state beyond report provider/model label.
- Demo-ready deployment/public repository/video are absent.

## Next blocker and prioritized remediation (audit only; no remediation performed)

1. Make the objective executable and meaningful: implement/validate environment stability and selection semantics; validate feasible action/parameter combinations before persistence; generate explicit falsifiable hypothesis from Meta structured output; require two useful evidence-dependent actions and prohibit no-progress duplicate recovery. Re-run the exact objective and preserve trace.
2. Make rankings scientifically scoped: specify estimand, include trial/environment/replication/block structure, report uncertainty/stability and multiplicity policy or keep ranking explicitly exploratory; have an independent reviewer approve assumptions.
3. Close identity/isolation before any public multi-user service; choose an identity provider and enforce owner scoping on every run/artifact/event/report/cancel/list endpoint.
4. Replace process-local controls with edge/shared-store throttling; use durable worker queue and cancellation semantics; validate retry/timeout/provider budget behavior.
5. Provision staging/production hosting, TLS, secrets/rotation, monitoring/alerting, provider quotas/spend controls, database lifecycle/backup/restore; run external security and abuse testing.
6. Add browser automation, keyboard/screen-reader/accessibility checks and mobile/tablet/1080p visual acceptance; verify actual workspace controls and backend charts.
7. Establish public repository/history, attribution and license review, public deployment, three-minute demo recording, and final platform submission evidence.

**Demo-readiness estimate:** approximately **3–5 focused engineering days** for a credible single-user staged demo (agent workflow correctness, traceable recommendation, browser walkthrough, deploy and rehearse), assuming credentials/hosting are available. A safe public multi-user launch is not credibly estimable from current evidence and requires auth, durable ops, monitoring, restore/security work beyond that demo estimate.

## Limitations

- No Git repo exists in the workspace; commit dates/history and public accessibility cannot be checked.
- `.env` key values were not read into output or report. Key presence was verified by variable name only.
- No model logs were found that provide a provider request ID/usage/cost/latency telemetry. Adapter response status was not retained in app logs; the successful smoke response and bounded experiment are direct observation.
- SciPy checks are independent diagnostic arithmetic, not design-valid significance tests. The unadjusted Welch test is explicitly exploratory and not used as an acceptance claim.
- Evaluation command `python3 scripts/run_evaluation.py --seed 2026 --budget 2` returned fixed workflow 6/12, seeded random 3/12, deterministic replay 6/12 target tools selected. It explicitly does not score LLM answer quality or compare live Meta; the label “Meta comparison: not run; live adapter unavailable” describes the fixture evaluation, not the separate real smoke/workflow calls recorded here.
- No full-stack live browser experiment was run. The end-to-end agent was invoked through the backend Python orchestrator with SQLite memory store; API/Next HTTP tests were separate. Existing Chrome screenshots are static captures and do not verify run interaction.
- No Docker build was possible: no Docker configuration exists.
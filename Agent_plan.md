# Codex execution plan — prioritized, autonomous

## Phase 0 (immediately)
- [x] Audit and hash data; execute `scripts/audit_datasets.py`; inspect anomaly report.
- [x] Add a repeatable local quality gate: Ruff lint/format, ESLint plus JavaScript syntax, tests, Python compilation and dataset integrity audit. Configure SonarQube analysis; server-side analysis remains conditional on a provisioned server and token.
- [x] Confirm Meta API credentials and model availability via `python scripts/smoke_meta_provider.py`; set `META_MODEL_VERIFIED=true` only after a successful real response. **2026-10-26: Meta Model API `muse-spark-1.3` returned schema-constrained JSON; one-step live agent run selected an allowlisted action and completed with persisted, tool-derived evidence.**
- [ ] Publish the application source in the public Git repository. Local Git history and `BUILD_LOG.md` now exist; public source publication and licensing remain open.

## Phase 1: Real data MVP (P0)
- [x] Run preprocessing, assert Ghana combined rows = 864 and two regime-specific files = 432 each.
- [x] Validate IITA irrigation file: 337,913 physical records, 336,953 empty, 960 substantive; preserve audit trail.
- [x] Implement canonical normalized Ghana dataset with source IDs, unit metadata and controlled missingness. IITA remains staged/audited, not enabled for analysis.
- [x] Build profile, regime contrast, genotype ranking and missingness endpoints/tools.
- [x] Implement exploratory block-bootstrap comparison and caveats; no confirmatory model.
- [x] Add unit and integration tests with deterministic execution; no separate property-test suite.

## Phase 2: Meta-powered scientific agent (P0)
- [x] Implement allowlisted tool registry and request/result JSON schema validation.
- [x] Implement bounded Meta-compatible structured adapter and model-selected allowlisted tool loop; model selection follows computed evidence, tool schemas and budgets are validated server-side. Fixture tests are not proof of a live Meta call.
- [x] Demonstrate sequential evidence-grounded replay decisions; this is not a live agent demo.
- [x] Store event trace/artifacts and expose concise decision summaries, not hidden chain-of-thought.
- [ ] Score groundedness, adversarial-injection and invalid-action answer quality. The runtime now emits evidence-ID-linked, tool-derived report claims and fake-adapter safety tests; the 12-task catalog checks action coverage only, not generated-answer quality. No live Meta comparison has run.

## Phase 3: Benchmarks and demo (P0)
- [x] Compare replay tool selections with fixed/random workflow baseline using same budgets/tasks. Not a human-rated utility benchmark.
- [x] Build interactive evidence workspace with persisted timeline, source citation, actual measured-result plots, report/artifact exports, saved run replay, provenance and error recovery.
- [x] Implement persisted stage transitions, SSE cursor replay, asynchronous Meta-mode background execution, and safe-boundary cancellation. Replay baseline remains synchronous for deterministic existing fixtures.
- [ ] Complete automated browser/accessibility testing, visual QA at mobile/tablet/1080p, plus test the live provider and prove cancellation under actual async execution. Current evidence report claims are generated from computed artifacts with linked evidence IDs.
- [x] Add a lightweight, explicitly illustrative React Three Fiber maize/soil scene to the overview with orbit/zoom/reset, low-power render settings, WebGL/error fallback, and reduced-motion static mode. The scene does not encode measured crop morphology or simulated measurements.
- [x] Task-scoped browser smoke: desktop WebGL scene and camera buttons, reduced-motion static illustration, and 390px mobile static fallback/no horizontal overflow. WebGL-disabled runtime fallback and full keyboard/screen-reader accessibility acceptance remain pending.
- [ ] Record complete 3-minute demo with visible provenance, live working product and new-code evidence.
- [ ] Verify deployment, README, license attribution, public Git, video access and submission.

## Phase 4: Optional prizes (P1; only after P0 green)
- [ ] Run actual Muse Spark Open/Glimmer through eligible provider and verify eligible serving; capture logs.
- [ ] Publish genuine X demo post and submit its URL if pursuing viral prize; prepare public gallery entry.
- [ ] Consider Muse Image/Wonder-generated explanatory asset only if it materially enhances the scientific experience and complies with prize rules.

## Production hardening (release gate; 2026-10-26)
- [x] Add production API authentication between Next.js and FastAPI, host allowlisting, hidden API docs, request-body caps, bounded per-process throttling, CSRF-origin checking and security headers.
- [x] Implement first-party email/password auth with Ed25519 JWT access tokens, Argon2id, rotating opaque refresh sessions, CSRF cookies, profile/password management, invite-gated signup, and owner isolation for runs/reports/artifacts/events/SSE/cancel. This is not an external identity-provider integration.
- [ ] Verify auth and isolation on deployed HTTPS; configure production secrets/invite process; complete missing exhaustive JWT matrix, concurrency tests, key-rotation rehearsal and browser acceptance.
- [ ] Add gateway/shared-store abuse controls, durable background workers, deployment/DB lifecycle and backup procedures, observability, and provider spend/tenant quotas; validate these on the target deployment.
- [ ] Complete automated browser, keyboard/accessibility, mobile/tablet/1080p and async live-provider acceptance.

## Day-by-day gates
D1 data and repo; D2 normalization; D3 statistical tools; D4 API; D5 Meta agent; D6 closed loop; D7 benchmark; D8 cinematic UI; D9 rehearsal and recording; D10 buffer/submission. If behind, drop optional model/visual features, not validation.

## 2026-10-27 cinematic/setup increment

- [x] Add event-bound cinematic replay cockpit on `/live-experiment`: real artifact reveals, immersive dialog, pause/step/seek/pacing, provenance/export, reduced-motion/manual and 2D fallback, reused optional 3D illustration.
- [x] Redesign research setup actions/configuration/mode cards; expose authenticated model availability and disable paid controls while paused. Add transport-level credit pause and document the local replay-only setting.
- [x] Diagnose the stale port-8000 API behind the draft HTTP 404 and restart the confirmed checkout process with its existing environment/database retained.
- [ ] Visually accept cinematic/setup views in the browser at desktop/tablet/mobile and test the real immersive-dialog/GPU behavior. Current browser access is unavailable; DOM tests are not a substitute.
- [ ] Complete remaining science/answer-quality and production gates above. No new crop simulation, Meta call or scientific analysis is claimed by this presentation increment.

## 2026-10-27 scientific-method increment

- [x] Add deterministic Ghana environment variability/centering and leave-one-environment-out rank sensitivity, keeping regimes separate and incomplete coverage explicit.
- [x] Add genotype-unit drought trait associations with conditional percentile resampling intervals, per-environment correlations, excluded counts and source-row lineage. These are exploratory, not confirmatory stability/causal estimates.
- [x] Wire both methods through strict schemas/registry/plans, bounded execution, artifact-linked report claims/limitations, result tables/association heatmap and event-bound cinematic reveals. Preserve over-budget selected tasks as pending/partial.
- [ ] Complete the full owner's investigation with explicitly evaluated hypotheses, candidate trade-offs and justified follow-up reporting; perform actual browser acceptance. Live Meta acceptance is paused by the owner's exhausted credits.

## 2026-10-27 full deterministic investigation/report increment

- [x] Add an explicit six-method Ghana investigation preset that keeps the exact original objective, declares four retrospective exploratory hypotheses/criteria before execution, and separates workflow completion from scientific validation.
- [x] Make missingness/follow-up ordering genuinely depend on computed evidence and honor the recorded choices. Report source-linked criterion evaluations, contradictions, candidate retention/variability trade-offs and an executed omitted-environment follow-up.
- [x] Add source-byte-verified inventory/comparability evidence, source/manifest hashes, loaded-code provenance and a clearly separate proposed randomized field trial with no invented power calculation.
- [x] Render/export the structured report and add exact-original-objective, partial/mismatched/custom-hypothesis, API and renderer tests. Preserve all six methods across budget limits; fix the persisted plan's former four-approach cap.
- [ ] Verify the full committed profile through the running authenticated service and browser. Live Meta quality remains blocked by exhausted credits; no field-validation or production-launch claim follows from this profile.

## 2026-10-27 portable scientific reporting increment

- [x] Verify the full committed profile through the owner-authenticated running service: `verification/full-investigation-runtime.json`. Browser acceptance remains separate and pending.
- [x] Add owner-scoped terminal evidence bundles and offline HTML reports with four actual-data PNG/SVG figure pairs, unrounded figure data and preserved source/code/event provenance.
- [ ] Finish generated-answer evaluation, live-provider acceptance when credits return, browser QA and external deployment/publication/submission gates.

## 2026-10-27 recorded-answer evaluation increment

- [x] Execute all twelve questions under equal-budget fixed/random/default replay policies; retain all 72 initial/corrected attempts, full artifacts and trace.
- [x] Add strict stale/duplicate/invalid review rejection, explicit null unreviewed scores, identified subjective non-blind assistant ratings and descriptive intervals. Never infer semantic quality from valid calls/citations.
- [ ] Fix focused replay/report relevance gaps revealed by review; complete model-visible adversarial fixtures, feedback ablations, blind review and live Meta comparison when permitted.

## 2026-10-27 focused replay/report relevance increment

- [x] Route automatic focused objectives to supported source/missingness/trait/environment/ranking/contrast methods; persist transparent heuristic constraints and fallback ambiguity. Preserve accepted plans, explicit preferences and full-profile criteria.
- [x] State observed ratio availability/value, denominator/null/noncausal scope and absent rank confidence intervals/probabilities directly. Include per-regime source counts.
- [x] Keep unmatched requested method tasks pending under small budgets; display planning ambiguity in the persisted-plan UI.
- [ ] Verify committed service runtime and record fresh known-question regression evidence without overwriting earlier attempts or inheriting stale ratings.

- [x] Post-commit focused API acceptance: five one-call cases, exact input, persisted numeric evidence and terminal SSE; no Meta.
- [x] Preserve known-question regression and identify the old four-tool/random versus six-tool/router eligibility mismatch. Correct the protocol and collect a separate six-tool 36-answer set with ratings pending; preserve all prior attempts.
- [ ] Complete fresh semantic adjudication of the corrected protocol, independent/held-out/live-provider evaluation and model-visible adversarial tests; retain the known-set and non-blind limitations.
- [ ] Address explicitly observed historical nonterminal state and durable/shared job lifecycle; do not infer an active executor or mark old evidence complete from a stale status alone.

## 2026-10-27 durable queue increment

- [x] Persist owned run/request/admission/events atomically; enforce two nonterminal runs per owner and queue/leased concurrency limits under shared SQL coordination.
- [x] Add standalone worker with database-time leases/heartbeats, stale-worker publication/provider fencing, source-hash preflight, cancellation and inactive-owner handling; never automatically retry started work. Keep legacy unowned records untouched.
- [x] Commit numeric artifacts/completion events and final reports/terminal events atomically. Add owner-only job status and terminal timeout UI/replay handling.
- [x] Verify isolated SQLite and disposable PostgreSQL operational/concurrency tests, separate worker execution without JWT signing key, and private local pre-migration backup/restore.
- [ ] Rehearse the committed API/worker restart and interruption paths on the isolated authenticated review service, then configure supervised local workers.
- [ ] Complete shared HTTP/account abuse controls, provider spend/tenant quotas, target deployment/supervision/backup policy, and remaining browser/live-model/submission gates.

- [x] Committed runtime rehearsal: exact original objective survives API restart and completes through a separate worker; controlled post-claim interruption becomes explicit FAILED/INTERRUPTED without retry/results; continuous worker accepts a fresh owned profile.
- [x] Start replay-only primary/review workers with API inline wakeups disabled; preserve legacy ownerless history and verify local health. Target deployment supervision remains unverified.

## 2026-10-27 shared request admission

- [x] Replace per-process peer buckets with bounded SQL fixed-window admission; add verified-account and prospective-login-subject limits, atomic failure counters, fail-closed behavior and explicit proxy trust. Local PostgreSQL/SQLite tests recorded separately from target ingress.
- [ ] Rehearse actual deployed ingress header replacement/private networking and multi-replica behavior; enforce shared provider/user spend reservations. Keep invite-only signup and Meta paused. Refresh reuse HTTP-path audit, rotation/monitoring and full browser acceptance remain open.

- [x] Correct refresh reuse HTTP path and returned failure-cookie clearing; test descendant family revocation, expired ancestors, forged-CSRF non-revocation and cross-connection rotation/replay races. Deployed/browser cookie lifecycle and key rotation remain unverified.

## 2026-10-27 shared model reservations

[Shared model spending](docs/SHARED_MODEL_SPENDING.md) adds SQL run/owner-day/global-day money and token reservations before transport, pinned policy matching and audited compare-and-swap changes. Local mocked-transport/actual-SQL evidence is separate from real provider billing. Unknown calls retain charges; replay requires no prices and makes no reservation. Real pricing/overhead/billing verification, provider-account controls, key rotation, deployed HTTPS/browser/operations and independent live Meta quality remain open. Signup stays invite-gated; Meta remains paused.

## 2026-10-27 signing key overlap

- [x] Add explicit, bounded Ed25519 verification overlap, current-only issuance, strict startup validation and generated-key/API rollover/retirement tests.
- [ ] Rehearse the committed multi-instance local fixture workflow, then separately verify secret distribution/rollout, retirement, incident response and browser/session behavior on the actual target. Operational keys and pepper remain unchanged.

## Synthetic model-visible containment and feedback controls

- [x] Exercise synthetic CSV labels through actual normalization/ranking/model input, reject programmed unsafe replies and prevent invented model summaries from becoming report claims; retain exact inputs/replies and failed trials.
- [x] Add internal result-feedback withholding with truthful decision/report labeling; keep normal HTTP requests unchanged and replay evidence intact.
- [ ] Execute committed collection; retain live Meta resistance/usefulness ablations, independent semantic review and browser/external delivery as separate unverified gates.


## 2026-10-27 current evaluation and execution boundary

- [x] Preserve ten synthetic CSV/feedback contract trials and complete 36 separate non-blind assistant reviews of the corrected six-tool collection. Historical combined unchecked items above retain their external/live/independent portions; see the current completion ledger.
- [x] Freeze a future live evaluation protocol with twelve accuracy tasks, ten fixed utility tasks, matched budgets/policies/seeds and eleven implementation/source hashes. See `docs/FUTURE_LIVE_EVALUATION.md` and `eval/future-live-protocol.json`.
- [ ] Build/review the future live collector before use, obtain explicit authorization and verified pricing/spend configuration, then execute all preserved trials, independent adjudication, safety and two result-dependent Meta decision acceptance. Meta remains paused; no live outcome is claimed.

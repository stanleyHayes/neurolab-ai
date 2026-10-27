# Original audited objective: failure analysis and correction

Historical evidence: [unaltered trace](AGENT_EXECUTION_TRACE.md), run `a150a5bb-15db-44f9-bc28-36a7fb1d770c`, 26 October 2026. The original store was SQLite `:memory:`; this repository retains the audit narrative, not a recoverable original database or full raw provider-response transcript. Exact prompt bytes beyond the recorded objective cannot be reconstructed honestly.

## Frozen objective and acceptance

“Investigate which maize genotypes demonstrate the strongest drought tolerance while maintaining relatively stable grain yield across the available experimental environments. Form hypotheses, select appropriate statistical analyses, execute the analyses, evaluate the evidence, and recommend the next experiment.”

Expected: falsifiable hypotheses with provider provenance; real genotype ranking and appropriate observed-environment sensitivity evidence; evidence evaluation; justified next trial; two useful result-dependent Meta decisions; valid tool parameters, nonredundant recovery and honest terminal status. Exploratory observational evidence cannot establish field-validated tolerance or broad adaptation. The historical limits were seed 2026, three model decisions, five tool calls, 120 seconds, Ghana combined SHA-256 `2e37c07f30e00efb33b59954dd6d02a04f3d67349790d782b70dbedfdaff05bc`.

Actual: model selected `dataset_profile`, then `inspect_missingness` referencing the first artifact. A third model selection of `dataset_profile` incorrectly supplied `bootstrap_samples`; validation rejected it. Recovery repeated `dataset_profile`. Three artifacts described 864 plots/72 genotypes, 432 observations per regime, missing locations/plot IDs and absent well-watered stay-green. No ranking, uncertainty estimate, stability analysis or justified experiment followed. Report said partial while events said complete. No numeric handler failure was recorded. Estimated token reservation 7,782 is not provider usage/billing.

## Causal diagnosis

| Layer | Finding and current evidence |
|---|---|
| Planning | Primary cause: inspection consumed the bounded workflow without ensuring objective coverage. Current pending-task plans prevent reselection of completed tasks. A newly reproduced defect remained: the exact objective routed solely to environment stability and incorrectly completed that narrowed plan. The correction recognizes explicitly requested maize/drought/genotype/stability/hypothesis/next-experiment investigations and preserves the full six-method contract. Explicit method selections retain precedence. |
| Action contract/recovery | Invalid action-specific resampling parameter was correctly rejected; historical recovery then wasted a step. Current recovery selects the next pending task and records deterministic provenance. Action-specific validation remains essential; a provider may still produce invalid output. |
| Numeric tools | Historical profile/missingness succeeded. Environment sensitivity and structured investigation reporting were absent then and are available now. Fresh real-source execution exercises all six handlers; no mocked results or provider substitutes are used. |
| Dataset | Confounding of regime and trial environment, few environments, unverified stay-green score direction and missing covariates constrain interpretation. These did not cause the invalid action or duplicate profile. Numeric rankings cannot prove strongest biological tolerance or validated stability. |
| Context | The historical trace establishes one evidence-linked decision, not context truncation. No evidence supports blaming context length. Current execution context carries the objective/plan and prior numeric summaries; full historical prompts are unavailable. |
| Report/status | Historically omitted scientific answers and overstated terminal status. Current investigation report includes actual hypothesis criteria/verdicts, candidate trade-offs, executed omitted-environment analysis, limitations and proposed trial; undersized budgets remain partial. Deterministic hypotheses must never be attributed to Meta. |
| Budget | Three decisions cannot execute the six-method contract now required. Retain the historical three-step attempt as partial; any six-step acceptance run is an explicit budget amendment, not an identical-budget success. |

## New execution evidence

- [Before correction](original-objective-diagnostic-2026-10-27.json): exact objective, seed and historical budgets; one real stability calculation, terminal COMPLETE, no structured scientific report. This is preserved negative evidence.
- [After correction](original-objective-routing-fix-2026-10-27.json): same objective/source/seed. Historical three-step/five-call budget ends PARTIAL after profile, missingness and contrast, retaining remaining tasks. Declared six-step/six-call diagnostic executes profile, missingness, contrast, ranking, environment sensitivity and trait associations, with full artifacts/events/report.
- Example actual result: TZm-1179 observed drought mean 2370.2905 kg/ha, observed well-watered mean 3662.5416 kg/ha, descriptive retention 64.7171%, three drought environments and omitted-environment rank range 3–5. This is an exploratory candidate, not a field recommendation or a combined tolerance/stability score.
- Validation: 61 focused Python tests passed, including exact-objective real-data regression at both budgets. Programmed adapter tests validate contracts only.

## Acceptance remains open

Both new diagnostic executions are explicitly deterministic replay with zero model calls, using real measured data and real numeric handlers. They are **not** the requested successful live Meta rerun. The original live acceptance criteria remain unchanged and unmet. Do not remove the README warning or present six-tool deterministic completion as live autonomous success.

Meta credits were exhausted and inference remains disabled. Before a real rerun: confirm restored access, explicit resumption and aggregate USD/token cap, verified pricing/overhead and active shared spend policy/provider limits. Freeze the exact original objective, seed/source, model identity and amended sufficient budgets; preserve all attempts and exact provider prompts/replies/usage/request IDs, tool events/artifacts and report. Require provider-authored falsifiable hypotheses and at least two useful evidence-dependent decisions, then adjudicate the original scientific outputs against numeric artifacts. Missing provider hypotheses, invalid actions, fallback dependence, partial coverage or unsupported claims fail acceptance even if a terminal workflow says complete.

# Full Ghana investigation: explicit deterministic profile

The **Full Ghana investigation** preset keeps the original objective unchanged, selects all six implemented methods, and sets a six-step/six-call/180-second budget. It selects deterministic mode and disables Meta planning for this profile. It is a named retrospective analysis contract, not a general-purpose language model pretending to understand every arbitrary objective. Original user questions/hypotheses remain stored; additional hypotheses outside its fixed criteria are explicitly unassessed and make the run partial.

The optional Meta refinement workflow remains available for ordinary non-profile objectives when the provider is enabled. The named deterministic profile uses fixed declared criteria, so it cannot be silently rewritten through Meta refinement. Changing to a focused/custom investigation requires deselecting its output. Meta is currently paused at the owner's request after exhausted credits; no new live-model acceptance is claimed.

## Declared hypotheses and actual evaluation

Before the first numeric tool request, the backend persists the profile notice, four proposals, rationales and operational evaluation criteria. These are retrospective template proposals, not preregistered hypotheses or model-generated discoveries:

1. A complete-coverage genotype is among the observed drought-yield top quartile in every recorded drought environment. Ranks are compared against ceil(complete panel size / 4); broad adaptation is not inferred.
2. ASI has a negative observed genotype-mean yield association with a strictly negative conditional resampling interval and negative correlations in every recorded environment. A zero-crossing interval or contradictory directions is inconclusive.
3. Lower numeric STYG codes meet the same negative-association criterion. Source score direction remains unverified, so this cannot establish that biologically greener plants perform better.
4. At least one of the three largest observed drought means moves by a quartile of the panel's rank positions or more when an environment is omitted. This is an operational sensitivity threshold, not a formal interaction significance test.

Evaluations are `criterion_met`, `criterion_not_met`, `inconclusive`, or `not_assessed`. Each finding cites actual artifact IDs. Workflow completion is kept separate from scientific validation. Missing tools, source mismatches, insufficient/constant data and custom unassessed hypotheses do not create optimistic results.

## Evidence-dependent follow-up

After profile execution, observed missingness in analytic yield/trait fields selects the missingness audit before comparison; absent such missingness, comparison is selected first. Missing optional location metadata alone does not trigger this rule. After the genotype ranking, leading means observed in multiple environments select omitted-environment rank sensitivity before candidate interpretation. The next actual executed task honors the recorded selection. Both decisions are labeled deterministic evidence rules, with their source artifact IDs. They do not establish live Meta autonomy.

The rank-sensitivity result is reported as an executed follow-up only when its artifact exists. Adaptive selection is claimed only when its recorded decision exists. Merely preplanning/executing the same tool is not mislabeled adaptive reasoning.

## Dataset inventory and comparability

The profile tool inventories all ten source files from the audited manifest. It checks their current bytes against each recorded SHA-256, preserves original columns, reports physical/empty/substantive records and records the inventory-manifest hash. Counts are explicitly audited-manifest counts verified against unchanged bytes, not new independent observations. A mismatch fails the tool rather than displaying a fabricated inventory.

Only Ghana combined is canonical analysis input. Its two regime components overlap those 864 plots and are not added to the sample size. Dictionaries are metadata. IITA files are reference-only; their 960-row drought file and 337,913-record irrigation file (336,953 empty, 960 substantive) do not establish matched year/replicate/environment or genotype identity. No row-order or ENTRY-only joining occurs. These limits implement a defensible Ghana-first alternative to unjustified pooling.

Genotype-specific retention is computed inside the registered environment-summary tool from complete, separately summarized regimes of the same canonical Ghana source. It is null for nonpositive watered denominators. It is a descriptive ratio; ratios over 100% are retained and caveated rather than presented as causal benefits of drought. No genotype confidence interval or validated combined tolerance/stability score is invented.

## Report and reproducibility

Reports and AI Insights show the structured report: declared criteria and evaluations, counter-evidence, global observed means/retention and block-bootstrap interval, candidate trade-offs, the executed follow-up, source audit/citations, methodology, unresolved scope, and a clearly separate proposed next experiment. Measured visualizations and cinematic processing replay link to the same saved run. JSON export preserves the complete report; the existing evidence export includes original artifacts/events and source-row lineage.

The future field trial is a proposal, not an executed experiment: independently replicated irrigation whole plots with genotype subplots where water delivery is hard to change, verified site-season/block identities, water/soil measurements and validated trait scoring. Its design reference is [Penn State STAT 503, Nested and Split Plot Designs](https://online.stat.psu.edu/stat503/Lesson14.html). No powered sample size is invented; a design-aware precision/power study and statistician review are required before field implementation.

Loaded-source provenance snapshots Git metadata (without executing commands), Python version and exact hashes of Python modules/action schema at API startup. Dirty-worktree status is explicitly not asserted by the application; hashes expose exact bytes even during development. Source data and manifest hashes, seeds, method versions, conditional intervals and warning/filter descriptions remain recorded. Source changes require restarting the API to load and snapshot the new code.

`python -m scripts.generate_science_fixtures` regenerates real-source UI fixtures in an isolated in-memory store. It never calls Meta. UUIDs/timestamps/startup code snapshots vary; these are fixture records, not timing benchmarks. The exact original owner-supplied maize brief is preserved in `tests/fixtures/ghana-research-objective.txt`.

## Acceptance boundary

The full supplied objective has been executed through this explicit supported profile in isolated tests with six numeric tools, four evaluations and two deterministic evidence-dependent choices. It is not evidence of live Meta quality, public-production readiness, field validity or browser/GPU accessibility acceptance. The API/authentication tests verify the six-method request, original-text preservation, invalid-plan/partial-method rejection and absence of provider-adapter invocation. Browser control remains unavailable, so no fresh screenshot or visual signoff is implied.

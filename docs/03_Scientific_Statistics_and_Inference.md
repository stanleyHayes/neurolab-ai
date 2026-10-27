# 03 — Scientific methods and honest inference

## Descriptive first
Counts by genotype/condition/ENVT/REP; grain-yield distribution; missingness; median/mean; stratified boxplots; plot-level data download. Yield retention = 100 × drought mean / well-watered mean *only* when denominators positive and the two summaries are comparable. Display n and uncertainty; retention is a descriptive index, not a causal treatment effect.

## Alpha-lattice design
Ghana is a replicated alpha-lattice trial. Do not use simple pooled means as definitive genotype rankings. Preferred model (after inspecting identifiers and residuals): yield ~ condition + genotype + condition:genotype + environment + appropriate replication/block-within-environment effects; choose fixed/random components with statistician review. Report fitted model, assumptions, convergence, missingness and variance components. If mixed-model package unavailable, use environment-stratified descriptive estimates with cluster bootstrap and label exploratory.

## Robustness
- Separate comparisons within environments; avoid treating three ENVT levels as 3 independent replicates of each plot.
- Pre-specify primary contrast, control multiplicity for many genotypes (e.g. FDR) or label exploratory.
- Use clustered bootstrap resampling at appropriate trial unit, not row-wise bootstrap that breaks block/replicate dependence.
- Show confidence intervals, effect sizes, sample counts, missingness, and sensitivity to outliers.
- Evaluate genotype-by-environment interaction and ranking stability; warn that three years limit generalization.
- No automatic field recommendation; invite confirmatory field trials.

## Hypothesis examples
H1: The drought-to-control yield ratio varies by genotype beyond sampling uncertainty. H2: Flowering interval correlates with yield under drought within environments. H3: Genotype rankings differ across environment levels. Each must include exact estimand, null, analysis tool, assumptions and limitations.

## Reproducibility
Store data hash, code commit, config, RNG seed, filtering criteria, model version, p-values (if used), intervals, warnings and rendered artifacts. Failed assumptions should trigger explicit 'inconclusive' outcomes, never silent optimistic summaries.

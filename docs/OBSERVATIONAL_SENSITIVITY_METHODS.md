# Observed-environment sensitivity and trait associations

These tools extend Ghana-only deterministic analysis. They do not run a calibrated crop simulation, predict future field performance, fit a confirmatory G×E model, or spend Meta credits. Original CSVs are read only. Source-row numbers and source SHA-256 remain attached to the resulting summaries/paired observations.

## Environment summaries

`summarize_environment_stability` summarizes DROUGHT and WELL_WATERED separately. It averages observed replicate plot yields within each genotype/environment cell, then gives environments equal weight for each genotype. Output includes the observed environment means (kg/ha), their sample SD (denominator n−1), CV only when the mean is positive, and SD after subtracting each environment's mean across complete-coverage genotypes. Centering is descriptive; it does not fit an alpha-lattice or variance-component model.

Environment codes come from the source, including an environment whose yields are entirely missing. Incomplete genotypes remain labeled, receive no comparison ranks, and are not silently treated as complete. Genotypes with no numeric yields are separately listed. Complete genotypes receive per-environment mean-yield ranks (average ties), plus ranks of their equal-environment means after each environment is omitted. This leave-one-environment-out rank range measures sensitivity to the observed environments. It is not a confidence interval, predictive validation, or an estimate of broad adaptation. A consistently poor genotype can have low variation; high mean yield and low variation are separate criteria.

## Trait associations

`analyze_trait_associations` examines seven measured traits against drought grain yield: ASI, stay-green score, ears per plant, plant/ear height, and anthesis/silking days. Only trait/yield-complete plots contribute to each genotype/environment pair. A genotype must have such a pair in every expected drought environment for that trait. Pairwise omissions, genotype counts, paired plot counts and source-row lineage are reported. Environment means are averaged equally, producing one point per genotype rather than treating six repeated plots as six independent genotypes.

The primary statistic is Spearman rank correlation with average ranks for ties; Pearson correlation is also provided. These describe monotonic and linear association respectively. See the primary [Spearman](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html) and [Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html) definitions. The implementation uses Python's standard-library correlation over values or average ranks. It reports no significance test. Constant/insufficient data produce null, never a fabricated zero. Per-environment correlations use the same included genotype profiles, exposing contradictory directions.

The exploratory 95% percentile resampling interval draws genotype profiles with replacement, conditional on the observed environments, with a fixed seed (default 2026, default 1,000 draws; allowlisted budget 100–10,000). Degenerate draws are omitted and counted; an interval requires at least 100 valid draws. The interval assumes exchangeable profiles and ignores relatedness, genotype selection, spatial/block effects, within-genotype measurement error and future-environment sampling. It does not establish validated population coverage. Seven exploratory comparisons have no multiplicity correction. Stay-green score direction is not established by the source dictionary, so a negative score association must not be translated into a biological “greener is better” claim.

## Actual deterministic Ghana check

The real-source fixture `tests/fixtures/ghana-descriptive-ui.json` was produced directly by these tools with seed 2026 and 1,000 draws, not by a model or synthetic crop generator. Each trait has 72 genotype means from 432 paired drought plots. Rounded results:

| Trait | Spearman rho | Conditional percentile interval |
| --- | ---: | --- |
| ASI | −0.250 | −0.467 to 0.013 |
| Stay-green score | −0.294 | −0.490 to −0.047 |
| Ears per plant | 0.361 | 0.154 to 0.553 |
| Plant height | 0.463 | 0.239 to 0.638 |
| Ear height | 0.453 | 0.241 to 0.635 |
| Anthesis days | 0.210 | −0.034 to 0.439 |
| Silking days | 0.096 | −0.147 to 0.329 |

The three largest observed drought means are TZm-1179 (2,370.3 kg/ha), TZEE-W HDT C3 STR C5 (CHECK) (2,356.7), and TZm-480 (2,334.9). Their omitted-environment ranks range 3–5, 1–26, and 2–8 respectively. This exposes sensitivity that a mean-only ranking hides. These are exploratory candidate summaries, not field recommendations or proof of drought tolerance.

## Workflow and verification boundary

Both methods are selectable in research configuration and constrained by the action schema, registry, iteration/call/wall budgets, owner isolation and persisted event/artifact workflow. A call budget never silently removes selected tasks: remaining tasks produce a partial report. Tool caveats propagate to report limitations. Subsequent model contexts use computed summaries rather than forwarding every plotted point; complete artifacts remain available for export. Meta remains paused locally.

Trait Analytics, Environments, Research Results and event-bound cinematic playback read the actual matching artifacts. No-artifact and source-mismatch cases do not substitute a fabricated chart. Synthetic datasets appear only in explicitly labeled unit tests with hand-calculated numerical oracles. Full scientific hypothesis evaluation/follow-up reporting and actual browser acceptance remain separate unfinished gates.

A subsequent authenticated API check ran the two methods under committed code `9666c16` with inference disabled. Focused run `a3358b92-ef34-4488-88fb-4c794c831d8a` completed with two artifacts and 23 persisted events. Its scope and exact summaries are in `verification/descriptive-analysis-runtime.json`. This is actual deterministic computation and saved-event acceptance, not a Meta run or completion of the full original investigation.

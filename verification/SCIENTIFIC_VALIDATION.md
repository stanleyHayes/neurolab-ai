# Scientific Validation and Data Audit

**Date:** 2026-10-26  
**Scope:** Source integrity, canonicalization, missingness, deterministic analyses, independent numerical comparison, and inference limits. No result here establishes causal drought effects or field recommendation.

## Source dataset integrity

`python3 scripts/audit_datasets.py` passed against `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/data/manifest.json`. All listed raw source SHA-256 values and row counts matched the source files.

### Ghana / WACCI

- Source: Abu et al. (2026), Zenodo DOI `10.5281/zenodo.22666201`, CC BY 4.0, per `/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/docs/01_Data_Inventory_and_Provenance.md`.
- Canonical analyzed source is `data/raw/ghana/maize_combined_phenotypes.csv`, 864 rows, SHA-256 `2e37c07f30e00efb33b59954dd6d02a04f3d67349790d782b70dbedfdaff05bc`.
- Drought component: 432 rows; well-watered component: 432 rows; combined contains 432 records in each regime.
- 72 genotype identifiers appear in each water regime and each of the three `ENVT` indices.
- Within each condition × ENVT stratum: 144 plots, 72 genotypes, 2 replication identifiers, and 9 block IDs.
- Source-row identity is one-based physical line number in `neurolab/ghana.py` (first data record row 2); source SHA and source file retained per canonical record. Source columns not mapped to canonical fields are serialized in `raw_extra_json`.
- `ENVT` is retained as `year_code`, not translated into calendar years. `ENV` values encode regime/environment and water regime is confounded with trial environment.
- `YIELD` unit is looked up from the original data dictionary; observed value `kg/ha`.
- The app imports only combined CSV. Independent component-file checks confirmed exact record correspondence by `(GENOTYPE, ENVT, REP, BLK, YIELD)` within the corresponding regime; components are not appended to combined observations.

### IITA

- Manifest lists drought stress: 960 substantive rows; full irrigation: 337,913 physical records, 336,953 fully empty, 960 substantive; multilocation: 23,616; multilocation II: 176; Striga: 1,636.
- `python3 scripts/prepare_data.py` writes a staged cleaned irrigation CSV with an added physical `source_row_number` and retains the unnamed third field under `unnamed_column_3`.
- Current run: 960 records kept, 336,953 fully empty rows skipped, zero other row filters, no source join.
- Cleaning is audited, but IITA is not loaded by the API and has no analysis tool/UI dataset card. Pairing, regression, normalization, and IITA cross-population claims are **not implemented**.

## Canonicalization and missing values

`/Users/shayford/Desktop/Dev/Projects/neurodyne-ai/neurolab/ghana.py` explicitly maps source fields into canonical columns. Missing tokens (`""`, `na`, `n/a`, `null`, `nan`, `.`) become `None`; numeric parsing rejects malformed/non-finite values and records row warnings/quarantine rather than dropping rows. Unknown original columns remain in `raw_extra_json`.

Verified values:

- `stay_green_score`: 432 missing / 864; structurally absent in well-watered trials by design.
- `location_code`: 864 missing / 864 (not present in the source schema).
- `plot`: 864 missing / 864 (not mapped to an identified Ghana plot source field).
- One ear-height and one plant-height value are missing according to the live Meta run's profile artifact.
- Unit tests alter a numeric source record to non-numeric; row remains in the dataset as null value and is included in quarantine with original source row text.
- Normalization run produced 864 canonical rows, no quarantine rows, and did not modify raw source data.

## Implemented scientific estimands

### Environment-weighted regime means and ratio

`neurolab/science.py::compare_regimes` calculates yield means within each observed regime × `ENVT`, then equally weights the three environment means. It calculates drought minus well-watered difference and a descriptive ratio. The ratio is `100 × mean drought / mean well-watered` when denominator is positive, otherwise null. The output correctly warns that regimes are confounded and the calculation is not causal.

Independent calculation from raw combined CSV:

| Summary | Tool and independent result |
|---|---:|
| Mean drought yield (equal-weighted ENVT means), kg/ha | 1,230.2687815072015 |
| Mean well-watered yield (equal-weighted ENVT means), kg/ha | 2,616.0414647785037 |
| Difference drought minus well-watered, kg/ha | -1,385.7726832713022 |
| Drought / well-watered ratio | 47.0278777332517% |
| `n` | 432 observations per regime |

The pooled means equal the equal-environment values here because the observed row counts are balanced across the three environment indices; the estimand nevertheless explicitly describes equal environment weighting.

### Cluster-bootstrap interval

Method: percentile bootstrap resampling block IDs within `CONDITION × ENVT × REP` strata; each draw recomputes equal-environment regime means and the difference. It is reproducible for a fixed seed/config. A separate implementation based directly on raw CSV, Python seeded draws, and SciPy percentile calculation exactly matched the product's seed 1001 / 500 replicate interval:

`[-1559.5278377901084, -1205.0839275256822] kg/ha` (95% percentile interval).

This is exploratory uncertainty for an observational, environment-confounded contrast; it is not a randomized treatment effect confidence interval and should not be presented as proof of drought damage or treatment benefit. The project notes describe an alpha-lattice design, but a fitted alpha-lattice/mixed-effects model and residual diagnostics are absent.

### Genotype ordering

The tool computes each genotype's drought mean within each ENVT and gives environments equal weight. Independent recomputation from canonical plot records matched the ordering and values for all 72 genotypes. Top five descriptive estimates:

| Rank | Genotype | Equal-ENVT drought mean (kg/ha) |
|---:|---|---:|
| 1 | `TZm-1179` | 2,370.290522875817 |
| 2 | `TZEE-W HDT C3 STR C5 (CHECK)` | 2,356.731699346405 |
| 3 | `TZm-480` | 2,334.9387254901962 |
| 4 | `TZm-1530` | 2,287.580718954248 |
| 5 | `TZm-1470` | 2,118.6783496732023 |

**Interpretation limit:** These are raw descriptive summaries. No standard errors/intervals or rank probabilities are supplied; block/replication structure is not modeled in the ranking; no multiplicity control or genotype-by-environment stability metric is computed. The output says they are not field recommendations. The workflow must not equate a top mean with “strongest drought tolerance while stable across environments.”

### Correlation and significance

There is no registered trait-correlation or inferential test tool; no SciPy/statsmodels methods are used by the application. As an independent diagnostic only, SciPy Pearson correlation between drought plot-level pollen date and yield (n=432) is `r=-0.0970354341`, `p=0.04382517`. This is an unadjusted exploratory calculation and is not valid design-adjusted evidence; it is not emitted by the application and should not appear as an agent result. A pooled Welch t-test is similarly not an acceptable alpha-lattice inference because it ignores environment/block/replication structure and confounding.

## Reproducibility and independent checks

- Manifest hashes and row counts independently verified by standard-library audit script.
- Repeated fixed-seed `compare_regimes` calls return identical output (direct audit check and unit test).
- Independent source-CSV calculation matches regime means, ratio and block-bootstrap CI exactly.
- Independent full genotype ordering matches `rank_genotypes` across 72 genotypes.
- Component-vs-combined checks match for both conditions without double-counting.
- Report includes source SHA, tool artifacts include source SHA, analysis version, sample size, scope and warnings. Report does not include a code commit because no Git metadata exists. Random seed/config are present in comparison artifact; ranking is deterministic without a random seed.

## Scientific acceptance verdict

**Verified:** data integrity, Ghana source-row lineage, condition/genotype counts, null handling, descriptive means/ranking arithmetic, stated ratio, deterministic bootstrap and its arithmetic reproduction, and conservative observational caveats.  
**Not verified / not implemented:** calibrated alpha-lattice/mixed model, inferential ranking uncertainty, genotype environment stability, multiple-comparison correction, trait-correlation tool, scientifically selected follow-up design, IITA analysis, field recommendation.  
**Critical constraint:** observed regime comparison is confounded by environment and cannot be interpreted causally; ENVT indices are not calendar year values absent source mapping.
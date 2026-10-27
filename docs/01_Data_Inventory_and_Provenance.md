# 01 — Data inventory, lineage, licenses and exact source facts

## Ghana / WACCI
Abu et al. (2026), *Phenotypic data: drought-tolerance evaluation of early and extra-early African maize (Zea mays L.) landraces*, Zenodo v1.0, DOI 10.5281/zenodo.22666201, CC BY 4.0. 72 accessions (68 landraces + 4 elite checks), three trial years, drought and well-watered regimes, 9×8 alpha-lattice, two replications. `maize_drought_phenotypes.csv` 432 rows, `maize_wellwatered_phenotypes.csv` 432, `maize_combined_phenotypes.csv` 864; dictionary 21 column definitions. Combined is a *stack*, not new observations. ENVT represents trial environment/year code, not automatically a calendar year; verify original metadata before displaying calendar years. STYG missing by design in well-watered records.

## IITA
Menkir et al., *Regional trials of Striga resistant and drought tolerant maize hybrids conducted for eight years*, DOI 10.25502/4xv7-bc93/d, CC BY 4.0 per landing page. Uploaded `m28drought_stress-data.csv`: 960 records, 16 columns. `m28fulli_irrigation-data.csv`: 337,913 records, 15 columns; **336,953 fully empty**, **960 substantive**, including an **unnamed third header column**. `m28multiloc-data.csv`: 23,616 records, 20 columns, with trailing unnamed header. `m28multiloc-data-ii.csv`: 176 records, 30 columns. `m28striga-data.csv`: 1,636 records, 25 columns, includes known header typos (`Striga counet 10 WAP`, `Eear aspect...`). The datasets are not a single homogeneous trial; document distinct trial populations and environments.

## Data handling
- All raw sources in `data/raw/` are immutable. `data/manifest.json` contains SHA-256 hashes, row counts, original columns and year counts.
- Include dataset authors, DOIs, license notices, download/source descriptions and any transformations in exported report.
- Use `data/raw/ghana/maize_combined_phenotypes.csv` as canonical Ghana analysis source; separate files are cross-checks.
- For IITA, strip *only fully empty records* in initial cleaning; preserve non-empty invalid-year rows for review, never silently discard.
- `ENTRY` and `GENOTYPE` identifiers are dataset-local. Do not merge Ghana and IITA at genotype level.
- Do not claim matched irrigation/drought IITA pairs until key cardinality checks pass; 'full irrigation' is a trial regime label, not proof of applied irrigation volumes.

## Not bundled
NASA POWER weather; FAO AquaCrop engine; CIRAD AgMIP calibration data (CC BY-NC-SA 4.0). These require separate sourcing, verification and permissions.

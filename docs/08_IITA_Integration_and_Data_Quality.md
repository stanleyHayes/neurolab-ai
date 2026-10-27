# 08 — IITA dataset integration: practical guardrails

## Uploaded files
- Drought 960 rows; full irrigation 337,913 physical records, only 960 substantive, 336,953 empty.
- Multi-location 23,616 rows and multi-location II 176 rows; distinct column schemas.
- Striga 1,636 rows: pest-stress trials, not water-stress observations.

## Required QA
1. Read with CSV parser retaining physical row number. Count and isolate fully empty records (including rows with only whitespace). Produce `data/processed/iita_full_irrigation_clean.csv` with 960 substantive rows.
2. Preserve unnamed third column in irrigation dataset; do not call it BLK without source proof.
3. Check candidate pair keys YEAR, REP, PLOT, ENTRY (and BLK only if documented); compute duplicate rates and unmatched keys before any pairwise analysis. If duplicates/unmatched or ambiguous design, treat drought vs irrigation as unpaired regime summaries.
4. Confirm trial metadata and units before combining sites/years. Explicitly track LOC and ENV; avoid label collisions across years.
5. Map known typos only in canonical layer, preserve originals; avoid silently treating `Yield infested` as maize drought yield.
6. Test outliers and missingness, but do not automatically delete scientifically plausible extremes.

## Scope
P0: Ghana-only closed loop. P1: IITA evidence panels and independent descriptive replication of *patterns* (e.g. ASI-yield association) without genotype identity assumption. P2: pooled modeling only after harmonization and scientific review.

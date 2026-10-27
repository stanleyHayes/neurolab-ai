# 02 — Canonical data contracts and normalization

## Canonical trial row
`source_dataset`, `source_file`, `source_sha256`, `source_row_number`, `trial_family`, `genotype_id`, `year_code`, `environment_code`, `location_code`, `water_regime`, `replication`, `block`, `plot`, `grain_yield_value`, `grain_yield_unit`, `anthesis_days`, `silking_days`, `asi_days`, `plant_height_value`, `plant_height_unit`, `ear_height_value`, `ear_height_unit`, `ears_per_plant`, `stay_green_score`, `raw_extra_json`.

## Exact source maps
Ghana: `GENOTYPE` -> genotype_id; `ENVT` -> year_code; `ENV` -> environment_code; `CONDITION` -> water_regime; `REP` -> replication; `BLK` -> block; `YIELD` -> grain_yield_value; `POLLEN` -> anthesis_days; `SILK` -> silking_days; `ASI` -> asi_days; `PLHT` -> plant_height_value; `EHT` -> ear_height_value; `STYG` -> stay_green_score. Ghana `YIELD` unit must be taken from data_dictionary.csv, not guessed.
IITA drought: `ENTRY`, `YEAR`, `REP`, `BLK`, `PLOT`, `YIELD (kg/ha)`, `Antheis Day`, `Silking date`, `ASI`, `Plant height`, `Eear height`, `Ears per plant`; water_regime = DROUGHT_STRESS (source filename classification).
IITA full irrigation: same mappings where columns present; blank third header is an *unknown field*; retain as `unnamed_column_3` pending interpretation. Regime = FULL_IRRIGATION.
IITA multiloc: preserve `LOC`, `ENV`, `NAME` where present; treat `YIELD` and `YIELD (kg/ha)` as source-specific; never infer identical scales without dictionary.
IITA striga: store paired infested/non-infested fields in dedicated striga table; **do not map Striga treatment to drought**.

## Rules
- Preserve exact raw text and record index; convert empty/NA tokens to null, never zero.
- Validate year and numeric fields; produce `quarantine.csv` for unexpected nonempty invalid records.
- Retain genotype IDs as strings (leading zeros possible).
- Compare only like-for-like grain-yield units; record missing/unknown units as blockers.
- Validate `ASI ≈ SILK - POLLEN` only as QA, not forced rewrite; units and phenology definition require source confirmation.
- Row key = source file SHA-256 + physical source row index, not an inferred agronomic identifier.
- `CONDITION` valid values from source; do not silently harmonize until checked.
- Derived metrics have formula/version/filters in metadata.

## QA gates
No duplicate raw-row IDs; Ghana 864 combined, 432 per regime; IITA substantive irrigation 960; all parsed rows traceable; no unexplained missingness; consistent yield unit before pooled calculations; test split by genotype or environment for ML tasks, not random plots if leakage is possible.

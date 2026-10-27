"""Deterministic exploratory analyses over normalized Ghana plot records."""

from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from .ghana import GhanaDataset

ANALYSIS_VERSION = "ghana-exploratory-v1"
REGIMES = ("DROUGHT", "WELL_WATERED")


def _records(dataset: GhanaDataset) -> list[dict[str, Any]]:
    return [dict(row) for row in dataset.records]


def _percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot calculate percentile of empty data")
    position = (len(ordered) - 1) * q
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def dataset_profile(dataset: GhanaDataset) -> dict[str, Any]:
    rows = _records(dataset)
    values: dict[str, list[Any]] = defaultdict(list)
    for row in rows:
        for key, value in row.items():
            if key != "raw_extra_json":
                values[key].append(value)
    return {
        "dataset_id": "ghana_combined",
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "row_count": len(rows),
        "yield_unit": dataset.yield_unit,
        "genotype_count": len({row["genotype_id"] for row in rows if row["genotype_id"]}),
        "environment_codes": sorted(
            {row["environment_code"] for row in rows if row["environment_code"]}
        ),
        "year_codes": sorted({row["year_code"] for row in rows if row["year_code"]}),
        "water_regimes": {
            regime: sum(row["water_regime"] == regime for row in rows) for regime in REGIMES
        },
        "missingness": {
            field: {"missing": sum(value is None for value in items), "total": len(items)}
            for field, items in sorted(values.items())
        },
        "warnings": list(dataset.warnings),
    }


def _mean(values: Iterable[float]) -> float:
    materialized = list(values)
    if not materialized:
        raise ValueError("Mean requires at least one value")
    return statistics.fmean(materialized)


def _regime_means(rows: list[dict[str, Any]]) -> dict[str, float]:
    selected = [row for row in rows if row["grain_yield_value"] is not None]
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in selected:
        grouped[(row["water_regime"], row["year_code"])].append(row["grain_yield_value"])
    means_by_regime: dict[str, list[float]] = defaultdict(list)
    for (regime, _year), values in grouped.items():
        means_by_regime[regime].append(_mean(values))
    return {regime: _mean(means_by_regime[regime]) for regime in REGIMES}


def compare_regimes(
    dataset: GhanaDataset, *, seed: int = 2026, bootstrap_samples: int = 2000
) -> dict[str, Any]:
    """Estimate exploratory regime contrast with alpha-lattice block bootstrap.

    Resamples incomplete blocks within regime, environment index and replication.
    The contrast is observational: water regime is confounded with trial
    environment and this is not a causal treatment effect.
    """
    if bootstrap_samples < 100 or bootstrap_samples > 100_000:
        raise ValueError("bootstrap_samples must be between 100 and 100000")
    rows = [
        row
        for row in _records(dataset)
        if row["water_regime"] in REGIMES and row["grain_yield_value"] is not None
    ]
    observed_counts = {
        regime: sum(row["water_regime"] == regime for row in rows) for regime in REGIMES
    }
    if not all(observed_counts.values()):
        raise ValueError("Both water regimes with numeric yield are required")

    observed_means = _regime_means(rows)
    observed_difference = observed_means["DROUGHT"] - observed_means["WELL_WATERED"]
    control_mean = observed_means["WELL_WATERED"]
    retention = 100 * observed_means["DROUGHT"] / control_mean if control_mean > 0 else None

    strata: dict[tuple[str, str, str], dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in rows:
        key = (row["water_regime"], row["year_code"], row["replication"])
        strata[key][row["block"]].append(row)
    for key, blocks in strata.items():
        if not blocks or any(block is None for block in blocks):
            raise ValueError(f"Cannot bootstrap: missing block IDs in design stratum {key}")

    # Seeded pseudo-randomness is intentional: it makes the bootstrap reproducible.
    rng = random.Random(seed)  # noqa: S311
    bootstrap_differences: list[float] = []
    for _ in range(bootstrap_samples):
        sample: list[dict[str, Any]] = []
        for blocks in strata.values():
            block_ids = list(blocks)
            sample.extend(
                row
                for block_id in rng.choices(block_ids, k=len(block_ids))
                for row in blocks[block_id]
            )
        means = _regime_means(sample)
        bootstrap_differences.append(means["DROUGHT"] - means["WELL_WATERED"])

    return {
        "artifact_id": "ghana-regime-contrast-"
        + hashlib.sha256(
            f"{dataset.source_sha256}:{seed}:{bootstrap_samples}".encode()
        ).hexdigest()[:16],
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "analysis_version": ANALYSIS_VERSION,
        "tool_name": "compare_regimes",
        "claim_scope": "exploratory",
        "estimand": "equal-weighted mean across ENVT indices: DROUGHT minus WELL_WATERED grain yield",
        "sample_size": sum(observed_counts.values()),
        "results": {
            "mean_yield_by_regime": observed_means,
            "plot_count_by_regime": observed_counts,
            "yield_difference_kg_ha": observed_difference,
            "drought_to_well_watered_yield_ratio_percent": retention,
            "environment_stratified": True,
        },
        "uncertainty": {
            "method": "percentile cluster bootstrap resampling BLK within CONDITION x ENVT x REP strata",
            "replicates": bootstrap_samples,
            "seed": seed,
            "yield_difference_95_ci_kg_ha": [
                _percentile(bootstrap_differences, 0.025),
                _percentile(bootstrap_differences, 0.975),
            ],
        },
        "warnings": [
            "Exploratory observational contrast; water regime is confounded with environment and this is not a causal treatment effect.",
            "Only three ENVT indices and two replications are represented; generalization is limited.",
            "The yield-retention ratio is descriptive and is null if the well-watered denominator is not positive.",
        ],
    }


def rank_genotypes(dataset: GhanaDataset) -> dict[str, Any]:
    """Rank descriptive drought yields with equal weight for each ENVT index."""
    rows = [
        row
        for row in _records(dataset)
        if row["water_regime"] == "DROUGHT"
        and row["genotype_id"]
        and row["grain_yield_value"] is not None
    ]
    by_genotype_environment: dict[tuple[str, str], list[float]] = defaultdict(list)
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        by_genotype_environment[(row["genotype_id"], row["year_code"])].append(
            row["grain_yield_value"]
        )
        counts[row["genotype_id"]] += 1
    environment_means = defaultdict(list)
    for (genotype, _year), values in by_genotype_environment.items():
        environment_means[genotype].append(_mean(values))
    genotypes = sorted(environment_means)
    estimates = []
    for genotype in genotypes:
        env_means = environment_means[genotype]
        estimates.append(
            {
                "genotype_id": genotype,
                "equal_environment_mean_yield_kg_ha": _mean(env_means),
                "plot_count": counts[genotype],
                "environment_count": len(env_means),
            }
        )
    estimates.sort(
        key=lambda item: (-item["equal_environment_mean_yield_kg_ha"], item["genotype_id"])
    )
    return {
        "artifact_id": "ghana-drought-rank-" + dataset.source_sha256[:16],
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "analysis_version": ANALYSIS_VERSION,
        "tool_name": "rank_genotypes",
        "claim_scope": "descriptive",
        "sample_size": len(rows),
        "results": {"regime": "DROUGHT", "yield_unit": dataset.yield_unit, "genotypes": estimates},
        "uncertainty": None,
        "warnings": [
            "Descriptive exploratory ranking only; alpha-lattice effects and multiplicity are not modeled.",
            "Not a field recommendation; candidates require confirmatory trials and model-based assessment.",
        ],
    }


def inspect_missingness(dataset: GhanaDataset) -> dict[str, Any]:
    profile = dataset_profile(dataset)
    return {
        "artifact_id": "ghana-missingness-" + dataset.source_sha256[:16],
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "analysis_version": ANALYSIS_VERSION,
        "tool_name": "inspect_missingness",
        "claim_scope": "descriptive",
        "sample_size": dataset.source_row_count,
        "results": {"missingness": profile["missingness"]},
        "uncertainty": None,
        "warnings": ["STYG is structurally absent for the well-watered source regime, by design."],
    }

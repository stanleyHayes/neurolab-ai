"""Observed-environment sensitivity and genotype-unit trait associations.

No causal model, environmental extrapolation or confirmatory GxE test is fitted.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
from collections import defaultdict
from typing import Any

from .ghana import GhanaDataset
from .science import _percentile

TRAITS = {
    "asi_days": "days",
    "stay_green_score": "ordinal score 1–9; direction not established here",
    "ears_per_plant": "ears/plant",
    "plant_height_value": "cm",
    "ear_height_value": "cm",
    "anthesis_days": "days",
    "silking_days": "days",
}
VERSION = "ghana-descriptive-sensitivity-v2"


def _artifact(dataset, name, results, size, warnings, uncertainty=None):
    return {
        "artifact_id": name
        + "-"
        + hashlib.sha256(
            json.dumps(
                {"source": dataset.source_sha256, "version": VERSION, "parameters": uncertainty},
                sort_keys=True,
            ).encode()
        ).hexdigest()[:16],
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "analysis_version": VERSION,
        "tool_name": name,
        "claim_scope": "exploratory",
        "sample_size": size,
        "results": results,
        "uncertainty": uncertainty,
        "warnings": warnings,
    }


def average_ranks(values: list[float]) -> list[float]:
    """Ascending one-based ranks; ties receive their average rank."""
    result = [0.0] * len(values)
    ordered = sorted(range(len(values)), key=values.__getitem__)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        for index in ordered[start:end]:
            result[index] = (start + 1 + end) / 2
        start = end
    return result


def correlation(x: list[float], y: list[float], *, ranked=False) -> float | None:
    if len(x) != len(y) or len(x) < 3 or not all(math.isfinite(value) for value in x + y):
        return None
    if ranked:
        x, y = average_ranks(x), average_ranks(y)
    if len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return statistics.correlation(x, y)


def _yield_cells(dataset, regime):
    cells = defaultdict(list)
    for row in dataset.records:
        if row["water_regime"] != regime or row["grain_yield_value"] is None:
            continue
        if not row["environment_code"] or not row["genotype_id"]:
            raise ValueError("Genotype and environment identities are required")
        cells[(row["genotype_id"], row["environment_code"])].append(row)
    return cells


def _environment_summary(cells, environments):
    means = {
        key: statistics.fmean(row["grain_yield_value"] for row in rows)
        for key, rows in cells.items()
    }
    genotypes = sorted({genotype for genotype, _ in cells})
    complete = [
        genotype for genotype in genotypes if all((genotype, env) in means for env in environments)
    ]
    env_means = (
        {
            env: statistics.fmean(means[(genotype, env)] for genotype in complete)
            for env in environments
        }
        if complete
        else {}
    )
    env_ranks = {}
    for env in environments:
        ranks = average_ranks([-means[(genotype, env)] for genotype in complete])
        env_ranks[env] = dict(zip(complete, ranks, strict=True))
    leave_out_ranks = defaultdict(dict)
    if len(environments) >= 2:
        for omitted in environments:
            values = [
                statistics.fmean(means[(genotype, env)] for env in environments if env != omitted)
                for genotype in complete
            ]
            for genotype, rank in zip(
                complete, average_ranks([-value for value in values]), strict=True
            ):
                leave_out_ranks[genotype][omitted] = rank
    entries = [
        _genotype_variability(
            genotype, cells, means, environments, env_means, env_ranks, leave_out_ranks
        )
        for genotype in genotypes
    ]
    entries.sort(key=lambda entry: (-entry["mean_yield_kg_ha"], entry["genotype_id"]))
    return {
        "environment_codes": environments,
        "complete_genotype_count": len(complete),
        "genotypes": entries,
    }


def _genotype_variability(genotype, cells, means, environments, env_means, env_ranks, leave_out):
    observed = [env for env in environments if (genotype, env) in means]
    values = [means[(genotype, env)] for env in observed]
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if len(values) >= 2 else None
    complete = len(observed) == len(environments)
    centered = (
        [means[(genotype, env)] - env_means[env] for env in observed]
        if complete and env_means
        else []
    )
    return {
        "genotype_id": genotype,
        "environment_count": len(observed),
        "complete_environment_coverage": complete,
        "mean_yield_kg_ha": mean,
        "environment_mean_sd_kg_ha": sd,
        "environment_mean_cv_percent": 100 * sd / mean if sd is not None and mean > 0 else None,
        "environment_centered_sd_kg_ha": statistics.stdev(centered) if len(centered) >= 2 else None,
        "environment_means": [
            {
                "environment_code": env,
                "mean_yield_kg_ha": means[(genotype, env)],
                "plot_count": len(cells[(genotype, env)]),
                "rank_among_complete_genotypes": env_ranks[env].get(genotype),
                "source_row_numbers": sorted(
                    row["source_row_number"] for row in cells[(genotype, env)]
                ),
            }
            for env in observed
        ],
        "leave_one_environment_out_ranks": leave_out.get(genotype, {}),
    }


def _regime_summary(dataset, regime):
    rows = [row for row in dataset.records if row["water_regime"] == regime]
    labels = {row["environment_code"] for row in rows}
    if None in labels or "" in labels:
        raise ValueError("Observed environment identities are required")
    cells = _yield_cells(dataset, regime)
    result = _environment_summary(cells, sorted(labels))
    observed = {genotype for genotype, _ in cells}
    result["genotypes_without_numeric_yield"] = sorted(
        {row["genotype_id"] for row in rows if row["genotype_id"]} - observed
    )
    return result


def _regime_retention(regimes):
    watered = {
        entry["genotype_id"]: entry
        for entry in regimes["WELL_WATERED"]["genotypes"]
        if entry["complete_environment_coverage"]
    }
    result = []
    for drought in regimes["DROUGHT"]["genotypes"]:
        control = watered.get(drought["genotype_id"])
        if not drought["complete_environment_coverage"] or control is None:
            continue
        denominator = control["mean_yield_kg_ha"]
        result.append(
            {
                "genotype_id": drought["genotype_id"],
                "drought_mean_kg_ha": drought["mean_yield_kg_ha"],
                "well_watered_mean_kg_ha": denominator,
                "descriptive_retention_percent": 100 * drought["mean_yield_kg_ha"] / denominator
                if denominator > 0
                else None,
                "drought_plot_count": sum(
                    env["plot_count"] for env in drought["environment_means"]
                ),
                "well_watered_plot_count": sum(
                    env["plot_count"] for env in control["environment_means"]
                ),
            }
        )
    return result


def summarize_environment_stability(dataset: GhanaDataset) -> dict[str, Any]:
    regimes = {regime: _regime_summary(dataset, regime) for regime in ("DROUGHT", "WELL_WATERED")}
    size = sum(
        len(rows)
        for regime in ("DROUGHT", "WELL_WATERED")
        for rows in _yield_cells(dataset, regime).values()
    )
    summary = {
        regime: {
            "environment_codes": result["environment_codes"],
            "complete_genotype_count": result["complete_genotype_count"],
            "leading_observed_means": [
                entry for entry in result["genotypes"] if entry["complete_environment_coverage"]
            ][:3],
        }
        for regime, result in regimes.items()
    }
    return _artifact(
        dataset,
        "summarize_environment_stability",
        {
            "regimes": regimes,
            "regime_retention_by_genotype": _regime_retention(regimes),
            "model_summary": summary,
        },
        size,
        [
            "Descriptive variation across observed ENVT indices, not a validated stability model or confirmatory genotype-by-environment interaction test.",
            "Water regimes are summarized separately. ENVT indices are not calendar years; no environment extrapolation is justified.",
            "Ranks and environmental centering use only genotypes observed in every available environment of that regime; incomplete coverage is retained and labeled.",
            "Leave-one-environment-out rank changes are sensitivity analyses, not confidence intervals. Three environments cannot establish broad adaptation.",
            "Alpha-lattice block effects, genotype ranking uncertainty and multiplicity are not modeled. Low variation alone does not imply high yield or drought tolerance.",
            "Genotype retention joins only canonical identities within this same Ghana source, after separate regime summaries; it does not prove matched causal irrigation contrasts. A high ratio can reflect a low watered denominator.",
        ],
    )


def _trait_points(dataset, field):
    drought = [row for row in dataset.records if row["water_regime"] == "DROUGHT"]
    labels = {row["environment_code"] for row in drought}
    if not labels or None in labels or "" in labels:
        raise ValueError("Observed drought environment identities are required")
    environments = sorted(labels)
    cells = defaultdict(list)
    for row in drought:
        if row[field] is not None and row["grain_yield_value"] is not None and row["genotype_id"]:
            cells[(row["genotype_id"], row["environment_code"])].append(row)
    points = []
    for genotype in sorted({row["genotype_id"] for row in drought if row["genotype_id"]}):
        if not all((genotype, env) in cells for env in environments):
            continue
        env_points = [
            {
                "environment_code": env,
                "trait_mean": statistics.fmean(row[field] for row in cells[(genotype, env)]),
                "yield_mean_kg_ha": statistics.fmean(
                    row["grain_yield_value"] for row in cells[(genotype, env)]
                ),
                "source_row_numbers": sorted(
                    row["source_row_number"] for row in cells[(genotype, env)]
                ),
            }
            for env in environments
        ]
        points.append(
            {
                "genotype_id": genotype,
                "trait_mean": statistics.fmean(point["trait_mean"] for point in env_points),
                "yield_mean_kg_ha": statistics.fmean(
                    point["yield_mean_kg_ha"] for point in env_points
                ),
                "environment_means": env_points,
            }
        )
    return points, environments


def _trait_association(dataset, field, unit, rng, samples):
    points, environments = _trait_points(dataset, field)
    x = [point["trait_mean"] for point in points]
    y = [point["yield_mean_kg_ha"] for point in points]
    rho = correlation(x, y, ranked=True)
    estimates = []
    if rho is not None:
        for _ in range(samples):
            indices = rng.choices(range(len(points)), k=len(points))
            value = correlation([x[i] for i in indices], [y[i] for i in indices], ranked=True)
            if value is not None:
                estimates.append(value)
    per_environment = []
    for env in environments:
        selected = [
            next(value for value in point["environment_means"] if value["environment_code"] == env)
            for point in points
        ]
        per_environment.append(
            {
                "environment_code": env,
                "genotype_count": len(selected),
                "spearman_rho": correlation(
                    [value["trait_mean"] for value in selected],
                    [value["yield_mean_kg_ha"] for value in selected],
                    ranked=True,
                ),
            }
        )
    interval = (
        [_percentile(estimates, 0.025), _percentile(estimates, 0.975)]
        if len(estimates) >= 100
        else None
    )
    all_genotypes = {
        row["genotype_id"]
        for row in dataset.records
        if row["water_regime"] == "DROUGHT" and row["genotype_id"]
    }
    return {
        "excluded_genotype_ids": sorted(all_genotypes - {point["genotype_id"] for point in points}),
        "paired_plot_count": sum(
            len(env["source_row_numbers"]) for point in points for env in point["environment_means"]
        ),
        "trait": field,
        "unit": unit,
        "genotype_count": len(points),
        "spearman_rho": rho,
        "pearson_r": correlation(x, y),
        "spearman_rho_95_percentile_interval": interval,
        "valid_bootstrap_replicates": len(estimates),
        "per_environment": per_environment,
        "points": points,
    }


def analyze_trait_associations(
    dataset: GhanaDataset, *, seed: int = 2026, bootstrap_samples: int = 1000
) -> dict[str, Any]:
    if (
        isinstance(bootstrap_samples, bool)
        or not isinstance(bootstrap_samples, int)
        or not 100 <= bootstrap_samples <= 10000
    ):
        raise ValueError("bootstrap_samples must be an integer between 100 and 10000")
    # Seeded scientific resampling only; never used for secrets or security identifiers.
    rng = random.Random(seed)  # noqa: S311
    associations = [
        _trait_association(dataset, field, unit, rng, bootstrap_samples)
        for field, unit in TRAITS.items()
    ]
    summary = [
        {key: value for key, value in association.items() if key != "points"}
        for association in associations
    ]
    return _artifact(
        dataset,
        "analyze_trait_associations",
        {
            "regime": "DROUGHT",
            "aggregation": "Paired complete plots -> genotype/environment means -> equal-environment genotype means",
            "associations": associations,
            "model_summary": {"associations": summary},
        },
        sum(row["water_regime"] == "DROUGHT" for row in dataset.records),
        [
            "Exploratory association with observed drought yield, not a causal trait effect, validated drought tolerance measure, or predictive model.",
            "Each genotype contributes one equal-environment mean per trait; incomplete genotype/environment trait-yield pairs are excluded for that trait and counts/lineage are retained.",
            "Percentile intervals resample genotype profiles, conditional on the observed environments; they do not quantify uncertainty across future environments or correct alpha-lattice effects.",
            "Spearman ranks average ties. Constant or insufficient data produce null correlations, not zero; degenerate bootstrap draws are omitted and counted.",
            "Seven exploratory trait comparisons have no multiplicity adjustment or confirmatory significance test. Stay-green score direction is not established by the source dictionary.",
            "Genotype case-resampling assumes exchangeable profiles and ignores relatedness, genotype selection and within-genotype plot error; these intervals do not establish validated population coverage.",
        ],
        {
            "method": "genotype-profile percentile bootstrap for Spearman rho",
            "seed": seed,
            "replicates": bootstrap_samples,
        },
    )


def descriptive_claim(artifact: dict[str, Any]) -> str:
    result = artifact["results"]
    if artifact["tool_name"] == "summarize_environment_stability":
        drought = result["regimes"]["DROUGHT"]
        return (
            f"Observed drought variability was summarized across {len(drought['environment_codes'])} environment codes; "
            f"{drought['complete_genotype_count']} genotypes had complete environment coverage. "
            "Leave-one-environment-out ranks quantify sensitivity, not validated adaptation or confidence intervals."
        )
    associations = [item for item in result["associations"] if item["spearman_rho"] is not None]
    if not associations:
        return "No non-degenerate genotype-mean trait association could be computed from the available paired data."
    leading = max(associations, key=lambda item: abs(item["spearman_rho"]))
    return (
        f"Among {len(associations)} exploratory drought trait associations, the largest absolute observed Spearman correlation "
        f"was {leading['trait']} versus yield (rho={leading['spearman_rho']:.3f}, {leading['genotype_count']} genotype means). "
        "Selection across traits is exploratory and unadjusted; association does not establish causal drought resilience."
    )

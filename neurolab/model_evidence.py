"""Explicit projections for model context; persisted numeric artifacts stay complete."""


def evidence_results(artifact):
    results = artifact["results"]
    if artifact["tool_name"] == "summarize_environment_stability":
        return _stability_summary(results)
    if "model_summary" in results:
        return results["model_summary"]
    if artifact["tool_name"] == "dataset_profile":
        return {
            **{key: value for key, value in results.items() if key != "available_source_inventory"},
            "context_projection": "Source-file inventory omitted here; full inventory remains in the cited artifact. Source and manifest hashes are retained.",
        }
    if artifact["tool_name"] == "rank_genotypes":
        entries = results["genotypes"]
        return {
            **{key: value for key, value in results.items() if key != "genotypes"},
            "genotype_count": len(entries),
            "leading_genotypes": entries[:5],
            "trailing_genotypes": entries[max(5, len(entries) - 5) :],
            "context_projection": "At most five leading and five trailing observed mean-yield entries, without duplicates. Full ranking remains in the cited artifact. Not rank confidence or validated tolerance/stability.",
        }
    return results


def _stability_summary(results):
    fields = (
        "genotype_id",
        "environment_count",
        "complete_environment_coverage",
        "mean_yield_kg_ha",
        "environment_mean_sd_kg_ha",
        "environment_mean_cv_percent",
        "environment_centered_sd_kg_ha",
        "leave_one_environment_out_ranks",
    )
    summary = {}
    for regime, data in results["model_summary"].items():
        summary[regime] = {
            "environment_codes": data["environment_codes"],
            "complete_genotype_count": data["complete_genotype_count"],
            "leading_observed_means": [
                {key: entry[key] for key in fields} for entry in data["leading_observed_means"]
            ],
        }
    drought_ids = {entry["genotype_id"] for entry in summary["DROUGHT"]["leading_observed_means"]}
    summary["leading_drought_retention"] = [
        entry
        for entry in results["regime_retention_by_genotype"]
        if entry["genotype_id"] in drought_ids
    ]
    summary["context_projection"] = (
        "Leading observed profiles with actual variability, omitted-environment ranks and matched descriptive retention. Per-environment plot means and source-row lists remain in the complete cited artifact; this is not a full-panel stability classification."
    )
    return summary

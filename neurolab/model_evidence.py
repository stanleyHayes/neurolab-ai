"""Explicit projections for model context; persisted numeric artifacts stay complete."""


def evidence_results(artifact):
    results = artifact["results"]
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

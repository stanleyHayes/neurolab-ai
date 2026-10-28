"""Deterministic evaluations of declared exploratory profile criteria.

Inputs are persisted numeric artifacts, never model-authored measurements.
"""

from __future__ import annotations

import math
from typing import Any

from .descriptive import descriptive_claim
from .hypothesis_contracts import NOTICE as STRUCTURED_NOTICE
from .hypothesis_contracts import criterion, hypothesis_text
from .investigation_profile import PROFILE_HYPOTHESES, PROFILE_NOTICE

REQUIRED_TOOLS = {
    "dataset_profile",
    "inspect_missingness",
    "compare_regimes",
    "rank_genotypes",
    "analyze_trait_associations",
    "summarize_environment_stability",
}


def _evaluation(hypothesis, verdict, findings, evidence_ids, contradictions=()):
    return {
        **hypothesis,
        "verdict": verdict,
        "findings": findings,
        "evidence_ids": evidence_ids,
        "contradictions": list(contradictions),
        "scope": "Retrospective descriptive criterion, not a confirmatory hypothesis test or field validation.",
    }


def _complete_drought(artifact):
    data = artifact["results"]["regimes"]["DROUGHT"]
    return data, [entry for entry in data["genotypes"] if entry["complete_environment_coverage"]]


def _consistent_candidate_hypothesis(artifact, hypothesis=None, rank_fraction=0.25):
    hypothesis = hypothesis or PROFILE_HYPOTHESES[0]
    if artifact is None:
        return _evaluation(
            hypothesis, "not_assessed", "Environment-summary evidence is unavailable.", []
        )
    data, entries = _complete_drought(artifact)
    ids = [artifact["artifact_id"]]
    if len(data["environment_codes"]) < 3 or not entries:
        return _evaluation(
            hypothesis,
            "inconclusive",
            "At least three observed environments and complete genotype profiles are required.",
            ids,
        )
    threshold = math.ceil(len(entries) * rank_fraction)
    matching = [
        entry["genotype_id"]
        for entry in entries
        if all(
            point["rank_among_complete_genotypes"] is not None
            and point["rank_among_complete_genotypes"] <= threshold
            for point in entry["environment_means"]
        )
    ]
    result = _evaluation(
        hypothesis,
        "criterion_met" if matching else "criterion_not_met",
        f"{len(matching)} of {len(entries)} complete genotype profiles met the observed rank threshold of {threshold} in every drought environment.",
        ids,
    )
    result["matching_genotype_ids"] = matching
    result["rank_threshold"] = threshold
    return result


def _negative_association_hypothesis(artifact, field, hypothesis):
    if artifact is None:
        return _evaluation(
            hypothesis, "not_assessed", "Trait-association evidence is unavailable.", []
        )
    entry = next(
        (item for item in artifact["results"]["associations"] if item["trait"] == field), None
    )
    ids = [artifact["artifact_id"]]
    if (
        entry is None
        or entry["spearman_rho"] is None
        or entry["spearman_rho_95_percentile_interval"] is None
    ):
        return _evaluation(
            hypothesis,
            "inconclusive",
            "A non-degenerate correlation and conditional interval were not estimated.",
            ids,
        )
    rho = entry["spearman_rho"]
    interval = entry["spearman_rho_95_percentile_interval"]
    environments = entry["per_environment"]
    negative = all(
        item["spearman_rho"] is not None and item["spearman_rho"] < 0 for item in environments
    )
    positive = all(
        item["spearman_rho"] is not None and item["spearman_rho"] > 0 for item in environments
    )
    verdict = "inconclusive"
    if rho < 0 and interval[1] < 0 and negative and len(environments) >= 3:
        verdict = "criterion_met"
    elif rho > 0 and interval[0] > 0 and positive and len(environments) >= 3:
        verdict = "criterion_not_met"
    contradictory = [
        f"{item['environment_code']}: rho={item['spearman_rho']} is not a strictly negative observed association."
        for item in environments
        if item["spearman_rho"] is None or item["spearman_rho"] >= 0
    ]
    if interval[0] <= 0 <= interval[1]:
        contradictory.append("The conditional resampling interval includes zero.")
    result = _evaluation(
        hypothesis,
        verdict,
        f"{entry['genotype_count']} genotype means: rho={rho:.3f}; conditional percentile interval {interval[0]:.3f} to {interval[1]:.3f}.",
        ids,
        contradictory,
    )
    result["statistics"] = {
        "genotype_count": entry["genotype_count"],
        "spearman_rho": rho,
        "conditional_interval": interval,
        "per_environment": environments,
    }
    return result


def _rank_sensitivity_hypothesis(artifact, hypothesis=None, rank_fraction=0.25, leading_count=3):
    hypothesis = hypothesis or PROFILE_HYPOTHESES[3]
    if artifact is None:
        return _evaluation(
            hypothesis, "not_assessed", "Omitted-environment evidence is unavailable.", []
        )
    data, entries = _complete_drought(artifact)
    ids = [artifact["artifact_id"]]
    if len(data["environment_codes"]) < 3 or not entries:
        return _evaluation(
            hypothesis,
            "inconclusive",
            "Too few environments or complete candidates for the declared sensitivity criterion.",
            ids,
        )
    threshold = math.ceil(len(entries) * rank_fraction)
    ranges = []
    for entry in entries[:leading_count]:
        values = list(entry["leave_one_environment_out_ranks"].values())
        if len(values) == len(data["environment_codes"]):
            ranges.append(
                {
                    "genotype_id": entry["genotype_id"],
                    "minimum_rank": min(values),
                    "maximum_rank": max(values),
                    "range_width": max(values) - min(values),
                }
            )
    if len(ranges) != min(leading_count, len(entries)):
        return _evaluation(
            hypothesis, "inconclusive", "Omitted-environment ranks were incomplete.", ids
        )
    matching = [entry for entry in ranges if entry["range_width"] >= threshold]
    result = _evaluation(
        hypothesis,
        "criterion_met" if matching else "criterion_not_met",
        f"{len(matching)} of {len(ranges)} leading observed means changed by at least {threshold} rank positions when an environment was omitted.",
        ids,
    )
    result["rank_ranges"] = ranges
    result["range_width_threshold"] = threshold
    return result


def _candidates(stability):
    if stability is None:
        return []
    _, entries = _complete_drought(stability)
    retention = {
        entry["genotype_id"]: entry
        for entry in stability["results"].get("regime_retention_by_genotype", [])
    }
    result = []
    for entry in entries[:5]:
        ranks = list(entry["leave_one_environment_out_ranks"].values())
        result.append(
            {
                "genotype_id": entry["genotype_id"],
                "drought_mean_kg_ha": entry["mean_yield_kg_ha"],
                "environment_mean_sd_kg_ha": entry["environment_mean_sd_kg_ha"],
                "environment_centered_sd_kg_ha": entry["environment_centered_sd_kg_ha"],
                "environment_count": entry["environment_count"],
                "omitted_environment_rank_range": [min(ranks), max(ranks)] if ranks else None,
                "observed_regime_summary": retention.get(entry["genotype_id"]),
                "selection_basis": "Largest complete-coverage observed drought means; not a combined tolerance/stability score.",
                "evidence_ids": [stability["artifact_id"]],
            }
        )
    return result


def _follow_up(stability, decisions):
    selected = next(
        (
            decision
            for decision in decisions
            if decision.get("selection_source") == "deterministic_evidence_rule"
            and decision["selected_action"] == "summarize_environment_stability"
        ),
        None,
    )
    return {
        "analysis": "Leave-one-environment-out rank sensitivity",
        "executed": stability is not None,
        "adaptively_selected": selected is not None,
        "selection_source": "deterministic evidence rule, not Meta inference"
        if selected
        else "Preplanned or not executed; no adaptive selection is claimed.",
        "selection_evidence_ids": [selected["based_on_evidence_id"]] if selected else [],
        "result_evidence_ids": [stability["artifact_id"]] if stability else [],
        "uncertainty_addressed": "Whether the ranking of leading observed mean yields depends strongly on which recorded environment contributes.",
        "remaining_uncertainty": "This sensitivity calculation cannot predict performance in an independent new environment or estimate causal drought tolerance.",
    }


def _observational_answer(stability, evaluations):
    consistency = next((item for item in evaluations if "rank_threshold" in item), None)
    matching = consistency.get("matching_genotype_ids", []) if consistency else []
    entries = _complete_drought(stability)[1] if stability else []
    selected = next((entry for entry in entries if entry["genotype_id"] in matching), None)
    primary = None
    if selected:
        ranks = list(selected["leave_one_environment_out_ranks"].values())
        primary = {
            "genotype_id": selected["genotype_id"],
            "drought_mean_kg_ha": selected["mean_yield_kg_ha"],
            "environment_centered_sd_kg_ha": selected["environment_centered_sd_kg_ha"],
            "omitted_environment_rank_range": [min(ranks), max(ranks)] if ranks else None,
        }
        summary = (
            f"{selected['genotype_id']} has the largest observed equal-environment drought mean "
            f"among the {len(matching)} genotypes meeting the declared consistency criterion "
            f"({selected['mean_yield_kg_ha']:.1f} kg/ha). This identifies an exploratory "
            "follow-up candidate, not proven biological drought tolerance or validated stability."
        )
    else:
        summary = (
            "No genotype is identified as meeting the declared consistency criterion from the "
            "available evidence. Observed high-mean candidates remain exploratory comparators; "
            "a stable drought-tolerance winner is not established."
        )
    return {
        "summary": summary,
        "primary_follow_up_candidate": primary,
        "consistent_candidate_ids": matching,
        "criterion_id": consistency["id"] if consistency else None,
        "criterion_rank_threshold": consistency["rank_threshold"] if consistency else None,
        "basis_evidence_ids": [stability["artifact_id"]] if stability else [],
        "selection_rule": "Largest observed complete-coverage drought mean among genotypes satisfying the declared across-environment rank criterion; no composite or validated tolerance/stability score.",
    }


def _next_experiment(candidates, evidence_ids, answer):
    primary = answer["primary_follow_up_candidate"]
    preferred = [primary["genotype_id"]] if primary else []
    ids = list(dict.fromkeys(preferred + [entry["genotype_id"] for entry in candidates]))[:3]
    return {
        "status": "proposal_only_not_executed",
        "title": "A replicated, randomized multi-environment water-regime trial",
        "candidate_ids": ids,
        "candidate_selection_basis": answer["selection_rule"]
        + " Include high-mean comparators and a common check; this is a proposed trial, not a field recommendation.",
        "basis_evidence_ids": evidence_ids,
        "design": "Where irrigation is a hard-to-change factor, randomize independently replicated water-regime whole plots within each site-season/block, and randomize candidate genotypes plus a common check to subplots within each whole plot. Avoid treating multiple plants/subplots as independent irrigation replicates.",
        "additional_data": [
            "Verified site-season identities and trial dates, rather than inferred calendar years from ENVT codes.",
            "Water delivery, soil moisture and soil/site covariates with units; treatment randomization and independent whole-plot replicate/block identities.",
            "Consistent genotype/barcode identities and seed lots; validated stay-green scale direction and measurement reliability.",
            "Plot-level yield and flowering observations, missing-data reasons, protocol deviations and blinded score records where feasible.",
        ],
        "analysis_plan": "Predeclare the primary genotype-by-water-regime contrast, the whole-plot and subplot error structure, multiplicity control, and the independent validation environments. Fit a design-aware mixed model with replication/block nesting, examine residuals and convergence, and report uncertainty and missingness sensitivity.",
        "sample_size": "Not calculated. Choose numbers of independent environments and whole-plot replicates through a design-aware power/precision study using justified pilot variance components; the current descriptive summaries do not justify a numeric powered sample size.",
        "reference": {
            "title": "Penn State STAT 503 — Nested and Split Plot Designs",
            "url": "https://online.stat.psu.edu/stat503/Lesson14.html",
        },
    }


def build_scientific_report(
    objective: str,
    evidence: list[dict[str, Any]],
    decisions,
    provenance,
    declared_hypotheses=(),
    hypothesis_tests=(),
):
    declared = (
        [criterion(test) for test in hypothesis_tests] if hypothesis_tests else PROFILE_HYPOTHESES
    )
    scope = STRUCTURED_NOTICE if hypothesis_tests else PROFILE_NOTICE
    version = "ghana-investigation-structured-v1" if hypothesis_tests else "ghana-investigation-v1"
    hashes = {item["source_sha256"] for item in evidence}
    if len(hashes) > 1:
        return {
            "version": version,
            "scope": scope,
            "evidence_coverage": "source_mismatch",
            "hypothesis_evaluations": [
                _evaluation(
                    h,
                    "not_assessed",
                    "Source hashes disagree; no combined interpretation is permitted.",
                    [],
                )
                for h in declared
            ],
        }
    index = {item["tool_name"]: item for item in evidence}
    profile = index.get("dataset_profile")
    comparison = index.get("compare_regimes")
    traits = index.get("analyze_trait_associations")
    stability = index.get("summarize_environment_stability")
    candidates = _candidates(stability)
    ids = [item["artifact_id"] for item in evidence]
    evaluations = (
        [_structured_evaluation(test, stability, traits) for test in hypothesis_tests]
        if hypothesis_tests
        else [
            _consistent_candidate_hypothesis(stability),
            _negative_association_hypothesis(traits, "asi_days", PROFILE_HYPOTHESES[1]),
            _negative_association_hypothesis(traits, "stay_green_score", PROFILE_HYPOTHESES[2]),
            _rank_sensitivity_hypothesis(stability),
        ]
    )
    matching = _consistent_candidate_hypothesis(stability).get("matching_genotype_ids")
    expected_hypotheses = (
        {hypothesis_text(test) for test in hypothesis_tests}
        if hypothesis_tests
        else {f"{item['id']}: {item['proposal']}" for item in PROFILE_HYPOTHESES}
    )
    answer = _observational_answer(stability, evaluations)
    for candidate in candidates:
        candidate["meets_observed_top_quartile_each_environment"] = (
            candidate["genotype_id"] in matching if matching is not None else None
        )
    return {
        "version": version,
        "hypothesis_tests": [test.model_dump(mode="json") for test in hypothesis_tests],
        "additional_hypotheses_not_assessed": [
            text for text in declared_hypotheses if text not in expected_hypotheses
        ],
        "inventory_manifest_sha256": profile["results"].get("inventory_manifest_sha256")
        if profile
        else None,
        "objective": objective,
        "scope": scope,
        "conclusion_status": "exploratory_not_field_validated",
        "evidence_coverage": "complete" if REQUIRED_TOOLS.issubset(index) else "partial",
        "missing_tools": sorted(REQUIRED_TOOLS - index.keys()),
        "dataset_inventory_evidence_ids": [profile["artifact_id"]] if profile else [],
        "dataset_inventory": profile["results"].get("available_source_inventory", [])
        if profile
        else [],
        "source_citations": [
            {
                "authors": "Abu et al. (2026)",
                "doi": "10.5281/zenodo.22666201",
                "license": "CC BY 4.0; source authors do not endorse these interpretations",
                "role": "Ghana canonical analysis source",
            },
            {
                "authors": "Menkir et al.",
                "doi": "10.25502/4xv7-bc93/d",
                "license": "CC BY 4.0 per supplied source pack",
                "role": "IITA audited reference only; not pooled or treated as matched observations",
            },
        ],
        "methodology": {
            "dependent_variable": "Observed grain yield, kg/ha",
            "explanatory_variables": "Canonical genotype, observed water regime and environment; measured flowering, stature, ears/plant and ordinal stay-green traits.",
            "design": "Source Ghana alpha-lattice: incomplete block within replication within observed environment; regimes analyzed descriptively because regime and environment are confounded.",
            "methods": [
                {
                    "tool": item["tool_name"],
                    "analysis_version": item["analysis_version"],
                    "sample_size": item["sample_size"],
                    "uncertainty": item.get("uncertainty"),
                    "evidence_id": item["artifact_id"],
                }
                for item in evidence
            ],
            "assumptions_and_limits": list(
                dict.fromkeys(warning for item in evidence for warning in item["warnings"])
            ),
        },
        "hypothesis_evaluations": evaluations,
        "findings": {
            "observed_regime_comparison": {
                "results": comparison["results"],
                "uncertainty": comparison.get("uncertainty"),
                "evidence_ids": [comparison["artifact_id"]],
            }
            if comparison
            else None,
            "trait_associations": {
                **traits["results"]["model_summary"],
                "screen_summary": descriptive_claim(traits),
                "evidence_ids": [traits["artifact_id"]],
            }
            if traits
            else None,
        },
        "candidate_summaries": candidates,
        "follow_up_analysis": _follow_up(stability, decisions),
        "observational_answer": answer,
        "next_experiment": _next_experiment(candidates, ids, answer),
        "reproducibility": provenance,
        "unresolved_scope": [
            "No cross-source genotype merge or matched IITA inference is justified by the supplied identifiers alone.",
            "No causal irrigation effect, calibrated crop simulation, field recommendation or validated broad adaptation is established.",
            "Declared criteria are retrospective operational definitions, not preregistered tests; resampling intervals are conditional and unadjusted for multiple traits/relatedness.",
        ],
    }


def _structured_evaluation(test, stability, traits):
    hypothesis = criterion(test)
    if test.kind == "consistent_high_yield":
        return _consistent_candidate_hypothesis(stability, hypothesis, test.rank_fraction)
    if test.kind == "leading_rank_sensitivity":
        return _rank_sensitivity_hypothesis(
            stability, hypothesis, test.rank_fraction, test.leading_count
        )
    return _negative_association_hypothesis(traits, test.trait, hypothesis)

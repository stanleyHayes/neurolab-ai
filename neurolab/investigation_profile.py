"""Explicit, retrospective Ghana investigation contract; never Meta inference."""

from __future__ import annotations

PROFILE_OUTPUT = "ghana_drought_investigation"
PROFILE_METHODS = (
    "dataset_profile",
    "missingness_audit",
    "block_bootstrap_contrast",
    "genotype_ranking",
    "trait_associations",
    "environment_stability",
)
PROFILE_HYPOTHESES = (
    {
        "id": "H1",
        "proposal": "At least one complete-coverage genotype is in the observed drought-yield top quartile in every available drought environment.",
        "rationale": "A large pooled mean can hide poor performance in an individual observed environment.",
        "criterion": "For the finite complete-coverage panel, require environment-specific mean-yield ranks no greater than ceil(panel size / 4) in every observed drought environment. This is a descriptive operational criterion, not validated broad adaptation.",
    },
    {
        "id": "H2",
        "proposal": "Longer observed anthesis–silking interval is negatively associated with drought yield across genotype means.",
        "rationale": "The measured SILK-minus-POLLEN interval provides a falsifiable timing association to investigate; its biological mechanism is not established here.",
        "criterion": "Require a negative Spearman rho, a conditional genotype-profile resampling interval entirely below zero, and negative associations in every observed environment. Mixed directions or a zero-crossing interval are inconclusive.",
    },
    {
        "id": "H3",
        "proposal": "Lower numeric stay-green scores are associated with higher observed drought yield across genotype means.",
        "rationale": "Variation in the recorded ordinal score can be compared with yield. Source score direction is unverified, so this hypothesis is about numeric codes, not an assertion that greener plants perform better.",
        "criterion": "Require a negative Spearman rho, a conditional resampling interval entirely below zero, and negative associations in every observed environment. No causal or biological score-direction claim is permitted.",
    },
    {
        "id": "H4",
        "proposal": "At least one of the three largest observed drought means has a rank sensitivity of a quartile of the panel or more when an environment is omitted.",
        "rationale": "Only a few environments contribute to the mean, making environment composition a useful follow-up uncertainty to examine.",
        "criterion": "Among the three leading complete-coverage mean-yield candidates, require an omitted-environment rank range width at least ceil(panel size / 4), with at least three observed environments. This operational sensitivity threshold is not a significance test.",
    },
)
PROFILE_NOTICE = "Deterministic retrospective Ghana investigation profile; template hypotheses are proposals, not Meta-generated findings or a preregistered confirmatory study."


def profile_constraints() -> list[str]:
    return [PROFILE_NOTICE] + [
        f"{item['id']}: {item['proposal']} Rationale: {item['rationale']} Criterion: {item['criterion']}"
        for item in PROFILE_HYPOTHESES
    ]


def profile_plan_check(plan) -> None:
    if PROFILE_OUTPUT not in plan.desired_outputs:
        raise ValueError("The Ghana investigation requires a fresh matching profile plan.")
    if not set(profile_constraints()).issubset(plan.important_constraints):
        raise ValueError(
            "The Ghana profile criteria must be declared in the plan before execution."
        )
    from .research_context import METHOD_TO_TOOL

    required = {METHOD_TO_TOOL[method][0] for method in PROFILE_METHODS}
    if len(plan.tasks) != len(required) or {task.tool_name for task in plan.tasks} != required:
        raise ValueError("The Ghana profile plan must retain all six supported analysis tasks.")


def profile_followup(result, pending):
    available = {task.tool_name for task in pending}
    if result["tool_name"] == "dataset_profile":
        missing = result["results"]["missingness"]
        analytical_fields = {
            "grain_yield_value",
            "asi_days",
            "stay_green_score",
            "ears_per_plant",
            "plant_height_value",
            "ear_height_value",
            "anthesis_days",
            "silking_days",
        }
        any_missing = any(
            item["missing"] > 0 for field, item in missing.items() if field in analytical_fields
        )
        target = "inspect_missingness" if any_missing else "compare_regimes"
        if target in available:
            return (
                target,
                "Observed missingness requires a diagnostic audit before comparison."
                if any_missing
                else "Profile reports no missing values; proceed to the observed regime contrast.",
            )
    if result["tool_name"] == "rank_genotypes" and "summarize_environment_stability" in available:
        entries = result["results"]["genotypes"][:3]
        if any(entry["environment_count"] >= 2 for entry in entries):
            return (
                "summarize_environment_stability",
                "Leading descriptive means span multiple environments; select omitted-environment rank sensitivity as the follow-up before interpreting candidates.",
            )
    return None

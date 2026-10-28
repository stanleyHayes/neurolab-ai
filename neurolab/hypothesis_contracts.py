"""Model-proposed, machine-evaluable observational criteria; never model verdicts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

NOTICE = (
    "Structured retrospective criteria from the accepted plan; backend-computed observational "
    "assessments, not model-generated findings, confirmatory tests or field validation."
)


class HypothesisTest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^H[1-9][0-9]?$")
    kind: Literal["consistent_high_yield", "negative_trait_association", "leading_rank_sensitivity"]
    rank_fraction: float | None = Field(default=None, ge=0.05, le=0.5, strict=True)
    leading_count: int | None = Field(default=None, ge=1, le=5, strict=True)
    trait: Literal["asi_days", "stay_green_score"] | None = None
    rationale: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_parameters(self):
        if self.kind == "negative_trait_association":
            valid = (
                self.trait is not None and self.rank_fraction is None and self.leading_count is None
            )
        elif self.kind == "consistent_high_yield":
            valid = (
                self.rank_fraction is not None
                and self.rank_fraction <= 0.25
                and self.trait is None
                and self.leading_count is None
            )
        else:
            valid = (
                self.rank_fraction is not None
                and self.leading_count is not None
                and self.trait is None
            )
        if not valid:
            raise ValueError("Hypothesis parameters do not match the supported criterion")
        return self


def criterion(test):
    if test.kind == "consistent_high_yield":
        proposal = f"At least one complete-coverage genotype ranks in the top {test.rank_fraction * 100:g}% of observed mean drought yields in every observed drought environment."
        rule = f"Require at least three observed drought environments and a within-environment rank no greater than ceil(complete panel size * {test.rank_fraction:g}) in each."
    elif test.kind == "leading_rank_sensitivity":
        proposal = f"At least one of the {test.leading_count} largest complete-coverage observed drought means changes rank by at least {test.rank_fraction * 100:g}% of the panel when an environment is omitted."
        rule = f"Require at least three observed environments; omitted-environment rank range width must be at least ceil(complete panel size * {test.rank_fraction:g}) among the leading {test.leading_count} candidates. This is sensitivity, not a significance test."
    else:
        proposal = f"Observed drought genotype-mean {test.trait} values are negatively associated with observed drought yield."
        rule = "Require negative Spearman rho, a conditional genotype-profile resampling interval entirely below zero, and negative correlations in all of at least three observed environments. Zero-crossing intervals or mixed directions are inconclusive, not falsification."
        if test.trait == "stay_green_score":
            rule += (
                " This concerns numeric ordinal codes; biological score direction is unverified."
            )
    return {"id": test.id, "proposal": proposal, "criterion": rule, "rationale": test.rationale}


def hypothesis_text(test):
    return f"{test.id}: {criterion(test)['proposal']}"


def validate_tests(tests):
    identities = [test.id for test in tests]
    signatures = [(test.kind, test.rank_fraction, test.leading_count, test.trait) for test in tests]
    if len(identities) != len(set(identities)) or len(signatures) != len(set(signatures)):
        raise ValueError("Hypothesis IDs and executable criteria must be unique")


def generation_schema():
    common = {
        "id": {"type": "string", "pattern": r"^H[1-9][0-9]?$"},
        "rationale": {"type": "string", "minLength": 1, "maxLength": 500},
    }
    branches = []
    for kind in ("consistent_high_yield", "negative_trait_association", "leading_rank_sensitivity"):
        properties = {
            **common,
            "kind": {"type": "string", "enum": [kind]},
            "rank_fraction": {"type": "null"},
            "leading_count": {"type": "null"},
            "trait": {"type": "null"},
        }
        if kind == "negative_trait_association":
            properties["trait"] = {"type": "string", "enum": ["asi_days", "stay_green_score"]}
        else:
            properties["rank_fraction"] = {
                "type": "number",
                "minimum": 0.05,
                "maximum": 0.25 if kind == "consistent_high_yield" else 0.5,
            }
            if kind == "leading_rank_sensitivity":
                properties["leading_count"] = {"type": "integer", "minimum": 1, "maximum": 5}
        branches.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": list(properties),
                "properties": properties,
            }
        )
    return {"type": "array", "maxItems": 4, "items": {"anyOf": branches}}


def validate_hypothesis_plan(plan):
    """Structured investigations retain the full evidence contract and every criterion."""
    tests = plan.hypothesis_tests
    validate_tests(tests)
    if len(tests) < 3:
        raise ValueError("A structured investigation requires at least three distinct hypotheses")
    if {test.kind for test in tests} != {
        "consistent_high_yield",
        "negative_trait_association",
        "leading_rank_sensitivity",
    }:
        raise ValueError(
            "The investigation must assess yield consistency, rank sensitivity and a trait association"
        )
    required = {
        "dataset_profile",
        "inspect_missingness",
        "compare_regimes",
        "rank_genotypes",
        "analyze_trait_associations",
        "summarize_environment_stability",
    }
    if (
        "ghana_drought_investigation" not in plan.desired_outputs
        or len(plan.tasks) != 6
        or {task.tool_name for task in plan.tasks} != required
    ):
        raise ValueError(
            "A structured investigation requires all six supported Ghana methods and its scientific report"
        )
    if not {hypothesis_text(test) for test in tests}.issubset(plan.hypotheses):
        raise ValueError("The declared hypotheses must preserve their exact executable criteria")

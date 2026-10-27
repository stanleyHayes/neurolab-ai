"""Structured objectives, research plans and context safety for investigations."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_RESEARCH_OBJECTIVE_CHARS = 20_000
MAX_RESEARCH_REQUEST_BYTES = 256 * 1024
META_CONTEXT_WINDOW_TOKENS = 1_048_576
META_CONTEXT_SAFETY_RESERVE_TOKENS = 8_000

SupportedMethod = Literal[
    "block_bootstrap_contrast",
    "genotype_ranking",
    "missingness_audit",
    "dataset_profile",
    "trait_associations",
    "environment_stability",
]
SupportedTool = Literal[
    "compare_regimes",
    "rank_genotypes",
    "inspect_missingness",
    "dataset_profile",
    "analyze_trait_associations",
    "summarize_environment_stability",
]
DatasetId = Literal[
    "ghana_combined",
    "iita_drought",
    "iita_full_irrigation",
    "iita_multiloc",
    "iita_striga",
]
DesiredOutput = Literal[
    "research_report",
    "regime_contrast",
    "genotype_summaries",
    "missingness_summary",
    "provenance_export",
    "trait_associations",
    "environment_summaries",
]
ResearchText = str


class ResearchConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_steps: int = Field(default=3, ge=1, le=6)
    max_tool_calls: int = Field(default=5, ge=1, le=10)
    max_seconds: int = Field(default=60, ge=1, le=180)


class AutonomyPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auto_plan_with_meta: bool = True
    execute_supported_tasks: bool = True
    stop_if_unsupported: bool = False


class ResearchConfiguration(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="", max_length=200)
    research_questions: list[str] = Field(default_factory=list, max_length=20)
    hypotheses: list[str] = Field(default_factory=list, max_length=20)
    dataset_id: DatasetId = "ghana_combined"
    constraints: ResearchConstraints = Field(default_factory=ResearchConstraints)
    preferred_methods: list[SupportedMethod] = Field(default_factory=list, max_length=6)
    desired_outputs: list[DesiredOutput] = Field(default_factory=list, max_length=7)
    autonomy_preferences: AutonomyPreferences = Field(default_factory=AutonomyPreferences)


class DatasetSuggestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dataset_id: DatasetId
    rationale: str = Field(default="", max_length=500)
    enabled_for_analysis: bool = False


class AnalysisApproach(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method_id: SupportedMethod
    rationale: str = Field(default="", max_length=500)


class ResearchTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=1_000)
    tool_name: SupportedTool | None
    status: Literal["pending", "completed", "unsupported"] = "pending"
    evidence_ids: list[str] = Field(default_factory=list, max_length=20)


class ResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    planning_mode: Literal["deterministic", "meta"]
    title: str = Field(default="", max_length=200)
    important_constraints: list[str] = Field(default_factory=list, max_length=40)
    refined_objective: str = Field(min_length=1, max_length=MAX_RESEARCH_OBJECTIVE_CHARS)
    ambiguities: list[str] = Field(default_factory=list, max_length=12)
    research_questions: list[str] = Field(default_factory=list, max_length=20)
    hypotheses: list[str] = Field(default_factory=list, max_length=20)
    dataset_suggestions: list[DatasetSuggestion] = Field(default_factory=list, max_length=5)
    analysis_approaches: list[AnalysisApproach] = Field(default_factory=list, max_length=4)
    desired_outputs: list[DesiredOutput] = Field(default_factory=list, max_length=7)
    tasks: list[ResearchTask] = Field(default_factory=list, max_length=10)
    unsupported_requirements: list[str] = Field(default_factory=list, max_length=20)


class ResearchDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(default="", max_length=200)
    objective: str = Field(default="", max_length=MAX_RESEARCH_OBJECTIVE_CHARS)
    research_questions: list[str] = Field(default_factory=list, max_length=20)
    hypotheses: list[str] = Field(default_factory=list, max_length=20)
    dataset_id: DatasetId = "ghana_combined"
    constraints: ResearchConstraints = Field(default_factory=ResearchConstraints)
    preferred_methods: list[SupportedMethod] = Field(default_factory=list, max_length=6)
    desired_outputs: list[DesiredOutput] = Field(default_factory=list, max_length=7)
    autonomy_preferences: AutonomyPreferences = Field(default_factory=AutonomyPreferences)
    accepted_plan: ResearchPlan | None = None

    @model_validator(mode="after")
    def validate_accepted_plan(self) -> ResearchDraft:
        if self.accepted_plan and self.accepted_plan.objective_sha256 != objective_digest(
            self.objective
        ):
            raise ValueError(
                "Accepted plan does not match the exact draft objective; refine it again"
            )
        return self

    def configuration(self) -> ResearchConfiguration:
        return ResearchConfiguration(
            title=self.title,
            research_questions=self.research_questions,
            hypotheses=self.hypotheses,
            dataset_id=self.dataset_id,
            constraints=self.constraints,
            preferred_methods=self.preferred_methods,
            desired_outputs=self.desired_outputs,
            autonomy_preferences=self.autonomy_preferences,
        )


class ResearchObjectiveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=MAX_RESEARCH_OBJECTIVE_CHARS)
    configuration: ResearchConfiguration = Field(default_factory=ResearchConfiguration)
    plan: ResearchPlan | None = None


class ResearchRunRequest(BaseModel):
    """Backward-compatible run request with optional structured configuration."""

    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=MAX_RESEARCH_OBJECTIVE_CHARS)
    dataset_id: DatasetId = "ghana_combined"
    constraints: ResearchConstraints = Field(default_factory=ResearchConstraints)
    configuration: ResearchConfiguration | None = None
    plan: ResearchPlan | None = None
    seed: int = Field(default=2026, ge=0, le=2**32 - 1)
    mode: Literal["replay", "meta"] = "replay"

    @model_validator(mode="after")
    def reconcile_configuration(self) -> ResearchRunRequest:
        if self.configuration is not None:
            if (
                "dataset_id" in self.model_fields_set
                and self.dataset_id != self.configuration.dataset_id
            ):
                raise ValueError("Top-level and configured dataset IDs must agree")
            if (
                "constraints" in self.model_fields_set
                and self.constraints != self.configuration.constraints
            ):
                raise ValueError("Top-level and configured research budgets must agree")
            self.dataset_id = self.configuration.dataset_id
            self.constraints = self.configuration.constraints
        return self


class ResearchDraftSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)
    draft: ResearchDraft


class ResearchPlanRefinementRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objective: str = Field(min_length=1, max_length=MAX_RESEARCH_OBJECTIVE_CHARS)
    configuration: ResearchConfiguration = Field(default_factory=ResearchConfiguration)


class DraftSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0)
    draft: ResearchDraft


def objective_digest(objective: str) -> str:
    return hashlib.sha256(objective.encode("utf-8")).hexdigest()


def validate_objective(objective: str) -> None:
    if not isinstance(objective, str) or not objective.strip():
        raise ValueError("Enter a research objective before starting an investigation.")
    if len(objective) > MAX_RESEARCH_OBJECTIVE_CHARS:
        raise ValueError(
            f"Research objectives may contain at most {MAX_RESEARCH_OBJECTIVE_CHARS:,} characters. "
            "No text was truncated."
        )


def validate_plan_objective(plan: ResearchPlan, objective: str) -> None:
    if plan.objective_sha256 != objective_digest(objective):
        raise ValueError(
            "This research plan was generated for a different objective. Refine it again."
        )


METHOD_TO_TOOL: dict[str, tuple[str, str]] = {
    "trait_associations": (
        "analyze_trait_associations",
        "Estimate exploratory drought genotype-mean trait associations with conditional genotype-profile bootstrap intervals.",
    ),
    "environment_stability": (
        "summarize_environment_stability",
        "Summarize observed environment yield variability and leave-one-environment-out rank sensitivity; not validated stability.",
    ),
    "block_bootstrap_contrast": (
        "compare_regimes",
        "Estimate an exploratory drought-versus-well-watered contrast with block-bootstrap uncertainty.",
    ),
    "genotype_ranking": (
        "rank_genotypes",
        "Compute descriptive genotype summaries across observed environments.",
    ),
    "missingness_audit": (
        "inspect_missingness",
        "Inspect observed missingness while preserving source-row counts and caveats.",
    ),
    "dataset_profile": (
        "dataset_profile",
        "Profile the enabled Ghana combined dataset and its provenance.",
    ),
}


def build_deterministic_plan(objective: str, config: ResearchConfiguration) -> ResearchPlan:
    validate_objective(objective)
    methods = config.preferred_methods or [
        "block_bootstrap_contrast",
        "genotype_ranking",
        "missingness_audit",
    ]
    tasks = [
        ResearchTask(
            task_id=f"task-{index + 1}",
            title=method.replace("_", " ").title(),
            description=METHOD_TO_TOOL[method][1],
            tool_name=METHOD_TO_TOOL[method][0],
        )
        for index, method in enumerate(methods)
    ]
    return ResearchPlan(
        objective_sha256=objective_digest(objective),
        planning_mode="deterministic",
        title=config.title,
        refined_objective=objective,
        research_questions=config.research_questions,
        hypotheses=config.hypotheses,
        dataset_suggestions=[
            DatasetSuggestion(
                dataset_id=config.dataset_id,
                rationale="Only Ghana combined is currently enabled for run execution; other datasets are suggestions only.",
                enabled_for_analysis=config.dataset_id == "ghana_combined",
            )
        ],
        analysis_approaches=[
            AnalysisApproach(method_id=method, rationale=METHOD_TO_TOOL[method][1])
            for method in methods
        ],
        desired_outputs=config.desired_outputs,
        tasks=tasks,
        unsupported_requirements=[],
    )


def estimated_context_tokens_upper_bound(messages: list[dict[str, str]]) -> int:
    """Conservative UTF-8 byte upper bound for pre-request context budget checks."""
    serialized = json.dumps(messages, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return len(serialized) + 4_096


def build_refinement_schema() -> dict[str, Any]:
    text_item = {"type": "string", "maxLength": 4_000}
    short_text = {"type": "string", "maxLength": 500}
    supported_methods = list(METHOD_TO_TOOL)
    datasets = [
        "ghana_combined",
        "iita_drought",
        "iita_full_irrigation",
        "iita_multiloc",
        "iita_striga",
    ]
    outputs = [
        "research_report",
        "regime_contrast",
        "genotype_summaries",
        "missingness_summary",
        "provenance_export",
        "trait_associations",
        "environment_summaries",
    ]
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title",
            "refined_objective",
            "important_constraints",
            "ambiguities",
            "research_questions",
            "hypotheses",
            "dataset_suggestions",
            "analysis_approaches",
            "desired_outputs",
            "tasks",
            "unsupported_requirements",
        ],
        "properties": {
            "title": {"type": "string", "maxLength": 200},
            "important_constraints": {"type": "array", "maxItems": 40, "items": text_item},
            "refined_objective": {
                "type": "string",
                "minLength": 1,
                "maxLength": MAX_RESEARCH_OBJECTIVE_CHARS,
            },
            "ambiguities": {"type": "array", "maxItems": 12, "items": text_item},
            "research_questions": {"type": "array", "maxItems": 20, "items": text_item},
            "hypotheses": {"type": "array", "maxItems": 20, "items": text_item},
            "dataset_suggestions": {
                "type": "array",
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["dataset_id", "rationale"],
                    "properties": {
                        "dataset_id": {"type": "string", "enum": datasets},
                        "rationale": short_text,
                    },
                },
            },
            "analysis_approaches": {
                "type": "array",
                "maxItems": 6,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["method_id", "rationale"],
                    "properties": {
                        "method_id": {"type": "string", "enum": supported_methods},
                        "rationale": short_text,
                    },
                },
            },
            "desired_outputs": {
                "type": "array",
                "maxItems": 7,
                "items": {"type": "string", "enum": outputs},
            },
            "tasks": {
                "type": "array",
                "maxItems": 10,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["task_id", "title", "description", "tool_name"],
                    "properties": {
                        "task_id": {"type": "string", "minLength": 1, "maxLength": 64},
                        "title": {"type": "string", "minLength": 1, "maxLength": 160},
                        "description": {"type": "string", "minLength": 1, "maxLength": 1000},
                        "tool_name": {
                            "type": ["string", "null"],
                            "enum": [
                                "compare_regimes",
                                "rank_genotypes",
                                "inspect_missingness",
                                "dataset_profile",
                                "analyze_trait_associations",
                                "summarize_environment_stability",
                                None,
                            ],
                        },
                    },
                },
            },
            "unsupported_requirements": {"type": "array", "maxItems": 20, "items": text_item},
        },
    }


def build_execution_context(
    objective: str,
    config: ResearchConfiguration,
    plan: ResearchPlan,
    pending_tasks: list[ResearchTask],
) -> dict[str, Any]:
    return {
        "objective_sha256": objective_digest(objective),
        "objective_characters": len(objective),
        "title": config.title,
        "dataset_id": config.dataset_id,
        "research_questions": config.research_questions or plan.research_questions,
        "hypotheses": config.hypotheses or plan.hypotheses,
        "constraints": config.constraints.model_dump(mode="json"),
        "active_plan_tasks": [task.model_dump(mode="json") for task in pending_tasks],
        "important_constraints": plan.important_constraints,
        "plan_ambiguities": plan.ambiguities,
        "plan_unsupported_requirements": plan.unsupported_requirements,
    }

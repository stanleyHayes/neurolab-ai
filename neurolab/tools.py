"""Strict JSON-schema validated research tool registry."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .ghana import GhanaDataset
from .science import compare_regimes, dataset_profile, inspect_missingness, rank_genotypes

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/agent_tool_call.schema.json"
RESULT_SCHEMA_PATH = ROOT / "schemas/research_result.schema.json"
ALLOWED_DATASETS = {
    "ghana_combined",
    "iita_drought",
    "iita_full_irrigation",
    "iita_multiloc",
    "iita_striga",
}
SCHEMA = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(SCHEMA)
_VALIDATOR = Draft202012Validator(SCHEMA)
RESULT_SCHEMA = json.loads(RESULT_SCHEMA_PATH.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(RESULT_SCHEMA)
_RESULT_VALIDATOR = Draft202012Validator(RESULT_SCHEMA)


class ToolValidationError(ValueError):
    """Tool request was malformed, unauthorized, or inapplicable."""


Tool = Callable[[GhanaDataset, dict[str, Any], int], dict[str, Any]]


def _profile(dataset: GhanaDataset, _parameters: dict[str, Any], _seed: int) -> dict[str, Any]:
    profile = dataset_profile(dataset)
    return {
        "artifact_id": "ghana-profile-" + dataset.source_sha256[:16],
        "source_file": dataset.source_file,
        "source_sha256": dataset.source_sha256,
        "analysis_version": "ghana-exploratory-v1",
        "tool_name": "dataset_profile",
        "claim_scope": "descriptive",
        "sample_size": profile["row_count"],
        "results": profile,
        "uncertainty": None,
        "warnings": [
            "Dataset profile is descriptive; ENVT codes are not interpreted as calendar years."
        ],
    }


def _compare(dataset: GhanaDataset, parameters: dict[str, Any], seed: int) -> dict[str, Any]:
    return compare_regimes(
        dataset,
        seed=seed,
        bootstrap_samples=parameters.get("bootstrap_samples", 2000),
    )


def _rank(dataset: GhanaDataset, _parameters: dict[str, Any], _seed: int) -> dict[str, Any]:
    return rank_genotypes(dataset)


def _missingness(dataset: GhanaDataset, _parameters: dict[str, Any], _seed: int) -> dict[str, Any]:
    return inspect_missingness(dataset)


REGISTRY: dict[str, Tool] = {
    "dataset_profile": _profile,
    "compare_regimes": _compare,
    "rank_genotypes": _rank,
    "inspect_missingness": _missingness,
}


def validate_tool_call(call: Any) -> dict[str, Any]:
    errors = sorted(_VALIDATOR.iter_errors(call), key=lambda error: list(error.path))
    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.path)) or '<root>'}: {error.message}" for error in errors
        )
        raise ToolValidationError(details)
    if call["dataset_id"] != "ghana_combined":
        raise ToolValidationError(
            f"Dataset {call['dataset_id']!r} is not enabled for Phase 1 scientific tools"
        )
    if call["action"] not in REGISTRY:
        raise ToolValidationError(f"Action {call['action']!r} has no implemented safe handler")
    if call["action"] == "compare_regimes":
        samples = call["parameters"].get("bootstrap_samples", 2000)
        if (
            isinstance(samples, bool)
            or not isinstance(samples, int)
            or not 100 <= samples <= 10_000
        ):
            raise ToolValidationError("bootstrap_samples must be an integer between 100 and 10000")
    return call


def execute_tool(
    call: Any,
    dataset: GhanaDataset,
    *,
    seed: int,
    artifact_id: str | None = None,
) -> dict[str, Any]:
    validated = validate_tool_call(call)
    result = REGISTRY[validated["action"]](dataset, validated["parameters"], seed)
    if artifact_id:
        result["artifact_id"] = artifact_id
    result_errors = sorted(
        _RESULT_VALIDATOR.iter_errors(result), key=lambda error: list(error.path)
    )
    if result_errors:
        details = "; ".join(error.message for error in result_errors)
        raise RuntimeError(f"Tool produced invalid research_result contract: {details}")
    return result

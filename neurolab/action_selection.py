"""Action-specific model-generation contract; server dispatch remains authoritative."""

from jsonschema import Draft202012Validator

RESAMPLING_ACTIONS = {"compare_regimes", "analyze_trait_associations"}


def selection_schema(actions):
    branches = []
    for action in sorted(actions):
        samples = (
            {"type": ["integer", "null"], "minimum": 100, "maximum": 10000}
            if action in RESAMPLING_ACTIONS
            else {"type": "null"}
        )
        branches.append(
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["action", "bootstrap_samples"],
                "properties": {
                    "action": {"type": "string", "enum": [action]},
                    "bootstrap_samples": samples,
                },
            }
        )
    if not branches:
        raise ValueError("No pending analysis action is available")
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["choice", "decision_summary"],
        "properties": {
            "choice": {"anyOf": branches},
            "decision_summary": {"type": "string", "minLength": 1, "maxLength": 240},
        },
    }


def validated_selection(response, schema):
    # Validate what actually returned, including programmed/nonconforming adapters.
    Draft202012Validator(schema).validate(response)
    return {**response["choice"], "decision_summary": response["decision_summary"]}

"""Verify configured Meta-provider connectivity; never prints or stores the key."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.providers import ModelProviderError, OpenAICompatibleAdapter  # noqa: E402


def main() -> int:
    try:
        adapter = OpenAICompatibleAdapter.from_environment()
        response = adapter.generate_structured(
            [
                {
                    "role": "system",
                    "content": "Return the requested safe acknowledgement in the exact JSON schema.",
                },
                {"role": "user", "content": "Acknowledge a provider integration smoke test."},
            ],
            {
                "type": "object",
                "additionalProperties": False,
                "required": ["ok"],
                "properties": {"ok": {"type": "boolean"}},
            },
            timeout=20,
        )
    except ModelProviderError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    if response != {"ok": True}:
        print("FAIL: provider returned an unexpected smoke-test response", file=sys.stderr)
        return 1
    print(f"PASS: provider responded with structured JSON for model {adapter.model_id!r}.")
    print("Set META_MODEL_VERIFIED=true only after reviewing this successful real-provider call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

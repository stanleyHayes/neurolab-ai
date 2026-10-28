"""Verify configured Meta-provider connectivity; never prints or stores the key."""

from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.model_configuration import PROVIDER_ENV  # noqa: E402
from neurolab.model_spend import ModelSpendError  # noqa: E402
from neurolab.providers import (  # noqa: E402
    ModelProviderError,
    OpenAICompatibleAdapter,
    require_inference_enabled,
)
from neurolab.store import RunStore  # noqa: E402


def main() -> int:
    store = None
    try:
        require_inference_enabled()
        owner = os.getenv("MODEL_SMOKE_OWNER_USER_ID", "").strip()
        if not owner:
            raise ModelSpendError(
                "Smoke test requires an operator-selected active owner for shared admission"
            )
        store = RunStore(os.getenv("DATABASE_URL", "postgresql:///neurolab"))
        adapter = OpenAICompatibleAdapter.from_environment().bind_spending(
            store, owner, "smoke:" + str(uuid.uuid4())
        )
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
    except (ModelProviderError, ModelSpendError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()
    if response != {"ok": True}:
        print("FAIL: provider returned an unexpected smoke-test response", file=sys.stderr)
        return 1
    print(f"PASS: provider responded with structured JSON for model {adapter.model_id!r}.")
    metadata = adapter._last_response_metadata or {}
    body = metadata.get("body") or {}
    print(
        json.dumps(
            {
                "provider": adapter.provider,
                "model_id": adapter.model_id,
                "reported_model_id": body.get("model"),
                "http_status": metadata.get("http_status"),
                "request_identifiers": metadata.get("request_identifiers", {}),
                "provider_reported_usage": body.get("usage"),
                "reserved_tokens": adapter.tokens_reserved,
                "response_schema_verified": True,
            }
        )
    )
    flag = PROVIDER_ENV[adapter.provider][3]
    print(f"Set {flag}=true only after reviewing this successful real-provider call.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

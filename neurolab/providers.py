"""Server-side structured model adapter for OpenAI-compatible inference APIs.

The configured URL must be the provider's chat-completions endpoint. This module
does not assume a Meta URL or claim a provider is Meta until explicitly configured.
"""

from __future__ import annotations

import http.client
import json
import os
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit

from .model_spend import ModelSpendError, ModelSpendGuard, SpendPolicy
from .research_context import (
    META_CONTEXT_SAFETY_RESERVE_TOKENS,
    META_CONTEXT_WINDOW_TOKENS,
)

HTTPS_REQUIRED = "Configured model endpoint must use HTTPS"


class ModelProviderError(RuntimeError):
    """Sanitized model configuration, transport, or response error."""

    def __init__(self, message: str, *, http_status: int | None = None):
        super().__init__(message)
        self.http_status = http_status

    @property
    def permanent(self) -> bool:
        return self.http_status in {400, 401, 402, 403, 404, 405, 410, 422}


class ModelContextLimitError(ModelProviderError):
    """The serialized request exceeds the safe model-context boundary."""


class StructuredModelAdapter(Protocol):
    provider: str
    model_id: str

    def generate_structured(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]: ...

    def generate_refinement(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]: ...


def inference_is_enabled() -> bool:
    return os.getenv("MODEL_INFERENCE_ENABLED", "true").lower() == "true"


def require_inference_enabled() -> None:
    if not inference_is_enabled():
        raise ModelProviderError(
            "Model inference is paused; use saved results or deterministic tools."
        )


@dataclass
class OpenAICompatibleAdapter:
    """Minimal stdlib adapter; API keys remain server-side and are never logged."""

    endpoint: str
    api_key: str
    model_id: str
    provider: str = "configured_openai_compatible_provider"
    max_output_tokens: int = 600
    max_run_tokens: int = 100_000
    max_context_tokens: int = META_CONTEXT_WINDOW_TOKENS
    tokens_reserved: int = 0
    _last_input_token_upper_bound: int = 0
    spend_guard: ModelSpendGuard | None = None

    def _request_structured(
        self,
        messages: list[dict[str, str]],
        schema: dict[str, Any],
        *,
        timeout: int,
        max_tokens: int,
        reasoning_effort: str = "low",
    ) -> dict[str, Any]:
        require_inference_enabled()
        serialized_messages = json.dumps(
            {
                "messages": messages,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "research_action", "strict": True, "schema": schema},
                },
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        serialized_bytes = len(serialized_messages.encode("utf-8"))
        # The current integration uses Chat Completions. It has no exact input
        # token-count endpoint here; a UTF-8-byte upper bound avoids relying on
        # an average chars/token ratio and we reject rather than truncate.
        overhead = self.spend_guard.policy.input_overhead_tokens if self.spend_guard else 0
        context_ceiling = min(
            self.max_context_tokens,
            META_CONTEXT_WINDOW_TOKENS - META_CONTEXT_SAFETY_RESERVE_TOKENS,
        )
        if serialized_bytes + max_tokens + overhead > context_ceiling:
            raise ModelContextLimitError(
                "The complete request exceeds the safe Meta context limit; no objective text was truncated. "
                "Reduce supplied context or use the saved plan/task workflow."
            )
        reservation = serialized_bytes + max_tokens + overhead
        if self.tokens_reserved + reservation > self.max_run_tokens:
            raise ModelProviderError(
                "Per-run model token budget exhausted before request; no prompt was truncated."
            )
        if not self.endpoint.startswith("https://"):
            raise ModelProviderError(HTTPS_REQUIRED)
        endpoint = urlsplit(self.endpoint)
        if endpoint.scheme != "https" or not endpoint.hostname:
            raise ModelProviderError(HTTPS_REQUIRED)
        body = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0,
            "reasoning_effort": reasoning_effort,
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "research_action", "strict": True, "schema": schema},
            },
        }
        if self.spend_guard is None:
            raise ModelProviderError("Model request requires shared owner spending admission")
        try:
            self.spend_guard.check_transport(self.endpoint, self.provider, self.model_id)
            identifier = self.spend_guard.reserve(serialized_bytes, max_tokens)
        except ModelSpendError as exc:
            raise ModelProviderError(str(exc)) from None
        self.tokens_reserved += reservation
        self._last_input_token_upper_bound = serialized_bytes + overhead
        completed = False
        try:
            result = self._send_structured(endpoint, body, timeout)
            completed = True
            return result
        finally:
            try:
                self.spend_guard.record_outcome(identifier, completed)
            except ModelSpendError as exc:
                raise ModelProviderError(str(exc)) from None

    def bind_spending(self, store, owner_id, scope_id):
        self.spend_guard = ModelSpendGuard.from_environment(
            store, owner_id, scope_id, self.provider, self.model_id
        )
        return self

    def _send_structured(self, endpoint, body, timeout):
        connection = None
        try:
            connection = http.client.HTTPSConnection(
                endpoint.hostname, endpoint.port or 443, timeout=timeout
            )
            connection.request(
                "POST",
                endpoint.path or "/",
                body=json.dumps(body),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
            )
            response = connection.getresponse()
            if response.status < 200 or response.status >= 300:
                raise ModelProviderError(
                    f"Model provider returned HTTP {response.status}", http_status=response.status
                )
            raw = response.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ModelProviderError("Model provider response exceeds the size limit")
            payload = json.loads(raw.decode("utf-8"))
        except ModelProviderError:
            raise
        except (OSError, http.client.HTTPException) as exc:
            raise ModelProviderError("Model provider could not be reached") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ModelProviderError("Model provider returned malformed JSON") from exc
        finally:
            if connection is not None:
                connection.close()
        try:
            if payload["choices"][0].get("finish_reason") == "length":
                raise ModelProviderError(
                    "Model output-token limit reached before a complete structured response; "
                    "reasoning tokens share this limit."
                )
            content = payload["choices"][0]["message"]["content"]
            result = json.loads(content) if isinstance(content, str) else content
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ModelProviderError(
                "Model provider returned no valid structured response"
            ) from exc
        if not isinstance(result, dict):
            raise ModelProviderError("Model structured response must be a JSON object")
        return result

    @classmethod
    def from_environment(cls) -> OpenAICompatibleAdapter:
        endpoint = os.getenv("META_MODEL_API_BASE_URL", "").strip()
        api_key = os.getenv("META_MODEL_API_KEY", "").strip()
        model_id = os.getenv("META_MODEL_ID", "").strip()
        provider = os.getenv("MODEL_PROVIDER", "meta").strip().lower()
        if provider != "meta":
            raise ModelProviderError("MODEL_PROVIDER must be 'meta' for Meta research runs")
        if not endpoint or not api_key or not model_id:
            raise ModelProviderError(
                "Meta model requires META_MODEL_API_BASE_URL, META_MODEL_API_KEY, and META_MODEL_ID"
            )
        if not endpoint.startswith("https://"):
            raise ModelProviderError(HTTPS_REQUIRED)
        try:
            max_output_tokens = int(os.getenv("MODEL_MAX_OUTPUT_TOKENS", "600"))
        except ValueError as exc:
            raise ModelProviderError("MODEL_MAX_OUTPUT_TOKENS must be an integer") from exc
        if not 100 <= max_output_tokens <= 4000:
            raise ModelProviderError("MODEL_MAX_OUTPUT_TOKENS must be between 100 and 4000")
        try:
            max_run_tokens = int(os.getenv("MODEL_MAX_RUN_TOKENS", "100000"))
        except ValueError as exc:
            raise ModelProviderError("MODEL_MAX_RUN_TOKENS must be an integer") from exc
        if not max_output_tokens <= max_run_tokens <= 100_000:
            raise ModelProviderError(
                "MODEL_MAX_RUN_TOKENS must be between MODEL_MAX_OUTPUT_TOKENS and 100000"
            )
        try:
            max_context_tokens = int(
                os.getenv("MODEL_MAX_CONTEXT_TOKENS", str(META_CONTEXT_WINDOW_TOKENS))
            )
        except ValueError as exc:
            raise ModelProviderError("MODEL_MAX_CONTEXT_TOKENS must be an integer") from exc
        if not 16_000 <= max_context_tokens <= META_CONTEXT_WINDOW_TOKENS:
            raise ModelProviderError(
                f"MODEL_MAX_CONTEXT_TOKENS must be between 16000 and {META_CONTEXT_WINDOW_TOKENS}"
            )
        return cls(
            endpoint=endpoint,
            api_key=api_key,
            model_id=model_id,
            provider="meta",
            max_output_tokens=max_output_tokens,
            max_run_tokens=max_run_tokens,
            max_context_tokens=max_context_tokens,
        )

    def generate_structured(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]:
        return self._request_structured(
            messages,
            schema,
            timeout=timeout,
            max_tokens=min(self.max_output_tokens, 1000),
            reasoning_effort="minimal",
        )

    def generate_refinement(
        self, messages: list[dict[str, str]], schema: dict[str, Any], *, timeout: int
    ) -> dict[str, Any]:
        # Refinement is an explicit one-shot operation with output headroom
        # independent from the smaller action-selection response budget.
        return self._request_structured(
            messages,
            schema,
            timeout=timeout,
            # Live Meta planning exhausted 2000 tokens entirely in reasoning.
            # Reserve this full bound before transport; never retry invisibly.
            max_tokens=4000,
        )


def adapter_status() -> dict[str, Any]:
    configured = all(
        os.getenv(name, "").strip()
        for name in ("META_MODEL_API_BASE_URL", "META_MODEL_API_KEY", "META_MODEL_ID")
    )
    configured = configured and os.getenv("MODEL_PROVIDER", "meta").strip().lower() == "meta"
    verified = os.getenv("META_MODEL_VERIFIED", "").lower() == "true"
    try:
        max_run_tokens = int(os.getenv("MODEL_MAX_RUN_TOKENS", "100000"))
    except ValueError:
        max_run_tokens = None
    try:
        max_context_tokens = int(
            os.getenv("MODEL_MAX_CONTEXT_TOKENS", str(META_CONTEXT_WINDOW_TOKENS))
        )
    except ValueError:
        max_context_tokens = None
    try:
        SpendPolicy.from_environment()
        spending_configured = True
    except ModelSpendError:
        spending_configured = False
    return {
        "spending_configured": spending_configured,
        "provider": "meta" if configured else None,
        "configured": configured,
        "smoke_test_verified": verified,
        "enabled_for_runs": configured
        and verified
        and inference_is_enabled()
        and spending_configured,
        "inference_paused": not inference_is_enabled(),
        "model_id": os.getenv("META_MODEL_ID") if configured else None,
        "endpoint_configured": bool(os.getenv("META_MODEL_API_BASE_URL", "").strip()),
        "api_key_present": bool(os.getenv("META_MODEL_API_KEY", "").strip()),
        "max_run_tokens": max_run_tokens,
        "max_context_tokens": max_context_tokens,
    }

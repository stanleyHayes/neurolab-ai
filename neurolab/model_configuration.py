"""Explicit serving-provider identity and isolated credentials for Meta models."""

import os
from dataclasses import dataclass, field

BASETEN_ENDPOINT = "https://inference.baseten.co/v1/chat/completions"
BASETEN_MODEL = "meta-models/muse-spark-open"
PROVIDER_ENV = {
    "meta": (
        "META_MODEL_API_BASE_URL",
        "META_MODEL_API_KEY",
        "META_MODEL_ID",
        "META_MODEL_VERIFIED",
    ),
    "baseten": (
        "BASETEN_MODEL_API_BASE_URL",
        "BASETEN_API_KEY",
        "BASETEN_MODEL_ID",
        "BASETEN_MODEL_VERIFIED",
    ),
}


@dataclass(frozen=True)
class ModelConfiguration:
    provider: str
    endpoint: str
    model_id: str
    api_key_name: str
    api_key: str = field(repr=False)
    verified: bool

    @property
    def configured(self):
        present = bool(self.endpoint and self.model_id and self.api_key)
        if self.provider == "baseten":
            return present and self.endpoint == BASETEN_ENDPOINT and self.model_id == BASETEN_MODEL
        return present


def model_configuration():
    provider = os.getenv("MODEL_PROVIDER", "meta").strip().lower()
    if provider not in PROVIDER_ENV:
        raise ValueError("MODEL_PROVIDER must be meta or baseten")
    endpoint, key, model, verified = PROVIDER_ENV[provider]
    return ModelConfiguration(
        provider=provider,
        endpoint=os.getenv(endpoint, "").strip(),
        model_id=os.getenv(model, "").strip(),
        api_key_name=key,
        api_key=os.getenv(key, "").strip(),
        verified=os.getenv(verified, "").lower() == "true",
    )

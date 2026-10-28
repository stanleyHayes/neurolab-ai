"""Default replay admission with explicit verified-provider opt-in for deployments."""

import os
import re


def configure_replay(*, worker=False):
    database = os.getenv("DATABASE_URL", "").strip()
    if not database.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        raise RuntimeError("Deployment requires persistent PostgreSQL DATABASE_URL")
    os.environ["DATABASE_URL"] = database
    os.environ["APP_ENV"] = "production"
    os.environ["MODEL_INFERENCE_ENABLED"] = "false"
    os.environ["RESEARCH_INLINE_WORKER"] = "false"
    # Render supplies the service's own canonical hostname, never a request header.
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if (
        not os.getenv("ALLOWED_HOSTS", "").strip()
        and len(host) <= 253
        and re.fullmatch(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", host
        )
    ):
        os.environ["ALLOWED_HOSTS"] = host
    # No paid inference is allowed in this deployment profile.
    for name in ("META_MODEL_API_KEY", "BASETEN_API_KEY", "MODEL_API_KEY"):
        os.environ.pop(name, None)
    if worker:
        for name in (
            "AUTH_ED25519_PRIVATE_KEY",
            "AUTH_ED25519_PREVIOUS_PUBLIC_KEYS",
            "AUTH_TOKEN_PEPPER",
            "AUTH_INVITE_CODE",
            "API_BEARER_TOKEN",
        ):
            os.environ.pop(name, None)


def configure_deployment(*, worker=False):
    """Enable Meta only on an explicit flag and a complete reviewed spend policy.

    No provider request is made at startup. Real calls still require SQL owner,
    run, money/token admission and worker lease checks at execution time.
    """
    if os.getenv("MODEL_INFERENCE_ENABLED", "false").lower() != "true":
        configure_replay(worker=worker)
        return
    from .providers import OpenAICompatibleAdapter, adapter_status

    if not adapter_status()["enabled_for_runs"]:
        raise RuntimeError(
            "Model deployment requires verified provider access and configured spending limits"
        )
    adapter = OpenAICompatibleAdapter.from_environment()
    configure_replay(worker=worker)
    from .model_configuration import model_configuration

    os.environ[model_configuration().api_key_name] = adapter.api_key
    os.environ["MODEL_INFERENCE_ENABLED"] = "true"

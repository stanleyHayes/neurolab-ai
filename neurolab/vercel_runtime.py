"""Owner-requested replay-only Vercel deployment admission."""

import os


def configure_replay(*, worker=False):
    database = os.getenv("DATABASE_URL", "").strip()
    if not database.startswith(("postgres://", "postgresql://", "postgresql+psycopg://")):
        raise RuntimeError("Vercel requires persistent PostgreSQL DATABASE_URL")
    os.environ["DATABASE_URL"] = database
    os.environ["APP_ENV"] = "production"
    os.environ["MODEL_INFERENCE_ENABLED"] = "false"
    os.environ["RESEARCH_INLINE_WORKER"] = "false"
    # No paid inference is allowed in this deployment profile.
    for name in ("META_MODEL_API_KEY", "MODEL_API_KEY"):
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

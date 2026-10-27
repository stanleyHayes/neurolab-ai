"""Native Python service entrypoint; keeps the research API internal and replay-only."""

from .vercel_runtime import configure_replay

configure_replay()

# Deployment policy must be applied before API globals initialize.
from .api import app  # noqa: E402, F401

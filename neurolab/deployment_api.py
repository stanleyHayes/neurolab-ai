"""Native Python service entrypoint; requires service authentication for the research API and replay-only."""

from .deployment_runtime import configure_replay

configure_replay()

# Deployment policy must be applied before API globals initialize.
from .api import app  # noqa: E402, F401

"""Authenticated production API with default replay and verified Meta opt-in."""

from .deployment_runtime import configure_deployment

configure_deployment()

# Deployment policy must be applied before API globals initialize.
from .api import app  # noqa: E402, F401

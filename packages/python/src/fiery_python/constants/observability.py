"""
Author: Sean Froning
Created Date: 9.22.2026
Definitions for observability and recovery
"""

SENTRY_HEALTH_PATHS = ("/health", "/ready")
SENTRY_JOB_CONTEXT_TAG_KEYS = (
    "volcano_id",
    "session_id",
    "artifact_id",
)

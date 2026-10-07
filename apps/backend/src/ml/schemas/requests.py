"""
Author: Sean Froning
Created Date: 8.26.2026
Request models for Models
"""

from pydantic import BaseModel, ConfigDict
from fiery_python import ModelTier, ModelRole


class ModelPromoteRequest(BaseModel):
    """Request model for promoting model artifact (empty body)"""

    model_config = ConfigDict(extra="forbid")


class ModelRefreshRequest(BaseModel):
    """Request model for reloading model registry"""

    tier: ModelTier
    role: ModelRole

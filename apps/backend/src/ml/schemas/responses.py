"""
Author: Sean Froning
Created Date: 8.26.2026
Response models for Models
"""

from typing import List, Optional
from pydantic import BaseModel
from fiery_python import ModelTier, ModelRole
from ..models import EvaluatedModel


class ModelPromoteResponse(BaseModel):
    """Response model for promoting model artifact"""

    evaluated_models: List[EvaluatedModel]


class ModelRefreshResponse(BaseModel):
    """Response model for reloading model registry"""

    artifact_id: Optional[str] = None
    tier: ModelTier
    role: ModelRole
    ready: bool

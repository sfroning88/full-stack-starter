"""
Author: Sean Froning
Created Date: 8.20.2026
Inference-side in-memory model
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel
from fiery_python import (
    ModelTier,
    ModelRole,
    TrainingStage,
    TrainingPrecision,
)


class EvaluatedModel(BaseModel):
    """In-memory representation of a evaluated model artifact"""

    artifact_id: str
    tier: ModelTier
    role: ModelRole
    evaluated_at: datetime
    promoted: bool
    promoted_at: Optional[datetime] = None
    denied_reason: Optional[str] = None
    ready: bool


class LoadedModel(BaseModel):
    """In-memory representation of a loaded model artifact"""

    artifact_id: str
    tier: ModelTier
    role: ModelRole
    stage: TrainingStage
    precision: TrainingPrecision
    architecture: str
    param_count: int
    sparsity: Decimal
    storage_path: str
    signature: str
    signed_at: datetime
    promoted: bool
    promoted_at: datetime
    mlflow_run_id: Optional[str] = None
    hf_repo_id: Optional[str] = None
    hf_revision: Optional[str] = None
    session_id: str
    parent_id: Optional[str] = None
    metrics: Dict[str, Decimal] = {}
    preprocessing: Dict[str, Any] = {}


@dataclass
class ArtifactRegistry:
    """Structured input to model registry of (tier, role)"""

    model: Optional[Any]
    metadata: Optional[LoadedModel]
    artifact_id: Optional[str]

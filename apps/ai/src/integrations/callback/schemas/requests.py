"""
Author: Sean Froning
Created Date: 8.24.2026
Request models for Callback
"""

from decimal import Decimal
from pydantic import BaseModel, Field, AfterValidator
from typing import Annotated, List, Optional
from fiery_python import (
    ModelTier,
    ModelRole,
    TrainingPrecision,
    ModelMetric,
    SchemaUtils,
)


class CallbackRequest(BaseModel):
    """Request model for receiving train callback"""

    session_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    tier: ModelTier
    role: ModelRole
    precision: TrainingPrecision = Field(default=TrainingPrecision.FP32)
    storage_path: str
    signature: str
    param_count: int
    architecture: str
    sparsity: Decimal = Decimal("0")
    metrics: List[ModelMetric]
    nonce: Optional[str] = None
    threshold: Decimal
    abstention_band: Decimal
    transform_hash: str
    op_version: int
    base_model_id: Optional[str] = None
    revision: Optional[str] = None
    parent_id: Optional[str] = None
    hf_repo_id: Optional[str] = None
    hf_revision: Optional[str] = None

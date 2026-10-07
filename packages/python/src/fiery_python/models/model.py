"""
Author: Sean Froning
Created Date: 8.19.2026
Class objects for Model schema
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import Field
from ._base_fiery import BaseFiery
from ..enums import (
    TrainingSplit,
    TrainingStage,
    TrainingPrecision,
    ModelTier,
    ModelRole,
    ModelMetricName,
)
from ..utils import UuidUtils


class ModelArtifact(BaseFiery):
    """Normalized Model Artifact"""

    tier: ModelTier
    role: ModelRole
    stage: TrainingStage
    precision: TrainingPrecision = Field(default=TrainingPrecision.FP32)
    architecture: str
    param_count: int
    sparsity: Decimal = Decimal("0")
    storage_path: str
    signature: str
    signed_at: datetime
    promoted: bool = False
    promoted_at: Optional[datetime] = None
    mlflow_run_id: Optional[str] = None
    hf_repo_id: Optional[str] = None
    hf_revision: Optional[str] = None
    session_id: str
    parent_id: Optional[str] = None

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from session_id"""
        if not self.session_id:
            return None
        return UuidUtils.deterministic_uuid(self.session_id)


class ModelMetric(BaseFiery):
    """Normalized Model Metric"""

    name: ModelMetricName
    split: TrainingSplit
    value: Decimal
    artifact_id: str

    def prepare_for_storage(self, include_id: bool = False) -> dict:
        """Composite PK table has no id column"""
        return super().prepare_for_storage(include_id=False)


class ModelBudget(BaseFiery):
    """Normalized Model Budget"""

    flash_kb: Decimal
    flash_budget_kb: Decimal
    peak_ram_kb: Decimal
    peak_ram_budget_kb: Decimal
    macs: int
    macs_budget: int
    latency_ms: Optional[Decimal] = None
    energy_mj: Optional[Decimal] = None
    days_autonomy: Optional[Decimal] = None
    passed: bool
    checked_at: datetime
    artifact_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from artifact_id"""
        if not self.artifact_id:
            return None
        return UuidUtils.deterministic_uuid(self.artifact_id)

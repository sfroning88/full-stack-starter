"""
Author: Sean Froning
Created Date: 8.20.2026
Class objects for Dataset schema
"""

from datetime import datetime
from typing import Optional
from ._base_fiery import BaseFiery
from ..enums import (
    TrainingSampleSource,
    TrainingStatus,
)
from ..utils import UuidUtils


class DatasetIngest(BaseFiery):
    """Normalized Dataset Ingest"""

    source: TrainingSampleSource
    asset_count: int = 0
    status: TrainingStatus
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


class DatasetVersion(BaseFiery):
    """Normalized Dataset Version"""

    transform_hash: str
    manifest_path: str
    shard_count: int
    sample_count: int
    status: TrainingStatus
    contract_id: str

    def deterministic_id(self) -> Optional[str]:
        """Stable id derived from (contract_id, transform_hash)"""
        if not self.contract_id or not self.transform_hash:
            return None
        return UuidUtils.deterministic_uuid(self.contract_id, self.transform_hash)

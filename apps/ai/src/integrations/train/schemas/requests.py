"""
Author: Sean Froning
Created Date: 8.28.2026
Request models for Train
"""

from pydantic import BaseModel, AfterValidator
from typing import Annotated, Optional
from fiery_python import TrainingStage, SchemaUtils


class TrainRequest(BaseModel):
    """Request model for running train job"""

    contract_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    version_id: Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    stage: TrainingStage
    parent_id: Optional[Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]] = None

"""
Author: Sean Froning
Created Date: 8.28.2026
Request models for Inferences
"""

from pydantic import BaseModel, AfterValidator
from typing import Annotated, Optional
from fiery_python import ModelTier, ModelRole, SchemaUtils


class InferencePreviewRequest(BaseModel):
    """Request model for image preview"""

    interferogram_id: Optional[
        Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    ] = None
    seismic_event_id: Optional[
        Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    ] = None

    def validate_payload(self) -> bool:
        if not self.interferogram_id and not self.seismic_event_id:
            return False
        if self.interferogram_id and self.seismic_event_id:
            return False
        return True


class InferenceSingleRequest(BaseModel):
    """Request model for single inference"""

    tier: ModelTier
    role: ModelRole
    interferogram_id: Optional[
        Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    ] = None
    seismic_event_id: Optional[
        Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]
    ] = None
    volcano_id: Optional[Annotated[str, AfterValidator(SchemaUtils.valid_uuid)]] = None

    def validate_payload(self) -> bool:
        if not self.interferogram_id and not self.seismic_event_id:
            return False
        if self.interferogram_id and self.seismic_event_id:
            return False
        return True


class InferenceBatchRequest(BaseModel):
    """Request model for batch inference"""

    tier: ModelTier
    role: ModelRole

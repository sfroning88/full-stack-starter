"""
Author: Sean Froning
Created Date: 8.29.2026
Response models for Inferences
"""

from pydantic import BaseModel
from typing import List
from ..models import InferenceOutcome


class InferenceSingleResponse(BaseModel):
    """Response model for retrieving inference"""

    result: InferenceOutcome
    artifact_id: str
    transform_hash: str


class InferenceBatchResponse(BaseModel):
    """Response model for running inference jobs"""

    job_ids: List[str]

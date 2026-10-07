"""
Author: Sean Froning
Created Date: 8.23.2026
Response models for Train
"""

from pydantic import BaseModel
from typing import List, Optional


class TrainResponse(BaseModel):
    """Response model for running train job"""

    job_ids: List[str]
    session_id: Optional[str]
    cached: bool = False

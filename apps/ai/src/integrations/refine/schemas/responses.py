"""
Author: Sean Froning
Created Date: 8.22.2026
Response models for Refine
"""

from pydantic import BaseModel
from typing import List


class RefineResponse(BaseModel):
    """Response model for running refine job"""

    job_ids: List[str]
    version_id: str
    transform_hash: str
    cached: bool = False

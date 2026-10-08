"""
Author: Sean Froning
Created Date: 10.7.2026
Response models for Backend
"""

from pydantic import BaseModel
from typing import List


class BackendResponse(BaseModel):
    """Response model for running Backend jobs"""

    job_ids: List[str]

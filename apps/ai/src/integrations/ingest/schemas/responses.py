"""
Author: Sean Froning
Created Date: 8.21.2026
Response models for Ingest
"""

from pydantic import BaseModel
from typing import List


class IngestResponse(BaseModel):
    """Response model for running ingest job"""

    job_ids: List[str]

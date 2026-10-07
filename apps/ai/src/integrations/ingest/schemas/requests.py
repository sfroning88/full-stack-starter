"""
Author: Sean Froning
Created Date: 8.21.2026
Request models for Ingest
"""

from pydantic import BaseModel
from fiery_python import TrainingSampleSource


class IngestRequest(BaseModel):
    """Request model for running ingest job"""

    source: TrainingSampleSource
    max_samples: int = 5

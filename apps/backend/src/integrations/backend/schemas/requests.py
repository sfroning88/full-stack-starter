"""
Author: Sean Froning
Created Date: 10.7.2026
Request models for MyProject
"""

from pydantic import BaseModel, ConfigDict


class BackendRequest(BaseModel):
    """Request model (empty body)"""

    model_config = ConfigDict(extra="forbid")
